"""Integration tests for Telegram authorization/commands, Voice Hinglish confirmation, and FFmpeg."""

from __future__ import annotations

from pathlib import Path
import subprocess

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.media_processor import MediaProcessor


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "tg_voice_test.db"
    sched_path = tmp_path / "tg_voice_sched.db"
    monkeypatch.setenv("JAVO_DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setenv("JAVO_SCHEDULER_DB_URL", f"sqlite:///{sched_path}")
    monkeypatch.setenv("JAVO_CONTENT_ROOT", str(tmp_path / "content"))
    monkeypatch.setenv("JAVO_UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("JAVO_BACKUP_DIR", str(tmp_path / "backups"))
    monkeypatch.setenv("JAVO_THUMBNAIL_DIR", str(tmp_path / "thumbnails"))

    import app.config as cfg
    import app.api.routes.telegram as tg_route
    from app.core.security import get_token_manager

    cfg._settings = None
    tg_route._TELEGRAM_OVERRIDES.clear()
    tg_route._PROCESSED_UPDATE_IDS.clear()

    token = get_token_manager().generate_token("owner", device_id="desktop-1", role="owner")
    app = create_app()
    with TestClient(app, headers={"Authorization": f"Bearer {token}"}) as test_client:
        yield test_client

    tg_route._TELEGRAM_OVERRIDES.clear()
    tg_route._PROCESSED_UPDATE_IDS.clear()
    cfg._settings = None


def test_telegram_fail_closed_and_all_commands(client: TestClient):
    # Unpaired user cannot run /status even when allowed_users is empty
    unauth = client.post(
        "/telegram/webhook",
        json={"message": {"from": {"id": 99999}, "text": "/status"}},
    )
    assert unauth.status_code == 403

    # /start returns numeric user ID for pairing
    start_unpaired = client.post(
        "/telegram/webhook",
        json={"message": {"from": {"id": 99999}, "text": "/start"}},
    )
    assert start_unpaired.status_code == 200
    assert "99999" in start_unpaired.json()["reply_text"]

    # Pair user 12345 and configure synthetic bot token (must remain redacted on GET)
    cfg_res = client.put(
        "/telegram/config",
        json={"bot_token": "123456:synthetic-bot-token", "allowed_users": ["12345"]},
    )
    assert cfg_res.status_code == 200
    assert cfg_res.json()["configured"] is True
    assert "bot_token" not in cfg_res.json()

    # Different user still blocked
    wrong_user = client.post(
        "/telegram/webhook",
        json={"message": {"from": {"id": 99999}, "text": "/status"}},
    )
    assert wrong_user.status_code == 403

    # Paired user can execute all supported bot commands
    for cmd in ["/help", "/status", "/goals", "/schedule", "/analytics", "/agents", "/accounts", "/security", "/pause", "/resume"]:
        r = client.post(
            "/telegram/webhook",
            json={"message": {"from": {"id": 12345}, "text": cmd}},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["handled"] is True
        assert body["reply_text"]
        assert "synthetic-bot-token" not in body["reply_text"]


def test_voice_hinglish_and_confirmation_gate(client: TestClient):
    # Sensitive Hinglish scheduling command must require confirmation first
    r1 = client.post(
        "/voice/command",
        json={
            "transcript": "Hey Javo, mere Facebook ke liye aaj ki posts schedule karo",
            "language": "hi-IN",
            "confirmed": False,
        },
    )
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["intent"] == "content_schedule"
    assert d1["requires_confirmation"] is True
    assert d1["action_taken"] == "awaiting_confirmation"

    # Confirmed execution proceeds
    r2 = client.post(
        "/voice/command",
        json={
            "transcript": "Hey Javo, mere Facebook ke liye aaj ki posts schedule karo",
            "language": "hi-IN",
            "confirmed": True,
        },
    )
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["requires_confirmation"] is False
    assert d2["action_taken"] == "schedule_queued"


def test_dashboard_static_mount_served_locally(tmp_path: Path, monkeypatch):
    from fastapi.routing import Mount

    app = create_app()
    has_built_mount = any(isinstance(r, Mount) and r.path == "/dashboard" for r in app.routes)
    if has_built_mount:
        with TestClient(app) as live_client:
            res = live_client.get("/dashboard/")
            assert res.status_code == 200
            assert "Javo Agents" in res.text
        return

    # Backend-only CI checkouts omit built frontend dist/; verify static mount with a staged bundle.
    db_path = tmp_path / "dash_mount.db"
    sched_path = tmp_path / "dash_sched.db"
    monkeypatch.setenv("JAVO_DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setenv("JAVO_SCHEDULER_DB_URL", f"sqlite:///{sched_path}")
    import app.config as cfg

    cfg._settings = None
    staged_dist = tmp_path / "dashboard_dist"
    staged_dist.mkdir(parents=True, exist_ok=True)
    (staged_dist / "index.html").write_text(
        "<!doctype html><html><title>Javo Agents</title><body>Javo Agents Dashboard</body></html>",
        encoding="utf-8",
    )
    monkeypatch.setenv("JAVO_DASHBOARD_DIST", str(staged_dist))
    try:
        with TestClient(create_app()) as staged_client:
            staged_res = staged_client.get("/dashboard/")
            assert staged_res.status_code == 200
            assert "Javo Agents" in staged_res.text
    finally:
        cfg._settings = None


def test_media_processor_with_local_ffmpeg(tmp_path: Path):
    proc = MediaProcessor()
    if not proc.is_ffmpeg_available():
        pytest.skip("FFmpeg binary not on PATH")

    sample_mp4 = tmp_path / "sample.mp4"
    subprocess.run(
        [
            proc.ffmpeg_path,
            "-y",
            "-f", "lavfi",
            "-i", "color=c=0x0B1026:s=320x240:d=1",
            "-pix_fmt", "yuv420p",
            str(sample_mp4),
        ],
        check=True,
        capture_output=True,
        timeout=20,
    )
    info = proc.probe_media(sample_mp4)
    assert info.valid is True
    assert info.width == 320
    assert info.height == 240

    thumb = proc.generate_thumbnail(sample_mp4, output_path=tmp_path / "thumb.jpg", timestamp_sec=0.2)
    assert thumb is not None
    assert Path(thumb).exists() and Path(thumb).stat().st_size > 0
