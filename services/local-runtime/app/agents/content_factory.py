"""Content Factory agent — generates content drafts using AI and applies brand voice."""

import logging
from typing import Any

from app.agents.base import BaseAgent
from app.core.ai_router import AIRouter

logger = logging.getLogger(__name__)


class ContentFactoryAgent(BaseAgent):
    """Specialist agent for generating platform-ready content drafts."""

    name = "content_factory"
    display_name = "Content Factory"
    description = "Generates social posts, scripts, captions, and threads using AI while enforcing the configured brand voice."
    version = "1.0.0"
    capabilities = ["generate_content", "copywriting", "script_writing", "hashtag_generation"]
    required_permissions = ["use_ai", "write_content"]
    input_schema = {
        "required": ["topic"],
        "properties": {
            "topic": {"type": "string"},
            "platform": {"type": "string"},
            "format": {"type": "string"},
            "brand_voice": {"type": "object"},
            "language": {"type": "string"},
        },
    }
    output_schema = {"required": ["status", "draft"]}

    PLATFORM_LIMITS = {
        "instagram": 2200,
        "youtube": 5000,
        "facebook": 63206,
        "x": 280,
        "linkedin": 3000,
        "telegram": 4096,
    }

    def __init__(self):
        super().__init__()
        self.ai_router = AIRouter()

    async def execute(self, task_data: dict) -> dict:
        topic = task_data.get("topic", "")
        platform = task_data.get("platform", "instagram").lower()
        content_format = task_data.get("format", "post")
        brand_voice = task_data.get("brand_voice", {})
        language = task_data.get("language", "en")
        count = min(max(int(task_data.get("variants", 1)), 1), 5)

        tone = brand_voice.get("tone", "clear, engaging, authentic")
        avoid = brand_voice.get("avoid_words", [])
        cta = task_data.get("cta", "")

        prompt = (
            f"Create {count} {platform} {content_format} draft(s) in '{language}' about: {topic}.\n"
            f"Brand tone: {tone}.\n"
            f"Max characters: {self.PLATFORM_LIMITS.get(platform, 2200)}.\n"
            f"Avoid words: {', '.join(avoid) if avoid else 'none'}.\n"
            f"Include CTA: {cta or 'encourage thoughtful comments'}."
        )

        fallback = (
            f"[Draft] {prompt.splitlines()[0]}\n\n"
            "Key takeaway: Focus on consistency, clear value, and an authentic call to action."
        )
        draft_text, tokens = await self.ask_ai(
            self.ai_router, prompt, provider=task_data.get("provider"), fallback=fallback
        )
        hashtags = self._suggest_hashtags(topic, task_data.get("hashtags"))
        char_limit = self.PLATFORM_LIMITS.get(platform, 2200)
        trimmed = draft_text[:char_limit]

        return {
            "status": "success",
            "platform": platform,
            "format": content_format,
            "draft": trimmed,
            "hashtags": hashtags,
            "character_count": len(trimmed),
            "within_limit": len(draft_text) <= char_limit,
            "tokens_used": tokens,
        }

    def _suggest_hashtags(self, topic: str, explicit: list[str] | None) -> list[str]:
        if explicit:
            return [h if h.startswith("#") else f"#{h}" for h in explicit[:10]]
        words = [w.strip(".,!?") for w in topic.split() if len(w) > 3]
        tags = [f"#{w.capitalize()}" for w in words[:4]]
        if "#JavoAgents" not in tags:
            tags.append("#CreatorWorkflow")
        return tags
