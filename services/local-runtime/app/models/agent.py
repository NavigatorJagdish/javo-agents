"""Agent definition, execution, and configuration models."""

import enum
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AgentStatus(str, enum.Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    DISABLED = "disabled"


class ExecutionStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class AgentDefinition(Base):
    __tablename__ = "agent_definitions"

    id: Mapped[str] = mapped_column(sa.String(36), primary_key=True, default=lambda: str(uuid4()))
    agent_key: Mapped[str] = mapped_column(sa.String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(sa.String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(sa.String(64), nullable=True)
    version: Mapped[str] = mapped_column(sa.String(16), default="1.0.0", nullable=False)
    status: Mapped[str] = mapped_column(sa.Enum(AgentStatus), default=AgentStatus.IDLE, nullable=False, index=True)
    capabilities: Mapped[Optional[List[str]]] = mapped_column(sa.JSON, nullable=True)
    input_schema: Mapped[Optional[Dict[str, Any]]] = mapped_column(sa.JSON, nullable=True)
    output_schema: Mapped[Optional[Dict[str, Any]]] = mapped_column(sa.JSON, nullable=True)
    tools: Mapped[Optional[List[str]]] = mapped_column(sa.JSON, nullable=True)
    dependencies: Mapped[Optional[List[str]]] = mapped_column(sa.JSON, nullable=True)
    trust_score: Mapped[float] = mapped_column(sa.Float, default=1.0, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    executions: Mapped[List["AgentExecution"]] = relationship("AgentExecution", back_populates="agent", cascade="all, delete-orphan")
    config: Mapped[Optional["AgentConfig"]] = relationship("AgentConfig", back_populates="agent", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<AgentDefinition id={self.id} key={self.agent_key} status={self.status}>"


class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id: Mapped[str] = mapped_column(sa.String(36), primary_key=True, default=lambda: str(uuid4()))
    agent_id: Mapped[str] = mapped_column(sa.String(36), ForeignKey("agent_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id: Mapped[Optional[str]] = mapped_column(sa.String(36), ForeignKey("tasks.task_id", ondelete="SET NULL"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(sa.Enum(ExecutionStatus), default=ExecutionStatus.QUEUED, nullable=False, index=True)
    inputs: Mapped[Optional[Dict[str, Any]]] = mapped_column(sa.JSON, nullable=True)
    outputs: Mapped[Optional[Dict[str, Any]]] = mapped_column(sa.JSON, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    tokens_used: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)
    cost: Mapped[float] = mapped_column(sa.Float, default=0.0, nullable=False)
    duration_ms: Mapped[Optional[int]] = mapped_column(sa.Integer, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), nullable=False)

    # Relationships
    agent: Mapped["AgentDefinition"] = relationship("AgentDefinition", back_populates="executions")

    def __repr__(self) -> str:
        return f"<AgentExecution id={self.id} agent={self.agent_id} status={self.status}>"


class AgentConfig(Base):
    __tablename__ = "agent_configs"

    id: Mapped[str] = mapped_column(sa.String(36), primary_key=True, default=lambda: str(uuid4()))
    agent_id: Mapped[str] = mapped_column(sa.String(36), ForeignKey("agent_definitions.id", ondelete="CASCADE"), unique=True, nullable=False)
    ai_provider: Mapped[Optional[str]] = mapped_column(sa.String(64), nullable=True)
    ai_model: Mapped[Optional[str]] = mapped_column(sa.String(128), nullable=True)
    temperature: Mapped[float] = mapped_column(sa.Float, default=0.7, nullable=False)
    max_tokens: Mapped[int] = mapped_column(sa.Integer, default=4096, nullable=False)
    system_prompt: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    retry_policy: Mapped[Optional[Dict[str, Any]]] = mapped_column(sa.JSON, nullable=True)
    rate_limits: Mapped[Optional[Dict[str, Any]]] = mapped_column(sa.JSON, nullable=True)
    custom_settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(sa.JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    agent: Mapped["AgentDefinition"] = relationship("AgentDefinition", back_populates="config")

    def __repr__(self) -> str:
        return f"<AgentConfig id={self.id} agent={self.agent_id}>"
