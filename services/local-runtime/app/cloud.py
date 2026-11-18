"""Password-protected, single-instance cloud entrypoint for the local runtime.

Run with ``python -m app.cloud``. The normal ``app.main:app`` entrypoint remains
available for desktop use and does not inherit the cloud login requirement.
"""

from __future__ import annotations

import base64
import binascii
import hmac
import os
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI
from sqlalchemy import text
from starlette.datastructures import Headers
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles
from starlette.types import ASGIApp, Receive, Scope, Send

from app.config import get_settings


class CloudLogin:
    """Require HTTP Basic authentication for HTTP and WebSocket requests."""

    def __init__(self, app: ASGIApp, username: str, password: str) -> None:
        self.app = app
        self.username = username.encode("utf-8")
        self.password = password.encode("utf-8")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in {"http", "websocket"}:
            await self.app(scope, receive, send)
            return

        # Only the minimal readiness probe is public, not runtime diagnostics.
        if (
            scope["type"] == "http"
            and scope["path"] == "/healthz"
            and scope["method"] in {"GET", "HEAD"}
        ):
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        origin = headers.get("origin")
        if origin:
            try:
                parsed_origin = urlsplit(origin)
                same_origin = (
                    parsed_origin.scheme in {"http", "https"}
                    and parsed_origin.netloc.lower() == headers.get("host", "").lower()
                    and not parsed_origin.path
                    and not parsed_origin.query
                    and not parsed_origin.fragment
                )
            except ValueError:
                same_origin = False
            if not same_origin:
                if scope["type"] == "websocket":
                    await send({"type": "websocket.close", "code": 1008})
                else:
                    await JSONResponse(
                        {"detail": "Cross-origin cloud access is not allowed"},
                        status_code=403,
                    )(scope, receive, send)
                return

        authorization = headers.get("authorization", "")
        scheme, _, encoded = authorization.partition(" ")
        valid = False
        if scheme.lower() == "basic":
            try:
                username, separator, password = base64.b64decode(
                    encoded, validate=True
                ).partition(b":")
                valid_user = hmac.compare_digest(username, self.username)
                valid_password = hmac.compare_digest(password, self.password)
                valid = bool(separator) and valid_user and valid_password
            except (ValueError, binascii.Error):
                pass

        if not valid:
            if scope["type"] == "websocket":
                await send({"type": "websocket.close", "code": 1008})
                return
            response = JSONResponse(
                {"detail": "Cloud login required"},
                status_code=401,
                headers={
                    "WWW-Authenticate": 'Basic realm="Javo Agents", charset="UTF-8"',
                    "Cache-Control": "no-store",
                },
            )
            await response(scope, receive, send)
            return

        async def private_send(message):
            if message["type"] == "http.response.start":
                message = dict(message)
                message["headers"] = list(message.get("headers", [])) + [
                    (b"cache-control", b"no-store"),
                ]
            await send(message)

        await self.app(scope, receive, private_send)


class DashboardFiles(StaticFiles):
    """Serve React routes without treating missing assets as HTML pages."""

    async def get_response(self, path: str, scope: Scope):
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            if exc.status_code != 404 or Path(path).suffix or path.startswith("assets/"):
                raise
            return await super().get_response("index.html", scope)


def _required_secret(name: str, minimum: int = 32) -> str:
    value = os.environ.get(name, "")
    if len(value) < minimum or value.startswith(("change-me", "replace-me")):
        raise RuntimeError(f"Set {name} to a unique secret of at least {minimum} characters")
    return value


def create_cloud_app() -> FastAPI:
    """Create the cloud app; refuse to expose the runtime without credentials."""
    username = os.environ.get("JAVO_CLOUD_USERNAME", "").strip()
    if not username or ":" in username:
        raise RuntimeError("Set JAVO_CLOUD_USERNAME to a non-empty username without ':'")
    password = _required_secret("JAVO_CLOUD_PASSWORD", minimum=20)
    _required_secret("JAVO_SECRET_KEY")
    _required_secret("JAVO_ENCRYPTION_KEY")

    # Import after validation, so an incomplete deployment fails before services start.
    from app import database as db
    from app.main import create_app

    runtime = create_app()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        async with runtime.router.lifespan_context(runtime):
            yield

    application = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    application.add_middleware(CloudLogin, username=username, password=password)

    @application.api_route("/healthz", methods=["GET", "HEAD"], include_in_schema=False)
    async def healthz():
        try:
            if db.async_session_factory is None:
                raise RuntimeError("Database has not started")
            async with db.async_session_factory() as session:
                await session.execute(text("SELECT 1"))
        except Exception:
            return JSONResponse({"status": "unavailable"}, status_code=503)
        return JSONResponse({"status": "ok"})

    application.mount("/api", runtime)

    dashboard = Path(os.environ.get("JAVO_DASHBOARD_DIST", ""))
    if not (dashboard / "index.html").is_file():
        raise RuntimeError("Set JAVO_DASHBOARD_DIST to the built dashboard directory")
    application.mount("/", DashboardFiles(directory=str(dashboard), html=True))
    return application


if __name__ == "__main__":
    import uvicorn

    # The container ingress is intentionally public; CloudLogin gates runtime access.
    uvicorn.run(
        "app.cloud:create_cloud_app",
        factory=True,
        host="0.0.0.0",  # nosec B104
        port=int(os.environ.get("PORT", str(get_settings().port))),
        workers=1,
        proxy_headers=True,
    )
