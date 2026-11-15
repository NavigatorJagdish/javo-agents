"""Real HTTP/SQLite evidence for persisted goals, isolation and task retention."""
from datetime import datetime, timedelta, timezone
import secrets
import sqlite3

from fastapi.testclient import TestClient
import pytest

from app.main import create_app


@pytest.fixture
def goal_runtime(tmp_path, monkeypatch):
    import app.config as cfg
    import app.core.resource_manager as resources
    token = secrets.token_urlsafe(32)
    values = {
        "OWNER_ACCESS_TOKEN": token,
        "DATABASE_URL": f"sqlite+aiosqlite:///{tmp_path / 'goals.db'}",
        "SCHEDULER_DB_URL": f"sqlite:///{tmp_path / 'schedule.db'}",
        "CONTROL_STATE_PATH": str(tmp_path / 'control.json'),
        "PROVIDER_CONFIG_PATH": str(tmp_path / 'provider.enc'),
        "ENCRYPTION_KEY": secrets.token_urlsafe(48),
    }
    for key in ("CONTENT_ROOT", "UPLOAD_DIR", "BACKUP_DIR", "THUMBNAIL_DIR"):
        values[key] = str(tmp_path / key.lower())
    for key, value in values.items():
        monkeypatch.setenv("JAVO_" + key, value)

    def client():
        cfg._settings = None
        resources._resource_manager = None
        return TestClient(create_app(), headers={"Authorization": f"Bearer {token}"})

    yield client, tmp_path / 'goals.db'
    cfg._settings = None
    resources._resource_manager = None


def objective(**changes):
    return {"metric": "Audience", "unit": "subscribers", "baseline": 100,
            "baseline_source": "Owner copied baseline from report", "target": 200, **changes}


def create(client, **values):
    response = client.post('/api/goals/', json={"title": "Saved objective", "objective": objective(), **values})
    assert response.status_code == 201, response.text
    return response.json()


def test_evidence_progress_restart_and_history(goal_runtime):
    factory, _ = goal_runtime
    observed = datetime.now(timezone.utc) - timedelta(seconds=1)
    with factory() as client:
        goal = create(client, deadline="2026-12-31T23:59:59+05:30")
        prefix = '/api/goals/' + goal['goal_id']
        assert goal['measurement'] is None
        assert goal['progress_basis'] == 'unmeasured'
        measured = client.post(prefix + '/measurements', json={
            "value": 150, "source": "Manually copied report", "observed_at": observed.isoformat()})
        assert measured.status_code == 200, measured.text
        assert measured.json()['progress'] == 50
        assert measured.json()['progress_basis'] == 'measurement'
        assert client.put(prefix, json={"progress": 99}).status_code == 409
        assert client.put(prefix, json={"objective": objective(target=1000)}).status_code == 409
        assert client.post(prefix + '/measurements', json={"value": 110, "source": "Old report",
            "observed_at": (observed-timedelta(days=1)).isoformat()}).status_code == 409
    # A new app lifespan/database connection reads the same evidence.
    with factory() as client:
        saved = client.get(prefix).json()
        assert saved['measurement']['source'] == 'Manually copied report'
        assert saved['deadline'] == '2026-12-31T18:29:59Z'
        assert client.get(prefix + '/progress').json()['progress'] == 50
        assert client.get('/api/goals/').json()[0]['progress'] == 50
        history = client.get(prefix + '/measurements').json()
        assert len(history) == 1 and history[0]['independently_verified'] is False
        assert client.put(prefix, json={"title": "Renamed", "description": None, "deadline": None}).status_code == 200
        assert client.get(prefix).json()['measurement']['value'] == 150


