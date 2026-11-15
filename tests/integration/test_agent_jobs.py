"""Real worker/HTTP/SQLite queue, controls, interruption and result evidence."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
import sqlite3
import threading
import time

import pytest


def wait_result(client, agent, execution_id, expected="completed"):
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        response = client.get(f"/api/agents/{agent}/executions/{execution_id}")
        assert response.status_code == 200, response.text
        result = response.json()
        if result["status"] == expected:
            return result
        time.sleep(0.05)
    raise AssertionError(f"Execution did not reach {expected}: {result}")


def run(client, agent, data=None, task_id=None):
    response = client.post(
        f"/api/agents/{agent}/run", json={"task_data": data or {}, "task_id": task_id}
    )
    assert response.status_code == 202, response.text
    return response.json()["execution_id"]


def test_queued_goal_summary_survives_restart_and_records_task_result(owner_runtime):
    factory, _ = owner_runtime
    with factory() as client:
        goal = client.post("/api/goals/", json={"title": "Actual saved goal"}).json()
        prefix = "/api/goals/" + goal["goal_id"]
        client.post(
            prefix + "/milestones",
            json={"title": "Actual stage", "target_value": 10, "current_value": 5},
        )
        task = client.post(
            "/api/tasks/",
            json={
                "title": "Summarize saved goal",
                "assigned_agent": "goal_persistence",
                "inputs": {"goal_id": goal["goal_id"]},
            },
        ).json()
        queued = client.post("/api/tasks/" + task["task_id"] + "/execute")
        assert queued.status_code == 202
        execution_id = queued.json()["execution_id"]
        assert queued.json()["state"] == "pending"
        assert client.post("/api/tasks/" + task["task_id"] + "/execute").status_code == 409
        assert (
            client.put(
                "/api/tasks/" + task["task_id"], json={"outputs": {"invented": "success"}}
            ).status_code
            == 409
        )
        assert (
            client.put(
                "/api/tasks/" + task["task_id"], json={"inputs": {"goal_id": "changed"}}
            ).status_code
            == 409
        )
        assert (
            client.get("/api/agents/goal_persistence/executions/" + execution_id).json()["status"]
            == "queued"
        )
    with factory() as client:
        assert (
            client.get("/api/agents/goal_persistence/executions/" + execution_id).json()["status"]
            == "queued"
        )
        assert client.post("/api/security/resume").status_code == 200
        result = wait_result(client, "goal_persistence", execution_id)
        assert result["outputs"]["goal"]["title"] == "Actual saved goal"
        assert result["outputs"]["goal"]["progress"] == 50
        saved_task = client.get("/api/tasks/" + task["task_id"]).json()
        assert saved_task["state"] == "completed"
        assert saved_task["outputs"]["goal"]["progress"] == 50
        assert any(row["action"] == "execution_completed" for row in saved_task["audit_trail"])


def test_unsupported_invalid_disabled_and_cancelled_requests_are_honest(owner_runtime):
    factory, _ = owner_runtime
    with factory() as client:
        assert (
            client.post("/api/agents/content_publisher/run", json={"task_data": {}}).status_code
            == 501
        )
        assert client.get("/api/agents/content_publisher/executions").json() == []
        task = client.post(
            "/api/tasks/",
            json={"title": "Unavailable publisher", "assigned_agent": "content_publisher"},
        ).json()
        assert client.post("/api/tasks/" + task["task_id"] + "/execute").status_code == 501
        assert client.get("/api/tasks/" + task["task_id"]).json()["state"] == "pending"
        assert (
            client.post(
                "/api/agents/goal_persistence/run", json={"task_data": {"goal_id": "missing"}}
            ).status_code
            == 404
        )
        assert (
            client.post(
                "/api/agents/budget_guardian/run", json={"task_data": {"action": "record_spend"}}
            ).status_code
            == 422
        )
        client.post("/api/agents/budget_guardian/disable")
        assert (
            client.post("/api/agents/budget_guardian/run", json={"task_data": {}}).status_code
            == 409
        )
        client.post("/api/agents/budget_guardian/enable")
        execution_id = run(client, "budget_guardian")
        assert (
            client.post(
                "/api/agents/goal_persistence/executions/" + execution_id + "/cancel"
            ).status_code
            == 404
        )
        assert (
            client.post(
                "/api/agents/budget_guardian/executions/" + execution_id + "/cancel"
            ).status_code
            == 204
        )
        assert client.post("/api/security/resume").status_code == 200
        assert wait_result(client, "budget_guardian", execution_id, "cancelled")["outputs"] is None
        assert (
            client.get(
                "/api/agents/budget_guardian/executions", headers={"Authorization": ""}
            ).status_code
            == 401
        )


def test_queue_bound_is_atomic_under_simultaneous_requests(owner_runtime, monkeypatch):
    factory, _ = owner_runtime
    monkeypatch.setenv("JAVO_MAX_QUEUE_SIZE", "1")
    with factory() as client:
        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses = list(
                pool.map(
                    lambda _: (
                        client.post(
                            "/api/agents/budget_guardian/run", json={"task_data": {}}
                        ).status_code
                    ),
                    range(2),
                )
            )
        assert sorted(statuses) == [202, 429]


@pytest.mark.parametrize("action", ["cancel", "emergency"])
def test_running_cancellation_cannot_be_overwritten_by_success(owner_runtime, monkeypatch, action):
    from app.services.agent_jobs import agent_worker

    factory, _ = owner_runtime
    started, cancelled = threading.Event(), threading.Event()
    original = agent_worker._invoke
    calls = 0

    async def blocked(key, payload):
        nonlocal calls
        calls += 1
        if calls > 1:
            return await original(key, payload)
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    monkeypatch.setattr(agent_worker, "_invoke", blocked)
    with factory() as client:
        execution_id = run(client, "budget_guardian")
        client.post("/api/security/resume")
        assert started.wait(3)
        if action == "cancel":
            assert (
                client.post(
                    "/api/agents/budget_guardian/executions/" + execution_id + "/cancel"
                ).status_code
                == 204
            )
        else:
            assert client.post("/api/security/emergency-stop").status_code == 200
        assert cancelled.wait(3)
        assert wait_result(client, "budget_guardian", execution_id, "cancelled")["outputs"] is None
        if action == "emergency":
            assert (
                client.post("/api/agents/budget_guardian/run", json={"task_data": {}}).status_code
                == 409
            )
            client.post("/api/security/resume")
        next_id = run(client, "budget_guardian")
        assert wait_result(client, "budget_guardian", next_id)["outputs"]["usage"]["persistent"]


def test_interrupted_execution_is_failed_after_restart_without_replay(owner_runtime):
    factory, path = owner_runtime
    with factory() as client:
        task = client.post(
            "/api/tasks/",
            json={"title": "Interrupted summary", "assigned_agent": "budget_guardian"},
        ).json()
        execution_id = run(client, "budget_guardian", task_id=task["task_id"])
    # Emulate the persisted marker a crashed process would leave.
    with sqlite3.connect(path) as db:
        db.execute("UPDATE agent_executions SET status='RUNNING' WHERE id=?", (execution_id,))
        db.execute("UPDATE tasks SET state='RUNNING' WHERE task_id=?", (task["task_id"],))
    with factory() as client:
        result = wait_result(client, "budget_guardian", execution_id, "failed")
        assert result["outputs"] is None and "restarted" in result["error"]
        assert client.get("/api/tasks/" + task["task_id"]).json()["state"] == "failed"


def test_registry_upgrade_preserves_owner_disable_and_config(owner_runtime):
    factory, path = owner_runtime
    with factory() as client:
        client.post("/api/agents/budget_guardian/disable")
        client.put("/api/agents/budget_guardian/config", json={"max_tokens": 123})
    with sqlite3.connect(path) as db:
        db.execute(
            "UPDATE agent_definitions SET description='obsolete description' WHERE agent_key='budget_guardian'"
        )
    with factory() as client:
        saved = client.get("/api/agents/budget_guardian").json()
        assert not saved["is_enabled"] and saved["config"]["max_tokens"] == 123
        assert saved["description"] != "obsolete description"
        assert saved["supported_actions"] == ["summary", "check_budget"]


def test_permissions_and_deadline_are_checked_again_before_execution(owner_runtime):
    factory, path = owner_runtime
    with factory() as client:
        denied = client.post(
            "/api/tasks/",
            json={
                "title": "No read permission",
                "assigned_agent": "budget_guardian",
                "permissions": {},
            },
        ).json()
        assert client.post("/api/tasks/" + denied["task_id"] + "/execute").status_code == 403
        past = client.post(
            "/api/tasks/",
            json={
                "title": "Missed",
                "assigned_agent": "budget_guardian",
                "deadline": "2020-01-01T12:00:00+05:30",
            },
        ).json()
        assert past["deadline"] == "2020-01-01T06:30:00Z"
        assert client.post("/api/tasks/" + past["task_id"] + "/execute").status_code == 409
        allowed = client.post(
            "/api/tasks/",
            json={
                "title": "Reviewed permissions",
                "assigned_agent": "budget_guardian",
                "permissions": {"read_usage": True, "enforce_budget": True},
            },
        ).json()
        execution_id = run(client, "budget_guardian", task_id=allowed["task_id"])
        # Direct DB fault injection emulates a revoked permission snapshot.
        with sqlite3.connect(path) as db:
            db.execute(
                "UPDATE tasks SET permissions=? WHERE task_id=?",
                ('{"read_usage": false, "enforce_budget": true}', allowed["task_id"]),
            )
        client.post("/api/security/resume")
        assert wait_result(client, "budget_guardian", execution_id, "failed")["outputs"] is None
        assert client.get("/api/tasks/" + allowed["task_id"]).json()["state"] == "failed"


def test_task_removal_cancels_and_detaches_saved_execution(owner_runtime):
    factory, _ = owner_runtime
    with factory() as client:
        task = client.post(
            "/api/tasks/", json={"title": "Remove queued task", "assigned_agent": "budget_guardian"}
        ).json()
        execution_id = run(client, "budget_guardian", task_id=task["task_id"])
        assert client.delete("/api/tasks/" + task["task_id"]).status_code == 204
        result = wait_result(client, "budget_guardian", execution_id, "cancelled")
        assert result["task_id"] is None and result["outputs"] is None
