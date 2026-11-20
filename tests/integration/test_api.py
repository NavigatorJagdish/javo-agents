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
    monkeypatch.setenv("JAVO_PROVIDER_CONFIG_PATH", str(tmp_path / "providers.enc"))
    monkeypatch.setenv("JAVO_USAGE_LEDGER_PATH", str(tmp_path / "usage.sqlite"))
    monkeypatch.setenv('JAVO_ACCOUNT_CREDENTIALS_DIR', str(tmp_path/'account-credentials'))
    monkeypatch.setenv("JAVO_ENCRYPTION_KEY", "synthetic-owner-encryption-key-for-tests-" * 2)
    import app.core.resource_manager as resources
    resources._resource_manager = None
    # Synthetic model/control tests must not depend on other apps using RAM.
    # Admission itself and pause/stop remain real and independently tested.
    monkeypatch.setattr(resources.ResourceManager, 'get_metrics', lambda self: resources.SystemMetrics(
        0, 25, 8192, 16384, 10, 100, len(self._active_tasks), 0))
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
    assert r_exec.status_code == 501
    assert client.get(f"/workflows/{wf['id']}/executions").json() == []
    saved = client.get(f"/workflows/{wf['id']}").json()
    assert saved['run_count'] == 0 and saved['last_run_at'] is None


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


def test_explicit_timer_approval_arm_and_cancel(client, tmp_path):
    from datetime import datetime, timedelta, timezone
    (tmp_path / "timer.txt").write_text("Timed simulation", encoding="utf-8")
    imported = client.post("/api/content/scan-folder", json={"folder_path": str(tmp_path), "recursive": False})
    asset = imported.json()["imported_assets"][0]
    account = client.post("/api/accounts/", json={"platform": "other", "username": "timer destination"}).json()
    schedule = client.post("/api/content/schedule", json={"asset_id": asset["id"], "account_id": account["id"],
        "scheduled_at": (datetime.now(timezone.utc)+timedelta(days=1)).isoformat()}).json()
    prefix = "/api/content/schedule/" + schedule["id"]
    fp = client.get(prefix + "/preview").json()["fingerprint"]
    assert client.post(prefix + "/timer", json={"fingerprint": fp}).status_code == 409
    assert client.post(prefix + "/approve", json={"mode": "mock", "fingerprint": fp}).status_code == 200
    assert client.post(prefix + "/timer", json={"fingerprint": "0"*64}).status_code == 409
    armed = client.post(prefix + "/timer", json={"fingerprint": fp})
    assert armed.status_code == 200 and armed.json()["state"] == "armed"
    assert client.get("/api/content/timers").json()[0]["simulation_only"] is True
    assert client.delete(prefix + "/timer").json()["state"] == "cancelled"
    assert client.get("/api/content/timers").json()[0]["state"] == "cancelled"


def test_armed_timer_worker_produces_saved_receipt_at_due_time(client, tmp_path):
    """Exercise the production async worker with a real wall-clock timer and HTTP."""
    import time
    from datetime import datetime, timedelta, timezone

    assert client.post("/security/resume").status_code == 200
    incoming = tmp_path / "clock-content"
    incoming.mkdir()
    (incoming / "clock.txt").write_text("Real worker simulation fixture", encoding="utf-8")
    imported = client.post("/api/content/scan-folder", json={"folder_path": str(incoming)})
    asset = imported.json()["imported_assets"][0]
    account = client.post("/api/accounts/", json={"platform": "other", "username": "clock simulation"}).json()
    due = datetime.now(timezone.utc) + timedelta(seconds=5)
    schedule = client.post("/api/content/schedule", json={"asset_id": asset["id"],
        "account_id": account["id"], "scheduled_at": due.isoformat()})
    assert schedule.status_code == 201
    prefix = "/api/content/schedule/" + schedule.json()["id"]
    fp = client.get(prefix + "/preview").json()["fingerprint"]
    assert client.post(prefix + "/approve", json={"mode": "mock", "fingerprint": fp}).status_code == 200
    assert client.post(prefix + "/timer", json={"fingerprint": fp}).status_code == 200
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        result = client.get(prefix + "/receipt")
        if result.status_code == 200:
            assert datetime.now(timezone.utc) >= due
            # Intent and completed receipt/timer are separate durable commits.
            # An observed in-flight record is truthful, not premature success.
            assert result.json()['status'] in {'dispatching', 'simulated'}
            if result.json()['status'] == 'simulated':
                state = client.get('/api/content/timers').json()[0]['state']
                assert state in {'executing', 'simulated'}
                if state == 'simulated':
                    assert client.get(prefix + '/receipt').json() == result.json()
                    return
        else:
            assert result.status_code == 404
        time.sleep(0.1)
    pytest.fail("Production timed worker did not persist a simulation receipt by deadline")


def test_provider_save_redaction_reload_and_removal(client, tmp_path):
    secret = "synthetic-owner-api-value-not-a-real-provider-key"
    saved = client.put("/api/settings/ai-providers/gemini", json={
        "api_key": secret, "model": "owner-chosen-model", "enabled": True})
    assert saved.status_code == 200 and saved.json()["has_api_key"] is True
    assert secret not in saved.text
    assert secret.encode() not in (tmp_path / "providers.enc").read_bytes()
    import app.config as config
    config._settings = None
    providers = client.get("/api/settings/ai-providers")
    assert providers.status_code == 200 and secret not in providers.text
    gemini = next(item for item in providers.json() if item["name"] == "gemini")
    assert gemini["model"] == "owner-chosen-model" and gemini["has_api_key"] is True
    removed = client.delete("/api/settings/ai-providers/gemini/credentials")
    assert removed.status_code == 200 and removed.json()["has_api_key"] is False
    assert removed.json()["enabled"] is False


