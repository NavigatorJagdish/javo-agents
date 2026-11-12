"""Growth Scientist agent — analyzes growth metrics, suggests strategies, designs A/B tests."""

import logging
import math
from typing import Any

from app.agents.base import BaseAgent
from app.core.ai_router import AIRouter

logger = logging.getLogger(__name__)


class GrowthScientistAgent(BaseAgent):
    """Specialist agent for growth analytics, strategy, and A/B test design."""

    name = "growth_scientist"
    display_name = "Growth Scientist"
    description = "Analyzes audience and engagement growth metrics, suggests data-driven strategies, and designs statistically sound A/B tests."
    version = "1.0.0"
    capabilities = ["growth_analysis", "ab_testing", "strategy_generation", "funnel_diagnostics"]
    required_permissions = ["read_analytics", "use_ai"]
    input_schema = {
        "required": ["action"],
        "properties": {
            "action": {"type": "string"},
            "metrics": {"type": "array"},
            "goal": {"type": "string"},
            "baseline_rate": {"type": "number"},
            "min_detectable_effect": {"type": "number"},
        },
    }
    output_schema = {"required": ["status"]}

    def __init__(self):
        super().__init__()
        self.ai_router = AIRouter()

    async def execute(self, task_data: dict) -> dict:
        action = task_data.get("action", "analyze_growth")
        if action == "design_ab_test":
            return self._design_ab_test(task_data)
        if action == "evaluate_ab_test":
            return self._evaluate_ab_test(task_data)
        return await self._analyze_growth(task_data)

    async def _analyze_growth(self, task_data: dict) -> dict:
        metrics: list[dict[str, Any]] = task_data.get("metrics", [])
        goal = task_data.get("goal", "Increase engagement rate and follower growth")

        summary = self._compute_metric_summary(metrics)
        prompt = (
            f"Analyze these growth metrics for goal '{goal}': {summary}. "
            "Provide 3 concrete growth experiments ranked by expected impact and effort."
        )
        ai_text, tokens = await self.ask_ai(
            self.ai_router,
            prompt,
            provider=task_data.get("provider"),
            fallback=(
                "1. Test hook variations on top-performing time slots. "
                "2. Double down on short-form high-retention formats. "
                "3. Run 48h A/B caption CTA experiment."
            ),
        )
        return {
            "status": "success",
            "summary": summary,
            "recommendations": ai_text,
            "tokens_used": tokens,
        }

    def _compute_metric_summary(self, metrics: list[dict[str, Any]]) -> dict[str, Any]:
        if not metrics:
            return {"count": 0, "trend": "insufficient_data"}
        values = [float(m.get("value", 0)) for m in metrics]
        first, last = values[0], values[-1]
        growth_pct = ((last - first) / first * 100) if first else 0.0
        avg = sum(values) / len(values)
        return {
            "count": len(values),
            "first": round(first, 2),
            "latest": round(last, 2),
            "average": round(avg, 2),
            "growth_pct": round(growth_pct, 2),
            "trend": "up" if growth_pct > 2 else ("down" if growth_pct < -2 else "flat"),
        }

    def _design_ab_test(self, task_data: dict) -> dict:
        p1 = float(task_data.get("baseline_rate", 0.05))
        mde = float(task_data.get("min_detectable_effect", 0.02))
        p2 = min(max(p1 + mde, 0.001), 0.999)
        z_alpha = 1.96  # 95% confidence
        z_beta = 0.84   # 80% power
        pooled = (p1 + p2) / 2
        numerator = (z_alpha * math.sqrt(2 * pooled * (1 - pooled)) +
                     z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
        sample_per_variant = math.ceil(numerator / max((p2 - p1) ** 2, 1e-6))

        return {
            "status": "success",
            "test_design": {
                "hypothesis": task_data.get("hypothesis", "Variant B improves conversion over Variant A"),
                "baseline_rate": p1,
                "target_rate": round(p2, 4),
                "confidence_level": 0.95,
                "statistical_power": 0.80,
                "sample_size_per_variant": sample_per_variant,
                "total_sample_needed": sample_per_variant * 2,
                "variants": ["control_A", "treatment_B"],
            },
        }

    def _evaluate_ab_test(self, task_data: dict) -> dict:
        a_conv = int(task_data.get("control_conversions", 0))
        a_tot = max(int(task_data.get("control_total", 1)), 1)
        b_conv = int(task_data.get("variant_conversions", 0))
        b_tot = max(int(task_data.get("variant_total", 1)), 1)

        p_a, p_b = a_conv / a_tot, b_conv / b_tot
        p_pool = (a_conv + b_conv) / (a_tot + b_tot)
        se = math.sqrt(max(p_pool * (1 - p_pool) * (1 / a_tot + 1 / b_tot), 1e-9))
        z_score = (p_b - p_a) / se
        significant = abs(z_score) >= 1.96
        winner = "variant_B" if significant and p_b > p_a else ("control_A" if significant else "inconclusive")
        return {
            "status": "success",
            "control_rate": round(p_a, 4),
            "variant_rate": round(p_b, 4),
            "lift_pct": round(((p_b - p_a) / max(p_a, 1e-6)) * 100, 2),
            "z_score": round(z_score, 3),
            "statistically_significant": significant,
            "winner": winner,
        }
