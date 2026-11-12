"""Facebook Pages connector using Meta Graph API."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.connectors.base import BaseConnector, ConnectorResult, PostPayload

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"


class FacebookConnector(BaseConnector):
    """Connector for Facebook Pages via Meta Graph API."""

    platform_name = "facebook"

    def __init__(self, access_token: str = "", account_id: str = "", page_id: str = "", **kwargs: Any):
        super().__init__(access_token=access_token, account_id=account_id, **kwargs)
        self.page_id = page_id or account_id

    async def verify_credentials(self) -> bool:
        if not self.access_token or not self.page_id:
            return False
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(
                    f"{GRAPH_API_BASE}/{self.page_id}",
                    params={"fields": "id,name", "access_token": self.access_token},
                )
                return res.status_code == 200
        except Exception as exc:
            logger.warning("Facebook credential verification failed: %s", exc)
            return False

    async def publish_post(self, payload: PostPayload) -> ConnectorResult:
        if not self.access_token or not self.page_id:
            return ConnectorResult(
                success=False,
                platform=self.platform_name,
                error="Missing Facebook page_id or access_token",
            )

        message = self.format_caption(payload)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if payload.media_type == "image" and payload.media_url:
                    endpoint = f"{GRAPH_API_BASE}/{self.page_id}/photos"
                    data = {
                        "url": payload.media_url,
                        "caption": message,
                        "access_token": self.access_token,
                    }
                    res = await client.post(endpoint, data=data)
                elif payload.media_type == "video" and payload.media_url:
                    endpoint = f"{GRAPH_API_BASE}/{self.page_id}/videos"
                    data = {
                        "file_url": payload.media_url,
                        "description": message,
                        "access_token": self.access_token,
                    }
                    res = await client.post(endpoint, data=data)
                else:
                    endpoint = f"{GRAPH_API_BASE}/{self.page_id}/feed"
                    data = {
                        "message": message,
                        "access_token": self.access_token,
                    }
                    res = await client.post(endpoint, data=data)

                res.raise_for_status()
                body = res.json()
                post_id = body.get("post_id") or body.get("id")
                return ConnectorResult(
                    success=True,
                    platform=self.platform_name,
                    post_id=post_id,
                    url=f"https://www.facebook.com/{post_id}" if post_id else None,
                    raw=body,
                )
        except Exception as exc:
            logger.error("Facebook publish_post failed: %s", exc)
            return ConnectorResult(
                success=False,
                platform=self.platform_name,
                error=str(exc),
            )

    async def fetch_analytics(self, since_days: int = 7) -> dict[str, Any]:
        if not self.access_token or not self.page_id:
            return {"platform": self.platform_name, "error": "Missing credentials"}
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.get(
                    f"{GRAPH_API_BASE}/{self.page_id}/insights",
                    params={
                        "metric": "page_impressions,page_post_engagements,page_fans",
                        "period": "day",
                        "access_token": self.access_token,
                    },
                )
                res.raise_for_status()
                return {"platform": self.platform_name, "data": res.json().get("data", [])}
        except Exception as exc:
            logger.warning("Facebook fetch_analytics error: %s", exc)
            return {"platform": self.platform_name, "error": str(exc)}

    async def fetch_comments(self, post_id: str, limit: int = 20) -> list[dict[str, Any]]:
        if not self.access_token:
            return []
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(
                    f"{GRAPH_API_BASE}/{post_id}/comments",
                    params={"limit": limit, "access_token": self.access_token},
                )
                res.raise_for_status()
                return res.json().get("data", [])
        except Exception as exc:
            logger.warning("Facebook fetch_comments error: %s", exc)
            return []

    async def reply_comment(self, comment_id: str, message: str) -> ConnectorResult:
        if not self.access_token:
            return ConnectorResult(success=False, platform=self.platform_name, error="Missing token")
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    f"{GRAPH_API_BASE}/{comment_id}/comments",
                    data={"message": message, "access_token": self.access_token},
                )
                res.raise_for_status()
                body = res.json()
                return ConnectorResult(
                    success=True,
                    platform=self.platform_name,
                    post_id=body.get("id"),
                    raw=body,
                )
        except Exception as exc:
            return ConnectorResult(success=False, platform=self.platform_name, error=str(exc))
