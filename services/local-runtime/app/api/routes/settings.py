"""Application settings, AI provider configuration, and backup/restore routes."""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.ai_router import get_ai_router
from app.database import get_session
from app.services.backup_service import BackupService

router = APIRouter(prefix="/settings", tags=["settings"])

# Runtime mutable overrides layered on top of Settings
_RUNTIME_OVERRIDES: dict[str, Any] = {}
_AI_PROVIDER_CONFIGS: dict[str, dict[str, Any]] = {}


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
    enabled: Optional[bool] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None


class CustomProviderCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=64)
    base_url: str = Field(..., min_length=8)
    model: str = Field(..., min_length=1)
    api_key: Optional[str] = None
    enabled: bool = True


class OllamaPullRequest(BaseModel):
    model: str = Field(..., min_length=2, max_length=128)


class BackupInfo(BaseModel):
    filename: str
    path: str
    size_bytes: int
    created_at: str
    encrypted: bool = True
    checksum: Optional[str] = None


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
    data.update(_RUNTIME_OVERRIDES)
    return SettingsResponse(**data)


def _init_providers() -> dict[str, dict[str, Any]]:
    if not _AI_PROVIDER_CONFIGS:
        s = get_settings()
        _AI_PROVIDER_CONFIGS["ollama"] = {
            "name": "ollama",
            "enabled": True,
            "model": s.ollama_default_model,
            "base_url": s.ollama_base_url,
            "has_api_key": False,
        }
        _AI_PROVIDER_CONFIGS["gemini"] = {
            "name": "gemini",
            "enabled": bool(s.gemini_api_key),
            "model": s.gemini_model,
            "base_url": None,
            "has_api_key": bool(s.gemini_api_key),
        }
        _AI_PROVIDER_CONFIGS["openai"] = {
            "name": "openai",
            "enabled": bool(s.openai_api_key),
            "model": s.openai_model,
            "base_url": s.openai_base_url,
            "has_api_key": bool(s.openai_api_key),
        }
    return _AI_PROVIDER_CONFIGS


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
    return _effective_settings()


@router.put("/", response_model=SettingsResponse)
async def update_settings(body: SettingsUpdate) -> SettingsResponse:
    """Update runtime application settings and sync active Settings singleton."""
    updates = body.model_dump(exclude_unset=True)
    _RUNTIME_OVERRIDES.update(updates)
    s = get_settings()
    for key, value in updates.items():
        if hasattr(s, key):
            setattr(s, key, value)
    return _effective_settings()


@router.get("/ai-providers", response_model=list[AIProviderInfo])
async def list_ai_providers() -> list[AIProviderInfo]:
    """List configured AI providers and their active models synced with AIRouter."""
    providers = _init_providers()
    router_status = get_ai_router().get_provider_status().get("providers", {})
    result: list[AIProviderInfo] = []
    for name, info in router_status.items():
        merged = {
            **providers.get(name, {}),
            "name": name,
            "enabled": bool(info.get("enabled", False)),
            "model": str(info.get("model", "")),
            "base_url": info.get("base_url"),
            "has_api_key": bool(info.get("has_api_key", False)),
        }
        providers[name] = merged
        result.append(AIProviderInfo(**merged))
    return result


@router.post("/ai-providers", response_model=AIProviderInfo, status_code=status.HTTP_201_CREATED)
async def create_custom_ai_provider(body: CustomProviderCreate) -> AIProviderInfo:
    """Register or update a custom OpenAI-compatible AI provider."""
    key = body.name.strip().lower()
    if key in {"ollama", "gemini", "openai"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Use PUT /settings/ai-providers/{key} to update built-in providers",
        )
    ai_router = get_ai_router()
    ai_router.configure_provider(
        key,
        {
            "base_url": body.base_url.strip(),
            "model": body.model.strip(),
            "api_key": body.api_key,
            "enabled": body.enabled,
        },
    )
    providers = _init_providers()
    providers[key] = {
        "name": key,
        "enabled": body.enabled,
        "model": body.model.strip(),
        "base_url": body.base_url.strip(),
        "has_api_key": bool(body.api_key),
    }
    return AIProviderInfo(**providers[key])


@router.get("/ai-providers/quota")
async def get_ai_provider_quota() -> dict[str, Any]:
    """Return usage, spend caps, queued offline jobs, and provider status."""
    return get_ai_router().get_provider_status()


@router.put("/ai-providers/{name}", response_model=AIProviderInfo)
async def update_ai_provider(name: str, body: AIProviderUpdate) -> AIProviderInfo:
    """Update configuration for an AI provider and sync immediately with AIRouter."""
    providers = _init_providers()
    key = name.lower()
    ai_router = get_ai_router()
    router_providers = ai_router.get_provider_status().get("providers", {})
    if key not in providers and key not in router_providers:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"AI provider '{name}' not found")

    cfg = providers.setdefault(
        key,
        {
            "name": key,
            "enabled": bool(router_providers.get(key, {}).get("enabled", False)),
            "model": str(router_providers.get(key, {}).get("model", "")),
            "base_url": router_providers.get(key, {}).get("base_url"),
            "has_api_key": bool(router_providers.get(key, {}).get("has_api_key", False)),
        },
    )
    data = body.model_dump(exclude_unset=True)
    router_update = dict(data)
    if "api_key" in data:
        api_key = data.pop("api_key")
        cfg["has_api_key"] = bool(api_key)
        if api_key and "enabled" not in data:
            cfg["enabled"] = True
            router_update["enabled"] = True
    ai_router.configure_provider(key, router_update)
    cfg.update(data)
    return AIProviderInfo(**cfg)


