"""Content Recycler agent — repurposes older evergreen content for new platforms and formats."""

import logging

from app.agents.base import BaseAgent
from app.core.ai_router import AIRouter

logger = logging.getLogger(__name__)


class ContentRecyclerAgent(BaseAgent):
    """Specialist agent that transforms high-performing past content into fresh multi-platform assets."""

    name = "content_recycler"
    display_name = "Content Recycler"
    description = "Identifies evergreen content candidates and repurposes them into fresh hooks, carousels, or shorts scripts."
    version = "1.0.0"
    capabilities = ["repurpose_content", "content_refresh", "cross_platform_adapt"]
    required_permissions = ["read_content", "write_content", "use_ai"]
    input_schema = {
        "required": ["original_content"],
        "properties": {
            "original_content": {"type": "string"},
            "source_platform": {"type": "string"},
            "target_platform": {"type": "string"},
            "target_format": {"type": "string"},
        },
    }
    output_schema = {"required": ["status", "repurposed_draft"]}

    def __init__(self):
        super().__init__()
        self.ai_router = AIRouter()

    async def execute(self, task_data: dict) -> dict:
        original = task_data.get("original_content", "").strip()
        if not original:
            return {"status": "error", "error": "original_content is required"}

        source_platform = task_data.get("source_platform", "youtube")
        target_platform = task_data.get("target_platform", "instagram")
        target_format = task_data.get("target_format", "carousel")

        prompt = (
            f"Repurpose this {source_platform} content into a fresh {target_platform} {target_format} "
            f"with a strong opening hook:\n\n{original[:1800]}"
        )
        first_line = original.splitlines()[0][:140]
        draft, tokens = await self.ask_ai(
            self.ai_router,
            prompt,
            fallback=f"Fresh Hook: {first_line}\n\n[Reframed for quick reading with actionable takeaway]",
        )

        return {
            "status": "success",
            "source_platform": source_platform,
            "target_platform": target_platform,
            "target_format": target_format,
            "repurposed_draft": draft,
            "suggested_updates": self._suggest_refresh_notes(original),
            "tokens_used": tokens,
        }

    def _suggest_refresh_notes(self, original: str) -> list[str]:
        notes = ["Update opening hook for current audience trends"]
        if len(original) > 500:
            notes.append("Split into 3-5 bite-sized slides or short clips")
        notes.append("Verify any statistics or dates mentioned are still current")
        return notes
