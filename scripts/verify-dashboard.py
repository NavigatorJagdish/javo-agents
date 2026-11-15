"""Start an isolated real runtime and exercise the built dashboard in Chrome."""
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

repo = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix="javo-ui-") as folder:
    data = Path(folder)
    incoming = data / "incoming"
    incoming.mkdir()
    (incoming / "sample.txt").write_text("Original browser test media", encoding="utf-8")
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    env = os.environ.copy()
    env.update({
        "PYTHONPATH": str(repo / "services/local-runtime"),
        "JAVO_OWNER_ACCESS_TOKEN": secrets.token_urlsafe(32),
        "JAVO_DASHBOARD_DIST": str(repo / "apps/dashboard/dist"),
        "JAVO_CONTROL_STATE_PATH": str(data / "control.json"),
        "JAVO_PROVIDER_CONFIG_PATH": str(data / "providers.enc"),
        "JAVO_ENCRYPTION_KEY": secrets.token_urlsafe(48),
        "JAVO_DATABASE_URL": "sqlite+aiosqlite:///" + str(data / "runtime.db"),
        "JAVO_SCHEDULER_DB_URL": "sqlite:///" + str(data / "scheduler.db"),
        "JAVO_SMOKE_CONTENT": str(incoming),
        "JAVO_SMOKE_URL": f"http://127.0.0.1:{port}/dashboard/?apiBase=http://127.0.0.1:{port}",
    })
    for key in ["CONTENT_ROOT", "UPLOAD_DIR", "BACKUP_DIR", "THUMBNAIL_DIR"]:
        env["JAVO_" + key] = str(data / key.lower())
    with (data / "runtime.log").open("w", encoding="utf-8") as log:
        bundled = os.environ.get("JAVO_RUNTIME_EXE")
        command = ([str(Path(bundled).resolve()), "--port", str(port)] if bundled else
                   [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)])
        backend = subprocess.Popen(command, cwd=data, env=env, stdout=log, stderr=log)
        failed = True
        try:
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline:
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/auth/status", timeout=1):
                        break
                except OSError:
                    if backend.poll() is not None:
                        raise RuntimeError("Temporary backend failed to start")
                    time.sleep(0.25)
            else:
                raise TimeoutError("Temporary backend readiness timed out")
            result = subprocess.run(["node", str(repo / "scripts/dashboard-smoke.cjs")], env=env, timeout=90)
            if result.returncode:
                sys.exit(result.returncode)
            failed = False
        finally:
            if backend.poll() is None:
                backend.terminate()
            try:
                backend.wait(timeout=10)
            except subprocess.TimeoutExpired:
                backend.kill()
                backend.wait()
            if failed:
                log.flush()
                tail = (data / "runtime.log").read_text(encoding="utf-8", errors="replace")[-6000:]
                for key, value in env.items():
                    if any(marker in key.upper() for marker in ("TOKEN", "KEY", "SECRET")) and len(value) > 8:
                        tail = tail.replace(value, "[REDACTED]")
                print("ISOLATED_RUNTIME_FAILURE_LOG:\n" + tail, file=sys.stderr)
