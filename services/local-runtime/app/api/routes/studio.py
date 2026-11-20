"""Owner-reviewed generation submissions, real artifacts, explicit trend refresh."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import hashlib
import os
from pathlib import Path
import tempfile
from typing import Literal
from uuid import uuid4
from defusedxml import ElementTree as ET

from fastapi import APIRouter, Depends, HTTPException, Query, Response
import httpx
from sqlalchemy import select, text

from app.core.provider_store import VaultUnavailable
from app.database import get_session
from app.models.studio import StudioJob, TrendSnapshot
from app.services import studio
from app.services.integrations import utc
from app.services.speech import require_capacity

router = APIRouter(prefix='/studio', tags=['creation-studio'])


def config():
    try:
        return studio.configuration()
    except (ValueError, VaultUnavailable):
        raise HTTPException(503, 'Creation settings are locked or damaged. Recover the original configuration and key.') from None


def receipt(row):
    return {'id': row.id, 'kind': row.kind, 'status': row.status, 'request': row.request,
            'created_at': utc(row.created_at), 'updated_at': utc(row.updated_at), 'message': row.message,
            'artifact_ready': bool(row.artifact), 'source': 'Configured local ComfyUI service',
            'model': row.configuration.get('image_checkpoint') if row.kind == 'image' else row.configuration.get('video_unet'),
            'actions_executed': False}


async def job(session, job_id):
    row = await session.get(StudioJob, job_id)
    if row is None:
        raise HTTPException(404, 'Generation job not found')
    return row


@router.get('/configuration')
async def configuration():
    return config()


@router.put('/configuration')
async def save_configuration(body: studio.Configuration):
    try:
        studio.vault().update(lambda value: value['settings'].update(body.model_dump()))
    except VaultUnavailable:
        raise HTTPException(503, 'Creation settings could not be saved. Existing settings were retained.') from None
    return config()


@router.post('/check/{kind}')
async def check(kind: Literal['image', 'video']):
    try:
        return await asyncio.wait_for(studio.preflight(config(), kind), 20)
    except HTTPException:
        raise
    except Exception:
        return {'ready': False, 'generation_verified': False, 'kind': kind,
                'message': 'Local service, native nodes or selected model files are unavailable. Check your ComfyUI setup. No generation was submitted.'}


@router.get('/jobs')
async def jobs(session=Depends(get_session)):
    rows = (await session.scalars(select(StudioJob).order_by(StudioJob.created_at.desc()).limit(50))).all()
    return [receipt(row) for row in rows]


@router.post('/jobs', status_code=202)
async def submit(body: studio.Generation, session=Depends(get_session)):
    previous = await session.scalar(select(StudioJob).where(StudioJob.request_key == body.request_key))
    if previous:
        if previous.request != body.model_dump():
            raise HTTPException(409, 'This request key belongs to different reviewed generation inputs')
        return receipt(previous)
    await session.rollback()
    manager = require_capacity()
    cfg = config()
    if cfg['fingerprint'] != body.configuration_fingerprint:
        raise HTTPException(409, 'Creation settings changed. Reload and review the selected models before submitting.')
    try:
        await asyncio.wait_for(studio.preflight(cfg, body.kind), 20)
    except Exception:
        raise HTTPException(503, 'Generation service or selected models are unavailable. No job was submitted.') from None
    await session.execute(text('BEGIN IMMEDIATE'))
    existing = await session.scalar(select(StudioJob).where(StudioJob.request_key == body.request_key))
    if existing:
        if existing.request != body.model_dump():
            raise HTTPException(409, 'This request key belongs to different reviewed generation inputs')
        return receipt(existing)
    active = await session.scalar(select(StudioJob.id).where(StudioJob.status.in_(['dispatching', 'queued', 'running', 'uncertain', 'cancel_requested'])).limit(1))
    if active:
        raise HTTPException(409, 'An existing generation is active or unconfirmed. Refresh its receipt before submitting another.')
    key = str(uuid4())
    now = datetime.now(timezone.utc)
    row = StudioJob(id=key, prompt_id=key, request_key=body.request_key, kind=body.kind,
        status='dispatching', request=body.model_dump(), configuration=cfg, created_at=now, updated_at=now,
        message='Submission intent saved. An accepted request is not a finished artifact.')
    session.add(row)
    await session.commit()
    try:
        result = await manager.submit_task('studio-'+key, lambda: studio.json_request(cfg, 'POST', '/prompt',
            payload={'prompt': studio.graph(cfg, body, key), 'client_id': 'javo-'+key, 'prompt_id': key}))
        if result.get('prompt_id') != key or result.get('node_errors'):
            raise ValueError('Generation service did not confirm the exact submitted job')
        next_status, next_message = 'queued', 'Accepted by the configured local service. Refresh to observe actual completion.'
    except httpx.HTTPStatusError as error:
        if 400 <= error.response.status_code < 500 and error.response.status_code != 408:
            next_status, next_message = 'failed', 'The generator rejected the submitted native graph. Check model and node compatibility; no success is claimed.'
        else:
            next_status, next_message = 'uncertain', 'Submission outcome is uncertain. Refresh this receipt; it is never automatically replayed.'
    except (Exception, asyncio.CancelledError):
        # Never repeat a POST whose outcome might have reached the generator.
        next_status, next_message = 'uncertain', 'Submission was not confirmed. Refresh this receipt; it is never automatically replayed.'
    await session.execute(text('BEGIN IMMEDIATE'))
    await session.refresh(row)
    if row.status == 'dispatching':
        row.status, row.message = next_status, next_message
        row.updated_at = datetime.now(timezone.utc)
    await session.commit()
    return receipt(row)


@router.post('/jobs/{job_id}/refresh')
async def refresh(job_id: str, session=Depends(get_session)):
    row = await job(session, job_id)
    if row.status in {'completed', 'failed', 'abandoned'}:
        return receipt(row)
    try:
        history = await studio.json_request(row.configuration, 'GET', '/history/'+row.prompt_id)
        entry = history.get(row.prompt_id)
        status, message, artifact = row.status, row.message, row.artifact
        if entry and entry.get('status', {}).get('status_str') == 'error':
            status, message = 'failed', 'The local generator reported an execution error. Inspect its own trusted diagnostics.'
        elif entry and entry.get('status', {}).get('completed') is True and entry.get('status', {}).get('status_str') == 'success':
            output = entry.get('outputs', {}).get('7' if row.kind == 'image' else '11', {})
            candidates = output.get('images') or output.get('videos') or output.get('gifs') or []
            if len(candidates) != 1:
                raise ValueError('Expected one actual generated output')
            reference, extension = studio.safe_artifact(candidates[0], row.kind)
            data = await studio.request(row.configuration, 'GET', '/view', params=reference,
                                        limit=16*1024*1024 if row.kind == 'image' else 64*1024*1024)
            mime = studio.media_type(data, extension)
            root = studio.artifact_root()
            root.mkdir(parents=True, exist_ok=True)
            if root.is_symlink():
                raise ValueError('Unsafe artifact directory')
            target = root/(row.id+extension)
            handle, temporary = tempfile.mkstemp(prefix=row.id, suffix='.tmp', dir=root)
            try:
                with os.fdopen(handle, 'wb') as output_file:
                    output_file.write(data)
                os.replace(temporary, target)
            finally:
                Path(temporary).unlink(missing_ok=True)
            artifact = {'filename': target.name, 'sha256': hashlib.sha256(data).hexdigest(), 'size': len(data), 'mime': mime}
            status, message = 'completed', 'Actual generated media downloaded and saved. Review its content and quality yourself.'
        else:
            queue = await studio.json_request(row.configuration, 'GET', '/queue')
            if any(isinstance(item, list) and len(item) > 1 and item[1] == row.prompt_id for item in queue.get('queue_running', [])):
                status, message = 'running', 'The configured local generator reports this request running.'
            elif any(isinstance(item, list) and len(item) > 1 and item[1] == row.prompt_id for item in queue.get('queue_pending', [])):
                status, message = 'queued', 'The configured local generator reports this request queued.'
            else:
                status, message = 'uncertain', 'No matching queued/running/completed receipt was observed. Inspect the service; no success or replay is assumed.'
    except Exception:
        raise HTTPException(503, 'Generation receipt or artifact could not be safely verified. Existing saved state was retained.') from None
    await session.execute(text('BEGIN IMMEDIATE'))
    await session.refresh(row)
    if row.status not in {'abandoned', 'completed', 'failed'}:
        row.status, row.message, row.artifact = status, message, artifact
        row.updated_at = datetime.now(timezone.utc)
    await session.commit()
    return receipt(row)


@router.post('/jobs/{job_id}/remove-queued')
async def remove_queued(job_id: str, session=Depends(get_session)):
    row = await job(session, job_id)
    if row.status in {'completed', 'failed', 'abandoned'}:
        raise HTTPException(409, 'This receipt is already final')
    try:
        queue = await studio.json_request(row.configuration, 'GET', '/queue')
        if not any(isinstance(item, list) and len(item) > 1 and item[1] == row.prompt_id for item in queue.get('queue_pending', [])):
            raise HTTPException(409, 'This request is not confirmed queued. A running request cannot be safely interrupted individually through this integration.')
        await studio.json_request(row.configuration, 'POST', '/queue', payload={'delete': [row.prompt_id]})
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(503, 'Queued cancellation could not be confirmed. Refresh the existing receipt.') from None
    await session.execute(text('BEGIN IMMEDIATE'))
    await session.refresh(row)
    if row.status not in {'completed', 'failed', 'abandoned'}:
        row.status, row.message = 'cancel_requested', 'Removal requested for this queued ID only. It may have begun concurrently; refresh before assuming it stopped.'
        row.updated_at = datetime.now(timezone.utc)
    await session.commit()
    return receipt(row)


@router.post('/jobs/{job_id}/abandon')
async def abandon(job_id: str, confirmed: bool = Query(False), session=Depends(get_session)):
    if not confirmed:
        raise HTTPException(422, 'Explicitly confirm that abandoning tracking does not stop the external generator')
    await session.execute(text('BEGIN IMMEDIATE'))
    row = await job(session, job_id)
    if row.status in {'completed', 'failed'}:
        raise HTTPException(409, 'This receipt is already final')
    row.status, row.message = 'abandoned', 'Owner stopped tracking. Work may still run in the external local service; no completion or cancellation is certified.'
    row.updated_at = datetime.now(timezone.utc)
    await session.commit()
    return receipt(row)


@router.get('/jobs/{job_id}/artifact')
async def artifact(job_id: str, session=Depends(get_session)):
    row = await job(session, job_id)
    if row.status != 'completed' or not row.artifact:
        raise HTTPException(409, 'No verified saved artifact is available')
    root = studio.artifact_root()
    target = root/row.artifact['filename']
    if root.is_symlink() or target.is_symlink() or target.resolve().parent != root.resolve() or not target.is_file() or target.stat().st_size > 64*1024*1024:
        raise HTTPException(503, 'Saved artifact is unavailable or unsafe')
    data = target.read_bytes()
    if hashlib.sha256(data).hexdigest() != row.artifact['sha256']:
        raise HTTPException(503, 'Saved artifact integrity check failed')
    return Response(data, media_type=row.artifact['mime'], headers={'Content-Disposition': 'attachment; filename="javo-generated'+target.suffix+'"', 'Cache-Control': 'no-store'})


Country = Literal['IN', 'US', 'GB', 'CA', 'AU']


def trend_response(row):
    return {'id': row.id, 'country': row.country, 'source': row.source, 'items': row.items,
            'fetched_at': utc(row.fetched_at), 'scope': 'Google search trends; not social-platform analytics or guaranteed opportunities'} if row else None


@router.get('/trends')
async def trends(country: Country = 'IN', session=Depends(get_session)):
    row = await session.scalar(select(TrendSnapshot).where(TrendSnapshot.country == country).order_by(TrendSnapshot.fetched_at.desc()).limit(1))
    return trend_response(row)


@router.post('/trends/refresh')
async def refresh_trends(country: Country = 'IN', session=Depends(get_session)):
    recent = await session.scalar(select(TrendSnapshot).where(TrendSnapshot.country == country).order_by(TrendSnapshot.fetched_at.desc()).limit(1))
    if recent and datetime.now(timezone.utc)-utc(recent.fetched_at) < timedelta(seconds=60):
        raise HTTPException(429, 'Trend snapshots may be refreshed once per minute per country')
    source = 'https://trends.google.com/trending/rss?geo='+country
    try:
        async with httpx.AsyncClient(timeout=10, trust_env=False, follow_redirects=False) as client:
            async with client.stream('GET', source, headers={'Accept-Encoding': 'identity'}) as response:
                response.raise_for_status()
                if response.headers.get('content-encoding', 'identity').lower() not in {'identity', ''}:
                    raise ValueError('Compressed trend feed is unsupported')
                data = bytearray()
                async for chunk in response.aiter_bytes():
                    data.extend(chunk)
                    if len(data) > 1024*1024:
                        raise ValueError('Trend response too large')
        if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
            raise ValueError('Active XML declarations are unsupported')
        xml = ET.fromstring(data, forbid_dtd=True, forbid_entities=True, forbid_external=True)
        items = []
        for entry in xml.findall('./channel/item')[:50]:
            title = (entry.findtext('title') or '').strip()[:200]
            if not title:
                continue
            published = entry.findtext('pubDate')
            try:
                published = parsedate_to_datetime(published).astimezone(timezone.utc).isoformat() if published else None
            except (ValueError, TypeError):
                published = None
            traffic = next((child.text for child in entry if child.tag.endswith('}approx_traffic')), None)
            items.append({'title': title, 'published_at': published, 'approximate_traffic_label': (traffic or '')[:40] or None})
        if not items:
            raise ValueError('No supported trend items')
    except Exception:
        raise HTTPException(503, 'Official trend feed unavailable or invalid. The previous saved snapshot was retained.') from None
    row = TrendSnapshot(country=country, source=source, items=items, fetched_at=datetime.now(timezone.utc))
    session.add(row)
    await session.commit()
    return trend_response(row)
