"""Mock social connector for local testing and dry-run publishing."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.connectors.base import BaseConnector, ConnectorResult, PostPayload


class MockConnector(BaseConnector):
    """In-memory mock connector for deterministic testing without external API calls."""

    platform_name = "mock"

    def __init__(self, access_token: str = "mock-token", account_id: str = "mock-account", **kwargs: Any):
        super().__init__(access_token=access_token, account_id=account_id, **kwargs)
        self.published_posts: list[dict[str, Any]] = []
        self.replies: list[dict[str, Any]] = []

    async def verify_credentials(self) -> bool:
        return bool(self.access_token)

    async def publish_post(self, payload: PostPayload) -> ConnectorResult:
        post_id = f"mock_{uuid.uuid4().hex[:12]}"
        formatted = self.format_caption(payload)
        record = {
            "post_id": post_id,
            "caption": formatted,
            "media_type": payload.media_type,
            "media_path": payload.media_path,
            "published_at": datetime.now(timezone.utc).isoformat(),
        }
        self.published_posts.append(record)
        return ConnectorResult(
            success=True,
            platform=self.platform_name,
            post_id=post_id,
            url=f"https://mock.social/posts/{post_id}",
            raw=record,
        )

    async def fetch_analytics(self, since_days: int = 7) -> dict[str, Any]:
        return {
            "platform": self.platform_name,
            "since_days": since_days,
            "followers": 1250,
            "impressions": 15400,
            "engagement_rate": 4.8,
            "posts_count": len(self.published_posts),
        }

    async def fetch_comments(self, post_id: str, limit: int = 20) -> list[dict[str, Any]]:
        return [
            {
                "id": f"cmt_{post_id}_1",
                "author": "demo_follower",
                "text": "Great content! Looking forward to more.",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        ][:limit]

    async def reply_comment(self, comment_id: str, message: str) -> ConnectorResult:
        reply_id = f"reply_{uuid.uuid4().hex[:8]}"
        self.replies.append({"comment_id": comment_id, "reply_id": reply_id, "message": message})
        return ConnectorResult(
            success=True,
            platform=self.platform_name,
            post_id=reply_id,
            raw={"comment_id": comment_id, "message": message},
        )
