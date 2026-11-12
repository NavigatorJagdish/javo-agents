"""Mandatory Security Regression Test Suite for PR #1 Remediation.

Covers:
1. Anonymous privileged API access rejection (401)
2. Cross-account access rejection (403)
3. Forged Telegram webhook requests, missing secrets, replay rejection (401/403/409)
4. Unauthorized skill upgrade attempts (401/403/422)
5. Repeated upgrade proposal replay and expiration rejection (409/410)
6. Unapproved content publishing blocked (400)
7. False publication success eliminated (honest failure / explicit mode)
8. Duplicate publication attempts rejected (409 idempotency)
9. Malicious plugin behavior and untrusted tier execution blocked
10. Backup restore failure, path traversal rejection, active task concurrency guard
11. WebSocket connection authentication enforcement
"""

from __future__ import annotations

import asyncio
import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.api.routes import skills as skills_route
from app.api.routes import telegram as tg_route
from app.config import get_settings
from app.core.security import get_token_manager
from app import database as db
from app.main import create_app
from app.models.content import AssetStatus, AssetType, ContentAsset, ContentSchedule, ScheduleStatus
from app.models.task import Task, TaskPriority, TaskState
from app.services.backup_service import BackupService
from skills.sandbox.runner import inspect_skill_ast, run_skill_sandboxed


@pytest.fixture()
def sec_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "sec_test.db"
    sched_path = tmp_path / "sec_sched.db"
    settings = get_settings()
    monkeypatch.setattr(settings, "database_url", f"sqlite+aiosqlite:///{db_path.as_posix()}")
    monkeypatch.setattr(settings, "scheduler_db_url", f"sqlite:///{sched_path.as_posix()}")
    monkeypatch.setattr(settings, "content_root", str(tmp_path / "content"))
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "backup_dir", str(tmp_path / "backups"))
    monkeypatch.setattr(settings, "thumbnail_dir", str(tmp_path / "thumbnails"))
    monkeypatch.setattr(settings, "host", "127.0.0.1")
    monkeypatch.setattr(settings, "owner_token", "test-fixed-owner-token-32-chars-long")

    tg_route._TELEGRAM_OVERRIDES.clear()
    tg_route._PROCESSED_UPDATE_IDS.clear()
    skills_route._PROPOSALS.clear()

    asyncio.run(db.close_db())
    db.init_engine()
    asyncio.run(db.create_tables())
    yield tmp_path
    tg_route._TELEGRAM_OVERRIDES.clear()
    tg_route._PROCESSED_UPDATE_IDS.clear()
    skills_route._PROPOSALS.clear()
    asyncio.run(db.close_db())


def test_anonymous_privileged_api_access_rejected(sec_env: Path):
    """Endpoints modifying accounts, skills, settings, content, tasks, or security must reject anonymous access."""
    with TestClient(create_app()) as unauth_client:
        assert unauth_client.post("/accounts/", json={"platform": "instagram", "username": "alice"}).status_code == 401
        assert unauth_client.post("/content/schedule/fake-id/publish").status_code == 401
        assert unauth_client.post("/skills/social-caption-optimizer/apply-upgrade", json={"proposal_id": "none"}).status_code == 401
        assert unauth_client.put("/settings/", json={"ai_daily_budget": 5.0}).status_code == 401
        assert unauth_client.post("/security/pause").status_code == 401
        assert unauth_client.post("/security/emergency-stop").status_code == 401
        assert unauth_client.post("/tasks/fake-id/execute").status_code == 401
        assert unauth_client.post("/devices/pair/123456/confirm").status_code == 401
        assert unauth_client.put("/telegram/config", json={"allowed_users": ["1"]}).status_code == 401


def test_websocket_authentication_enforced(sec_env: Path):
    """WebSocket /ws and /ws/events must reject unauthenticated or invalid token connections."""
    mgr = get_token_manager()
    valid_token = mgr.generate_token("owner", role="owner")

    with TestClient(create_app()) as client:
        # Unauthenticated WebSocket connection rejected
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/ws"):
                pass

        # Invalid token rejected
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/ws?token=invalid-token-123"):
                pass

        # Valid token succeeds
        with client.websocket_connect(f"/ws?token={valid_token}") as ws:
            msg = ws.receive_json()
            assert msg["event"] == "connected"
            assert msg["data"]["user_id"] == "owner"


