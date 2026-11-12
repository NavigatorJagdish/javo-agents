"""Device pairing, listing, syncing, and revocation routes."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
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
    push_token: Optional[str] = None


class SyncResponse(BaseModel):
    device_id: str
    synced_at: str
    status: str


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
async def list_devices(session: AsyncSession = Depends(get_session)) -> list[DeviceResponse]:
    """List all paired devices."""
    res = await session.execute(select(Device).order_by(Device.paired_at.desc()))
    return [DeviceResponse.model_validate(d) for d in res.scalars().all()]


@router.post("/pair", response_model=PairInitiateResponse, status_code=status.HTTP_201_CREATED)
async def initiate_pairing(
    body: PairInitiateRequest,
    session: AsyncSession = Depends(get_session),
) -> PairInitiateResponse:
    """Generate a short-lived 6-digit pairing code for a new device."""
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


@router.post("/pair/{code}/confirm", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def confirm_pairing(
    code: str,
    body: PairConfirmRequest = PairConfirmRequest(),
    session: AsyncSession = Depends(get_session),
) -> DeviceResponse:
    """Confirm device pairing using the pairing code and persist the trusted device."""
    pending = _PENDING_PAIRINGS.pop(code, None)
    if not pending:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid or unknown pairing code")

    if datetime.now(timezone.utc) > pending["expires_at"]:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Pairing code has expired")

    now = datetime.now(timezone.utc)
    device = Device(
        id=str(uuid4()),
        user_id=pending["user_id"],
        device_name=pending["device_name"],
        device_type=pending["device_type"],
        platform=pending["platform"],
        push_token=body.push_token,
        last_seen=now,
        is_trusted=True,
    )
    session.add(device)
    await session.commit()
    await session.refresh(device)
    return DeviceResponse.model_validate(device)


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_device(device_id: str, session: AsyncSession = Depends(get_session)) -> None:
    """Revoke and remove a paired device."""
    res = await session.execute(select(Device).where(Device.id == device_id))
    device = res.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    await session.delete(device)
    await session.commit()


@router.post("/{device_id}/sync", response_model=SyncResponse)
async def sync_device(device_id: str, session: AsyncSession = Depends(get_session)) -> SyncResponse:
    """Record a device sync heartbeat and return current sync status."""
    res = await session.execute(select(Device).where(Device.id == device_id))
    device = res.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    now = datetime.now(timezone.utc)
    device.last_seen = now
    await session.commit()

    return SyncResponse(
        device_id=device_id,
        synced_at=now.isoformat(),
        status="synced",
    )
