"""Bounded, explicit local Ollama inventory check; never generates/downloads."""

import asyncio
from datetime import datetime, timezone
import json
import re

import httpx

from app.services import provider_settings

MODEL_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}")


def _client():
    return httpx.AsyncClient(
        timeout=httpx.Timeout(2, connect=1), trust_env=False, follow_redirects=False
    )


def _canonical(name):
    return name if ":" in name.rsplit("/", 1)[-1] else name + ":latest"


async def check_local_model():
    result = {
        "status": "unavailable",
        "selected_model": None,
        "available_models": [],
        "more_models": False,
        "generation_verified": False,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "message": "Local Ollama could not be checked. Start it and retry.",
    }
    try:
        configuration = provider_settings.effective()["providers"]["ollama"]
        model, endpoint = configuration["model"], configuration["base_url"]
        provider_settings._validate_url("ollama", endpoint)
        if not isinstance(model, str) or not MODEL_NAME.fullmatch(model):
            raise ValueError("Invalid model")
        if not isinstance(configuration.get("enabled"), bool):
            raise ValueError("Invalid enabled state")
        result["selected_model"] = model
    except Exception:
        return {
            **result,
            "status": "invalid_configuration",
            "message": "Saved local provider configuration is unavailable. Recover storage or edit Settings.",
        }
    if not configuration["enabled"]:
        return {**result, "status": "disabled", "message": "The saved local provider is disabled."}
    try:
        async with asyncio.timeout(3):
            async with _client() as client:
                async with client.stream(
                    "GET",
                    endpoint.rstrip("/") + "/api/tags",
                    headers={"Accept": "application/json", "Accept-Encoding": "identity"},
                ) as response:
                    # Redirects are refused, even from a loopback server.
                    if response.status_code != 200:
                        raise ValueError("Inventory unavailable")
                    if response.headers.get("content-encoding", "identity").lower() != "identity":
                        raise ValueError("Compressed inventory is unsupported")
                    payload = bytearray()
                    async for chunk in response.aiter_bytes():
                        if len(payload) + len(chunk) > 1048576:
                            raise ValueError("Inventory too large")
                        payload.extend(chunk)
        inventory = json.loads(payload)
        rows = inventory["models"]
        if not isinstance(rows, list) or len(rows) > 1000:
            raise ValueError("Invalid inventory")
        names = []
        for item in rows:
            if not isinstance(item, dict):
                raise ValueError("Invalid model record")
            name = item.get("name") or item.get("model")
            if not isinstance(name, str) or not MODEL_NAME.fullmatch(name):
                raise ValueError("Invalid model name")
            if name not in names:
                names.append(name)
        found = any(_canonical(name) == _canonical(model) for name in names)
        return {
            **result,
            "status": "available" if found else "model_missing",
            "available_models": names[:100],
            "more_models": len(names) > 100,
            "message": "The saved model is listed by loopback Ollama. Generation and performance have not been tested."
            if found
            else "Ollama responded, but the saved model is not listed. Install a compatible model separately or select an installed one.",
        }
    except Exception:
        # Never return response bodies, endpoints, credentials or raw errors.
        return result
