"""Device pairing, listing, syncing, and revocation routes."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_auth, require_owner
from app.database import get_session
from app.models.agent import AgentDefinition, AgentStatus
from app.models.content import AssetStatus, AssetType, ContentAsset, ContentSchedule, ScheduleStatus
from app.models.user import Device, DeviceType, User

router = APIRouter(prefix="/devices", tags=["devices"])

# Ephemeral in-memory pairing codes: code -> metadata dict
_PENDING_PAIRINGS: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    device_name: str
    device_type: DeviceType
    platform: Optional[str] = None
    last_seen: Optional[datetime] = None
    is_trusted: bool
    paired_at: datetime


class PairInitiateRequest(BaseModel):
    device_name: str = Field(..., min_length=1, max_length=128)
    device_type: DeviceType = DeviceType.MOBILE
    platform: Optional[str] = "android"
    user_id: Optional[str] = None


class PairInitiateResponse(BaseModel):
    code: str
    expires_at: str
    device_name: str
    device_type: str


class PairConfirmRequest(BaseModel):
    device_id: Optional[str] = None
    device_name: Optional[str] = None
    platform: Optional[str] = "android"
    device_token: Optional[str] = None
    push_token: Optional[str] = None


class PairConfirmResponse(BaseModel):
    paired: bool = True
    device_id: str
    device_token: str
    message: str = "Paired successfully"


class SyncResponse(BaseModel):
    device_id: str
    synced_at: str
    status: str
    active_agents: int = 0
    pending_approvals: int = 0
    acknowledged_ids: list[str] = Field(default_factory=list)
    synced_drafts_count: int = 0
    message: str = "Synced"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _resolve_user_id(requested_user_id: Optional[str], session: AsyncSession) -> str:
    if requested_user_id:
        return requested_user_id
    res = await session.execute(select(User.id).limit(1))
    return res.scalar_one_or_none() or "default-user"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/", response_model=list[DeviceResponse])
async def list_devices(
    user: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> list[DeviceResponse]:
    """List all paired devices."""
    del user
    res = await session.execute(select(Device).order_by(Device.paired_at.desc()))
    return [DeviceResponse.model_validate(d) for d in res.scalars().all()]


@router.post("/pair", response_model=PairInitiateResponse, status_code=status.HTTP_201_CREATED)
async def initiate_pairing(
    body: PairInitiateRequest,
    user: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> PairInitiateResponse:
    """Generate a short-lived 6-digit pairing code for a new device."""
    del user
    user_id = await _resolve_user_id(body.user_id, session)
    code = f"{secrets.randbelow(1_000_000):06d}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    _PENDING_PAIRINGS[code] = {
        "user_id": user_id,
        "device_name": body.device_name,
        "device_type": body.device_type,
        "platform": body.platform,
        "expires_at": expires_at,
    }

    return PairInitiateResponse(
        code=code,
        expires_at=expires_at.isoformat(),
        device_name=body.device_name,
        device_type=body.device_type.value,
    )


@router.post("/pair/{code}/confirm", response_model=PairConfirmResponse, status_code=status.HTTP_201_CREATED)
async def confirm_pairing(
    code: str,
    body: PairConfirmRequest = PairConfirmRequest(),
    session: AsyncSession = Depends(get_session),
) -> PairConfirmResponse:
    """Confirm device pairing using the pairing challenge code without requiring pre-existing bearer auth."""
    from app.core.security import get_token_manager

    pending = _PENDING_PAIRINGS.pop(code, None)
    if not pending:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid or unknown pairing code")

    if datetime.now(timezone.utc) > pending["expires_at"]:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Pairing code has expired")

    now = datetime.now(timezone.utc)
    device_id = body.device_id or str(uuid4())
    device_name = body.device_name or pending["device_name"]

    # Generate device-bound authentication token
    token_mgr = get_token_manager()
    device_token = token_mgr.generate_token(user_id=pending["user_id"], device_id=device_id, role="device")

    # Check if device already exists
    res = await session.execute(select(Device).where(Device.id == device_id))
    device = res.scalar_one_or_none()
    if device:
        device.device_name = device_name
        device.platform = body.platform or pending["platform"]
        device.push_token = body.push_token or body.device_token
        device.last_seen = now
        device.is_trusted = True
    else:
        device = Device(
            id=device_id,
            user_id=pending["user_id"],
            device_name=device_name,
            device_type=pending["device_type"],
            platform=body.platform or pending["platform"],
            push_token=body.push_token or body.device_token,
            last_seen=now,
            is_trusted=True,
        )
        session.add(device)

    await session.commit()
    await session.refresh(device)

    return PairConfirmResponse(
        paired=True,
        device_id=device.id,
        device_token=device_token,
        message="Paired successfully",
    )


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_device(
    device_id: str,
    user: dict = Depends(require_owner),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Revoke and remove a paired device."""
    del user
    res = await session.execute(select(Device).where(Device.id == device_id))
    device = res.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    await session.delete(device)
    await session.commit()


