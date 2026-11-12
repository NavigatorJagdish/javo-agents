"""Niche Radar agent — tracks trends, competitor patterns, and content opportunities."""

import logging
from typing import Any

from app.agents.base import BaseAgent
from app.core.ai_router import AIRouter

logger = logging.getLogger(__name__)


class NicheRadarAgent(BaseAgent):
    """Specialist agent for trend discovery, competitor benchmarking, and topic opportunity scoring."""

    name = "niche_radar"
    display_name = "Niche Radar"
    description = "Tracks niche trends, compares competitor engagement patterns, and scores content opportunities."
    version = "1.0.0"
    capabilities = ["trend_tracking", "competitor_analysis", "opportunity_detection"]
    required_permissions = ["read_analytics", "use_ai"]
    input_schema = {
        "required": ["niche"],
        "properties": {
            "niche": {"type": "string"},
            "competitors": {"type": "array"},
            "signals": {"type": "array"},
        },
    }
    output_schema = {"required": ["status", "opportunities"]}

    def __init__(self):
        super().__init__()
        self.ai_router = AIRouter()

    async def execute(self, task_data: dict) -> dict:
        niche = task_data.get("niche", "AI productivity")
        competitors: list[str] = task_data.get("competitors", [])
        signals: list[dict[str, Any]] = task_data.get("signals", [])

        ranked_signals = sorted(
            signals,
            key=lambda s: float(s.get("momentum", 0)) - float(s.get("saturation", 0)) * 0.5,
            reverse=True,
        )

        prompt = (
            f"Identify 3 high-opportunity content angles in the '{niche}' niche. "
            f"Competitors watched: {competitors or ['none specified']}. "
            f"Top local trend signals: {ranked_signals[:5]}."
        )
        ai_summary, tokens = await self.ask_ai(
            self.ai_router,
            prompt,
            fallback="Focus on beginner tutorials, behind-the-scenes workflows, and transparent tool comparisons.",
        )

        opportunities = [
            {
                "topic": sig.get("topic", "Untitled trend"),
                "opportunity_score": round(float(sig.get("momentum", 50)) - float(sig.get("saturation", 20)) * 0.4, 1),
            }
            for sig in ranked_signals[:5]
        ]

        return {
            "status": "success",
            "niche": niche,
            "opportunities": opportunities,
            "strategic_brief": ai_summary,
            "tokens_used": tokens,
        }
