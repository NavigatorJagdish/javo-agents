"""Two independent runtime lifecycles prove persisted stop across process restart."""
import os
from pathlib import Path
import secrets
import subprocess
import sys


def test_emergency_stop_survives_process_restart(tmp_path):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2] / "services" / "local-runtime")
    env["JAVO_OWNER_ACCESS_TOKEN"] = secrets.token_urlsafe(32)
    env["JAVO_DATABASE_URL"] = "sqlite+aiosqlite:///" + str(tmp_path / "runtime.db")
    env["JAVO_SCHEDULER_DB_URL"] = "sqlite:///" + str(tmp_path / "scheduler.db")
    env["JAVO_CONTROL_STATE_PATH"] = str(tmp_path / "control.json")
    for name in ["CONTENT_ROOT", "UPLOAD_DIR", "BACKUP_DIR", "THUMBNAIL_DIR"]:
        env["JAVO_" + name] = str(tmp_path / name.lower())
    script = '''
import os, sys
from fastapi.testclient import TestClient
from app.main import create_app
from app.core.scheduler import scheduler
with TestClient(create_app(), headers={"Authorization": "Bearer " + os.environ["JAVO_OWNER_ACCESS_TOKEN"]}) as client:
    if sys.argv[1] == "stop":
        assert client.post("/security/resume").status_code == 200
        assert client.post("/security/emergency-stop").status_code == 200
    status = client.get("/security/autopilot-status")
    assert status.status_code == 200
    assert status.json()["paused"] is True
    assert status.json()["emergency_stopped"] is True
    assert scheduler._scheduler.state == 2
print("RESTART_STATE_OK")
'''
    for phase in ["stop", "restore"]:
        result = subprocess.run([sys.executable, "-c", script, phase], env=env,
                                capture_output=True, text=True, timeout=60)
        assert result.returncode == 0, result.stderr
        assert "RESTART_STATE_OK" in result.stdout
