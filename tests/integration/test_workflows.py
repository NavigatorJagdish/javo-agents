"""Real saved graph/worker/restart tests. Synthetic model text is labelled."""

from datetime import datetime, timedelta, timezone
import json
import sqlite3
import time
from uuid import uuid4

import pytest


def definition(delay=None, ai=False):
    nodes = [
        {
            "id": str(uuid4()),
            "node_type": "trigger",
            "label": "Manual start",
            "is_entry_point": True,
            "config": {},
        }
    ]
    if delay is not None:
        nodes.append(
            {
                "id": str(uuid4()),
                "node_type": "delay",
                "label": "Wait",
                "config": {"seconds": delay},
            }
        )
    if ai:
        nodes.append(
            {
                "id": str(uuid4()),
                "node_type": "ai_prompt",
                "label": "Draft text",
                "config": {"prompt": "Draft a caption", "provider": "ollama", "max_tokens": 64},
            }
        )
    nodes.append({"id": str(uuid4()), "node_type": "end", "label": "End", "config": {}})
    return {
        "name": "Saved local workflow",
        "nodes": nodes,
        "edges": [
            {"id": str(uuid4()), "source_node_id": a["id"], "target_node_id": b["id"]}
            for a, b in zip(nodes, nodes[1:])
        ],
    }


def create(client, graph=None):
    result = client.post("/api/workflows/", json=graph or definition())
    assert result.status_code == 201, result.text
    return result.json()


def run(client, graph):
    result = client.post(
        "/api/workflows/" + graph["id"] + "/execute",
        json={"expected_revision": graph["revision"], "fingerprint": graph["fingerprint"]},
    )
    assert result.status_code == 202, result.text
    return result.json()


def wait(client, execution, status="completed"):
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        result = client.get("/api/workflows/executions/" + execution["id"]).json()
        if result["status"] == status:
            return result
        if status == "completed" and result["status"] in {"failed", "cancelled"}:
            pytest.fail(str(result))
        time.sleep(0.03)
    pytest.fail("Workflow did not reach " + status)


def test_saved_graph_revision_reload_conflict_restore_and_scope(owner_runtime):
    factory, path = owner_runtime
    original = definition()
    with factory() as client:
        graph = create(client, original)
        prefix = "/api/workflows/" + graph["id"]
        assert graph["revision"] == 1 and graph["execution_available"] is True
        renamed = {**original, "name": "Reviewed new name", "expected_revision": 1}
        update = client.put(prefix, json=renamed)
        assert update.status_code == 200, update.text
        assert update.json()["revision"] == 2
        assert client.put(prefix, json=renamed).status_code == 409
        assert client.get(prefix).json()["name"] == "Reviewed new name"
    with factory() as client:
        assert client.get(prefix).json()["revision"] == 2
        history = client.get(prefix + "/revisions").json()
        assert [item["revision"] for item in history] == [2, 1]
        restored = client.post(prefix + "/restore", json={"expected_revision": 2, "revision": 1})
        assert restored.status_code == 200 and restored.json()["revision"] == 3
        assert restored.json()["name"] == original["name"]
        assert restored.json()["nodes"] == graph["nodes"]
        with sqlite3.connect(path) as db:
            db.execute("UPDATE workflows SET user_id=? WHERE id=?", ("foreign-owner", graph["id"]))
        assert client.get("/api/workflows/").json() == []
        assert client.get(prefix).status_code == 404
        assert client.get(prefix + "/revisions").status_code == 404
        assert (
            client.post(
                prefix + "/restore", json={"expected_revision": 3, "revision": 1}
            ).status_code
            == 404
        )


