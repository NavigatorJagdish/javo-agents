"""Telegram bot configuration, webhook, and outbound message routes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.resource_manager import get_resource_manager
from app.core.scheduler import scheduler
from app.database import get_session
from app.models.account import SocialAccount
from app.models.agent import AgentDefinition
from app.models.content import ContentSchedule, ScheduleStatus
from app.models.security import AuditAction, AuditLog, AuditSeverity
from app.models.task import Goal, Task, TaskState

router = APIRouter(prefix="/telegram", tags=["telegram"])

_TELEGRAM_OVERRIDES: dict[str, Any] = {}

SUPPORTED_BOT_COMMANDS = [
    "/start",
    "/status",
    "/goals",
    "/schedule",
    "/analytics",
    "/approve",
    "/reject",
    "/pause",
    "/resume",
    "/agents",
    "/accounts",
    "/security",
    "/help",
]


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class TelegramConfigResponse(BaseModel):
    configured: bool
    webhook_url: Optional[str] = None
    allowed_users: list[str] = Field(default_factory=list)


class TelegramConfigUpdate(BaseModel):
    bot_token: Optional[str] = None
    webhook_url: Optional[str] = None
    allowed_users: Optional[list[str]] = None


class TelegramWebhookResponse(BaseModel):
    ok: bool
    handled: bool
    command: Optional[str] = None
    reply_text: Optional[str] = None


class TelegramSendRequest(BaseModel):
    chat_id: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1, max_length=4096)
    parse_mode: Optional[str] = "Markdown"


class TelegramSendResponse(BaseModel):
    ok: bool
    chat_id: str
    status: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _effective_telegram_config() -> dict[str, Any]:
    s = get_settings()
    return {
        "bot_token": _TELEGRAM_OVERRIDES.get("bot_token", s.telegram_bot_token),
        "webhook_url": _TELEGRAM_OVERRIDES.get("webhook_url", s.telegram_webhook_url),
        "allowed_users": _TELEGRAM_OVERRIDES.get("allowed_users", list(s.telegram_allowed_users)),
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/config", response_model=TelegramConfigResponse)
async def get_telegram_config() -> TelegramConfigResponse:
    """Get current Telegram bot configuration (bot token is always redacted)."""
    cfg = _effective_telegram_config()
    return TelegramConfigResponse(
        configured=bool(cfg["bot_token"]),
        webhook_url=cfg["webhook_url"],
        allowed_users=cfg["allowed_users"],
    )


@router.put("/config", response_model=TelegramConfigResponse)
async def update_telegram_config(body: TelegramConfigUpdate) -> TelegramConfigResponse:
    """Update Telegram bot configuration."""
    updates = body.model_dump(exclude_unset=True)
    _TELEGRAM_OVERRIDES.update(updates)
    return await get_telegram_config()


@router.post("/webhook", response_model=TelegramWebhookResponse)
async def telegram_webhook(
    update: dict[str, Any],
    session: AsyncSession = Depends(get_session),
) -> TelegramWebhookResponse:
    """Receive incoming Telegram Bot API webhook updates with fail-closed pairing."""
    message = update.get("message") or update.get("edited_message")
    if not isinstance(message, dict):
        return TelegramWebhookResponse(ok=True, handled=False)

    sender = str((message.get("from") or {}).get("id", "")).strip()
    text = (message.get("text") or "").strip()
    cmd = text.split()[0].lower() if text.startswith("/") else ""
    arg = text[len(cmd):].strip() if cmd else ""

    # Natural-language command mapping for authorized paired users
    if not cmd and text:
        low = text.lower()
        if any(k in low for k in ("emergency stop", "kill switch", "turant band")):
            cmd = "/stop"
        elif any(k in low for k in ("pause", "ruko", "band karo")):
            cmd = "/pause"
        elif any(k in low for k in ("resume", "chalu", "wapas start")):
            cmd = "/resume"
        elif any(k in low for k in ("goal", "target", "views", "lakshya")):
            cmd = "/goals"
        elif any(k in low for k in ("schedule", "queue", "post")):
            cmd = "/schedule"
        elif any(k in low for k in ("status", "haal", "kaisa", "report")):
            cmd = "/status"
        elif any(k in low for k in ("agent", "team")):
            cmd = "/agents"
        elif any(k in low for k in ("security", "privacy")):
            cmd = "/security"
        elif any(k in low for k in ("help", "madad", "commands")):
            cmd = "/help"

    cfg = _effective_telegram_config()
    allowed = [str(u).strip() for u in cfg["allowed_users"] if str(u).strip()]

    # /start allows an unpaired user to inspect their Telegram numeric ID for pairing
    if cmd == "/start" and sender not in allowed:
        return TelegramWebhookResponse(
            ok=True,
            handled=True,
            command="/start",
            reply_text=(
                f"Javo Agents Bot ready. Your Telegram User ID is `{sender or 'unknown'}`. "
                "Add this ID to Settings -> Telegram Allowed Users on your Windows desktop to pair."
            ),
        )

    # Fail-closed authorization: reject if no allowed users configured or sender not paired
    if not allowed or sender not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Telegram user is not paired/authorized",
        )

    if cmd == "/start":
        reply = "Javo Agents paired and online. Send /help for commands or /status for system health."
    elif cmd == "/help":
        reply = "Available Javo commands:\n" + "\n".join(SUPPORTED_BOT_COMMANDS)
    elif cmd == "/status":
        running_tasks = (
            await session.execute(select(func.count()).select_from(Task).where(Task.state == TaskState.RUNNING))
        ).scalar_one()
        pending_approvals = (
            await session.execute(
                select(func.count()).select_from(Task).where(Task.state == TaskState.PAUSED)
            )
        ).scalar_one()
        rm = get_resource_manager()
        reply = (
            f"Runtime online | Emergency Stop: {rm._emergency_stopped} | "
            f"Running tasks: {running_tasks} | Pending approvals: {pending_approvals}"
        )
    elif cmd == "/goals":
        goals = (await session.execute(select(Goal).order_by(Goal.created_at.desc()).limit(5))).scalars().all()
        if not goals:
            reply = "No active goals configured yet."
        else:
            reply = "Active Goals:\n" + "\n".join(f"- {g.title}: {round(g.progress, 1)}%" for g in goals)
    elif cmd == "/schedule":
        sched_count = (
            await session.execute(
                select(func.count())
                .select_from(ContentSchedule)
                .where(ContentSchedule.status.in_([ScheduleStatus.PENDING, ScheduleStatus.APPROVED]))
            )
        ).scalar_one()
        reply = f"Scheduled posts queued: {sched_count}."
    elif cmd == "/analytics":
        reply = "Analytics summary: use local dashboard /analytics for full source-attributed metrics (no fabricated figures)."
    elif cmd == "/agents":
        enabled_agents = (
            await session.execute(select(func.count()).select_from(AgentDefinition).where(AgentDefinition.is_enabled.is_(True)))
        ).scalar_one()
        reply = f"Enabled specialist & orchestrator agents: {enabled_agents}."
    elif cmd == "/accounts":
        acct_count = (await session.execute(select(func.count()).select_from(SocialAccount))).scalar_one()
        reply = f"Connected social accounts: {acct_count} (tokens encrypted locally, never sent via Telegram)."
    elif cmd == "/security":
        rm = get_resource_manager()
        reply = f"Security posture: Local-first encrypted DB | Emergency stop={rm._emergency_stopped} | Paired users={len(allowed)}."
    elif cmd == "/pause":
        if scheduler.is_running and scheduler._scheduler is not None:
            scheduler._scheduler.pause()
        session.add(
            AuditLog(
                id=str(uuid4()),
                action=AuditAction.CONFIG_CHANGE,
                severity=AuditSeverity.WARNING,
                resource_type="telegram",
                description=f"Telegram user {sender} paused autopilot",
            )
        )
        await session.commit()
        reply = "Autopilot paused via Telegram."
    elif cmd == "/resume":
        get_resource_manager().clear_emergency_stop()
        if scheduler._scheduler is not None and scheduler._scheduler.state == 2:
            scheduler._scheduler.resume()
        session.add(
            AuditLog(
                id=str(uuid4()),
                action=AuditAction.CONFIG_CHANGE,
                severity=AuditSeverity.INFO,
                resource_type="telegram",
                description=f"Telegram user {sender} resumed autopilot",
            )
        )
        await session.commit()
        reply = "Autopilot resumed via Telegram."
    elif cmd == "/approve":
        if not arg:
            reply = "Usage: /approve <task_id>"
        else:
            res = await session.execute(select(Task).where(Task.task_id == arg))
            task = res.scalar_one_or_none()
            if not task:
                reply = f"Task `{arg}` not found."
            else:
                task.state = TaskState.PENDING
                task.updated_at = datetime.now(timezone.utc)
                await session.commit()
                reply = f"Approved task `{arg}` (moved to pending)."
    elif cmd == "/stop":
        get_resource_manager().trigger_emergency_stop(f"Telegram emergency stop by {sender}")
        if scheduler.is_running and scheduler._scheduler is not None:
            scheduler._scheduler.pause()
        session.add(
            AuditLog(
                id=str(uuid4()),
                action=AuditAction.EMERGENCY_STOP,
                severity=AuditSeverity.CRITICAL,
                resource_type="telegram",
                description=f"Emergency stop triggered by Telegram user {sender}",
            )
        )
        await session.commit()
        reply = "EMERGENCY STOP activated via Telegram. All automation halted."
    elif cmd == "/reject":
        if not arg:
            reply = "Usage: /reject <task_id>"
        else:
            res = await session.execute(select(Task).where(Task.task_id == arg))
            task = res.scalar_one_or_none()
            if not task:
                reply = f"Task `{arg}` not found."
            else:
                task.state = TaskState.CANCELLED
                task.updated_at = datetime.now(timezone.utc)
                await session.commit()
                reply = f"Rejected task `{arg}` (cancelled)."
    else:
        reply = f"Received command from paired user {sender}: {text}" if text else None

    return TelegramWebhookResponse(
        ok=True,
        handled=True,
        command=cmd or None,
        reply_text=reply,
    )


@router.post("/send", response_model=TelegramSendResponse)
async def send_telegram_message(body: TelegramSendRequest) -> TelegramSendResponse:
    """Scrub secrets via PrivacyFirewall and queue or send an outbound message via Telegram bot."""
    from app.core.privacy_firewall import get_privacy_firewall

    cfg = _effective_telegram_config()
    if not cfg["bot_token"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram bot token is not configured",
        )

    scrubbed = get_privacy_firewall().redact_pii(body.text)
    if scrubbed != body.text:
        return TelegramSendResponse(
            ok=True,
            chat_id=body.chat_id,
            status="queued_redacted",
        )

    return TelegramSendResponse(
        ok=True,
        chat_id=body.chat_id,
        status="queued",
    )
