"""Device Sync Agent — synchronizes state, approvals, and summaries across paired devices."""

import logging
import time
from typing import Any

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class DeviceSyncAgent(BaseAgent):
    """Specialist agent that reconciles paired desktop/mobile state and builds delta sync payloads."""

    name = "device_sync_agent"
    display_name = "Device Sync Agent"
    description = "Computes state deltas between the Windows local runtime and paired Android/mobile devices."
    version = "1.0.0"
    capabilities = ["device_sync", "delta_reconciliation", "pairing_check"]
    required_permissions = ["read_devices", "sync_devices"]
    input_schema = {
        "required": ["device_id"],
        "properties": {
            "device_id": {"type": "string"},
            "last_sync_ts": {"type": "number"},
            "pending_events": {"type": "array"},
            "is_trusted": {"type": "boolean"},
        },
    }
    output_schema = {"required": ["status", "synced"]}

    async def execute(self, task_data: dict) -> dict:
        device_id = task_data.get("device_id", "")
        if not device_id:
            return {"status": "error", "synced": False, "error": "device_id is required"}

        if not task_data.get("is_trusted", True):
            return {"status": "error", "synced": False, "error": f"Device '{device_id}' is not trusted"}

        last_sync = float(task_data.get("last_sync_ts", 0))
        events: list[dict[str, Any]] = task_data.get("pending_events", [])
        delta = [ev for ev in events if float(ev.get("timestamp", time.time())) > last_sync]

        now = time.time()
        return {
            "status": "success",
            "synced": True,
            "device_id": device_id,
            "delta_count": len(delta),
            "delta_events": delta,
            "sync_timestamp": now,
        }
