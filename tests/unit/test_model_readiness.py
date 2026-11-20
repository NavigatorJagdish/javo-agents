"""Explicit inventory checks, not synthetic claims of generation or benchmarks."""

import json
import asyncio

import httpx
import pytest

from app.services import model_readiness as readiness


@pytest.fixture
def inventory(monkeypatch):
    config = {
        "enabled": True,
        "model": "synthetic-model",
        "base_url": "http://127.0.0.1:11434",
        "api_key": "synthetic-must-not-send",
    }
    monkeypatch.setattr(
        readiness.provider_settings, "effective", lambda: {"providers": {"ollama": config}}
    )
    calls = []

    def install(response):
        def handle(request):
            calls.append(request)
            assert request.method == "GET" and request.url.path == "/api/tags"
            assert "authorization" not in request.headers
            return response

        monkeypatch.setattr(
            readiness,
            "_client",
            lambda: httpx.AsyncClient(
                transport=httpx.MockTransport(handle), follow_redirects=False, trust_env=False
            ),
        )

    return config, calls, install


@pytest.mark.asyncio
async def test_available_alias_and_missing_model_remain_generation_unverified(inventory):
    config, calls, install = inventory
    install(httpx.Response(200, json={"models": [{"name": "synthetic-model:latest"}]}))
    result = await readiness.check_local_model()
    assert result["status"] == "available" and not result["generation_verified"]
    assert result["available_models"] == ["synthetic-model:latest"] and len(calls) == 1
    config["model"] = "missing-model"
    result = await readiness.check_local_model()
    assert result["status"] == "model_missing" and not result["generation_verified"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "patch,status",
    [
        ({"enabled": False}, "disabled"),
        ({"base_url": "https://remote.invalid"}, "invalid_configuration"),
        ({"base_url": "http://127.0.0.1/?key=synthetic-secret"}, "invalid_configuration"),
        ({"enabled": "yes"}, "invalid_configuration"),
    ],
)
async def test_disabled_invalid_or_remote_configuration_never_connects(inventory, patch, status):
    config, calls, _ = inventory
    config.update(patch)
    result = await readiness.check_local_model()
    assert result["status"] == status and not calls
    assert "synthetic-secret" not in json.dumps(result)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(302, headers={"location": "https://remote.invalid/secret"}),
        httpx.Response(503, text="synthetic-server-secret"),
        httpx.Response(200, content=b"x" * 1048577),
        httpx.Response(200, headers={"content-encoding": "br"}, content=b"unsupported-encoding"),
        httpx.Response(200, json={"models": "not-a-list"}),
        httpx.Response(200, json={"models": [{"name": "<unsafe-markup>"}]}),
    ],
)
async def test_redirect_errors_oversize_and_invalid_inventory_are_unavailable(inventory, response):
    _, calls, install = inventory
    install(response)
    result = await readiness.check_local_model()
    assert result["status"] == "unavailable" and len(calls) == 1
    assert result["available_models"] == []
    assert "synthetic-server-secret" not in json.dumps(result)


@pytest.mark.asyncio
async def test_transport_errors_and_configured_storage_failure_are_sanitized(
    inventory, monkeypatch
):
    def fail(request):
        raise httpx.ConnectError("synthetic-private-error")

    monkeypatch.setattr(
        readiness, "_client", lambda: httpx.AsyncClient(transport=httpx.MockTransport(fail))
    )
    result = await readiness.check_local_model()
    assert result["status"] == "unavailable" and "synthetic-private-error" not in json.dumps(result)

    def locked():
        raise RuntimeError("synthetic-private-configuration")

    monkeypatch.setattr(readiness.provider_settings, "effective", locked)
    result = await readiness.check_local_model()
    assert result[
        "status"
    ] == "invalid_configuration" and "synthetic-private-configuration" not in json.dumps(result)


@pytest.mark.asyncio
async def test_total_timeout_and_cancellation_do_not_become_success(inventory, monkeypatch):
    async def slow(request):
        await asyncio.sleep(30)
        return httpx.Response(200, json={"models": []})

    monkeypatch.setattr(
        readiness, "_client", lambda: httpx.AsyncClient(transport=httpx.MockTransport(slow))
    )
    start = asyncio.get_running_loop().time()
    result = await readiness.check_local_model()
    assert result["status"] == "unavailable"
    assert asyncio.get_running_loop().time() - start < 5
    task = asyncio.create_task(readiness.check_local_model())
    await asyncio.sleep(0.01)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


def test_inventory_endpoint_requires_owner_and_has_no_generation_claim(owner_runtime, monkeypatch):
    async def inventory():
        return {"status": "model_missing", "generation_verified": False}

    monkeypatch.setattr(readiness, "check_local_model", inventory)
    factory, _ = owner_runtime
    with factory() as client:
        response = client.post("/api/settings/ai-providers/ollama/check")
        assert response.status_code == 200 and response.json()["generation_verified"] is False
        assert (
            client.post(
                "/api/settings/ai-providers/ollama/check", headers={"Authorization": ""}
            ).status_code
            == 401
        )
