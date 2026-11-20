"""Owner-only durable checkpoints. Waiting never holds a model worker."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import select, text

from app import database as db
from app.core.resource_manager import get_resource_manager
from app.models.workflow import (
    WorkflowExecution as Run,
    WorkflowExecutionStatus as State,
    WorkflowNodeReview,
    WorkflowStatus,
)
from app.models.security import AuditAction, AuditLog
from app.services.workflow_graphs import (
    bounded_json,
    fingerprint,
    owned_workflow,
    revision_number,
    snapshot,
)


class ReviewWait(Exception):
    pass


def utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def completed_events(run):
    if not isinstance(run.execution_log, list):
        raise ValueError("Invalid saved execution log")
    return [
        event
        for event in run.execution_log
        if isinstance(event, dict) and event.get("event") == "completed"
    ]


def review_checkpoint(run, value, node, previous):
    result = {
        "execution_id": run.id,
        "workflow_id": run.workflow_id,
        "workflow_revision": value["revision"],
        "definition_fingerprint": value["fingerprint"],
        "node_id": node.id,
        "instructions": node.config["instructions"],
        "input": value["input"],
        "previous_output": previous,
        "completed_nodes": completed_events(run),
    }
    bounded_json(result, 262144)
    return result


async def at_gate(run_id, value, node, previous):
    from app.services.workflow_jobs import saved_run, RunCancelled

    async with db.async_session_factory() as session:
        await session.execute(text("BEGIN IMMEDIATE"))
        run = await session.get(Run, run_id)
        if (
            not run
            or run.status != State.RUNNING
            or saved_run(run) != value
            or get_resource_manager()._emergency_stopped
        ):
            raise RunCancelled("Review checkpoint was cancelled")
        checkpoint = review_checkpoint(run, value, node, previous)
        row = await session.scalar(
            select(WorkflowNodeReview).where(
                WorkflowNodeReview.execution_id == run_id, WorkflowNodeReview.node_id == node.id
            )
        )
        if row:
            if row.checkpoint != checkpoint or row.fingerprint != fingerprint(checkpoint):
                raise ValueError("Review checkpoint changed")
            if row.status == "approved":
                # The approval deadline was checked at the decision. Actual
                # dispatch still has its own short queue/operation deadline.
                return {"review_id": row.id, "decision": "approved", "actions_executed": False}
            if row.status != "pending" or utc(row.expires_at) <= datetime.now(timezone.utc):
                raise RunCancelled("Review is no longer eligible")
        else:
            now = datetime.now(timezone.utc)
            row = WorkflowNodeReview(
                execution_id=run_id,
                node_id=node.id,
                status="pending",
                revision=1,
                checkpoint=checkpoint,
                fingerprint=fingerprint(checkpoint),
                created_at=now,
                expires_at=now + timedelta(hours=24),
            )
            session.add(row)
        run.status = State.WAITING_APPROVAL
        await session.commit()
    raise ReviewWait()


async def inspect(session, review_id):
    from app.services.workflow_jobs import saved_run

    row = await session.get(WorkflowNodeReview, review_id)
    if row is None:
        raise HTTPException(404, "Workflow review not found")
    run = await session.get(Run, row.execution_id)
    if run is None:
        raise HTTPException(503, "Review execution is unavailable")
    workflow = await owned_workflow(session, run.workflow_id)
    value = saved_run(run)
    if not isinstance(row.checkpoint, dict) or not isinstance(run.execution_log, list):
        raise HTTPException(503, 'Saved checkpoint is damaged; cancel the run and inspect its original records')
    try:
        checkpoint_fingerprint = fingerprint(row.checkpoint)
    except (ValueError, TypeError):
        raise HTTPException(503, 'Saved checkpoint integrity could not be checked') from None
    matching = bool(
        value
        and row.fingerprint == checkpoint_fingerprint
        and row.checkpoint.get("execution_id") == run.id
        and row.checkpoint.get("workflow_id") == run.workflow_id
        and row.checkpoint.get("workflow_revision") == value["revision"]
        and row.checkpoint.get("definition_fingerprint") == value["fingerprint"]
        and row.checkpoint.get("input") == value["input"]
        and row.checkpoint.get("completed_nodes") == completed_events(run)
        and run.current_node_id == row.node_id
        and fingerprint(snapshot(workflow)) == value["fingerprint"]
        and await revision_number(session, workflow.id) == value["revision"]
    )
    eligible = (
        matching
        and run.status == State.WAITING_APPROVAL
        and row.status == "pending"
        and workflow.status != WorkflowStatus.ARCHIVED
        and utc(row.expires_at) > datetime.now(timezone.utc)
    )
    result = {
        "id": row.id,
        "execution_id": run.id,
        "workflow_id": workflow.id,
        "workflow_name": workflow.name,
        "node_id": row.node_id,
        "status": row.status,
        "revision": row.revision,
        "fingerprint": row.fingerprint,
        "execution_status": run.status.value,
        "expires_at": utc(row.expires_at),
        "approvable": bool(eligible),
        "checkpoint": row.checkpoint,
        "definition": value["definition"] if value else None,
        "message": "Approve only this saved checkpoint. Approval queues continuation; it does not resume the runtime or authorize other actions.",
    }
    return row, run, result


async def decide(session, review_id, expected_revision, expected_fingerprint, decision):
    await session.execute(text("BEGIN IMMEDIATE"))
    row, run, result = await inspect(session, review_id)
    if (
        row.status != "pending"
        or row.revision != expected_revision
        or row.fingerprint != expected_fingerprint
    ):
        raise HTTPException(409, "Review changed; reload its current saved checkpoint")
    if run.status != State.WAITING_APPROVAL:
        raise HTTPException(409, "Execution is no longer waiting for this review")
    if decision == "approve":
        if not result["approvable"] or get_resource_manager()._emergency_stopped:
            raise HTTPException(
                409,
                "Review expired, changed, archived or emergency stopped. Reject or cancel it and review a fresh run.",
            )
        # Only explicit owner approval extends dispatch time after a human wait.
        run.trigger_data = {
            **run.trigger_data,
            "deadline": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
        }
        run.status = State.QUEUED
    else:
        run.status, run.completed_at, run.error = (
            State.CANCELLED,
            datetime.now(timezone.utc),
            "Owner rejected workflow checkpoint",
        )
    row.status, row.decided_at, row.revision = (
        ("approved" if decision == "approve" else "rejected"),
        datetime.now(timezone.utc),
        row.revision + 1,
    )
    session.add(
        AuditLog(
            action=AuditAction.UPDATE,
            resource_type="workflow_node_review",
            resource_id=row.id,
            description="Owner " + row.status + " an exact saved workflow checkpoint",
        )
    )
    await session.commit()
    return {
        "id": row.id,
        "status": row.status,
        "execution_id": run.id,
        "execution_status": run.status.value,
    }
