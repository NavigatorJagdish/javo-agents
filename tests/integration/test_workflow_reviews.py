"""Real durable branch/review execution. Only model text is synthetic."""

import json
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest


def graph(*, gate=True, condition=False, second_gate=False):
    nodes = []

    def node(kind, label, config=None):
        item = {
            "id": str(uuid4()),
            "node_type": kind,
            "label": label,
            "config": config or {},
            "is_entry_point": not nodes,
        }
        nodes.append(item)
        return item["id"]

    start = node("trigger", "Start")
    branch = (
        node(
            "condition",
            "Generate requested?",
            {"source": "input", "field": "generate", "operator": "equals", "value": True},
        )
        if condition
        else None
    )
    first = node(
        "ai_prompt", "First draft", {"prompt": "First synthetic instruction", "provider": "ollama"}
    )
    review = (
        node("approval", "Owner review", {"instructions": "Review this exact actual draft."})
        if gate
        else None
    )
    second = (
        node(
            "ai_prompt",
            "After review",
            {"prompt": "Continue using the reviewed draft", "provider": "ollama"},
        )
        if gate
        else None
    )
    another = (
        node("approval", "Second review", {"instructions": "Review the second actual draft."})
        if second_gate
        else None
    )
    end = node("end", "End")
    path = [x for x in [start, branch, first, review, second, another, end] if x]
    edges = [
        {"source_node_id": a, "target_node_id": b, "condition": "true" if a == branch else None}
        for a, b in zip(path, path[1:])
    ]
    if branch:
        edges.append({"source_node_id": branch, "target_node_id": end, "condition": "false"})
    return {"name": "Native reviewed draft", "nodes": nodes, "edges": edges}


def create(client, definition):
    response = client.post("/api/workflows/", json=definition)
    assert response.status_code == 201, response.text
    assert response.json()["execution_available"], response.text
    return response.json()


def enqueue(client, saved, data=None):
    response = client.post(
        "/api/workflows/" + saved["id"] + "/execute",
        json={
            "expected_revision": saved["revision"],
            "fingerprint": saved["fingerprint"],
            "trigger_data": data or {},
        },
    )
    assert response.status_code == 202, response.text
    return response.json()


def wait(client, run, state):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        result = client.get("/api/workflows/executions/" + run["id"]).json()
        if result["status"] == state:
            return result
        assert result["status"] not in {"failed", "cancelled"}, result
        time.sleep(0.03)
    pytest.fail("Run did not reach " + state)


@pytest.fixture
def model(monkeypatch):
    from app.core.ai_router import AIRouter, AIResponse

    seen = []

    async def generate(self, prompt, **kwargs):
        seen.append(json.loads(prompt))
        return AIResponse(
            content="Synthetic actual draft " + str(len(seen)),
            provider="ollama",
            model="synthetic-review-fixture",
        )

    monkeypatch.setattr(AIRouter, "generate", generate)
    return seen


def preview(client, run):
    summary = next(
        r
        for r in client.get("/api/workflows/approvals").json()
        if r["execution_id"] == run["id"] and r["status"] == "pending"
    )
    response = client.get("/api/workflows/approvals/" + summary["id"])
    assert response.status_code == 200, response.text
    return response.json()


def decision(client, item, choice="approve", **changes):
    return client.post(
        "/api/workflows/approvals/" + item["id"] + "/decision",
        json={
            "expected_revision": item["revision"],
            "fingerprint": item["fingerprint"],
            "decision": choice,
            **changes,
        },
    )


@pytest.mark.parametrize(
    "generate,expected", [(True, True), (False, False), ("true", False), (1, False), (None, False)]
)
def test_only_selected_branch_invokes_actual_nodes(owner_runtime, model, generate, expected):
    factory, _ = owner_runtime
    with factory() as client:
        saved = create(client, graph(gate=False, condition=True))
        run = enqueue(client, saved, {"generate": generate})
        client.post("/api/security/resume")
        result = wait(client, run, "completed")
        assert len(model) == int(expected)
        events = [e for e in result["execution_log"] if e["event"] == "completed"]
        assert (
            next(e["output"]["matched"] for e in events if e["node_type"] == "condition")
            is expected
        )
        assert sum(e["node_type"] == "ai_prompt" for e in events) == int(expected)
        assert sum(e["node_type"] == "end" for e in events) == 1


