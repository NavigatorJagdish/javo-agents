"""Task management routes — CRUD, execution, and audit history."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.task import Task, TaskPriority, TaskState

router = APIRouter(prefix="/tasks", tags=["tasks"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    description: Optional[str] = None
    assigned_agent: Optional[str] = None
    goal_id: Optional[str] = None
    account_id: Optional[str] = None
    priority: TaskPriority = TaskPriority.NORMAL
    inputs: Optional[dict[str, Any]] = None
    permissions: Optional[dict[str, Any]] = None
    deadline: Optional[datetime] = None
    retry_budget: int = Field(default=3, ge=0)
    cost_budget: Optional[float] = Field(default=None, ge=0.0)
    resource_budget: Optional[dict[str, Any]] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=256)
    description: Optional[str] = None
    assigned_agent: Optional[str] = None
    priority: Optional[TaskPriority] = None
    state: Optional[TaskState] = None
    inputs: Optional[dict[str, Any]] = None
    outputs: Optional[dict[str, Any]] = None
    permissions: Optional[dict[str, Any]] = None
    deadline: Optional[datetime] = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: str
    goal_id: Optional[str] = None
    account_id: Optional[str] = None
    assigned_agent: Optional[str] = None
    title: str
    description: Optional[str] = None
    inputs: Optional[dict[str, Any]] = None
    outputs: Optional[dict[str, Any]] = None
    permissions: Optional[dict[str, Any]] = None
    state: TaskState
    priority: TaskPriority
    deadline: Optional[datetime] = None
    retry_budget: int = 3
    cost_budget: Optional[float] = None
    resource_budget: Optional[dict[str, Any]] = None
    failure_history: Optional[list[dict[str, Any]]] = None
    audit_trail: Optional[list[dict[str, Any]]] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


class TaskHistoryEntry(BaseModel):
    timestamp: str
    action: str
    actor: Optional[str] = None
    details: dict[str, Any] = Field(default_factory=dict)


class ExecuteTaskResponse(BaseModel):
    task_id: str
    state: str
    message: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _get_task_or_404(task_id: str, session: AsyncSession) -> Task:
    result = await session.execute(select(Task).where(Task.task_id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/", response_model=list[TaskResponse])
async def list_tasks(
    status_filter: Optional[TaskState] = Query(default=None, alias="status"),
    agent: Optional[str] = None,
    priority: Optional[TaskPriority] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[TaskResponse]:
    """List tasks with optional filters for status (state), agent, and priority."""
    stmt = select(Task)
    if status_filter is not None:
        stmt = stmt.where(Task.state == status_filter)
    if agent is not None:
        stmt = stmt.where(Task.assigned_agent == agent)
    if priority is not None:
        stmt = stmt.where(Task.priority == priority)
    stmt = stmt.order_by(Task.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(stmt)
    return [TaskResponse.model_validate(t) for t in result.scalars().all()]


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    body: TaskCreate,
    session: AsyncSession = Depends(get_session),
) -> TaskResponse:
    """Create a new task with an initial audit trail entry."""
    now = datetime.now(timezone.utc).isoformat()
    task = Task(
        task_id=str(uuid4()),
        title=body.title,
        description=body.description,
        assigned_agent=body.assigned_agent,
        goal_id=body.goal_id,
        account_id=body.account_id,
        priority=body.priority,
        inputs=body.inputs,
        permissions=body.permissions,
        deadline=body.deadline,
        retry_budget=body.retry_budget,
        cost_budget=body.cost_budget,
        resource_budget=body.resource_budget,
        state=TaskState.PENDING,
        audit_trail=[{"timestamp": now, "action": "created", "details": {"priority": body.priority.value}}],
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return TaskResponse.model_validate(task)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, session: AsyncSession = Depends(get_session)) -> TaskResponse:
    """Retrieve a single task by ID."""
    task = await _get_task_or_404(task_id, session)
    return TaskResponse.model_validate(task)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    body: TaskUpdate,
    session: AsyncSession = Depends(get_session),
) -> TaskResponse:
    """Update fields of an existing task."""
    task = await _get_task_or_404(task_id, session)
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    trail = list(task.audit_trail or [])
    trail.append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "updated",
            "details": {"fields": list(update_data.keys())},
        }
    )
    task.audit_trail = trail

    await session.commit()
    await session.refresh(task)
    return TaskResponse.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: str, session: AsyncSession = Depends(get_session)) -> None:
    """Delete a task."""
    task = await _get_task_or_404(task_id, session)
    await session.delete(task)
    await session.commit()


@router.post("/{task_id}/execute", response_model=ExecuteTaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def execute_task(task_id: str, session: AsyncSession = Depends(get_session)) -> ExecuteTaskResponse:
    """Start or queue a task for execution."""
    task = await _get_task_or_404(task_id, session)
    if task.state == TaskState.RUNNING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Task is already running")

    task.state = TaskState.RUNNING
    trail = list(task.audit_trail or [])
    trail.append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "execute_requested",
            "details": {"assigned_agent": task.assigned_agent},
        }
    )
    task.audit_trail = trail

    await session.commit()
    return ExecuteTaskResponse(
        task_id=task_id,
        state=TaskState.RUNNING.value,
        message="Task dispatched for execution",
    )


@router.get("/{task_id}/history", response_model=list[TaskHistoryEntry])
async def task_history(task_id: str, session: AsyncSession = Depends(get_session)) -> list[TaskHistoryEntry]:
    """Return the audit trail for a task."""
    task = await _get_task_or_404(task_id, session)
    trail = task.audit_trail or []
    return [TaskHistoryEntry(**entry) for entry in trail]
