"""FastAPI application entrypoint for Javo Agents Local Runtime."""

from __future__ import annotations

import json
import logging
import os
from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

import app.models  # noqa: F401 - ensure all SQLAlchemy models are registered
from app.api import api_router
from app.config import get_settings
from app.core.resource_manager import get_resource_manager
from app.core.scheduler import scheduler
from app.core.local_auth import is_valid_owner_token, require_local_owner
from app import database as db
from app.database import close_db, create_tables, init_engine
from app.models.agent import AgentDefinition, AgentStatus
from app.services.content_watcher import get_content_watcher

settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("javo.main")


class WebSocketManager:
    """Manages active dashboard/companion WebSocket connections for live events."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket client connected (total=%d)", len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info("WebSocket client disconnected (total=%d)", len(self.active_connections))

    async def broadcast(self, event_type: str, data: dict[str, Any]) -> None:
        payload = json.dumps({"event": event_type, "data": data})
        dead: list[WebSocket] = []
        for conn in self.active_connections:
            try:
                await conn.send_text(payload)
            except Exception:
                dead.append(conn)
        for conn in dead:
            self.disconnect(conn)


ws_manager = WebSocketManager()


async def _seed_agents() -> None:
    """Register all specialist agents and MasterAgent in the database if missing."""
    try:
        from app.agents import get_all_agents
    except Exception as exc:
        logger.warning("Skipping agent seeding because agent registry failed to import: %s", exc)
        return

    if db.async_session_factory is None:
        return

    agents = get_all_agents()
    async with db.async_session_factory() as session:
        existing_res = await session.execute(select(AgentDefinition.agent_key))
        existing_keys = set(existing_res.scalars().all())

        created = 0
        for key, agent in agents.items():
            if key in existing_keys:
                continue
            definition = AgentDefinition(
                agent_key=key,
                name=getattr(agent, "display_name", key.replace("_", " ").title()),
                description=getattr(agent, "description", ""),
                category=getattr(agent, "category", "specialist"),
                version=getattr(agent, "version", "1.0.0"),
                status=AgentStatus.IDLE if getattr(agent, "is_enabled", True) else AgentStatus.DISABLED,
                capabilities=list(getattr(agent, "capabilities", [])),
                input_schema=getattr(agent, "input_schema", {}),
                output_schema=getattr(agent, "output_schema", {}),
                tools=list(getattr(agent, "tools", [])),
                is_enabled=getattr(agent, "is_enabled", True),
            )
            session.add(definition)
            created += 1

        if created:
            await session.commit()
            logger.info("Seeded %d agent definitions into database", created)


def _ensure_directories() -> None:
    settings = get_settings()
    for path_str in (
        settings.content_root,
        settings.upload_dir,
        settings.backup_dir,
        settings.thumbnail_dir,
    ):
        Path(path_str).mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle for Javo Agents local runtime."""
    settings = get_settings()
    logger.info("Starting %s v%s", settings.app_name, settings.app_version)
    _ensure_directories()

    # Register cleanup before each start, including partially failed starts.
    # AsyncExitStack attempts all cleanups even if an earlier cleanup raises.
    async with AsyncExitStack() as cleanup:
        cleanup.push_async_callback(close_db)
        init_engine()
        await create_tables()
        await _seed_agents()

        resource_mgr = get_resource_manager()
        cleanup.push_async_callback(resource_mgr.stop_worker)
        resource_mgr.start_worker()

        cleanup.callback(scheduler.shutdown, wait=False)
        scheduler.start(paused=resource_mgr._paused or resource_mgr._emergency_stopped)

        watcher = get_content_watcher()
        cleanup.callback(watcher.stop)
        watcher.start_watching(settings.content_root)

        try:
            yield
        finally:
            logger.info("Shutting down %s", settings.app_name)



def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Local-first multi-agent automation backend for Javo Agents",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins + ["http://127.0.0.1:3000", "http://127.0.0.1:5173", "null"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Both path forms use exactly the same handlers and authentication boundary.
    application.include_router(api_router, dependencies=[Depends(require_local_owner)])
    application.include_router(api_router, prefix="/api", dependencies=[Depends(require_local_owner)])

    @application.get("/auth/status", tags=["auth"])
    async def auth_status() -> dict[str, bool]:
        token = get_settings().owner_access_token
        return {"configured": bool(token and len(token.get_secret_value()) >= 32)}

    @application.get("/", tags=["root"])
    async def root() -> dict[str, Any]:
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "status": "running",
            "docs_url": "/docs",
            "health_url": "/health/",
        }

    @application.websocket("/ws")
    @application.websocket("/ws/events")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        if not is_valid_owner_token(websocket.headers.get("authorization")):
            await websocket.close(code=1008)
            return
        await ws_manager.connect(websocket)
        try:
            await websocket.send_json({"event": "connected", "data": {"version": settings.app_version}})
            while True:
                raw = await websocket.receive_text()
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    msg = {"type": "text", "payload": raw}

                if msg.get("type") == "ping":
                    await websocket.send_json({"event": "pong", "data": {}})
                else:
                    await websocket.send_json({"event": "ack", "data": msg})
        except WebSocketDisconnect:
            pass
        finally:
            ws_manager.disconnect(websocket)

    # Serve built local web dashboard when present (localhost-only by default via JAVO_HOST=127.0.0.1)
    override_dist = os.environ.get("JAVO_DASHBOARD_DIST")
    dashboard_dist = (
        Path(override_dist)
        if override_dist
        else Path(__file__).resolve().parents[3] / "apps" / "dashboard" / "dist"
    )
    if dashboard_dist.is_dir() and (dashboard_dist / "index.html").is_file():
        application.mount(
            "/dashboard",
            StaticFiles(directory=str(dashboard_dist), html=True),
            name="dashboard",
        )

    return application


app = create_app()
