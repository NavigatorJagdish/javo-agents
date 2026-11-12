"""Security Guardian agent — monitors runtime security, PII egress, and threat indicators."""

import logging
import re
from typing import Any

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class SecurityGuardianAgent(BaseAgent):
    """Specialist agent for threat detection, secret-leak scanning, and privacy firewall checks."""

    name = "security_guardian"
    display_name = "Security Guardian"
    description = "Scans outbound payloads for leaked secrets/PII, audits permission requests, and flags security threats."
    version = "1.0.0"
    capabilities = ["threat_detection", "secret_scan", "egress_audit", "security_monitoring"]
    required_permissions = ["read_audit_log", "manage_security"]
    input_schema = {
        "required": ["action"],
        "properties": {
            "action": {"type": "string"},
            "payload": {"type": "string"},
            "requested_permissions": {"type": "array"},
        },
    }
    output_schema = {"required": ["status", "safe"]}

    SECRET_PATTERNS = [
        ("openai_or_generic_sk", re.compile(r"sk-[A-Za-z0-9]{20,}")),
        ("google_api_key", re.compile(r"AIza[0-9A-Za-z\-_]{30,}")),
        ("telegram_bot_token", re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{30,}\b")),
        ("private_key_block", re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ]

    async def execute(self, task_data: dict) -> dict:
        action = task_data.get("action", "scan_payload")
        if action == "audit_permissions":
            return self._audit_permissions(task_data)
        return self._scan_payload(task_data)

    def _scan_payload(self, task_data: dict) -> dict:
        payload = str(task_data.get("payload", ""))
        detections: list[dict[str, Any]] = []
        for label, pattern in self.SECRET_PATTERNS:
            if pattern.search(payload):
                detections.append({"type": label, "severity": "critical"})

        safe = len(detections) == 0
        if not safe:
            self.logger.warning("Security Guardian blocked payload with %d secret detections", len(detections))
        return {
            "status": "success",
            "safe": safe,
            "detections": detections,
            "recommendation": "redact_secrets_before_egress" if not safe else "clear",
        }

    def _audit_permissions(self, task_data: dict) -> dict:
        requested = set(task_data.get("requested_permissions", []))
        high_risk = {"emergency_override", "raw_filesystem_write", "unrestricted_shell"}
        flagged = sorted(requested & high_risk)
        return {
            "status": "success",
            "safe": len(flagged) == 0,
            "flagged_permissions": flagged,
        }
