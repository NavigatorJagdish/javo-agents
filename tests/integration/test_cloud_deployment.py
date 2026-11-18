"""Cloud boundaries: login, readiness, SPA routing, and restart persistence."""

from __future__ import annotations

import base64

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.cloud import create_cloud_app


@pytest.fixture()
def cloud_environment(tmp_path, monkeypatch):
    import app.config as cfg
    import app.main as main
    from app.core.resource_manager import ResourceManager
    from app.core.scheduler import SchedulerService
    from app.services.content_watcher import ContentWatcher

    dashboard = tmp_path / "dashboard"
    (dashboard / "assets").mkdir(parents=True)
    (dashboard / "index.html").write_text("<html>Javo dashboard</html>", encoding="utf-8")
    (dashboard / "assets" / "app.js").write_text("window.javo = true;", encoding="utf-8")
    values = {
        "JAVO_CLOUD_USERNAME": "javo-test",
        "JAVO_CLOUD_PASSWORD": "test-password-used-only-in-tests",
        "JAVO_SECRET_KEY": "test-signing-key-used-only-in-tests-123",
        "JAVO_ENCRYPTION_KEY": "test-encryption-key-used-only-in-tests",
        "JAVO_DASHBOARD_DIST": str(dashboard),
        "JAVO_DATABASE_URL": f"sqlite+aiosqlite:///{tmp_path / 'runtime.db'}",
        "JAVO_SCHEDULER_DB_URL": f"sqlite:///{tmp_path / 'scheduler.db'}",
        "JAVO_CONTENT_ROOT": str(tmp_path / "content"),
        "JAVO_UPLOAD_DIR": str(tmp_path / "uploads"),
        "JAVO_BACKUP_DIR": str(tmp_path / "backups"),
        "JAVO_THUMBNAIL_DIR": str(tmp_path / "thumbnails"),
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(cfg, "_settings", None)
    monkeypatch.setattr(main, "settings", cfg.get_settings())

    def open_app():
        # Simulate process-local services being recreated on container restart.
        monkeypatch.setattr(main, "scheduler", SchedulerService())
        manager = ResourceManager()
        watcher = ContentWatcher()
        monkeypatch.setattr(main, "get_resource_manager", lambda: manager)
        monkeypatch.setattr(main, "get_content_watcher", lambda: watcher)
        return TestClient(create_cloud_app())

    yield open_app, (values["JAVO_CLOUD_USERNAME"], values["JAVO_CLOUD_PASSWORD"])


@pytest.mark.parametrize(
    "name",
    ["JAVO_CLOUD_USERNAME", "JAVO_CLOUD_PASSWORD", "JAVO_SECRET_KEY", "JAVO_ENCRYPTION_KEY"],
)
def test_missing_cloud_credentials_prevent_startup(cloud_environment, monkeypatch, name):
    monkeypatch.delenv(name)
    with pytest.raises(RuntimeError, match=name):
        create_cloud_app()


def test_weak_cloud_password_prevents_startup(cloud_environment, monkeypatch):
    monkeypatch.setenv("JAVO_CLOUD_PASSWORD", "short")
    with pytest.raises(RuntimeError, match="JAVO_CLOUD_PASSWORD"):
        create_cloud_app()


def test_cloud_requires_a_built_dashboard(cloud_environment, monkeypatch, tmp_path):
    monkeypatch.setenv("JAVO_DASHBOARD_DIST", str(tmp_path / "missing"))
    with pytest.raises(RuntimeError, match="JAVO_DASHBOARD_DIST"):
        create_cloud_app()


def test_only_minimal_readiness_is_public(cloud_environment):
    open_app, auth = cloud_environment
    with open_app() as client:
        assert client.get("/healthz").json() == {"status": "ok"}
        assert client.head("/healthz").status_code == 200
        for path in ["/", "/ai-team", "/assets/app.js", "/api/health/", "/api/docs"]:
            response = client.get(path)
            assert response.status_code == 401
            assert response.headers["www-authenticate"].startswith("Basic")
        assert client.post("/healthz").status_code == 401
        assert client.get("/api/agents/", auth=(auth[0], "wrong")).status_code == 401
        assert client.get("/api/agents/", headers={"Authorization": "Basic !!!"}).status_code == 401
        assert client.get("/api/agents/", auth=auth).status_code == 200


def test_dashboard_deep_links_and_missing_assets(cloud_environment):
    open_app, auth = cloud_environment
    with open_app() as client:
        for path in ["/", "/ai-team", "/setup/welcome"]:
            response = client.get(path, auth=auth)
            assert response.status_code == 200
            assert "Javo dashboard" in response.text
            assert "no-store" in response.headers["cache-control"]
        assert client.get("/assets/app.js", auth=auth).text == "window.javo = true;"
        assert client.get("/assets/missing.js", auth=auth).status_code == 404
        assert client.get("/api/not-an-endpoint", auth=auth).status_code == 404


def test_cross_origin_requests_cannot_use_cached_browser_login(cloud_environment):
    open_app, auth = cloud_environment
    with open_app() as client:
        response = client.post(
            "/api/tasks/", auth=auth, headers={"Origin": "https://unrelated.example"},
            json={"title": "Must not be created"},
        )
        assert response.status_code == 403
        assert client.get(
            "/api/agents/", auth=auth, headers={"Origin": "https://[invalid"}
        ).status_code == 403
        assert client.get("/api/tasks/", auth=auth).json() == []
        assert client.get(
            "/api/agents/", auth=auth, headers={"Origin": "https://testserver"}
        ).status_code == 200


def test_runtime_data_survives_restart(cloud_environment):
    open_app, auth = cloud_environment
    with open_app() as client:
        assert len(client.get("/api/agents/", auth=auth).json()) == 30
        response = client.post("/api/tasks/", auth=auth, json={"title": "Persistent cloud task"})
        assert response.status_code == 201
        task_id = response.json()["task_id"]
    with open_app() as client:
        tasks = client.get("/api/tasks/", auth=auth).json()
        assert any(task["task_id"] == task_id for task in tasks)
        assert len(client.get("/api/agents/", auth=auth).json()) == 30


def test_websocket_requires_the_same_cloud_login(cloud_environment):
    open_app, auth = cloud_environment
    header = "Basic " + base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
    with open_app() as client:
        with pytest.raises(WebSocketDisconnect) as error:
            with client.websocket_connect("/api/ws/events"):
                pass
        assert error.value.code == 1008
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(
                "/api/ws/events",
                headers={"Authorization": header, "Origin": "https://unrelated.example"},
            ):
                pass
        with client.websocket_connect("/api/ws/events", headers={"Authorization": header}) as ws:
            assert ws.receive_json()["event"] == "connected"
            ws.send_json({"type": "ping"})
            assert ws.receive_json()["event"] == "pong"
