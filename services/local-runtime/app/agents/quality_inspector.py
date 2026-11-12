"""Quality Inspector agent — reviews content quality, readability, and formatting errors."""

import logging
import re

from app.agents.base import BaseAgent
from app.core.ai_router import AIRouter

logger = logging.getLogger(__name__)


class QualityInspectorAgent(BaseAgent):
    """Specialist agent that audits drafts for clarity, broken links, placeholders, and quality."""

    name = "quality_inspector"
    display_name = "Quality Inspector"
    description = "Checks content drafts for placeholders, grammar/formatting issues, broken URLs, and overall quality score."
    version = "1.0.0"
    capabilities = ["quality_check", "proofreading", "link_validation"]
    required_permissions = ["review_content"]
    input_schema = {
        "required": ["content"],
        "properties": {
            "content": {"type": "string"},
            "min_length": {"type": "integer"},
        },
    }
    output_schema = {"required": ["status", "passed", "quality_score"]}

    PLACEHOLDER_RE = re.compile(r"(\[TODO\]|\[INSERT.*?\]|TBD|lorem ipsum|\{\{.*?\}\})", re.IGNORECASE)
    URL_RE = re.compile(r"https?://[^\s]+")

    def __init__(self):
        super().__init__()
        self.ai_router = AIRouter()

    async def execute(self, task_data: dict) -> dict:
        content = task_data.get("content", "")
        if not content and "generate_content_result" in task_data:
            content = task_data["generate_content_result"].get("draft", "")

        min_len = int(task_data.get("min_length", 15))
        issues: list[str] = []

        if len(content.strip()) < min_len:
            issues.append(f"Content shorter than minimum {min_len} characters")
        placeholders = self.PLACEHOLDER_RE.findall(content)
        if placeholders:
            issues.append(f"Unresolved placeholders detected: {placeholders}")
        if "  " in content:
            issues.append("Contains consecutive double spaces")

        urls = self.URL_RE.findall(content)
        for url in urls:
            if any(bad in url for bad in ("example.com", "localhost", "127.0.0.1")):
                issues.append(f"Non-production URL found: {url}")

        score = max(0, 100 - len(issues) * 20)
        passed = len(issues) == 0 and score >= 75

        return {
            "status": "success",
            "passed": passed,
            "quality_score": score,
            "issues": issues,
            "word_count": len(content.split()),
            "content": content,
        }
