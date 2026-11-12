"""Social accounts, OAuth initiation, and brand profile routes."""

from __future__ import annotations

import secrets
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_auth
from app.database import get_session
from app.models.account import AccountStatus, BrandProfile, Platform, SocialAccount
from app.models.user import User

router = APIRouter(prefix="/accounts", tags=["accounts"], dependencies=[Depends(require_auth)])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class AccountCreate(BaseModel):
    platform: Platform
    username: str = Field(..., min_length=1, max_length=128)
    display_name: Optional[str] = None
    platform_user_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class AccountUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=1, max_length=128)
    display_name: Optional[str] = None
    status: Optional[AccountStatus] = None
    metadata: Optional[dict[str, Any]] = None


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    user_id: str
    platform: Platform
    platform_user_id: Optional[str] = None
    username: str
    display_name: Optional[str] = None
    status: AccountStatus
    token_expires_at: Optional[datetime] = None
    metadata: Optional[dict[str, Any]] = Field(default=None, validation_alias="metadata_")
    created_at: datetime
    updated_at: datetime


class OAuthInitiateRequest(BaseModel):
    redirect_uri: str = "http://localhost:8000/api/accounts/oauth/callback"
    scopes: list[str] = Field(default_factory=list)


class OAuthInitiateResponse(BaseModel):
    account_id: str
    platform: str
    state: str
    authorization_url: str


class BrandProfileSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = None
    account_id: Optional[str] = None
    brand_name: str
    brand_voice: Optional[str] = None
    target_audience: Optional[str] = None
    content_pillars: Optional[list[str]] = None
    hashtag_groups: Optional[dict[str, Any]] = None
    color_palette: Optional[list[str]] = None
    logo_url: Optional[str] = None
    guidelines: Optional[dict[str, Any]] = None


