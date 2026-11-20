"""Shared local control handlers used by API and Telegram."""
from app.core.resource_manager import get_resource_manager
from app.core.scheduler import scheduler


def pause_runtime() -> None:
    try:
        get_resource_manager().pause()
    finally:
        if scheduler.is_running:
            scheduler._scheduler.pause()


def stop_runtime() -> int:
    try:
        return get_resource_manager().trigger_emergency_stop()
    finally:
        if scheduler.is_running:
            scheduler._scheduler.pause()


def resume_runtime() -> None:
    manager = get_resource_manager()
    # Overdue jobs remain held, including jobs missed during a long pause.
    if scheduler.is_running:
        scheduler._reconcile_jobs()
    manager.resume()
    try:
        if scheduler.is_running:
            scheduler._scheduler.resume()
    except Exception:
        manager.pause()
        raise
