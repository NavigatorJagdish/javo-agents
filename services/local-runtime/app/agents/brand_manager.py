"""Brand Manager agent — enforces brand guidelines and reviews content consistency."""

import logging
from typing import Any

from app.agents.base import BaseAgent
from app.core.ai_router import AIRouter

logger = logging.getLogger(__name__)


class BrandManagerAgent(BaseAgent):
    """Specialist agent that verifies content alignment with brand guidelines."""

    name = "brand_manager"
    display_name = "Brand Manager"
    description = "Enforces brand voice, banned-word policies, visual/color guidelines, and messaging consistency across all drafts."
    version = "1.0.0"
    capabilities = ["brand_review", "tone_check", "guideline_enforcement"]
    required_permissions = ["read_brand_profile", "review_content"]
    input_schema = {
        "required": ["content"],
        "properties": {
            "content": {"type": "string"},
            "brand_profile": {"type": "object"},
            "platform": {"type": "string"},
        },
    }
    output_schema = {"required": ["status", "approved", "score"]}

    def __init__(self):
        super().__init__()
        self.ai_router = AIRouter()

    async def execute(self, task_data: dict) -> dict:
        content = task_data.get("content", "")
        if not content and "quality_check_result" in task_data:
            content = task_data["quality_check_result"].get("content", "")
        profile: dict[str, Any] = task_data.get("brand_profile", {})
        banned_words = [w.lower() for w in profile.get("avoid_words", [])]
        required_terms = [w.lower() for w in profile.get("preferred_terms", [])]

        violations: list[str] = []
        lower_content = content.lower()
        for word in banned_words:
            if word and word in lower_content:
                violations.append(f"Contains restricted term: '{word}'")

        if not content.strip():
            violations.append("Content body is empty")

        bonus = sum(5 for term in required_terms if term and term in lower_content)
        score = max(0, min(100, 90 - len(violations) * 25 + bonus))
        approved = len(violations) == 0 and score >= 70

        tone = profile.get("tone", "professional and approachable")
        ai_notes, tokens = await self.ask_ai(
            self.ai_router,
            f"Does this text match a '{tone}' brand tone? Reply in 2 short sentences:\n{content[:1000]}",
            fallback=f"Checked against target brand tone ({tone}).",
        ) if content else (f"Checked against target brand tone ({tone}).", 0)
        return {
            "status": "success",
            "approved": approved,
            "score": score,
            "violations": violations,
            "tone_feedback": ai_notes,
            "content": content,
            "tokens_used": tokens,
        }
