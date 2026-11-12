"""Security dashboard, audit log, permissions, and emergency stop routes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.resource_manager import get_resource_manager
from app.core.scheduler import scheduler
from app.database import get_session
from app.models.agent import AgentExecution, ExecutionStatus
from app.models.security import (
    AuditAction,
    AuditLog,
    AuditSeverity,
    Permission,
    PermissionAction,
    Session as UserSession,
    SessionStatus,
    TrustedDevice,
)
from app.models.task import Task, TaskState

router = APIRouter(prefix="/security", tags=["security"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    action: AuditAction
    severity: AuditSeverity
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    description: str
    details: Optional[dict[str, Any]] = None
    ip_address: Optional[str] = None
    created_at: datetime


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    subject_type: str
    subject_id: str
    resource_type: str
    resource_id: Optional[str] = None
    action: PermissionAction
    is_allowed: bool
    conditions: Optional[dict[str, Any]] = None
    granted_by: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime


class PermissionUpdate(BaseModel):
    is_allowed: Optional[bool] = None
    conditions: Optional[dict[str, Any]] = None
    expires_at: Optional[datetime] = None


class SecurityDashboardResponse(BaseModel):
    active_sessions: int
    trusted_devices: int
    running_tasks: int
    total_permissions: int
    recent_critical_events: int
    recent_audit_logs: list[AuditLogResponse]


class EmergencyStopRequest(BaseModel):
    reason: str = "User triggered emergency stop"


class EmergencyStopResponse(BaseModel):
    stopped_tasks: int
    stopped_executions: int
    timestamp: str
    message: str


class AutopilotControlResponse(BaseModel):
    paused: bool
    emergency_stopped: bool
    timestamp: str
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/dashboard", response_model=SecurityDashboardResponse)
async def security_dashboard(
    session: AsyncSession = Depends(get_session),
) -> SecurityDashboardResponse:
    """Return high-level security posture overview."""
    active_sessions = (
        await session.execute(
            select(func.count()).select_from(UserSession).where(UserSession.status == SessionStatus.ACTIVE)
        )
    ).scalar_one()
    trusted_devices = (
        await session.execute(
            select(func.count()).select_from(TrustedDevice).where(TrustedDevice.is_active.is_(True))
        )
    ).scalar_one()
    running_tasks = (
        await session.execute(
            select(func.count()).select_from(Task).where(Task.state == TaskState.RUNNING)
        )
    ).scalar_one()
    total_permissions = (
        await session.execute(select(func.count()).select_from(Permission))
    ).scalar_one()
    critical_events = (
        await session.execute(
            select(func.count()).select_from(AuditLog).where(AuditLog.severity == AuditSeverity.CRITICAL)
        )
    ).scalar_one()

    recent_res = await session.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc()).limit(10)
    )
    recent_logs = [AuditLogResponse.model_validate(r) for r in recent_res.scalars().all()]

    return SecurityDashboardResponse(
        active_sessions=active_sessions,
        trusted_devices=trusted_devices,
        running_tasks=running_tasks,
        total_permissions=total_permissions,
        recent_critical_events=critical_events,
        recent_audit_logs=recent_logs,
    )


@router.get("/audit-log", response_model=list[AuditLogResponse])
async def list_audit_logs(
    action: Optional[AuditAction] = None,
    severity: Optional[AuditSeverity] = None,
    agent_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[AuditLogResponse]:
    """List audit log entries with optional filters."""
    stmt = select(AuditLog)
    if action is not None:
        stmt = stmt.where(AuditLog.action == action)
    if severity is not None:
        stmt = stmt.where(AuditLog.severity == severity)
    if agent_id is not None:
        stmt = stmt.where(AuditLog.agent_id == agent_id)
    if resource_type is not None:
        stmt = stmt.where(AuditLog.resource_type == resource_type)

    stmt = stmt.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
    res = await session.execute(stmt)
    return [AuditLogResponse.model_validate(log) for log in res.scalars().all()]


@router.get("/permissions", response_model=list[PermissionResponse])
async def list_permissions(
    subject_type: Optional[str] = None,
    subject_id: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
) -> list[PermissionResponse]:
    """List configured access control permissions."""
    stmt = select(Permission)
    if subject_type is not None:
        stmt = stmt.where(Permission.subject_type == subject_type)
    if subject_id is not None:
        stmt = stmt.where(Permission.subject_id == subject_id)
    res = await session.execute(stmt.order_by(Permission.created_at.desc()))
    return [PermissionResponse.model_validate(p) for p in res.scalars().all()]


@router.put("/permissions/{permission_id}", response_model=PermissionResponse)
async def update_permission(
    permission_id: str,
    body: PermissionUpdate,
    session: AsyncSession = Depends(get_session),
) -> PermissionResponse:
    """Update an existing permission rule."""
    res = await session.execute(select(Permission).where(Permission.id == permission_id))
    perm = res.scalar_one_or_none()
    if not perm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")

    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(perm, key, value)

    session.add(
        AuditLog(
            id=str(uuid4()),
            action=AuditAction.PERMISSION_CHANGE,
            severity=AuditSeverity.WARNING,
            resource_type="permission",
            resource_id=permission_id,
            description=f"Updated permission {permission_id}",
            details=body.model_dump(exclude_unset=True, mode="json"),
        )
    )
    await session.commit()
    await session.refresh(perm)
    return PermissionResponse.model_validate(perm)


@router.post("/emergency-stop", response_model=EmergencyStopResponse)
async def emergency_stop(
    body: EmergencyStopRequest = EmergencyStopRequest(),
    session: AsyncSession = Depends(get_session),
) -> EmergencyStopResponse:
    """Immediately cancel all running/queued tasks and agent executions."""
    now = datetime.now(timezone.utc)

    running_tasks = (
        await session.execute(select(Task).where(Task.state == TaskState.RUNNING))
    ).scalars().all()
    for task in running_tasks:
        task.state = TaskState.CANCELLED
        trail = list(task.audit_trail or [])
        trail.append(
            {
                "timestamp": now.isoformat(),
                "action": "emergency_stop",
                "details": {"reason": body.reason},
            }
        )
        task.audit_trail = trail

    active_execs = (
        await session.execute(
            select(AgentExecution).where(
                AgentExecution.status.in_([ExecutionStatus.QUEUED, ExecutionStatus.RUNNING])
            )
        )
    ).scalars().all()
    for execution in active_execs:
        execution.status = ExecutionStatus.CANCELLED
        execution.completed_at = now
        execution.error = f"Emergency stop: {body.reason}"

    session.add(
        AuditLog(
            id=str(uuid4()),
            action=AuditAction.EMERGENCY_STOP,
            severity=AuditSeverity.CRITICAL,
            resource_type="system",
            description=f"Emergency stop triggered: {body.reason}",
            details={
                "stopped_tasks": len(running_tasks),
                "stopped_executions": len(active_execs),
            },
        )
    )
    get_resource_manager().trigger_emergency_stop()
    try:
        if scheduler.is_running and scheduler._scheduler is not None:
            scheduler._scheduler.pause()
    except Exception:
        pass

    await session.commit()

    return EmergencyStopResponse(
        stopped_tasks=len(running_tasks),
        stopped_executions=len(active_execs),
        timestamp=now.isoformat(),
        message="All running tasks and agent executions have been cancelled.",
    )


@router.get("/autopilot-status", response_model=AutopilotControlResponse)
async def autopilot_status() -> AutopilotControlResponse:
    """Return global autopilot pause and emergency-stop status."""
    rm = get_resource_manager()
    paused = bool(
        rm._emergency_stopped
        or (scheduler._scheduler is not None and scheduler._scheduler.state == 2)
    )
    return AutopilotControlResponse(
        paused=paused,
        emergency_stopped=rm._emergency_stopped,
        timestamp=datetime.now(timezone.utc).isoformat(),
        message="Emergency stop active" if rm._emergency_stopped else ("Paused" if paused else "Active"),
    )


@router.post("/pause", response_model=AutopilotControlResponse)
async def pause_autopilot(
    session: AsyncSession = Depends(get_session),
) -> AutopilotControlResponse:
    """Pause scheduled automation without cancelling persisted jobs."""
    now = datetime.now(timezone.utc)
    try:
        if scheduler.is_running and scheduler._scheduler is not None:
            scheduler._scheduler.pause()
    except Exception:
        pass

    session.add(
        AuditLog(
            id=str(uuid4()),
            action=AuditAction.CONFIG_CHANGE,
            severity=AuditSeverity.WARNING,
            resource_type="autopilot",
            description="Global autopilot paused",
        )
    )
    await session.commit()
    return AutopilotControlResponse(
        paused=True,
        emergency_stopped=get_resource_manager()._emergency_stopped,
        timestamp=now.isoformat(),
        message="Autopilot paused. Scheduled jobs held.",
    )


@router.post("/resume", response_model=AutopilotControlResponse)
async def resume_autopilot(
    session: AsyncSession = Depends(get_session),
) -> AutopilotControlResponse:
    """Clear emergency stop (if active) and resume scheduled automation."""
    now = datetime.now(timezone.utc)
    rm = get_resource_manager()
    rm.clear_emergency_stop()
    try:
        if scheduler._scheduler is not None and scheduler._scheduler.state == 2:
            scheduler._scheduler.resume()
    except Exception:
        pass

    session.add(
        AuditLog(
            id=str(uuid4()),
            action=AuditAction.CONFIG_CHANGE,
            severity=AuditSeverity.INFO,
            resource_type="autopilot",
            description="Global autopilot resumed",
        )
    )
    await session.commit()
    return AutopilotControlResponse(
        paused=False,
        emergency_stopped=False,
        timestamp=now.isoformat(),
        message="Autopilot resumed.",
    )
