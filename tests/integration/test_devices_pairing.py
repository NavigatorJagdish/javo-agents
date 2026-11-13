"""Integration tests for device pairing endpoint contract."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import get_owner_token
from app.main import app


@pytest.mark.asyncio
async def test_pairing_flow_from_unauthenticated_device():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        owner_tok = get_owner_token()
        headers = {"Authorization": f"Bearer {owner_tok}"}

        # 1. Initiate pairing on Windows desktop (authenticated)
        init_res = await client.post(
            "/devices/pair",
            json={"device_name": "Pixel 9 Pro", "platform": "android"},
            headers=headers,
        )
        assert init_res.status_code == 201
        data = init_res.json()
        code = data["code"]
        assert len(code) == 6

        # 2. Confirm pairing from Android client WITHOUT Bearer auth
        confirm_res = await client.post(
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

        # 3. Use newly issued device token to sync drafts
        sync_res = await client.post(
            "/devices/android-test-device-uuid/sync",
            json=[],
            headers={"Authorization": f"Bearer {device_token}"},
        )
        assert sync_res.status_code == 200
        assert sync_res.json()["status"] == "synced"
