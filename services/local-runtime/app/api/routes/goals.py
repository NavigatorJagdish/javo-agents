"""Goal management routes — CRUD, progress tracking, and milestones."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_auth
from app.database import get_session
from app.models.task import Goal, GoalStatus, Milestone
from app.models.user import User

router = APIRouter(prefix="/goals", tags=["goals"], dependencies=[Depends(require_auth)])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class GoalCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    description: Optional[str] = None
    owner_id: Optional[str] = None
    target_metrics: Optional[dict[str, Any]] = None
    deadline: Optional[datetime] = None


class GoalUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=256)
    description: Optional[str] = None
    target_metrics: Optional[dict[str, Any]] = None
    progress: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    status: Optional[GoalStatus] = None
    deadline: Optional[datetime] = None


class GoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    goal_id: str
    title: str
    description: Optional[str] = None
    owner_id: str
    target_metrics: Optional[dict[str, Any]] = None
    progress: float = 0.0
    status: GoalStatus = GoalStatus.ACTIVE
    deadline: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ProgressResponse(BaseModel):
    goal_id: str
    title: str
    progress: float
    total_milestones: int
    completed_milestones: int
    status: str


class MilestoneCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    target_value: float = 100.0
    current_value: float = 0.0
    due_date: Optional[datetime] = None


class MilestoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    goal_id: str
    title: str
    target_value: float = 100.0
    current_value: float = 0.0
    is_completed: bool = False
    due_date: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _get_goal_or_404(goal_id: str, session: AsyncSession) -> Goal:
    result = await session.execute(select(Goal).where(Goal.goal_id == goal_id))
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    return goal


async def _resolve_owner_id(requested_owner_id: Optional[str], session: AsyncSession) -> str:
    if requested_owner_id:
        return requested_owner_id
    res = await session.execute(select(User.id).limit(1))
    user_id = res.scalar_one_or_none()
    return user_id or "default-user"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/", response_model=list[GoalResponse])
async def list_goals(
    status_filter: Optional[GoalStatus] = Query(default=None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[GoalResponse]:
    """List all goals with optional status filter."""
    stmt = select(Goal)
    if status_filter is not None:
        stmt = stmt.where(Goal.status == status_filter)
    stmt = stmt.order_by(Goal.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(stmt)
    return [GoalResponse.model_validate(g) for g in result.scalars().all()]


@router.post("/", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(body: GoalCreate, session: AsyncSession = Depends(get_session)) -> GoalResponse:
    """Create a new goal."""
    owner_id = await _resolve_owner_id(body.owner_id, session)
    goal = Goal(
        goal_id=str(uuid4()),
        title=body.title,
        description=body.description,
        owner_id=owner_id,
        target_metrics=body.target_metrics,
        deadline=body.deadline,
        status=GoalStatus.ACTIVE,
        progress=0.0,
    )
    session.add(goal)
    await session.commit()
    await session.refresh(goal)
    return GoalResponse.model_validate(goal)


@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(goal_id: str, session: AsyncSession = Depends(get_session)) -> GoalResponse:
    """Get a single goal."""
    goal = await _get_goal_or_404(goal_id, session)
    return GoalResponse.model_validate(goal)


@router.put("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: str,
    body: GoalUpdate,
    session: AsyncSession = Depends(get_session),
) -> GoalResponse:
    """Update goal fields."""
    goal = await _get_goal_or_404(goal_id, session)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(goal, key, value)
    await session.commit()
    await session.refresh(goal)
    return GoalResponse.model_validate(goal)


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(goal_id: str, session: AsyncSession = Depends(get_session)) -> None:
    """Delete a goal."""
    goal = await _get_goal_or_404(goal_id, session)
    await session.delete(goal)
    await session.commit()


@router.get("/{goal_id}/progress", response_model=ProgressResponse)
async def goal_progress(goal_id: str, session: AsyncSession = Depends(get_session)) -> ProgressResponse:
    """Get progress summary for a goal."""
    goal = await _get_goal_or_404(goal_id, session)
    milestones_result = await session.execute(select(Milestone).where(Milestone.goal_id == goal_id))
    milestones = milestones_result.scalars().all()
    completed = sum(1 for m in milestones if m.is_completed)
    total = len(milestones)
    progress = (completed / total * 100.0) if total > 0 else goal.progress

    return ProgressResponse(
        goal_id=goal_id,
        title=goal.title,
        progress=round(progress, 1),
        total_milestones=total,
        completed_milestones=completed,
        status=goal.status.value if isinstance(goal.status, GoalStatus) else str(goal.status),
    )


@router.get("/{goal_id}/milestones", response_model=list[MilestoneResponse])
async def list_milestones(goal_id: str, session: AsyncSession = Depends(get_session)) -> list[MilestoneResponse]:
    """List milestones for a goal."""
    await _get_goal_or_404(goal_id, session)
    result = await session.execute(select(Milestone).where(Milestone.goal_id == goal_id))
    return [MilestoneResponse.model_validate(m) for m in result.scalars().all()]


@router.post("/{goal_id}/milestones", response_model=MilestoneResponse, status_code=status.HTTP_201_CREATED)
async def create_milestone(
    goal_id: str,
    body: MilestoneCreate,
    session: AsyncSession = Depends(get_session),
) -> MilestoneResponse:
    """Add a milestone to a goal."""
    await _get_goal_or_404(goal_id, session)
    milestone = Milestone(
        id=str(uuid4()),
        goal_id=goal_id,
        title=body.title,
        target_value=body.target_value,
        current_value=body.current_value,
        is_completed=body.current_value >= body.target_value,
        due_date=body.due_date,
    )
    session.add(milestone)
    await session.commit()
    await session.refresh(milestone)
    return MilestoneResponse.model_validate(milestone)


@router.post("/{goal_id}/plan")
async def plan_goal(
    goal_id: str,
    body: Optional[dict] = None,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Decompose a goal into milestones and zero-cost permitted tasks."""
    from app.services.goal_planner import plan_goal_for_id

    return await plan_goal_for_id(goal_id=goal_id, session=session, extra=body)


@router.post("/{goal_id}/evaluate")
async def evaluate_goal(
    goal_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Evaluate goal progress from persisted analytics metrics and revise strategy."""
    from app.services.goal_planner import evaluate_goal_for_id

    return await evaluate_goal_for_id(goal_id=goal_id, session=session)
