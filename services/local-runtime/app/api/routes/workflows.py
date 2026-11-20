"""Owner-scoped saved workflow graphs, revision checks and actual local runs."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import Field, ValidationError
from sqlalchemy import delete, func, select, text

from app.core.local_identity import LOCAL_OWNER, OWNER_IDS, ensure_local_owner
from app.database import get_session
from app.models.security import AuditAction, AuditLog
from app.models.workflow import (
    Workflow,
    WorkflowNode,
    WorkflowEdge,
    WorkflowRevision,
    WorkflowExecution,
    WorkflowStatus,
)
from app.services.workflow_graphs import (
    Definition,
    Input,
    bounded_json,
    execution_plan,
    fingerprint,
    owned_workflow,
    revision_number,
    snapshot,
)

router = APIRouter(prefix="/workflows", tags=["workflows"])


def utc_date(value):
    return value.replace(tzinfo=timezone.utc) if value and value.tzinfo is None else value


class Create(Definition):
    user_id: str | None = None


class Update(Definition):
    expected_revision: int = Field(ge=0, strict=True)


class Restore(Input):
    expected_revision: int = Field(ge=0, strict=True)
    revision: int = Field(ge=1, strict=True)


class Execute(Input):
    expected_revision: int | None = Field(default=None, ge=0, strict=True)
    fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    trigger_data: dict = Field(default_factory=dict)


def audit(session, workflow_id, description):
    session.add(
        AuditLog(
            user_id=LOCAL_OWNER,
            action=AuditAction.UPDATE,
            resource_type="workflow",
            resource_id=workflow_id,
            description=description,
        )
    )


async def response(session, workflow):
    definition = snapshot(workflow)
    errors = []
    try:
        execution_plan(definition)
    except (ValueError, ValidationError):
        # Do not return raw validation input: graph config may contain private text.
        try:
            Definition.model_validate(definition)
            try:
                execution_plan(definition)
            except ValidationError:
                errors = ["Saved graph needs repair before running"]
            except ValueError as error:
                errors = [str(error)]  # Only fixed messages from our graph validator.
        except (ValueError, ValidationError):
            errors = ["Saved legacy graph needs repair before running"]
    return {
        **definition,
        "id": workflow.id,
        "user_id": workflow.user_id,
        "revision": await revision_number(session, workflow.id),
        "fingerprint": fingerprint(definition),
        "execution_available": not errors,
        "validation_errors": errors,
        "run_count": await session.scalar(
            select(func.count())
            .select_from(WorkflowExecution)
            .where(
                WorkflowExecution.workflow_id == workflow.id,
                WorkflowExecution.status == "COMPLETED",
                WorkflowExecution.trigger_data["_javo_workflow_run"].as_integer() == 1,
            )
        ),
        "reported_run_count": workflow.run_count,
        "last_run_at": utc_date(workflow.last_run_at),
        "created_at": utc_date(workflow.created_at),
        "updated_at": utc_date(workflow.updated_at),
    }


async def replace_graph(session, workflow, definition):
    node_ids, edge_ids = [n.id for n in definition.nodes], [e.id for e in definition.edges]
    for model, ids in ((WorkflowNode, node_ids), (WorkflowEdge, edge_ids)):
        if ids and await session.scalar(
            select(model.id).where(model.id.in_(ids), model.workflow_id != workflow.id).limit(1)
        ):
            raise HTTPException(
                409,
                "Graph identifiers belong to another workflow; make a copy with new identifiers",
            )
    workflow.edges.clear()
    await session.flush()
    workflow.nodes.clear()
    await session.flush()
    for node in definition.nodes:
        workflow.nodes.append(WorkflowNode(workflow_id=workflow.id, **node.model_dump()))
    await session.flush()
    for edge in definition.edges:
        workflow.edges.append(WorkflowEdge(workflow_id=workflow.id, **edge.model_dump()))
    for key in ("name", "description", "trigger_config", "viewport"):
        setattr(workflow, key, getattr(definition, key))
    workflow.status = WorkflowStatus(definition.status)
    workflow.updated_at = datetime.now(timezone.utc)
    await session.flush()
    number = await revision_number(session, workflow.id) + 1
    saved = snapshot(workflow)
    session.add(
        WorkflowRevision(
            id=str(uuid4()),
            workflow_id=workflow.id,
            revision=number,
            definition=saved,
            fingerprint=fingerprint(saved),
        )
    )
    await session.flush()


async def check_revision(session, workflow_id, expected):
    if expected != await revision_number(session, workflow_id):
        raise HTTPException(
            409, "This workflow changed elsewhere. Reload the saved version before overwriting it."
        )


@router.get("/")
async def list_workflows(
    limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0), session=Depends(get_session)
):
    await session.execute(text("BEGIN"))
    ids = (
        await session.scalars(
            select(Workflow.id)
            .where(Workflow.user_id.in_(OWNER_IDS))
            .order_by(Workflow.updated_at.desc(), Workflow.id)
            .offset(offset)
            .limit(limit)
        )
    ).all()
    return [await response(session, await owned_workflow(session, key)) for key in ids]


@router.post("/", status_code=201)
async def create_workflow(body: Create, session=Depends(get_session)):
    if body.user_id is not None and body.user_id != LOCAL_OWNER:
        raise HTTPException(403, "Cannot assign another workflow owner")
    await session.execute(text("BEGIN IMMEDIATE"))
    await ensure_local_owner(session)
    workflow = Workflow(
        id=str(uuid4()),
        user_id=LOCAL_OWNER,
        name=body.name,
        status=WorkflowStatus.DRAFT,
        nodes=[],
        edges=[],
    )
    session.add(workflow)
    await session.flush()
    await replace_graph(session, workflow, body)
    audit(
        session,
        workflow.id,
        "Workflow definition saved as a new revision; no automatic trigger enabled",
    )
    result = await response(session, workflow)
    await session.commit()
    return result


@router.get("/executions/{exec_id}")
async def get_execution(exec_id: str, session=Depends(get_session)):
    from app.services.workflow_jobs import run_response

    execution = await session.get(WorkflowExecution, exec_id)
    if execution is None:
        raise HTTPException(404, "Workflow execution not found")
    await owned_workflow(session, execution.workflow_id)
    return run_response(execution)


@router.get('/node-types')
async def node_types():
    from app.models.workflow import NodeType
    from app.services.workflow_graphs import SUPPORTED_NODES
    defaults = {'trigger': {}, 'end': {}, 'ai_prompt': {'prompt': 'Draft a short original caption from the supplied brief.', 'provider': 'ollama', 'max_tokens': 256},
                'delay': {'seconds': 1}, 'schedule': {'cron': '0 9 * * *', 'timezone': 'Asia/Kolkata'},
                'condition': {'source': 'input', 'field': 'generate', 'operator': 'equals', 'value': True}, 'approval': {'instructions': 'Review the actual saved draft before continuing.'},
                'retry': {'max_attempts': 2}, 'error_handler': {'mode': 'stop_and_report'}}
    return [{'node_type': kind.value, 'execution_available': kind.value in SUPPORTED_NODES,
             'default_config': defaults.get(kind.value, {}), 'owner_review_required': True,
             'message': 'Supported bounded manual local-text node' if kind.value in SUPPORTED_NODES else
                'Planning node only in the native executor. Use a separately configured reviewed n8n path where supported; this node is never silently executed.'}
             for kind in NodeType]


@router.get('/templates')
async def workflow_templates():
    from uuid import uuid4
    result = []
    for name, prompt in [
        ('Reviewed caption draft', 'Write one short original caption from the supplied trigger brief. Use only supplied facts. Text advice only; no action claims.'),
        ('Hindi voice script', 'Write a short natural Hindi voiceover in Devanagari from the supplied brief. Keep it below600 characters. Do not claim actions or invented facts.'),
        ('Source-labelled trend ideas', 'Suggest three original content ideas using only the supplied trend titles, sources and timestamps. State missing context. Do not claim live social analytics or guaranteed popularity.'),
    ]:
        first, middle, end = [str(uuid4()) for _ in range(3)]
        result.append({'name': name, 'description': 'Manual local-text template. Review before running. Voice/media rendering and publishing are separate explicit operations.',
            'status': 'draft', 'nodes': [
                {'id': first, 'node_type': 'trigger', 'label': 'Reviewed manual start', 'position_x': 30, 'position_y': 90, 'is_entry_point': True, 'config': {}},
                {'id': middle, 'node_type': 'ai_prompt', 'label': name, 'position_x': 300, 'position_y': 90, 'config': {'prompt': prompt, 'provider': 'ollama', 'max_tokens': 256}},
                {'id': end, 'node_type': 'end', 'label': 'Saved text result', 'position_x': 570, 'position_y': 90, 'config': {}}],
            'edges': [{'source_node_id': first, 'target_node_id': middle}, {'source_node_id': middle, 'target_node_id': end}]})
    from app.services.workflow_graphs import conditional_review_template
    result.append(conditional_review_template())
    return result


@router.get('/approvals')
async def node_reviews(session=Depends(get_session)):
    from app.models.workflow import WorkflowNodeReview, WorkflowExecutionStatus
    from app.services.workflow_reviews import utc
    rows = (await session.execute(select(WorkflowNodeReview, WorkflowExecution, Workflow).join(
        WorkflowExecution, WorkflowExecution.id == WorkflowNodeReview.execution_id).join(
        Workflow, Workflow.id == WorkflowExecution.workflow_id).where(Workflow.user_id.in_(OWNER_IDS)).order_by(
        WorkflowNodeReview.created_at.desc()).limit(100))).all()
    return [{'id': review.id, 'workflow_name': workflow.name, 'execution_id': run.id,
        'node_id': review.node_id, 'status': review.status, 'revision': review.revision,
        'execution_status': run.status.value, 'expires_at': utc(review.expires_at),
        'waiting': run.status == WorkflowExecutionStatus.WAITING_APPROVAL and review.status == 'pending'}
        for review, run, workflow in rows]


@router.get('/approvals/{review_id}')
async def node_review_preview(review_id: str, session=Depends(get_session)):
    from app.services.workflow_reviews import inspect
    await session.execute(text('BEGIN'))
    return (await inspect(session, review_id))[2]


class NodeReviewDecision(Input):
    expected_revision: int = Field(ge=1, strict=True)
    fingerprint: str = Field(pattern=r'^[a-f0-9]{64}$')
    decision: Literal['approve', 'reject']


@router.post('/approvals/{review_id}/decision')
async def node_review_decision(review_id: str, body: NodeReviewDecision, session=Depends(get_session)):
    from app.services.workflow_reviews import decide
    return await decide(session, review_id, body.expected_revision, body.fingerprint, body.decision)


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str, session=Depends(get_session)):
    await session.execute(text("BEGIN"))
    return await response(session, await owned_workflow(session, workflow_id))


@router.put("/{workflow_id}")
async def update_workflow(workflow_id: str, body: Update, session=Depends(get_session)):
    await session.execute(text("BEGIN IMMEDIATE"))
    workflow = await owned_workflow(session, workflow_id)
    await check_revision(session, workflow_id, body.expected_revision)
    await replace_graph(session, workflow, body)
    audit(session, workflow_id, "Workflow definition updated; previous revisions retained")
    result = await response(session, workflow)
    await session.commit()
    return result


@router.get("/{workflow_id}/revisions")
async def revisions(
    workflow_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session=Depends(get_session),
):
    await owned_workflow(session, workflow_id)
    rows = (
        await session.scalars(
            select(WorkflowRevision)
            .where(WorkflowRevision.workflow_id == workflow_id)
            .order_by(WorkflowRevision.revision.desc())
            .offset(offset)
            .limit(limit)
        )
    ).all()
    return [
        {
            "revision": row.revision,
            "fingerprint": row.fingerprint,
            "name": row.definition.get("name"),
            "created_at": utc_date(row.created_at),
        }
        for row in rows
    ]


@router.post("/{workflow_id}/restore")
async def restore_revision(workflow_id: str, body: Restore, session=Depends(get_session)):
    await session.execute(text("BEGIN IMMEDIATE"))
    workflow = await owned_workflow(session, workflow_id)
    await check_revision(session, workflow_id, body.expected_revision)
    revision = await session.scalar(
        select(WorkflowRevision).where(
            WorkflowRevision.workflow_id == workflow_id, WorkflowRevision.revision == body.revision
        )
    )
    if revision is None:
        raise HTTPException(404, "Workflow revision not found")
    try:
        definition = Definition.model_validate(revision.definition)
    except (ValueError, ValidationError):
        raise HTTPException(
            503, "Saved revision is invalid; original definition was retained"
        ) from None
    if revision.fingerprint != fingerprint(revision.definition):
        raise HTTPException(
            503, "Saved revision integrity check failed; original definition was retained"
        )
    await replace_graph(session, workflow, definition)
    audit(session, workflow_id, "Earlier workflow definition restored as a new revision")
    result = await response(session, workflow)
    await session.commit()
    return result


@router.delete("/{workflow_id}", status_code=204)
async def delete_workflow(
    workflow_id: str, expected_revision: int = Query(ge=0), session=Depends(get_session)
):
    await session.execute(text("BEGIN IMMEDIATE"))
    workflow = await owned_workflow(session, workflow_id)
    await check_revision(session, workflow_id, expected_revision)
    if await session.scalar(
        select(WorkflowExecution.id).where(WorkflowExecution.workflow_id == workflow_id).limit(1)
    ):
        raise HTTPException(
            409, "This workflow has execution history. Archive it to preserve the receipts."
        )
    await session.execute(
        delete(WorkflowRevision).where(WorkflowRevision.workflow_id == workflow_id)
    )
    audit(session, workflow_id, "Unused workflow and definition revisions removed")
    await session.delete(workflow)
    await session.commit()


@router.post("/{workflow_id}/execute", status_code=202)
async def execute_workflow(workflow_id: str, body: Execute, session=Depends(get_session)):
    from app.services.workflow_jobs import enqueue, run_response

    await session.execute(text("BEGIN IMMEDIATE"))
    workflow = await owned_workflow(session, workflow_id)
    definition = snapshot(workflow)
    try:
        execution_plan(definition)
    except (ValueError, ValidationError):
        raise HTTPException(
            501,
            "This graph is not executable by the supported local executor; inspect its validation messages",
        ) from None
    if body.expected_revision is None or body.fingerprint is None:
        raise HTTPException(422, "Review a saved revision and fingerprint before running")
    await check_revision(session, workflow_id, body.expected_revision)
    if body.fingerprint != fingerprint(definition):
        raise HTTPException(409, "The saved graph changed; reload and review before running")
    try:
        bounded_json(body.trigger_data, 8192)
    except (ValueError, TypeError):
        raise HTTPException(422, "Trigger data exceeds its supported limit") from None
    return run_response(
        await enqueue(session, workflow, definition, body.expected_revision, body.trigger_data)
    )


@router.get("/{workflow_id}/executions")
async def list_executions(
    workflow_id: str, limit: int = Query(50, ge=1, le=100), session=Depends(get_session)
):
    from app.services.workflow_jobs import run_response

    await owned_workflow(session, workflow_id)
    rows = (
        await session.scalars(
            select(WorkflowExecution)
            .where(WorkflowExecution.workflow_id == workflow_id)
            .order_by(WorkflowExecution.started_at.desc(), WorkflowExecution.id)
            .limit(limit)
        )
    ).all()
    return [run_response(row) for row in rows]


@router.post("/{workflow_id}/executions/{exec_id}/cancel")
async def cancel_run(workflow_id: str, exec_id: str, session=Depends(get_session)):
    from app.services.workflow_jobs import cancel

    await session.execute(text("BEGIN IMMEDIATE"))
    await owned_workflow(session, workflow_id)
    execution = await session.get(WorkflowExecution, exec_id)
    if execution is None or execution.workflow_id != workflow_id:
        raise HTTPException(404, "Workflow execution not found")
    await cancel(session, execution)
    return {"status": "cancelled"}
