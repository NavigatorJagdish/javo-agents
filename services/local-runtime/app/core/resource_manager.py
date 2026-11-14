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
from app.core.resource_profiles import select_resource_profile
from app.core.control_state import ControlState, ControlStateStore

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

    def __init__(self, state_store: ControlStateStore | None = None):
        settings = get_settings()
        self.profile = select_resource_profile(
            psutil.virtual_memory().total / (1024 * 1024),
            psutil.cpu_count() or 1,
            settings.resource_profile,
            settings.max_concurrent_agents,
            settings.memory_headroom_mb,
        )
        self._max_concurrent = self.profile.max_concurrent_agents
        self._active_tasks: set[str] = set()
        self._pending_ids: set[str] = set()
        self._futures: dict[str, asyncio.Future] = {}
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=settings.max_queue_size)
        self._loaded_models: dict[str, datetime] = {}
        self._workers: list[asyncio.Task] = []
        self._executions: dict[str, asyncio.Task] = {}
        self._state_store = state_store or ControlStateStore(settings.control_state_path)
        state = self._state_store.load()
        self._emergency_stopped = state.emergency_stopped
        self._paused = state.paused
        self._closing = False
        self._loop = None
        self._resume_event: Optional[asyncio.Event] = None

    def start_worker(self) -> None:
        loop = asyncio.get_running_loop()
        if self._workers and any(not w.done() for w in self._workers):
            if self._loop is not loop:
                raise RuntimeError("Resource manager is running on another event loop")
            return
        self._loop = loop
        self._closing = False
        self._queue = asyncio.Queue(maxsize=get_settings().max_queue_size)
        self._resume_event = asyncio.Event()
        if not self._paused and not self._emergency_stopped:
            self._resume_event.set()
        self._workers = [
            asyncio.create_task(self._process_queue(), name=f"javo-worker-{i}")
            for i in range(self._max_concurrent)
        ]

    def _drain_queue(self, reason: str) -> int:
        drained = 0
        while True:
            try:
                task_id, _, future = self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            if not future.done():
                future.set_exception(RuntimeError(reason))
            self._pending_ids.discard(task_id)
            self._futures.pop(task_id, None)
            self._queue.task_done()
            drained += 1
        return drained

    async def stop_worker(self) -> None:
        self._closing = True
        self._drain_queue("Resource manager stopped")
        tasks = [*self._executions.values(), *self._workers]
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._workers.clear()
        self._executions.clear()
        self._active_tasks.clear()
        self._pending_ids.clear()
        self._futures.clear()

    def get_metrics(self) -> SystemMetrics:
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
            queued_tasks=len(self._pending_ids) - len(self._active_tasks),
            loaded_models=list(self._loaded_models),
        )

    def can_accept_work(self) -> tuple[bool, str]:
        if self._emergency_stopped:
            return False, "System is in emergency stop state"
        if self._paused or self._closing:
            return False, "System is paused or shutting down"
        settings = get_settings()
        metrics = self.get_metrics()
        if metrics.cpu_percent > settings.cpu_limit_percent:
            return False, f"CPU usage too high ({metrics.cpu_percent:.1f}%)"
        if (metrics.memory_percent > settings.memory_limit_percent
                or metrics.memory_available_mb < self.profile.memory_headroom_mb):
            return False, "Insufficient RAM headroom"
        if self._queue.full():
            return False, "Execution queue is full"
        return True, "OK"

    async def submit_task(self, task_id: str, coro_factory: Callable[[], Awaitable[Any]]) -> Any:
        if not task_id or task_id in self._pending_ids:
            raise ValueError("Task ID is empty or already queued/running")
        allowed, reason = self.can_accept_work()
        if not allowed:
            raise RuntimeError(reason)
        if not self._workers or not any(not w.done() for w in self._workers):
            self.start_worker()
        future = asyncio.get_running_loop().create_future()
        # Nonblocking admission keeps queue bounds real and does not leave producers
        # stuck behind a stop. Workers never fan out an unbounded set of tasks.
        self._queue.put_nowait((task_id, coro_factory, future))
        self._pending_ids.add(task_id)
        self._futures[task_id] = future
        try:
            return await future
        except asyncio.CancelledError:
            execution = self._executions.get(task_id)
            if execution:
                execution.cancel()
            raise

    async def _process_queue(self) -> None:
        while True:
            await self._resume_event.wait()
            task_id, coro_factory, future = await self._queue.get()
            try:
                await self._resume_event.wait()
                if future.done():
                    continue
                if self._emergency_stopped or self._closing:
                    future.set_exception(RuntimeError("Execution stopped"))
                    continue
                self._active_tasks.add(task_id)
                try:
                    execution = asyncio.ensure_future(coro_factory())
                    self._executions[task_id] = execution
                    result = await execution
                    if not future.done():
                        future.set_result(result)
                except asyncio.CancelledError:
                    if not future.done():
                        future.set_exception(RuntimeError("Execution cancelled"))
                    if self._closing:
                        raise
                except Exception as exc:
                    if not future.done():
                        future.set_exception(exc)
            finally:
                if not future.done():
                    future.set_exception(RuntimeError("Worker stopped"))
                self._executions.pop(task_id, None)
                self._active_tasks.discard(task_id)
                self._pending_ids.discard(task_id)
                self._futures.pop(task_id, None)
                self._queue.task_done()

    def pause(self) -> None:
        self._paused = True
        if self._resume_event:
            self._resume_event.clear()
        self._state_store.save(ControlState(True, self._emergency_stopped))

    def resume(self) -> None:
        # Persist before releasing any queued work. Failed writes keep it held.
        self._state_store.save(ControlState(False, False))
        self._paused = False
        self._emergency_stopped = False
        if self._resume_event:
            self._resume_event.set()

    async def load_ollama_model(self, model_name: str) -> dict[str, Any]:
        """Warm/load an Ollama model into memory."""
        settings = get_settings()
        url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(url, json={"model": model_name, "keep_alive": "10m", "stream": False})
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
        """Cancel queued/cooperative in-flight work; remote side effects cannot be undone."""
        self._emergency_stopped = True
        self._paused = True
        if self._resume_event:
            self._resume_event.clear()
        drained = self._drain_queue("Cancelled by emergency stop")
        for future in self._futures.values():
            if not future.done():
                future.set_exception(RuntimeError("Cancelled by emergency stop"))
        for execution in self._executions.values():
            execution.cancel()
        self._state_store.save(ControlState(True, True))
        logger.critical("Emergency stop: %d queued tasks cancelled", drained)
        return drained

    def clear_emergency_stop(self) -> None:
        self.resume()


_resource_manager: Optional[ResourceManager] = None


def get_resource_manager() -> ResourceManager:
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager()
    return _resource_manager
