"""Integration tests for FastAPI application endpoints and lifecycle."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
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
    with TestClient(app) as test_client:
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
