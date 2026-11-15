"""Report the actual owner-scoped goal snapshot; never infer invented progress."""

from app.agents.base import BaseAgent


class GoalPersistenceAgent(BaseAgent):
    name = "goal_persistence"
    display_name = "Goal Persistence"
    description = "Reads saved objectives, evidence and milestone progress from the local database."
    version = "1.1.0"
    capabilities = ["goal_tracking"]
    required_permissions = ["read_goals"]
    input_schema = {
        "required": ["goal_id"],
        "properties": {"goal_id": {"type": "string"}, "action": {"type": "string"}},
    }
    output_schema = {"required": ["status", "goal"]}

    async def execute(self, task_data: dict) -> dict:
        if task_data.get("action", "summary") != "summary":
            raise ValueError("Only saved goal summaries are supported")
        if set(task_data) - {"goal_id", "action"}:
            raise ValueError("Goal summary accepts only a saved goal ID and action")
        from app import database as db
        from app.api.routes.goals import get_goal

        if db.async_session_factory is None:
            raise RuntimeError("Runtime database is unavailable")
        async with db.async_session_factory() as session:
            goal = await get_goal(task_data["goal_id"], session)
        return {
            "status": "success",
            "goal": goal.model_dump(mode="json"),
            "message": "Saved owner-reported evidence; no live analytics or automatic experiments were generated.",
        }
