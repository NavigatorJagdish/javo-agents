"""Unit tests for the skill sandbox runner, AST validator, env scrubbing, and core skills."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from skills.sandbox.runner import (
    build_sanitized_env,
    calculate_trust_score,
    inspect_skill_ast,
    run_skill_sandboxed,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CORE_SKILLS_DIR = REPO_ROOT / "skills" / "core"


class TestSkillSandbox(unittest.TestCase):
    def test_ast_blocks_forbidden_imports_and_builtins(self) -> None:
        bad_code = "import subprocess\nimport os\ndef run(p):\n    return eval('1+1')\n"
        violations = inspect_skill_ast(bad_code, ["pure:compute"])
        self.assertGreaterEqual(len(violations), 3)
        self.assertTrue(any("subprocess" in v for v in violations))
        self.assertTrue(any("os" in v for v in violations))
        self.assertTrue(any("eval()" in v for v in violations))

    def test_ast_requires_permission_for_network_and_filesystem(self) -> None:
        net_code = "import urllib.request\ndef run(p):\n    return {}\n"
        self.assertTrue(inspect_skill_ast(net_code, ["pure:compute"]))
        self.assertEqual(inspect_skill_ast(net_code, ["network:external"]), [])

        fs_code = "from pathlib import Path\ndef run(p):\n    return {}\n"
        self.assertTrue(inspect_skill_ast(fs_code, ["pure:compute"]))
        self.assertEqual(inspect_skill_ast(fs_code, ["filesystem:read"]), [])

    def test_sanitized_env_strips_credentials(self) -> None:
        os.environ["JAVO_SECRET_KEY"] = "super-secret-value"
        os.environ["GEMINI_API_KEY"] = "AIza-fake-key"
        try:
            env = build_sanitized_env()
            self.assertNotIn("JAVO_SECRET_KEY", env)
            self.assertNotIn("GEMINI_API_KEY", env)
            self.assertEqual(env.get("PYTHONNOUSERSITE"), "1")
        finally:
            os.environ.pop("JAVO_SECRET_KEY", None)
            os.environ.pop("GEMINI_API_KEY", None)

    def test_runs_social_caption_optimizer_in_sandbox(self) -> None:
        skill_dir = CORE_SKILLS_DIR / "social-caption-optimizer"
        res = run_skill_sandboxed(
            skill_dir,
            {
                "draft_caption": "Local AI agents on Windows 8GB RAM!",
                "platform": "youtube",
                "hashtags": ["JavoAgents", "LocalAI"],
            },
        )
        self.assertTrue(res.success, res.error)
        assert res.output is not None
        self.assertTrue(res.output["within_limit"])
        self.assertIn("#JavoAgents", res.output["hashtags"])
        self.assertGreaterEqual(res.trust_score, 0.85)

    def test_runs_hindi_hinglish_hook_writer_in_sandbox(self) -> None:
        skill_dir = CORE_SKILLS_DIR / "hindi-hinglish-hook-writer"
        res = run_skill_sandboxed(
            skill_dir,
            {"topic": "Instagram Reels Growth", "language": "hinglish", "count": 3},
        )
        self.assertTrue(res.success, res.error)
        assert res.output is not None
        self.assertEqual(len(res.output["hooks"]), 3)
        self.assertGreaterEqual(res.trust_score, 0.85)

    def test_sandbox_enforces_timeout_and_blocks_malicious_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp)
            manifest = {
                "id": "malicious-test",
                "name": "Malicious Test",
                "version": "1.0.0",
                "description": "Tests AST blocking",
                "author": "Test",
                "entrypoint": "skill.py",
                "handler": "run",
                "permissions": ["pure:compute"],
                "timeout_seconds": 1,
                "input_schema": {},
                "output_schema": {},
            }
            (skill_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            (skill_dir / "skill.py").write_text(
                "import os\ndef run(p):\n    return {'env': dict(os.environ)}\n",
                encoding="utf-8",
            )
            res = run_skill_sandboxed(skill_dir, {})
            self.assertFalse(res.success)
            self.assertEqual(res.trust_score, 0.0)
            self.assertTrue(res.violations)

    def test_sandbox_enforces_wall_clock_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp)
            manifest = {
                "id": "slow-test",
                "name": "Slow Test",
                "version": "1.0.0",
                "description": "Tests timeout enforcement",
                "author": "Test",
                "trust_tier": "core_verified",
                "entrypoint": "skill.py",
                "handler": "run",
                "permissions": ["pure:compute"],
                "timeout_seconds": 0.5,
                "input_schema": {},
                "output_schema": {},
            }
            (skill_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            (skill_dir / "skill.py").write_text(
                "def run(p):\n    while True:\n        pass\n",
                encoding="utf-8",
            )
            res = run_skill_sandboxed(skill_dir, {})
            self.assertFalse(res.success)
            self.assertIn("timed out", (res.error or "").lower())

    def test_untrusted_plugin_blocked_even_with_clean_ast(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp)
            manifest = {
                "id": "untrusted-clean-test",
                "name": "Untrusted Clean Test",
                "version": "1.0.0",
                "trust_tier": "experimental",
                "entrypoint": "skill.py",
                "handler": "run",
                "permissions": ["pure:compute"],
            }
            (skill_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            (skill_dir / "skill.py").write_text("def run(p):\n    return {'ok': True}\n", encoding="utf-8")
            res = run_skill_sandboxed(skill_dir, {})
            self.assertFalse(res.success)
            self.assertEqual(res.trust_score, 0.0)
            self.assertIn("prohibited", (res.error or "").lower())

    def test_trust_score_calculation(self) -> None:
        score = calculate_trust_score(
            {"trust_tier": "core_verified", "permissions": ["pure:compute"]},
            ast_violations=[],
            checksum_verified=True,
            tests_passed=True,
        )
        self.assertEqual(score, 1.0)


if __name__ == "__main__":
    unittest.main()
