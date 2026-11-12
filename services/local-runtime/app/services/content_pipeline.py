"""Local-folder Content Factory pipeline and approval-gated connector dispatch."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import get_all_agents
from app.connectors.base import PostPayload
from app.connectors.facebook import FacebookConnector
from app.connectors.instagram import InstagramConnector
from app.connectors.mock import MockConnector
from app.connectors.youtube import YouTubeConnector
from app.core.privacy_firewall import get_privacy_firewall
from app.models.account import AccountStatus, Platform, SocialAccount
from app.models.content import (
    AssetStatus,
    AssetType,
    ContentAsset,
    ContentSchedule,
    MediaMetadata,
    PublishRecord,
    PublishStatus,
    ScheduleStatus,
)
from app.models.user import User
from app.services.media_processor import MediaProcessor

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".ogg", ".flac"}
TEXT_EXTS = {".txt", ".md"}
SUPPORTED_EXTS = IMAGE_EXTS | VIDEO_EXTS | AUDIO_EXTS | TEXT_EXTS


def _classify_asset_type(path: Path) -> AssetType:
    ext = path.suffix.lower()
    if ext in IMAGE_EXTS:
        return AssetType.IMAGE
    if ext in VIDEO_EXTS:
        return AssetType.VIDEO
    if ext in AUDIO_EXTS:
        return AssetType.AUDIO
    return AssetType.TEXT


async def _ensure_default_user(session: AsyncSession, preferred_user_id: Optional[str]) -> User:
    if preferred_user_id:
        res = await session.execute(select(User).where(User.id == preferred_user_id))
        u = res.scalar_one_or_none()
        if u is not None:
            return u
    res = await session.execute(select(User).limit(1))
    u = res.scalar_one_or_none()
    if u is not None:
        return u
    u = User(
        id=preferred_user_id or str(uuid4()),
        username="local_owner",
        email="owner@localhost.localdomain",
        password_hash="local-only-disabled-login",
    )
    session.add(u)
    await session.flush()
    return u


async def run_content_pipeline(
    session: AsyncSession,
    folder_path: str,
    platform: str = "instagram",
    account_id: Optional[str] = None,
    user_id: Optional[str] = None,
    topic: Optional[str] = None,
    auto_schedule: bool = True,
    approval_required: bool = True,
    limit: int = 20,
) -> dict[str, Any]:
    """Scan a local folder, probe media, draft captions/hashtags, inspect quality, and queue schedules."""
    root = Path(folder_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Content folder does not exist or is not a directory: {folder_path}",
        )

    owner = await _ensure_default_user(session, user_id)

    resolved_account: Optional[SocialAccount] = None
    if account_id:
        acc_res = await session.execute(select(SocialAccount).where(SocialAccount.id == account_id))
        resolved_account = acc_res.scalar_one_or_none()
        if resolved_account is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Account '{account_id}' not found")
    elif auto_schedule:
        try:
            plat_enum = Platform(platform.lower())
        except ValueError:
            plat_enum = Platform.INSTAGRAM
        acc_res = await session.execute(select(SocialAccount).where(SocialAccount.platform == plat_enum).limit(1))
        resolved_account = acc_res.scalar_one_or_none()
        if resolved_account is None:
            resolved_account = SocialAccount(
                id=str(uuid4()),
                user_id=owner.id,
                platform=plat_enum,
                username=f"local_{plat_enum.value}_drafts",
                display_name=f"Local {plat_enum.value.title()} Draft Queue",
                status=AccountStatus.DISCONNECTED,
            )
            session.add(resolved_account)
            await session.flush()

    files = sorted(
        p for p in root.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS
    )[:max(1, min(limit, 50))]

    agents = get_all_agents()
    factory_agent = agents.get("content_factory") or agents.get("content_creator")
    quality_agent = agents.get("quality_inspector")
    processor = MediaProcessor()

    processed_assets: list[dict[str, Any]] = []
    scheduled_items: list[dict[str, Any]] = []

    for idx, file_path in enumerate(files):
        asset_type = _classify_asset_type(file_path)
        media_info: dict[str, Any] = {"file_size": file_path.stat().st_size, "extension": file_path.suffix.lower()}

        if asset_type in (AssetType.IMAGE, AssetType.VIDEO, AssetType.AUDIO):
            try:
                media_info.update(processor.probe_media(file_path))
            except Exception as exc:
                media_info["probe_warning"] = str(exc)
        elif asset_type == AssetType.TEXT:
            media_info["text_preview"] = file_path.read_text(encoding="utf-8", errors="ignore")[:500]

        stem_title = file_path.stem.replace("_", " ").replace("-", " ").strip().title() or file_path.name
        prompt_topic = topic or stem_title

        draft_caption = f"{stem_title} — prepared locally by Javo Agents."
        draft_hashtags = ["#JavoAgents", f"#{platform.lower()}", "#Automation"]
        factory_meta: dict[str, Any] = {}
        if factory_agent is not None:
            factory_res = await factory_agent.run(
                {
                    "topic": prompt_topic,
                    "title": stem_title,
                    "platform": platform.lower(),
                    "media_path": str(file_path),
                    "media_type": asset_type.value,
                    "text_preview": media_info.get("text_preview", ""),
                }
            )
            factory_meta = factory_res
            if isinstance(factory_res.get("caption"), str) and factory_res["caption"].strip():
                draft_caption = factory_res["caption"].strip()
            elif isinstance(factory_res.get("draft"), str) and factory_res["draft"].strip():
                draft_caption = factory_res["draft"].strip()
            if isinstance(factory_res.get("hashtags"), list) and factory_res["hashtags"]:
                draft_hashtags = [str(h) for h in factory_res["hashtags"][:10]]

        quality_report: dict[str, Any] = {"passed": True, "score": 0.85}
        if quality_agent is not None:
            quality_report = await quality_agent.run(
                {
                    "title": stem_title,
                    "content": draft_caption,
                    "platform": platform.lower(),
                    "hashtags": draft_hashtags,
                }
            )

        asset = ContentAsset(
            id=str(uuid4()),
            user_id=owner.id,
            title=stem_title,
            description=f"Imported from local folder {root}",
            asset_type=asset_type,
            status=AssetStatus.READY,
            file_path=str(file_path),
            content_text=draft_caption,
            hashtags=draft_hashtags,
            ai_generated=True,
            ai_metadata={"factory": factory_meta, "quality": quality_report, "platform": platform.lower()},
        )
        session.add(asset)
        await session.flush()

        meta = MediaMetadata(
            id=str(uuid4()),
            asset_id=asset.id,
            mime_type=media_info.get("mime_type"),
            file_size=media_info.get("file_size"),
            width=media_info.get("width"),
            height=media_info.get("height"),
            duration_seconds=media_info.get("duration_seconds"),
            bitrate=media_info.get("bitrate"),
            codec=media_info.get("codec"),
            ai_analysis=media_info,
        )
        session.add(meta)

        schedule_id: Optional[str] = None
        if auto_schedule and resolved_account is not None:
            sched = ContentSchedule(
                id=str(uuid4()),
                asset_id=asset.id,
                account_id=resolved_account.id,
                scheduled_at=datetime.now(timezone.utc) + timedelta(hours=idx + 1),
                status=ScheduleStatus.PENDING if approval_required else ScheduleStatus.APPROVED,
                caption=draft_caption,
                platform_options={"platform": platform.lower(), "hashtags": draft_hashtags, "requires_approval": approval_required},
            )
            session.add(sched)
            asset.status = AssetStatus.SCHEDULED
            schedule_id = sched.id
            scheduled_items.append(
                {
                    "schedule_id": sched.id,
                    "asset_id": asset.id,
                    "status": sched.status.value,
                    "requires_approval": approval_required,
                }
            )

        processed_assets.append(
            {
                "asset_id": asset.id,
                "title": asset.title,
                "asset_type": asset.asset_type.value,
                "file_path": str(file_path),
                "caption": draft_caption,
                "hashtags": draft_hashtags,
                "quality": quality_report,
                "schedule_id": schedule_id,
            }
        )

    await session.commit()
    return {
        "folder_path": str(root),
        "platform": platform.lower(),
        "scanned_count": len(files),
        "processed_assets": processed_assets,
        "scheduled_items": scheduled_items,
        "requires_approval": approval_required,
    }


async def approve_and_dispatch_schedule(
    session: AsyncSession,
    schedule_id: str,
    approved_by: str = "owner",
    publish_now: bool = False,
    allow_mock: bool = True,
) -> dict[str, Any]:
    """Approve a pending schedule and optionally dispatch it via live connector or explicit MockConnector."""
    sched_res = await session.execute(select(ContentSchedule).where(ContentSchedule.id == schedule_id))
    sched = sched_res.scalar_one_or_none()
    if sched is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Schedule '{schedule_id}' not found")

    asset_res = await session.execute(select(ContentAsset).where(ContentAsset.id == sched.asset_id))
    asset = asset_res.scalar_one_or_none()
    acc_res = await session.execute(select(SocialAccount).where(SocialAccount.id == sched.account_id))
    account = acc_res.scalar_one_or_none()

    sched.status = ScheduleStatus.APPROVED
    sched.approved_by = approved_by
    sched.approved_at = datetime.now(timezone.utc)

    if not publish_now:
        await session.commit()
        return {
            "schedule_id": sched.id,
            "status": ScheduleStatus.APPROVED.value,
            "approved_by": approved_by,
            "published": False,
            "mode": "approved_only",
        }

    # Compliance & PrivacyFirewall check before outbound publish
    caption = sched.caption or (asset.content_text if asset else "") or ""
    firewall = get_privacy_firewall()
    level, findings = firewall.classify_text(caption)
    if str(getattr(level, "value", level)) == "restricted":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Blocked by PrivacyFirewall: restricted secrets detected ({', '.join(findings)})",
        )
    caption = firewall.redact_pii(caption)

    compliance_agent = get_all_agents().get("compliance_checker")
    if compliance_agent is not None:
        comp_res = await compliance_agent.run(
            {
                "content": caption,
                "platform": account.platform.value if account else "instagram",
                "approved_by": approved_by,
            }
        )
        if comp_res.get("approved") is False:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Blocked by ComplianceAgent: {comp_res.get('reason', 'Policy check failed')}",
            )

    platform_enum = account.platform if account else Platform.INSTAGRAM
    has_live_oauth = bool(account and account.access_token and account.status == AccountStatus.CONNECTED)

    mode = "mock"
    connector: Any = MockConnector(
        access_token="",
        account_id=account.id if account else "local_mock",
    )
    if has_live_oauth and not allow_mock:
        tok = account.access_token or ""
        ext_id = account.platform_user_id or ""
        if platform_enum == Platform.FACEBOOK:
            connector = FacebookConnector(access_token=tok, account_id=ext_id)
        elif platform_enum == Platform.INSTAGRAM:
            connector = InstagramConnector(access_token=tok, account_id=ext_id)
        elif platform_enum == Platform.YOUTUBE:
            connector = YouTubeConnector(access_token=tok, account_id=ext_id)
        mode = "live"

    payload = PostPayload(
        caption=caption,
        hashtags=list(asset.hashtags or []) if asset else [],
        media_path=asset.file_path if asset else None,
        media_type=asset.asset_type.value if asset else "text",
        title=asset.title if asset else None,
        extra=dict(sched.platform_options or {}),
    )
    pub_res = await connector.publish_post(payload)

    record = PublishRecord(
        id=str(uuid4()),
        schedule_id=sched.id,
        platform=platform_enum,
        platform_post_id=pub_res.post_id,
        platform_url=pub_res.url,
        status=PublishStatus.SUCCESS if pub_res.success else PublishStatus.FAILED,
        error_message=pub_res.error,
        engagement_data={"mode": mode, "raw": pub_res.raw},
    )
    session.add(record)

    if pub_res.success:
        sched.status = ScheduleStatus.PUBLISHED
        if asset is not None:
            asset.status = AssetStatus.PUBLISHED
    else:
        sched.status = ScheduleStatus.FAILED

    await session.commit()
    return {
        "schedule_id": sched.id,
        "status": sched.status.value,
        "approved_by": approved_by,
        "published": pub_res.success,
        "mode": mode,
        "platform": platform_enum.value,
        "platform_post_id": pub_res.post_id,
        "platform_url": pub_res.url,
        "error": pub_res.error,
    }
