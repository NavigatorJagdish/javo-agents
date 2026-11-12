"""Weekly Analyst agent — generates weekly performance reports and trend summaries."""

import logging
from typing import Any

from app.agents.base import BaseAgent
from app.core.ai_router import AIRouter

logger = logging.getLogger(__name__)


class WeeklyAnalystAgent(BaseAgent):
    """Specialist agent that synthesizes weekly metrics into executive summaries and action plans."""

    name = "weekly_analyst"
    display_name = "Weekly Analyst"
    description = "Aggregates weekly performance metrics, detects week-over-week trends, and compiles actionable weekly briefings."
    version = "1.0.0"
    capabilities = ["analyze_trends", "compile_report", "weekly_summary"]
    required_permissions = ["read_analytics", "use_ai"]
    input_schema = {
        "required": ["action"],
        "properties": {
            "action": {"type": "string"},
            "current_week": {"type": "object"},
            "previous_week": {"type": "object"},
        },
    }
    output_schema = {"required": ["status", "report"]}

    def __init__(self):
        super().__init__()
        self.ai_router = AIRouter()

    async def execute(self, task_data: dict) -> dict:
        curr: dict[str, Any] = task_data.get("current_week", {})
        prev: dict[str, Any] = task_data.get("previous_week", {})

        # Pull upstream orchestrator data if available
        if not curr and "gather_analytics_result" in task_data:
            curr = task_data["gather_analytics_result"].get("totals", {})

        deltas = self._compute_deltas(curr, prev)
        prompt = f"Write a concise weekly performance summary with 3 priorities based on these WoW deltas: {deltas}"
        narrative, tokens = await self.ask_ai(
            self.ai_router,
            prompt,
            fallback="Weekly performance tracked. Prioritize top-converting topics and consistent posting cadence.",
        )

        report = {
            "current_week": curr,
            "previous_week": prev,
            "wow_deltas": deltas,
            "executive_summary": narrative,
            "growth_insights": task_data.get("growth_insights_result", {}).get("recommendations"),
        }
        return {"status": "success", "report": report, "tokens_used": tokens}

    def _compute_deltas(self, curr: dict[str, Any], prev: dict[str, Any]) -> dict[str, Any]:
        deltas = {}
        for key, val in curr.items():
            if isinstance(val, (int, float)):
                old = float(prev.get(key, 0))
                pct = ((val - old) / old * 100) if old else (100.0 if val > 0 else 0.0)
                deltas[key] = {"current": val, "previous": old, "change_pct": round(pct, 2)}
        return deltas
