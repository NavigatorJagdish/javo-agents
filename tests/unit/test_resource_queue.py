"""Async worker lifecycle coverage; requires a functioning asyncio environment."""
import asyncio
import pytest
from app.core.resource_manager import ResourceManager
from app.core.control_state import ControlStateStore


@pytest.mark.asyncio
async def test_worker_survives_factory_exception(monkeypatch, tmp_path):
    manager = ResourceManager(ControlStateStore(str(tmp_path / "control.json")))
    manager.resume()
    manager._max_concurrent = 1
    monkeypatch.setattr(manager, "can_accept_work", lambda: (True, "OK"))
    def broken(): raise ValueError("factory failed")
    async def good(): return "done"
    try:
        with pytest.raises(ValueError, match="factory failed"):
            await asyncio.wait_for(manager.submit_task("bad", broken), 2)
        assert await asyncio.wait_for(manager.submit_task("good", good), 2) == "done"
        assert len(manager._workers) == 1
        assert not manager._futures
    finally:
        await manager.stop_worker()


@pytest.mark.asyncio
async def test_emergency_stop_cancels_running_and_queued(monkeypatch, tmp_path):
    manager = ResourceManager(ControlStateStore(str(tmp_path / "control.json")))
    manager.resume()
    manager._max_concurrent = 1
    monkeypatch.setattr(manager, "can_accept_work", lambda: (True, "OK"))
    started = asyncio.Event()
    blocked = asyncio.Event()
    ran_second = []
    async def first():
        started.set()
        await blocked.wait()
    async def second(): ran_second.append(True)
    try:
        one = asyncio.create_task(manager.submit_task("one", first))
        await asyncio.wait_for(started.wait(), 2)
        two = asyncio.create_task(manager.submit_task("two", second))
        await asyncio.sleep(0)
        manager.trigger_emergency_stop()
        results = await asyncio.wait_for(asyncio.gather(one, two, return_exceptions=True), 2)
        assert all(isinstance(result, RuntimeError) for result in results)
        assert not ran_second
    finally:
        await manager.stop_worker()


@pytest.mark.asyncio
async def test_fixed_workers_limit_active_work(monkeypatch, tmp_path):
    manager = ResourceManager(ControlStateStore(str(tmp_path / "control.json")))
    manager.resume()
    manager._max_concurrent = 2
    monkeypatch.setattr(manager, "can_accept_work", lambda: (True, "OK"))
    release = asyncio.Event()
    two_running = asyncio.Event()
    active = 0
    peak = 0
    async def work():
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        if active == 2: two_running.set()
        try: await release.wait()
        finally: active -= 1
    try:
        tasks = [asyncio.create_task(manager.submit_task(str(i), work)) for i in range(8)]
        await asyncio.wait_for(two_running.wait(), 2)
        assert len(manager._workers) == 2
        assert len(manager._executions) == 2
        release.set()
        await asyncio.wait_for(asyncio.gather(*tasks), 2)
        assert peak == 2
    finally:
        await manager.stop_worker()
