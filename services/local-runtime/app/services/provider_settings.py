"""Durable provider configuration shared by the owner API and AI router."""

from __future__ import annotations

import re
from urllib.parse import urlsplit

from app.config import get_settings
from app.core.provider_store import ProviderVault

PROVIDERS = {"ollama", "gemini", "openai"}
AI_FIELDS = {
    "default_ai_provider",
    "ai_daily_budget",
    "ai_monthly_budget",
    "max_tokens_per_request",
}


def vault() -> ProviderVault:
    settings = get_settings()
    return ProviderVault(settings.provider_config_path, settings.encryption_key)


def effective() -> dict:
    s = get_settings()
    saved = vault().read()
    providers = {
        "ollama": {
            "enabled": True,
            "model": s.ollama_default_model,
            "base_url": s.ollama_base_url,
            "api_key": None,
        },
        "gemini": {
            "enabled": bool(s.gemini_api_key),
            "model": s.gemini_model,
            "base_url": None,
            "api_key": s.gemini_api_key,
        },
        "openai": {
            "enabled": bool(s.openai_api_key),
            "model": s.openai_model,
            "base_url": s.openai_base_url,
            "api_key": s.openai_api_key,
        },
    }
    for name in PROVIDERS:
        providers[name].update(saved["providers"].get(name, {}))
    settings = {name: getattr(s, name) for name in AI_FIELDS}
    settings.update(saved["settings"])
    return {"providers": providers, "settings": settings}


def metadata() -> list[dict]:
    result = [
        {
            "name": name,
            "enabled": cfg["enabled"],
            "model": cfg["model"],
            "base_url": cfg["base_url"],
            "has_api_key": bool(cfg["api_key"]),
        }
        for name, cfg in effective()["providers"].items()
    ]
    for item in result:
        try:
            _validate_url(item["name"], item["base_url"])
        except ValueError:
            # Legacy environment endpoints may contain credentials or query secrets.
            item["base_url"] = None
    return result


def _validate_url(name: str, value: str | None) -> None:
    if name == "gemini":
        if value is not None:
            raise ValueError("Gemini uses its official endpoint; custom base URL is unsupported")
        return
    try:
        url = urlsplit(value or "")
        port = url.port
    except ValueError:
        raise ValueError("Invalid provider endpoint") from None
    if (
        not url.hostname
        or url.username
        or url.password
        or url.query
        or url.fragment
        or (port is not None and not 1 <= port <= 65535)
    ):
        raise ValueError("Provider endpoint must not contain credentials, query or fragment")
    local = url.hostname.lower() in {"localhost", "127.0.0.1", "::1"}
    if name == "ollama" and not local:
        raise ValueError("Local Ollama must use a loopback endpoint")
    if url.scheme != "https" and not (url.scheme == "http" and local):
        raise ValueError("Remote provider endpoints require HTTPS")


def update_provider(name: str, patch: dict) -> list[dict]:
    if name not in PROVIDERS:
        raise KeyError("Unknown AI provider")
    if set(patch) - {"enabled", "model", "base_url", "api_key"}:
        raise ValueError("Unknown provider fields")
    if "model" in patch and (
        not isinstance(patch["model"], str)
        or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}", patch["model"])
    ):
        raise ValueError("Model must be a nonempty supported identifier")
    if "api_key" in patch:
        key = patch["api_key"]
        if key is not None and (not isinstance(key, str) or not 1 <= len(key) <= 4096):
            raise ValueError("Provider key must be a nonempty string or null to remove it")
        if name == "ollama" and key:
            raise ValueError("Local Ollama does not accept a cloud API key")
        if key is None and "enabled" not in patch and name != "ollama":
            patch = {**patch, "enabled": False}
    if "enabled" in patch and not isinstance(patch["enabled"], bool):
        raise ValueError("Enabled must be boolean")
    if "base_url" in patch:
        _validate_url(name, patch["base_url"])

    def mutate(document):
        current = document["providers"].get(name, {})
        document["providers"][name] = {**current, **patch}

    vault().update(mutate)
    return metadata()


def update_ai_settings(patch: dict) -> dict:
    if set(patch) - AI_FIELDS:
        raise ValueError("Only AI defaults and zero budgets can be edited in this build")
    if "default_ai_provider" in patch and patch["default_ai_provider"] not in PROVIDERS:
        raise ValueError("Unknown default AI provider")
    if "max_tokens_per_request" in patch and not 1 <= patch["max_tokens_per_request"] <= 32768:
        raise ValueError("Max tokens must be between 1 and 32768")
    for name in ("ai_daily_budget", "ai_monthly_budget"):
        if name in patch and patch[name] != 0:
            raise ValueError(
                "Paid budget changes require verified prices and explicit spending authorization; keep budgets zero"
            )
    vault().update(lambda document: document["settings"].update(patch))
    return effective()["settings"]


def remove_credentials(name: str) -> list[dict]:
    return update_provider(name, {"api_key": None, "enabled": False})
