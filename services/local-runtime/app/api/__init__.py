"""API package — collects every router and exposes a single ``api_router``."""

from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.agents import router as agents_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.goals import router as goals_router
from app.api.routes.accounts import router as accounts_router
from app.api.routes.content import router as content_router
from app.api.routes.workflows import router as workflows_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.security import router as security_router
from app.api.routes.settings import router as settings_router
from app.api.routes.voice import router as voice_router
from app.api.routes.telegram import router as telegram_router
from app.api.routes.devices import router as devices_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(agents_router)
api_router.include_router(tasks_router)
api_router.include_router(goals_router)
api_router.include_router(accounts_router)
api_router.include_router(content_router)
api_router.include_router(workflows_router)
api_router.include_router(analytics_router)
api_router.include_router(security_router)
api_router.include_router(settings_router)
api_router.include_router(voice_router)
api_router.include_router(telegram_router)
api_router.include_router(devices_router)

__all__ = ["api_router"]
