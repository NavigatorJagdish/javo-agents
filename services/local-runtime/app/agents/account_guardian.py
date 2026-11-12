"""Account Guardian agent — monitors connected account security and detects anomalies."""

import logging
import time
from typing import Any

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class AccountGuardianAgent(BaseAgent):
    """Specialist agent for social account health, token expiry, and anomaly detection."""

    name = "account_guardian"
    display_name = "Account Guardian"
    description = "Monitors connected social accounts for token expiration, unusual login/publish spikes, and policy warnings."
    version = "1.0.0"
    capabilities = ["configure_security", "anomaly_detection", "token_health_check", "account_protection"]
    required_permissions = ["read_accounts", "read_audit_log"]
    input_schema = {
        "required": ["action"],
        "properties": {
            "action": {"type": "string"},
            "accounts": {"type": "array"},
            "recent_events": {"type": "array"},
        },
    }
    output_schema = {"required": ["status", "alerts"]}

    async def execute(self, task_data: dict) -> dict:
        accounts: list[dict[str, Any]] = task_data.get("accounts", [])
        events: list[dict[str, Any]] = task_data.get("recent_events", [])
        now = time.time()
        alerts: list[dict[str, Any]] = []

        for acc in accounts:
            acc_id = acc.get("id", acc.get("handle", "unknown"))
            expires_at = acc.get("token_expires_at")
            if expires_at and float(expires_at) - now < 86400 * 3:
                alerts.append({
                    "severity": "medium",
                    "account_id": acc_id,
                    "type": "token_expiring_soon",
                    "message": f"OAuth token for {acc_id} expires within 72 hours.",
                })
            if not acc.get("two_factor_enabled", True):
                alerts.append({
                    "severity": "high",
                    "account_id": acc_id,
                    "type": "missing_2fa",
                    "message": f"Two-factor authentication is not confirmed for {acc_id}.",
                })

        failed_auth = sum(1 for ev in events if ev.get("type") == "auth_failed")
        if failed_auth >= 5:
            alerts.append({
                "severity": "critical",
                "type": "brute_force_indicator",
                "message": f"Detected {failed_auth} failed authentication attempts in recent events.",
            })

        return {
            "status": "success",
            "accounts_checked": len(accounts),
            "events_checked": len(events),
            "alerts": alerts,
            "healthy": len(alerts) == 0,
        }
