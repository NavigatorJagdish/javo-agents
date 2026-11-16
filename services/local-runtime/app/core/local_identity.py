"""Relational identity for the existing single-owner local token boundary."""

from sqlalchemy.dialects.sqlite import insert
from app.models.user import User, UserRole

LOCAL_OWNER = "local-owner"
OWNER_IDS = (LOCAL_OWNER, "default-user")  # Prior synthetic fallback, never another real user.


async def ensure_local_owner(session):
    await session.execute(
        insert(User)
        .values(
            id=LOCAL_OWNER,
            username=LOCAL_OWNER,
            email="local-owner@localhost.invalid",
            password_hash="!disabled-local-token-auth",
            role=UserRole.ADMIN,
            is_active=True,
        )
        .on_conflict_do_nothing(index_elements=[User.id])
    )