@pytest.mark.parametrize(
    "mistake",
    [
        "cycle",
        "missing-node",
        "duplicate-node",
        "foreign-owner",
        "unknown-field",
        "oversize-config",
        "nan-position",
    ],
)
def test_invalid_graphs_do_not_write_partial_definitions(owner_runtime, mistake):
    factory, _ = owner_runtime
    graph = definition()
    if mistake == "cycle":
        graph["edges"].append(
            {"source_node_id": graph["nodes"][-1]["id"], "target_node_id": graph["nodes"][0]["id"]}
        )
    elif mistake == "missing-node":
        graph["edges"][0]["target_node_id"] = "missing-node"
    elif mistake == "duplicate-node":
        graph["nodes"][1]["id"] = graph["nodes"][0]["id"]
    elif mistake == "foreign-owner":
        graph["user_id"] = "another-owner"
    elif mistake == "unknown-field":
        graph["active"] = True
    elif mistake == "oversize-config":
        graph["nodes"][0]["config"] = {"text": "x" * 140000}
    else:
        graph["nodes"][0]["position_x"] = "NaN"
    with factory() as client:
        result = client.post("/api/workflows/", json=graph)
        assert result.status_code in {403, 422}, result.text
        assert client.get("/api/workflows/").json() == []


def test_id_collision_and_failed_replace_preserve_original(owner_runtime):
    factory, _ = owner_runtime
    with factory() as client:
        original = definition()
        create(client, original)
        collision = client.post("/api/workflows/", json=original)
        assert collision.status_code == 409
        assert len(client.get("/api/workflows/").json()) == 1
        other = create(client)
        overwrite = client.put(
            "/api/workflows/" + other["id"], json={**original, "expected_revision": 1}
        )
        assert overwrite.status_code == 409
        assert client.get("/api/workflows/" + other["id"]).json()["nodes"] == other["nodes"]


def test_queue_cancel_emergency_resume_and_history_retention(owner_runtime):
    factory, _ = owner_runtime
    with factory() as client:
        graph = create(client, definition(delay=2))
        queued = run(client, graph)
        assert queued["status"] == "queued" and queued["started_at"] is None
        assert queued["execution_verified"]
        duplicate = client.post(
            "/api/workflows/" + graph["id"] + "/execute",
            json={"expected_revision": 1, "fingerprint": graph["fingerprint"]},
        )
        assert duplicate.status_code == 409
        assert client.post("/api/security/emergency-stop").status_code == 200
        assert wait(client, queued, "cancelled")["status"] == "cancelled"
        assert client.post("/api/security/resume").status_code == 200
        current = run(client, graph)
        wait(client, current, "running")
        assert (
            client.post(
                "/api/workflows/" + graph["id"] + "/executions/" + current["id"] + "/cancel"
            ).status_code
            == 200
        )
        assert wait(client, current, "cancelled")["status"] == "cancelled"
        assert (
            client.delete(
                "/api/workflows/" + graph["id"], params={"expected_revision": 1}
            ).status_code
            == 409
        )
        assert client.get("/api/workflows/" + graph["id"]).json()["run_count"] == 0


def test_actual_node_execution_saves_output_and_immutable_snapshot(owner_runtime, monkeypatch):
    from app.core.ai_router import AIRouter, AIResponse

    seen = []

    async def synthetic(self, prompt, **kwargs):
        seen.append((json.loads(prompt), kwargs))
        return AIResponse(
            content="Synthetic workflow draft",
            provider="ollama",
            model="synthetic-fixture",
            usage_reported=True,
            total_tokens=7,
        )

    monkeypatch.setattr(AIRouter, "generate", synthetic)
    factory, _ = owner_runtime
    original = definition(ai=True)
    with factory() as client:
        graph = create(client, original)
        receipt = run(client, graph)
        changed = {**original, "name": "Changed after queue", "expected_revision": 1}
        changed["nodes"][1]["config"]["prompt"] = "Different later prompt"
        assert client.put("/api/workflows/" + graph["id"], json=changed).status_code == 200
        client.post("/api/security/resume")
        completed = wait(client, receipt)
        assert completed["revision"] == 1
        assert seen[0][0]["instruction"] == "Draft a caption"
        assert seen[0][1]["provider"] == "ollama" and seen[0][1]["fallback_to_local"] is False
        outputs = [
            event["output"]
            for event in completed["execution_log"]
            if event.get("output", {}).get("text")
        ]
        assert outputs == [
            {
                "text": "Synthetic workflow draft",
                "provider": "ollama",
                "model": "synthetic-fixture",
                "tokens_reported": 7,
                "actions_executed": False,
            }
        ]
        assert client.get("/api/workflows/" + graph["id"]).json()["run_count"] == 1
    with factory() as client:
        assert wait(client, receipt)["execution_log"] == completed["execution_log"]


