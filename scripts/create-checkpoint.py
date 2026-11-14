"""Create and restore-verify a source checkpoint. Does not upload or delete files."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BLOCKED_PARTS = {".git", "node_modules", ".venv", "__pycache__", ".pytest_cache"}
SECRET = re.compile(
    rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|"
    rb"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,}|"
    rb"AIza[A-Za-z0-9_-]{35}|sk-proj-[A-Za-z0-9_-]{30,})\b"
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--memory", type=Path)
    args = parser.parse_args()
    names = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT
    ).decode().split("\0")
    payload: dict[str, bytes] = {}
    for name in sorted(set(filter(None, names))):
        rel = Path(name)
        source = ROOT / rel
        if (source.is_symlink() or not source.resolve().is_relative_to(ROOT)
                or any(part in BLOCKED_PARTS for part in rel.parts)):
            raise ValueError(f"Unsafe source selection: {name}")
        if rel.name.startswith(".env") and rel.name not in {".env.example", ".env.sample"}:
            raise ValueError(f"Environment file cannot enter source backup: {name}")
        if rel.suffix.lower() in {".db", ".sqlite", ".sqlite3", ".pem", ".key", ".p12", ".keystore"}:
            raise ValueError(f"Private data cannot enter source backup: {name}")
        if not source.is_file():
            # Tracked deletions are represented by the working tree and patch.
            continue
        data = source.read_bytes()
        if SECRET.search(data):
            raise ValueError(f"Credential pattern in {name}; inspect before backing up")
        payload[f"source/{rel.as_posix()}"] = data
    if args.memory:
        data = args.memory.read_bytes()
        if SECRET.search(data):
            raise ValueError("Credential pattern in continuity document")
        payload["JAVO_PROJECT_MEMORY.md"] = data
    payload["working-changes.patch"] = subprocess.check_output(
        ["git", "-c", "core.autocrlf=false", "diff", "--binary", "HEAD"], cwd=ROOT
    )
    payload["RESTORE.txt"] = (
        "Extract this ZIP; source/ is the complete selected working source.\n"
        "Verify every SHA256 in MANIFEST.json before using it.\n"
        "Install dependencies and follow source/README.md and REBUILD_STATUS.md.\n"
        "This is an unfinished development checkpoint, not a tested installer.\n"
        "Credentials, owner data, node_modules, model files and caches are excluded.\n"
        "working-changes.patch covers tracked changes; source/ also includes new files.\n"
    ).encode()
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "local_base": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
        "files": {name: hashlib.sha256(data).hexdigest() for name, data in payload.items()},
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive = args.output_dir / f"JavoAgents-Checkpoint-{stamp}.zip"
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as bundle:
        for name, data in payload.items():
            bundle.writestr(name, data)
        bundle.writestr("MANIFEST.json", json.dumps(manifest, indent=2))
    with zipfile.ZipFile(archive) as bundle, tempfile.TemporaryDirectory(prefix="javo-restore-") as folder:
        if bundle.testzip() is not None:
            raise ValueError("ZIP integrity check failed")
        bundle.extractall(folder)
        for name, expected in manifest["files"].items():
            if hashlib.sha256((Path(folder) / name).read_bytes()).hexdigest() != expected:
                raise ValueError(f"Restore hash mismatch: {name}")
    receipt = {"file": str(archive.resolve()), "size": archive.stat().st_size,
               "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
               "md5": hashlib.md5(archive.read_bytes()).hexdigest(),
               "verified_files": len(payload), "restore_verified": True}
    archive.with_suffix(".receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
