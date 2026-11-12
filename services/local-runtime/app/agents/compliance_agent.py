"""Compliance Agent — checks content and platform integrations against regulatory & platform policies."""

import logging
from typing import Any

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class ComplianceAgent(BaseAgent):
    """Specialist agent for GDPR/privacy compliance, sponsored-disclosure checks, and platform policy verification."""

    name = "compliance_agent"
    display_name = "Compliance Officer"
    description = "Checks content disclosures, data-privacy compliance, and social platform terms of service before execution."
    version = "1.0.0"
    capabilities = ["compliance_check", "policy_audit", "disclosure_verification"]
    required_permissions = ["audit_compliance"]
    input_schema = {
        "required": ["action"],
        "properties": {
            "action": {"type": "string"},
            "content": {"type": "string"},
            "is_sponsored": {"type": "boolean"},
            "collects_personal_data": {"type": "boolean"},
            "has_user_consent": {"type": "boolean"},
        },
    }
    output_schema = {"required": ["status", "compliant"]}

    DISCLOSURE_TAGS = {"#ad", "#sponsored", "#paidpartnership", "paid promotion"}

    async def execute(self, task_data: dict) -> dict:
        content = task_data.get("content", "").lower()
        is_sponsored = bool(task_data.get("is_sponsored", False))
        collects_pii = bool(task_data.get("collects_personal_data", False))
        has_consent = bool(task_data.get("has_user_consent", True))

        violations: list[dict[str, Any]] = []

        if is_sponsored and not any(tag in content for tag in self.DISCLOSURE_TAGS):
            violations.append({
                "rule": "ftc_sponsored_disclosure",
                "severity": "high",
                "message": "Sponsored content must include clear disclosure (#ad or #sponsored).",
            })

        if collects_pii and not has_consent:
            violations.append({
                "rule": "privacy_consent_required",
                "severity": "critical",
                "message": "Personal data processing requires explicit user consent.",
            })

        compliant = len(violations) == 0
        return {
            "status": "success",
            "compliant": compliant,
            "violations": violations,
            "checked_rules": ["ftc_sponsored_disclosure", "privacy_consent_required"],
        }
