"""Resource Optimizer agent — monitors CPU/RAM/model usage and optimizes allocations."""

import logging
import os
from typing import Any

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class ResourceOptimizerAgent(BaseAgent):
    """Specialist agent for hardware resource monitoring and local AI model allocation."""

    name = "resource_optimizer"
    display_name = "Resource Optimizer"
    description = "Monitors CPU, RAM, and queue depth to recommend model quantization and worker concurrency limits."
    version = "1.0.0"
    capabilities = ["resource_monitoring", "model_allocation", "concurrency_tuning"]
    required_permissions = ["read_system_metrics", "manage_resources"]
    input_schema = {
        "required": ["action"],
        "properties": {
            "action": {"type": "string"},
            "ram_total_gb": {"type": "number"},
            "ram_used_pct": {"type": "number"},
            "cpu_pct": {"type": "number"},
            "queue_depth": {"type": "integer"},
        },
    }
    output_schema = {"required": ["status", "profile"]}

    async def execute(self, task_data: dict) -> dict:
        ram_total_gb = float(task_data.get("ram_total_gb", 8.0))
        ram_used_pct = float(task_data.get("ram_used_pct", 55.0))
        cpu_pct = float(task_data.get("cpu_pct", 35.0))
        queue_depth = int(task_data.get("queue_depth", 0))

        if ram_total_gb <= 8.5:
            tier = "8gb_constrained"
            recommended_model = "qwen2.5:3b-instruct-q4_K_M"
            max_concurrent_agents = 2
        elif ram_total_gb <= 16.5:
            tier = "16gb_balanced"
            recommended_model = "llama3.1:8b-instruct-q4_K_M"
            max_concurrent_agents = 4
        else:
            tier = "32gb_performance"
            recommended_model = "qwen2.5:14b-instruct-q4_K_M"
            max_concurrent_agents = 6

        actions: list[str] = []
        if ram_used_pct > 82:
            actions.append("unload_idle_models")
            max_concurrent_agents = 1
        if cpu_pct > 85:
            actions.append("defer_background_analytics")
        if queue_depth > 10:
            actions.append("batch_low_priority_tasks")

        profile: dict[str, Any] = {
            "hardware_tier": tier,
            "cpu_cores": os.cpu_count() or 2,
            "recommended_local_model": recommended_model,
            "max_concurrent_agents": max_concurrent_agents,
            "recommended_actions": actions,
        }
        return {"status": "success", "profile": profile}
