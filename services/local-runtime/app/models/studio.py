"""Actual external local-generation receipts and source-labelled trend snapshots."""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import String, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class StudioJob(Base):
    __tablename__ = 'studio_jobs'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    request_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    prompt_id: Mapped[str] = mapped_column(String(36), nullable=False)
    request: Mapped[dict] = mapped_column(JSON, nullable=False)
    configuration: Mapped[dict] = mapped_column(JSON, nullable=False)
    artifact: Mapped[dict | None] = mapped_column(JSON)
    message: Mapped[str] = mapped_column(String(400), default='', nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TrendSnapshot(Base):
    __tablename__ = 'trend_snapshots'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    country: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(200), nullable=False)
    items: Mapped[list] = mapped_column(JSON, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
