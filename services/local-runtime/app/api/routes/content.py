"""Content library, upload, folder scanning, scheduling, and publishing routes."""

from __future__ import annotations

import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, ConfigDict, field_validator, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.local_identity import LOCAL_OWNER, OWNER_IDS, ensure_local_owner
from app.database import get_session
from app.models.account import SocialAccount
from app.services.publishing import approve_schedule, dispatch_schedule, load_snapshot, receipt, fingerprint_payload
from app.models.content import (
    AssetStatus,
    AssetType,
    ContentAsset,
    ContentSchedule,
    MediaMetadata,
    ScheduleStatus,
)
from app.models.publication import PublicationAttempt, PublicationTimer
from app.services.timed_dispatch import arm_timer, cancel_timer, timer_receipt

router = APIRouter(prefix="/content", tags=["content"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class ContentAssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    title: str
    description: Optional[str] = None
    asset_type: AssetType
    status: AssetStatus
    file_path: Optional[str] = None
    file_url: Optional[str] = None
    content_text: Optional[str] = None
    hashtags: Optional[list[str]] = None
    tags: Optional[list[str]] = None
    ai_generated: bool = False
    ai_metadata: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class ScanFolderRequest(BaseModel):
    folder_path: Optional[str] = None
    recursive: bool = True
    user_id: Optional[str] = None


class ScanFolderResponse(BaseModel):
    scanned_path: str
    discovered_files: int
    imported_assets: list[ContentAssetResponse]


class ScheduleCreate(BaseModel):
    asset_id: str
    account_id: str
    scheduled_at: datetime

    @field_validator("scheduled_at")
    @classmethod
    def validate_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Schedule requires an explicit timezone")
        if value <= datetime.now(timezone.utc):
            raise ValueError("Schedule must be in the future")
        return value.astimezone(timezone.utc)

    caption: Optional[str] = None
    platform_options: Optional[dict[str, Any]] = None


class ApprovalRequest(BaseModel):
    mode: Literal["mock", "live"] = "live"
    fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")


class TimerRequest(BaseModel):
    fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")


class ScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    asset_id: str
    account_id: str
    scheduled_at: datetime
    status: ScheduleStatus
    caption: Optional[str] = None
    platform_options: Optional[dict[str, Any]] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class PublishResponse(BaseModel):
    schedule_id: str
    publish_record_id: str
    status: str
    platform_post_id: Optional[str] = None
    message: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_EXT_TO_TYPE: dict[str, AssetType] = {
    ".jpg": AssetType.IMAGE,
    ".jpeg": AssetType.IMAGE,
    ".png": AssetType.IMAGE,
    ".webp": AssetType.IMAGE,
    ".gif": AssetType.IMAGE,
    ".mp4": AssetType.VIDEO,
    ".mov": AssetType.VIDEO,
    ".mkv": AssetType.VIDEO,
    ".webm": AssetType.VIDEO,
    ".mp3": AssetType.AUDIO,
    ".wav": AssetType.AUDIO,
    ".m4a": AssetType.AUDIO,
    ".pdf": AssetType.DOCUMENT,
    ".txt": AssetType.TEXT,
    ".md": AssetType.TEXT,
}


def _infer_asset_type(filename: str) -> AssetType:
    return _EXT_TO_TYPE.get(Path(filename).suffix.lower(), AssetType.DOCUMENT)


async def _resolve_user_id(requested_user_id: Optional[str], session: AsyncSession) -> str:
    if requested_user_id is not None and requested_user_id not in OWNER_IDS:
        raise HTTPException(403, "Cannot assign another content owner")
    await ensure_local_owner(session)
    return LOCAL_OWNER


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/", response_model=list[ContentAssetResponse])
async def list_content(
    asset_type: Optional[AssetType] = None,
    status_filter: Optional[AssetStatus] = Query(default=None, alias="status"),
    ai_generated: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[ContentAssetResponse]:
    """List content assets in the library with optional filters."""
    stmt = select(ContentAsset)
    if asset_type is not None:
        stmt = stmt.where(ContentAsset.asset_type == asset_type)
    if status_filter is not None:
        stmt = stmt.where(ContentAsset.status == status_filter)
    if ai_generated is not None:
        stmt = stmt.where(ContentAsset.ai_generated == ai_generated)
    stmt = stmt.order_by(ContentAsset.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(stmt)
    return [ContentAssetResponse.model_validate(a) for a in result.scalars().all()]


@router.post("/upload", response_model=ContentAssetResponse, status_code=status.HTTP_201_CREATED)
async def upload_content(
    file: UploadFile = File(...),
    title: Optional[str] = Form(default=None),
    description: Optional[str] = Form(default=None),
    user_id: Optional[str] = Form(default=None),
    session: AsyncSession = Depends(get_session),
) -> ContentAssetResponse:
    """Upload a media or document file into the content library."""
    resolved_user = await _resolve_user_id(user_id, session)
    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    original_name = Path(file.filename or "upload.bin").name
    asset_id = str(uuid4())
    dest_path = upload_dir / f"{asset_id}_{original_name}"
    size = 0
    try:
        with dest_path.open('xb') as destination:
            while chunk := await file.read(65536):
                size += len(chunk)
                if size > 64 * 1024 * 1024:
                    raise HTTPException(413, 'Upload exceeds64MiB. Import a larger local file through its content folder instead.')
                destination.write(chunk)
    except BaseException:
        dest_path.unlink(missing_ok=True)
        raise
    finally:
        await file.close()

    asset = ContentAsset(
        id=asset_id,
        user_id=resolved_user,
        title=title or original_name,
        description=description,
        asset_type=_infer_asset_type(original_name),
        status=AssetStatus.READY,
        file_path=str(dest_path),
    )
    meta = MediaMetadata(
        id=str(uuid4()),
        asset_id=asset_id,
        mime_type=file.content_type or mimetypes.guess_type(original_name)[0],
        file_size=size,
    )
    session.add(asset)
    session.add(meta)
    await session.commit()
    await session.refresh(asset)
    return ContentAssetResponse.model_validate(asset)


@router.post("/scan-folder", response_model=ScanFolderResponse)
async def scan_folder(
    body: ScanFolderRequest,
    session: AsyncSession = Depends(get_session),
) -> ScanFolderResponse:
    """Scan a local folder and register discovered media files as content assets."""
    settings = get_settings()
    target = Path(body.folder_path or settings.content_root).resolve()
    if not target.exists() or not target.is_dir():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Folder does not exist: {target}",
        )

    resolved_user = await _resolve_user_id(body.user_id, session)
    iterator = target.rglob("*") if body.recursive else target.glob("*")
    files = [p for p in iterator if p.is_file() and p.suffix.lower() in _EXT_TO_TYPE]

    existing_res = await session.execute(select(ContentAsset.file_path))
    existing_paths = {row[0] for row in existing_res.all() if row[0]}

    imported: list[ContentAsset] = []
    for fpath in files:
        spath = str(fpath)
        if spath in existing_paths:
            continue
        asset_id = str(uuid4())
        asset = ContentAsset(
            id=asset_id,
            user_id=resolved_user,
            title=fpath.stem,
            asset_type=_infer_asset_type(fpath.name),
            status=AssetStatus.READY,
            file_path=spath,
        )
        meta = MediaMetadata(
            id=str(uuid4()),
            asset_id=asset_id,
            mime_type=mimetypes.guess_type(fpath.name)[0],
            file_size=fpath.stat().st_size,
        )
        session.add(asset)
        session.add(meta)
        imported.append(asset)

    await session.commit()
    for asset in imported:
        await session.refresh(asset)

    return ScanFolderResponse(
        scanned_path=str(target),
        discovered_files=len(files),
        imported_assets=[ContentAssetResponse.model_validate(a) for a in imported],
    )


@router.post("/schedule", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    body: ScheduleCreate,
    session: AsyncSession = Depends(get_session),
) -> ScheduleResponse:
    """Schedule a content asset for publishing to a social account."""
    asset_res = await session.execute(select(ContentAsset).where(ContentAsset.id == body.asset_id))
    asset = asset_res.scalar_one_or_none()
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content asset not found")

    account = await session.get(SocialAccount, body.account_id)
    if account is None:
        raise HTTPException(404, "Destination account not found")
    if account.user_id != asset.user_id and not (
        account.user_id in OWNER_IDS and asset.user_id in OWNER_IDS
    ):
        raise HTTPException(403, "Content and destination have different owners")

    schedule = ContentSchedule(
        id=str(uuid4()),
        asset_id=body.asset_id,
        account_id=body.account_id,
        scheduled_at=body.scheduled_at,
        caption=body.caption,
        platform_options=body.platform_options,
        status=ScheduleStatus.PENDING,
    )
    session.add(schedule)
    await session.commit()
    await session.refresh(schedule)
    return ScheduleResponse.model_validate(schedule)


@router.get("/schedule", response_model=list[ScheduleResponse])
async def list_schedules(
    status_filter: Optional[ScheduleStatus] = Query(default=None, alias="status"),
    account_id: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
) -> list[ScheduleResponse]:
    """List scheduled content items."""
    stmt = select(ContentSchedule)
    if status_filter is not None:
        stmt = stmt.where(ContentSchedule.status == status_filter)
    if account_id is not None:
        stmt = stmt.where(ContentSchedule.account_id == account_id)
    stmt = stmt.order_by(ContentSchedule.scheduled_at.asc())
    result = await session.execute(stmt)
    return [ScheduleResponse.model_validate(s) for s in result.scalars().all()]


@router.get("/schedule/{schedule_id}/preview")
async def preview_schedule(schedule_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    schedule, snapshot = await load_snapshot(session, schedule_id)
    return {"schedule_id": schedule.id, "status": schedule.status, "snapshot": snapshot, "fingerprint": fingerprint_payload(snapshot)}


@router.get("/timers")
async def list_timers(session: AsyncSession = Depends(get_session)) -> list[dict]:
    timers = (await session.execute(select(PublicationTimer).order_by(
        PublicationTimer.due_at.desc()).limit(200))).scalars().all()
    return [timer_receipt(timer) for timer in timers]


@router.post("/schedule/{schedule_id}/timer")
async def arm_content_timer(schedule_id: str, body: TimerRequest,
                            session: AsyncSession = Depends(get_session)) -> dict:
    return await arm_timer(session, schedule_id, body.fingerprint)


@router.delete("/schedule/{schedule_id}/timer")
async def cancel_content_timer(schedule_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    return await cancel_timer(session, schedule_id)


@router.get("/schedule/{schedule_id}/receipt")
async def publication_receipt(schedule_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    attempt = (await session.execute(select(PublicationAttempt).where(
        PublicationAttempt.schedule_id == schedule_id))).scalar_one_or_none()
    if attempt is None:
        raise HTTPException(404, "No dispatch receipt recorded")
    return receipt(attempt)


@router.post("/schedule/{schedule_id}/approve")
async def approve_content(schedule_id: str, body: ApprovalRequest,
                          session: AsyncSession = Depends(get_session)) -> dict:
    return await approve_schedule(session, schedule_id, body.mode, "local-owner", body.fingerprint)


@router.post("/schedule/{schedule_id}/publish", response_model=PublishResponse)
async def publish_scheduled_content(schedule_id: str,
                                    session: AsyncSession = Depends(get_session)) -> dict:
    return await dispatch_schedule(session, schedule_id)


@router.get("/{asset_id}", response_model=ContentAssetResponse)
async def get_content_asset(
    asset_id: str,
    session: AsyncSession = Depends(get_session),
) -> ContentAssetResponse:
    """Get a single content asset by ID."""
    res = await session.execute(select(ContentAsset).where(ContentAsset.id == asset_id))
    asset = res.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content asset not found")
    return ContentAssetResponse.model_validate(asset)


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content_asset(asset_id: str, session: AsyncSession = Depends(get_session)) -> None:
    """Delete a content asset."""
    res = await session.execute(select(ContentAsset).where(ContentAsset.id == asset_id))
    asset = res.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content asset not found")
    await session.delete(asset)
    await session.commit()
