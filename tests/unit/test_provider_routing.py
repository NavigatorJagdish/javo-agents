"""No external provider requests: capture payloads through httpx MockTransport."""

import json

import httpx
import pytest

from app.config import Settings
from app.core.ai_router import AIRouter, AIResponse
from app.services import provider_settings as providers


@pytest.fixture
def configured(tmp_path, monkeypatch):
    settings = Settings(
        provider_config_path=str(tmp_path / "providers.enc"),
        encryption_key="synthetic-routing-master-key-" * 2,
    )
    monkeypatch.setattr(providers, "get_settings", lambda: settings)
    return settings


@pytest.mark.asyncio
async def test_router_reads_persisted_local_model(configured, monkeypatch):
    providers.update_provider(
        "ollama", {"model": "owner-local-model", "base_url": "http://127.0.0.1:11434"}
    )
    seen = []

    def handle(request):
        seen.append(json.loads(request.content))
        return httpx.Response(
            200, json={"response": "local response", "prompt_eval_count": 2, "eval_count": 2}
        )

    original_client = httpx.AsyncClient
    monkeypatch.setattr(
        "app.core.ai_router.httpx.AsyncClient",
        lambda **kwargs: original_client(transport=httpx.MockTransport(handle)),
    )
    result = await AIRouter().generate("Hello", fallback_to_local=False)
    assert result.provider == "ollama" and seen[0]["model"] == "owner-local-model"


@pytest.mark.asyncio
async def test_gemini_key_is_in_header_never_url(configured, monkeypatch):
    key = "synthetic-header-only-key"
    providers.update_provider("gemini", {"api_key": key, "enabled": True})

    def handle(request):
        assert key not in str(request.url)
        assert request.headers["x-goog-api-key"] == key
        return httpx.Response(
            200, json={"candidates": [{"content": {"parts": [{"text": "fixture"}]}}]}
        )

    original_client = httpx.AsyncClient
    monkeypatch.setattr(
        "app.core.ai_router.httpx.AsyncClient",
        lambda **kwargs: original_client(transport=httpx.MockTransport(handle)),
    )
    await AIRouter()._call_gemini("Hello", None, None, 0.7, 50)


@pytest.mark.asyncio
async def test_disabled_provider_cannot_be_called(configured):
    providers.update_provider("ollama", {"enabled": False})
    with pytest.raises(RuntimeError, match="disabled"):
        await AIRouter().generate("Hello", fallback_to_local=False)


@pytest.mark.asyncio
async def test_cloud_budget_fallback_drops_cloud_model(configured, monkeypatch):
    async def local(prompt, system, model, temperature, max_tokens):
        assert model is None
        return AIResponse(content="local", provider="ollama", model="stored-local-model")

    router = AIRouter()
    monkeypatch.setattr(router, "_call_ollama", local)
    response = await router.generate("Hello", provider="gemini", model="cloud-only-model")
    assert response.provider == "ollama"


def test_router_status_never_contains_saved_secret(configured):
    providers.update_provider("gemini", {"api_key": "synthetic-hidden-value"})
    assert "synthetic-hidden-value" not in json.dumps(AIRouter().get_provider_status())