def test_review_survives_restart_releases_worker_and_never_replays_completed_model(
    owner_runtime, model
):
    factory, _ = owner_runtime
    with factory() as client:
        saved = create(client, graph(condition=True))
        run = enqueue(client, saved, {"generate": True, "brief": "Synthetic verified facts"})
        client.post("/api/security/resume")
        waiting = wait(client, run, "waiting_approval")
        item = preview(client, run)
        assert (
            item["approvable"]
            and item["checkpoint"]["previous_output"] == "Synthetic actual draft 1"
        )
        assert item["checkpoint"]["input"]["brief"] == "Synthetic verified facts"
        assert item["definition"]["name"] == saved["name"]
        # Human review must not occupy the sole execution resource.
        simple = graph(gate=False)
        simple["nodes"] = [n for n in simple["nodes"] if n["node_type"] != "ai_prompt"]
        simple["edges"] = [
            {
                "source_node_id": simple["nodes"][0]["id"],
                "target_node_id": simple["nodes"][-1]["id"],
            }
        ]
        wait(client, enqueue(client, create(client, simple)), "completed")
        assert len(model) == 1
        assert (
            client.post(
                "/api/workflows/" + saved["id"] + "/execute",
                json={"expected_revision": saved["revision"], "fingerprint": saved["fingerprint"]},
            ).status_code
            == 409
        )
    with factory() as client:
        client.post("/api/security/pause")
        assert wait(client, run, "waiting_approval")["execution_log"] == waiting["execution_log"]
        item = preview(client, run)
        assert decision(client, item).status_code == 200
        assert decision(client, item).status_code == 409
        assert client.get("/api/workflows/executions/" + run["id"]).json()["status"] == "queued"
        assert len(model) == 1
    with factory() as client:
        assert len(model) == 1
        client.post("/api/security/resume")
        result = wait(client, run, "completed")
        assert len(model) == 2 and model[1]["previous_output"] == "Synthetic actual draft 1"
        ids = [e["node_id"] for e in result["execution_log"] if e["event"] == "completed"]
        assert len(ids) == len(set(ids)) == len(saved["nodes"])


@pytest.mark.parametrize(
    "mistake",
    [
        "revision",
        "fingerprint",
        "changed_graph",
        "expired",
        "tampered",
        "changed_draft",
        "damaged_checkpoint",
        "cancelled",
        "emergency",
        "foreign_owner",
    ],
)
def test_stale_expired_cancelled_or_changed_checkpoint_cannot_continue(
    owner_runtime, model, mistake
):
    factory, path = owner_runtime
    with factory() as client:
        definition = graph()
        saved = create(client, definition)
        run = enqueue(client, saved)
        client.post("/api/security/resume")
        wait(client, run, "waiting_approval")
        item = preview(client, run)
        changes = {}
        if mistake == "revision":
            changes["expected_revision"] = 99
        elif mistake == "fingerprint":
            changes["fingerprint"] = "0" * 64
        elif mistake == "changed_graph":
            assert (
                client.put(
                    "/api/workflows/" + saved["id"],
                    json={**definition, "name": "Changed elsewhere", "expected_revision": 1},
                ).status_code
                == 200
            )
        elif mistake == "expired":
            with sqlite3.connect(path) as db:
                db.execute(
                    "UPDATE workflow_node_reviews SET expires_at=? WHERE id=?",
                    ((datetime.now(timezone.utc) - timedelta(days=1)).isoformat(), item["id"]),
                )
        elif mistake == "tampered":
            with sqlite3.connect(path) as db:
                changed = {**item["checkpoint"], "previous_output": "Different draft"}
                db.execute(
                    "UPDATE workflow_node_reviews SET checkpoint=? WHERE id=?",
                    (json.dumps(changed), item["id"]),
                )
        elif mistake == "cancelled":
            client.post("/api/workflows/" + saved["id"] + "/executions/" + run["id"] + "/cancel")
        elif mistake == "changed_draft":
            with sqlite3.connect(path) as db:
                log = json.loads(
                    db.execute(
                        "SELECT execution_log FROM workflow_executions WHERE id=?", (run["id"],)
                    ).fetchone()[0]
                )
                next(e for e in log if e.get("output", {}).get("text"))["output"]["text"] = (
                    "Changed after review"
                )
                db.execute(
                    "UPDATE workflow_executions SET execution_log=? WHERE id=?",
                    (json.dumps(log), run["id"]),
                )
        elif mistake == "damaged_checkpoint":
            with sqlite3.connect(path) as db:
                db.execute(
                    "UPDATE workflow_node_reviews SET checkpoint=? WHERE id=?",
                    (json.dumps("damaged"), item["id"]),
                )
        elif mistake == "emergency":
            client.post("/api/security/emergency-stop", json={"reason": "Synthetic review test"})
        elif mistake == "foreign_owner":
            with sqlite3.connect(path) as db:
                db.execute(
                    "UPDATE workflows SET user_id=? WHERE id=?", ("foreign-owner", saved["id"])
                )
        assert decision(client, item, **changes).status_code == (
            503 if mistake == "damaged_checkpoint" else 404 if mistake == "foreign_owner" else 409
        )
        assert len(model) == 1


