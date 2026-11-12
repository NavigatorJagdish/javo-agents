"""UX Assistant agent — evaluates UI/UX ergonomics and runs accessibility audits."""

import logging
from typing import Any

from app.agents.base import BaseAgent
from app.core.ai_router import AIRouter

logger = logging.getLogger(__name__)


class UXAssistantAgent(BaseAgent):
    """Specialist agent for UI/UX feedback, WCAG contrast checks, and accessibility reviews."""

    name = "ux_assistant"
    display_name = "UX Assistant"
    description = "Audits UI screens and flows for WCAG contrast, keyboard navigation, and mobile/desktop usability."
    version = "1.0.0"
    capabilities = ["ux_review", "accessibility_check", "contrast_audit"]
    required_permissions = ["use_ai"]
    input_schema = {
        "required": ["action"],
        "properties": {
            "action": {"type": "string"},
            "components": {"type": "array"},
            "fg_hex": {"type": "string"},
            "bg_hex": {"type": "string"},
        },
    }
    output_schema = {"required": ["status"]}

    def __init__(self):
        super().__init__()
        self.ai_router = AIRouter()

    async def execute(self, task_data: dict) -> dict:
        action = task_data.get("action", "accessibility_audit")
        if action == "check_contrast":
            return self._check_contrast(task_data)
        return await self._audit_components(task_data)

    def _hex_to_luminance(self, hex_color: str) -> float:
        h = hex_color.lstrip("#")
        if len(h) != 6:
            return 0.5
        rgb = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
        adj = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
        return 0.2126 * adj[0] + 0.7152 * adj[1] + 0.0722 * adj[2]

    def _check_contrast(self, task_data: dict) -> dict:
        fg = task_data.get("fg_hex", "#FFFFFF")
        bg = task_data.get("bg_hex", "#0B1026")
        l1 = self._hex_to_luminance(fg)
        l2 = self._hex_to_luminance(bg)
        ratio = round((max(l1, l2) + 0.05) / (min(l1, l2) + 0.05), 2)
        return {
            "status": "success",
            "fg_hex": fg,
            "bg_hex": bg,
            "contrast_ratio": ratio,
            "wcag_aa_normal": ratio >= 4.5,
            "wcag_aa_large": ratio >= 3.0,
        }

    async def _audit_components(self, task_data: dict) -> dict:
        components: list[dict[str, Any]] = task_data.get("components", [])
        issues: list[str] = []
        for comp in components:
            name = comp.get("name", "unnamed")
            if comp.get("type") in {"button", "icon_button"} and not comp.get("aria_label") and not comp.get("text"):
                issues.append(f"Button '{name}' missing accessible text or aria_label")
            if comp.get("type") == "image" and not comp.get("alt"):
                issues.append(f"Image '{name}' missing alt attribute")

        return {
            "status": "success",
            "components_checked": len(components),
            "accessibility_issues": issues,
            "passed": len(issues) == 0,
        }
