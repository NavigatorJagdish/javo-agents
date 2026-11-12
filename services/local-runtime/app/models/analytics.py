"""Analytics models for metrics, snapshots, and experiments."""

import enum
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MetricType(str, enum.Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    RATE = "rate"
    PERCENTAGE = "percentage"


class MetricCategory(str, enum.Enum):
    ENGAGEMENT = "engagement"
    GROWTH = "growth"
    CONTENT = "content"
    REVENUE = "revenue"
    AGENT = "agent"
    SYSTEM = "system"


class ExperimentStatus(str, enum.Enum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Metric(Base):
    __tablename__ = "metrics"

    id: Mapped[str] = mapped_column(sa.String(36), primary_key=True, default=lambda: str(uuid4()))
    account_id: Mapped[Optional[str]] = mapped_column(sa.String(36), ForeignKey("social_accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(sa.String(128), nullable=False, index=True)
    metric_type: Mapped[str] = mapped_column(sa.Enum(MetricType), nullable=False)
    category: Mapped[str] = mapped_column(sa.Enum(MetricCategory), nullable=False, index=True)
    value: Mapped[float] = mapped_column(sa.Float, nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(sa.String(32), nullable=True)
    dimensions: Mapped[Optional[Dict[str, Any]]] = mapped_column(sa.JSON, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<Metric id={self.id} name={self.name} value={self.value}>"


class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"

    id: Mapped[str] = mapped_column(sa.String(36), primary_key=True, default=lambda: str(uuid4()))
    account_id: Mapped[Optional[str]] = mapped_column(sa.String(36), ForeignKey("social_accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    snapshot_type: Mapped[str] = mapped_column(sa.String(64), nullable=False, index=True)
    period_start: Mapped[datetime] = mapped_column(sa.DateTime, nullable=False)
    period_end: Mapped[datetime] = mapped_column(sa.DateTime, nullable=False)
    data: Mapped[Dict[str, Any]] = mapped_column(sa.JSON, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    comparison: Mapped[Optional[Dict[str, Any]]] = mapped_column(sa.JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<AnalyticsSnapshot id={self.id} type={self.snapshot_type}>"


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[str] = mapped_column(sa.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(sa.String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(sa.String(256), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    hypothesis: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    status: Mapped[str] = mapped_column(sa.Enum(ExperimentStatus), default=ExperimentStatus.DRAFT, nullable=False, index=True)
    variants: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(sa.JSON, nullable=True)
    target_metric: Mapped[Optional[str]] = mapped_column(sa.String(128), nullable=True)
    results: Mapped[Optional[Dict[str, Any]]] = mapped_column(sa.JSON, nullable=True)
    winner: Mapped[Optional[str]] = mapped_column(sa.String(64), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<Experiment id={self.id} name={self.name} status={self.status}>"