def test_multiple_review_gates_resume_and_rejection_stops_downstream(owner_runtime, model):
    factory, _ = owner_runtime
    with factory() as client:
        saved = create(client, graph(second_gate=True))
        run = enqueue(client, saved)
        client.post("/api/security/resume")
        wait(client, run, "waiting_approval")
        assert decision(client, preview(client, run)).status_code == 200
        deadline = time.monotonic() + 8
        while len(model) < 2 and time.monotonic() < deadline:
            time.sleep(0.03)
        wait(client, run, "waiting_approval")
        item = preview(client, run)
        assert item["checkpoint"]["previous_output"] == "Synthetic actual draft 2"
        assert decision(client, item, "reject").status_code == 200
        assert client.get("/api/workflows/executions/" + run["id"]).json()["status"] == "cancelled"
        assert len(model) == 2


def test_scoped_client_has_no_native_review_privilege(owner_runtime, model):
    factory, _ = owner_runtime
    with factory() as client:
        saved = create(client, graph())
        run = enqueue(client, saved)
        client.post("/api/security/resume")
        wait(client, run, "waiting_approval")
        item = preview(client, run)
        token = client.post(
            "/api/integrations/grants",
            json={
                "client": "n8n",
                "label": "Synthetic client",
                "scopes": ["propose_workflow", "read_own_results"],
            },
        ).json()["token"]
        for route in ["/api/workflows/approvals", "/api/workflows/approvals/" + item["id"]]:
            assert (
                client.get(route, headers={"Authorization": "Bearer " + token}).status_code == 401
            )
        assert (
            client.post(
                "/api/workflows/approvals/" + item["id"] + "/decision",
                headers={"Authorization": "Bearer " + token},
                json={
                    "expected_revision": 1,
                    "fingerprint": item["fingerprint"],
                    "decision": "approve",
                },
            ).status_code
            == 401
        )
        assert decision(client, item, "reject").status_code == 200


def test_concurrent_owner_decisions_queue_one_continuation(owner_runtime, model):
    from concurrent.futures import ThreadPoolExecutor

    factory, _ = owner_runtime
    with factory() as client:
        run = enqueue(client, create(client, graph()))
        client.post("/api/security/resume")
        wait(client, run, "waiting_approval")
        item = preview(client, run)
        client.post("/api/security/pause")
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(decision, client, item) for _ in range(2)]
            assert sorted(f.result().status_code for f in futures) == [200, 409]
        client.post("/api/security/resume")
        wait(client, run, "completed")
        assert len(model) == 2


def test_orphaned_legacy_wait_is_failed_on_restart_without_execution(owner_runtime, model):
    factory, path = owner_runtime
    with factory() as client:
        run = enqueue(client, create(client, graph()))
        with sqlite3.connect(path) as db:
            db.execute(
                "UPDATE workflow_executions SET status='WAITING_APPROVAL' WHERE id=?", (run["id"],)
            )
    with factory() as client:
        result = client.get("/api/workflows/executions/" + run["id"]).json()
        assert result["status"] == "failed" and "missing owner-review" in result["error"]
        assert not model
