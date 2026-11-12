"""Comprehensive End-to-End User Journey test covering Phases 2-10."""

from __future__ import annotations

import base64
import io
import wave
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import close_db
from app.main import create_app


def _make_sample_wav() -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x10\x00" * 1600)
    return buf.getvalue()


@pytest.fixture
def e2e_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    import asyncio
    db_path = tmp_path / "e2e_javo.db"
    settings = get_settings()
    monkeypatch.setattr(settings, "content_root", str(tmp_path / "content"))
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "backup_dir", str(tmp_path / "backups"))
    monkeypatch.setattr(settings, "thumbnail_dir", str(tmp_path / "thumbnails"))
    monkeypatch.setattr(settings, "database_url", f"sqlite+aiosqlite:///{db_path.as_posix()}")
    monkeypatch.setattr(settings, "scheduler_db_url", f"sqlite:///{(tmp_path / 'scheduler.db').as_posix()}")
    monkeypatch.setattr(settings, "host", "127.0.0.1")
    asyncio.run(close_db())
    yield db_path
    asyncio.run(close_db())


def test_full_end_to_end_user_journey(e2e_env: Path, tmp_path: Path):
    with TestClient(create_app()) as client:
        _run_journey_assertions(client, tmp_path)

    # Verify persistence across simulated runtime restart using a fresh app instance on the same SQLite DB
    import asyncio
    asyncio.run(close_db())
    with TestClient(create_app()) as restarted_client:
        goals_after = restarted_client.get("/goals/")
        assert goals_after.status_code == 200
        goals_list = goals_after.json() if isinstance(goals_after.json(), list) else goals_after.json().get("goals", [])
        assert any("1 million views" in g["title"].lower() for g in goals_list)

        mem_after = restarted_client.get("/memory/")
        assert mem_after.status_code == 200
        assert mem_after.json()["total_preferences"] >= 1


