"""Visual workflow CRUD and execution routes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.models.user import User
from app.models.workflow import (
    NodeType,
    Workflow,
    WorkflowEdge,
    WorkflowExecution,
    WorkflowExecutionStatus,
    WorkflowNode,
    WorkflowStatus,
)

router = APIRouter(prefix="/workflows", tags=["workflows"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class WorkflowNodeInput(BaseModel):
    id: Optional[str] = None
    node_type: NodeType
    label: str = Field(..., min_length=1, max_length=128)
    position_x: float = 0.0
    position_y: float = 0.0
    config: Optional[dict[str, Any]] = None
    is_entry_point: bool = False


class WorkflowNodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workflow_id: str
    node_type: NodeType
    label: str
    position_x: float
    position_y: float
    config: Optional[dict[str, Any]] = None
    is_entry_point: bool


class WorkflowEdgeInput(BaseModel):
    id: Optional[str] = None
    source_node_id: str
    target_node_id: str
    condition: Optional[str] = None
    label: Optional[str] = None


class WorkflowEdgeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workflow_id: str
    source_node_id: str
    target_node_id: str
    condition: Optional[str] = None
    label: Optional[str] = None


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    description: Optional[str] = None
    user_id: Optional[str] = None
    status: WorkflowStatus = WorkflowStatus.DRAFT
    trigger_config: Optional[dict[str, Any]] = None
    viewport: Optional[dict[str, Any]] = None
    nodes: list[WorkflowNodeInput] = Field(default_factory=list)
    edges: list[WorkflowEdgeInput] = Field(default_factory=list)


class WorkflowUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=256)
    description: Optional[str] = None
    status: Optional[WorkflowStatus] = None
    trigger_config: Optional[dict[str, Any]] = None
    viewport: Optional[dict[str, Any]] = None
    nodes: Optional[list[WorkflowNodeInput]] = None
    edges: Optional[list[WorkflowEdgeInput]] = None


class WorkflowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    status: WorkflowStatus
    trigger_config: Optional[dict[str, Any]] = None
    viewport: Optional[dict[str, Any]] = None
    run_count: int = 0
    last_run_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    nodes: list[WorkflowNodeResponse] = Field(default_factory=list)
    edges: list[WorkflowEdgeResponse] = Field(default_factory=list)


class ExecuteWorkflowRequest(BaseModel):
    trigger_data: dict[str, Any] = Field(default_factory=dict)


class WorkflowExecutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workflow_id: str
    status: WorkflowExecutionStatus
    trigger_data: Optional[dict[str, Any]] = None
    current_node_id: Optional[str] = None
    execution_log: Optional[list[dict[str, Any]]] = None
    error: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _get_workflow_or_404(workflow_id: str, session: AsyncSession) -> Workflow:
    stmt = (
        select(Workflow)
        .where(Workflow.id == workflow_id)
        .options(selectinload(Workflow.nodes), selectinload(Workflow.edges))
    )
    result = await session.execute(stmt)
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return wf


async def _resolve_user_id(requested_user_id: Optional[str], session: AsyncSession) -> str:
    if requested_user_id:
        return requested_user_id
    res = await session.execute(select(User.id).limit(1))
    return res.scalar_one_or_none() or "default-user"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/", response_model=list[WorkflowResponse])
async def list_workflows(
    status_filter: Optional[WorkflowStatus] = Query(default=None, alias="status"),
    session: AsyncSession = Depends(get_session),
) -> list[WorkflowResponse]:
    """List all workflows with their nodes and edges."""
    stmt = select(Workflow).options(selectinload(Workflow.nodes), selectinload(Workflow.edges))
    if status_filter is not None:
        stmt = stmt.where(Workflow.status == status_filter)
    result = await session.execute(stmt.order_by(Workflow.created_at.desc()))
    return [WorkflowResponse.model_validate(w) for w in result.scalars().all()]


@router.post("/", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    body: WorkflowCreate,
    session: AsyncSession = Depends(get_session),
) -> WorkflowResponse:
    """Create a workflow with optional initial nodes and edges."""
    wf_id = str(uuid4())
    user_id = await _resolve_user_id(body.user_id, session)
    wf = Workflow(
        id=wf_id,
        user_id=user_id,
        name=body.name,
        description=body.description,
        status=body.status,
        trigger_config=body.trigger_config,
        viewport=body.viewport,
    )
    session.add(wf)

    for node_in in body.nodes:
        session.add(
            WorkflowNode(
                id=node_in.id or str(uuid4()),
                workflow_id=wf_id,
                node_type=node_in.node_type,
                label=node_in.label,
                position_x=node_in.position_x,
                position_y=node_in.position_y,
                config=node_in.config,
                is_entry_point=node_in.is_entry_point,
            )
        )

    for edge_in in body.edges:
        session.add(
            WorkflowEdge(
                id=edge_in.id or str(uuid4()),
                workflow_id=wf_id,
                source_node_id=edge_in.source_node_id,
                target_node_id=edge_in.target_node_id,
                condition=edge_in.condition,
                label=edge_in.label,
            )
        )

    await session.commit()
    wf = await _get_workflow_or_404(wf_id, session)
    return WorkflowResponse.model_validate(wf)


@router.get("/executions/{exec_id}", response_model=WorkflowExecutionResponse)
async def get_execution(
    exec_id: str,
    session: AsyncSession = Depends(get_session),
) -> WorkflowExecutionResponse:
    """Get status and log of a specific workflow execution."""
    res = await session.execute(select(WorkflowExecution).where(WorkflowExecution.id == exec_id))
    execution = res.scalar_one_or_none()
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow execution not found")
    return WorkflowExecutionResponse.model_validate(execution)


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    session: AsyncSession = Depends(get_session),
) -> WorkflowResponse:
    """Retrieve a workflow by ID."""
    wf = await _get_workflow_or_404(workflow_id, session)
    return WorkflowResponse.model_validate(wf)


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str,
    body: WorkflowUpdate,
    session: AsyncSession = Depends(get_session),
) -> WorkflowResponse:
    """Update workflow metadata and optionally replace its graph (nodes/edges)."""
    wf = await _get_workflow_or_404(workflow_id, session)
    data = body.model_dump(exclude_unset=True)

    nodes_in = data.pop("nodes", None)
    edges_in = data.pop("edges", None)
    for key, value in data.items():
        setattr(wf, key, value)

    if nodes_in is not None:
        wf.nodes.clear()
        await session.flush()
        for n in body.nodes or []:
            wf.nodes.append(
                WorkflowNode(
                    id=n.id or str(uuid4()),
                    workflow_id=workflow_id,
                    node_type=n.node_type,
                    label=n.label,
                    position_x=n.position_x,
                    position_y=n.position_y,
                    config=n.config,
                    is_entry_point=n.is_entry_point,
                )
            )

    if edges_in is not None:
        wf.edges.clear()
        await session.flush()
        for e in body.edges or []:
            wf.edges.append(
                WorkflowEdge(
                    id=e.id or str(uuid4()),
                    workflow_id=workflow_id,
                    source_node_id=e.source_node_id,
                    target_node_id=e.target_node_id,
                    condition=e.condition,
                    label=e.label,
                )
            )

    await session.commit()
    wf = await _get_workflow_or_404(workflow_id, session)
    return WorkflowResponse.model_validate(wf)


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(workflow_id: str, session: AsyncSession = Depends(get_session)) -> None:
    """Delete a workflow."""
    wf = await _get_workflow_or_404(workflow_id, session)
    await session.delete(wf)
    await session.commit()


@router.post(
    "/{workflow_id}/execute",
    response_model=WorkflowExecutionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def execute_workflow(
    workflow_id: str,
    body: ExecuteWorkflowRequest = ExecuteWorkflowRequest(),
    session: AsyncSession = Depends(get_session),
) -> WorkflowExecutionResponse:
    """Trigger execution of a workflow."""
    wf = await _get_workflow_or_404(workflow_id, session)
    entry_node = next((n for n in wf.nodes if n.is_entry_point), wf.nodes[0] if wf.nodes else None)

    now = datetime.now(timezone.utc)
    execution = WorkflowExecution(
        id=str(uuid4()),
        workflow_id=wf.id,
        status=WorkflowExecutionStatus.RUNNING,
        trigger_data=body.trigger_data,
        current_node_id=entry_node.id if entry_node else None,
        execution_log=[
            {
                "timestamp": now.isoformat(),
                "event": "started",
                "node_id": entry_node.id if entry_node else None,
            }
        ],
    )
    wf.run_count += 1
    wf.last_run_at = now
    session.add(execution)
    await session.commit()
    await session.refresh(execution)
    return WorkflowExecutionResponse.model_validate(execution)


@router.get("/{workflow_id}/executions", response_model=list[WorkflowExecutionResponse])
async def list_workflow_executions(
    workflow_id: str,
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> list[WorkflowExecutionResponse]:
    """List past and running executions of a workflow."""
    await _get_workflow_or_404(workflow_id, session)
    stmt = (
        select(WorkflowExecution)
        .where(WorkflowExecution.workflow_id == workflow_id)
        .order_by(WorkflowExecution.started_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return [WorkflowExecutionResponse.model_validate(e) for e in result.scalars().all()]