class BrandProfileUpdate(BaseModel):
    brand_name: Optional[str] = None
    brand_voice: Optional[str] = None
    target_audience: Optional[str] = None
    content_pillars: Optional[list[str]] = None
    hashtag_groups: Optional[dict[str, Any]] = None
    color_palette: Optional[list[str]] = None
    logo_url: Optional[str] = None
    guidelines: Optional[dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_OAUTH_AUTH_URLS: dict[Platform, str] = {
    Platform.FACEBOOK: "https://www.facebook.com/v19.0/dialog/oauth",
    Platform.INSTAGRAM: "https://api.instagram.com/oauth/authorize",
    Platform.YOUTUBE: "https://accounts.google.com/o/oauth2/v2/auth",
    Platform.TWITTER: "https://twitter.com/i/oauth2/authorize",
    Platform.LINKEDIN: "https://www.linkedin.com/oauth/v2/authorization",
    Platform.TIKTOK: "https://www.tiktok.com/v2/auth/authorize/",
    Platform.PINTEREST: "https://www.pinterest.com/oauth/",
    Platform.THREADS: "https://threads.net/oauth/authorize",
}


async def _get_account_or_404(
    account_id: str,
    session: AsyncSession,
    user: Optional[dict[str, Any]] = None,
) -> SocialAccount:
    result = await session.execute(select(SocialAccount).where(SocialAccount.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Social account not found")
    if user is not None:
        is_admin = bool(user.get("is_owner")) or str(user.get("role", "")).lower() in {"owner", "admin"}
        if not is_admin and account.user_id != user.get("user_id"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cross-account access denied",
            )
    return account


async def _resolve_user_id(
    requested_user_id: Optional[str],
    session: AsyncSession,
    user: Optional[dict[str, Any]] = None,
) -> str:
    if user is not None:
        is_admin = bool(user.get("is_owner")) or str(user.get("role", "")).lower() in {"owner", "admin"}
        if not is_admin:
            return str(user.get("user_id"))
        if requested_user_id:
            return requested_user_id
        return str(user.get("user_id") or "owner")
    if requested_user_id:
        return requested_user_id
    res = await session.execute(select(User.id).limit(1))
    return res.scalar_one_or_none() or "default-user"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/", response_model=list[AccountResponse])
async def list_accounts(
    platform: Optional[Platform] = None,
    status_filter: Optional[AccountStatus] = Query(default=None, alias="status"),
    user: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> list[AccountResponse]:
    """List all connected social accounts accessible to the current principal."""
    stmt = select(SocialAccount)
    is_admin = bool(user.get("is_owner")) or str(user.get("role", "")).lower() in {"owner", "admin"}
    if not is_admin:
        stmt = stmt.where(SocialAccount.user_id == user.get("user_id"))
    if platform is not None:
        stmt = stmt.where(SocialAccount.platform == platform)
    if status_filter is not None:
        stmt = stmt.where(SocialAccount.status == status_filter)
    result = await session.execute(stmt.order_by(SocialAccount.created_at.desc()))
    return [AccountResponse.model_validate(a) for a in result.scalars().all()]


@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    body: AccountCreate,
    user: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> AccountResponse:
    """Register a new social media account."""
    user_id = await _resolve_user_id(body.user_id, session, user=user)
    account = SocialAccount(
        id=str(uuid4()),
        user_id=user_id,
        platform=body.platform,
        platform_user_id=body.platform_user_id,
        username=body.username,
        display_name=body.display_name,
        status=AccountStatus.DISCONNECTED,
        metadata_=body.metadata,
    )
    session.add(account)
    await session.commit()
    await session.refresh(account)
    return AccountResponse.model_validate(account)


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str,
    user: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> AccountResponse:
    """Retrieve a single social account."""
    account = await _get_account_or_404(account_id, session, user=user)
    return AccountResponse.model_validate(account)


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: str,
    body: AccountUpdate,
    user: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> AccountResponse:
    """Update a social account."""
    account = await _get_account_or_404(account_id, session, user=user)
    data = body.model_dump(exclude_unset=True)
    if "metadata" in data:
        account.metadata_ = data.pop("metadata")
    for key, value in data.items():
        setattr(account, key, value)
    await session.commit()
    await session.refresh(account)
    return AccountResponse.model_validate(account)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: str,
    user: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a social account."""
    account = await _get_account_or_404(account_id, session, user=user)
    await session.delete(account)
    await session.commit()


@router.post("/{account_id}/oauth/initiate", response_model=OAuthInitiateResponse)
async def initiate_oauth(
    account_id: str,
    body: OAuthInitiateRequest,
    user: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> OAuthInitiateResponse:
    """Generate an OAuth authorization URL and state token for the account's platform."""
    account = await _get_account_or_404(account_id, session, user=user)
    platform_enum = Platform(account.platform)
    base_url = _OAUTH_AUTH_URLS.get(platform_enum)
    if not base_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth is not supported for platform '{platform_enum.value}'",
        )

    state = secrets.token_urlsafe(24)
    scope_str = "%20".join(body.scopes)
    auth_url = f"{base_url}?response_type=code&redirect_uri={body.redirect_uri}&state={state}"
    if scope_str:
        auth_url += f"&scope={scope_str}"

    return OAuthInitiateResponse(
        account_id=account.id,
        platform=platform_enum.value,
        state=state,
        authorization_url=auth_url,
    )


@router.get("/{account_id}/brand-profile", response_model=BrandProfileSchema)
async def get_brand_profile(
    account_id: str,
    user: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> BrandProfileSchema:
    """Get the brand profile associated with a social account."""
    await _get_account_or_404(account_id, session, user=user)
    result = await session.execute(
        select(BrandProfile).where(BrandProfile.account_id == account_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand profile not found")
    return BrandProfileSchema.model_validate(profile)


@router.put("/{account_id}/brand-profile", response_model=BrandProfileSchema)
async def upsert_brand_profile(
    account_id: str,
    body: BrandProfileUpdate,
    user: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> BrandProfileSchema:
    """Create or update the brand profile for a social account."""
    account = await _get_account_or_404(account_id, session, user=user)
    result = await session.execute(
        select(BrandProfile).where(BrandProfile.account_id == account_id)
    )
    profile = result.scalar_one_or_none()
    update_data = body.model_dump(exclude_unset=True)

    if profile is None:
        brand_name = update_data.pop("brand_name", None) or account.display_name or account.username
        profile = BrandProfile(
            id=str(uuid4()),
            account_id=account_id,
            brand_name=brand_name,
            **update_data,
        )
        session.add(profile)
    else:
        for key, value in update_data.items():
            setattr(profile, key, value)

    await session.commit()
    await session.refresh(profile)
    return BrandProfileSchema.model_validate(profile)
