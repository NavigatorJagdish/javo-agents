"""Health-check, system info, and diagnostics routes."""

from __future__ import annotations

import platform
import time
from datetime import datetime, timezone

import psutil
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session

router = APIRouter(prefix="/health", tags=["health"])

_START_TIME = time.monotonic()
_VERSION = "0.1.0"


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------
class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float
    database: str
    timestamp: str


class SystemInfoResponse(BaseModel):
    cpu_percent: float
    cpu_count: int
    ram_total_mb: float
    ram_used_mb: float
    ram_percent: float
    disk_total_gb: float
    disk_used_gb: float
    disk_percent: float
    python_version: str
    platform: str


class ServiceCheck(BaseModel):
    name: str
    status: str
    message: str | None = None


class DiagnosticsResponse(BaseModel):
    overall: str
    checks: list[ServiceCheck]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/", response_model=HealthResponse)
async def health_check(session: AsyncSession = Depends(get_session)) -> HealthResponse:
    """Basic health check including database connectivity."""
    db_status = "connected"
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "unavailable"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        version=_VERSION,
        uptime_seconds=round(time.monotonic() - _START_TIME, 2),
        database=db_status,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/system", response_model=SystemInfoResponse)
async def system_info() -> SystemInfoResponse:
    """Return CPU, RAM, disk usage, and Python version."""
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return SystemInfoResponse(
        cpu_percent=psutil.cpu_percent(interval=0.1),
        cpu_count=psutil.cpu_count() or 1,
        ram_total_mb=round(vm.total / 1_048_576, 1),
        ram_used_mb=round(vm.used / 1_048_576, 1),
        ram_percent=vm.percent,
        disk_total_gb=round(disk.total / 1_073_741_824, 2),
        disk_used_gb=round(disk.used / 1_073_741_824, 2),
        disk_percent=disk.percent,
        python_version=platform.python_version(),
        platform=platform.platform(),
    )


@router.get("/diagnostics", response_model=DiagnosticsResponse)
async def diagnostics(session: AsyncSession = Depends(get_session)) -> DiagnosticsResponse:
    """Run diagnostic checks against every critical service."""
    checks: list[ServiceCheck] = []

    # Database
    try:
        await session.execute(text("SELECT 1"))
        checks.append(ServiceCheck(name="database", status="ok"))
    except Exception as exc:
        checks.append(ServiceCheck(name="database", status="error", message=str(exc)))

    # Scheduler (best-effort import)
    try:
        from app.core.scheduler import scheduler  # type: ignore[import-untyped]

        running = getattr(scheduler, "running", False)
        checks.append(
            ServiceCheck(
                name="scheduler",
                status="ok" if running else "warning",
                message=None if running else "scheduler not running",
            )
        )
    except Exception:
        checks.append(ServiceCheck(name="scheduler", status="warning", message="scheduler module not loaded"))

    # AI router
    try:
        from app.core.ai_router import AIRouter  # noqa: F401

        checks.append(ServiceCheck(name="ai_router", status="ok"))
    except Exception:
        checks.append(ServiceCheck(name="ai_router", status="warning", message="ai_router module not loaded"))

    overall = "healthy"
    if any(c.status == "error" for c in checks):
        overall = "unhealthy"
    elif any(c.status == "warning" for c in checks):
        overall = "degraded"

    return DiagnosticsResponse(overall=overall, checks=checks)


class BenchmarkResponse(BaseModel):
    ram_total_gb: float
    ram_available_gb: float
    cpu_cores: int
    disk_free_gb: float
    recommended_mode: str
    recommended_ollama_model: str
    recommended_max_concurrent_agents: int
    zero_cost_default: bool
    ollama_reachable: bool
    ollama_models: list[str]
    ffmpeg_available: bool
    notes: list[str]


@router.get("/benchmark", response_model=BenchmarkResponse)
async def device_benchmark() -> BenchmarkResponse:
    """Measure local device capabilities and recommend a safe 8GB+ operating mode."""
    import shutil

    from app.core.ai_router import get_ai_router

    vm = psutil.virtual_memory()
    disk = psutil.disk_usage(".")
    ram_total_gb = round(vm.total / (1024**3), 2)
    ram_avail_gb = round(vm.available / (1024**3), 2)
    disk_free_gb = round(disk.free / (1024**3), 2)
    cpu_cores = psutil.cpu_count() or 1

    ai_router = get_ai_router()
    ollama = await ai_router.check_ollama_health()
    ffmpeg_ok = shutil.which("ffmpeg") is not None

    notes: list[str] = []
    if ram_total_gb >= 24:
        mode = "32gb_workstation"
        model = "qwen2.5:14b-instruct-q4_K_M"
        max_agents = 5
    elif ram_total_gb >= 14:
        mode = "16gb_hybrid"
        model = "qwen2.5:7b-instruct-q4_K_M"
        max_agents = 3
    else:
        mode = "8gb_cpu_optimized"
        model = "qwen2.5:3b-instruct-q4_K_M"
        max_agents = 2
        notes.append("8GB-class host detected: use serialized single-model loading and 4-bit quantized models.")

    if not ollama.get("reachable"):
        notes.append("Ollama daemon not detected; offline job queue and deterministic fallbacks are active at $0 cost.")
    if not ffmpeg_ok:
        notes.append("FFmpeg not found on PATH; media probing will use basic file-size fallback.")

    return BenchmarkResponse(
        ram_total_gb=ram_total_gb,
        ram_available_gb=ram_avail_gb,
        cpu_cores=cpu_cores,
        disk_free_gb=disk_free_gb,
        recommended_mode=mode,
        recommended_ollama_model=model,
        recommended_max_concurrent_agents=max_agents,
        zero_cost_default=True,
        ollama_reachable=bool(ollama.get("reachable")),
        ollama_models=list(ollama.get("models", [])),
        ffmpeg_available=ffmpeg_ok,
        notes=notes,
    )
