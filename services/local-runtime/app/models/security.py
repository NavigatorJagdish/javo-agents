"""Security models: audit log, permissions, sessions, trusted devices."""

import enum
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AuditAction(str, enum.Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    APPROVE = "approve"
    REJECT = "reject"
    PUBLISH = "publish"
    ACCESS = "access"
    EMERGENCY_STOP = "emergency_stop"
    CONFIG_CHANGE = "config_change"
    PERMISSION_CHANGE = "permission_change"


class AuditSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class PermissionAction(str, enum.Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    ADMIN = "admin"


class SessionStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(sa.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[Optional[str]] = mapped_column(sa.String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    agent_id: Mapped[Optional[str]] = mapped_column(sa.String(128), nullable=True, index=True)
    action: Mapped[str] = mapped_column(sa.Enum(AuditAction), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(sa.Enum(AuditSeverity), default=AuditSeverity.INFO, nullable=False, index=True)
    resource_type: Mapped[Optional[str]] = mapped_column(sa.String(64), nullable=True)
    resource_id: Mapped[Optional[str]] = mapped_column(sa.String(36), nullable=True)
    description: Mapped[str] = mapped_column(sa.Text, nullable=False)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(sa.JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(sa.String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(sa.String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} action={self.action} severity={self.severity}>"


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[str] = mapped_column(sa.String(36), primary_key=True, default=lambda: str(uuid4()))
    subject_type: Mapped[str] = mapped_column(sa.String(32), nullable=False, index=True)  # "user" or "agent"
    subject_id: Mapped[str] = mapped_column(sa.String(128), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(sa.String(64), nullable=False, index=True)
    resource_id: Mapped[Optional[str]] = mapped_column(sa.String(36), nullable=True)  # null = all of type
    action: Mapped[str] = mapped_column(sa.Enum(PermissionAction), nullable=False)
    is_allowed: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)
    conditions: Mapped[Optional[Dict[str, Any]]] = mapped_column(sa.JSON, nullable=True)
    granted_by: Mapped[Optional[str]] = mapped_column(sa.String(36), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        sa.UniqueConstraint("subject_type", "subject_id", "resource_type", "resource_id", "action", name="uq_permission"),
    )

    def __repr__(self) -> str:
        return f"<Permission id={self.id} {self.subject_type}:{self.subject_id} -> {self.resource_type}:{self.action}>"


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(sa.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(sa.String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id: Mapped[Optional[str]] = mapped_column(sa.String(36), ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    token_hash: Mapped[str] = mapped_column(sa.String(256), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(sa.Enum(SessionStatus), default=SessionStatus.ACTIVE, nullable=False, index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(sa.String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(sa.String(512), nullable=True)
    last_active: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(sa.DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<Session id={self.id} user={self.user_id} status={self.status}>"


class TrustedDevice(Base):
    __tablename__ = "trusted_devices"

    id: Mapped[str] = mapped_column(sa.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(sa.String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_fingerprint: Mapped[str] = mapped_column(sa.String(256), nullable=False)
    device_name: Mapped[str] = mapped_column(sa.String(128), nullable=False)
    platform: Mapped[Optional[str]] = mapped_column(sa.String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)
    last_verified: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), nullable=False)
    trusted_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, nullable=True)

    __table_args__ = (
        sa.UniqueConstraint("user_id", "device_fingerprint", name="uq_trusted_device"),
    )

    def __repr__(self) -> str:
        return f"<TrustedDevice id={self.id} name={self.device_name} active={self.is_active}>"
