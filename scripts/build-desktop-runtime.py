"""Build and import-check the self-contained Windows runtime. No uploads."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "services" / "local-runtime"
OUTPUT = ROOT / "apps" / "windows" / "build" / "runtime"


def source_fingerprints() -> dict[str, str]:
    paths = sorted((RUNTIME / "app").rglob("*.py")) + [
        RUNTIME / name for name in ("desktop_entry.py", "pyproject.toml", "requirements.txt")
    ]
    return {p.relative_to(RUNTIME).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in paths}


def main() -> None:
    if sys.platform != "win32" or platform.machine().lower() not in {"amd64", "x86_64"}:
        raise SystemExit("Build the Windows x64 runtime using Windows x64 Python.")
    if importlib.util.find_spec("PyInstaller") is None:
        raise SystemExit("Install PyInstaller in the build environment first; see docs/WINDOWS_PACKAGING.md.")
    command = [
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
        "--onedir", "--console", "--name", "javo-runtime",
        "--distpath", str(OUTPUT), "--workpath", str(OUTPUT.parent / "pyinstaller-work"),
        "--specpath", str(OUTPUT.parent), "--paths", str(RUNTIME),
        "--collect-submodules", "app", "--collect-submodules", "apscheduler",
        "--copy-metadata", "apscheduler",
        "--hidden-import", "sqlalchemy.dialects.sqlite.aiosqlite",
        "--hidden-import", "aiosqlite",
        "--hidden-import", "sqlalchemy.dialects.sqlite.pysqlite",
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.loops.asyncio",
        "--hidden-import", "uvicorn.protocols.http.h11_impl",
        "--hidden-import", "uvicorn.protocols.websockets.websockets_impl",
        "--hidden-import", "uvicorn.lifespan.on",
        str(RUNTIME / "desktop_entry.py"),
    ]
    # Build hooks and the import check must never inherit owner credentials.
    env = {key: value for key, value in os.environ.items() if not key.startswith("JAVO_")}
    source_files = source_fingerprints()
    subprocess.run(command, cwd=ROOT, env=env, check=True)
    bundle = OUTPUT / "javo-runtime"
    # Invalidate previous verification before inspecting the newly built payload.
    manifest = bundle / "runtime-manifest.json"
    manifest.unlink(missing_ok=True)
    import tempfile
    with tempfile.TemporaryDirectory(prefix="javo-bundle-check-") as folder:
        result = subprocess.run([str(bundle / "javo-runtime.exe"), "--self-test"],
                                cwd=folder, env=env, check=True, capture_output=True,
                                text=True, timeout=60)
    evidence = json.loads(result.stdout.strip())
    if evidence.get("result") != "RUNTIME_IMPORTS_OK" or evidence.get("agents") != 30:
        raise SystemExit("Bundled runtime import check failed; no verified manifest written.")
    files = {p.relative_to(bundle).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(bundle.rglob("*")) if p.is_file()}
    if source_fingerprints() != source_files:
        raise SystemExit("Backend source changed during bundling; rebuild from stable source.")
    manifest.write_text(json.dumps({"schema": 1, "platform": "win32", "arch": "x64",
                                   "built_utc": datetime.now(timezone.utc).isoformat(),
                                   "self_test": evidence, "files": files,
                                   "source_files": source_files}, indent=2), encoding="utf-8")
    print(f"BUNDLED_RUNTIME_IMPORTS_OK: {len(files)} files; HTTP startup still requires testing.")


if __name__ == "__main__":
    main()
