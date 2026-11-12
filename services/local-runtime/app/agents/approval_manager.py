"""Approval Manager agent — routes items for approval and manages human-in-the-loop queues."""

import logging
import time
from typing import Any

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class ApprovalManagerAgent(BaseAgent):
    """Specialist agent managing Supervised Autopilot approval queues and risk policies."""

    name = "approval_manager"
    display_name = "Approval Manager"
    description = "Evaluates action risk levels, auto-approves safe low-risk tasks, and queues high-risk actions for user review."
    version = "1.0.0"
    capabilities = ["request_approval", "approval_workflow", "policy_evaluation"]
    required_permissions = ["manage_approvals"]
    input_schema = {
        "required": ["action"],
        "properties": {
            "action": {"type": "string"},
            "item_type": {"type": "string"},
            "item_id": {"type": "string"},
            "risk_level": {"type": "string"},
            "decision": {"type": "string"},
        },
    }
    output_schema = {"required": ["status"]}

    def __init__(self):
        super().__init__()
        self._queue: dict[str, dict[str, Any]] = {}

    async def execute(self, task_data: dict) -> dict:
        action = task_data.get("action", "request_approval")
        if action == "resolve":
            return self._resolve(task_data)
        if action == "list_pending":
            pending = [v for v in self._queue.values() if v["state"] == "pending"]
            return {"status": "success", "pending": pending, "count": len(pending)}
        return self._request_approval(task_data)

    def _request_approval(self, task_data: dict) -> dict:
        risk = task_data.get("risk_level", "low").lower()
        item_id = task_data.get("item_id", f"apr_{int(time.time())}")
        item_type = task_data.get("item_type", "task")

        if risk in {"low", "medium"}:
            return {
                "status": "success",
                "approved": True,
                "auto_approved": True,
                "item_id": item_id,
                "risk_level": risk,
            }

        record = {
            "item_id": item_id,
            "item_type": item_type,
            "risk_level": risk,
            "details": task_data.get("details", {}),
            "state": "pending",
            "created_at": time.time(),
        }
        self._queue[item_id] = record
        self.logger.info("Queued item %s (risk=%s) for human approval", item_id, risk)
        return {
            "status": "success",
            "approved": False,
            "auto_approved": False,
            "queued": True,
            "item_id": item_id,
        }

    def _resolve(self, task_data: dict) -> dict:
        item_id = task_data.get("item_id", "")
        decision = task_data.get("decision", "reject").lower()
        if item_id not in self._queue:
            return {"status": "error", "error": f"Approval item '{item_id}' not found"}
        approved = decision in {"approve", "approved", "yes"}
        self._queue[item_id]["state"] = "approved" if approved else "rejected"
        self._queue[item_id]["resolved_at"] = time.time()
        return {"status": "success", "item_id": item_id, "approved": approved, "state": self._queue[item_id]["state"]}