def test_milestone_consistency_scoping_and_task_retention(goal_runtime):
    factory, path = goal_runtime
    with factory() as client:
        goal = create(client, objective=None)
        prefix = '/api/goals/' + goal['goal_id']
        task = client.post('/api/tasks/', json={"title": "Retained task", "goal_id": goal['goal_id']}).json()
        milestone = client.post(prefix + '/milestones', json={"title": "First stage", "target_value": 10, "current_value": 5}).json()
        for url in (prefix, prefix + '/progress'):
            assert client.get(url).json()['progress'] == 50
        assert client.get('/api/goals/').json()[0]['progress'] == 50
        assert client.put(prefix, json={"progress": 90}).status_code == 409
        second = create(client)
        wrong = f"/api/goals/{second['goal_id']}/milestones/{milestone['id']}"
        assert client.put(wrong, json={"current_value": 10}).status_code == 404
        assert client.delete(wrong).status_code == 404
        url = prefix + '/milestones/' + milestone['id']
        assert client.put(url, json={"current_value": 20}).json()['is_completed'] is True
        assert client.get(prefix).json()['progress'] == 100
        assert client.put(url, json={"current_value": 0}).json()['is_completed'] is False
        assert client.get(prefix).json()['progress'] == 0
        assert client.delete(prefix).status_code == 204
        retained = client.get('/api/tasks/' + task['task_id'])
        assert retained.status_code == 200 and retained.json()['goal_id'] is None
    with sqlite3.connect(path) as db:
        assert db.execute('select count(*) from milestones where goal_id=?', (goal['goal_id'],)).fetchone()[0] == 0
        assert db.execute('select count(*) from audit_logs where resource_id=?', (goal['goal_id'],)).fetchone()[0] >= 4


def test_owner_scope_legacy_and_no_token(goal_runtime):
    factory, path = goal_runtime
    with factory() as client:
        assert client.post('/api/goals/', json={"title": "Wrong owner", "owner_id": "someone-else"}).status_code == 403
        goal = create(client)
        with sqlite3.connect(path) as db:
            db.execute('update goals set owner_id=? where goal_id=?', ('someone-else', goal['goal_id']))
        prefix = '/api/goals/' + goal['goal_id']
        assert client.get('/api/goals/').json() == []
        for url in (prefix, prefix + '/progress', prefix + '/milestones', prefix + '/measurements'):
            assert client.get(url).status_code == 404
        assert client.put(prefix, json={"title": "No"}).status_code == 404
        assert client.delete(prefix).status_code == 404
        assert client.get('/api/goals/', headers={"Authorization": ""}).status_code == 401
        with sqlite3.connect(path) as db:
            db.execute('update goals set owner_id=? where goal_id=?', ('default-user', goal['goal_id']))
        assert client.get(prefix).status_code == 200


@pytest.mark.parametrize('payload', [
    {"title": "   "}, {"title": "G", "deadline": "2026-12-31T12:00:00"},
    {"title": "G", "objective": objective(target=100)},
    {"title": "G", "objective": objective(baseline=True)},
    {"title": "G", "objective": objective(target="Infinity")},
    {"title": "G", "target_value": 100},
    {"title": "G", "target_metrics": {"measurement": {"value": 99}}},
])
def test_invalid_goal_never_saves(goal_runtime, payload):
    factory, _ = goal_runtime
    with factory() as client:
        assert client.post('/api/goals/', json=payload).status_code == 422
        assert client.get('/api/goals/').json() == []


def test_decreasing_objective_and_validation(goal_runtime):
    factory, _ = goal_runtime
    with factory() as client:
        goal = create(client, objective=objective(baseline=200, target=100))
        prefix = '/api/goals/' + goal['goal_id']
        now = datetime.now(timezone.utc).isoformat()
        assert client.post(prefix + '/measurements', json={"value": 150, "source": "Report", "observed_at": now}).json()['progress'] == 50
        assert client.post(prefix + '/measurements', json={"value": 300, "source": "Report", "observed_at": now}).json()['progress'] == 0
        assert client.post(prefix + '/measurements', json={"value": 0, "source": "Report", "observed_at": now}).json()['progress'] == 100
        for payload in ({"value": 10, "source": "", "observed_at": now},
                        {"value": 10, "source": "Report", "observed_at": "2026-01-01T12:00:00"},
                        {"value": 10, "source": "Report", "observed_at": (datetime.now(timezone.utc)+timedelta(days=2)).isoformat()}):
            assert client.post(prefix + '/measurements', json=payload).status_code == 422
        assert client.post(prefix + '/milestones', json={"title": "Invalid", "target_value": 0}).status_code == 422
        assert client.put(prefix, json={"title": None}).status_code == 422
        assert client.put(prefix, json={"status": "completed"}).json()['status'] == 'completed'
