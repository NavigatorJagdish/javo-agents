"""Single-owner local control boundary; device-scoped credentials are separate."""

import secrets

from fastapi import HTTPException, Request

from app.config import get_settings


def is_valid_owner_token(header: str | None) -> bool:
    configured = get_settings().owner_access_token
    if not configured or len(configured.get_secret_value()) < 32:
        return False
    scheme, _, token = (header or "").partition(" ")
    return scheme.lower() == "bearer" and secrets.compare_digest(
        token.encode("utf-8"), configured.get_secret_value().encode("utf-8")
    )


async def require_local_owner(request: Request) -> dict:
    configured = get_settings().owner_access_token
    if not configured or len(configured.get_secret_value()) < 32:
        raise HTTPException(503, "Local access is not configured. Start with the secure launcher.")
    if not is_valid_owner_token(request.headers.get("authorization")):
        raise HTTPException(401, "Local authorization required", headers={"WWW-Authenticate": "Bearer"})
    return {"user_id": "local-owner", "role": "admin"}
