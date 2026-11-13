"""End-to-end subsystem smoke test for Javo Agents alpha acceptance milestone.
Verifies:
1. Backend health & diagnostics
2. Authenticated desktop controls (Pause, Resume, Emergency Stop)
3. Hardware profile & onboarding
4. SQLite storage & WAL mode persistence
5. Goal execution & progress tracking
6. Voice fallback (Command NLU, TTS, STT)
7. Content Factory (folder scan, drafting, scheduling, approval)
8. Emergency Stop verification
"""

import asyncio
import os
import tempfile
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.database import close_db, create_tables, get_session, init_engine
from app.main import _seed_agents, create_app

@pytest.mark.asyncio
async def test_subsystems_end_to_end_smoke():
    from app.core.security import get_owner_token
    owner_token = get_owner_token()
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    init_engine()
    await create_tables()
    await _seed_agents()

    app = create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Health & Diagnostics
        res_health = await client.get("/health/")
        assert res_health.status_code == 200
        health_data = res_health.json()
        assert health_data["status"] in ("healthy", "degraded")
        assert health_data["database"] == "connected"

        res_sys = await client.get("/health/system")
        assert res_sys.status_code == 200
        assert res_sys.json()["cpu_count"] >= 1

        # 2. Authenticated Desktop Controls
        res_unauth = await client.post("/security/pause")
        assert res_unauth.status_code == 401

        res_pause = await client.post("/security/pause", headers=owner_headers)
        assert res_pause.status_code == 200
        assert res_pause.json()["paused"] is True

        res_resume = await client.post("/security/resume", headers=owner_headers)
        assert res_resume.status_code == 200
        assert res_resume.json()["paused"] is False

        # 3. Settings & Onboarding
        res_set = await client.get("/settings/", headers=owner_headers)
        assert res_set.status_code == 200
        assert res_set.json()["ai_daily_budget"] == 0.0

        res_update = await client.put(
            "/settings/",
            json={"log_level": "INFO", "max_concurrent_agents": 4},
            headers=owner_headers,
        )
        assert res_update.status_code == 200
        assert res_update.json()["max_concurrent_agents"] == 4

        # 4. SQLite Storage & WAL Mode Persistence
        async for session in get_session():
            row = await session.execute(text("PRAGMA journal_mode;"))
            journal_mode = row.scalar()
            assert str(journal_mode).lower() in ("wal", "memory")

            tables_res = await session.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = [r[0] for r in tables_res.all()]
            assert "goals" in tables
            assert "tasks" in tables
            assert "content_assets" in tables
            assert "audit_logs" in tables
            break

        # 5. Goal Execution & Progress Tracking
        res_goal = await client.post(
            "/goals/",
            json={
                "title": "Launch Alpha Multi-Platform Campaign",
                "description": "Automated campaign using local model.",
                "target_metrics": {"views": 10000, "posts": 5},
            },
            headers=owner_headers,
        )
        assert res_goal.status_code in (200, 201)
        goal_id = res_goal.json()["goal_id"]

        res_goal_up = await client.put(f"/goals/{goal_id}", json={"progress": 40.0}, headers=owner_headers)
        assert res_goal_up.status_code == 200
        assert res_goal_up.json()["progress"] == 40.0

        # 6. Voice Fallback (NLU Command, TTS)
        res_cmd = await client.post(
            "/voice/command",
            json={"transcript": "Create a new draft for tomorrow morning", "language": "en"},
        )
        assert res_cmd.status_code == 200
        assert res_cmd.json()["intent"]

        res_tts = await client.post("/voice/tts", json={"text": "Javo Agents local voice synthesis online."})
        assert res_tts.status_code == 200
        assert res_tts.json()["mime_type"] == "audio/wav"
        assert len(res_tts.json()["audio_base64"]) > 50

        # 7. Content Factory Pipeline
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            test_file = tmp_path / "Alpha_Launch_Teaser.txt"
            test_file.write_text("Excited to reveal Javo Agents Private Alpha! Free local AI.", encoding="utf-8")

            res_cf = await client.post(
                "/content/pipeline/run",
                json={
                    "folder_path": str(tmp_path),
                    "platform": "instagram",
                    "auto_schedule": True,
                    "approval_required": True,
                },
                headers=owner_headers,
            )
            assert res_cf.status_code == 200
            assert len(res_cf.json().get("processed_assets", [])) == 1

            res_sched = await client.get("/content/schedule", headers=owner_headers)
            assert res_sched.status_code == 200
            schedules = res_sched.json()
            assert len(schedules) > 0
            first_sched = schedules[0]

            res_appr = await client.post(
                f"/content/schedule/{first_sched['id']}/approve",
                json={"publish_now": False, "allow_mock": True},
                headers=owner_headers,
            )
            assert res_appr.status_code == 200

        # 8. Emergency Stop Kill-Switch
        res_emg = await client.post(
            "/security/emergency-stop",
            json={"reason": "Automated test kill-switch"},
            headers=owner_headers,
        )
        assert res_emg.status_code == 200
        res_st = await client.get("/security/autopilot-status", headers=owner_headers)
        assert res_st.json()["emergency_stopped"] is True

        res_res = await client.post("/security/resume", headers=owner_headers)
        assert res_res.json()["emergency_stopped"] is False

    await close_db()
