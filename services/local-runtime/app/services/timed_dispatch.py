"""Explicitly armed timed simulations. Missed work is held, never catch-up posted."""
from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import select, update, or_
from sqlalchemy.exc import IntegrityError

from app import database as db
from app.core.resource_manager import get_resource_manager
from app.models.content import ScheduleStatus
from app.models.publication import PublicationApproval, PublicationAttempt, PublicationTimer
from app.services.publishing import load_snapshot, fingerprint_payload, dispatch_schedule

logger = logging.getLogger(__name__)
GRACE_SECONDS = 30


def utc_naive(value: datetime) -> datetime:
    # SQLite stores schedule timestamps as UTC without timezone metadata.
    return value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else value


def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def timer_receipt(timer: PublicationTimer) -> dict:
    return {"schedule_id": timer.schedule_id, "state": timer.state,
            "due_at": timer.due_at.replace(tzinfo=timezone.utc).isoformat(),
            "reason": timer.reason, "simulation_only": True}


async def arm_timer(session, schedule_id: str, fingerprint: str, *, now=None) -> dict:
    schedule, snapshot = await load_snapshot(session, schedule_id)
    approval = await session.get(PublicationApproval, schedule_id)
    if (schedule.status != ScheduleStatus.APPROVED or approval is None
            or approval.mode != "mock" or approval.fingerprint != fingerprint
            or fingerprint_payload(snapshot) != fingerprint):
        raise HTTPException(409, "Review and approve this exact snapshot for simulation first")
    due_at = utc_naive(schedule.scheduled_at)
    if due_at <= utc_naive(now or now_utc()):
        raise HTTPException(409, "Missed schedule: create a new future schedule and review it")
    if (await session.execute(select(PublicationAttempt).where(
            PublicationAttempt.schedule_id == schedule_id))).scalar_one_or_none():
        raise HTTPException(409, "Dispatch already attempted; inspect its receipt")
    timer = await session.get(PublicationTimer, schedule_id)
    if timer and timer.state in {"executing", "simulated"}:
        raise HTTPException(409, "Timer already dispatched or unresolved")
    if timer is None:
        timer = PublicationTimer(schedule_id=schedule_id)
        session.add(timer)
        timer.fingerprint, timer.due_at = fingerprint, due_at
        timer.state, timer.reason = "armed", None
    else:
        changed = await session.execute(update(PublicationTimer).where(
            PublicationTimer.schedule_id == schedule_id,
            PublicationTimer.state.in_(["armed", "held", "cancelled"]),
        ).values(fingerprint=fingerprint, due_at=due_at, state="armed", reason=None))
        if changed.rowcount != 1:
            await session.rollback()
            raise HTTPException(409, "Timer was claimed concurrently; reload its status")
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(409, "Timer changed concurrently; reload its status") from None
    return timer_receipt(timer)


async def cancel_timer(session, schedule_id: str) -> dict:
    timer = await session.get(PublicationTimer, schedule_id)
    if timer is None:
        raise HTTPException(404, "No timer exists")
    changed = await session.execute(update(PublicationTimer).where(
        PublicationTimer.schedule_id == schedule_id,
        PublicationTimer.state.in_(["armed", "held", "cancelled"]),
    ).values(state="cancelled", reason="Cancelled by owner"))
    await session.commit()
    if changed.rowcount != 1:
        raise HTTPException(409, "Dispatch is in progress or finished; inspect receipt")
    timer.state, timer.reason = "cancelled", "Cancelled by owner"
    return timer_receipt(timer)


async def hold_after_restart(session, *, now=None) -> None:
    await session.execute(update(PublicationTimer).where(or_(
        PublicationTimer.state == "executing",
        (PublicationTimer.state == "armed") & (PublicationTimer.due_at <= utc_naive(now or now_utc())),
    )).values(state="held", reason="Runtime restarted after due time or during dispatch; review receipt and create a new schedule"))
    await session.commit()


async def run_due(session, *, now=None) -> None:
    current = utc_naive(now or now_utc())
    timer_ids = (await session.execute(select(PublicationTimer.schedule_id).where(
        PublicationTimer.state == "armed", PublicationTimer.due_at <= current,
    ).order_by(PublicationTimer.due_at, PublicationTimer.schedule_id).limit(20))).scalars().all()
    for timer_id in timer_ids:
        timer = await session.get(PublicationTimer, timer_id)
        if timer is None or timer.state != "armed":
            continue
        current = utc_naive(now) if now is not None else now_utc()
        manager = get_resource_manager()
        reason = None
        if manager._paused or manager._emergency_stopped:
            reason = "Automation paused or stopped at due time; create a new schedule"
        elif current - timer.due_at > timedelta(seconds=GRACE_SECONDS):
            reason = "Schedule exceeded dispatch grace period; create a new schedule"
        if reason:
            await session.execute(update(PublicationTimer).where(
                PublicationTimer.schedule_id == timer.schedule_id, PublicationTimer.state == "armed",
            ).values(state="held", reason=reason))
            await session.commit()
            continue
        # Persist an exclusive claim before invoking the shared approval/dispatch policy.
        claimed = await session.execute(update(PublicationTimer).where(
            PublicationTimer.schedule_id == timer.schedule_id, PublicationTimer.state == "armed",
        ).values(state="executing"))
        await session.commit()
        if claimed.rowcount != 1:
            continue
        try:
            _, snapshot = await load_snapshot(session, timer.schedule_id)
            approval = await session.get(PublicationApproval, timer.schedule_id)
            if (fingerprint_payload(snapshot) != timer.fingerprint or approval is None
                    or approval.fingerprint != timer.fingerprint or approval.mode != "mock"):
                raise HTTPException(409, "Armed snapshot changed")
            result = await dispatch_schedule(session, timer.schedule_id)
            timer.state, timer.reason = "simulated", result["message"]
        except Exception:
            await session.rollback()
            timer = await session.get(PublicationTimer, timer_id)
            timer.state, timer.reason = "held", "Dispatch blocked or unconfirmed; inspect approval and receipt"
        await session.commit()


class TimedDispatchWorker:
    def __init__(self):
        self._task = None

    async def start(self):
        if self._task is not None:
            return
        async with db.async_session_factory() as session:
            await hold_after_restart(session)
        self._task = asyncio.create_task(self._run(), name="javo-timed-simulation")

    async def _run(self):
        while True:
            try:
                async with db.async_session_factory() as session:
                    await run_due(session)
            except Exception:
                # An executing marker survives failures and is held on next startup.
                logger.error("Timed dispatch check failed; inspect saved timer/receipt status")
            await asyncio.sleep(5)

    async def stop(self):
        if self._task is not None:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None


timed_worker = TimedDispatchWorker()
