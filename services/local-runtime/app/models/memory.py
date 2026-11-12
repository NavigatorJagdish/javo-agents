"""Memory, Preference, and Instruction models for agent memory system."""

import enum
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MemoryType(str, enum.Enum):
    FACT = "fact"
    PREFERENCE = "preference"
    INTERACTION = "interaction"
    OBSERVATION = "observation"
    FEEDBACK = "feedback"
    CONTEXT = "context"


class InstructionScope(str, enum.Enum):
    GLOBAL = "global"
    AGENT = "agent"
    TASK = "task"
    ACCOUNT = "account"
    CONTENT = "content"


class Importance(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MemoryEntry(Base):
    __tablename__ = "memory_entries"

    id: Mapped[str] = mapped_column(sa.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(sa.String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    memory_type: Mapped[str] = mapped_column(sa.Enum(MemoryType), nullable=False, index=True)
    key: Mapped[str] = mapped_column(sa.String(256), nullable=False, index=True)
    content: Mapped[str] = mapped_column(sa.Text, nullable=False)
    importance: Mapped[str] = mapped_column(sa.Enum(Importance), default=Importance.MEDIUM, nullable=False)
    source_agent: Mapped[Optional[str]] = mapped_column(sa.String(128), nullable=True)
    context: Mapped[Optional[Dict[str, Any]]] = mapped_column(sa.JSON, nullable=True)
    embedding: Mapped[Optional[List[float]]] = mapped_column(sa.JSON, nullable=True)
    access_count: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)
    last_accessed: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<MemoryEntry id={self.id} type={self.memory_type} key={self.key}>"


class Preference(Base):
    __tablename__ = "preferences"

    id: Mapped[str] = mapped_column(sa.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(sa.String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(sa.String(64), nullable=False, index=True)
    key: Mapped[str] = mapped_column(sa.String(128), nullable=False, index=True)
    value: Mapped[str] = mapped_column(sa.Text, nullable=False)
    confidence: Mapped[float] = mapped_column(sa.Float, default=0.5, nullable=False)
    learned_from: Mapped[Optional[str]] = mapped_column(sa.String(256), nullable=True)
    is_explicit: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        sa.UniqueConstraint("user_id", "category", "key", name="uq_user_pref"),
    )

    def __repr__(self) -> str:
        return f"<Preference id={self.id} category={self.category} key={self.key}>"


class Instruction(Base):
    __tablename__ = "instructions"

    id: Mapped[str] = mapped_column(sa.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(sa.String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    scope: Mapped[str] = mapped_column(sa.Enum(InstructionScope), default=InstructionScope.GLOBAL, nullable=False, index=True)
    scope_target: Mapped[Optional[str]] = mapped_column(sa.String(128), nullable=True)
    instruction: Mapped[str] = mapped_column(sa.Text, nullable=False)
    priority: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<Instruction id={self.id} scope={self.scope} active={self.is_active}>"
