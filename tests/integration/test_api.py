"""Integration tests for FastAPI application endpoints and lifecycle."""

from __future__ import annotations

import secrets
import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    token = secrets.token_urlsafe(32)
    monkeypatch.setenv("JAVO_OWNER_ACCESS_TOKEN", token)
    monkeypatch.setenv("JAVO_CONTROL_STATE_PATH", str(tmp_path / "control.json"))
    import app.core.resource_manager as resources
    resources._resource_manager = None
    db_path = tmp_path / "integration_test.db"
    sched_path = tmp_path / "integration_sched.db"
    monkeypatch.setenv("JAVO_DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setenv("JAVO_SCHEDULER_DB_URL", f"sqlite:///{sched_path}")
    monkeypatch.setenv("JAVO_CONTENT_ROOT", str(tmp_path / "content"))
    monkeypatch.setenv("JAVO_UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("JAVO_BACKUP_DIR", str(tmp_path / "backups"))
    monkeypatch.setenv("JAVO_THUMBNAIL_DIR", str(tmp_path / "thumbnails"))

    import app.config as cfg
    cfg._settings = None

    app = create_app()
    with TestClient(app, headers={"Authorization": f"Bearer {token}"}) as test_client:
        yield test_client

    cfg._settings = None


def test_root_and_health_endpoints(client: TestClient):
    r_root = client.get("/")
    assert r_root.status_code == 200
    assert r_root.json()["status"] == "running"

    r_health = client.get("/health/")
    assert r_health.status_code == 200
    body = r_health.json()
    assert body["status"] == "healthy"
    assert body["database"] == "connected"

    r_diag = client.get("/health/diagnostics")
    assert r_diag.status_code == 200
    assert r_diag.json()["overall"] == "healthy"


def test_agents_seeded_and_task_crud(client: TestClient):
    r_agents = client.get("/agents/")
    assert r_agents.status_code == 200
    agents = r_agents.json()
    assert len(agents) == 30

    # Create a task
    r_create = client.post(
        "/tasks/",
        json={
            "title": "Draft launch announcement",
            "assigned_agent": "content_factory",
            "priority": "high",
            "inputs": {"topic": "Javo Agents v1"},
        },
    )
    assert r_create.status_code in (200, 201)
    task = r_create.json()
    task_id = task["task_id"]

    # Fetch task list
    r_list = client.get("/tasks/")
    assert r_list.status_code == 200
    assert any(t["task_id"] == task_id for t in r_list.json())


def test_workflow_crud_and_execution(client: TestClient):
    r_wf = client.post(
        "/workflows/",
        json={
            "name": "Daily Reel Pipeline",
            "description": "Scan ready folder, draft caption, require approval",
            "nodes": [
                {
                    "id": "n1",
                    "node_type": "folder_watcher",
                    "label": "Watch Ready",
                    "is_entry_point": True,
                },
                {
                    "id": "n2",
                    "node_type": "approval",
                    "label": "Human Approval",
                },
            ],
            "edges": [
                {"source_node_id": "n1", "target_node_id": "n2"},
            ],
        },
    )
    assert r_wf.status_code == 201
    wf = r_wf.json()
    assert len(wf["nodes"]) == 2
    assert len(wf["edges"]) == 1

    r_exec = client.post(
        f"/workflows/{wf['id']}/execute",
        json={"trigger_data": {"folder": "Ready"}},
    )
    assert r_exec.status_code == 202
    assert r_exec.json()["workflow_id"] == wf["id"]
    assert r_exec.json()["status"] == "running"


def test_goal_and_security_pause_resume_emergency_stop(client: TestClient):
    r_goal = client.post(
        "/goals/",
        json={
            "title": "Reach 1M organic views",
            "description": "Free local-first workflow with human approval",
            "target_metrics": {"views": 1000000},
        },
    )
    assert r_goal.status_code in (200, 201)
    goal = r_goal.json()
    goal_id = goal["goal_id"]

    r_prog = client.get(f"/goals/{goal_id}/progress")
    assert r_prog.status_code == 200

    # Pause -> Status -> Emergency Stop -> Resume
    r_pause = client.post("/security/pause")
    assert r_pause.status_code == 200
    assert r_pause.json()["paused"] is True

    r_stop = client.post("/security/emergency-stop", json={"reason": "Integration test stop"})
    assert r_stop.status_code == 200
    assert "cancelled" in r_stop.json()["message"].lower()

    r_status = client.get("/security/autopilot-status")
    assert r_status.status_code == 200
    assert r_status.json()["emergency_stopped"] is True

    r_resume = client.post("/security/resume")
    assert r_resume.status_code == 200
    assert r_resume.json()["emergency_stopped"] is False
    assert r_resume.json()["paused"] is False


def test_control_requires_owner_token(client):
    assert client.post("/security/emergency-stop", headers={"Authorization": "Bearer wrong"}).status_code == 401
    assert client.get("/api/health/", headers={"Authorization": ""}).status_code == 401


def test_content_import_approval_and_simulated_receipt(client, tmp_path):
    assert client.post("/security/resume").status_code == 200
    folder = tmp_path / "incoming"
    folder.mkdir()
    (folder / "caption.txt").write_text("Original local content", encoding="utf-8")
    imported = client.post("/api/content/scan-folder", json={"folder_path": str(folder)})
    assert imported.status_code == 200
    asset = imported.json()["imported_assets"][0]
    account = client.post("/api/accounts/", json={"platform": "other", "username": "simulation"})
    assert account.status_code == 201
    from datetime import datetime, timedelta, timezone
    scheduled = client.post("/api/content/schedule", json={
        "asset_id": asset["id"], "account_id": account.json()["id"],
        "scheduled_at": (datetime.now(timezone.utc)+timedelta(days=1)).isoformat(), "caption": "Reviewed caption"})
    assert scheduled.status_code == 201
    prefix = "/api/content/schedule/" + scheduled.json()["id"]
    assert client.post(prefix + "/publish").status_code == 409
    preview = client.get(prefix + "/preview")
    assert preview.status_code == 200
    assert client.post(prefix + "/approve", json={"mode": "mock", "fingerprint": preview.json()["fingerprint"]}).status_code == 200
    first = client.post(prefix + "/publish")
    assert first.status_code == 200
    assert first.json()["status"] == "simulated"
    assert client.post(prefix + "/publish").json() == first.json()
    assert client.get(prefix + "/receipt").json() == first.json()
    assert client.get("/api/content/schedule").json()[0]["status"] == "approved"


def test_emergency_stop_cancels_pending_task(client):
    task = client.post("/tasks/", json={"title": "Pending work", "priority": "normal"})
    assert task.status_code in (200, 201)
    response = client.post("/security/emergency-stop")
    assert response.status_code == 200
    assert response.json()["stopped_tasks"] >= 1
