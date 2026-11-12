"""Plugin Trust agent — verifies skill/plugin manifests, AST safety, and computes trust scores."""

import ast
import logging
from typing import Any

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class PluginTrustAgent(BaseAgent):
    """Specialist agent for auditing third-party or self-upgraded skills and managing trust scores."""

    name = "plugin_trust"
    display_name = "Plugin Trust Verifier"
    description = "Verifies skill manifests, scans Python skill code for unsafe imports/calls, and maintains trust scores."
    version = "1.0.0"
    capabilities = ["verify_plugin", "ast_security_scan", "trust_scoring"]
    required_permissions = ["audit_plugins"]
    input_schema = {
        "required": ["plugin_name"],
        "properties": {
            "plugin_name": {"type": "string"},
            "source_code": {"type": "string"},
            "manifest": {"type": "object"},
        },
    }
    output_schema = {"required": ["status", "trusted", "trust_score"]}

    BLOCKED_IMPORTS = {"subprocess", "ctypes", "socket", "shutil"}
    BLOCKED_CALLS = {"eval", "exec", "__import__", "compile"}

    async def execute(self, task_data: dict) -> dict:
        plugin_name = task_data.get("plugin_name", "unknown")
        source_code = task_data.get("source_code", "")
        manifest: dict[str, Any] = task_data.get("manifest", {})

        findings: list[str] = []
        if not manifest.get("name") or not manifest.get("version"):
            findings.append("Manifest missing required 'name' or 'version'")

        if source_code:
            findings.extend(self._scan_ast(source_code))

        trust_score = max(0, 100 - len(findings) * 30)
        trusted = len(findings) == 0 and trust_score >= 80
        return {
            "status": "success",
            "plugin_name": plugin_name,
            "trusted": trusted,
            "trust_score": trust_score,
            "findings": findings,
        }

    def _scan_ast(self, source_code: str) -> list[str]:
        issues: list[str] = []
        try:
            tree = ast.parse(source_code)
        except SyntaxError as exc:
            return [f"SyntaxError in plugin code: {exc}"]

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    if root in self.BLOCKED_IMPORTS:
                        issues.append(f"Blocked import: '{root}'")
            elif isinstance(node, ast.ImportFrom) and node.module:
                root = node.module.split(".")[0]
                if root in self.BLOCKED_IMPORTS:
                    issues.append(f"Blocked import-from: '{root}'")
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in self.BLOCKED_CALLS:
                    issues.append(f"Blocked dynamic call: '{node.func.id}()'")
        return issues
