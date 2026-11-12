"""Constrained AST + Subprocess Sandbox Runner for Javo Agents skills.

Security guarantees:
1. AST static inspection rejects dangerous builtins (`eval`, `exec`, `compile`,
   `__import__`, `globals`, `locals`) and unauthorized imports (`subprocess`,
   `os`, `socket`, `http`, `urllib`, `requests`, `ctypes`, `shutil`, etc.).
2. Permission enforcement aligns imported capabilities with `manifest.json`.
3. Subprocess execution uses a scrubbed environment (`env`) so host secrets
   (`JAVO_*`, `GEMINI_*`, `OPENAI_*`, `TELEGRAM_*`, tokens, keys) never leak.
4. Wall-clock timeout enforcement kills runaway skills cleanly.
5. Deterministic Trust Score calculator (0.0 to 1.0) evaluates skill safety.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
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
}

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


REPO_ROOT = Path(__file__).resolve().parents[2]
CORE_SKILLS_DIR = REPO_ROOT / "skills" / "core"

# Official Cryptographic Integrity Ledger for Built-in Core Skills
CORE_SKILL_PROVENANCE_LEDGER: dict[str, dict[str, Any]] = {
    "hindi-hinglish-hook-writer": {
        "id": "hindi-hinglish-hook-writer",
        "relative_dir": "hindi-hinglish-hook-writer",
        "allowed_permissions": {"pure:compute", "text:transform"},
        "entrypoint": "skill.py",
        "entrypoint_sha256": "e77d68f5a7f6e75f120f74d5b87a60f27db0bc1a987f566884d1702793c81b7a",
        "manifest_sha256": "86f26fcaaad4de1e3ee5c6b136cacecff4ea57ede34e618f4a6b80334f8d4aaf",
    },
    "social-caption-optimizer": {
        "id": "social-caption-optimizer",
        "relative_dir": "social-caption-optimizer",
        "allowed_permissions": {"pure:compute", "text:transform"},
        "entrypoint": "skill.py",
        "entrypoint_sha256": "318760f1444955f98673397287d9c0d17c2976984d1e9cdc23d6f725a68c3e40",
        "manifest_sha256": "23a435086fa241e98a7725f9b64bb0f6814c1e90291651a6de4638ac8f2f9a44",
    },
}


def verify_skill_provenance(skill_dir: Path, manifest: dict[str, Any]) -> tuple[bool, str]:
    """Verify that a skill claiming core_verified has genuine installation provenance and untampered cryptographic integrity."""
    skill_id = str(manifest.get("id") or "").strip()
    if skill_id not in CORE_SKILL_PROVENANCE_LEDGER:
        return False, f"Skill '{skill_id}' is not registered in the core provenance ledger; cannot claim core_verified"

    ledger = CORE_SKILL_PROVENANCE_LEDGER[skill_id]

    # 1. Provenance check: must reside inside canonical CORE_SKILLS_DIR
    try:
        rel_path = skill_dir.resolve().relative_to(CORE_SKILLS_DIR.resolve())
        if rel_path.parts[0] != ledger["relative_dir"]:
            return False, f"Skill directory '{skill_dir.name}' does not match expected core path '{ledger['relative_dir']}'"
    except (ValueError, IndexError):
        return False, f"Skill claiming 'core_verified' is located outside official core directory ({skill_dir})"

    # 2. Permission check: cannot exceed pinned core permissions
    requested_perms = set(manifest.get("permissions", []))
    if not requested_perms.issubset(ledger["allowed_permissions"]):
        excess = requested_perms - ledger["allowed_permissions"]
        return False, f"Manifest requests unpinned permissions for core skill: {excess}"

    # 3. Integrity check: manifest hash must match
    manifest_file = skill_dir / "manifest.json"
    if not manifest_file.exists():
        return False, "Missing manifest.json"
    actual_manifest_sha = compute_sha256(manifest_file)
    if not actual_manifest_sha.lower() == str(ledger["manifest_sha256"]).lower():
        return False, f"Core manifest SHA-256 integrity mismatch ({actual_manifest_sha} != {ledger['manifest_sha256']}): tampering detected"

    # 4. Integrity check: entrypoint file hash must match
    entrypoint = manifest.get("entrypoint", ledger["entrypoint"])
    skill_file = skill_dir / entrypoint
    if not skill_file.exists():
        return False, f"Missing entrypoint file {entrypoint}"
    actual_code_sha = compute_sha256(skill_file)
    if not actual_code_sha.lower() == str(ledger["entrypoint_sha256"]).lower():
        return False, f"Core skill code SHA-256 integrity mismatch ({actual_code_sha} != {ledger['entrypoint_sha256']}): tampering detected"

    return True, "verified"


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
            if node.attr.startswith("__") and node.attr in {"__subclasses__", "__globals__", "__builtins__", "__code__"}:
                violations.append(f"Forbidden dunder attribute access: {node.attr}")

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
    allow_untrusted: bool = False,
) -> SandboxResult:
    """Validate manifest, inspect AST, enforce trust tier, and execute skill in an isolated subprocess."""
    import time

    t0 = time.monotonic()
    manifest_path = skill_dir / "manifest.json"
    if not manifest_path.exists():
        return SandboxResult(success=False, error=f"Missing manifest.json in {skill_dir}")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return SandboxResult(success=False, error=f"Invalid manifest.json: {exc}")

    trust_tier = str(manifest.get("trust_tier", "untrusted")).lower()

    # Enforce genuine provenance and cryptographic integrity for any core_verified claim
    if trust_tier == "core_verified":
        is_valid_core, reason = verify_skill_provenance(skill_dir, manifest)
        if not is_valid_core:
            return SandboxResult(
                success=False,
                error=f"Provenance/integrity verification failed: {reason}",
                violations=[f"Core provenance violation: {reason}"],
                trust_score=0.0,
                duration_ms=0,
            )

    if not allow_untrusted and trust_tier != "core_verified":
        return SandboxResult(
            success=False,
            error=(
                f"Execution of untrusted plugin (trust_tier='{trust_tier}') is prohibited: "
                "OS-level container isolation is unavailable; only verified core skills with valid provenance may execute."
            ),
            violations=[f"Untrusted plugin blocked: trust_tier='{trust_tier}'"],
            trust_score=0.0,
            duration_ms=0,
        )

    entrypoint = manifest.get("entrypoint", "skill.py")
    handler = manifest.get("handler", "run")
    permissions = list(manifest.get("permissions", []))
    timeout_sec = float(manifest.get("timeout_seconds", 5.0))

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

    allow_net = "network:external" in permissions or "network:local_ollama" in permissions
    allow_fs_write = "filesystem:write" in permissions
    bootstrap = (
        "import builtins, importlib.util, json, os, socket, sys\n"
        f"if not {allow_net!r}:\n"
        "    def _no_net(*a, **kw): raise PermissionError('Network capability blocked by sandbox')\n"
        "    socket.socket = _no_net\n"
        f"if not {allow_fs_write!r}:\n"
        "    _orig_open = builtins.open\n"
        "    def _ro_open(file, mode='r', *a, **kw):\n"
        "        if any(m in str(mode) for m in ('w', 'a', 'x', '+')):\n"
        "            raise PermissionError('Filesystem write blocked by sandbox')\n"
        "        return _orig_open(file, mode, *a, **kw)\n"
        "    builtins.open = _ro_open\n"
        "os.system = lambda *a, **kw: (_ for _ in ()).throw(PermissionError('Process spawn blocked'))\n"
        "spec = importlib.util.spec_from_file_location('javo_skill', sys.argv[1])\n"
        "mod = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(mod)\n"
        "fn = getattr(mod, sys.argv[2])\n"
        "payload = json.loads(sys.stdin.read())\n"
        "result = fn(payload)\n"
        "sys.stdout.write(json.dumps(result, ensure_ascii=True))\n"
    )

    run_kwargs: dict[str, Any] = {}
    if os.name == "nt":
        run_kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)

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
            **run_kwargs,
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
