"""Instagram Professional connector using Instagram Graph API."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.connectors.base import BaseConnector, ConnectorResult, PostPayload

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"


class InstagramConnector(BaseConnector):
    """Connector for Instagram Business/Creator accounts via Graph API."""

    platform_name = "instagram"

    def __init__(self, access_token: str = "", account_id: str = "", ig_user_id: str = "", **kwargs: Any):
        super().__init__(access_token=access_token, account_id=account_id, **kwargs)
        self.ig_user_id = ig_user_id or account_id

    async def verify_credentials(self) -> bool:
        if not self.access_token or not self.ig_user_id:
            return False
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(
                    f"{GRAPH_API_BASE}/{self.ig_user_id}",
                    params={"fields": "id,username", "access_token": self.access_token},
                )
                return res.status_code == 200
        except Exception as exc:
            logger.warning("Instagram credential verification failed: %s", exc)
            return False

    async def publish_post(self, payload: PostPayload) -> ConnectorResult:
        if not self.access_token or not self.ig_user_id:
            return ConnectorResult(
                success=False,
                platform=self.platform_name,
                error="Missing Instagram user ID or access token",
            )
        if not payload.media_url:
            return ConnectorResult(
                success=False,
                platform=self.platform_name,
                error="Instagram requires a public media_url to create a media container",
            )

        caption = self.format_caption(payload)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Step 1: Create media container
                container_params: dict[str, Any] = {
                    "caption": caption,
                    "access_token": self.access_token,
                }
                if payload.media_type == "video":
                    container_params["media_type"] = "REELS"
                    container_params["video_url"] = payload.media_url
                else:
                    container_params["image_url"] = payload.media_url

                c_res = await client.post(
                    f"{GRAPH_API_BASE}/{self.ig_user_id}/media",
                    data=container_params,
                )
                c_res.raise_for_status()
                creation_id = c_res.json().get("id")

                # Step 2: Publish container
                p_res = await client.post(
                    f"{GRAPH_API_BASE}/{self.ig_user_id}/media_publish",
                    data={"creation_id": creation_id, "access_token": self.access_token},
                )
                p_res.raise_for_status()
                body = p_res.json()
                post_id = body.get("id")
                return ConnectorResult(
                    success=True,
                    platform=self.platform_name,
                    post_id=post_id,
                    url=f"https://www.instagram.com/p/{post_id}/" if post_id else None,
                    raw=body,
                )
        except Exception as exc:
            logger.error("Instagram publish_post failed: %s", exc)
            return ConnectorResult(success=False, platform=self.platform_name, error=str(exc))

    async def fetch_analytics(self, since_days: int = 7) -> dict[str, Any]:
        if not self.access_token or not self.ig_user_id:
            return {"platform": self.platform_name, "error": "Missing credentials"}
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.get(
                    f"{GRAPH_API_BASE}/{self.ig_user_id}/insights",
                    params={
                        "metric": "impressions,reach,profile_views",
                        "period": "day",
                        "access_token": self.access_token,
                    },
                )
                res.raise_for_status()
                return {"platform": self.platform_name, "data": res.json().get("data", [])}
        except Exception as exc:
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
        except Exception:
            return []

    async def reply_comment(self, comment_id: str, message: str) -> ConnectorResult:
        if not self.access_token:
            return ConnectorResult(success=False, platform=self.platform_name, error="Missing token")
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    f"{GRAPH_API_BASE}/{comment_id}/replies",
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
