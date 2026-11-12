"""Reporting Agent — generates structured analytics reports and dashboard data aggregations."""

import logging
from typing import Any

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class ReportingAgent(BaseAgent):
    """Specialist agent that aggregates metrics into structured dashboard widgets and exportable reports."""

    name = "reporting_agent"
    display_name = "Reporting Agent"
    description = "Aggregates cross-platform engagement metrics, computes KPI totals, and builds dashboard report payloads."
    version = "1.0.0"
    capabilities = ["gather_analytics", "generate_report", "dashboard_aggregation"]
    required_permissions = ["read_analytics"]
    input_schema = {
        "required": ["action"],
        "properties": {
            "action": {"type": "string"},
            "records": {"type": "array"},
            "period": {"type": "string"},
            "format": {"type": "string"},
        },
    }
    output_schema = {"required": ["status", "totals"]}

    async def execute(self, task_data: dict) -> dict:
        records: list[dict[str, Any]] = task_data.get("records", [])
        period = task_data.get("period", "7d")
        export_format = task_data.get("format", "json")

        totals: dict[str, float] = {"impressions": 0, "engagements": 0, "clicks": 0, "followers_gained": 0}
        by_platform: dict[str, dict[str, float]] = {}

        for rec in records:
            platform = rec.get("platform", "general")
            bucket = by_platform.setdefault(platform, {"impressions": 0, "engagements": 0, "clicks": 0})
            for k in totals:
                val = float(rec.get(k, 0))
                totals[k] += val
                if k in bucket:
                    bucket[k] += val

        engagement_rate = (
            round((totals["engagements"] / totals["impressions"]) * 100, 2)
            if totals["impressions"] > 0 else 0.0
        )

        return {
            "status": "success",
            "period": period,
            "format": export_format,
            "totals": totals,
            "engagement_rate_pct": engagement_rate,
            "by_platform": by_platform,
            "record_count": len(records),
        }
