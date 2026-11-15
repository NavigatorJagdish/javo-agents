"""Application settings, AI provider configuration, and backup/restore routes."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, SecretStr, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_session
from app.services.backup_service import BackupService
from app.core.provider_store import VaultUnavailable
from app.services import provider_settings

router = APIRouter(prefix="/settings", tags=["settings"])

# Runtime mutable overrides layered on top of Settings


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class SettingsResponse(BaseModel):
    app_name: str
    app_version: str
    debug: bool
    log_level: str
    default_ai_provider: str
    ai_daily_budget: float
    ai_monthly_budget: float
    max_tokens_per_request: int
    max_concurrent_agents: int
    cpu_limit_percent: float
    memory_limit_percent: float
    require_device_approval: bool
    content_root: str
    upload_dir: str
    backup_dir: str


class SettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    log_level: Optional[str] = None
    default_ai_provider: Optional[str] = None
    ai_daily_budget: Optional[float] = Field(default=None, ge=0.0)
    ai_monthly_budget: Optional[float] = Field(default=None, ge=0.0)
    max_tokens_per_request: Optional[int] = Field(default=None, ge=1)
    max_concurrent_agents: Optional[int] = Field(default=None, ge=1)
    cpu_limit_percent: Optional[float] = Field(default=None, ge=10.0, le=100.0)
    memory_limit_percent: Optional[float] = Field(default=None, ge=10.0, le=100.0)
    require_device_approval: Optional[bool] = None


class AIProviderInfo(BaseModel):
    name: str
    enabled: bool
    model: str
    base_url: Optional[str] = None
    has_api_key: bool = False


class AIProviderUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: Optional[bool] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[SecretStr] = None


class BackupInfo(BaseModel):
    filename: str
    path: str
    size_bytes: int
    created_at: str
    encrypted: bool = False


class RestoreRequest(BaseModel):
    filename: str


class RestoreResponse(BaseModel):
    restored_from: str
    status: str
    message: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _effective_settings() -> SettingsResponse:
    s = get_settings()
    data = {
        "app_name": s.app_name,
        "app_version": s.app_version,
        "debug": s.debug,
        "log_level": s.log_level,
        "default_ai_provider": s.default_ai_provider,
        "ai_daily_budget": s.ai_daily_budget,
        "ai_monthly_budget": s.ai_monthly_budget,
        "max_tokens_per_request": s.max_tokens_per_request,
        "max_concurrent_agents": s.max_concurrent_agents,
        "cpu_limit_percent": s.cpu_limit_percent,
        "memory_limit_percent": s.memory_limit_percent,
        "require_device_approval": s.require_device_approval,
        "content_root": s.content_root,
        "upload_dir": s.upload_dir,
        "backup_dir": s.backup_dir,
    }
    data.update(provider_settings.effective()["settings"])
    return SettingsResponse(**data)


def _init_providers() -> dict[str, dict[str, Any]]:
    return {cfg["name"]: cfg for cfg in provider_settings.metadata()}


def _resolve_sqlite_path() -> Optional[Path]:
    url = get_settings().database_url
    prefix = "sqlite+aiosqlite:///"
    if url.startswith(prefix):
        return Path(url[len(prefix) :]).resolve()
    return None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/", response_model=SettingsResponse)
async def get_all_settings() -> SettingsResponse:
    """Return effective application settings (sensitive keys excluded)."""
    try:
        return _effective_settings()
    except VaultUnavailable as error:
        raise HTTPException(503, str(error)) from None


@router.put("/", response_model=SettingsResponse)
def update_settings(body: SettingsUpdate) -> SettingsResponse:
    try:
        provider_settings.update_ai_settings(body.model_dump(exclude_unset=True, exclude_none=True))
        return _effective_settings()
    except VaultUnavailable as error:
        raise HTTPException(503, str(error)) from None
    except ValueError as error:
        raise HTTPException(422, str(error)) from None


@router.get("/ai-providers", response_model=list[AIProviderInfo])
async def list_ai_providers() -> list[AIProviderInfo]:
    """List configured AI providers and their active models."""
    try:
        return [AIProviderInfo(**cfg) for cfg in provider_settings.metadata()]
    except VaultUnavailable as error:
        raise HTTPException(503, str(error)) from None


@router.put("/ai-providers/{name}", response_model=AIProviderInfo)
def update_ai_provider(name: str, body: AIProviderUpdate) -> AIProviderInfo:
    """Update configuration for an AI provider (ollama, gemini, openai)."""
    key = name.lower()
    if key not in provider_settings.PROVIDERS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"AI provider '{name}' not found")

    patch = body.model_dump(exclude_unset=True)
    if body.api_key is not None:
        patch["api_key"] = body.api_key.get_secret_value()
    try:
        providers = provider_settings.update_provider(key, patch)
        return AIProviderInfo(**next(cfg for cfg in providers if cfg["name"] == key))
    except VaultUnavailable as error:
        raise HTTPException(503, str(error)) from None
    except ValueError as error:
        raise HTTPException(422, str(error)) from None


@router.delete("/ai-providers/{name}/credentials", response_model=AIProviderInfo)
def remove_provider_credentials(name: str) -> AIProviderInfo:
    if name not in provider_settings.PROVIDERS:
        raise HTTPException(404, "AI provider not found")
    try:
        providers = provider_settings.remove_credentials(name)
        return AIProviderInfo(**next(cfg for cfg in providers if cfg["name"] == name))
    except VaultUnavailable as error:
        raise HTTPException(503, str(error)) from None


@router.get("/provider-storage")
def provider_storage_status() -> dict:
    storage = provider_settings.vault()
    try:
        storage.read()
        return {"available": storage.protection != "unavailable", "protection": storage.protection}
    except VaultUnavailable:
        return {"available": False, "protection": "locked"}


@router.post("/backup", response_model=BackupInfo, status_code=status.HTTP_201_CREATED)
def create_backup(session: AsyncSession = Depends(get_session)) -> BackupInfo:
    """Create an encrypted online SQLite snapshot with a configured persistent key."""
    del session  # ensures DB initialization before backup
    settings = get_settings()
    if not settings.encryption_key or len(settings.encryption_key) < 32:
        raise HTTPException(503, "Configure and securely retain a persistent backup encryption key first")
    db_path = _resolve_sqlite_path()
    if db_path is None or not db_path.is_file():
        raise HTTPException(409, "Local SQLite database is unavailable; no backup created")
    service = BackupService(backup_dir=settings.backup_dir, encryption_key=settings.encryption_key)
    try:
        result = service.create_sqlite_backup(db_path)
    except Exception:
        raise HTTPException(503, "Database snapshot failed; no verified backup available") from None
    return BackupInfo(
        filename=result["backup_file"], path=result["path"], size_bytes=result["size_bytes"],
        created_at=result["created_at"], encrypted=True,
    )


@router.post("/restore", response_model=RestoreResponse)
async def restore_backup(body: RestoreRequest) -> RestoreResponse:
    """Never overwrite a database while runtime services hold active connections."""
    raise HTTPException(409, "Live restore is disabled. Stop runtime, verify/decrypt into empty staging, then perform an offline restore.")


@router.get("/backups", response_model=list[BackupInfo])
async def list_backups() -> list[BackupInfo]:
    """List available backup files."""
    backup_dir = Path(get_settings().backup_dir).resolve()
    if not backup_dir.exists():
        return []

    backups: list[BackupInfo] = []
    entries = list(backup_dir.glob("*.db")) + list(backup_dir.glob("*.jbackup"))
    for entry in sorted(entries, key=lambda p: p.stat().st_mtime, reverse=True):
        stat = entry.stat()
        backups.append(
            BackupInfo(
                filename=entry.name,
                path=str(entry),
                size_bytes=stat.st_size,
                created_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                encrypted=entry.suffix == ".jbackup",
            )
        )
    return backups