@router.post("/{device_id}/sync", response_model=SyncResponse)
async def sync_device(
    device_id: str,
    drafts: Optional[list[dict[str, Any]]] = None,
    user: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> SyncResponse:
    """Record a device sync heartbeat, persist queued drafts durably, and return current truthful sync status."""
    res = await session.execute(select(Device).where(Device.id == device_id))
    device = res.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    target_user_id = device.user_id
    now = datetime.now(timezone.utc)
    device.last_seen = now

    acknowledged_ids: list[str] = []
    if drafts:
        for d in drafts:
            draft_id = str(d.get("id") or "").strip()
            if not draft_id:
                continue
            title = str(d.get("title") or "Untitled Draft").strip()
            content_text = str(d.get("body") or d.get("content_text") or "").strip()
            platform_str = str(d.get("platform") or "Instagram").strip()

            # Map platform to asset type
            asset_type = AssetType.TEXT
            if platform_str.lower() in ("youtube", "reel", "tiktok"):
                asset_type = AssetType.REEL

            # Idempotent upsert
            asset_res = await session.execute(
                select(ContentAsset).where(ContentAsset.id == draft_id)
            )
            asset = asset_res.scalar_one_or_none()
            if asset:
                asset.title = title
                asset.content_text = content_text
                asset.updated_at = now
                meta = dict(asset.ai_metadata or {})
                meta["synced_from_device"] = device_id
                meta["platform"] = platform_str
                asset.ai_metadata = meta
            else:
                asset = ContentAsset(
                    id=draft_id,
                    user_id=target_user_id,
                    title=title,
                    description=f"Synced from mobile device {device.device_name}",
                    asset_type=asset_type,
                    status=AssetStatus.DRAFT,
                    content_text=content_text,
                    ai_metadata={
                        "synced_from_device": device_id,
                        "platform": platform_str,
                        "created_via": "android_sync",
                    },
                    created_at=now,
                    updated_at=now,
                )
                session.add(asset)
            acknowledged_ids.append(draft_id)

    await session.commit()

    # Truthful counts from real database tables
    active_agents = await session.scalar(
        select(func.count(AgentDefinition.id)).where(AgentDefinition.status == AgentStatus.RUNNING)
    ) or 0

    pending_approvals = await session.scalar(
        select(func.count(ContentSchedule.id)).where(ContentSchedule.status == ScheduleStatus.PENDING)
    ) or 0

    return SyncResponse(
        device_id=device_id,
        synced_at=now.isoformat(),
        status="synced",
        active_agents=active_agents,
        pending_approvals=pending_approvals,
        acknowledged_ids=acknowledged_ids,
        synced_drafts_count=len(acknowledged_ids),
        message=f"Synced {len(acknowledged_ids)} drafts durably" if acknowledged_ids else "Heartbeat synced",
    )


@router.get("/{device_id}/drafts")
async def get_device_drafts(
    device_id: str,
    user: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    """Retrieve durable drafts associated with this device or user."""
    del user
    res = await session.execute(select(Device).where(Device.id == device_id))
    device = res.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    asset_res = await session.execute(
        select(ContentAsset)
        .where(ContentAsset.user_id == device.user_id, ContentAsset.status == AssetStatus.DRAFT)
        .order_by(ContentAsset.updated_at.desc())
    )
    assets = asset_res.scalars().all()
    return [
        {
            "id": a.id,
            "title": a.title,
            "body": a.content_text or "",
            "platform": (a.ai_metadata or {}).get("platform", "Instagram"),
            "status": a.status.value if hasattr(a.status, "value") else str(a.status),
            "updated_at": a.updated_at.isoformat() if a.updated_at else "",
        }
        for a in assets
    ]
