"""Verify a disconnected owner tab cancels actual bounded worker inference."""
import asyncio

import pytest
from fastapi import HTTPException

from app.api.routes.voice import _await_connected
from app.core.control_state import ControlStateStore
from app.core.resource_manager import ResourceManager


@pytest.mark.asyncio
async def test_disconnect_cancels_running_model_request(tmp_path):
    manager = ResourceManager(ControlStateStore(str(tmp_path / 'control.json')))
    manager.resume()
    started = asyncio.Event()
    cancelled = asyncio.Event()

    async def infer():
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    class Tab:
        async def is_disconnected(self):
            return started.is_set()

    try:
        with pytest.raises(HTTPException) as error:
            await _await_connected(Tab(), manager.submit_task('disconnect-test', infer))
        assert error.value.status_code == 499
        await asyncio.wait_for(cancelled.wait(), 1)
        await asyncio.sleep(0)
        assert not manager._executions
    finally:
        await manager.stop_worker()


@pytest.mark.asyncio
async def test_emergency_stop_interrupts_companion_inference(tmp_path):
    manager = ResourceManager(ControlStateStore(str(tmp_path / 'control.json')))
    manager.resume()
    started = asyncio.Event()
    cancelled = asyncio.Event()

    async def infer():
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    class Tab:
        async def is_disconnected(self):
            return False

    request = asyncio.create_task(_await_connected(Tab(), manager.submit_task('stop-test', infer)))
    try:
        await asyncio.wait_for(started.wait(), 1)
        manager.trigger_emergency_stop()
        with pytest.raises(RuntimeError, match='emergency stop'):
            await request
        await asyncio.wait_for(cancelled.wait(), 1)
        assert manager._emergency_stopped
    finally:
        if not request.done():
            request.cancel()
        await asyncio.gather(request, return_exceptions=True)
        await manager.stop_worker()