def test_cross_account_access_denied(sec_env: Path):
    """Non-owner users cannot inspect, update, or publish content belonging to another user account."""
    mgr = get_token_manager()
    token_alice = mgr.generate_token("alice", role="user")
    token_bob = mgr.generate_token("bob", role="user")

    with TestClient(create_app()) as base_client:
        # Alice creates an account
        res = base_client.post(
            "/accounts/",
            headers={"Authorization": f"Bearer {token_alice}"},
            json={"platform": "instagram", "username": "alice_ig"},
        )
        assert res.status_code == 201
        account_id = res.json()["id"]

        # Bob attempts to read/update/delete Alice's account -> 403 Forbidden
        assert base_client.get(f"/accounts/{account_id}", headers={"Authorization": f"Bearer {token_bob}"}).status_code == 403
        assert (
            base_client.put(
                f"/accounts/{account_id}",
                headers={"Authorization": f"Bearer {token_bob}"},
                json={"display_name": "hacked"},
            ).status_code
            == 403
        )
        assert base_client.delete(f"/accounts/{account_id}", headers={"Authorization": f"Bearer {token_bob}"}).status_code == 403


def test_forged_telegram_requests_and_replay_rejected(sec_env: Path):
    """Telegram webhook enforces secret-token header verification and rejects forged or duplicate updates."""
    mgr = get_token_manager()
    owner_token = mgr.generate_token("owner", role="owner")

    with TestClient(create_app(), headers={"Authorization": f"Bearer {owner_token}"}) as client:
        cfg_res = client.put(
            "/telegram/config",
            json={
                "bot_token": "999999:test-bot-token",
                "webhook_secret": "secure-secret-token-12345",
                "allowed_users": ["12345"],
            },
        )
        assert cfg_res.status_code == 200
        assert cfg_res.json()["has_webhook_secret"] is True

        # 1. Missing secret token header -> 401
        assert (
            client.post(
                "/telegram/webhook",
                json={"update_id": 1001, "message": {"from": {"id": 12345}, "text": "/status"}},
            ).status_code
            == 401
        )

        # 2. Forged secret token header -> 401
        assert (
            client.post(
                "/telegram/webhook",
                headers={"X-Telegram-Bot-Api-Secret-Token": "wrong-secret-token"},
                json={"update_id": 1002, "message": {"from": {"id": 12345}, "text": "/status"}},
            ).status_code
            == 401
        )

        # 3. Valid secret token but unpaired sender ID -> 403
        assert (
            client.post(
                "/telegram/webhook",
                headers={"X-Telegram-Bot-Api-Secret-Token": "secure-secret-token-12345"},
                json={"update_id": 1003, "message": {"from": {"id": 88888}, "text": "/status"}},
            ).status_code
            == 403
        )

        # 4. Valid secret token and paired sender ID -> 200
        valid_res = client.post(
            "/telegram/webhook",
            headers={"X-Telegram-Bot-Api-Secret-Token": "secure-secret-token-12345"},
            json={"update_id": 1004, "message": {"from": {"id": 12345}, "text": "/status"}},
        )
        assert valid_res.status_code == 200
        assert valid_res.json()["handled"] is True

        # 5. Replay attempt with exact same update_id -> 409
        assert (
            client.post(
                "/telegram/webhook",
                headers={"X-Telegram-Bot-Api-Secret-Token": "secure-secret-token-12345"},
                json={"update_id": 1004, "message": {"from": {"id": 12345}, "text": "/status"}},
            ).status_code
            == 409
        )


def test_unauthorized_skill_upgrades_and_unapproved_licenses(sec_env: Path):
    """Skill upgrades require owner privileges and enforce license approval."""
    mgr = get_token_manager()
    user_token = mgr.generate_token("guest_user", role="user")
    owner_token = mgr.generate_token("owner", role="owner")

    with TestClient(create_app()) as client:
        # Propose an upgrade with rejected license -> 422
        bad_lic = client.post(
            "/skills/social-caption-optimizer/propose-upgrade",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "target_version": "1.0.2",
                "license_name": "GPL-3.0-only",
                "requested_permissions": ["pure:compute"],
                "summary": "License check",
            },
        )
        assert bad_lic.status_code == 422

        # Propose a valid upgrade
        prop = client.post(
            "/skills/social-caption-optimizer/propose-upgrade",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "target_version": "1.0.2",
                "license_name": "Apache-2.0",
                "requested_permissions": ["pure:compute"],
                "summary": "Valid proposal",
            },
        )
        assert prop.status_code == 200
        prop_id = prop.json()["proposal_id"]

        # Non-owner user cannot apply the upgrade -> 403 Forbidden
        non_owner_apply = client.post(
            "/skills/social-caption-optimizer/apply-upgrade",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"proposal_id": prop_id},
        )
        assert non_owner_apply.status_code == 403


