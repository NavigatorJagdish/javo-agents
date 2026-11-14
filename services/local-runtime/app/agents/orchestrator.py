"""Master orchestrator agent for task decomposition and specialist coordination."""

import asyncio
import logging
from typing import Any

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)

# Risk levels for approval workflow
RISK_LOW = "low"
RISK_MEDIUM = "medium"
RISK_HIGH = "high"
RISK_CRITICAL = "critical"

AUTO_APPROVE_LEVELS = {RISK_LOW, RISK_MEDIUM}


class MasterAgent(BaseAgent):
    """Orchestrator that decomposes tasks, selects specialists, and manages workflows."""

    name = "orchestrator"
    display_name = "Master Orchestrator"
    description = "Receives tasks, decomposes them into subtasks, selects specialist agents, manages dependencies, handles approvals, and aggregates results."
    version = "1.0.0"
    capabilities = [
        "task_decomposition", "agent_selection", "dependency_management",
        "approval_workflow", "failure_recovery", "result_aggregation",
    ]
    required_permissions = ["orchestrate", "read_agents", "execute_agents"]
    input_schema = {
        "required": ["task_type"],
        "properties": {
            "task_type": {"type": "string"},
            "description": {"type": "string"},
            "parameters": {"type": "object"},
            "priority": {"type": "string"},
            "risk_level": {"type": "string"},
        },
    }
    output_schema = {
        "required": ["status"],
        "properties": {
            "status": {"type": "string"},
            "subtask_results": {"type": "array"},
        },
    }

    MAX_RETRIES = 2

    def __init__(self):
        super().__init__()
        self._registry: dict[str, BaseAgent] = {}

    def register_agent(self, agent: BaseAgent):
        """Register a specialist agent."""
        self._registry[agent.name] = agent
        self.logger.info("Registered agent: %s", agent.name)

    def get_agent(self, name: str) -> BaseAgent | None:
        agent = self._registry.get(name)
        if agent and agent.is_enabled:
            return agent
        return None

    def list_agents(self) -> list[dict]:
        return [a.to_dict() for a in self._registry.values()]

    # ── Task decomposition ──────────────────────────────────────────

    async def decompose_task(self, task_data: dict) -> list[dict]:
        """Break a complex task into ordered subtasks with dependencies."""
        task_type = task_data.get("task_type", "")
        params = task_data.get("parameters", {})

        # Mapping of composite task types to subtask sequences
        composite_map: dict[str, list[dict]] = {
            "publish_content": [
                {"task_type": "generate_content", "agent": "content_factory", "depends_on": []},
                {"task_type": "quality_check", "agent": "quality_inspector", "depends_on": ["generate_content"]},
                {"task_type": "brand_review", "agent": "brand_manager", "depends_on": ["quality_check"]},
                {"task_type": "publish", "agent": "content_publisher", "depends_on": ["brand_review"]},
            ],
            "weekly_report": [
                {"task_type": "gather_analytics", "agent": "reporting_agent", "depends_on": []},
                {"task_type": "analyze_trends", "agent": "weekly_analyst", "depends_on": ["gather_analytics"]},
                {"task_type": "growth_insights", "agent": "growth_scientist", "depends_on": ["gather_analytics"]},
                {"task_type": "compile_report", "agent": "weekly_analyst", "depends_on": ["analyze_trends", "growth_insights"]},
            ],
            "onboard_account": [
                {"task_type": "connect_api", "agent": "api_integration", "depends_on": []},
                {"task_type": "setup_brand", "agent": "brand_studio", "depends_on": ["connect_api"]},
                {"task_type": "compliance_check", "agent": "compliance_agent", "depends_on": ["connect_api"]},
                {"task_type": "configure_security", "agent": "account_guardian", "depends_on": ["compliance_check"]},
            ],
        }

        if task_type in composite_map:
            subtasks = []
            for st in composite_map[task_type]:
                subtasks.append({**st, "parameters": params, "risk_level": task_data.get("risk_level", RISK_LOW)})
            return subtasks

        # Single-agent task: find best match
        agent_name = self._select_agent_for_task(task_type)
        return [{"task_type": task_type, "agent": agent_name, "depends_on": [], "parameters": params,
                 "risk_level": task_data.get("risk_level", RISK_LOW)}]

    def _select_agent_for_task(self, task_type: str) -> str:
        """Select the best agent for a task type based on capabilities."""
        best_agent = None
        best_score = -1
        for agent in self._registry.values():
            if not agent.is_enabled:
                continue
            score = sum(1 for cap in agent.capabilities if cap in task_type or task_type in cap)
            # Direct name match gets a boost
            if task_type.replace("_", "") in agent.name.replace("_", ""):
                score += 10
            if score > best_score:
                best_score = score
                best_agent = agent.name
        return best_agent or "smart_memory"  # fallback

    # ── Approval workflow ───────────────────────────────────────────

    async def check_approval(self, subtask: dict) -> bool:
        """Return True if the subtask is approved to execute."""
        risk = subtask.get("risk_level", RISK_LOW)
        if risk in AUTO_APPROVE_LEVELS:
            self.logger.info("Auto-approved subtask %s (risk=%s)", subtask["task_type"], risk)
            return True
        # High/critical: delegate to approval_manager
        approval_agent = self.get_agent("approval_manager")
        if approval_agent:
            result = await approval_agent.run({
                "action": "request_approval",
                "item_type": "subtask",
                "item_id": subtask["task_type"],
                "risk_level": risk,
                "details": subtask,
            })
            return result.get("approved", False)
        self.logger.warning("No approval manager; holding %s", subtask["task_type"])
        return False

    # ── Execution with retry / fallback ─────────────────────────────

    async def _execute_subtask(self, subtask: dict, context: dict[str, Any]) -> dict:
        """Execute a single subtask with retry and fallback logic."""
        agent_name = subtask["agent"]
        task_payload = {**subtask.get("parameters", {}), "task_type": subtask["task_type"]}

        # Inject upstream results as context
        for dep in subtask.get("depends_on", []):
            if dep in context:
                task_payload[f"{dep}_result"] = context[dep]

        retry_limit = 1 if agent_name == "content_publisher" else self.MAX_RETRIES
        for attempt in range(1, retry_limit + 1):
            agent = self.get_agent(agent_name)
            if not agent:
                self.logger.error("Agent %s not found or disabled", agent_name)
                return {"status": "error", "error": f"Agent {agent_name} unavailable"}

            result = await agent.run(task_payload)
            if result.get("status") != "error":
                return result

            self.logger.warning("Subtask %s attempt %d failed: %s", subtask["task_type"], attempt, result.get("error"))
            if attempt < retry_limit:
                await asyncio.sleep(0.5 * attempt)

        if agent_name == "content_publisher":
            return result  # Never retry uncertain external writes via a recovery agent.

        # Fallback: try recovery_agent
        fallback = self.get_agent("recovery_agent")
        if fallback:
            self.logger.info("Falling back to recovery_agent for %s", subtask["task_type"])
            return await fallback.run({
                "action": "recover_subtask",
                "original_agent": agent_name,
                "task_data": task_payload,
                "last_error": result.get("error"),
            })
        return result

    # ── Main execute ────────────────────────────────────────────────

    async def execute(self, task_data: dict) -> dict:
        subtasks = await self.decompose_task(task_data)
        context: dict[str, Any] = {}
        results: list[dict] = []
        failed: list[str] = []

        # Build dependency graph layers
        remaining = list(subtasks)
        while remaining:
            ready = [s for s in remaining if all(d in context for d in s.get("depends_on", []))]
            if not ready:
                failed.extend(s["task_type"] for s in remaining)
                self.logger.error("Dependency deadlock for: %s", [s["task_type"] for s in remaining])
                break

            # Approval pass
            approved = []
            pending_approval = []
            for s in ready:
                if any(context[d].get("status") not in {"success", "completed"}
                       for d in s.get("depends_on", [])):
                    outcome = {"status": "blocked", "reason": "dependency_not_successful"}
                    context[s["task_type"]] = outcome
                    results.append({"task_type": s["task_type"], **outcome})
                    failed.append(s["task_type"])
                    continue
                if await self.check_approval(s):
                    approved.append(s)
                else:
                    pending_approval.append(s)
                    results.append({
                        "task_type": s["task_type"],
                        "status": "pending_approval",
                        "reason": "approval_required",
                    })

            if pending_approval:
                return {
                    "status": "pending_approval",
                    "subtask_results": results,
                    "pending_subtasks": [s["task_type"] for s in pending_approval],
                    "remaining_subtasks": remaining,
                    "failed_subtasks": failed,
                    "total_subtasks": len(subtasks),
                }

            # Execute approved subtasks in parallel
            coros = [self._execute_subtask(s, context) for s in approved]
            batch_results = await asyncio.gather(*coros, return_exceptions=True)

            for subtask, res in zip(approved, batch_results):
                if isinstance(res, Exception):
                    res = {"status": "error", "error": str(res)}
                context[subtask["task_type"]] = res
                results.append({"task_type": subtask["task_type"], **res})
                if res.get("status") == "error":
                    failed.append(subtask["task_type"])

            remaining = [s for s in remaining if s not in ready]

        overall_status = "success" if not failed else ("partial" if len(failed) < len(subtasks) else "error")
        return {
            "status": overall_status,
            "subtask_results": results,
            "failed_subtasks": failed,
            "total_subtasks": len(subtasks),
        }
