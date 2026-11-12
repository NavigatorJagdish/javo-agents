"""Base agent class for the Javo Agents framework."""

import logging
import time
import traceback
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all Javo specialist agents."""

    name: str = "base_agent"
    display_name: str = "Base Agent"
    description: str = "Abstract base agent"
    version: str = "1.0.0"
    capabilities: list[str] = []
    required_permissions: list[str] = []
    input_schema: dict[str, Any] = {}
    output_schema: dict[str, Any] = {}
    is_enabled: bool = True

    # Observability counters
    _total_executions: int = 0
    _total_errors: int = 0
    _total_tokens: int = 0
    _total_duration_ms: float = 0

    def __init__(self):
        self.logger = logging.getLogger(f"agent.{self.name}")

    @abstractmethod
    async def execute(self, task_data: dict) -> dict:
        """Execute the agent's primary task. Must be implemented by subclasses."""
        ...

    def validate_input(self, task_data: dict) -> tuple[bool, str | None]:
        """Validate task_data against input_schema. Returns (is_valid, error_msg)."""
        if not self.input_schema:
            return True, None
        required = self.input_schema.get("required", [])
        for field in required:
            if field not in task_data:
                return False, f"Missing required field: {field}"
        properties = self.input_schema.get("properties", {})
        for field, spec in properties.items():
            if field in task_data and "type" in spec:
                expected = spec["type"]
                type_map = {"string": str, "integer": int, "number": (int, float),
                            "boolean": bool, "array": list, "object": dict}
                if expected in type_map and not isinstance(task_data[field], type_map[expected]):
                    return False, f"Field '{field}' expected type {expected}"
        return True, None

    def validate_output(self, result: dict) -> tuple[bool, str | None]:
        """Validate result against output_schema. Returns (is_valid, error_msg)."""
        if not self.output_schema:
            return True, None
        required = self.output_schema.get("required", [])
        for field in required:
            if field not in result:
                return False, f"Missing required output field: {field}"
        return True, None

    def check_permissions(self, granted_permissions: list[str]) -> bool:
        """Check if all required permissions are granted."""
        return all(p in granted_permissions for p in self.required_permissions)

    def log_execution(self, task_data: dict, result: dict, duration_ms: float):
        """Log execution details for observability."""
        self.logger.info(
            "Agent %s executed in %.1fms | status=%s | tokens=%s",
            self.name,
            duration_ms,
            result.get("status", "unknown"),
            result.get("tokens_used", 0),
        )
        self._total_executions += 1
        self._total_duration_ms += duration_ms
        self._total_tokens += result.get("tokens_used", 0)

    def handle_error(self, error: Exception, task_data: dict) -> dict:
        """Standard error handling. Returns an error result dict."""
        self._total_errors += 1
        self.logger.error("Agent %s error: %s", self.name, str(error), exc_info=True)
        return {
            "status": "error",
            "agent": self.name,
            "error": str(error),
            "error_type": type(error).__name__,
            "traceback": traceback.format_exc(),
        }

    async def run(self, task_data: dict, granted_permissions: list[str] | None = None) -> dict:
        """Full execution pipeline with validation, timing, and error handling."""
        if not self.is_enabled:
            return {"status": "error", "agent": self.name, "error": "Agent is disabled"}

        if granted_permissions is not None and not self.check_permissions(granted_permissions):
            missing = [p for p in self.required_permissions if p not in granted_permissions]
            return {"status": "error", "agent": self.name, "error": f"Missing permissions: {missing}"}

        valid, err = self.validate_input(task_data)
        if not valid:
            return {"status": "error", "agent": self.name, "error": f"Input validation failed: {err}"}

        start = time.perf_counter()
        try:
            result = await self.execute(task_data)
        except Exception as exc:
            return self.handle_error(exc, task_data)

        duration_ms = (time.perf_counter() - start) * 1000
        result.setdefault("agent", self.name)
        result.setdefault("duration_ms", round(duration_ms, 2))
        self.log_execution(task_data, result, duration_ms)
        return result

    def get_stats(self) -> dict:
        """Return observability stats."""
        return {
            "agent": self.name,
            "total_executions": self._total_executions,
            "total_errors": self._total_errors,
            "total_tokens": self._total_tokens,
            "avg_duration_ms": round(self._total_duration_ms / max(self._total_executions, 1), 2),
        }

    def to_dict(self) -> dict:
        """Serialize agent metadata."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "version": self.version,
            "capabilities": self.capabilities,
            "required_permissions": self.required_permissions,
            "is_enabled": self.is_enabled,
        }

    async def ask_ai(
        self,
        ai_router: Any,
        prompt: str,
        *,
        system_prompt: str | None = None,
        provider: str | None = None,
        fallback: str = "",
    ) -> tuple[str, int]:
        """Call AIRouter.generate() safely, handling AIResponse dataclasses or dicts."""
        try:
            if hasattr(ai_router, "generate"):
                res = await ai_router.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    provider=provider,
                )
                if hasattr(res, "content"):
                    return str(res.content), int(getattr(res, "total_tokens", 0))
                if isinstance(res, dict):
                    return str(res.get("content", res.get("text", res))), int(
                        res.get("total_tokens", res.get("tokens_used", 0))
                    )
                return str(res), 0
        except Exception as exc:
            self.logger.warning("AI router fallback in %s: %s", self.name, exc)
        return fallback, 0