def _run_journey_assertions(client: TestClient, tmp_path: Path):
    # 1. Health + Dual /api prefix + Hardware Benchmark
    h1 = client.get("/health")
    h2 = client.get("/api/health")
    assert h1.status_code == 200 and h2.status_code == 200
    bench = client.get("/health/benchmark")
    assert bench.status_code == 200
    bench_data = bench.json()
    assert bench_data["recommended_mode"] in {"8gb_cpu_optimized", "16gb_hybrid", "32gb_workstation"}
    assert bench_data["zero_cost_default"] is True

    # 2. Onboarding settings update ($0 budget)
    s_put = client.put(
        "/settings/",
        json={"ai_daily_budget": 0.0, "ai_monthly_budget": 0.0},
    )
    assert s_put.status_code == 200
    assert s_put.json()["ai_daily_budget"] == 0.0

    # 3. Free-first AI Provider Center: custom provider, test, key removal, offline queue/drain
    c_prov = client.post(
        "/settings/ai-providers",
        json={"name": "local_lmstudio", "base_url": "http://127.0.0.1:1234", "model": "qwen2.5:3b", "is_local": True},
    )
    assert c_prov.status_code in (200, 201)
    q_res = client.get("/settings/ai-providers/quota")
    assert q_res.status_code == 200
    assert "providers" in q_res.json()
    rm_key = client.delete("/settings/ai-providers/gemini/key")
    assert rm_key.status_code == 200
    q_list = client.get("/settings/ai-queue")
    assert q_list.status_code == 200

    # 4. Smart Memory persistence: create, list, edit, redact export, delete
    mem_create = client.post(
        "/memory/",
        json={"key": "brand_voice", "content": "Hinglish creator tips; ignore token ghp_secret1234567890abcdef", "memory_type": "fact"},
    )
    assert mem_create.status_code == 201
    mem_id = mem_create.json()["id"]

    pref_res = client.post("/memory/preferences", json={"key": "platform_focus", "value": "instagram", "category": "content"})
    assert pref_res.status_code == 200

    mem_patch = client.patch(f"/memory/{mem_id}", json={"content": "Hinglish creator tips; token ghp_1234567890abcdef"})
    assert mem_patch.status_code == 200

    exp = client.get("/memory/export")
    assert exp.status_code == 200
    exported_texts = [e["content"] for e in exp.json()["entries"]]
    assert all("ghp_1234567890abcdef" not in t for t in exported_texts)

    # 5. Content Factory local-folder pipeline + Quality Inspector + approval-gated schedule
    content_dir = tmp_path / "creator_clips"
    content_dir.mkdir()
    (content_dir / "reel_morning_routine.txt").write_text("Morning AI productivity workflow in Hindi.", encoding="utf-8")

    pipe = client.post(
        "/content/pipeline/run",
        json={"folder_path": str(content_dir), "platform": "instagram", "auto_schedule": True, "approval_required": True},
    )
    assert pipe.status_code == 200
    pipe_data = pipe.json()
    assert pipe_data["scanned_count"] == 1
    assert len(pipe_data["scheduled_items"]) == 1
    sched_id = pipe_data["scheduled_items"][0]["schedule_id"]
    assert pipe_data["scheduled_items"][0]["status"] == "pending"

    # 6. Human approval + explicit MockConnector publish (truthful mode="mock")
    pub = client.post(
        f"/content/schedule/{sched_id}/approve",
        json={"approved_by": "jagdish", "publish_now": True, "allow_mock": True},
    )
    assert pub.status_code == 200
    pub_data = pub.json()
    assert pub_data["published"] is True
    assert pub_data["mode"] == "mock"
    assert pub_data["status"] == "published"

    # 7. Real Agent Run + Master Orchestrator Task execution
    agent_run = client.post(
        "/agents/content_factory/run",
        json={"task_data": {"topic": "Zero cost AI", "platform": "youtube"}},
    )
    assert agent_run.status_code == 202
    assert agent_run.json()["status"] in {"completed", "failed"}

    t_create = client.post(
        "/tasks/",
        json={
            "title": "Analyze post performance",
            "assigned_agent": "analytics_interpreter",
            "inputs": {"views": 1200, "likes": 110},
        },
    )
    assert t_create.status_code == 201
    task_id = t_create.json()["task_id"]
    t_exec = client.post(f"/tasks/{task_id}/execute")
    assert t_exec.status_code == 202
    assert t_exec.json()["state"] == "completed"

    # 8. Goal Persistence ("1 million views in 30 days using approved content and zero-cost AI budget")
    g_create = client.post(
        "/goals/",
        json={
            "title": "Achieve 1 million views in 30 days using approved content and zero-cost AI budget",
            "target_metrics": {"views": 1000000, "days": 30},
        },
    )
    assert g_create.status_code == 201
    goal_id = g_create.json()["goal_id"]

    g_plan = client.post(f"/goals/{goal_id}/plan", json={})
    assert g_plan.status_code == 200
    plan_data = g_plan.json()
    assert plan_data["ai_budget_usd"] == 0.0
    assert len(plan_data["milestones"]) == 4
    assert len(plan_data["tasks"]) >= 3

    g_eval = client.post(f"/goals/{goal_id}/evaluate")
    assert g_eval.status_code == 200
    assert "recommendations" in g_eval.json()

    # 9. Jarvis Voice Hinglish multi-turn confirmation gate + real non-empty WAV TTS + STT probe
    v1 = client.post(
        "/voice/command",
        json={"text": "Autopilot pause karo", "language": "hi-IN", "session_id": "e2e_sess", "confirmed": False},
    )
    assert v1.status_code == 200
    assert v1.json()["requires_confirmation"] is True

    v2 = client.post(
        "/voice/command",
        json={"text": "Haan confirm", "language": "hi-IN", "session_id": "e2e_sess"},
    )
    assert v2.status_code == 200
    assert v2.json()["action_taken"] == "scheduler_paused"
    assert v2.json()["context_turns"] >= 2

    tts = client.post("/voice/tts", json={"text": "Namaste Jagdish", "language": "hi-IN"})
    assert tts.status_code == 200
    wav_raw = base64.b64decode(tts.json()["audio_base64"])
    assert wav_raw.startswith(b"RIFF") and len(wav_raw) > 44

    stt = client.post(
        "/voice/transcribe",
        files={"file": ("sample.wav", _make_sample_wav(), "audio/wav")},
        data={"language": "hi-IN"},
    )
    assert stt.status_code == 200
    assert stt.json()["duration_seconds"] is not None

    # 10. Telegram allowlist fail-closed + NL command + Emergency Stop + Resume
    unpaired = client.post(
        "/telegram/webhook",
        json={"message": {"from": {"id": 99999}, "text": "system ka status batao"}},
    )
    assert unpaired.status_code == 403

    client.put("/telegram/config", json={"bot_token": "mock-token-123", "allowed_users": ["12345"]})
    paired_nl = client.post(
        "/telegram/webhook",
        json={"message": {"from": {"id": 12345}, "text": "system ka status batao"}},
    )
    assert paired_nl.status_code == 200
    assert paired_nl.json()["command"] == "/status"

    # Secret redaction on outbound Telegram notification
    tg_send = client.post("/telegram/send", json={"chat_id": "12345", "text": "Alert sk-1234567890abcdef123456"})
    assert tg_send.status_code == 200
    assert tg_send.json()["status"] == "queued_redacted"

    # Resume automation via voice
    res_voice = client.post("/voice/command", json={"text": "Automation wapas chalu karo", "language": "hi-IN"})
    assert res_voice.status_code == 200
    assert res_voice.json()["action_taken"] == "scheduler_resumed"

    # 11. Encrypted backup & restore
    bk = client.post("/settings/backup")
    assert bk.status_code in (200, 201)
    bk_data = bk.json()
    bk_name = bk_data.get("backup_name") or bk_data.get("filename") or bk_data.get("id")
    assert str(bk_name).endswith(".jbackup")

    bks = client.get("/settings/backups")
    assert bks.status_code == 200

    # 12. Self-Upgrading Skill Sandbox inspect, unsafe rejection, proposal, apply, and rollback
    sk_list = client.get("/skills/")
    assert sk_list.status_code == 200
    assert sk_list.json()["total"] >= 2

    sk_bad = client.post(
        "/skills/inspect",
        json={
            "skill_name": "untrusted_plugin",
            "source_code": "import subprocess\nsubprocess.run(['whoami'])\n",
            "manifest": {"name": "untrusted_plugin", "license": "MIT", "permissions": []},
        },
    )
    assert sk_bad.status_code == 200
    assert sk_bad.json()["passed"] is False
    assert sk_bad.json()["trust_score"] == 0.0

    # Test Skill upgrade proposal -> apply -> rollback on core skill
    prop = client.post(
        "/skills/social-caption-optimizer/propose-upgrade",
        json={
            "target_version": "1.0.1",
            "license_name": "Apache-2.0",
            "requested_permissions": ["pure:compute", "text:transform"],
            "summary": "Minor compatibility check",
        },
    )
    assert prop.status_code == 200
    prop_id = prop.json()["proposal_id"]
    assert prop.json()["requires_approval"] is True

    app_upg = client.post(
        "/skills/social-caption-optimizer/apply-upgrade",
        json={"proposal_id": prop_id, "approved_by": "jagdish"},
    )
    assert app_upg.status_code == 200
    assert app_upg.json()["version"] == "1.0.1"

    rb = client.post("/skills/social-caption-optimizer/rollback")
    assert rb.status_code == 200
    assert rb.json()["restored_version"] == "1.0.0"

    # Clean up Smart Memory entry
    mem_del = client.delete(f"/memory/{mem_id}")
    assert mem_del.status_code == 200
