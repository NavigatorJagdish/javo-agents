"""Analytics routes — metrics, account dashboards, reports, and experiments."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.analytics import (
    AnalyticsSnapshot,
    Experiment,
    ExperimentStatus,
    Metric,
    MetricCategory,
    MetricType,
)
from app.models.user import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class MetricResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    account_id: Optional[str] = None
    name: str
    metric_type: MetricType
    category: MetricCategory
    value: float
    unit: Optional[str] = None
    dimensions: Optional[dict[str, Any]] = None
    recorded_at: datetime


class DashboardResponse(BaseModel):
    account_id: str
    total_metrics: int
    latest_snapshot: Optional[dict[str, Any]] = None
    metrics_by_category: dict[str, list[MetricResponse]]


class ReportGenerateRequest(BaseModel):
    account_id: Optional[str] = None
    snapshot_type: str = "weekly"
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    account_id: Optional[str] = None
    snapshot_type: str
    period_start: datetime
    period_end: datetime
    data: dict[str, Any]
    summary: Optional[str] = None
    created_at: datetime


class ExperimentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    description: Optional[str] = None
    hypothesis: Optional[str] = None
    user_id: Optional[str] = None
    variants: Optional[list[dict[str, Any]]] = None
    target_metric: Optional[str] = None


class ExperimentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=256)
    description: Optional[str] = None
    hypothesis: Optional[str] = None
    status: Optional[ExperimentStatus] = None
    variants: Optional[list[dict[str, Any]]] = None
    target_metric: Optional[str] = None
    results: Optional[dict[str, Any]] = None
    winner: Optional[str] = None


class ExperimentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    hypothesis: Optional[str] = None
    status: ExperimentStatus
    variants: Optional[list[dict[str, Any]]] = None
    target_metric: Optional[str] = None
    results: Optional[dict[str, Any]] = None
    winner: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _resolve_user_id(requested_user_id: Optional[str], session: AsyncSession) -> str:
    if requested_user_id:
        return requested_user_id
    res = await session.execute(select(User.id).limit(1))
    return res.scalar_one_or_none() or "default-user"


async def _get_experiment_or_404(exp_id: str, session: AsyncSession) -> Experiment:
    res = await session.execute(select(Experiment).where(Experiment.id == exp_id))
    exp = res.scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")
    return exp


# ---------------------------------------------------------------------------
# Metrics, Dashboard & Reports
# ---------------------------------------------------------------------------
@router.get("/metrics", response_model=list[MetricResponse])
async def get_metrics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    category: Optional[MetricCategory] = None,
    account_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
) -> list[MetricResponse]:
    """Query recorded metrics filtered by date range, category, and account."""
    stmt = select(Metric)
    if start_date is not None:
        stmt = stmt.where(Metric.recorded_at >= start_date)
    if end_date is not None:
        stmt = stmt.where(Metric.recorded_at <= end_date)
    if category is not None:
        stmt = stmt.where(Metric.category == category)
    if account_id is not None:
        stmt = stmt.where(Metric.account_id == account_id)

    stmt = stmt.order_by(Metric.recorded_at.desc()).limit(limit)
    res = await session.execute(stmt)
    return [MetricResponse.model_validate(m) for m in res.scalars().all()]


@router.get("/dashboard/{account_id}", response_model=DashboardResponse)
async def get_account_dashboard(
    account_id: str,
    session: AsyncSession = Depends(get_session),
) -> DashboardResponse:
    """Aggregate analytics dashboard data for a social account."""
    metrics_res = await session.execute(
        select(Metric)
        .where(Metric.account_id == account_id)
        .order_by(Metric.recorded_at.desc())
        .limit(200)
    )
    metrics = metrics_res.scalars().all()

    grouped: dict[str, list[MetricResponse]] = {}
    for m in metrics:
        cat_key = m.category.value if isinstance(m.category, MetricCategory) else str(m.category)
        grouped.setdefault(cat_key, []).append(MetricResponse.model_validate(m))

    snap_res = await session.execute(
        select(AnalyticsSnapshot)
        .where(AnalyticsSnapshot.account_id == account_id)
        .order_by(AnalyticsSnapshot.created_at.desc())
        .limit(1)
    )
    snap = snap_res.scalar_one_or_none()
    snap_data = (
        {
            "id": snap.id,
            "snapshot_type": snap.snapshot_type,
            "period_start": snap.period_start.isoformat(),
            "period_end": snap.period_end.isoformat(),
            "data": snap.data,
            "summary": snap.summary,
        }
        if snap
        else None
    )

    return DashboardResponse(
        account_id=account_id,
        total_metrics=len(metrics),
        latest_snapshot=snap_data,
        metrics_by_category=grouped,
    )


@router.post("/reports/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_report(
    body: ReportGenerateRequest,
    session: AsyncSession = Depends(get_session),
) -> ReportResponse:
    """Generate and persist an analytics snapshot report over a time period."""
    now = datetime.now(timezone.utc)
    period_end = body.period_end or now
    period_start = body.period_start or (period_end - timedelta(days=7))

    stmt = select(Metric).where(
        Metric.recorded_at >= period_start,
        Metric.recorded_at <= period_end,
    )
    if body.account_id:
        stmt = stmt.where(Metric.account_id == body.account_id)

    metrics = (await session.execute(stmt)).scalars().all()
    aggregated: dict[str, dict[str, float]] = {}
    for m in metrics:
        bucket = aggregated.setdefault(m.name, {"count": 0.0, "sum": 0.0, "latest": m.value})
        bucket["count"] += 1
        bucket["sum"] += m.value

    for bucket in aggregated.values():
        bucket["avg"] = round(bucket["sum"] / bucket["count"], 4) if bucket["count"] else 0.0

    snapshot = AnalyticsSnapshot(
        id=str(uuid4()),
        account_id=body.account_id,
        snapshot_type=body.snapshot_type,
        period_start=period_start,
        period_end=period_end,
        data={"metrics_count": len(metrics), "aggregated": aggregated},
        summary=f"Generated {body.snapshot_type} report with {len(metrics)} data points.",
    )
    session.add(snapshot)
    await session.commit()
    await session.refresh(snapshot)
    return ReportResponse.model_validate(snapshot)


# ---------------------------------------------------------------------------
# Experiments CRUD
# ---------------------------------------------------------------------------
@router.get("/experiments", response_model=list[ExperimentResponse])
async def list_experiments(
    status_filter: Optional[ExperimentStatus] = Query(default=None, alias="status"),
    session: AsyncSession = Depends(get_session),
) -> list[ExperimentResponse]:
    """List growth/content experiments."""
    stmt = select(Experiment)
    if status_filter is not None:
        stmt = stmt.where(Experiment.status == status_filter)
    res = await session.execute(stmt.order_by(Experiment.created_at.desc()))
    return [ExperimentResponse.model_validate(e) for e in res.scalars().all()]


@router.post("/experiments", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED)
async def create_experiment(
    body: ExperimentCreate,
    session: AsyncSession = Depends(get_session),
) -> ExperimentResponse:
    """Create a new experiment."""
    user_id = await _resolve_user_id(body.user_id, session)
    exp = Experiment(
        id=str(uuid4()),
        user_id=user_id,
        name=body.name,
        description=body.description,
        hypothesis=body.hypothesis,
        status=ExperimentStatus.DRAFT,
        variants=body.variants,
        target_metric=body.target_metric,
    )
    session.add(exp)
    await session.commit()
    await session.refresh(exp)
    return ExperimentResponse.model_validate(exp)


@router.get("/experiments/{exp_id}", response_model=ExperimentResponse)
async def get_experiment(exp_id: str, session: AsyncSession = Depends(get_session)) -> ExperimentResponse:
    """Retrieve an experiment by ID."""
    exp = await _get_experiment_or_404(exp_id, session)
    return ExperimentResponse.model_validate(exp)


@router.put("/experiments/{exp_id}", response_model=ExperimentResponse)
async def update_experiment(
    exp_id: str,
    body: ExperimentUpdate,
    session: AsyncSession = Depends(get_session),
) -> ExperimentResponse:
    """Update an experiment."""
    exp = await _get_experiment_or_404(exp_id, session)
    update_data = body.model_dump(exclude_unset=True)
    now = datetime.now(timezone.utc)
    if update_data.get("status") == ExperimentStatus.RUNNING and exp.started_at is None:
        exp.started_at = now
    if update_data.get("status") == ExperimentStatus.COMPLETED and exp.completed_at is None:
        exp.completed_at = now
    for key, value in update_data.items():
        setattr(exp, key, value)
    await session.commit()
    await session.refresh(exp)
    return ExperimentResponse.model_validate(exp)


@router.delete("/experiments/{exp_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_experiment(exp_id: str, session: AsyncSession = Depends(get_session)) -> None:
    """Delete an experiment."""
    exp = await _get_experiment_or_404(exp_id, session)
    await session.delete(exp)
    await session.commit()
