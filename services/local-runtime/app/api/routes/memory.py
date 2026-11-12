"""Smart Memory inspection, editing, preference management, export, and deletion routes."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import get_all_agents
from app.core.privacy_firewall import get_privacy_firewall
from app.core.security import require_auth
from app.database import get_session
from app.models.memory import Importance, MemoryEntry, MemoryType, Preference
from app.models.user import User

router = APIRouter(dependencies=[Depends(require_auth)])


class MemoryCreateRequest(BaseModel):
    key: str = Field(..., min_length=1, max_length=256)
    content: str = Field(..., min_length=1)
    memory_type: MemoryType = MemoryType.FACT
    importance: Importance = Importance.MEDIUM
    tags: Optional[list[str]] = None
    source_agent: Optional[str] = "user"
    user_id: Optional[str] = None


class MemoryUpdateRequest(BaseModel):
    content: Optional[str] = None
    memory_type: Optional[MemoryType] = None
    importance: Optional[Importance] = None
    tags: Optional[list[str]] = None


class PreferenceUpsertRequest(BaseModel):
    key: str = Field(..., min_length=1, max_length=128)
    value: Any
    category: str = Field(default="general", max_length=64)
    user_id: Optional[str] = None


async def _resolve_user_id(session: AsyncSession, preferred_user_id: Optional[str]) -> str:
    if preferred_user_id:
        res = await session.execute(select(User).where(User.id == preferred_user_id))
        u = res.scalar_one_or_none()
        if u is not None:
            return u.id
    res = await session.execute(select(User).limit(1))
    u = res.scalar_one_or_none()
    if u is not None:
        return u.id
    u = User(
        id=preferred_user_id or str(uuid4()),
        username="local_owner",
        email="owner@localhost.localdomain",
        password_hash="local-only-disabled-login",
    )
    session.add(u)
    await session.flush()
    return u.id


@router.get("/")
async def list_memories(
    memory_type: Optional[MemoryType] = None,
    q: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """List persisted Smart Memory entries and active user preferences."""
    stmt = select(MemoryEntry).order_by(MemoryEntry.updated_at.desc()).limit(limit)
    if memory_type is not None:
        stmt = (
            select(MemoryEntry)
            .where(MemoryEntry.memory_type == memory_type)
            .order_by(MemoryEntry.updated_at.desc())
            .limit(limit)
        )
    res = await session.execute(stmt)
    entries = list(res.scalars().all())
    if q:
        q_low = q.lower()
        entries = [e for e in entries if q_low in e.key.lower() or q_low in e.content.lower()]

    pref_res = await session.execute(select(Preference).order_by(Preference.key))
    prefs = list(pref_res.scalars().all())

    return {
        "entries": [
            {
                "id": e.id,
                "key": e.key,
                "memory_type": e.memory_type.value if isinstance(e.memory_type, MemoryType) else str(e.memory_type),
                "content": e.content,
                "importance": e.importance.value if isinstance(e.importance, Importance) else str(e.importance),
                "tags": (e.context or {}).get("tags", []),
                "source_agent": e.source_agent,
                "updated_at": e.updated_at.isoformat() if e.updated_at else None,
            }
            for e in entries
        ],
        "preferences": [
            {
                "id": p.id,
                "key": p.key,
                "value": p.value,
                "category": p.category,
                "is_explicit": p.is_explicit,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            }
            for p in prefs
        ],
        "total_entries": len(entries),
        "total_preferences": len(prefs),
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_memory(
    body: MemoryCreateRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Persist a new Smart Memory entry in SQLite and sync SmartMemoryAgent cache."""
    uid = await _resolve_user_id(session, body.user_id)
    entry = MemoryEntry(
        id=str(uuid4()),
        user_id=uid,
        memory_type=body.memory_type,
        key=body.key,
        content=body.content,
        importance=body.importance,
        source_agent=body.source_agent,
        context={"tags": body.tags or []},
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)

    smart_agent = get_all_agents().get("smart_memory")
    if smart_agent is not None:
        await smart_agent.run({"action": "store", "key": body.key, "value": body.content, "category": body.memory_type.value})

    return {
        "id": entry.id,
        "key": entry.key,
        "memory_type": entry.memory_type.value,
        "content": entry.content,
        "importance": entry.importance.value,
        "tags": (entry.context or {}).get("tags", []),
    }