def test_repeated_upgrade_proposal_replay_and_expiration(sec_env: Path):
    """Skill upgrade proposals can only be applied once and expire after validity TTL."""
    mgr = get_token_manager()
    owner_token = mgr.generate_token("owner", role="owner")

    with TestClient(create_app(), headers={"Authorization": f"Bearer {owner_token}"}) as client:
        prop = client.post(
            "/skills/social-caption-optimizer/propose-upgrade",
            json={
                "target_version": "1.0.3",
                "license_name": "Apache-2.0",
                "requested_permissions": ["pure:compute"],
                "summary": "Replay test proposal",
            },
        )
        assert prop.status_code == 200
        prop_id = prop.json()["proposal_id"]

        # First apply succeeds
        app1 = client.post(
            "/skills/social-caption-optimizer/apply-upgrade",
            json={"proposal_id": prop_id},
        )
        assert app1.status_code == 200
        assert app1.json()["status"] == "applied"
        assert app1.json()["approved_by"] == "owner"

        # Repeated application (replay) must be rejected with 409 Conflict
        app2 = client.post(
            "/skills/social-caption-optimizer/apply-upgrade",
            json={"proposal_id": prop_id},
        )
        assert app2.status_code == 409

        # Clean up rollback
        rb = client.post("/skills/social-caption-optimizer/rollback")
        assert rb.status_code == 200

        # Expired proposal test
        prop_exp = client.post(
            "/skills/social-caption-optimizer/propose-upgrade",
            json={
                "target_version": "1.0.4",
                "license_name": "Apache-2.0",
                "requested_permissions": ["pure:compute"],
                "summary": "Expiration check",
            },
        )
        exp_id = prop_exp.json()["proposal_id"]
        skills_route._PROPOSALS[exp_id]["expires_at"] = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        res_exp = client.post("/skills/social-caption-optimizer/apply-upgrade", json={"proposal_id": exp_id})
        assert res_exp.status_code == 410


def test_unapproved_content_publishing_blocked(sec_env: Path):
    """Directly publishing unapproved (pending) content is blocked with 400 Bad Request."""
    mgr = get_token_manager()
    token = mgr.generate_token("owner", role="owner")

    with TestClient(create_app(), headers={"Authorization": f"Bearer {token}"}) as client:
        acc = client.post("/accounts/", json={"platform": "instagram", "username": "creator_reel"})
        assert acc.status_code == 201
        account_id = acc.json()["id"]

        content_dir = sec_env / "content"
        content_dir.mkdir(parents=True, exist_ok=True)
        (content_dir / "sample.txt").write_text("Unapproved content draft", encoding="utf-8")

        pipe = client.post(
            "/content/pipeline/run",
            json={
                "folder_path": str(content_dir),
                "platform": "instagram",
                "account_id": account_id,
                "auto_schedule": True,
                "approval_required": True,
            },
        )
        assert pipe.status_code == 200
        sched_id = pipe.json()["scheduled_items"][0]["schedule_id"]

        # Schedule is pending (not yet approved) -> publish MUST fail with 400
        res_unapproved = client.post(
            f"/content/schedule/{sched_id}/publish",
            json={"allow_mock": True},
        )
        assert res_unapproved.status_code == 400


