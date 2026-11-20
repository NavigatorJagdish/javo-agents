"""Owned account records, protected legacy credentials and real brand profiles.

An account record or stored token is not verified platform connectivity. Official
OAuth configuration/flow remains unavailable; this API never fabricates it.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Annotated, Any, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.account_credentials import credential_store, split_legacy_metadata
from app.core.local_identity import LOCAL_OWNER, OWNER_IDS, ensure_local_owner
from app.core.provider_store import VaultUnavailable
from app.database import get_session
from app.models.account import AccountStatus, BrandProfile, Platform, SocialAccount
from app.models.content import ContentSchedule
from app.models.security import AuditAction, AuditLog
from app.models.task import Task
from app.services.social_credentials import migrate_one, owned_account

router = APIRouter(prefix="/accounts", tags=["accounts"])


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, allow_inf_nan=False)


class PublicMetadata(Input):
    account_type: Literal["page", "professional", "channel", "simulation", "other"] | None = None
    page_id: str | None = Field(default=None, max_length=128)
    channel_id: str | None = Field(default=None, max_length=128)
    instagram_user_id: str | None = Field(default=None, max_length=128)


class AccountCreate(Input):
    platform: Platform
    username: str = Field(min_length=1, max_length=128)
    display_name: str | None = Field(default=None, max_length=256)
    platform_user_id: str | None = Field(default=None, max_length=128)
    user_id: str | None = None
    metadata: PublicMetadata | None = None


class AccountUpdate(Input):
    username: str | None = Field(default=None, min_length=1, max_length=128)
    display_name: str | None = Field(default=None, max_length=256)
    status: Literal["disconnected"] | None = None
    metadata: PublicMetadata | None = None

    @model_validator(mode="after")
    def non_null(self):
        for name in ("username", "status"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


class AccountResponse(BaseModel):
    id: str
    user_id: str
    platform: Platform
    platform_user_id: str | None
    username: str
    display_name: str | None
    status: AccountStatus = AccountStatus.DISCONNECTED
    reported_status: AccountStatus
    connection_verified: bool = False
    token_expires_at: datetime | None
    metadata: dict[str, str] | None
    credential_state: str
    has_saved_credentials: bool | None
    credentials_protection: str
    has_refresh_token: bool | None
    credential_expires_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @field_validator("token_expires_at", "credential_expires_at", "created_at", "updated_at")
    @classmethod
    def utc_dates(cls, value):
        return value.replace(tzinfo=timezone.utc) if value and value.tzinfo is None else value


class OAuthInitiateRequest(Input):
    redirect_uri: str = Field(
        default="http://localhost:8000/api/accounts/oauth/callback", max_length=2048
    )
    scopes: list[str] = Field(default_factory=list, max_length=20)


class BrandProfileSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    account_id: str
    brand_name: str
    brand_voice: str | None
    target_audience: str | None
    content_pillars: list[str] | None
    hashtag_groups: dict[str, Any] | None
    color_palette: list[str] | None
    logo_url: str | None
    guidelines: dict[str, Any] | None


class BrandProfileUpdate(Input):
    brand_name: str | None = Field(default=None, min_length=1, max_length=128)
    brand_voice: str | None = Field(default=None, max_length=4000)
    target_audience: str | None = Field(default=None, max_length=2000)
    content_pillars: list[Annotated[str, Field(min_length=1, max_length=200)]] | None = Field(
        default=None, max_length=20
    )
    hashtag_groups: dict[str, Any] | None = None
    color_palette: list[str] | None = Field(default=None, max_length=20)
    logo_url: str | None = Field(default=None, max_length=512)
    guidelines: dict[str, Any] | None = None

    @model_validator(mode="after")
    def required_name(self):
        if "brand_name" in self.model_fields_set and self.brand_name is None:
            raise ValueError("Brand name cannot be null")
        return self


def _public_metadata(value):
    if not isinstance(value, dict):
        return None
    # Older arbitrary metadata could include credentials/unsupported analytics.
    # Retain its source in the DB, but never return unreviewed keys as public data.
    result = {
        key: value[key]
        for key in PublicMetadata.model_fields
        if isinstance(value.get(key), str) and len(value[key]) <= 128
    }
    return result or None


async def _response(account):
    try:
        _, legacy_metadata = split_legacy_metadata(account.metadata_)
        legacy_present = bool(account.access_token or account.refresh_token or legacy_metadata)
    except VaultUnavailable:
        legacy_present = True
    meta = await asyncio.to_thread(
        credential_store().metadata,
        account.id,
        legacy_present=legacy_present,
    )
    return AccountResponse(
        id=account.id,
        user_id=account.user_id,
        platform=account.platform,
        platform_user_id=account.platform_user_id,
        username=account.username,
        display_name=account.display_name,
        reported_status=account.status,
        token_expires_at=account.token_expires_at,
        metadata=_public_metadata(account.metadata_),
        created_at=account.created_at,
        updated_at=account.updated_at,
        **meta,
    )


def _audit(session, account_id, description):
    session.add(
        AuditLog(
            action=AuditAction.UPDATE,
            resource_type="account",
            resource_id=account_id,
            description=description,
        )
    )


@router.get("/", response_model=list[AccountResponse])
async def list_accounts(
    platform: Platform | None = None,
    status_filter: AccountStatus | None = Query(default=None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(SocialAccount).where(SocialAccount.user_id.in_(OWNER_IDS))
    if platform is not None:
        stmt = stmt.where(SocialAccount.platform == platform)
    if status_filter is not None:
        # This build has no verified connected accounts, regardless of old flags.
        if status_filter != AccountStatus.DISCONNECTED:
            return []
    records = list(
        (
            await session.execute(
                stmt.order_by(SocialAccount.created_at.desc(), SocialAccount.id)
                .offset(offset)
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    return await asyncio.gather(*(_response(row) for row in records))


@router.post("/", response_model=AccountResponse, status_code=201)
async def create_account(body: AccountCreate, session: AsyncSession = Depends(get_session)):
    if body.user_id is not None and body.user_id != LOCAL_OWNER:
        raise HTTPException(403, "Cannot assign another account owner")
    await session.execute(text("BEGIN IMMEDIATE"))
    await ensure_local_owner(session)
    account = SocialAccount(
        id=str(uuid4()),
        user_id=LOCAL_OWNER,
        platform=body.platform,
        platform_user_id=body.platform_user_id,
        username=body.username,
        display_name=body.display_name,
        status=AccountStatus.DISCONNECTED,
        metadata_=body.metadata.model_dump(exclude_none=True) if body.metadata else None,
        created_at=datetime.now(timezone.utc),
    )
    session.add(account)
    _audit(session, account.id, "Unconnected local account record created")
    await session.commit()
    await session.refresh(account)
    return await _response(account)


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(account_id: str, session: AsyncSession = Depends(get_session)):
    return await _response(await owned_account(account_id, session))


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: str, body: AccountUpdate, session: AsyncSession = Depends(get_session)
):
    await session.execute(text("BEGIN IMMEDIATE"))
    account = await owned_account(account_id, session)
    data = body.model_dump(exclude_unset=True)
    if "metadata" in data:
        try:
            _, pending_secrets = split_legacy_metadata(account.metadata_)
        except VaultUnavailable:
            raise HTTPException(409, "Legacy metadata needs recovery before replacement") from None
        if pending_secrets:
            raise HTTPException(409, "Protect legacy credentials before replacing account metadata")
        account.metadata_ = data.pop("metadata")
    for key, value in data.items():
        setattr(account, key, value)
    account.status = AccountStatus.DISCONNECTED
    _audit(session, account_id, "Unverified local account record updated")
    await session.commit()
    await session.refresh(account)
    return await _response(account)


@router.post("/{account_id}/credentials/migrate", response_model=AccountResponse)
async def protect_credentials(account_id: str, session: AsyncSession = Depends(get_session)):
    try:
        account = await migrate_one(account_id, session)
    except VaultUnavailable:
        raise HTTPException(
            503, "Credential protection is unavailable; original values were retained for recovery"
        ) from None
    await session.refresh(account)
    return await _response(account)


@router.delete("/{account_id}/credentials", response_model=AccountResponse)
async def remove_credentials(account_id: str, session: AsyncSession = Depends(get_session)):
    await session.execute(text("BEGIN IMMEDIATE"))
    account = await owned_account(account_id, session)
    try:
        cleaned_metadata, _ = split_legacy_metadata(account.metadata_)
        await asyncio.to_thread(credential_store().clear, account_id)
    except VaultUnavailable:
        raise HTTPException(
            503, "Credential storage is locked; recover the original key/profile before removal"
        ) from None
    account.access_token = account.refresh_token = None
    account.metadata_ = cleaned_metadata
    account.token_expires_at = None
    account.status = AccountStatus.DISCONNECTED
    _audit(
        session,
        account_id,
        "Saved local credentials removed; platform revocation was not requested",
    )
    await session.commit()
    await session.refresh(account)
    return await _response(account)


@router.delete("/{account_id}", status_code=204)
async def delete_account(account_id: str, session: AsyncSession = Depends(get_session)):
    await session.execute(text("BEGIN IMMEDIATE"))
    account = await owned_account(account_id, session)
    schedules = await session.scalar(
        select(ContentSchedule.id).where(ContentSchedule.account_id == account_id).limit(1)
    )
    tasks = await session.scalar(select(Task.task_id).where(Task.account_id == account_id).limit(1))
    if schedules or tasks:
        raise HTTPException(
            409, "This account has saved work/history; remove credentials instead to preserve it"
        )
    try:
        await asyncio.to_thread(credential_store().clear, account_id)
    except VaultUnavailable:
        raise HTTPException(
            503, "Credential storage is locked; recover the original profile before account removal"
        ) from None
    _audit(session, account_id, "Unused local account record removed")
    await session.delete(account)
    await session.commit()


@router.post("/{account_id}/oauth/initiate")
async def initiate_oauth(
    account_id: str, body: OAuthInitiateRequest, session: AsyncSession = Depends(get_session)
):
    await owned_account(account_id, session)
    # The previous URL lacked a configured client ID, persisted state, PKCE and
    # a verified callback. Never label that prototype a successful sign-in.
    raise HTTPException(
        501,
        "Official OAuth setup and callback verification are not configured; no account was connected",
    )


@router.get("/{account_id}/brand-profile", response_model=BrandProfileSchema)
async def get_brand_profile(account_id: str, session: AsyncSession = Depends(get_session)):
    await owned_account(account_id, session)
    profile = (
        await session.execute(select(BrandProfile).where(BrandProfile.account_id == account_id))
    ).scalar_one_or_none()
    if profile is None:
        raise HTTPException(404, "Brand profile not found")
    return profile


@router.put("/{account_id}/brand-profile", response_model=BrandProfileSchema)
async def upsert_brand_profile(
    account_id: str, body: BrandProfileUpdate, session: AsyncSession = Depends(get_session)
):
    await session.execute(text("BEGIN IMMEDIATE"))
    account = await owned_account(account_id, session)
    profile = (
        await session.execute(select(BrandProfile).where(BrandProfile.account_id == account_id))
    ).scalar_one_or_none()
    changes = body.model_dump(exclude_unset=True)
    if profile is None:
        name = changes.pop("brand_name", None) or account.display_name or account.username
        profile = BrandProfile(id=str(uuid4()), account_id=account_id, brand_name=name, **changes)
        session.add(profile)
    else:
        for key, value in changes.items():
            setattr(profile, key, value)
    _audit(session, account_id, "Local brand profile saved")
    await session.commit()
    await session.refresh(profile)
    return profile