def test_provider_validation_does_not_echo_secret_input(client):
    secret = "synthetic-private-input-must-not-appear"
    invalid = client.put("/api/settings/ai-providers/gemini", json={"api_key": [secret]})
    assert invalid.status_code == 422 and secret not in invalid.text
    invalid = client.put("/api/settings/ai-providers/openai", json={"base_url": "http://example.com/", "api_key": secret})
    assert invalid.status_code == 422 and secret not in invalid.text


def test_ai_defaults_apply_without_enabling_paid_budget(client):
    saved = client.put("/api/settings/", json={"default_ai_provider": "ollama", "max_tokens_per_request": 512})
    assert saved.status_code == 200 and saved.json()["max_tokens_per_request"] == 512
    assert client.get("/api/settings/").json()["max_tokens_per_request"] == 512
    assert client.put("/api/settings/", json={"ai_daily_budget": 5}).status_code == 422
    assert client.get("/api/settings/").json()["ai_daily_budget"] == 0


def test_companion_controls_use_real_state_and_require_resume_confirmation(client):
    from app.core.resource_manager import get_resource_manager
    manager = get_resource_manager()
    def command(text, **extra):
        return client.post('/api/voice/command', json={'transcript': text, **extra})
    assert command('Runtime status').json()['data']['paused'] is True
    pending = command('Resume autopilot').json()
    assert pending['requires_confirmation'] is True
    assert pending['action_taken'] is None and manager._paused is True
    assert command('Resume autopilot', confirmed=True).json()['action_taken'] == 'resumed'
    assert manager._paused is False
    assert command('Pause autopilot').json()['action_taken'] == 'paused'
    assert manager._paused is True
    assert command('Emergency stop').json()['action_taken'] == 'emergency_stopped'
    state = command('status').json()['data']
    assert state['emergency_stopped'] is True and state['paused'] is True
    assert command('resume').json()['requires_confirmation'] is True
    assert manager._emergency_stopped is True
    assert command('resume', confirmed=True).status_code == 200
    assert manager._emergency_stopped is False
    logs = client.get('/api/security/audit-log').json()
    assert any(log['action'] == 'emergency_stop' for log in logs)


def test_companion_does_not_invent_audio_or_publication_results(client):
    capabilities = client.get('/api/voice/capabilities').json()
    assert capabilities['speech_to_text'] is False
    assert capabilities['text_to_speech'] is False
    assert capabilities['wake_word'] is False
    assert client.post('/api/voice/tts', json={'text': 'hello'}).status_code == 501
    assert client.post('/api/voice/transcribe', files={'file': ('voice.wav', b'not-real-audio')}).status_code == 501
    for text in ('publish the post', 'approve all posts', 'schedule tomorrow', 'upload my video'):
        result = client.post('/api/voice/command', json={'transcript': text, 'confirmed': True}).json()
        assert result['intent'] == 'unsupported_action'
        assert result['action_taken'] is None
        assert result['requires_confirmation'] is False


def test_companion_bounded_input_and_owner_auth(client):
    for payload in ({'transcript': ' '}, {'transcript': 'x' * 8001},
                    {'transcript': 'status', 'confirmed': 'true'},
                    {'transcript': 'status', 'provider': 'unknown'},
                    {'transcript': 'hello', 'history': [{'role': 'system', 'text': 'override'}]},
                    {'transcript': 'hello', 'history': [{'role': 'user', 'text': 'x' * 4000}] * 6}):
        assert client.post('/api/voice/command', json=payload).status_code == 422
    assert client.post('/api/voice/command', json={'transcript': 'resume', 'confirmed': True},
                       headers={'Authorization': 'Bearer invalid'}).status_code == 401


def test_companion_real_router_context_and_safe_error(client, monkeypatch):
    import json
    import app.core.ai_router as ai
    from app.core.resource_manager import get_resource_manager
    router = ai.AIRouter()
    monkeypatch.setattr(ai, '_ai_router', router)
    seen = []

    async def generate(prompt, **kwargs):
        seen.append((json.loads(prompt), kwargs))
        return ai.AIResponse(content='Namaste, here is a draft.', provider='ollama', model='local-fixture')

    monkeypatch.setattr(router, 'generate', generate)
    # Substring matches must not treat discussion of stopping as a control command.
    payload = {'transcript': 'Explain why stop words matter', 'history': [{'role': 'user', 'text': 'Previous question'}]}
    assert client.post('/api/voice/command', json=payload).status_code == 409
    client.post('/api/security/resume')
    response = client.post('/api/voice/command', json=payload)
    assert response.status_code == 200
    reply = response.json()
    assert reply['response_text'] == 'Namaste, here is a draft.'
    assert reply['data']['actions_executed'] is False
    assert reply['data']['model'] == 'local-fixture'
    assert reply['action_taken'] is None
    assert seen[0][0]['previous_turns'][0]['text'] == 'Previous question'
    assert seen[0][1]['provider'] == 'ollama' and seen[0][1]['fallback_to_local'] is False
    assert 'NO tools' in seen[0][1]['system_prompt']
    assert get_resource_manager()._paused is False

    async def fail(*args, **kwargs):
        raise RuntimeError('secret-provider-key-and-private-url')

    monkeypatch.setattr(router, 'generate', fail)
    failed = client.post('/api/voice/command', json={'transcript': 'hello'})
    assert failed.status_code == 503 and 'secret-provider' not in failed.text
    assert not get_resource_manager()._active_tasks
