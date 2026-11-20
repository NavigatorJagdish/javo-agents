"""Reviewed built-in skill runner with AST checks and a subprocess deadline.

This is not an OS sandbox for downloaded Python. Only the two pinned original
built-ins can execute. AST/environment checks provide defense in depth; a trust
score does not prove arbitrary-code isolation. External/native tools stay in
separately configured runtimes and do not get execution through this runner.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import math
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ALWAYS_FORBIDDEN_CALLS = {
    "eval",
    "exec",
    "compile",
    "__import__",
    "breakpoint",
    "input",
    "globals",
    "locals",
    "vars",
    "getattr", "setattr", "delattr", "hasattr", "dir",
}

BUILTIN_SOURCES = {
    'social-caption-optimizer': 'e1db25209b827b4925201f786d48fcea968ea5697e7896574ac717513b5c13c8',
    'hindi-hinglish-hook-writer': 'e77d68f5a7f6e75f120f74d5b87a60f27db0bc1a987f566884d1702793c81b7a',
}


def _trusted_builtin(skill_dir: Path, source: str) -> bool:
    root = (Path(__file__).resolve().parents[1]/'core').resolve()
    directory = skill_dir.resolve()
    expected = BUILTIN_SOURCES.get(directory.name)
    return directory.parent == root and expected == hashlib.sha256(source.encode('utf-8')).hexdigest()

ALWAYS_FORBIDDEN_MODULES = {
    "subprocess",
    "os",
    "sys",
    "socket",
    "ctypes",
    "shutil",
    "importlib",
    "pickle",
    "marshal",
    "pty",
    "multiprocessing",
}

NETWORK_MODULES = {"urllib", "http", "requests", "httpx", "aiohttp", "websockets"}
FILESYSTEM_MODULES = {"pathlib", "io", "glob", "tempfile"}

SAFE_BASE_MODULES = {
    "__future__",
    "re",
    "json",
    "math",
    "datetime",
    "typing",
    "collections",
    "dataclasses",
    "enum",
    "functools",
    "itertools",
    "string",
    "unicodedata",
    "hashlib",
}

SENSITIVE_ENV_FRAGMENTS = (
    "KEY",
    "SECRET",
    "TOKEN",
    "PASSWORD",
    "PASS",
    "AUTH",
    "CREDENTIAL",
    "JAVO_",
    "GEMINI",
    "OPENAI",
    "TELEGRAM",
    "AWS_",
)


@dataclass
class SandboxResult:
    success: bool
    output: dict[str, Any] | None = None
    error: str | None = None
    violations: list[str] = field(default_factory=list)
    trust_score: float = 0.0
    duration_ms: int = 0


def compute_sha256(file_path: Path) -> str:
    return hashlib.sha256(file_path.read_bytes()).hexdigest()


def inspect_skill_ast(source_code: str, permissions: list[str]) -> list[str]:
    """Statically inspect Python AST against allowed modules and calls."""
    violations: list[str] = []
    try:
        tree = ast.parse(source_code)
    except SyntaxError as exc:
        return [f"SyntaxError: {exc}"]

    perm_set = set(permissions)
    allow_fs = "filesystem:read" in perm_set
    allow_net = "network:external" in perm_set or "network:local_ollama" in perm_set

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_mod = alias.name.split(".")[0]
                violations.extend(_check_module_allowed(root_mod, allow_fs, allow_net))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root_mod = node.module.split(".")[0]
                violations.extend(_check_module_allowed(root_mod, allow_fs, allow_net))
            if any(alias.name.startswith('_') or alias.name == '*' or alias.name in {'sys','os','builtins','codecs','subprocess','importlib'} for alias in node.names):
                violations.append('Forbidden indirect/private import')
        elif isinstance(node, ast.Name):
            if node.id in ALWAYS_FORBIDDEN_CALLS or (node.id.startswith('__') and node.id != '__name__') or (node.id == 'open' and not allow_fs):
                violations.append('Forbidden dynamic builtin reference: '+node.id)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in ALWAYS_FORBIDDEN_CALLS:
                    violations.append(f"Forbidden builtin call: {node.func.id}()")
                if node.func.id == "open" and not allow_fs:
                    violations.append("Forbidden builtin call: open() without filesystem:read permission")
            elif isinstance(node.func, ast.Attribute):
                if node.func.attr in {"system", "popen", "execv", "spawnl"}:
                    violations.append(f"Forbidden method call: .{node.func.attr}()")
        elif isinstance(node, ast.Attribute):
            if node.attr.startswith('_') or node.attr in {'sys','os','builtins','codecs','subprocess','importlib','environ','modules'}:
                violations.append(f"Forbidden private/runtime attribute access: {node.attr}")

    return violations


def _check_module_allowed(root_mod: str, allow_fs: bool, allow_net: bool) -> list[str]:
    if root_mod in SAFE_BASE_MODULES:
        return []
    if root_mod in ALWAYS_FORBIDDEN_MODULES:
        return [f"Forbidden module import: {root_mod}"]
    if root_mod in NETWORK_MODULES:
        if not allow_net:
            return [f"Network module '{root_mod}' requires network permission in manifest"]
        return []
    if root_mod in FILESYSTEM_MODULES:
        if not allow_fs:
            return [f"Filesystem module '{root_mod}' requires filesystem:read permission in manifest"]
        return []
    return [f"Unapproved module import: {root_mod}"]


def calculate_trust_score(
    manifest: dict[str, Any],
    ast_violations: list[str],
    checksum_verified: bool,
    tests_passed: bool = True,
) -> float:
    """Compute a deterministic trust score in [0.0, 1.0]."""
    if ast_violations:
        return 0.0

    score = 0.50
    tier = manifest.get("trust_tier", "experimental")
    if tier == "core_verified":
        score += 0.25
    elif tier == "community_reviewed":
        score += 0.15

    perms = set(manifest.get("permissions", []))
    if "network:external" not in perms and "filesystem:read" not in perms:
        score += 0.10
    elif "network:external" in perms:
        score -= 0.05

    if checksum_verified:
        score += 0.10
    if tests_passed:
        score += 0.05

    return round(max(0.0, min(1.0, score)), 2)


def build_sanitized_env() -> dict[str, str]:
    """Return a minimal environment dictionary with all credentials stripped."""
    safe_env: dict[str, str] = {}
    for k in ("SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "LANG", "LC_ALL"):
        if k in os.environ:
            safe_env[k] = os.environ[k]
    safe_env["PYTHONNOUSERSITE"] = "1"
    safe_env["PYTHONDONTWRITEBYTECODE"] = "1"
    safe_env["PYTHONIOENCODING"] = "utf-8"
    safe_env["PYTHONUTF8"] = "1"

    # Explicitly confirm no sensitive keys remain
    for key in list(safe_env.keys()):
        upper = key.upper()
        if any(frag in upper for frag in SENSITIVE_ENV_FRAGMENTS):
            safe_env.pop(key, None)
    return safe_env


def run_skill_sandboxed(
    skill_dir: Path,
    payload: dict[str, Any],
    verify_checksum: bool = True,
) -> SandboxResult:
    """Validate and run a pinned original built-in; reject downloaded Python."""
    import time

    t0 = time.monotonic()
    manifest_path = skill_dir / "manifest.json"
    if not manifest_path.exists():
        return SandboxResult(success=False, error=f"Missing manifest.json in {skill_dir}")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return SandboxResult(success=False, error=f"Invalid manifest.json: {exc}")

    entrypoint = manifest.get("entrypoint", "skill.py")
    handler = manifest.get("handler", "run")
    permissions = list(manifest.get("permissions", []))
    timeout_sec = float(manifest.get("timeout_seconds", 5.0))
    if not math.isfinite(timeout_sec) or not 0.05 <= timeout_sec <= 30:
        return SandboxResult(success=False, error='Skill deadline must be finite and between0.05 and30seconds')

    skill_file = (skill_dir / entrypoint).resolve()
    if not skill_file.exists() or skill_dir.resolve() not in skill_file.parents:
        return SandboxResult(success=False, error=f"Invalid entrypoint path: {entrypoint}")

    expected_sha = manifest.get("sha256")
    actual_sha = compute_sha256(skill_file)
    checksum_verified = bool(expected_sha and expected_sha.lower() == actual_sha.lower())
    if verify_checksum and expected_sha and not checksum_verified:
        return SandboxResult(
            success=False,
            error="Skill SHA-256 checksum mismatch",
            violations=["Checksum verification failed"],
            trust_score=0.0,
        )

    source_code = skill_file.read_text(encoding="utf-8")
    violations = inspect_skill_ast(source_code, permissions)
    if violations:
        return SandboxResult(
            success=False,
            error="AST security inspection failed",
            violations=violations,
            trust_score=0.0,
        )

    if not _trusted_builtin(skill_dir, source_code) or set(permissions) - {'pure:compute', 'text:transform'}:
        return SandboxResult(success=False,
            error='External, modified or privileged skill execution requires real OS isolation; this runner permits only reviewed pinned built-ins.',
            trust_score=0.0)

    bootstrap = (
        "import importlib.util, json, sys\n"
        "spec = importlib.util.spec_from_file_location('javo_skill', sys.argv[1])\n"
        "mod = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(mod)\n"
        "fn = getattr(mod, sys.argv[2])\n"
        "payload = json.loads(sys.stdin.read())\n"
        "result = fn(payload)\n"
        "sys.stdout.write(json.dumps(result, ensure_ascii=True))\n"
    )

    try:
        proc = subprocess.run(
            [sys.executable, "-I", "-c", bootstrap, str(skill_file), handler],
            input=json.dumps(payload, ensure_ascii=True),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout_sec,
            env=build_sanitized_env(),
            cwd=str(skill_dir),
        )
    except subprocess.TimeoutExpired:
        elapsed = int((time.monotonic() - t0) * 1000)
        return SandboxResult(
            success=False,
            error=f"Skill execution timed out after {timeout_sec}s",
            trust_score=0.0,
            duration_ms=elapsed,
        )

    elapsed = int((time.monotonic() - t0) * 1000)
    if proc.returncode != 0:
        return SandboxResult(
            success=False,
            error=proc.stderr.strip() or f"Skill exited with code {proc.returncode}",
            trust_score=calculate_trust_score(manifest, violations, checksum_verified, tests_passed=False),
            duration_ms=elapsed,
        )

    try:
        output = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return SandboxResult(
            success=False,
            error=f"Skill returned invalid JSON: {exc}",
            trust_score=0.0,
            duration_ms=elapsed,
        )

    trust = calculate_trust_score(manifest, violations, checksum_verified, tests_passed=True)
    return SandboxResult(
        success=True,
        output=output,
        trust_score=trust,
        duration_ms=elapsed,
    )
