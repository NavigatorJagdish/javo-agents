"""Release Agent — manages application/skill releases, version tracking, and rollout checks."""

import logging
import re
from typing import Any

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class ReleaseAgent(BaseAgent):
    """Specialist agent for semantic versioning, release readiness checks, and deployment tracking."""

    name = "release_agent"
    display_name = "Release Manager"
    description = "Validates semantic versions, checks release readiness gates, and records deployment history."
    version = "1.0.0"
    capabilities = ["release_management", "version_tracking", "readiness_check"]
    required_permissions = ["manage_releases"]
    input_schema = {
        "required": ["version"],
        "properties": {
            "version": {"type": "string"},
            "channel": {"type": "string"},
            "checks": {"type": "object"},
        },
    }
    output_schema = {"required": ["status", "ready_for_release"]}

    SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?$")

    def __init__(self):
        super().__init__()
        self._releases: list[dict[str, Any]] = []

    async def execute(self, task_data: dict) -> dict:
        version = task_data.get("version", "0.1.0")
        channel = task_data.get("channel", "beta")
        checks: dict[str, bool] = task_data.get("checks", {"tests_passed": True, "security_scan_passed": True})

        blockers: list[str] = []
        if not self.SEMVER_RE.match(version):
            blockers.append(f"Invalid semantic version: '{version}'")
        for check_name, passed in checks.items():
            if not passed:
                blockers.append(f"Release gate failed: {check_name}")

        ready = len(blockers) == 0
        record = {"version": version, "channel": channel, "ready": ready, "blockers": blockers}
        if ready:
            self._releases.append(record)

        return {
            "status": "success",
            "version": version,
            "channel": channel,
            "ready_for_release": ready,
            "blockers": blockers,
            "release_history_count": len(self._releases),
        }
