"""Integration tests for device pairing endpoint contract and truthful draft sync."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.security import get_token_manager
from app.main import create_app


def test_pairing_flow_from_unauthenticated_device(tmp_path, monkeypatch):
    db_path = tmp_path / "pairing_test.db"
    sched_path = tmp_path / "pairing_sched.db"
    monkeypatch.setenv("JAVO_DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setenv("JAVO_SCHEDULER_DB_URL", f"sqlite:///{sched_path}")
    monkeypatch.setenv("JAVO_CONTENT_ROOT", str(tmp_path / "content"))
    monkeypatch.setenv("JAVO_UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("JAVO_BACKUP_DIR", str(tmp_path / "backups"))
    monkeypatch.setenv("JAVO_THUMBNAIL_DIR", str(tmp_path / "thumbnails"))

    import app.config as cfg
    cfg._settings = None

    token = get_token_manager().generate_token("owner", device_id="desktop-1", role="owner")
    app = create_app()
    with TestClient(app) as client:
        # 1. Initiate pairing on Windows desktop (authenticated)
        init_res = client.post(
            "/devices/pair",
            json={"device_name": "Pixel 9 Pro", "platform": "android"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert init_res.status_code == 201
        data = init_res.json()
        code = data["code"]
        assert len(code) == 6

        # 2. Confirm pairing from Android client WITHOUT Bearer auth
        confirm_res = client.post(
            f"/devices/pair/{code}/confirm",
            json={
                "device_id": "android-test-device-uuid",
                "device_name": "Pixel 9 Pro",
                "platform": "android",
                "device_token": "client-initial-token-xyz",
            },
        )
        assert confirm_res.status_code == 201
        conf_data = confirm_res.json()
        assert conf_data["paired"] is True
        assert conf_data["device_id"] == "android-test-device-uuid"
        assert conf_data["device_token"]
        device_token = conf_data["device_token"]

        # 3. Use newly issued device token to sync drafts durably
        draft_payload = [
            {
                "id": "draft-phone-101",
                "title": "Hinglish AI Reel Hook",
                "body": "5 local AI tools jo har creator ko pata hone chahiye!",
                "platform": "Instagram",
                "status": "draft",
            },
            {
                "id": "draft-phone-102",
                "title": "YouTube Tech Shorts Script",
                "body": "Local LLM vs Cloud API comparison script.",
                "platform": "YouTube",
                "status": "draft",
            },
        ]

        sync_res = client.post(
            "/devices/android-test-device-uuid/sync",
            json=draft_payload,
            headers={"Authorization": f"Bearer {device_token}"},
        )
        assert sync_res.status_code == 200
        sync_data = sync_res.json()
        assert sync_data["status"] == "synced"
        assert sync_data["acknowledged_ids"] == ["draft-phone-101", "draft-phone-102"]
        assert sync_data["synced_drafts_count"] == 2
        # Truthful metric: 0 active running background agents on idle test DB, NOT hardcoded 14!
        assert sync_data["active_agents"] == 0

        # 4. Verify durable database storage and idempotent update
        updated_draft_payload = [
            {
                "id": "draft-phone-101",
                "title": "Hinglish AI Reel Hook (Updated)",
                "body": "Updated body text for local AI tools reel.",
                "platform": "Instagram",
                "status": "draft",
            }
        ]
        sync_res_2 = client.post(
            "/devices/android-test-device-uuid/sync",
            json=updated_draft_payload,
            headers={"Authorization": f"Bearer {device_token}"},
        )
        assert sync_res_2.status_code == 200
        assert sync_res_2.json()["acknowledged_ids"] == ["draft-phone-101"]

        # 5. Retrieve drafts via device endpoint to confirm durable persistence
        drafts_res = client.get(
            "/devices/android-test-device-uuid/drafts",
            headers={"Authorization": f"Bearer {device_token}"},
        )
        assert drafts_res.status_code == 200
        stored_drafts = drafts_res.json()
        assert len(stored_drafts) == 2
        d1 = next(d for d in stored_drafts if d["id"] == "draft-phone-101")
        assert d1["title"] == "Hinglish AI Reel Hook (Updated)"
        assert "Updated body text" in d1["body"]

    cfg._settings = None
