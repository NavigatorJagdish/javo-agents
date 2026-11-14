"""Fault injection for cleanup ordering, not a real service startup test."""
from types import SimpleNamespace
import pytest
from app import main


def complete(coro):
    try: coro.send(None)
    except StopIteration as result: return result.value
    finally: coro.close()
    raise AssertionError("Unexpected asynchronous IO in lifecycle fault injection")


@pytest.mark.parametrize("failure,expected", [
    ("db_start", ["db_close"]),
    ("tables", ["db_close"]),
    ("worker_start", ["worker_stop", "db_close"]),
    ("scheduler_start", ["scheduler_stop", "worker_stop", "db_close"]),
    ("watcher_start", ["watcher_stop", "scheduler_stop", "worker_stop", "db_close"]),
    ("watcher_stop", ["watcher_stop", "scheduler_stop", "worker_stop", "db_close"]),
    (None, ["watcher_stop", "scheduler_stop", "worker_stop", "db_close"]),
])
def test_partial_start_and_cleanup_failures_release_resources(monkeypatch, failure, expected):
    events = []
    def sync(name):
        def call(*args, **kwargs):
            events.append(name)
            if name == failure: raise RuntimeError(name)
        return call
    def asynchronous(name):
        async def call(*args, **kwargs):
            events.append(name)
            if name == failure: raise RuntimeError(name)
        return call
    monkeypatch.setattr(main, "_ensure_directories", lambda: None)
    monkeypatch.setattr(main, "init_engine", sync("db_start"))
    monkeypatch.setattr(main, "create_tables", asynchronous("tables"))
    monkeypatch.setattr(main, "_seed_agents", asynchronous("seed"))
    monkeypatch.setattr(main, "close_db", asynchronous("db_close"))
    monkeypatch.setattr(main, "get_resource_manager", lambda: SimpleNamespace(
        _paused=True, _emergency_stopped=False,
        start_worker=sync("worker_start"), stop_worker=asynchronous("worker_stop")))
    monkeypatch.setattr(main, "scheduler", SimpleNamespace(start=sync("scheduler_start"), shutdown=sync("scheduler_stop")))
    monkeypatch.setattr(main, "get_content_watcher", lambda: SimpleNamespace(start_watching=sync("watcher_start"), stop=sync("watcher_stop")))
    context = main.lifespan(None)
    if failure and failure != "watcher_stop":
        with pytest.raises(RuntimeError, match=failure): complete(context.__aenter__())
    else:
        complete(context.__aenter__())
        if failure:
            with pytest.raises(RuntimeError, match=failure): complete(context.__aexit__(None, None, None))
        else: complete(context.__aexit__(None, None, None))
    assert [event for event in events if event.endswith(("stop", "close"))] == expected
