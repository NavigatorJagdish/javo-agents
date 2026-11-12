"""Resource manager: CPU/RAM monitoring, model loading/unloading, queue-based scheduling."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Optional

import httpx
import psutil

from app.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    memory_total_mb: float
    disk_percent: float
    disk_free_gb: float
    active_tasks: int
    queued_tasks: int
    loaded_models: list[str] = field(default_factory=list)


class ResourceManager:
    """Monitors host hardware resources and enforces concurrency/model limits."""

    def __init__(self):
        settings = get_settings()
        self._max_concurrent = settings.max_concurrent_agents
        self._semaphore = asyncio.Semaphore(self._max_concurrent)
        self._active_tasks: set[str] = set()
        self._queue: asyncio.Queue[tuple[str, Callable[[], Awaitable[Any]], asyncio.Future]] = (
            asyncio.Queue(maxsize=settings.max_queue_size)
        )
        self._loaded_models: dict[str, datetime] = {}
        self._worker_task: Optional[asyncio.Task] = None
        self._emergency_stopped: bool = False

    def start_worker(self) -> None:
        loop = asyncio.get_running_loop()
        if getattr(self, "_loop", None) is not loop:
            settings = get_settings()
            self._semaphore = asyncio.Semaphore(self._max_concurrent)
            self._queue = asyncio.Queue(maxsize=settings.max_queue_size)
            self._loop = loop
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._process_queue())
            logger.info("ResourceManager queue worker started (max_concurrent=%d)", self._max_concurrent)

    async def stop_worker(self) -> None:
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            logger.info("ResourceManager queue worker stopped")

    def get_metrics(self) -> SystemMetrics:
        """Collect current CPU, RAM, disk, and queue metrics."""
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage(".")
        return SystemMetrics(
            cpu_percent=psutil.cpu_percent(interval=None),
            memory_percent=mem.percent,
            memory_available_mb=round(mem.available / (1024 * 1024), 2),
            memory_total_mb=round(mem.total / (1024 * 1024), 2),
            disk_percent=disk.percent,
            disk_free_gb=round(disk.free / (1024 * 1024 * 1024), 2),
            active_tasks=len(self._active_tasks),
            queued_tasks=self._queue.qsize(),
            loaded_models=list(self._loaded_models.keys()),
        )

    def can_accept_work(self) -> tuple[bool, str]:
        """Check whether system resources allow accepting a new task."""
        if self._emergency_stopped:
            return False, "System is in emergency stop state"
        settings = get_settings()
        metrics = self.get_metrics()
        if metrics.cpu_percent > settings.cpu_limit_percent:
            return False, f"CPU usage too high ({metrics.cpu_percent:.1f}%)"
        if metrics.memory_percent > settings.memory_limit_percent:
            return False, f"RAM usage too high ({metrics.memory_percent:.1f}%)"
        if self._queue.full():
            return False, "Execution queue is full"
        return True, "OK"

    async def submit_task(self, task_id: str, coro_factory: Callable[[], Awaitable[Any]]) -> Any:
        """Queue a coroutine task and await its result under concurrency limits."""
        if self._emergency_stopped:
            raise RuntimeError("Cannot submit task during emergency stop")

        loop = asyncio.get_running_loop()
        future: asyncio.Future = loop.create_future()
        await self._queue.put((task_id, coro_factory, future))
        return await future

    async def _process_queue(self) -> None:
        while True:
            task_id, coro_factory, future = await self._queue.get()
            asyncio.create_task(self._run_with_semaphore(task_id, coro_factory, future))

    async def _run_with_semaphore(
        self,
        task_id: str,
        coro_factory: Callable[[], Awaitable[Any]],
        future: asyncio.Future,
    ) -> None:
        async with self._semaphore:
            self._active_tasks.add(task_id)
            try:
                result = await coro_factory()
                if not future.done():
                    future.set_result(result)
            except Exception as exc:
                if not future.done():
                    future.set_exception(exc)
            finally:
                self._active_tasks.discard(task_id)
                self._queue.task_done()

    async def load_ollama_model(self, model_name: str) -> dict[str, Any]:
        """Warm/load an Ollama model into memory."""
        settings = get_settings()
        url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(url, json={"model": model_name, "keep_alive": "10m"})
                res.raise_for_status()
            self._loaded_models[model_name] = datetime.now(timezone.utc)
            return {"status": "loaded", "model": model_name}
        except Exception as exc:
            logger.warning("Failed to load Ollama model %s: %s", model_name, exc)
            return {"status": "error", "model": model_name, "error": str(exc)}

    async def unload_ollama_model(self, model_name: str) -> dict[str, Any]:
        """Unload an Ollama model from RAM/VRAM by setting keep_alive=0."""
        settings = get_settings()
        url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, json={"model": model_name, "keep_alive": 0})
                res.raise_for_status()
            self._loaded_models.pop(model_name, None)
            return {"status": "unloaded", "model": model_name}
        except Exception as exc:
            logger.warning("Failed to unload Ollama model %s: %s", model_name, exc)
            return {"status": "error", "model": model_name, "error": str(exc)}

    def trigger_emergency_stop(self) -> int:
        """Block new work and drain pending queued tasks."""
        self._emergency_stopped = True
        drained = 0
        while not self._queue.empty():
            try:
                task_id, _, future = self._queue.get_nowait()
                if not future.done():
                    future.set_exception(RuntimeError("Cancelled by emergency stop"))
                self._queue.task_done()
                drained += 1
            except asyncio.QueueEmpty:
                break
        logger.critical("Emergency stop triggered! Drained %d queued tasks", drained)
        return drained

    def clear_emergency_stop(self) -> None:
        self._emergency_stopped = False
        logger.info("Emergency stop cleared")


_resource_manager: Optional[ResourceManager] = None


def get_resource_manager() -> ResourceManager:
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager()
    return _resource_manager
