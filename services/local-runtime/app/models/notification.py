"""Notification and Alert models."""

import enum
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class NotificationType(str, enum.Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    APPROVAL = "approval"
    TASK = "task"
    SYSTEM = "system"


class NotificationChannel(str, enum.Enum):
    IN_APP = "in_app"
    PUSH = "push"
    EMAIL = "email"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"


class AlertSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, enum.Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SILENCED = "silenced"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(sa.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(sa.String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    notification_type: Mapped[str] = mapped_column(sa.Enum(NotificationType), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(sa.Enum(NotificationChannel), default=NotificationChannel.IN_APP, nullable=False)
    title: Mapped[str] = mapped_column(sa.String(256), nullable=False)
    message: Mapped[str] = mapped_column(sa.Text, nullable=False)
    data: Mapped[Optional[Dict[str, Any]]] = mapped_column(sa.JSON, nullable=True)
    action_url: Mapped[Optional[str]] = mapped_column(sa.String(512), nullable=True)
    is_read: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False, index=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<Notification id={self.id} type={self.notification_type} read={self.is_read}>"


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(sa.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(sa.String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source: Mapped[str] = mapped_column(sa.String(128), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(sa.Enum(AlertSeverity), nullable=False, index=True)
    status: Mapped[str] = mapped_column(sa.Enum(AlertStatus), default=AlertStatus.ACTIVE, nullable=False, index=True)
    title: Mapped[str] = mapped_column(sa.String(256), nullable=False)
    message: Mapped[str] = mapped_column(sa.Text, nullable=False)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(sa.JSON, nullable=True)
    threshold: Mapped[Optional[float]] = mapped_column(sa.Float, nullable=True)
    current_value: Mapped[Optional[float]] = mapped_column(sa.Float, nullable=True)
    acknowledged_by: Mapped[Optional[str]] = mapped_column(sa.String(36), nullable=True)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<Alert id={self.id} severity={self.severity} status={self.status}>"