@router.patch("/{entry_id}")
async def update_memory(
    entry_id: str,
    body: MemoryUpdateRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Edit an existing Smart Memory entry."""
    res = await session.execute(select(MemoryEntry).where(MemoryEntry.id == entry_id))
    entry = res.scalar_one_or_none()
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Memory entry '{entry_id}' not found")

    if body.content is not None:
        entry.content = body.content
    if body.memory_type is not None:
        entry.memory_type = body.memory_type
    if body.importance is not None:
        entry.importance = body.importance
    if body.tags is not None:
        ctx = dict(entry.context or {})
        ctx["tags"] = body.tags
        entry.context = ctx

    await session.commit()
    await session.refresh(entry)
    return {
        "id": entry.id,
        "key": entry.key,
        "memory_type": entry.memory_type.value if isinstance(entry.memory_type, MemoryType) else str(entry.memory_type),
        "content": entry.content,
        "importance": entry.importance.value if isinstance(entry.importance, Importance) else str(entry.importance),
        "tags": (entry.context or {}).get("tags", []),
    }


@router.delete("/{entry_id}")
async def delete_memory(
    entry_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Delete a Smart Memory entry by ID."""
    res = await session.execute(select(MemoryEntry).where(MemoryEntry.id == entry_id))
    entry = res.scalar_one_or_none()
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Memory entry '{entry_id}' not found")

    await session.delete(entry)
    await session.commit()
    return {"deleted": True, "id": entry_id}


@router.post("/preferences")
async def upsert_preference(
    body: PreferenceUpsertRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Create or update a persisted user preference."""
    uid = await _resolve_user_id(session, body.user_id)
    val_str = body.value if isinstance(body.value, str) else json.dumps(body.value)
    res = await session.execute(
        select(Preference).where(
            Preference.user_id == uid,
            Preference.category == body.category,
            Preference.key == body.key,
        )
    )
    pref = res.scalar_one_or_none()
    if pref is None:
        pref = Preference(
            id=str(uuid4()),
            user_id=uid,
            category=body.category,
            key=body.key,
            value=val_str,
            is_explicit=True,
            confidence=1.0,
        )
        session.add(pref)
    else:
        pref.value = val_str
        pref.is_explicit = True
    await session.commit()
    await session.refresh(pref)

    smart_agent = get_all_agents().get("smart_memory")
    if smart_agent is not None:
        await smart_agent.run({"action": "set_preference", "key": body.key, "value": val_str})

    return {"id": pref.id, "key": pref.key, "value": pref.value, "category": pref.category}


@router.get("/export")
async def export_memories(session: AsyncSession = Depends(get_session)) -> dict[str, Any]:
    """Export all Smart Memory entries and preferences with secret redaction."""
    firewall = get_privacy_firewall()
    res = await session.execute(select(MemoryEntry).order_by(MemoryEntry.created_at))
    entries = list(res.scalars().all())
    pref_res = await session.execute(select(Preference).order_by(Preference.key))
    prefs = list(pref_res.scalars().all())

    return {
        "schema_version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "entries": [
            {
                "id": e.id,
                "key": e.key,
                "memory_type": e.memory_type.value if isinstance(e.memory_type, MemoryType) else str(e.memory_type),
                "content": firewall.redact_pii(e.content),
                "importance": e.importance.value if isinstance(e.importance, Importance) else str(e.importance),
                "tags": (e.context or {}).get("tags", []),
                "source_agent": e.source_agent,
            }
            for e in entries
        ],
        "preferences": [
            {
                "id": p.id,
                "key": p.key,
                "category": p.category,
                "value": firewall.redact_pii(p.value),
            }
            for p in prefs
        ],
    }