def test_false_publication_success_and_duplicate_idempotency(sec_env: Path):
    """Publish endpoint with allow_mock=False fails without live OAuth; duplicates fail with 409."""
    mgr = get_token_manager()
    token = mgr.generate_token("owner", role="owner")

    with TestClient(create_app(), headers={"Authorization": f"Bearer {token}"}) as client:
        acc = client.post("/accounts/", json={"platform": "instagram", "username": "live_ig_test"})
        assert acc.status_code == 201
        account_id = acc.json()["id"]

        async def _seed_approved_schedule() -> str:
            if db.async_session_factory is None:
                db.init_engine()
                await db.create_tables()
            async with db.async_session_factory() as session:
                asset = ContentAsset(
                    id=str(uuid4()),
                    user_id="owner",
                    title="Test Reel",
                    asset_type=AssetType.VIDEO,
                    status=AssetStatus.READY,
                )
                sched = ContentSchedule(
                    id=str(uuid4()),
                    asset_id=asset.id,
                    account_id=account_id,
                    scheduled_at=datetime.now(timezone.utc),
                    status=ScheduleStatus.APPROVED,
                    approved_by="owner",
                )
                session.add(asset)
                session.add(sched)
                await session.commit()
                return sched.id

        sched_id = asyncio.run(_seed_approved_schedule())

        # Live publication without valid OAuth credentials MUST fail (never fabricate success)
        res_live = client.post(
            f"/content/schedule/{sched_id}/publish",
            json={"allow_mock": False},
        )
        assert res_live.status_code == 400

        # Explicit mock publication succeeds and truthfully reports mode="mock"
        res_mock = client.post(
            f"/content/schedule/{sched_id}/publish",
            json={"allow_mock": True},
        )
        assert res_mock.status_code == 200
        mock_body = res_mock.json()
        assert mock_body["status"] == "success"
        assert mock_body["mode"] == "mock"

        # Subsequent publish attempt on already published schedule rejected with 409 Conflict
        res_dup = client.post(
            f"/content/schedule/{sched_id}/publish",
            json={"allow_mock": True},
        )
        assert res_dup.status_code == 409


def test_malicious_plugin_behavior_blocked():
    """Untrusted executable plugins are prohibited from host execution without OS isolation."""
    with tempfile.TemporaryDirectory() as tmp:
        skill_dir = Path(tmp)
        manifest = {
            "id": "untrusted-plugin",
            "name": "Untrusted Plugin",
            "version": "1.0.0",
            "trust_tier": "untrusted",
            "entrypoint": "skill.py",
            "handler": "run",
            "permissions": ["pure:compute"],
        }
        (skill_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (skill_dir / "skill.py").write_text("def run(p):\n    return {'pwned': True}\n", encoding="utf-8")

        res = run_skill_sandboxed(skill_dir, {})
        assert res.success is False
        assert "prohibited" in (res.error or "").lower()

    bad_code = "import socket\ndef run(p):\n    return {}\n"
    violations = inspect_skill_ast(bad_code, ["pure:compute"])
    assert any("socket" in v for v in violations)


def test_backup_restore_failure_and_active_task_guard(sec_env: Path):
    """Restoring invalid/traversal backups fails and restoring while tasks run returns 409 Conflict."""
    backup_dir = sec_env / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    svc = BackupService(backup_dir=str(backup_dir), encryption_key="sec-test-key")

    # Path traversal rejected
    assert svc.verify_backup("../../etc/passwd")["valid"] is False

    # Corrupted archive rejected
    corrupt_file = backup_dir / "javo_backup_bad.jbackup"
    corrupt_file.write_bytes(b"corrupted-ciphertext")
    assert svc.verify_backup(corrupt_file.name)["valid"] is False
    with pytest.raises(ValueError):
        svc.restore_backup(corrupt_file.name, restore_dir=sec_env / "out")

    # API-level guard: active running task blocks restore with 409 Conflict
    mgr = get_token_manager()
    owner_token = mgr.generate_token("owner", role="owner")
    with TestClient(create_app(), headers={"Authorization": f"Bearer {owner_token}"}) as client:
        bk = client.post("/settings/backup")
        assert bk.status_code == 201
        bk_name = bk.json()["filename"]

        async def _seed_running_task() -> None:
            if db.async_session_factory is None:
                db.init_engine()
                await db.create_tables()
            async with db.async_session_factory() as session:
                session.add(
                    Task(
                        task_id=str(uuid4()),
                        title="Running task",
                        state=TaskState.RUNNING,
                        priority=TaskPriority.NORMAL,
                    )
                )
                await session.commit()

        asyncio.run(_seed_running_task())

        # Path traversal attempt on restore endpoint -> 400
        assert client.post("/settings/restore", json={"filename": "../evil.jbackup"}).status_code == 400

        # Restore while running task active -> 409 Conflict
        res_active = client.post("/settings/restore", json={"filename": bk_name})
        assert res_active.status_code == 409
