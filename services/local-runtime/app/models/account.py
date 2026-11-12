"""Social Account and Brand Profile models."""

import enum
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Platform(str, enum.Enum):
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    PINTEREST = "pinterest"
    THREADS = "threads"
    TELEGRAM = "telegram"
    OTHER = "other"


class AccountStatus(str, enum.Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    EXPIRED = "expired"
    ERROR = "error"


class SocialAccount(Base):
    __tablename__ = "social_accounts"

    id: Mapped[str] = mapped_column(sa.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(sa.String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    platform: Mapped[str] = mapped_column(sa.Enum(Platform), nullable=False, index=True)
    platform_user_id: Mapped[Optional[str]] = mapped_column(sa.String(128), nullable=True)
    username: Mapped[str] = mapped_column(sa.String(128), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(sa.String(256), nullable=True)
    access_token: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, nullable=True)
    status: Mapped[str] = mapped_column(sa.Enum(AccountStatus), default=AccountStatus.CONNECTED, nullable=False)
    metadata_: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", sa.JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    brand_profile: Mapped[Optional["BrandProfile"]] = relationship("BrandProfile", back_populates="account", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<SocialAccount id={self.id} platform={self.platform} username={self.username}>"


class BrandProfile(Base):
    __tablename__ = "brand_profiles"

    id: Mapped[str] = mapped_column(sa.String(36), primary_key=True, default=lambda: str(uuid4()))
    account_id: Mapped[str] = mapped_column(sa.String(36), ForeignKey("social_accounts.id", ondelete="CASCADE"), unique=True, nullable=False)
    brand_name: Mapped[str] = mapped_column(sa.String(128), nullable=False)
    brand_voice: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    target_audience: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    content_pillars: Mapped[Optional[List[str]]] = mapped_column(sa.JSON, nullable=True)
    hashtag_groups: Mapped[Optional[Dict[str, Any]]] = mapped_column(sa.JSON, nullable=True)
    color_palette: Mapped[Optional[List[str]]] = mapped_column(sa.JSON, nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(sa.String(512), nullable=True)
    guidelines: Mapped[Optional[Dict[str, Any]]] = mapped_column(sa.JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    account: Mapped["SocialAccount"] = relationship("SocialAccount", back_populates="brand_profile")

    def __repr__(self) -> str:
        return f"<BrandProfile id={self.id} brand={self.brand_name}>"
