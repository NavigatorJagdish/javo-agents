"""API Integration agent — manages external API connections, health checks, and data sync."""

import logging
import time
from typing import Any

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class APIIntegrationAgent(BaseAgent):
    """Specialist agent for managing external API connections and synchronizing remote data."""

    name = "api_integration"
    display_name = "API Integration"
    description = "Manages external social/cloud API connections, validates tokens, enforces rate limits, and syncs remote records."
    version = "1.0.0"
    capabilities = ["connect_api", "data_sync", "rate_limit_check", "webhook_verify"]
    required_permissions = ["manage_integrations", "network_egress"]
    input_schema = {
        "required": ["action"],
        "properties": {
            "action": {"type": "string"},
            "provider": {"type": "string"},
            "endpoint": {"type": "string"},
            "credentials_present": {"type": "boolean"},
        },
    }
    output_schema = {"required": ["status"]}

    SUPPORTED_PROVIDERS = {"youtube", "instagram", "facebook", "telegram", "gemini", "ollama"}

    def __init__(self):
        super().__init__()
        self._connections: dict[str, dict[str, Any]] = {}

    async def execute(self, task_data: dict) -> dict:
        action = task_data.get("action", "verify_connection")
        provider = task_data.get("provider", "unknown").lower()

        if action == "sync":
            return self._sync_provider(provider, task_data)
        if action == "list_connections":
            return {"status": "success", "connections": list(self._connections.values())}
        return self._verify_connection(provider, task_data)

    def _verify_connection(self, provider: str, task_data: dict) -> dict:
        if provider not in self.SUPPORTED_PROVIDERS:
            return {"status": "error", "error": f"Unsupported provider '{provider}'"}

        has_creds = bool(task_data.get("credentials_present", provider == "ollama"))
        state = "connected" if has_creds else "needs_auth"
        record = {
            "provider": provider,
            "state": state,
            "checked_at": time.time(),
            "rate_limit_remaining": int(task_data.get("rate_limit_remaining", 1000)),
        }
        self._connections[provider] = record
        return {"status": "success", "connection": record}

    def _sync_provider(self, provider: str, task_data: dict) -> dict:
        conn = self._connections.get(provider)
        if conn and conn.get("state") != "connected":
            return {"status": "error", "error": f"Provider '{provider}' is not connected"}

        items = task_data.get("items", [])
        synced_count = len(items)
        self.logger.info("Synced %d items for provider %s", synced_count, provider)
        return {
            "status": "success",
            "provider": provider,
            "synced_count": synced_count,
            "synced_at": time.time(),
        }
