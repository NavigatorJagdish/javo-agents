"""Publisher delegates to the same durable approval handler as the API."""
from fastapi import HTTPException
from app.agents.base import BaseAgent
from app import database
from app.services.publishing import dispatch_schedule


class ContentPublisherAgent(BaseAgent):
    name = "content_publisher"
    display_name = "Content Publisher"
    description = "Dispatches an explicitly approved persisted schedule."
    version = "2.0.0"
    capabilities = ["publish", "connector_dispatch"]
    required_permissions = ["publish_content", "use_connectors"]
    input_schema = {"required": ["schedule_id"], "properties": {
        "schedule_id": {"type": "string"}, "dry_run": {"type": "boolean"}}}
    output_schema = {"required": ["status", "published"]}

    async def execute(self, task_data: dict) -> dict:
        schedule_id = task_data.get("schedule_id")
        if not isinstance(schedule_id, str) or not schedule_id.strip():
            return {"status": "error", "published": False,
                    "error": "A persisted, approved schedule_id is required"}
        if task_data.get("dry_run"):
            return {"status": "preview", "published": False,
                    "schedule_id": schedule_id, "message": "No dispatch attempted"}
        if database.async_session_factory is None:
            database.init_engine()
        async with database.async_session_factory() as session:
            try:
                result = await dispatch_schedule(session, schedule_id)
            except HTTPException as exc:
                return {"status": "error", "published": False, "error": exc.detail}
        return {"status": result["status"], "published": False, "receipt": result}
