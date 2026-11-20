"""Small shared bridge: scoped reads/proposals; human approval owns dispatch."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import secrets
from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select, text

from app.models.integration import IntegrationGrant, IntegrationProposal
from app.services.workflow_graphs import bounded_json, execution_plan, fingerprint, owned_workflow, revision_number, snapshot

SCOPES = {'read_status', 'read_goals', 'read_workflows', 'propose_workflow', 'read_own_results'}


def catalog():
    return json.loads(Path(__file__).with_name('integration_catalog.json').read_text(encoding='utf-8'))


def utc(value):
    return value.replace(tzinfo=timezone.utc) if value and value.tzinfo is None else value


class GrantInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    client: str = Field(min_length=1, max_length=40)
    label: str = Field(min_length=1, max_length=100)
    scopes: list[Literal['read_status', 'read_goals', 'read_workflows', 'propose_workflow', 'read_own_results']] = Field(default=['read_status'], min_length=1, max_length=5)
    lifetime_hours: int = Field(default=24, ge=1, le=168, strict=True)


class ProposalInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    request_key: str = Field(min_length=1, max_length=64, pattern=r'^[a-zA-Z0-9_-]+$')
    title: str = Field(min_length=1, max_length=160)
    workflow_id: str = Field(min_length=1, max_length=36)
    expected_revision: int = Field(ge=1, strict=True)
    fingerprint: str = Field(pattern=r'^[a-f0-9]{64}$')
    trigger_data: dict = Field(default_factory=dict)


def grant_response(row):
    return {name: utc(getattr(row, name)) if name.endswith('_at') else getattr(row, name)
            for name in ['id', 'client', 'label', 'scopes', 'created_at', 'expires_at', 'revoked_at']}


def proposal_response(row):
    return {name: utc(getattr(row, name)) if name.endswith('_at') else getattr(row, name)
            for name in ['id', 'grant_id', 'title', 'payload', 'status', 'revision', 'execution_id', 'created_at', 'expires_at', 'reviewed_at']}


async def new_grant(session, body):
    if body.client not in {item['id'] for item in catalog()}:
        raise HTTPException(422, 'Choose a reviewed integration from the catalog')
    await session.execute(text('BEGIN IMMEDIATE'))
    now = datetime.now(timezone.utc)
    count = await session.scalar(select(func.count()).select_from(IntegrationGrant).where(
        IntegrationGrant.revoked_at.is_(None), IntegrationGrant.expires_at > now))
    if count >= 16:
        raise HTTPException(429, 'At most16 active integration grants are allowed; revoke an unused grant first')
    token = 'javo_client_' + secrets.token_urlsafe(32)
    row = IntegrationGrant(client=body.client, label=body.label, scopes=sorted(set(body.scopes)),
        token_hash=hashlib.sha256(token.encode()).hexdigest(), created_at=now,
        expires_at=now + timedelta(hours=body.lifetime_hours))
    session.add(row)
    await session.commit()
    return {**grant_response(row), 'token': token, 'message': 'Shown once. This scoped token cannot approve, publish, execute shell commands or change runtime controls.'}


async def client_identity(session, header):
    from app.core.local_auth import is_valid_owner_token
    from app.config import get_settings
    configured = get_settings().owner_access_token
    if not configured or len(configured.get_secret_value()) < 32:
        raise HTTPException(503, 'Local owner access must be configured before integration clients can connect')
    if is_valid_owner_token(header):
        return {'grant_id': 'owner', 'scopes': SCOPES}
    scheme, _, token = (header or '').partition(' ')
    if scheme.casefold() != 'bearer' or not token.startswith('javo_client_') or len(token) > 128:
        raise HTTPException(401, 'Integration authorization required')
    row = await session.scalar(select(IntegrationGrant).where(
        IntegrationGrant.token_hash == hashlib.sha256(token.encode()).hexdigest()))
    if not row or row.revoked_at or utc(row.expires_at) <= datetime.now(timezone.utc):
        raise HTTPException(401, 'Integration token is revoked, expired or invalid')
    return {'grant_id': row.id, 'scopes': set(row.scopes)}


async def propose(session, principal, body):
    if 'propose_workflow' not in principal['scopes']:
        raise HTTPException(403, 'This grant cannot propose workflow runs')
    bounded_json(body.trigger_data, 8192)
    await session.execute(text('BEGIN IMMEDIATE'))
    payload = body.model_dump(exclude={'title', 'request_key'})
    existing = await session.scalar(select(IntegrationProposal).where(
        IntegrationProposal.grant_id == principal['grant_id'], IntegrationProposal.request_key == body.request_key))
    if existing:
        if existing.payload != payload or existing.title != body.title:
            raise HTTPException(409, 'This request key already belongs to different proposal content')
        return proposal_response(existing)
    now = datetime.now(timezone.utc)
    pending = await session.scalar(select(func.count()).select_from(IntegrationProposal).where(
        IntegrationProposal.status == 'pending', IntegrationProposal.expires_at > now))
    recent = await session.scalar(select(func.count()).select_from(IntegrationProposal).where(
        IntegrationProposal.grant_id == principal['grant_id'], IntegrationProposal.created_at > now - timedelta(hours=1)))
    if pending >= 100 or recent >= 30:
        raise HTTPException(429, 'Proposal inbox limit reached; review pending work or wait before retrying')
    graph = await owned_workflow(session, body.workflow_id)
    definition = snapshot(graph)
    execution_plan(definition)
    if await revision_number(session, graph.id) != body.expected_revision or fingerprint(definition) != body.fingerprint:
        raise HTTPException(409, 'Reload the saved workflow before proposing a run')
    row = IntegrationProposal(grant_id=principal['grant_id'], request_key=body.request_key,
        title=body.title, payload=payload, created_at=now, expires_at=now + timedelta(hours=24))
    session.add(row)
    await session.commit()
    return proposal_response(row)


async def review(session, proposal_id, revision, decision):
    from app.services.workflow_jobs import enqueue
    await session.execute(text('BEGIN IMMEDIATE'))
    row = await session.get(IntegrationProposal, proposal_id)
    if not row:
        raise HTTPException(404, 'Proposal not found')
    if row.status != 'pending' or row.revision != revision:
        raise HTTPException(409, 'Proposal already changed; reload its current receipt')
    now = datetime.now(timezone.utc)
    if decision == 'approve':
        if utc(row.expires_at) <= now:
            raise HTTPException(409, 'Proposal expired. Ask the client to propose the current saved revision again.')
        if row.grant_id != 'owner':
            grant = await session.get(IntegrationGrant, row.grant_id)
            if not grant or grant.revoked_at or utc(grant.expires_at) <= now or 'propose_workflow' not in grant.scopes:
                raise HTTPException(409, 'Proposal source grant is no longer authorized')
        data = ProposalInput.model_validate({**row.payload, 'request_key': row.request_key, 'title': row.title})
        graph = await owned_workflow(session, data.workflow_id)
        definition = snapshot(graph)
        execution_plan(definition)
        current = await revision_number(session, graph.id)
        if current != data.expected_revision or fingerprint(definition) != data.fingerprint:
            raise HTTPException(409, 'Saved workflow changed. Reject this stale proposal and review a fresh one.')
        # Save the decision and the actual queued run in one transaction.
        run = await enqueue(session, graph, definition, current, data.trigger_data, commit=False)
        row.execution_id = run.id
    row.status, row.reviewed_at, row.revision = ('approved' if decision == 'approve' else 'rejected'), now, row.revision + 1
    await session.commit()
    return proposal_response(row)
