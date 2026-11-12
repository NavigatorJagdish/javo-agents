"""Content library, upload, folder scanning, scheduling, and publishing routes."""

from __future__ import annotations

import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.security import require_auth
from app.database import get_session
from app.models.content import (
    AssetStatus,
    AssetType,
    ContentAsset,
    ContentSchedule,
    MediaMetadata,
    PublishStatus,
    ScheduleStatus,
)
from app.models.user import User

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
    caption: Optional[str] = None
    platform_options: Optional[dict[str, Any]] = None


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


class PublishRequest(BaseModel):
    allow_mock: bool = False


class PublishResponse(BaseModel):
    schedule_id: str
    publish_record_id: str
    status: str
    platform_post_id: Optional[str] = None
    message: str
    mode: str = "live"
    platform: Optional[str] = None


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
    if requested_user_id:
        return requested_user_id
    res = await session.execute(select(User.id).limit(1))
    return res.scalar_one_or_none() or "default-user"


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
    user: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> ContentAssetResponse:
    """Upload a media or document file into the content library."""
    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    original_name = Path(file.filename or "upload.bin").name
    asset_id = str(uuid4())
    dest_path = upload_dir / f"{asset_id}_{original_name}"
    contents = await file.read()
    dest_path.write_bytes(contents)

    resolved_user = user.get("user_id") or await _resolve_user_id(user_id, session)
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
        file_size=len(contents),
    )
    session.add(asset)
    session.add(meta)
    await session.commit()
    await session.refresh(asset)
    return ContentAssetResponse.model_validate(asset)


@router.post("/scan-folder", response_model=ScanFolderResponse)
async def scan_folder(
    body: ScanFolderRequest,
    user: dict = Depends(require_auth),
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

    resolved_user = user.get("user_id") or await _resolve_user_id(body.user_id, session)
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
    user: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> ScheduleResponse:
    """Schedule a content asset for publishing to a social account."""
    asset_res = await session.execute(select(ContentAsset).where(ContentAsset.id == body.asset_id))
    if not asset_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content asset not found")

    from app.models.account import SocialAccount

    acc_res = await session.execute(select(SocialAccount).where(SocialAccount.id == body.account_id))
    account = acc_res.scalar_one_or_none()
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Social account not found")
    is_admin = bool(user.get("is_owner")) or str(user.get("role", "")).lower() in {"owner", "admin"}
    if not is_admin and account.user_id != user.get("user_id"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-account access denied")

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


@router.post("/schedule/{schedule_id}/publish", response_model=PublishResponse)
async def publish_scheduled_content(
    schedule_id: str,
    body: Optional[PublishRequest] = None,
    user: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> PublishResponse:
    """Execute verified publish for an approved scheduled content item via real connector or explicit mock."""
    from app.models.account import SocialAccount
    from app.services.content_pipeline import approve_and_dispatch_schedule

    res = await session.execute(select(ContentSchedule).where(ContentSchedule.id == schedule_id))
    schedule = res.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content schedule not found")

    if schedule.status == ScheduleStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Content schedule has already been published to live platform",
        )

    if schedule.status not in {ScheduleStatus.APPROVED, ScheduleStatus.SIMULATED}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Schedule cannot be published while status is '{schedule.status.value}'; approval required first.",
        )

    acc_res = await session.execute(select(SocialAccount).where(SocialAccount.id == schedule.account_id))
    account = acc_res.scalar_one_or_none()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target social account not found for schedule",
        )

    is_admin = bool(user.get("is_owner")) or str(user.get("role", "")).lower() in {"owner", "admin"}
    if not is_admin and account.user_id != user.get("user_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-account access denied: schedule account belongs to another user",
        )

    req = body or PublishRequest()
    result = await approve_and_dispatch_schedule(
        session=session,
        schedule_id=schedule.id,
        approved_by=str(schedule.approved_by or user.get("user_id") or "owner"),
        publish_now=True,
        allow_mock=req.allow_mock,
    )

    if req.allow_mock:
        return PublishResponse(
            schedule_id=schedule.id,
            publish_record_id=str(result.get("publish_record_id", "")),
            status=PublishStatus.SIMULATED.value,
            platform_post_id=result.get("platform_post_id"),
            mode="mock",
            platform=result.get("platform"),
            message="Content simulated via mock connector; schedule remains approved for live publishing",
        )

    if not result.get("published"):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Platform connector failed to publish post: {result.get('error', 'Unknown error')}",
        )

    return PublishResponse(
        schedule_id=schedule.id,
        publish_record_id=str(result.get("publish_record_id", "")),
        status=PublishStatus.SUCCESS.value,
        platform_post_id=result.get("platform_post_id"),
        mode="live",
        platform=result.get("platform"),
        message="Content published via live connector",
    )


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
async def delete_content_asset(
    asset_id: str,
    user: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a content asset."""
    del user
    res = await session.execute(select(ContentAsset).where(ContentAsset.id == asset_id))
    asset = res.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content asset not found")
    await session.delete(asset)
    await session.commit()


@router.post("/pipeline/run")
async def trigger_content_pipeline(
    body: dict,
    user: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Scan a local folder, probe media, draft captions/hashtags, check quality, and queue approval-gated schedules."""
    from app.services.content_pipeline import run_content_pipeline

    folder_path = str(body.get("folder_path", "")).strip()
    if not folder_path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="folder_path is required")
    return await run_content_pipeline(
        session=session,
        folder_path=folder_path,
        platform=str(body.get("platform", "instagram")),
        account_id=body.get("account_id"),
        user_id=str(body.get("user_id") or user.get("user_id") or "owner"),
        topic=body.get("topic"),
        auto_schedule=bool(body.get("auto_schedule", True)),
        approval_required=bool(body.get("approval_required", True)),
        limit=int(body.get("limit", 20)),
    )


@router.post("/schedule/{schedule_id}/approve")
async def approve_schedule(
    schedule_id: str,
    body: Optional[dict] = None,
    user: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Approve a scheduled post and optionally dispatch it via connector or explicit MockConnector."""
    from app.models.account import SocialAccount
    from app.services.content_pipeline import approve_and_dispatch_schedule

    sched_res = await session.execute(select(ContentSchedule).where(ContentSchedule.id == schedule_id))
    sched = sched_res.scalar_one_or_none()
    if not sched:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content schedule not found")

    if sched.status == ScheduleStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Content schedule has already been published",
        )

    acc_res = await session.execute(select(SocialAccount).where(SocialAccount.id == sched.account_id))
    account = acc_res.scalar_one_or_none()
    is_admin = bool(user.get("is_owner")) or str(user.get("role", "")).lower() in {"owner", "admin"}
    if account is not None and not is_admin and account.user_id != user.get("user_id"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-account access denied")

    payload = body or {}
    principal = str(user.get("user_id", "owner"))
    return await approve_and_dispatch_schedule(
        session=session,
        schedule_id=schedule_id,
        approved_by=principal,
        publish_now=bool(payload.get("publish_now", False)),
        allow_mock=bool(payload.get("allow_mock", True)),
    )