@router.delete("/ai-providers/{name}/key", response_model=AIProviderInfo)
async def remove_ai_provider_key(name: str) -> AIProviderInfo:
    """Remove stored runtime API key for a provider and keep zero-cost local fallback intact."""
    providers = _init_providers()
    key = name.lower()
    ai_router = get_ai_router()
    if key not in providers and key not in ai_router.get_provider_status().get("providers", {}):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"AI provider '{name}' not found")
    ai_router.remove_provider_key(key)
    cfg = providers.get(key, {"name": key, "model": "default", "base_url": None})
    cfg["has_api_key"] = False
    if key in {"gemini", "openai"}:
        cfg["enabled"] = False
    providers[key] = cfg
    return AIProviderInfo(**cfg)


@router.delete("/ai-providers/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_provider(name: str) -> None:
    """Delete a custom AI provider (built-in providers cannot be deleted)."""
    key = name.lower()
    if key in {"ollama", "gemini", "openai"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Built-in providers cannot be deleted; remove their API key or disable instead.",
        )
    existed = get_ai_router().delete_custom_provider(key)
    _AI_PROVIDER_CONFIGS.pop(key, None)
    if not existed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Custom provider '{name}' not found")


@router.post("/ai-providers/{name}/test")
async def test_ai_provider(name: str) -> dict[str, Any]:
    """Run an active connection check against an AI provider."""
    return await get_ai_router().test_provider(name)


@router.get("/ollama/models")
async def list_ollama_models() -> dict[str, Any]:
    """List local Ollama models and daemon reachability."""
    return await get_ai_router().check_ollama_health()


@router.post("/ollama/pull")
async def pull_ollama_model(body: OllamaPullRequest) -> dict[str, Any]:
    """Pull a local Ollama model cleanly without raising on daemon unavailability."""
    return await get_ai_router().pull_ollama_model(body.model)


@router.get("/ai-queue")
async def list_ai_offline_queue() -> list[dict[str, Any]]:
    """Inspect jobs queued while all AI providers were unavailable."""
    return get_ai_router().get_queued_jobs()


@router.post("/ai-queue/drain")
async def drain_ai_offline_queue() -> dict[str, Any]:
    """Attempt to process offline queued AI jobs."""
    return await get_ai_router().drain_queued_jobs()


@router.post("/backup", response_model=BackupInfo, status_code=status.HTTP_201_CREATED)
async def create_backup(session: AsyncSession = Depends(get_session)) -> BackupInfo:
    """Create an encrypted .jbackup archive in the configured backup directory."""
    del session  # ensures DB initialization before backup
    settings = get_settings()
    db_path = _resolve_sqlite_path()
    sched_prefix = "sqlite:///"
    sched_path = (
        Path(settings.scheduler_db_url[len(sched_prefix):]).resolve()
        if settings.scheduler_db_url.startswith(sched_prefix)
        else None
    )
    targets: list[str | Path] = []
    if db_path and db_path.exists():
        targets.append(db_path)
    if sched_path and sched_path.exists():
        targets.append(sched_path)

    svc = BackupService(backup_dir=settings.backup_dir)
    info = svc.create_backup(include_paths=targets, label="manual")
    return BackupInfo(
        filename=info["backup_file"],
        path=info["path"],
        size_bytes=info["size_bytes"],
        created_at=info["created_at"],
        encrypted=True,
        checksum=info["checksum"],
    )


@router.post("/restore", response_model=RestoreResponse)
async def restore_backup(body: RestoreRequest) -> RestoreResponse:
    """Verify & restore the SQLite database from an encrypted .jbackup or legacy .db backup."""
    settings = get_settings()
    backup_dir = Path(settings.backup_dir).resolve()
    safe_name = Path(body.filename).name
    if safe_name != body.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid backup filename")
    src = (backup_dir / safe_name).resolve()

    if not src.exists() or src.parent != backup_dir:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup file not found")

    db_path = _resolve_sqlite_path()
    if not db_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Restore is only supported for local SQLite databases",
        )

    if safe_name.endswith(".jbackup"):
        svc = BackupService(backup_dir=settings.backup_dir)
        verification = svc.verify_backup(safe_name)
        if not verification.get("valid"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Encrypted backup verification failed: {verification.get('error', 'corrupt archive')}",
            )
        restore_res = svc.restore_backup(safe_name, restore_dir=db_path.parent)
        if not restore_res.get("restored"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(restore_res.get("error", "Restore failed")),
            )
        return RestoreResponse(
            restored_from=safe_name,
            status="restored",
            message="Encrypted backup verified and restored. Restart or reconnect active sessions if needed.",
        )

    shutil.copy2(src, db_path)
    return RestoreResponse(
        restored_from=safe_name,
        status="restored",
        message="Database restored from backup. Restart or reconnect active sessions if needed.",
    )


@router.get("/backups", response_model=list[BackupInfo])
async def list_backups() -> list[BackupInfo]:
    """List available encrypted (.jbackup) and legacy (.db) backup files."""
    backup_dir = Path(get_settings().backup_dir).resolve()
    if not backup_dir.exists():
        return []

    entries = list(backup_dir.glob("*.jbackup")) + list(backup_dir.glob("*.db"))
    backups: list[BackupInfo] = []
    for entry in sorted(entries, key=lambda p: p.stat().st_mtime, reverse=True):
        stat = entry.stat()
        sha_path = entry.with_suffix(".jbackup.sha256")
        checksum = sha_path.read_text(encoding="utf-8").strip() if sha_path.exists() else None
        backups.append(
            BackupInfo(
                filename=entry.name,
                path=str(entry),
                size_bytes=stat.st_size,
                created_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                encrypted=entry.suffix == ".jbackup",
                checksum=checksum,
            )
        )
    return backups
