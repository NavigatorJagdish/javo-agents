"""Goal Persistence agent — tracks long-term creator/business goals and updates milestones."""

import logging
from typing import Any

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class GoalPersistenceAgent(BaseAgent):
    """Specialist agent that tracks multi-week goals, computes milestone progress, and flags pacing risks."""

    name = "goal_persistence"
    display_name = "Goal Persistence"
    description = "Tracks long-term goals and milestones, calculates completion percentages, and recommends pacing adjustments."
    version = "1.0.0"
    capabilities = ["goal_tracking", "milestone_update", "pacing_analysis"]
    required_permissions = ["read_goals", "write_goals"]
    input_schema = {
        "required": ["goal_title"],
        "properties": {
            "goal_title": {"type": "string"},
            "milestones": {"type": "array"},
            "days_remaining": {"type": "integer"},
        },
    }
    output_schema = {"required": ["status", "overall_progress"]}

    async def execute(self, task_data: dict) -> dict:
        goal_title = task_data.get("goal_title", "Untitled Goal")
        milestones: list[dict[str, Any]] = task_data.get("milestones", [])
        days_remaining = int(task_data.get("days_remaining", 30))

        if not milestones:
            return {
                "status": "success",
                "goal_title": goal_title,
                "overall_progress": 0.0,
                "completed_milestones": 0,
                "total_milestones": 0,
                "pacing_status": "no_milestones",
            }

        progress_values = []
        completed_count = 0
        updated_milestones = []
        for ms in milestones:
            target = max(float(ms.get("target_value", 1)), 1e-6)
            current = float(ms.get("current_value", 0))
            pct = min(100.0, round((current / target) * 100, 2))
            is_done = bool(ms.get("is_completed", current >= target))
            if is_done:
                completed_count += 1
                pct = 100.0
            progress_values.append(pct)
            updated_milestones.append({**ms, "progress_pct": pct, "is_completed": is_done})

        overall = round(sum(progress_values) / len(progress_values), 2)
        pacing = "on_track"
        if overall < 50 and days_remaining <= 7:
            pacing = "at_risk"
        elif overall >= 100:
            pacing = "completed"

        return {
            "status": "success",
            "goal_title": goal_title,
            "overall_progress": overall,
            "completed_milestones": completed_count,
            "total_milestones": len(milestones),
            "pacing_status": pacing,
            "milestones": updated_milestones,
        }
