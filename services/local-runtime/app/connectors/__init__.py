"""Social platform connectors package."""

from app.connectors.base import BaseConnector, ConnectorResult, PostPayload
from app.connectors.facebook import FacebookConnector
from app.connectors.instagram import InstagramConnector
from app.connectors.mock import MockConnector
from app.connectors.youtube import YouTubeConnector

CONNECTOR_REGISTRY: dict[str, type[BaseConnector]] = {
    "facebook": FacebookConnector,
    "instagram": InstagramConnector,
    "youtube": YouTubeConnector,
    "mock": MockConnector,
}


def get_connector(platform: str, access_token: str = "", **kwargs) -> BaseConnector:
    """Factory to instantiate a connector for the given platform."""
    cls = CONNECTOR_REGISTRY.get(platform.lower())
    if cls is None:
        raise ValueError(f"Unsupported social platform: {platform}")
    return cls(access_token=access_token, **kwargs)


__all__ = [
    "BaseConnector",
    "ConnectorResult",
    "PostPayload",
    "FacebookConnector",
    "InstagramConnector",
    "YouTubeConnector",
    "MockConnector",
    "CONNECTOR_REGISTRY",
    "get_connector",
]
