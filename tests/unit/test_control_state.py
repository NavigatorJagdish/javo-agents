"""Real file persistence and failure behavior; no event-loop simulation."""
import json
import pytest
from app.core.control_state import ControlState, ControlStateStore
from app.core.resource_manager import ResourceManager


def manager(path):
    return ResourceManager(ControlStateStore(str(path)))


def test_first_start_is_paused(tmp_path):
    runtime = manager(tmp_path / "control.json")
    assert runtime._paused and not runtime._emergency_stopped
    assert not runtime.can_accept_work()[0]


def test_pause_and_resume_survive_new_manager(tmp_path):
    path = tmp_path / "control.json"
    runtime = manager(path)
    runtime.resume()
    assert not manager(path)._paused
    runtime.pause()
    assert manager(path)._paused
    runtime.resume()
    restored = manager(path)
    assert not restored._paused and not restored._emergency_stopped


def test_emergency_stop_survives_new_manager(tmp_path):
    path = tmp_path / "control.json"
    runtime = manager(path)
    runtime.resume()
    runtime.trigger_emergency_stop()
    restored = manager(path)
    assert restored._paused and restored._emergency_stopped
    restored.resume()
    assert not manager(path)._emergency_stopped


@pytest.mark.parametrize("payload", ['broken', '[]', '{"version":1,"paused":"false","emergency_stopped":false}', '{"version":1,"paused":false,"emergency_stopped":true}'])
def test_corruption_holds_runtime(tmp_path, payload):
    path = tmp_path / "control.json"
    path.write_text(payload)
    runtime = manager(path)
    assert runtime._paused and runtime._emergency_stopped
    assert runtime._state_store.load_error


def test_resume_write_failure_keeps_work_held(tmp_path, monkeypatch):
    runtime = manager(tmp_path / "control.json")
    def fail(state): raise OSError("disk full")
    monkeypatch.setattr(runtime._state_store, "save", fail)
    with pytest.raises(OSError): runtime.resume()
    assert runtime._paused


def test_emergency_write_failure_still_stops_memory_state(tmp_path, monkeypatch):
    runtime = manager(tmp_path / "control.json")
    runtime.resume()
    def fail(state): raise OSError("disk full")
    monkeypatch.setattr(runtime._state_store, "save", fail)
    with pytest.raises(OSError): runtime.trigger_emergency_stop()
    assert runtime._paused and runtime._emergency_stopped


def test_atomic_replace_failure_retains_previous_stop(tmp_path, monkeypatch):
    from app.core import control_state
    path = tmp_path / "control.json"
    store = ControlStateStore(str(path))
    store.save(ControlState(True, True))
    def fail(*args): raise OSError("replace failed")
    monkeypatch.setattr(control_state.os, "replace", fail)
    with pytest.raises(OSError): store.save(ControlState(False, False))
    assert store.load() == ControlState(True, True)
    assert not list(tmp_path.glob("*.tmp"))


def test_pause_still_holds_scheduler_on_storage_failure(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from app.core import runtime_control
    runtime = manager(tmp_path / "control.json")
    runtime.resume()
    held = []
    def fail(state): raise OSError("disk full")
    monkeypatch.setattr(runtime._state_store, "save", fail)
    monkeypatch.setattr(runtime_control, "get_resource_manager", lambda: runtime)
    monkeypatch.setattr(runtime_control, "scheduler", SimpleNamespace(is_running=True, _scheduler=SimpleNamespace(pause=lambda: held.append(True))))
    with pytest.raises(OSError): runtime_control.pause_runtime()
    assert runtime._paused and held == [True]


def test_scheduler_resume_failure_restores_durable_pause(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from app.core import runtime_control
    path = tmp_path / "control.json"
    runtime = manager(path)
    reconciled = []
    def fail(): raise RuntimeError("scheduler unavailable")
    monkeypatch.setattr(runtime_control, "get_resource_manager", lambda: runtime)
    monkeypatch.setattr(runtime_control, "scheduler", SimpleNamespace(is_running=True,
        _reconcile_jobs=lambda: reconciled.append(True), _scheduler=SimpleNamespace(resume=fail)))
    with pytest.raises(RuntimeError): runtime_control.resume_runtime()
    assert reconciled == [True]
    assert runtime._paused and manager(path)._paused
