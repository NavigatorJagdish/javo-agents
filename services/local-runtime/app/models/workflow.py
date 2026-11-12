"""Workflow models for visual workflow builder."""

import enum
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class WorkflowStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class NodeType(str, enum.Enum):
    TRIGGER = "trigger"
    SCHEDULE = "schedule"
    FOLDER_WATCHER = "folder_watcher"
    ACCOUNT_EVENT = "account_event"
    CONTENT_ANALYZER = "content_analyzer"
    AI_PROMPT = "ai_prompt"
    CONDITION = "condition"
    APPROVAL = "approval"
    PUBLISH = "publish"
    COMMENT_REPLY = "comment_reply"
    NOTIFICATION = "notification"
    ANALYTICS = "analytics"
    DELAY = "delay"
    RETRY = "retry"
    ERROR_HANDLER = "error_handler"
    END = "end"


class WorkflowExecutionStatus(str, enum.Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING_APPROVAL = "waiting_approval"


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[str] = mapped_column(sa.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(sa.String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(sa.String(256), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    status: Mapped[str] = mapped_column(sa.Enum(WorkflowStatus), default=WorkflowStatus.DRAFT, nullable=False, index=True)
    trigger_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(sa.JSON, nullable=True)
    viewport: Mapped[Optional[Dict[str, Any]]] = mapped_column(sa.JSON, nullable=True)
    run_count: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    nodes: Mapped[List["WorkflowNode"]] = relationship("WorkflowNode", back_populates="workflow", cascade="all, delete-orphan")
    edges: Mapped[List["WorkflowEdge"]] = relationship("WorkflowEdge", back_populates="workflow", cascade="all, delete-orphan")
    executions: Mapped[List["WorkflowExecution"]] = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Workflow id={self.id} name={self.name} status={self.status}>"


class WorkflowNode(Base):
    __tablename__ = "workflow_nodes"

    id: Mapped[str] = mapped_column(sa.String(36), primary_key=True, default=lambda: str(uuid4()))
    workflow_id: Mapped[str] = mapped_column(sa.String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    node_type: Mapped[str] = mapped_column(sa.Enum(NodeType), nullable=False)
    label: Mapped[str] = mapped_column(sa.String(128), nullable=False)
    position_x: Mapped[float] = mapped_column(sa.Float, default=0.0, nullable=False)
    position_y: Mapped[float] = mapped_column(sa.Float, default=0.0, nullable=False)
    config: Mapped[Optional[Dict[str, Any]]] = mapped_column(sa.JSON, nullable=True)
    is_entry_point: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)

    # Relationships
    workflow: Mapped["Workflow"] = relationship("Workflow", back_populates="nodes")

    def __repr__(self) -> str:
        return f"<WorkflowNode id={self.id} type={self.node_type} label={self.label}>"


class WorkflowEdge(Base):
    __tablename__ = "workflow_edges"

    id: Mapped[str] = mapped_column(sa.String(36), primary_key=True, default=lambda: str(uuid4()))
    workflow_id: Mapped[str] = mapped_column(sa.String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    source_node_id: Mapped[str] = mapped_column(sa.String(36), ForeignKey("workflow_nodes.id", ondelete="CASCADE"), nullable=False)
    target_node_id: Mapped[str] = mapped_column(sa.String(36), ForeignKey("workflow_nodes.id", ondelete="CASCADE"), nullable=False)
    condition: Mapped[Optional[str]] = mapped_column(sa.String(256), nullable=True)
    label: Mapped[Optional[str]] = mapped_column(sa.String(128), nullable=True)

    # Relationships
    workflow: Mapped["Workflow"] = relationship("Workflow", back_populates="edges")

    def __repr__(self) -> str:
        return f"<WorkflowEdge id={self.id} {self.source_node_id} -> {self.target_node_id}>"


class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"

    id: Mapped[str] = mapped_column(sa.String(36), primary_key=True, default=lambda: str(uuid4()))
    workflow_id: Mapped[str] = mapped_column(sa.String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(sa.Enum(WorkflowExecutionStatus), default=WorkflowExecutionStatus.RUNNING, nullable=False, index=True)
    trigger_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(sa.JSON, nullable=True)
    current_node_id: Mapped[Optional[str]] = mapped_column(sa.String(36), nullable=True)
    execution_log: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(sa.JSON, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, nullable=True)

    # Relationships
    workflow: Mapped["Workflow"] = relationship("Workflow", back_populates="executions")

    def __repr__(self) -> str:
        return f"<WorkflowExecution id={self.id} workflow={self.workflow_id} status={self.status}>"
