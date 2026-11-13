"""Privacy firewall: data classification, egress control, and provider-specific policies."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class DataClassification(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"  # Credentials, tokens, keys - never leaves local


@dataclass
class EgressDecision:
    allowed: bool
    reason: str
    should_redact: bool = False
    detected_patterns: list[str] = field(default_factory=list)


SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("api_key", re.compile(r"(?:sk-[A-Za-z0-9]{20,}|AIza[0-9A-Za-z\-_]{35})")),
    ("bearer_token", re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE)),
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("password_assignment", re.compile(r"(?:password|passwd|secret|token)\s*[:=]\s*['\"]?[^\s'\"]{6,}", re.IGNORECASE)),
]

PII_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
    ("phone", re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"), "[REDACTED_PHONE]"),
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]"),
]


class PrivacyFirewall:
    """Evaluates outbound AI/API payloads and enforces provider-specific policies."""

    def __init__(self):
        # By default, local ollama allows all classifications; cloud providers block RESTRICTED
        self.provider_policies: dict[str, dict] = {
            "ollama": {
                "local": True,
                "max_classification": DataClassification.RESTRICTED,
                "redact_pii": False,
                "allow_egress": True,
            },
            "gemini": {
                "local": False,
                "max_classification": DataClassification.INTERNAL,
                "redact_pii": True,
                "allow_egress": True,
            },
            "openai": {
                "local": False,
                "max_classification": DataClassification.INTERNAL,
                "redact_pii": True,
                "allow_egress": True,
            },
        }
        self._audit_events: list[dict] = []

    def update_policy(self, provider: str, policy_updates: dict) -> None:
        current = self.provider_policies.get(
            provider,
            {
                "local": False,
                "max_classification": DataClassification.PUBLIC,
                "redact_pii": True,
                "allow_egress": True,
            },
        )
        current.update(policy_updates)
        self.provider_policies[provider] = current

    def classify_text(self, text: str) -> tuple[DataClassification, list[str]]:
        """Automatically classify text sensitivity based on detected secrets/PII."""
        findings: list[str] = []
        for label, pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(label)
        if findings:
            return DataClassification.RESTRICTED, findings

        for label, pattern, _ in PII_PATTERNS:
            if pattern.search(text):
                findings.append(label)
        if findings:
            return DataClassification.CONFIDENTIAL, findings

        return DataClassification.INTERNAL, findings

    def redact_pii(self, text: str) -> str:
        """Redact common PII and credential/secret patterns before export or egress."""
        import re as _re

        redacted = text
        for _, pattern, replacement in PII_PATTERNS:
            redacted = pattern.sub(replacement, redacted)
        secret_regexes = [
            _re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{12,}\b"),
            _re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
            _re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"),
            _re.compile(r"\b\d{6,12}:[A-Za-z0-9_-]{20,}\b"),
            _re.compile(r"\b(?:EAAG|EAA)[A-Za-z0-9]{16,}\b"),
        ]
        for pat in secret_regexes:
            redacted = pat.sub("[REDACTED_SECRET]", redacted)
        return redacted

    def evaluate_egress(
        self,
        data: str,
        provider: str,
        classification: Optional[DataClassification] = None,
    ) -> EgressDecision:
        """Determine whether payload can be sent to the target provider."""
        policy = self.provider_policies.get(provider)
        if not policy:
            return EgressDecision(
                allowed=False,
                reason=f"No privacy policy defined for unknown provider '{provider}'",
            )

        if not policy.get("allow_egress", False):
            return EgressDecision(
                allowed=False,
                reason=f"Egress disabled for provider '{provider}'",
            )

        if policy.get("local", False):
            return EgressDecision(allowed=True, reason="Local provider permits processing")

        detected_level, findings = self.classify_text(data)
        order = [
            DataClassification.PUBLIC,
            DataClassification.INTERNAL,
            DataClassification.CONFIDENTIAL,
            DataClassification.RESTRICTED,
        ]
        effective_level = detected_level
        if classification and order.index(classification) > order.index(detected_level):
            effective_level = classification

        max_allowed = policy.get("max_classification", DataClassification.PUBLIC)
        if effective_level == DataClassification.RESTRICTED:
            self._record_block(provider, effective_level.value, findings)
            return EgressDecision(
                allowed=False,
                reason="Secrets or restricted data detected; blocked from cloud egress",
                detected_patterns=findings,
            )

        if order.index(effective_level) > order.index(max_allowed):
            if policy.get("redact_pii", True) and effective_level == DataClassification.CONFIDENTIAL:
                return EgressDecision(
                    allowed=True,
                    reason="Allowed after PII redaction",
                    should_redact=True,
                    detected_patterns=findings,
                )
            self._record_block(provider, effective_level.value, findings)
            return EgressDecision(
                allowed=False,
                reason=f"Classification '{effective_level.value}' exceeds '{max_allowed.value}' for {provider}",
                detected_patterns=findings,
            )

        return EgressDecision(
            allowed=True,
            reason="Permitted under provider policy",
            should_redact=bool(policy.get("redact_pii", False) and findings),
            detected_patterns=findings,
        )

    def _record_block(self, provider: str, classification: str, findings: list[str]) -> None:
        logger.warning(
            "PrivacyFirewall blocked egress to %s (level=%s, patterns=%s)",
            provider,
            classification,
            findings,
        )
        self._audit_events.append({
            "provider": provider,
            "classification": classification,
            "patterns": findings,
            "action": "blocked",
        })

    def get_blocked_events(self, limit: int = 50) -> list[dict]:
        return self._audit_events[-limit:]


_privacy_firewall: Optional[PrivacyFirewall] = None


def get_privacy_firewall() -> PrivacyFirewall:
    global _privacy_firewall
    if _privacy_firewall is None:
        _privacy_firewall = PrivacyFirewall()
    return _privacy_firewall
