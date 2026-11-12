"""Unit tests for SchedulerService persistent job store and job management."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.core.scheduler import SchedulerService


async def _dummy_job(label: str = "test") -> str:
    return f"ran:{label}"


@pytest.mark.asyncio
async def test_scheduler_add_list_pause_remove(tmp_path, monkeypatch):
    """Verify interval, cron, and one-time jobs persist and manage cleanly."""
    db_file = tmp_path / "test_sched.db"
    monkeypatch.setenv("JAVO_SCHEDULER_DB_URL", f"sqlite:///{db_file}")

    # Reset settings cache so monkeypatched env takes effect
    import app.config as cfg
    cfg._settings = None

    sched = SchedulerService()
    sched.initialize()
    sched.start()
    try:
        j1 = sched.add_interval_job(_dummy_job, job_id="interval-1", seconds=60, kwargs={"label": "a"})
        j2 = sched.add_cron_job(_dummy_job, job_id="cron-1", cron_expression="0 9 * * *")
        j3 = sched.add_one_time_job(
            _dummy_job,
            job_id="once-1",
            run_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        assert j1 == "interval-1"
        assert j2 == "cron-1"
        assert j3 == "once-1"
        assert sched.running is True

        jobs = sched.get_jobs()
        ids = {j["id"] for j in jobs}
        assert {"interval-1", "cron-1", "once-1"}.issubset(ids)

        assert sched.pause_job("interval-1") is True
        assert sched.resume_job("interval-1") is True
        assert sched.remove_job("once-1") is True
        assert sched.get_job("once-1") is None
    finally:
        sched.shutdown(wait=False)
        cfg._settings = None
