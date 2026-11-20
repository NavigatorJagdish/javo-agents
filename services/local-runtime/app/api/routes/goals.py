"""Owner-scoped goals, manual evidence and milestones in existing database columns."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.security import AuditAction, AuditLog
from app.models.task import Goal, GoalStatus, Milestone
from app.core.local_identity import LOCAL_OWNER, OWNER_IDS, ensure_local_owner as _ensure_owner

router = APIRouter(prefix="/goals", tags=["goals"])
SCHEMA_KEY = '_javo_goal_schema'


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, allow_inf_nan=False)


class Objective(Input):
    metric: str = Field(min_length=1, max_length=100)
    unit: str = Field(min_length=1, max_length=80)
    baseline: float = Field(ge=-1e15, le=1e15, strict=True)
    baseline_source: str = Field(min_length=1, max_length=500)
    target: float = Field(ge=-1e15, le=1e15, strict=True)
    constraints: str = Field(default="", max_length=4000)
    stopping_conditions: str = Field(default="", max_length=4000)
    uncertainty: str = Field(default="Manual measurements are not independently verified.", max_length=4000)

    @model_validator(mode="after")
    def distinct_target(self):
        if self.baseline == self.target:
            raise ValueError("Target must differ from baseline")
        return self


class Measurement(Input):
    value: float = Field(ge=-1e15, le=1e15, strict=True)
    source: str = Field(min_length=1, max_length=500)
    observed_at: AwareDatetime

    @field_validator("observed_at")
    @classmethod
    def observation_time(cls, value):
        if value > datetime.now(timezone.utc) + timedelta(minutes=5):
            raise ValueError("Observation cannot be in the future")
        return value.astimezone(timezone.utc)


def legacy_metrics(value):
    if value is not None:
        if {"objective", "measurement", SCHEMA_KEY} & value.keys():
            raise ValueError("Use objective and measurement endpoints for structured evidence")
        try:
            encoded = json.dumps(value, allow_nan=False)
        except (ValueError, TypeError):
            raise ValueError("Metrics must contain finite JSON values") from None
        if len(encoded) > 16000:
            raise ValueError("Metrics exceed 16000 characters")
    return value


class GoalCreate(Input):
    title: str = Field(min_length=1, max_length=256)
    description: str | None = Field(default=None, max_length=8000)
    owner_id: str | None = None
    target_metrics: dict[str, Any] | None = None
    objective: Objective | None = None
    deadline: AwareDatetime | None = None
    _legacy = field_validator("target_metrics")(legacy_metrics)


class GoalUpdate(Input):
    title: str | None = Field(default=None, min_length=1, max_length=256)
    description: str | None = Field(default=None, max_length=8000)
    target_metrics: dict[str, Any] | None = None
    objective: Objective | None = None
    progress: float | None = Field(default=None, ge=0, le=100)
    status: GoalStatus | None = None
    deadline: AwareDatetime | None = None
    _legacy = field_validator("target_metrics")(legacy_metrics)

    @model_validator(mode="after")
    def non_null_required(self):
        for name in ("title", "progress", "status", "objective"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


def database_utc(value):
    # SQLite strips offsets; all route writes normalize to UTC.
    return value.replace(tzinfo=timezone.utc) if value and value.tzinfo is None else value


class GoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    goal_id: str
    title: str
    description: str | None = None
    owner_id: str
    target_metrics: dict[str, Any] | None = None
    objective: Objective | None = None
    measurement: Measurement | None = None
    progress: float = 0
    progress_basis: Literal["measurement", "milestones", "legacy_manual", "unmeasured"] = "unmeasured"
    total_milestones: int = 0
    completed_milestones: int = 0
    status: GoalStatus
    deadline: datetime | None = None
    created_at: datetime
    updated_at: datetime
    _dates = field_validator("deadline", "created_at", "updated_at")(database_utc)


class ProgressResponse(BaseModel):
    goal_id: str
    title: str
    progress: float
    progress_basis: str
    total_milestones: int
    completed_milestones: int
    status: str


class MilestoneCreate(Input):
    title: str = Field(min_length=1, max_length=256)
    target_value: float = Field(default=100, gt=0)
    current_value: float = Field(default=0, ge=0)
    due_date: AwareDatetime | None = None


class MilestoneUpdate(Input):
    title: str | None = Field(default=None, min_length=1, max_length=256)
    target_value: float | None = Field(default=None, gt=0)
    current_value: float | None = Field(default=None, ge=0)
    due_date: AwareDatetime | None = None

    @model_validator(mode="after")
    def non_null_required(self):
        for name in ("title", "target_value", "current_value"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


class MilestoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    goal_id: str
    title: str
    target_value: float
    current_value: float
    is_completed: bool
    due_date: datetime | None = None
    _date = field_validator("due_date")(database_utc)


async def _get_goal_or_404(goal_id: str, session: AsyncSession) -> Goal:
    goal = (await session.execute(select(Goal).where(
        Goal.goal_id == goal_id, Goal.owner_id.in_(OWNER_IDS)
    ))).scalar_one_or_none()
    if goal is None:
        raise HTTPException(404, "Goal not found")
    return goal


async def _audit(session, goal_id, action, event, details=None):
    await _ensure_owner(session)
    session.add(AuditLog(user_id=LOCAL_OWNER, action=action, resource_type="goal",
                         resource_id=goal_id, description=event, details=details))


def _utc(value):
    return value.astimezone(timezone.utc) if isinstance(value, datetime) else value


async def _milestones(goal_id, session):
    result = await session.execute(select(Milestone).where(Milestone.goal_id == goal_id)
                                   .order_by(Milestone.id))
    return list(result.scalars().all())


def _response(goal: Goal, milestones: list[Milestone]) -> GoalResponse:
    result = GoalResponse.model_validate(goal)
    metrics = goal.target_metrics or {}
    result.objective, result.measurement = _structured(metrics)
    result.total_milestones = len(milestones)
    result.completed_milestones = sum(m.is_completed for m in milestones)
    if result.objective:
        result.progress_basis = "measurement" if result.measurement else "unmeasured"
        result.progress = (100 * (result.measurement.value - result.objective.baseline)
                           / (result.objective.target - result.objective.baseline)) if result.measurement else 0
    elif milestones:
        result.progress_basis = "milestones"
        result.progress = sum(min(1, max(0, m.current_value / m.target_value)) for m in milestones) / len(milestones) * 100
    else:
        result.progress_basis = "legacy_manual" if goal.progress else "unmeasured"
    result.progress = round(min(100, max(0, result.progress)), 1)
    return result


def _structured(metrics):
    """Keep opaque legacy metrics readable; validate versioned evidence strictly."""
    if SCHEMA_KEY in metrics and (type(metrics[SCHEMA_KEY]) is not int or metrics[SCHEMA_KEY] != 1):
        raise HTTPException(503, 'Saved goal evidence format is unsupported')
    try:
        if SCHEMA_KEY in metrics and not metrics.get('objective'):
            raise ValueError('Versioned evidence requires an objective')
        objective = Objective.model_validate(metrics['objective']) if metrics.get('objective') else None
        measurement = Measurement.model_validate(metrics['measurement']) if metrics.get('measurement') else None
        if measurement is not None and objective is None:
            raise ValueError('Measurement without an objective')
        return objective, measurement
    except (ValidationError, ValueError, TypeError):
        if SCHEMA_KEY in metrics:
            raise HTTPException(503, 'Saved goal evidence is invalid; recover a verified copy') from None
        # Before structured evidence existed this JSON column accepted arbitrary
        # keys. They cannot be reinterpreted as trustworthy typed observations.
        return None, None


async def _saved(goal, session):
    goal.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await session.execute(text('BEGIN'))
    await session.refresh(goal)
    return _response(goal, await _milestones(goal.goal_id, session))


@router.get("/", response_model=list[GoalResponse])
async def list_goals(status_filter: GoalStatus | None = Query(default=None, alias="status"),
                     limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
                     session: AsyncSession = Depends(get_session)):
    await session.execute(text('BEGIN'))
    stmt = select(Goal).where(Goal.owner_id.in_(OWNER_IDS))
    if status_filter is not None:
        stmt = stmt.where(Goal.status == status_filter)
    goals = list((await session.execute(stmt.order_by(Goal.created_at.desc(), Goal.goal_id)
                                       .offset(offset).limit(limit))).scalars().all())
    rows = list((await session.execute(select(Milestone).where(
        Milestone.goal_id.in_([g.goal_id for g in goals])
    ))).scalars().all()) if goals else []
    grouped: dict[str, list[Milestone]] = {}
    for row in rows:
        grouped.setdefault(row.goal_id, []).append(row)
    return [_response(g, grouped.get(g.goal_id, [])) for g in goals]


@router.post("/", response_model=GoalResponse, status_code=201)
async def create_goal(body: GoalCreate, session: AsyncSession = Depends(get_session)):
    if body.owner_id is not None and body.owner_id != LOCAL_OWNER:
        raise HTTPException(403, "Cannot assign another owner")
    await session.execute(text("BEGIN IMMEDIATE"))
    await _ensure_owner(session)
    metrics = dict(body.target_metrics or {})
    if body.objective:
        metrics["objective"] = body.objective.model_dump(mode="json")
        metrics[SCHEMA_KEY] = 1
    goal = Goal(goal_id=str(uuid4()), title=body.title, description=body.description,
                owner_id=LOCAL_OWNER, target_metrics=metrics or None, deadline=_utc(body.deadline),
                status=GoalStatus.ACTIVE, progress=0)
    session.add(goal)
    await _audit(session, goal.goal_id, AuditAction.CREATE, "Goal created")
    return await _saved(goal, session)


@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(goal_id: str, session: AsyncSession = Depends(get_session)):
    await session.execute(text('BEGIN'))
    return _response(await _get_goal_or_404(goal_id, session), await _milestones(goal_id, session))


@router.put("/{goal_id}", response_model=GoalResponse)
async def update_goal(goal_id: str, body: GoalUpdate, session: AsyncSession = Depends(get_session)):
    await session.execute(text("BEGIN IMMEDIATE"))
    goal = await _get_goal_or_404(goal_id, session)
    milestones = await _milestones(goal_id, session)
    changes = body.model_dump(exclude_unset=True)
    metrics = dict(goal.target_metrics or {})
    objective, measurement = _structured(metrics)
    if "progress" in changes and (objective or milestones or body.objective):
        raise HTTPException(409, "Progress is derived from measurements or milestones")
    if "objective" in changes:
        if measurement:
            raise HTTPException(409, "A measured objective is fixed; create a new goal to change its baseline or target")
        if objective is None and {'objective', 'measurement'} & metrics.keys():
            raise HTTPException(409, 'Legacy free-form evidence is retained; create a new goal for structured measurements')
        metrics["objective"] = body.objective.model_dump(mode="json")
        metrics[SCHEMA_KEY] = 1
        changes.pop("objective")
    if "target_metrics" in changes:
        legacy = changes.pop("target_metrics") or {}
        protected = {'objective', 'measurement', SCHEMA_KEY} if objective or body.objective else set()
        metrics = {**legacy, **{k: v for k, v in metrics.items() if k in protected}}
    goal.target_metrics = metrics or None
    for key, value in changes.items():
        setattr(goal, key, _utc(value))
    await _audit(session, goal_id, AuditAction.UPDATE, "Goal updated", {"fields": sorted(body.model_fields_set)})
    return await _saved(goal, session)


@router.delete("/{goal_id}", status_code=204)
async def delete_goal(goal_id: str, session: AsyncSession = Depends(get_session)):
    await session.execute(text("BEGIN IMMEDIATE"))
    goal = await _get_goal_or_404(goal_id, session)
    await _audit(session, goal_id, AuditAction.DELETE, "Goal removed; task history retained")
    await session.delete(goal)
    await session.commit()


@router.get("/{goal_id}/progress", response_model=ProgressResponse)
async def goal_progress(goal_id: str, session: AsyncSession = Depends(get_session)):
    goal = await get_goal(goal_id, session)
    return ProgressResponse(**goal.model_dump(include=set(ProgressResponse.model_fields)))


@router.post("/{goal_id}/measurements", response_model=GoalResponse)
async def record_measurement(goal_id: str, body: Measurement, session: AsyncSession = Depends(get_session)):
    # Serialize read-modify-write operations in SQLite so simultaneous edits
    # cannot overwrite newer evidence with an older observation or metadata.
    await session.execute(text("BEGIN IMMEDIATE"))
    goal = await _get_goal_or_404(goal_id, session)
    metrics = dict(goal.target_metrics or {})
    objective, previous = _structured(metrics)
    if not objective:
        raise HTTPException(409, "Set an objective before recording a measurement")
    if previous and body.observed_at < previous.observed_at:
        raise HTTPException(409, "Observation is older than the latest saved measurement")
    metrics["measurement"] = body.model_dump(mode="json")
    metrics[SCHEMA_KEY] = 1
    goal.target_metrics = metrics
    await _audit(session, goal_id, AuditAction.UPDATE, "Manual goal measurement recorded",
                 {"kind": "manual_measurement", **body.model_dump(mode="json"), "independently_verified": False})
    return await _saved(goal, session)


@router.get("/{goal_id}/measurements")
async def list_measurements(goal_id: str, limit: int = Query(50, ge=1, le=200),
                            offset: int = Query(0, ge=0), session: AsyncSession = Depends(get_session)):
    await session.execute(text('BEGIN'))
    await _get_goal_or_404(goal_id, session)
    rows = (await session.execute(select(AuditLog).where(
        AuditLog.resource_type == "goal", AuditLog.resource_id == goal_id,
        AuditLog.description == "Manual goal measurement recorded",
    ).order_by(AuditLog.created_at.desc(), AuditLog.id).offset(offset).limit(limit))).scalars().all()
    return [{"id": row.id, **row.details} for row in rows]


@router.get("/{goal_id}/milestones", response_model=list[MilestoneResponse])
async def list_milestones(goal_id: str, session: AsyncSession = Depends(get_session)):
    await session.execute(text('BEGIN'))
    await _get_goal_or_404(goal_id, session)
    return await _milestones(goal_id, session)


@router.post("/{goal_id}/milestones", response_model=MilestoneResponse, status_code=201)
async def create_milestone(goal_id: str, body: MilestoneCreate, session: AsyncSession = Depends(get_session)):
    await session.execute(text("BEGIN IMMEDIATE"))
    goal = await _get_goal_or_404(goal_id, session)
    milestone = Milestone(id=str(uuid4()), goal_id=goal_id, title=body.title,
                          target_value=body.target_value, current_value=body.current_value,
                          is_completed=body.current_value >= body.target_value, due_date=_utc(body.due_date))
    session.add(milestone)
    await _audit(session, goal_id, AuditAction.UPDATE, "Milestone created", {"milestone_id": milestone.id})
    await _saved(goal, session)
    await session.refresh(milestone)
    return milestone


@router.put("/{goal_id}/milestones/{milestone_id}", response_model=MilestoneResponse)
async def update_milestone(goal_id: str, milestone_id: str, body: MilestoneUpdate,
                           session: AsyncSession = Depends(get_session)):
    await session.execute(text("BEGIN IMMEDIATE"))
    goal = await _get_goal_or_404(goal_id, session)
    milestone = (await session.execute(select(Milestone).where(
        Milestone.id == milestone_id, Milestone.goal_id == goal_id
    ))).scalar_one_or_none()
    if milestone is None:
        raise HTTPException(404, "Milestone not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(milestone, key, _utc(value))
    milestone.is_completed = milestone.current_value >= milestone.target_value
    await _audit(session, goal_id, AuditAction.UPDATE, "Milestone updated",
                 {"milestone_id": milestone_id, "fields": sorted(body.model_fields_set)})
    await _saved(goal, session)
    await session.refresh(milestone)
    return milestone


@router.delete("/{goal_id}/milestones/{milestone_id}", status_code=204)
async def delete_milestone(goal_id: str, milestone_id: str, session: AsyncSession = Depends(get_session)):
    await session.execute(text("BEGIN IMMEDIATE"))
    goal = await _get_goal_or_404(goal_id, session)
    milestone = (await session.execute(select(Milestone).where(
        Milestone.id == milestone_id, Milestone.goal_id == goal_id
    ))).scalar_one_or_none()
    if milestone is None:
        raise HTTPException(404, "Milestone not found")
    await session.delete(milestone)
    await _audit(session, goal_id, AuditAction.UPDATE, "Milestone removed", {"milestone_id": milestone_id})
    await _saved(goal, session)
