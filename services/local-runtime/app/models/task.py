"""Task, Goal, and Milestone models."""

import enum
from datetime import datetime
from typing import Optional, List, Any, Dict
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TaskState(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class GoalStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Task(Base):
    __tablename__ = "tasks"

    task_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True, default=lambda: str(uuid4()))
    goal_id: Mapped[Optional[str]] = mapped_column(sa.String(36), ForeignKey("goals.goal_id", ondelete="SET NULL"), nullable=True, index=True)
    account_id: Mapped[Optional[str]] = mapped_column(sa.String(36), ForeignKey("social_accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_agent: Mapped[Optional[str]] = mapped_column(sa.String(128), nullable=True, index=True)
    title: Mapped[str] = mapped_column(sa.String(256), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    inputs: Mapped[Optional[Dict[str, Any]]] = mapped_column(sa.JSON, nullable=True)
    outputs: Mapped[Optional[Dict[str, Any]]] = mapped_column(sa.JSON, nullable=True)
    permissions: Mapped[Optional[Dict[str, Any]]] = mapped_column(sa.JSON, nullable=True)
    state: Mapped[str] = mapped_column(sa.Enum(TaskState), default=TaskState.PENDING, nullable=False, index=True)
    priority: Mapped[str] = mapped_column(sa.Enum(TaskPriority), default=TaskPriority.NORMAL, nullable=False, index=True)
    deadline: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, nullable=True)
    retry_budget: Mapped[int] = mapped_column(sa.Integer, default=3, nullable=False)
    cost_budget: Mapped[Optional[float]] = mapped_column(sa.Float, nullable=True)
    resource_budget: Mapped[Optional[Dict[str, Any]]] = mapped_column(sa.JSON, nullable=True)
    failure_history: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(sa.JSON, nullable=True)
    audit_trail: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(sa.JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, nullable=True)

    # Relationships
    goal: Mapped[Optional["Goal"]] = relationship("Goal", back_populates="tasks")

    def __repr__(self) -> str:
        return f"<Task id={self.task_id} title={self.title} state={self.state}>"


class Goal(Base):
    __tablename__ = "goals"

    goal_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True, default=lambda: str(uuid4()))
    title: Mapped[str] = mapped_column(sa.String(256), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    owner_id: Mapped[str] = mapped_column(sa.String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    target_metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(sa.JSON, nullable=True)
    progress: Mapped[float] = mapped_column(sa.Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(sa.Enum(GoalStatus), default=GoalStatus.ACTIVE, nullable=False, index=True)
    deadline: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="goals")
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="goal", cascade="all, delete-orphan")
    milestones: Mapped[List["Milestone"]] = relationship("Milestone", back_populates="goal", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Goal id={self.goal_id} title={self.title} progress={self.progress}>"


class Milestone(Base):
    __tablename__ = "milestones"

    id: Mapped[str] = mapped_column(sa.String(36), primary_key=True, default=lambda: str(uuid4()))
    goal_id: Mapped[str] = mapped_column(sa.String(36), ForeignKey("goals.goal_id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(sa.String(256), nullable=False)
    target_value: Mapped[float] = mapped_column(sa.Float, default=100.0, nullable=False)
    current_value: Mapped[float] = mapped_column(sa.Float, default=0.0, nullable=False)
    is_completed: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)
    due_date: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, nullable=True)

    # Relationships
    goal: Mapped["Goal"] = relationship("Goal", back_populates="milestones")

    def __repr__(self) -> str:
        return f"<Milestone id={self.id} title={self.title} completed={self.is_completed}>"
