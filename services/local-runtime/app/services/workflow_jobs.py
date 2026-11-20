"""Durable explicitly reviewed manual local-text runs; no action/tool nodes."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from datetime import datetime, timedelta, timezone
import json
import logging
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import func, select, text, update
from sqlalchemy.engine import make_url

from app import database as db
from app.config import get_settings
from app.core.ai_router import get_ai_router
from app.core.local_identity import LOCAL_OWNER, OWNER_IDS
from app.core.resource_manager import get_resource_manager, WorkAdmissionRefused
from app.core.runtime_lease import RuntimeLease
from app.models.security import AuditAction, AuditLog
from app.models.workflow import (
    Workflow,
    WorkflowExecution as Run,
    WorkflowExecutionStatus as State,
    WorkflowStatus,
    NodeType,
    WorkflowNodeReview,
)
from app.services.workflow_graphs import bounded_json, execution_plan, fingerprint, condition_result
from app.services.workflow_reviews import ReviewWait, at_gate, completed_events

logger = logging.getLogger(__name__)
AUTHORIZATION = {
    "owner": LOCAL_OWNER,
    "permissions": ["read_workflows", "local_text_generation"],
    "version": 1,
}


def saved_run(row):
    value = row.trigger_data
    if (
        not isinstance(value, dict)
        or type(value.get("_javo_workflow_run")) is not int
        or value.get("_javo_workflow_run") != 1
    ):
        return None
    if value.get("authorization") != AUTHORIZATION:
        return None
    try:
        if fingerprint(value["definition"]) != value["fingerprint"]:
            return None
        execution_plan(value["definition"])
        bounded_json(value["input"], 8192)
        if type(value["revision"]) is not int or value["revision"] < 1:
            return None
        if datetime.fromisoformat(value["deadline"]).utcoffset() is None:
            return None
    except Exception:
        return None
    return value


def run_response(row):
    value = saved_run(row)

    def utc_date(date):
        return date.replace(tzinfo=timezone.utc) if date and date.tzinfo is None else date

    return {
        "id": row.id,
        "workflow_id": row.workflow_id,
        "status": row.status.value,
        "execution_verified": value is not None,
        "revision": value["revision"] if value else None,
        "fingerprint": value["fingerprint"] if value else None,
        "created_at": value.get("queued_at") if value else row.started_at,
        "started_at": utc_date(row.started_at) if row.status != State.QUEUED else None,
        "completed_at": utc_date(row.completed_at),
        "expires_at": value["deadline"] if value else None,
        "current_node_id": row.current_node_id,
        "execution_log": row.execution_log if value else [],
        "error": row.error,
        "message": "Actual local-text execution receipt; no tools or social action was performed"
        if value
        else "Legacy or invalid receipt is not verified evidence of workflow execution",
    }


async def enqueue(session, workflow, definition, revision, input_data, *, commit=True):
    if get_resource_manager()._emergency_stopped:
        raise HTTPException(409, "Runtime is emergency stopped; review and explicitly resume first")
    if revision < 1:
        raise HTTPException(409, "Save and review this legacy definition before running")
    count = await session.scalar(
        select(func.count()).select_from(Run).where(Run.status.in_([State.QUEUED, State.RUNNING, State.WAITING_APPROVAL]))
    )
    if count >= get_settings().max_queue_size:
        raise HTTPException(429, "Saved workflow execution queue is full")
    if await session.scalar(
        select(Run.id)
        .where(Run.workflow_id == workflow.id, Run.status.in_([State.QUEUED, State.RUNNING, State.WAITING_APPROVAL]))
        .limit(1)
    ):
        raise HTTPException(409, "This workflow already has a queued or running execution")
    now = datetime.now(timezone.utc)
    run = Run(
        id=str(uuid4()),
        workflow_id=workflow.id,
        status=State.QUEUED,
        started_at=now,
        execution_log=[],
        trigger_data={
            "_javo_workflow_run": 1,
            "authorization": AUTHORIZATION,
            "definition": definition,
            "revision": revision,
            "fingerprint": fingerprint(definition),
            "input": input_data,
            "queued_at": now.isoformat(),
            "deadline": (now + timedelta(minutes=5)).isoformat(),
        },
    )
    session.add(run)
    session.add(
        AuditLog(
            action=AuditAction.EXECUTE,
            resource_type="workflow_execution",
            resource_id=run.id,
            description="Owner queued a reviewed manual local-text workflow",
        )
    )
    if commit:
        await session.commit()
    else:
        await session.flush()
    return run


async def cancel(session, run):
    changed = await session.execute(
        update(Run)
        .where(Run.id == run.id, Run.status.in_([State.QUEUED, State.RUNNING, State.WAITING_APPROVAL]))
        .values(
            status=State.CANCELLED,
            completed_at=datetime.now(timezone.utc),
            error="Cancelled by owner",
        )
    )
    if changed.rowcount != 1:
        raise HTTPException(409, "Execution already finished; reload its receipt")
    session.add(
        AuditLog(
            action=AuditAction.UPDATE,
            resource_type="workflow_execution",
            resource_id=run.id,
            description="Owner cancelled workflow execution",
        )
    )
    await session.commit()
    workflow_worker.cancel(run.id)


class RunCancelled(RuntimeError):
    pass


class WorkflowWorker:
    def __init__(self):
        self._task = self._operation = self._lease = self._active_id = None
        self._closing = False

    async def start(self):
        if self._task is not None:
            return
        self._closing = False
        path = make_url(get_settings().database_url).database
        if path and path != ":memory:":
            self._lease = RuntimeLease(path + ".workflow-worker.lock")
            self._lease.acquire()
        async with db.async_session_factory() as session:
            await session.execute(update(Run).where(
                Run.status == State.WAITING_APPROVAL,
                ~select(WorkflowNodeReview.id).where(
                    WorkflowNodeReview.execution_id == Run.id,
                    WorkflowNodeReview.status == 'pending').exists(),
            ).values(status=State.FAILED, completed_at=datetime.now(timezone.utc),
                error='Legacy or missing owner-review checkpoint; no continuation was run'))
            await session.execute(
                update(Run)
                .where(Run.status == State.RUNNING)
                .values(
                    status=State.FAILED,
                    completed_at=datetime.now(timezone.utc),
                    error="Runtime restarted during an unconfirmed run; inspect results and explicitly run again",
                )
            )
            await session.commit()
        self._task = asyncio.create_task(self._run(), name="javo-manual-workflows")

    async def _claim(self):
        async with db.async_session_factory() as session:
            await session.execute(text("BEGIN IMMEDIATE"))
            rows = (
                await session.scalars(
                    select(Run)
                    .where(Run.status == State.QUEUED)
                    .order_by(Run.started_at, Run.id)
                    .limit(get_settings().max_queue_size)
                )
            ).all()
            for row in rows:
                workflow = await session.get(Workflow, row.workflow_id)
                value = saved_run(row)
                if workflow is not None and workflow.status == WorkflowStatus.ARCHIVED:
                    row.status, row.error = (
                        State.CANCELLED,
                        "Cancelled because the workflow was archived",
                    )
                    row.completed_at = datetime.now(timezone.utc)
                    continue
                if not value or workflow is None or workflow.user_id not in OWNER_IDS:
                    row.status, row.error = (
                        State.FAILED,
                        "Saved run is invalid, archived or no longer authorized",
                    )
                    row.completed_at = datetime.now(timezone.utc)
                    continue
                if datetime.fromisoformat(value["deadline"]) <= datetime.now(timezone.utc):
                    row.status, row.error = (
                        State.FAILED,
                        "Queued run expired; review and explicitly run again",
                    )
                    row.completed_at = datetime.now(timezone.utc)
                    continue
                if workflow.status == WorkflowStatus.PAUSED:
                    continue
                manager = get_resource_manager()
                if manager._paused or manager._emergency_stopped:
                    break
                row.status, row.started_at = State.RUNNING, datetime.now(timezone.utc)
                await session.commit()
                return row.id, value
            await session.commit()
        return None

    async def _checkpoint(self, run_id, value, node=None, output=None):
        while True:
            manager = get_resource_manager()
            if manager._emergency_stopped:
                raise RunCancelled("Cancelled by emergency stop")
            if datetime.fromisoformat(value["deadline"]) <= datetime.now(timezone.utc):
                raise RuntimeError("Deadline exceeded")
            async with db.async_session_factory() as session:
                await session.execute(text("BEGIN IMMEDIATE"))
                row = await session.get(Run, run_id)
                workflow = await session.get(Workflow, row.workflow_id) if row else None
                if (
                    row is None
                    or row.status != State.RUNNING
                    or saved_run(row) != value
                    or workflow is None
                    or workflow.user_id not in OWNER_IDS
                    or workflow.status == WorkflowStatus.ARCHIVED
                ):
                    raise RunCancelled("Run cancelled, archived or no longer authorized")
                paused = manager._paused or workflow.status == WorkflowStatus.PAUSED
                if not paused and node is not None:
                    event = {
                        "node_id": node.id,
                        "node_type": node.node_type.value,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "event": "completed" if output is not None else "started",
                    }
                    if output is not None:
                        event["output"] = output
                    row.execution_log = [*(row.execution_log or []), event]
                    row.current_node_id = node.id
                    bounded_json(row.execution_log, 131072)
                await session.commit()
            if not paused:
                return
            await asyncio.sleep(0.1)

    async def _invoke(self, run_id, value):
        plan = execution_plan(value['definition'])
        nodes = {node.id: node for node in plan}
        outgoing = {node.id: [] for node in plan}
        for edge in value['definition']['edges']:
            outgoing[edge['source_node_id']].append(edge)
        async with db.async_session_factory() as session:
            stored = await session.get(Run, run_id)
            completed = completed_events(stored)
        previous = ""
        current, step = plan[0].id, 0
        while current:
            node = nodes[current]
            # Reconstruct the chosen path from durable completed events. No
            # completed AI/delay node is invoked again after owner approval.
            if step < len(completed):
                event = completed[step]
                if event.get('node_id') != current or event.get('node_type') != node.node_type.value:
                    raise ValueError('Saved checkpoint path changed')
                result = event.get('output')
                if not isinstance(result, dict):
                    raise ValueError('Missing completed-node output')
                await self._checkpoint(run_id, value)
                if node.node_type == NodeType.AI_PROMPT:
                    previous = result['text']
                if node.node_type == NodeType.CONDITION and result.get('matched') is not condition_result(node.config, value['input'], previous):
                    raise ValueError('Saved branch decision changed')
                current = self._next(node, outgoing[current], result)
                step += 1
                continue
            await self._checkpoint(run_id, value, node=node)
            result = {"status": "completed"}
            config = node.config or {}
            if node.node_type == NodeType.AI_PROMPT:
                envelope = json.dumps(
                    {
                        "instruction": config["prompt"],
                        "trigger_data": value["input"],
                        "previous_output": previous,
                    },
                    ensure_ascii=False,
                )
                response = await get_ai_router().generate(
                    envelope,
                    system_prompt="Draft text for a manually reviewed workflow. Return text only. You have no tools and cannot perform actions or verify platform results.",
                    provider="ollama",
                    fallback_to_local=False,
                    max_tokens=config.get("max_tokens", 256),
                )
                if not response.content.strip() or len(response.content) > 8192:
                    raise RuntimeError("Invalid local model output")
                previous = response.content
                result = {
                    "text": previous,
                    "provider": response.provider,
                    "model": response.model,
                    "tokens_reported": response.total_tokens if response.usage_reported else None,
                    "actions_executed": False,
                }
            elif node.node_type == NodeType.DELAY:
                await asyncio.sleep(config["seconds"])
                result = {"waited_seconds": config["seconds"]}
            elif node.node_type == NodeType.CONDITION:
                result = {'matched': condition_result(config, value['input'], previous), 'actions_executed': False}
            elif node.node_type == NodeType.APPROVAL:
                result = await at_gate(run_id, value, node, previous)
            await self._checkpoint(run_id, value, node=node, output=result)
            current = self._next(node, outgoing[current], result)
            step += 1
        if step < len(completed):
            raise ValueError('Saved checkpoint extends beyond this path')

    @staticmethod
    def _next(node, edges, result):
        if node.node_type == NodeType.END:
            return None
        if node.node_type == NodeType.CONDITION:
            branch = 'true' if result['matched'] else 'false'
            return next(edge['target_node_id'] for edge in edges if edge.get('condition') == branch)
        return edges[0]['target_node_id']

    async def _finish(self, run_id, state, error=None):
        async with db.async_session_factory() as session:
            await session.execute(text("BEGIN IMMEDIATE"))
            if get_resource_manager()._emergency_stopped:
                state, error = State.CANCELLED, "Cancelled by emergency stop"
            row = await session.get(Run, run_id)
            if row and row.status == State.RUNNING:
                workflow = await session.get(Workflow, row.workflow_id)
                if (
                    workflow is None
                    or workflow.user_id not in OWNER_IDS
                    or workflow.status == WorkflowStatus.ARCHIVED
                ):
                    state, error = State.CANCELLED, "Run archived or no longer authorized"
                changed = await session.execute(
                    update(Run)
                    .where(Run.id == run_id, Run.status == State.RUNNING)
                    .values(status=state, error=error, completed_at=datetime.now(timezone.utc))
                )
                if changed.rowcount:
                    if state == State.COMPLETED and workflow:
                        workflow.run_count += 1
                        workflow.last_run_at = datetime.now(timezone.utc)
                    session.add(
                        AuditLog(
                            action=AuditAction.EXECUTE,
                            resource_type="workflow_execution",
                            resource_id=run_id,
                            description="Local workflow execution " + state.value,
                        )
                    )
            await session.commit()

    async def _one(self, claim):
        key, value = claim
        self._active_id = key
        started = False
        async def admitted():
            nonlocal started
            started = True
            return await self._invoke(key, value)
        try:
            self._operation = asyncio.create_task(
                get_resource_manager().submit_task(
                    "workflow-" + key, admitted
                )
            )
            await asyncio.wait_for(self._operation, timeout=180)
            await self._finish(key, State.COMPLETED)
        except asyncio.CancelledError:
            await self._finish(key, State.CANCELLED, "Execution cancelled or runtime shutting down")
            if self._closing:
                raise
        except ReviewWait:
            pass  # Durable WAITING_APPROVAL releases this resource task.
        except WorkAdmissionRefused:
            if started:
                # A refusal raised inside actual work is not proof it did not run.
                await self._finish(key, State.FAILED, 'An admitted operation failed; no automatic replay')
            else:
                await self._defer_unstarted(key, value)
        except RunCancelled:
            await self._finish(
                key, State.CANCELLED, "Execution cancelled, archived or no longer authorized"
            )
        except Exception as error:
            logger.warning('Local workflow segment failed (%s)', type(error).__name__)
            await self._finish(
                key,
                State.FAILED,
                "Execution failed, timed out or was interrupted. Check local model, resource headroom and saved inputs.",
            )
        finally:
            self._operation = self._active_id = None

    async def _defer_unstarted(self, key, value):
        """Close claim/admission race without replaying an invoked operation."""
        async with db.async_session_factory() as session:
            await session.execute(text('BEGIN IMMEDIATE'))
            row = await session.get(Run, key)
            if row and row.status == State.RUNNING and saved_run(row) == value:
                workflow = await session.get(Workflow, row.workflow_id)
                if (get_resource_manager()._emergency_stopped or not workflow or
                        workflow.user_id not in OWNER_IDS or workflow.status == WorkflowStatus.ARCHIVED):
                    row.status, row.error = State.CANCELLED, 'Work cancelled before admission'
                    row.completed_at = datetime.now(timezone.utc)
                elif datetime.fromisoformat(value['deadline']) <= datetime.now(timezone.utc):
                    row.status, row.error = State.FAILED, 'Queued run expired before admission'
                    row.completed_at = datetime.now(timezone.utc)
                else:
                    row.status = State.QUEUED
            await session.commit()

    async def _run(self):
        while True:
            try:
                if get_resource_manager().can_accept_work()[0]:
                    claim = await self._claim()
                    if claim:
                        await self._one(claim)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.error("Saved workflow dispatch unavailable; no success is assumed")
            await asyncio.sleep(0.25)

    def cancel(self, key):
        if self._active_id == key and self._operation is not None:
            self._operation.cancel()

    async def stop(self):
        self._closing = True
        try:
            if self._task is not None:
                self._task.cancel()
                with suppress(asyncio.CancelledError):
                    await self._task
        finally:
            self._task = self._operation = self._active_id = None
            if self._lease is not None:
                self._lease.release()
                self._lease = None


workflow_worker = WorkflowWorker()
