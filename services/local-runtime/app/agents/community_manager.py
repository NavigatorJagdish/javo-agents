"""Community Manager agent — monitors engagement, drafts replies, and runs sentiment analysis."""

import logging
from typing import Any

from app.agents.base import BaseAgent
from app.core.ai_router import AIRouter

logger = logging.getLogger(__name__)


class CommunityManagerAgent(BaseAgent):
    """Specialist agent for comment triage, sentiment scoring, and reply drafting."""

    name = "community_manager"
    display_name = "Community Manager"
    description = "Monitors community comments and DMs, classifies sentiment, flags toxicity, and drafts brand-safe replies."
    version = "1.0.0"
    capabilities = ["sentiment_analysis", "auto_reply", "comment_moderation", "engagement_monitoring"]
    required_permissions = ["read_comments", "draft_replies", "use_ai"]
    input_schema = {
        "required": ["comments"],
        "properties": {
            "comments": {"type": "array"},
            "auto_draft": {"type": "boolean"},
            "brand_tone": {"type": "string"},
        },
    }
    output_schema = {"required": ["status", "analyzed"]}

    POSITIVE_WORDS = {"love", "great", "awesome", "thanks", "helpful", "amazing", "nice", "fire"}
    NEGATIVE_WORDS = {"hate", "spam", "scam", "worst", "terrible", "broken", "bad", "fake"}

    def __init__(self):
        super().__init__()
        self.ai_router = AIRouter()

    async def execute(self, task_data: dict) -> dict:
        comments: list[dict[str, Any] | str] = task_data.get("comments", [])
        auto_draft = bool(task_data.get("auto_draft", True))
        tone = task_data.get("brand_tone", "warm and helpful")

        analyzed = []
        counts = {"positive": 0, "neutral": 0, "negative": 0}
        total_tokens = 0

        for idx, item in enumerate(comments):
            text = item.get("text", "") if isinstance(item, dict) else str(item)
            sentiment = self._classify_sentiment(text)
            counts[sentiment] += 1
            entry: dict[str, Any] = {
                "index": idx,
                "text": text,
                "sentiment": sentiment,
                "needs_escalation": sentiment == "negative",
            }
            if auto_draft and sentiment != "negative":
                reply, tokens = await self.ask_ai(
                    self.ai_router,
                    f"Write a short, {tone} social media reply (1-2 sentences) to: {text}",
                    fallback="Thank you for sharing your thoughts! We appreciate you being part of the community.",
                )
                entry["suggested_reply"] = reply
                total_tokens += tokens
            analyzed.append(entry)

        return {
            "status": "success",
            "analyzed": analyzed,
            "sentiment_summary": counts,
            "tokens_used": total_tokens,
        }

    def _classify_sentiment(self, text: str) -> str:
        words = set(text.lower().split())
        pos = len(words & self.POSITIVE_WORDS)
        neg = len(words & self.NEGATIVE_WORDS)
        if neg > pos:
            return "negative"
        if pos > neg:
            return "positive"
        return "neutral"
