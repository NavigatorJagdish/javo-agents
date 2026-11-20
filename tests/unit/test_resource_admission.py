"""Admission rejects deterministic pressure; test fixtures never weaken runtime policy."""
import asyncio
from dataclasses import replace

import pytest

from app.core.control_state import ControlStateStore
from app.core.resource_manager import ResourceManager, SystemMetrics


@pytest.mark.asyncio
async def test_insufficient_memory_rejects_work_before_factory_runs(tmp_path, monkeypatch):
    manager = ResourceManager(ControlStateStore(str(tmp_path / 'control.json')))
    manager.resume()
    metrics = SystemMetrics(0, 25, 0, 8192, 10, 100, 0, 0)
    monkeypatch.setattr(manager, 'get_metrics', lambda: metrics)
    executed = False

    async def work():
        nonlocal executed
        executed = True

    with pytest.raises(RuntimeError, match='RAM headroom'):
        await manager.submit_task('no-memory', work)
    assert not executed and not manager._workers
    metrics = replace(metrics, memory_available_mb=8192, memory_percent=99)
    assert manager.can_accept_work() == (False, 'Insufficient RAM headroom')
    metrics = replace(metrics, memory_percent=25, cpu_percent=99)
    assert manager.can_accept_work()[0] is False
    metrics = replace(metrics, cpu_percent=0)
    assert manager.can_accept_work() == (True, 'OK')
    manager.pause()
    assert manager.can_accept_work()[0] is False
    await asyncio.sleep(0)
