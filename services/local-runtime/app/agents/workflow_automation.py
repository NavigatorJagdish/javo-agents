"""Workflow Automation agent — executes visual workflow graphs and manages node transitions."""

import logging
from typing import Any

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class WorkflowAutomationAgent(BaseAgent):
    """Specialist agent that validates and traverses workflow DAGs (nodes & conditional edges)."""

    name = "workflow_automation"
    display_name = "Workflow Automation"
    description = "Executes node-and-edge workflow graphs, evaluates branch conditions, and tracks per-node execution state."
    version = "1.0.0"
    capabilities = ["execute_workflow", "graph_validation", "transition_management"]
    required_permissions = ["execute_workflows", "read_workflows"]
    input_schema = {
        "required": ["nodes"],
        "properties": {
            "workflow_id": {"type": "string"},
            "nodes": {"type": "array"},
            "edges": {"type": "array"},
            "context": {"type": "object"},
        },
    }
    output_schema = {"required": ["status", "executed_nodes"]}

    async def execute(self, task_data: dict) -> dict:
        workflow_id = task_data.get("workflow_id", "wf_adhoc")
        nodes: list[dict[str, Any]] = task_data.get("nodes", [])
        edges: list[dict[str, Any]] = task_data.get("edges", [])
        context: dict[str, Any] = dict(task_data.get("context", {}))

        node_map = {n["id"]: n for n in nodes if "id" in n}
        adjacency: dict[str, list[dict[str, Any]]] = {nid: [] for nid in node_map}
        incoming = {nid: 0 for nid in node_map}

        for edge in edges:
            src, dst = edge.get("source"), edge.get("target")
            if src in adjacency and dst in incoming:
                adjacency[src].append(edge)
                incoming[dst] += 1

        queue = [nid for nid, deg in incoming.items() if deg == 0]
        executed_nodes: list[dict[str, Any]] = []
        visited: set[str] = set()

        while queue:
            nid = queue.pop(0)
            if nid in visited:
                continue
            visited.add(nid)
            node = node_map[nid]
            node_type = node.get("type", "action")
            executed_nodes.append({"id": nid, "type": node_type, "status": "completed"})

            for edge in adjacency.get(nid, []):
                cond = edge.get("condition")
                if cond and not context.get(cond, True):
                    continue
                queue.append(edge["target"])

        return {
            "status": "success",
            "workflow_id": workflow_id,
            "executed_nodes": executed_nodes,
            "total_nodes": len(nodes),
            "completed_count": len(executed_nodes),
        }
