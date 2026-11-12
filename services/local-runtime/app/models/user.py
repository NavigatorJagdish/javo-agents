"""User and Device models."""

import enum
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class DeviceType(str, enum.Enum):
    MOBILE = "mobile"
    DESKTOP = "desktop"
    TABLET = "tablet"
    BROWSER = "browser"
    OTHER = "other"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(sa.String(36), primary_key=True, default=lambda: str(uuid4()))
    username: Mapped[str] = mapped_column(sa.String(64), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(sa.String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    role: Mapped[str] = mapped_column(sa.Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    devices: Mapped[List["Device"]] = relationship("Device", back_populates="user", cascade="all, delete-orphan")
    goals: Mapped[List["Goal"]] = relationship("Goal", back_populates="owner", lazy="selectin")

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username}>"


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(sa.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(sa.String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_name: Mapped[str] = mapped_column(sa.String(128), nullable=False)
    device_type: Mapped[str] = mapped_column(sa.Enum(DeviceType), default=DeviceType.OTHER, nullable=False)
    platform: Mapped[Optional[str]] = mapped_column(sa.String(64), nullable=True)
    push_token: Mapped[Optional[str]] = mapped_column(sa.String(512), nullable=True)
    last_seen: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, nullable=True)
    is_trusted: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)
    paired_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="devices")

    def __repr__(self) -> str:
        return f"<Device id={self.id} name={self.device_name} user={self.user_id}>"