def test_restart_keeps_queue_and_rejects_unconfirmed_legacy_or_tampered_runs(owner_runtime):
    factory, path = owner_runtime
    with factory() as client:
        graph = create(client)
        queued = run(client, graph)
    with factory() as client:
        assert client.get("/api/workflows/executions/" + queued["id"]).json()["status"] == "queued"
        client.post("/api/security/resume")
        assert wait(client, queued)["status"] == "completed"
        assert client.get("/api/workflows/" + graph["id"]).json()["run_count"] == 1
    with sqlite3.connect(path) as db:
        row = json.loads(
            db.execute(
                "SELECT trigger_data FROM workflow_executions WHERE id=?", (queued["id"],)
            ).fetchone()[0]
        )
        row["authorization"]["permissions"] = []
        db.execute(
            "UPDATE workflow_executions SET status=?,trigger_data=? WHERE id=?",
            ("QUEUED", json.dumps(row), queued["id"]),
        )
    with factory() as client:
        client.post("/api/security/resume")
        failed = wait(client, queued, "failed")
        assert failed["execution_verified"] is False


def test_expired_queue_and_unsupported_nodes_fail_closed(owner_runtime):
    factory, path = owner_runtime
    with factory() as client:
        graph = create(client)
        queued = run(client, graph)
        with sqlite3.connect(path) as db:
            value = json.loads(
                db.execute(
                    "SELECT trigger_data FROM workflow_executions WHERE id=?", (queued["id"],)
                ).fetchone()[0]
            )
            value["deadline"] = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
            db.execute(
                "UPDATE workflow_executions SET trigger_data=? WHERE id=?",
                (json.dumps(value), queued["id"]),
            )
        client.post("/api/security/resume")
        assert wait(client, queued, "failed")["status"] == "failed"
        unsupported = definition()
        unsupported["nodes"][0]["node_type"] = "publish"
        saved = create(client, unsupported)
        assert saved["execution_available"] is False
        assert (
            client.post(
                "/api/workflows/" + saved["id"] + "/execute",
                json={"expected_revision": 1, "fingerprint": saved["fingerprint"]},
            ).status_code
            == 501
        )
        assert client.get("/api/workflows/" + saved["id"] + "/executions").json() == []


def test_active_model_cancellation_never_becomes_completed(owner_runtime, monkeypatch):
    import asyncio
    import threading
    from app.core.ai_router import AIRouter

    entered, cancelled = threading.Event(), threading.Event()

    async def slow(self, *args, **kwargs):
        entered.set()
        try:
            await asyncio.sleep(20)
        except asyncio.CancelledError:
            cancelled.set()
            raise

    monkeypatch.setattr(AIRouter, "generate", slow)
    factory, _ = owner_runtime
    with factory() as client:
        graph = create(client, definition(ai=True))
        client.post("/api/security/resume")
        execution = run(client, graph)
        assert entered.wait(3), "Actual workflow node did not enter the synthetic model operation"
        assert client.post("/api/security/emergency-stop").status_code == 200
        result = wait(client, execution, "cancelled")
        assert cancelled.wait(3)
        assert not any(event.get("output", {}).get("text") for event in result["execution_log"])
        assert client.get("/api/workflows/" + graph["id"]).json()["run_count"] == 0


