"""Abstract base class for social media platform connectors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class PostPayload:
    caption: str
    media_path: Optional[str] = None
    media_url: Optional[str] = None
    media_type: str = "text"  # text | image | video
    title: Optional[str] = None
    hashtags: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectorResult:
    success: bool
    platform: str
    post_id: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None
    raw: dict[str, Any] = field(default_factory=dict)


class BaseConnector(ABC):
    """Base interface all social platform connectors must implement."""

    platform_name: str = "base"

    def __init__(self, access_token: str = "", account_id: str = "", **kwargs: Any):
        self.access_token = access_token
        self.account_id = account_id
        self.extra_config = kwargs

    @abstractmethod
    async def verify_credentials(self) -> bool:
        """Check whether stored credentials/tokens are valid."""

    @abstractmethod
    async def publish_post(self, payload: PostPayload) -> ConnectorResult:
        """Publish a post to the target social platform."""

    @abstractmethod
    async def fetch_analytics(self, since_days: int = 7) -> dict[str, Any]:
        """Retrieve engagement and follower metrics for the account."""

    @abstractmethod
    async def fetch_comments(self, post_id: str, limit: int = 20) -> list[dict[str, Any]]:
        """Fetch recent comments on a published post."""

    @abstractmethod
    async def reply_comment(self, comment_id: str, message: str) -> ConnectorResult:
        """Reply to a comment on the platform."""

    def format_caption(self, payload: PostPayload) -> str:
        """Combine caption text and formatted hashtags."""
        tags = " ".join(
            tag if tag.startswith("#") else f"#{tag}" for tag in payload.hashtags
        )
        if tags:
            return f"{payload.caption.strip()}\n\n{tags}".strip()
        return payload.caption.strip()
