"""Budget Guardian agent — tracks spending, enforces zero-cost/low-cost budgets, optimizes AI spend."""

import logging
from typing import Any

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class BudgetGuardianAgent(BaseAgent):
    """Specialist agent that tracks API/cloud usage costs and enforces hard spending caps."""

    name = "budget_guardian"
    display_name = "Budget Guardian"
    description = "Tracks AI token and API costs, enforces monthly/task budgets, and recommends zero-cost local routing."
    version = "1.0.0"
    capabilities = ["budget_tracking", "cost_enforcement", "cost_optimization"]
    required_permissions = ["read_usage", "enforce_budget"]
    input_schema = {
        "required": ["action"],
        "properties": {
            "action": {"type": "string"},
            "spent_usd": {"type": "number"},
            "budget_usd": {"type": "number"},
            "estimated_cost_usd": {"type": "number"},
            "provider": {"type": "string"},
        },
    }
    output_schema = {"required": ["status", "allowed"]}

    def __init__(self):
        super().__init__()
        self._ledger: list[dict[str, Any]] = []

    async def execute(self, task_data: dict) -> dict:
        action = task_data.get("action", "check_budget")
        budget_usd = float(task_data.get("budget_usd", 0.0))  # Default $0 zero-cost mode
        spent_usd = float(task_data.get("spent_usd", sum(x["cost_usd"] for x in self._ledger)))
        est_cost = float(task_data.get("estimated_cost_usd", 0.0))
        provider = task_data.get("provider", "ollama")

        if action == "record_spend":
            self._ledger.append({"provider": provider, "cost_usd": est_cost})
            spent_usd += est_cost

        projected = spent_usd + (est_cost if action != "record_spend" else 0.0)
        allowed = projected <= budget_usd or provider == "ollama"

        recommendation = "use_local_ollama" if not allowed else "within_budget"
        if not allowed:
            self.logger.warning("Budget exceeded: projected=$%.4f > limit=$%.4f", projected, budget_usd)

        return {
            "status": "success",
            "allowed": allowed,
            "spent_usd": round(spent_usd, 4),
            "budget_usd": round(budget_usd, 4),
            "remaining_usd": round(max(0.0, budget_usd - spent_usd), 4),
            "recommendation": recommendation,
        }