def test_paused_run_holds_between_nodes_and_archiving_cancels_queue(owner_runtime):
    factory, _ = owner_runtime
    graph_input = definition(delay=0.6)
    with factory() as client:
        graph = create(client, graph_input)
        client.post("/api/security/resume")
        execution = run(client, graph)
        wait(client, execution, "running")
        client.post("/api/security/pause")
        time.sleep(0.7)
        assert wait(client, execution, "running")["status"] == "running"
        client.post("/api/security/resume")
        assert wait(client, execution)["status"] == "completed"
        client.post("/api/security/pause")
        queued = run(client, graph)
        changed = client.put(
            "/api/workflows/" + graph["id"],
            json={**graph_input, "status": "archived", "expected_revision": 1},
        )
        assert changed.status_code == 200
        client.post("/api/security/resume")
        assert wait(client, queued, "cancelled")["status"] == "cancelled"


def test_interrupted_and_legacy_runs_do_not_replay_and_unused_delete_is_real(owner_runtime):
    factory, path = owner_runtime
    with factory() as client:
        graph = create(client)
        queued = run(client, graph)
        unused = create(client)
        assert (
            client.delete(
                "/api/workflows/" + unused["id"], params={"expected_revision": 1}
            ).status_code
            == 204
        )
        assert client.get("/api/workflows/" + unused["id"]).status_code == 404
    with sqlite3.connect(path) as db:
        db.execute("UPDATE workflow_executions SET status=? WHERE id=?", ("RUNNING", queued["id"]))
    with factory() as client:
        restarted = wait(client, queued, "failed")
        assert "restarted" in restarted["error"]
        client.post("/api/security/resume")
        assert wait(client, queued, "failed")["status"] == "failed"
        with sqlite3.connect(path) as db:
            db.execute(
                "UPDATE workflow_executions SET trigger_data=?,status=? WHERE id=?",
                ("{}", "COMPLETED", queued["id"]),
            )
            db.execute("UPDATE workflows SET run_count=99 WHERE id=?", (graph["id"],))
        old = client.get("/api/workflows/executions/" + queued["id"]).json()
        assert old["execution_verified"] is False and old["execution_log"] == []
        assert client.get("/api/workflows/" + graph["id"]).json()["run_count"] == 0


def test_corrupt_revision_restore_does_not_overwrite_current_graph(owner_runtime):
    factory, path = owner_runtime
    with factory() as client:
        graph = create(client)
        with sqlite3.connect(path) as db:
            db.execute(
                "UPDATE workflow_revisions SET fingerprint=? WHERE workflow_id=?",
                ("bad-hash", graph["id"]),
            )
        result = client.post(
            "/api/workflows/" + graph["id"] + "/restore",
            json={"expected_revision": 1, "revision": 1},
        )
        assert result.status_code == 503
        current = client.get("/api/workflows/" + graph["id"]).json()
        assert current["revision"] == 1 and current["fingerprint"] == graph["fingerprint"]


def test_busy_memory_reports_actionable_guidance_without_dispatch(owner_runtime, monkeypatch):
    from app.core import resource_manager
    from app.core.ai_router import AIRouter

    called = []

    async def forbidden(*args, **kwargs):
        called.append(True)
        raise RuntimeError("Synthetic private provider detail")

    monkeypatch.setattr(AIRouter, "generate", forbidden)
    factory, _ = owner_runtime
    with factory() as client:
        client.post("/api/security/resume")
        monkeypatch.setattr(
            resource_manager.ResourceManager,
            "get_metrics",
            lambda self: resource_manager.SystemMetrics(0, 90, 128, 8192, 10, 100, 0, 0),
        )
        result = client.post(
            "/api/voice/command", json={"transcript": "Draft a caption", "provider": "ollama"}
        )
        assert result.status_code == 503 and "Not enough free memory" in result.json()["detail"]
        assert not called and "private provider" not in result.text
