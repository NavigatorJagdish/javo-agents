"""Content management models."""

import enum
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.account import Platform


class AssetType(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    TEXT = "text"
    CAROUSEL = "carousel"
    STORY = "story"
    REEL = "reel"


class AssetStatus(str, enum.Enum):
    DRAFT = "draft"
    READY = "ready"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    FAILED = "failed"


class ScheduleStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PublishStatus(str, enum.Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class ContentAsset(Base):
    __tablename__ = "content_assets"

    id: Mapped[str] = mapped_column(sa.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(sa.String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(sa.String(256), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    asset_type: Mapped[str] = mapped_column(sa.Enum(AssetType), nullable=False, index=True)
    status: Mapped[str] = mapped_column(sa.Enum(AssetStatus), default=AssetStatus.DRAFT, nullable=False, index=True)
    file_path: Mapped[Optional[str]] = mapped_column(sa.String(512), nullable=True)
    file_url: Mapped[Optional[str]] = mapped_column(sa.String(512), nullable=True)
    content_text: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    hashtags: Mapped[Optional[List[str]]] = mapped_column(sa.JSON, nullable=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(sa.JSON, nullable=True)
    ai_generated: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)
    ai_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(sa.JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    schedules: Mapped[List["ContentSchedule"]] = relationship("ContentSchedule", back_populates="asset", cascade="all, delete-orphan")
    media_metadata: Mapped[Optional["MediaMetadata"]] = relationship("MediaMetadata", back_populates="asset", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ContentAsset id={self.id} title={self.title} type={self.asset_type}>"


class ContentSchedule(Base):
    __tablename__ = "content_schedules"

    id: Mapped[str] = mapped_column(sa.String(36), primary_key=True, default=lambda: str(uuid4()))
    asset_id: Mapped[str] = mapped_column(sa.String(36), ForeignKey("content_assets.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id: Mapped[str] = mapped_column(sa.String(36), ForeignKey("social_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    scheduled_at: Mapped[datetime] = mapped_column(sa.DateTime, nullable=False, index=True)
    status: Mapped[str] = mapped_column(sa.Enum(ScheduleStatus), default=ScheduleStatus.PENDING, nullable=False, index=True)
    caption: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    platform_options: Mapped[Optional[Dict[str, Any]]] = mapped_column(sa.JSON, nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(sa.String(36), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    asset: Mapped["ContentAsset"] = relationship("ContentAsset", back_populates="schedules")
    publish_records: Mapped[List["PublishRecord"]] = relationship("PublishRecord", back_populates="schedule", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ContentSchedule id={self.id} asset={self.asset_id} at={self.scheduled_at}>"


class PublishRecord(Base):
    __tablename__ = "publish_records"

    id: Mapped[str] = mapped_column(sa.String(36), primary_key=True, default=lambda: str(uuid4()))
    schedule_id: Mapped[str] = mapped_column(sa.String(36), ForeignKey("content_schedules.id", ondelete="CASCADE"), nullable=False, index=True)
    platform: Mapped[Platform] = mapped_column(sa.Enum(Platform), nullable=False)
    platform_post_id: Mapped[Optional[str]] = mapped_column(sa.String(256), nullable=True)
    platform_url: Mapped[Optional[str]] = mapped_column(sa.String(512), nullable=True)
    status: Mapped[str] = mapped_column(sa.Enum(PublishStatus), nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    engagement_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(sa.JSON, nullable=True)
    published_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), nullable=False)

    # Relationships
    schedule: Mapped["ContentSchedule"] = relationship("ContentSchedule", back_populates="publish_records")

    def __repr__(self) -> str:
        return f"<PublishRecord id={self.id} platform={self.platform} status={self.status}>"


class MediaMetadata(Base):
    __tablename__ = "media_metadata"

    id: Mapped[str] = mapped_column(sa.String(36), primary_key=True, default=lambda: str(uuid4()))
    asset_id: Mapped[str] = mapped_column(sa.String(36), ForeignKey("content_assets.id", ondelete="CASCADE"), unique=True, nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(sa.String(128), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(sa.BigInteger, nullable=True)
    width: Mapped[Optional[int]] = mapped_column(sa.Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(sa.Integer, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(sa.Float, nullable=True)
    bitrate: Mapped[Optional[int]] = mapped_column(sa.Integer, nullable=True)
    codec: Mapped[Optional[str]] = mapped_column(sa.String(64), nullable=True)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(sa.String(512), nullable=True)
    exif_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(sa.JSON, nullable=True)
    ai_analysis: Mapped[Optional[Dict[str, Any]]] = mapped_column(sa.JSON, nullable=True)

    # Relationships
    asset: Mapped["ContentAsset"] = relationship("ContentAsset", back_populates="media_metadata")

    def __repr__(self) -> str:
        return f"<MediaMetadata id={self.id} asset={self.asset_id} mime={self.mime_type}>"
