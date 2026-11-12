"""APScheduler integration with persistent job store and restart reconciliation."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Callable, Optional

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, EVENT_JOB_MISSED
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings

logger = logging.getLogger(__name__)


class SchedulerService:
    """Persistent job scheduler with reconciliation after restart."""

    def __init__(self):
        self._scheduler: Optional[AsyncIOScheduler] = None
        self._job_history: list[dict] = []
        self._missed_jobs: list[dict] = []

    @property
    def is_running(self) -> bool:
        return self._scheduler is not None and self._scheduler.running

    @property
    def running(self) -> bool:
        return self.is_running

    def initialize(self) -> None:
        """Initialize the scheduler with persistent job store."""
        settings = get_settings()

        jobstores = {
            "default": SQLAlchemyJobStore(url=settings.scheduler_db_url),
        }
        executors = {
            "default": AsyncIOExecutor(),
        }
        job_defaults = {
            "coalesce": True,
            "max_instances": 3,
            "misfire_grace_time": 3600,  # 1 hour grace for misfires
        }

        self._scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone="UTC",
        )

        # Event listeners
        self._scheduler.add_listener(self._on_job_executed, EVENT_JOB_EXECUTED)
        self._scheduler.add_listener(self._on_job_error, EVENT_JOB_ERROR)
        self._scheduler.add_listener(self._on_job_missed, EVENT_JOB_MISSED)

        logger.info("Scheduler initialized with persistent job store")

    def start(self) -> None:
        """Start the scheduler and reconcile any missed jobs."""
        if self._scheduler is None:
            self.initialize()

        self._scheduler.start()
        logger.info("Scheduler started")

        # Reconcile after restart
        self._reconcile_jobs()

    def shutdown(self, wait: bool = True) -> None:
        """Shut down the scheduler."""
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown(wait=wait)
            logger.info("Scheduler shut down")

    def _reconcile_jobs(self) -> None:
        """Check for jobs that may have been missed during downtime."""
        jobs = self._scheduler.get_jobs()
        now = datetime.now(timezone.utc)
        reconciled = 0

        for job in jobs:
            if job.next_run_time and job.next_run_time < now:
                logger.warning(
                    f"Job '{job.id}' missed its scheduled time "
                    f"({job.next_run_time}). Rescheduling."
                )
                self._missed_jobs.append({
                    "job_id": job.id,
                    "scheduled_time": job.next_run_time.isoformat(),
                    "detected_at": now.isoformat(),
                })
                # APScheduler's misfire_grace_time handles re-execution
                reconciled += 1

        if reconciled:
            logger.info(f"Reconciled {reconciled} missed jobs after restart")

    def add_interval_job(
        self,
        func: Callable,
        job_id: str,
        seconds: int = 0,
        minutes: int = 0,
        hours: int = 0,
        kwargs: Optional[dict] = None,
        replace_existing: bool = True,
    ) -> str:
        """Add a recurring interval job."""
        if not self._scheduler:
            self.initialize()

        job = self._scheduler.add_job(
            func,
            trigger=IntervalTrigger(seconds=seconds, minutes=minutes, hours=hours),
            id=job_id,
            kwargs=kwargs or {},
            replace_existing=replace_existing,
        )
        logger.info(f"Added interval job: {job_id}")
        return job.id

    def add_cron_job(
        self,
        func: Callable,
        job_id: str,
        cron_expression: Optional[str] = None,
        hour: Optional[int] = None,
        minute: Optional[int] = None,
        day_of_week: Optional[str] = None,
        kwargs: Optional[dict] = None,
        replace_existing: bool = True,
    ) -> str:
        """Add a cron-based scheduled job."""
        if not self._scheduler:
            self.initialize()

        if cron_expression:
            parts = cron_expression.split()
            trigger = CronTrigger(
                minute=parts[0] if len(parts) > 0 else None,
                hour=parts[1] if len(parts) > 1 else None,
                day=parts[2] if len(parts) > 2 else None,
                month=parts[3] if len(parts) > 3 else None,
                day_of_week=parts[4] if len(parts) > 4 else None,
            )
        else:
            trigger = CronTrigger(
                hour=hour, minute=minute, day_of_week=day_of_week
            )

        job = self._scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            kwargs=kwargs or {},
            replace_existing=replace_existing,
        )
        logger.info(f"Added cron job: {job_id}")
        return job.id

    def add_one_time_job(
        self,
        func: Callable,
        job_id: str,
        run_at: datetime,
        kwargs: Optional[dict] = None,
    ) -> str:
        """Add a one-time job to run at a specific time."""
        if not self._scheduler:
            self.initialize()

        job = self._scheduler.add_job(
            func,
            trigger=DateTrigger(run_date=run_at),
            id=job_id,
            kwargs=kwargs or {},
            replace_existing=True,
        )
        logger.info(f"Added one-time job: {job_id} at {run_at}")
        return job.id

    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job."""
        try:
            self._scheduler.remove_job(job_id)
            logger.info(f"Removed job: {job_id}")
            return True
        except Exception as e:
            logger.warning(f"Could not remove job {job_id}: {e}")
            return False

    def pause_job(self, job_id: str) -> bool:
        """Pause a job."""
        try:
            self._scheduler.pause_job(job_id)
            logger.info(f"Paused job: {job_id}")
            return True
        except Exception:
            return False

    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job."""
        try:
            self._scheduler.resume_job(job_id)
            logger.info(f"Resumed job: {job_id}")
            return True
        except Exception:
            return False

    def get_jobs(self) -> list[dict]:
        """Get all scheduled jobs."""
        if not self._scheduler:
            return []

        jobs = []
        for job in self._scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
                "pending": job.pending,
            })
        return jobs

    def get_job(self, job_id: str) -> Optional[dict]:
        """Get a specific job's details."""
        job = self._scheduler.get_job(job_id)
        if not job:
            return None
        return {
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger),
            "pending": job.pending,
        }

    def get_history(self, limit: int = 50) -> list[dict]:
        """Get recent job execution history."""
        return self._job_history[-limit:]

    def get_missed_jobs(self) -> list[dict]:
        """Get list of jobs that were missed during downtime."""
        return self._missed_jobs

    def _on_job_executed(self, event) -> None:
        """Handle successful job execution."""
        self._job_history.append({
            "job_id": event.job_id,
            "status": "success",
            "scheduled_time": event.scheduled_run_time.isoformat() if event.scheduled_run_time else None,
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "retval": str(event.retval) if event.retval else None,
        })
        logger.info(f"Job executed successfully: {event.job_id}")

    def _on_job_error(self, event) -> None:
        """Handle job execution error."""
        self._job_history.append({
            "job_id": event.job_id,
            "status": "error",
            "scheduled_time": event.scheduled_run_time.isoformat() if event.scheduled_run_time else None,
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "error": str(event.exception),
        })
        logger.error(f"Job error: {event.job_id} - {event.exception}")

    def _on_job_missed(self, event) -> None:
        """Handle missed job."""
        self._missed_jobs.append({
            "job_id": event.job_id,
            "scheduled_time": event.scheduled_run_time.isoformat() if event.scheduled_run_time else None,
            "detected_at": datetime.now(timezone.utc).isoformat(),
        })
        logger.warning(f"Job missed: {event.job_id}")


# Singleton
_scheduler: Optional[SchedulerService] = None


def get_scheduler() -> SchedulerService:
    """Get or create the scheduler singleton."""
    global _scheduler
    if _scheduler is None:
        _scheduler = SchedulerService()
    return _scheduler


scheduler = get_scheduler()
