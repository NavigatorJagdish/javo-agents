"""Agent management routes."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.models.agent import (
    AgentConfig,
    AgentDefinition,
    AgentExecution,
    AgentStatus,
    ExecutionStatus,
)

router = APIRouter(prefix="/agents", tags=["agents"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class AgentConfigSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    system_prompt: Optional[str] = None
    retry_policy: Optional[dict[str, Any]] = None
    rate_limits: Optional[dict[str, Any]] = None
    custom_settings: Optional[dict[str, Any]] = None


class AgentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    agent_key: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    version: str = "1.0.0"
    status: str = AgentStatus.IDLE.value
    trust_score: float = 1.0
    is_enabled: bool = True


class AgentDetail(AgentSummary):
    capabilities: Optional[list[str]] = None
    input_schema: Optional[dict[str, Any]] = None
    output_schema: Optional[dict[str, Any]] = None
    tools: Optional[list[str]] = None
    dependencies: Optional[list[str]] = None
    config: Optional[AgentConfigSchema] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RunAgentRequest(BaseModel):
    task_data: dict[str, Any] = Field(default_factory=dict)
    task_id: Optional[str] = None


class RunAgentResponse(BaseModel):
    execution_id: str
    agent_id: str
    agent_key: str
    status: str


class AgentConfigUpdate(BaseModel):
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    system_prompt: Optional[str] = None
    retry_policy: Optional[dict[str, Any]] = None
    rate_limits: Optional[dict[str, Any]] = None
    custom_settings: Optional[dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _find_agent(
    agent_name: str, session: AsyncSession, load_config: bool = False
) -> AgentDefinition:
    stmt = select(AgentDefinition).where(
        or_(
            AgentDefinition.agent_key == agent_name,
            AgentDefinition.name == agent_name,
        )
    )
    if load_config:
        stmt = stmt.options(selectinload(AgentDefinition.config))
    result = await session.execute(stmt)
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_name}' not found",
        )
    return agent


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/", response_model=list[AgentSummary])
async def list_agents(session: AsyncSession = Depends(get_session)) -> list[AgentSummary]:
    """List all registered agents with their current status."""
    result = await session.execute(select(AgentDefinition).order_by(AgentDefinition.agent_key))
    agents = result.scalars().all()
    return [AgentSummary.model_validate(a) for a in agents]


@router.get("/{agent_name}", response_model=AgentDetail)
async def get_agent(agent_name: str, session: AsyncSession = Depends(get_session)) -> AgentDetail:
    """Get detailed information about a specific agent."""
    agent = await _find_agent(agent_name, session, load_config=True)
    return AgentDetail.model_validate(agent)


@router.post("/{agent_name}/run", response_model=RunAgentResponse, status_code=status.HTTP_202_ACCEPTED)
async def run_agent(
    agent_name: str,
    body: RunAgentRequest,
    session: AsyncSession = Depends(get_session),
) -> RunAgentResponse:
    """Dispatch a task execution to the named agent."""
    agent = await _find_agent(agent_name, session)
    if not agent.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Agent '{agent.agent_key}' is disabled",
        )

    execution = AgentExecution(
        id=str(uuid4()),
        agent_id=agent.id,
        task_id=body.task_id,
        status=ExecutionStatus.QUEUED,
        inputs=body.task_data,
    )
    session.add(execution)
    await session.commit()
    await session.refresh(execution)

    return RunAgentResponse(
        execution_id=execution.id,
        agent_id=agent.id,
        agent_key=agent.agent_key,
        status=ExecutionStatus.QUEUED.value,
    )


@router.put("/{agent_name}/config", response_model=AgentDetail)
async def update_agent_config(
    agent_name: str,
    body: AgentConfigUpdate,
    session: AsyncSession = Depends(get_session),
) -> AgentDetail:
    """Update or create the configuration for an agent."""
    agent = await _find_agent(agent_name, session, load_config=True)

    update_fields = body.model_dump(exclude_unset=True)
    if agent.config is None:
        config = AgentConfig(id=str(uuid4()), agent_id=agent.id, **update_fields)
        session.add(config)
    else:
        for key, value in update_fields.items():
            setattr(agent.config, key, value)

    await session.commit()
    agent = await _find_agent(agent_name, session, load_config=True)
    return AgentDetail.model_validate(agent)


@router.post("/{agent_name}/enable", response_model=AgentSummary)
async def enable_agent(agent_name: str, session: AsyncSession = Depends(get_session)) -> AgentSummary:
    """Enable an agent."""
    agent = await _find_agent(agent_name, session)
    agent.is_enabled = True
    if agent.status == AgentStatus.DISABLED:
        agent.status = AgentStatus.IDLE
    await session.commit()
    await session.refresh(agent)
    return AgentSummary.model_validate(agent)


@router.post("/{agent_name}/disable", response_model=AgentSummary)
async def disable_agent(agent_name: str, session: AsyncSession = Depends(get_session)) -> AgentSummary:
    """Disable an agent."""
    agent = await _find_agent(agent_name, session)
    agent.is_enabled = False
    agent.status = AgentStatus.DISABLED
    await session.commit()
    await session.refresh(agent)
    return AgentSummary.model_validate(agent)
