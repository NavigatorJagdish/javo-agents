"""Brand Studio agent — generates brand asset specs, color palettes, and content templates."""

import logging
from typing import Any

from app.agents.base import BaseAgent
from app.core.ai_router import AIRouter

logger = logging.getLogger(__name__)


class BrandStudioAgent(BaseAgent):
    """Specialist agent for generating brand palettes, typography tokens, and social templates."""

    name = "brand_studio"
    display_name = "Brand Studio"
    description = "Generates cohesive brand color schemes, typography systems, and reusable content layout templates."
    version = "1.0.0"
    capabilities = ["setup_brand", "color_palette", "template_generation", "brand_kit"]
    required_permissions = ["write_brand_profile", "use_ai"]
    input_schema = {
        "required": ["brand_name"],
        "properties": {
            "brand_name": {"type": "string"},
            "niche": {"type": "string"},
            "style": {"type": "string"},
        },
    }
    output_schema = {"required": ["status", "brand_kit"]}

    DEFAULT_PALETTES = {
        "futuristic": {"primary": "#00E5FF", "secondary": "#8B5CF6", "background": "#0B1026", "text": "#E2E6F0"},
        "minimal": {"primary": "#111827", "secondary": "#3B82F6", "background": "#F9FAFB", "text": "#1F2937"},
        "warm": {"primary": "#EA580C", "secondary": "#F59E0B", "background": "#FFFBEB", "text": "#292524"},
    }

    def __init__(self):
        super().__init__()
        self.ai_router = AIRouter()

    async def execute(self, task_data: dict) -> dict:
        brand_name = task_data.get("brand_name", "Javo Creator")
        niche = task_data.get("niche", "Technology & AI")
        style = task_data.get("style", "futuristic").lower()

        palette = self.DEFAULT_PALETTES.get(style, self.DEFAULT_PALETTES["futuristic"])
        tagline, tokens = await self.ask_ai(
            self.ai_router,
            f"Write one crisp 5-7 word tagline for '{brand_name}' in the '{niche}' niche.",
            fallback=f"{brand_name} — Smart Automation for {niche}",
        )
        tagline = tagline.strip()

        brand_kit: dict[str, Any] = {
            "brand_name": brand_name,
            "tagline": tagline,
            "style": style,
            "colors": palette,
            "typography": {"heading": "Space Grotesk", "body": "Inter", "mono": "JetBrains Mono"},
            "templates": [
                {"name": "Hook + Value Carousel", "slides": 5, "aspect_ratio": "4:5"},
                {"name": "Short Video Overlay", "duration_s": 45, "aspect_ratio": "9:16"},
                {"name": "Announcement Card", "aspect_ratio": "16:9"},
            ],
        }
        return {"status": "success", "brand_kit": brand_kit, "tokens_used": tokens}
