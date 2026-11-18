"""Explicit real-model acceptance check using only an isolated Javo profile.

Requires an existing local-only Ollama service and an already installed model.
Does not install/pull a model, enable cloud spending or modify an owner profile.
Actual production capacity admission remains enabled. Not a general benchmark.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile
import time
from uuid import uuid4


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="qwen2.5:0.5b")
    parser.add_argument(
        "--workflow", action="store_true", help="Also run a reviewed saved local drafting workflow"
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "services/local-runtime"))
    # Never inherit an owner's private profile, API key or endpoint settings.
    for name in list(os.environ):
        if name.startswith("JAVO_"):
            del os.environ[name]
    with tempfile.TemporaryDirectory(prefix="javo-real-local-model-") as folder:
        data = Path(folder)
        values = {
            "OWNER_ACCESS_TOKEN": secrets.token_urlsafe(32),
            "ENCRYPTION_KEY": secrets.token_urlsafe(48),
            "DATABASE_URL": "sqlite+aiosqlite:///" + str(data / "runtime.db"),
            "SCHEDULER_DB_URL": "sqlite:///" + str(data / "scheduler.db"),
            "PROVIDER_CONFIG_PATH": str(data / "providers.enc"),
            "ACCOUNT_CREDENTIALS_DIR": str(data / "accounts"),
            "CONTROL_STATE_PATH": str(data / "control.json"),
            "USAGE_LEDGER_PATH": str(data / "usage.sqlite"),
            "OLLAMA_BASE_URL": "http://127.0.0.1:11434",
        }
        for name in ("CONTENT_ROOT", "UPLOAD_DIR", "BACKUP_DIR", "THUMBNAIL_DIR"):
            values[name] = str(data / name.lower())
        os.environ.update({"JAVO_" + name: value for name, value in values.items()})
        from fastapi.testclient import TestClient
        from app import config
        from app.core import resource_manager
        from app.main import create_app

        headers = {"Authorization": "Bearer " + values["OWNER_ACCESS_TOKEN"]}
        config._settings = None
        resource_manager._resource_manager = None
        with TestClient(create_app(), headers=headers) as client:
            saved = client.put(
                "/api/settings/ai-providers/ollama",
                json={"model": args.model, "base_url": values["OLLAMA_BASE_URL"], "enabled": True},
            )
            if saved.status_code != 200:
                raise RuntimeError("Local test configuration was rejected")
            defaults = client.put(
                "/api/settings/",
                json={"max_tokens_per_request": 48, "default_ai_provider": "ollama"},
            )
            assert defaults.status_code == 200
            inventory = client.post("/api/settings/ai-providers/ollama/check").json()
            assert inventory["status"] == "available", inventory["message"]
            assert client.post("/api/security/resume").status_code == 200
            started = time.monotonic()
            response = client.post(
                "/api/voice/command",
                json={
                    "transcript": "Write one short English sentence welcoming a local creator to Javo.",
                    "language": "en",
                    "provider": "ollama",
                },
            )
            if response.status_code != 200:
                raise RuntimeError(
                    "Real companion generation unavailable; inspect resource headroom/local model. No production admission safeguard was changed."
                )
            result = response.json()
            assert result["intent"] == "assistant_text" and result["response_text"].strip()
            assert result["data"]["model"] == args.model
            assert result["data"]["actions_executed"] is False
            usage = client.get("/api/settings/ai-usage").json()
            assert usage["total_requests"] == 1 and usage["total_tokens"] > 0
            evidence = {
                "marker": "REAL_LOCAL_MODEL_COMPANION_LEDGER_RESTART_OK",
                "model": args.model,
                "seconds": round(time.monotonic() - started, 3),
                "response": result["response_text"],
                "reported_tokens": usage["total_tokens"],
                "production_resource_admission": True,
                "cloud_execution": False,
            }
            if args.workflow:
                start_id, text_id, end_id = (str(uuid4()) for _ in range(3))
                created = client.post(
                    "/api/workflows/",
                    json={
                        "name": "Real local workflow acceptance",
                        "nodes": [
                            {
                                "id": start_id,
                                "node_type": "trigger",
                                "label": "Manual start",
                                "is_entry_point": True,
                            },
                            {
                                "id": text_id,
                                "node_type": "ai_prompt",
                                "label": "Local draft",
                                "config": {
                                    "prompt": "Write one short friendly welcome sentence for a local creator.",
                                    "provider": "ollama",
                                    "max_tokens": 48,
                                },
                            },
                            {"id": end_id, "node_type": "end", "label": "End"},
                        ],
                        "edges": [
                            {"source_node_id": start_id, "target_node_id": text_id},
                            {"source_node_id": text_id, "target_node_id": end_id},
                        ],
                    },
                )
                assert created.status_code == 201
                graph = created.json()
                queued = client.post(
                    "/api/workflows/" + graph["id"] + "/execute",
                    json={
                        "expected_revision": graph["revision"],
                        "fingerprint": graph["fingerprint"],
                    },
                )
                assert queued.status_code == 202
                run_id = queued.json()["id"]
                began = time.monotonic()
                deadline = began + 90
                while time.monotonic() < deadline:
                    receipt = client.get("/api/workflows/executions/" + run_id).json()
                    if receipt["status"] in {"completed", "failed", "cancelled"}:
                        break
                    time.sleep(0.1)
                assert receipt["status"] == "completed", (
                    "Actual local workflow did not complete within its acceptance window"
                )
                drafts = [
                    event["output"]
                    for event in receipt["execution_log"]
                    if event.get("output", {}).get("text")
                ]
                assert (
                    len(drafts) == 1
                    and drafts[0]["model"] == args.model
                    and drafts[0]["actions_executed"] is False
                )
                evidence.update(
                    workflow_marker="REAL_SAVED_LOCAL_WORKFLOW_OUTPUT_LEDGER_OK",
                    workflow_seconds=round(time.monotonic() - began, 3),
                    workflow_response=drafts[0]["text"],
                )
                usage = client.get("/api/settings/ai-usage").json()
                assert (
                    usage["total_requests"] == 2
                    and usage["total_tokens"] > evidence["reported_tokens"]
                )
                evidence["reported_tokens"] = usage["total_tokens"]
        config._settings = None
        resource_manager._resource_manager = None
        with TestClient(create_app(), headers=headers) as client:
            restored = client.get("/api/settings/ai-usage").json()
            assert (
                restored["total_requests"] == (2 if args.workflow else 1)
                and restored["total_tokens"] == usage["total_tokens"]
            )
        print(json.dumps(evidence, ensure_ascii=False))


if __name__ == "__main__":
    main()
