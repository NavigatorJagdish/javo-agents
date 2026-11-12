"""Repository secret and static security hygiene scanner for Javo Agents."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

IGNORE_DIRS = {
    ".git",
    "node_modules",
    ".next",
    "out",
    "dist",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
    "release",
    "build",
}

SCAN_EXTS = {".py", ".ts", ".tsx", ".js", ".jsx", ".kt", ".kts", ".json", ".yml", ".yaml", ".md", ".ps1", ".env"}

SECRET_REGEXES = [
    ("OpenAI-style key", re.compile(r"\bsk-[A-Za-z0-9]{24,}\b")),
    ("Google/Gemini API key", re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b")),
    ("GitHub PAT", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("AWS Access Key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("PEM Private Key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
]

# Known synthetic test strings intentionally used in unit tests/firewall definitions
ALLOWLIST_SUBSTRINGS = {
    "AIzaSyDummyKey123456789012345678901234567",
    "AIzaSyDummyTestKey1234567890123456789012345",
    "sk-test-",
}


def scan_repo() -> int:
    findings: list[str] = []
    files_scanned = 0

    for path in ROOT.rglob("*"):
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        if not path.is_file():
            continue
        if path.name == ".env":
            findings.append(f"COMMITTED_ENV_FILE: {path.relative_to(ROOT)}")
            continue
        if path.suffix.lower() not in SCAN_EXTS and path.name != ".env.example":
            continue
        if path.resolve() == Path(__file__).resolve():
            continue

        files_scanned += 1
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for lineno, line in enumerate(text.splitlines(), start=1):
            if any(marker in line for marker in ALLOWLIST_SUBSTRINGS):
                continue
            for label, pattern in SECRET_REGEXES:
                if pattern.search(line):
                    findings.append(f"{label} at {path.relative_to(ROOT)}:{lineno}")

    print(f"Scanned {files_scanned} files across {ROOT}")
    if findings:
        for item in findings:
            print(f"FINDING: {item}", file=sys.stderr)
        return 1
    print("SECURITY_SCAN_OK: 0 leaked secrets or committed .env files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(scan_repo())
