"""Durable approval snapshots and dispatch receipts; additive schema only."""

import sqlalchemy as sa
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PublicationApproval(Base):
    __tablename__ = "publication_approvals"
    schedule_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    fingerprint: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    mode: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    approved_by: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class PublicationAttempt(Base):
    __tablename__ = "publication_attempts"
    id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    schedule_id: Mapped[str] = mapped_column(sa.String(36), unique=True, nullable=False)
    dedupe_key: Mapped[str] = mapped_column(sa.String(64), unique=True, nullable=False)
    state: Mapped[str] = mapped_column(sa.String(24), nullable=False)
    mode: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    post_id: Mapped[str | None] = mapped_column(sa.String(256), nullable=True)
    error: Mapped[str | None] = mapped_column(sa.String(512), nullable=True)


class PublicationTimer(Base):
    __tablename__ = "publication_timers"
    schedule_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    fingerprint: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    due_at: Mapped[datetime] = mapped_column(sa.DateTime, nullable=False, index=True)
    state: Mapped[str] = mapped_column(sa.String(24), nullable=False, index=True)
    reason: Mapped[str | None] = mapped_column(sa.String(256), nullable=True)
