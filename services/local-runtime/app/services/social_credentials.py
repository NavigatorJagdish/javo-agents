"""Verified encrypted staging before legacy SQL token fields are cleared."""

import asyncio
import logging
import time

from fastapi import HTTPException
from sqlalchemy import or_, select, text

from app import database as db
from app.core.account_credentials import credential_store, split_legacy_metadata
from app.core.local_identity import OWNER_IDS
from app.core.provider_store import VaultUnavailable
from app.models.account import AccountStatus, SocialAccount
from app.models.security import AuditAction, AuditLog

logger = logging.getLogger(__name__)


async def owned_account(account_id, session):
    account = (
        await session.execute(
            select(SocialAccount).where(
                SocialAccount.id == account_id, SocialAccount.user_id.in_(OWNER_IDS)
            )
        )
    ).scalar_one_or_none()
    if account is None:
        raise HTTPException(404, "Social account not found")
    return account


async def migrate_one(account_id, session):
    await session.execute(text("BEGIN IMMEDIATE"))
    account = await owned_account(account_id, session)
    cleaned_metadata, metadata_secrets = split_legacy_metadata(account.metadata_)
    if account.access_token is None and account.refresh_token is None and not metadata_secrets:
        await session.commit()
        return account
    if account.access_token or account.refresh_token or metadata_secrets:
        await asyncio.to_thread(
            credential_store().stage_legacy,
            account.id,
            account.access_token,
            account.refresh_token,
            account.token_expires_at,
            metadata_secrets,
        )
    # Only after an encrypted file has been atomically saved and reopened.
    account.access_token = None
    account.refresh_token = None
    account.metadata_ = cleaned_metadata
    account.status = AccountStatus.DISCONNECTED
    session.add(
        AuditLog(
            action=AuditAction.UPDATE,
            resource_type="account",
            resource_id=account.id,
            description="Legacy credentials protected; connection remains unverified",
        )
    )
    await session.commit()
    return account


async def migrate_legacy_credentials():
    """Bounded startup pass; inaccessible credentials stay intact and unavailable."""
    async with db.async_session_factory() as session:
        ids = list(
            (
                await session.execute(
                    select(SocialAccount.id)
                    .where(
                        SocialAccount.user_id.in_(OWNER_IDS),
                        or_(
                            SocialAccount.access_token.is_not(None),
                            SocialAccount.refresh_token.is_not(None),
                            SocialAccount.metadata_.is_not(None),
                        ),
                    )
                    .order_by(
                        or_(
                            SocialAccount.access_token.is_not(None),
                            SocialAccount.refresh_token.is_not(None),
                        ).desc(),
                        SocialAccount.id,
                    )
                    .limit(100)
                )
            )
            .scalars()
            .all()
        )
    deadline = time.monotonic() + 5
    for account_id in ids:
        if time.monotonic() >= deadline:
            break
        try:
            async with db.async_session_factory() as session:
                await migrate_one(account_id, session)
        except VaultUnavailable:
            # No credential, raw validation exception or private file path is logged.
            logger.warning(
                "Legacy social credential protection deferred; recover the original key/profile"
            )
