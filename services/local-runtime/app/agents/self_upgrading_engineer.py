"""Self-Upgrading Engineer agent — monitors system health, suggests optimizations, proposes patches."""

import logging
import platform
from typing import Any

from app.agents.base import BaseAgent
from app.core.ai_router import AIRouter

logger = logging.getLogger(__name__)


class SelfUpgradingEngineerAgent(BaseAgent):
    """Specialist agent for diagnostics, performance optimization, and safe skill/patch proposals."""

    name = "self_upgrading_engineer"
    display_name = "Self-Upgrading Engineer"
    description = "Monitors runtime health, detects bottlenecks, proposes optimizations, and prepares sandboxed skill upgrades."
    version = "1.0.0"
    capabilities = ["system_diagnostics", "optimization_analysis", "patch_proposal", "skill_upgrade"]
    required_permissions = ["read_diagnostics", "propose_upgrades"]
    input_schema = {
        "required": ["action"],
        "properties": {
            "action": {"type": "string"},
            "metrics": {"type": "object"},
            "error_logs": {"type": "array"},
            "target_module": {"type": "string"},
        },
    }
    output_schema = {"required": ["status"]}

    def __init__(self):
        super().__init__()
        self.ai_router = AIRouter()

    async def execute(self, task_data: dict) -> dict:
        action = task_data.get("action", "health_audit")
        if action == "diagnose_errors":
            return await self._diagnose_errors(task_data)
        if action == "propose_optimization":
            return await self._propose_optimization(task_data)
        return self._health_audit(task_data)

    def _health_audit(self, task_data: dict) -> dict:
        metrics: dict[str, Any] = task_data.get("metrics", {})
        cpu_pct = float(metrics.get("cpu_percent", 0))
        ram_pct = float(metrics.get("ram_percent", 0))
        disk_pct = float(metrics.get("disk_percent", 0))

        findings = []
        if cpu_pct > 85:
            findings.append({"severity": "high", "area": "cpu", "recommendation": "Throttle concurrent background workers"})
        if ram_pct > 80:
            findings.append({"severity": "high", "area": "memory", "recommendation": "Unload idle local LLM weights"})
        if disk_pct > 90:
            findings.append({"severity": "critical", "area": "disk", "recommendation": "Rotate logs and archive old media cache"})

        return {
            "status": "success",
            "environment": {
                "python_version": platform.python_version(),
                "os": platform.system(),
                "machine": platform.machine(),
            },
            "health_score": max(0, 100 - len(findings) * 20),
            "findings": findings,
        }

    async def _diagnose_errors(self, task_data: dict) -> dict:
        logs = task_data.get("error_logs", [])
        if not logs:
            return {"status": "success", "diagnosis": "No recent error logs provided.", "tokens_used": 0}
        sample = "\n".join(str(x) for x in logs[:15])
        prompt = f"Analyze these application error logs and suggest root cause + safe fix:\n{sample}"
        text, tokens = await self.ask_ai(
            self.ai_router,
            prompt,
            fallback="Inspect recent stack traces, add input validation, and verify retry limits.",
        )
        return {"status": "success", "error_count": len(logs), "diagnosis": text, "tokens_used": tokens}

    async def _propose_optimization(self, task_data: dict) -> dict:
        target = task_data.get("target_module", "local-runtime")
        prompt = f"Suggest concrete performance and reliability optimizations for module '{target}' with context: {task_data.get('metrics', {})}"
        text, tokens = await self.ask_ai(
            self.ai_router,
            prompt,
            fallback="Enable connection pooling, cache repeated queries, and bound worker concurrency.",
        )
        return {
            "status": "success",
            "target_module": target,
            "requires_approval": True,
            "proposal": text,
            "tokens_used": tokens,
        }
