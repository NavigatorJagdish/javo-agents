"""YouTube Data API v3 connector."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import httpx

from app.connectors.base import BaseConnector, ConnectorResult, PostPayload

logger = logging.getLogger(__name__)

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
YOUTUBE_UPLOAD_BASE = "https://www.googleapis.com/upload/youtube/v3"


class YouTubeConnector(BaseConnector):
    """Connector for YouTube channels via YouTube Data API v3."""

    platform_name = "youtube"

    async def verify_credentials(self) -> bool:
        if not self.access_token:
            return False
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(
                    f"{YOUTUBE_API_BASE}/channels",
                    params={"part": "snippet", "mine": "true"},
                    headers={"Authorization": f"Bearer {self.access_token}"},
                )
                return res.status_code == 200
        except Exception as exc:
            logger.warning("YouTube credential verification failed: %s", exc)
            return False

    async def publish_post(self, payload: PostPayload) -> ConnectorResult:
        if not self.access_token:
            return ConnectorResult(
                success=False,
                platform=self.platform_name,
                error="Missing YouTube OAuth access token",
            )
        if not payload.media_path or not Path(payload.media_path).exists():
            return ConnectorResult(
                success=False,
                platform=self.platform_name,
                error="YouTube upload requires a valid local video file media_path",
            )

        metadata = {
            "snippet": {
                "title": payload.title or payload.caption[:95] or "Javo Agents Upload",
                "description": self.format_caption(payload),
                "tags": [t.lstrip("#") for t in payload.hashtags],
                "categoryId": payload.extra.get("category_id", "22"),
            },
            "status": {
                "privacyStatus": payload.extra.get("privacy_status", "private"),
            },
        }

        try:
            video_bytes = Path(payload.media_path).read_bytes()
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json; charset=UTF-8",
                "X-Upload-Content-Length": str(len(video_bytes)),
                "X-Upload-Content-Type": "video/*",
            }
            async with httpx.AsyncClient(timeout=120.0) as client:
                init_res = await client.post(
                    f"{YOUTUBE_UPLOAD_BASE}/videos",
                    params={"uploadType": "resumable", "part": "snippet,status"},
                    headers=headers,
                    json=metadata,
                )
                init_res.raise_for_status()
                upload_url = init_res.headers.get("Location")
                if not upload_url:
                    raise RuntimeError("Missing resumable upload Location header from YouTube")

                up_res = await client.put(
                    upload_url,
                    headers={"Content-Type": "video/*"},
                    content=video_bytes,
                )
                up_res.raise_for_status()
                body = up_res.json()
                video_id = body.get("id")
                return ConnectorResult(
                    success=True,
                    platform=self.platform_name,
                    post_id=video_id,
                    url=f"https://www.youtube.com/watch?v={video_id}" if video_id else None,
                    raw=body,
                )
        except Exception as exc:
            logger.error("YouTube publish_post failed: %s", exc)
            return ConnectorResult(success=False, platform=self.platform_name, error=str(exc))

    async def fetch_analytics(self, since_days: int = 7) -> dict[str, Any]:
        if not self.access_token:
            return {"platform": self.platform_name, "error": "Missing credentials"}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(
                    f"{YOUTUBE_API_BASE}/channels",
                    params={"part": "statistics,snippet", "mine": "true"},
                    headers={"Authorization": f"Bearer {self.access_token}"},
                )
                res.raise_for_status()
                items = res.json().get("items", [])
                return {
                    "platform": self.platform_name,
                    "statistics": items[0].get("statistics", {}) if items else {},
                }
        except Exception as exc:
            return {"platform": self.platform_name, "error": str(exc)}

    async def fetch_comments(self, post_id: str, limit: int = 20) -> list[dict[str, Any]]:
        if not self.access_token:
            return []
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(
                    f"{YOUTUBE_API_BASE}/commentThreads",
                    params={"part": "snippet", "videoId": post_id, "maxResults": limit},
                    headers={"Authorization": f"Bearer {self.access_token}"},
                )
                res.raise_for_status()
                return res.json().get("items", [])
        except Exception:
            return []

    async def reply_comment(self, comment_id: str, message: str) -> ConnectorResult:
        if not self.access_token:
            return ConnectorResult(success=False, platform=self.platform_name, error="Missing token")
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    f"{YOUTUBE_API_BASE}/comments",
                    params={"part": "snippet"},
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    json={"snippet": {"parentId": comment_id, "textOriginal": message}},
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
