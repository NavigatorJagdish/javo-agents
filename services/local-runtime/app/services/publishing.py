"""Approved, durable publication dispatch. Live connectors remain fail-closed.

The existing connectors have not passed OAuth/capability verification. They must
not be silently enabled by this service. Explicit mock dispatch exercises the
workflow without presenting a simulated result as a real social publication.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.base import PostPayload
from app.connectors.mock import MockConnector
from app.core.resource_manager import get_resource_manager
from app.models.account import SocialAccount
from app.models.content import ContentAsset, ContentSchedule, ScheduleStatus
from app.models.publication import PublicationApproval, PublicationAttempt


def fingerprint_payload(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def load_snapshot(session: AsyncSession, schedule_id: str):
    schedule = await session.get(ContentSchedule, schedule_id)
    if schedule is None:
        raise HTTPException(404, "Schedule not found")
    asset = await session.get(ContentAsset, schedule.asset_id)
    account = await session.get(SocialAccount, schedule.account_id)
    if asset is None or account is None:
        raise HTTPException(409, "Content or destination account is missing")
    if asset.user_id != account.user_id:
        raise HTTPException(403, "Content and destination account have different owners")
    digest = None
    if asset.file_path:
        source = Path(asset.file_path)
        if not source.is_file():
            raise HTTPException(409, "Source media is unavailable")
        hasher = hashlib.sha256()
        with source.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
        digest = hasher.hexdigest()
    snapshot = {
        "asset_id": asset.id, "account_id": account.id,
        "platform": account.platform.value, "destination": account.platform_user_id,
        "caption": schedule.caption if schedule.caption is not None else (asset.content_text or ""),
        "hashtags": asset.hashtags or [], "media_type": asset.asset_type.value,
        "file_path": asset.file_path, "file_sha256": digest, "file_url": asset.file_url,
        "title": asset.title, "options": schedule.platform_options or {},
        "scheduled_at": schedule.scheduled_at.isoformat(),
    }
    return schedule, snapshot


async def approve_schedule(session: AsyncSession, schedule_id: str, mode: str, approver: str, expected_fingerprint: str | None = None) -> dict:
    if mode not in {"mock", "live"}:
        raise HTTPException(422, "Unknown dispatch mode")
    schedule, snapshot = await load_snapshot(session, schedule_id)
    if expected_fingerprint is not None and expected_fingerprint != fingerprint_payload(snapshot):
        raise HTTPException(409, "Preview changed; reload and review before approving")
    if schedule.status not in {ScheduleStatus.PENDING, ScheduleStatus.APPROVED}:
        raise HTTPException(409, "Schedule is not eligible for approval")
    attempted = (await session.execute(select(PublicationAttempt).where(
        PublicationAttempt.schedule_id == schedule_id
    ))).scalar_one_or_none()
    if attempted:
        raise HTTPException(409, "A dispatch attempt already exists; review its receipt")
    approval = await session.get(PublicationApproval, schedule_id)
    if approval is None:
        approval = PublicationApproval(schedule_id=schedule_id)
        session.add(approval)
    approval.fingerprint = fingerprint_payload(snapshot)
    approval.mode = mode
    approval.approved_by = approver
    schedule.status = ScheduleStatus.APPROVED
    schedule.approved_by = approver
    schedule.approved_at = datetime.now(timezone.utc)
    await session.commit()
    return {"schedule_id": schedule_id, "mode": mode, "status": "approved", "fingerprint": approval.fingerprint}


def receipt(attempt: PublicationAttempt) -> dict:
    return {
        "schedule_id": attempt.schedule_id, "publish_record_id": attempt.id,
        "status": attempt.state, "platform_post_id": attempt.post_id,
        "message": "Simulation only: no social media post was published." if attempt.mode == "mock"
        else "Dispatch outcome requires verification.",
    }


async def dispatch_schedule(session: AsyncSession, schedule_id: str) -> dict:
    manager = get_resource_manager()
    if manager._emergency_stopped or manager._paused:
        raise HTTPException(409, "Automation is paused or stopped")
    schedule, snapshot = await load_snapshot(session, schedule_id)
    approval = await session.get(PublicationApproval, schedule_id)
    if schedule.status != ScheduleStatus.APPROVED or approval is None:
        raise HTTPException(409, "Explicit content approval is required")
    if approval.fingerprint != fingerprint_payload(snapshot):
        raise HTTPException(409, "Content or destination changed; review and approve again")
    if approval.mode != "mock":
        raise HTTPException(503, "Live publishing unavailable until OAuth, permissions and connector capabilities are verified")
    existing = (await session.execute(select(PublicationAttempt).where(
        PublicationAttempt.schedule_id == schedule_id
    ))).scalar_one_or_none()
    if existing:
        if existing.state == "simulated":
            return receipt(existing)
        raise HTTPException(409, "Dispatch outcome is unresolved; automatic retry is blocked")
    # Ignore schedule ID/time for duplicate prevention across separately created schedules.
    identity = {k: v for k, v in snapshot.items() if k not in {"scheduled_at", "asset_id", "file_path"}}
    attempt = PublicationAttempt(
        id=str(uuid4()), schedule_id=schedule_id,
        dedupe_key=fingerprint_payload({"mode": approval.mode, "payload": identity}),
        state="dispatching", mode=approval.mode,
    )
    session.add(attempt)
    try:
        await session.commit()  # Durable intent exists before any connector side effect.
    except IntegrityError:
        await session.rollback()
        raise HTTPException(409, "Duplicate dispatch is already recorded") from None
    if manager._paused or manager._emergency_stopped:
        attempt.state = "cancelled"
        await session.commit()
        raise HTTPException(409, "Dispatch cancelled by pause/stop")
    attempt_id = attempt.id
    connector = MockConnector(account_id=snapshot["account_id"])
    try:
        result = await connector.publish_post(PostPayload(
            caption=snapshot["caption"], media_path=snapshot["file_path"],
            media_url=snapshot["file_url"], media_type=snapshot["media_type"],
            title=snapshot["title"], hashtags=snapshot["hashtags"],
        ))
        if not result.success or not result.post_id:
            raise RuntimeError("Connector did not provide a confirmed receipt")
        attempt.state = "simulated"
        attempt.post_id = result.post_id
        await session.commit()
    except Exception:
        # A restart during dispatch leaves 'dispatching', also requiring reconciliation.
        await session.rollback()
        attempt = await session.get(PublicationAttempt, attempt_id)
        attempt.state = "unknown"
        attempt.error = "Connector outcome unconfirmed; inspect before retrying"
        await session.commit()
        raise HTTPException(502, "Dispatch outcome unconfirmed; no automatic retry") from None
    return receipt(attempt)
