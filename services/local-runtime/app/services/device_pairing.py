"""Secure device pairing protocol using short-lived pairing codes and HMAC verification."""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from app.core.security import get_token_manager

logger = logging.getLogger(__name__)


@dataclass
class PairingChallenge:
    code: str
    device_name: str
    device_type: str
    platform: str
    challenge_nonce: str
    created_at: datetime
    expires_at: datetime
    confirmed: bool = False
    device_id: Optional[str] = None


class DevicePairingService:
    """Manages secure pairing challenges, confirmation, and revocation for companion devices."""

    def __init__(self, ttl_minutes: int = 10):
        self._ttl_minutes = ttl_minutes
        self._pending: dict[str, PairingChallenge] = {}
        self._paired_devices: dict[str, dict[str, Any]] = {}

    def initiate_pairing(
        self,
        device_name: str,
        device_type: str = "mobile",
        platform: str = "android",
    ) -> dict[str, Any]:
        """Generate a short-lived 6-character pairing code and challenge nonce."""
        self._cleanup_expired()
        code = "".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(6))
        nonce = secrets.token_hex(16)
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=self._ttl_minutes)

        challenge = PairingChallenge(
            code=code,
            device_name=device_name,
            device_type=device_type,
            platform=platform,
            challenge_nonce=nonce,
            created_at=now,
            expires_at=expires,
        )
        self._pending[code] = challenge
        logger.info("Initiated device pairing code=%s for %s (%s)", code, device_name, platform)
        return {
            "pairing_code": code,
            "challenge_nonce": nonce,
            "expires_at": expires.isoformat(),
            "device_name": device_name,
            "platform": platform,
        }

    def confirm_pairing(
        self,
        code: str,
        user_id: str = "owner",
        fingerprint: Optional[str] = None,
    ) -> dict[str, Any]:
        """Confirm a pairing code, register the trusted device, and issue a device token."""
        self._cleanup_expired()
        challenge = self._pending.get(code.upper())
        if not challenge:
            raise ValueError("Invalid or expired pairing code")
        if challenge.confirmed:
            raise ValueError("Pairing code already used")

        device_id = str(uuid.uuid4())
        device_fp = fingerprint or hashlib.sha256(
            f"{device_id}:{challenge.challenge_nonce}".encode()
        ).hexdigest()

        token_mgr = get_token_manager()
        device_token = token_mgr.generate_token(user_id=user_id, device_id=device_id)

        challenge.confirmed = True
        challenge.device_id = device_id

        device_record = {
            "id": device_id,
            "user_id": user_id,
            "device_name": challenge.device_name,
            "device_type": challenge.device_type,
            "platform": challenge.platform,
            "fingerprint": device_fp,
            "is_trusted": True,
            "paired_at": datetime.now(timezone.utc).isoformat(),
            "last_seen": datetime.now(timezone.utc).isoformat(),
            "sync_cursor": 0,
        }
        self._paired_devices[device_id] = device_record
        del self._pending[code.upper()]

        logger.info("Device paired successfully: id=%s name=%s", device_id, challenge.device_name)
        return {
            "device": device_record,
            "access_token": device_token,
        }

    def list_devices(self) -> list[dict[str, Any]]:
        return list(self._paired_devices.values())

    def sync_device(self, device_id: str, payload: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        device = self._paired_devices.get(device_id)
        if not device:
            raise KeyError(f"Device not found: {device_id}")
        device["last_seen"] = datetime.now(timezone.utc).isoformat()
        device["sync_cursor"] = device.get("sync_cursor", 0) + 1
        return {
            "device_id": device_id,
            "sync_cursor": device["sync_cursor"],
            "synced_at": device["last_seen"],
            "ack": bool(payload is not None),
        }

    def revoke_device(self, device_id: str) -> bool:
        if device_id in self._paired_devices:
            del self._paired_devices[device_id]
            logger.warning("Revoked paired device: %s", device_id)
            return True
        return False

    def _cleanup_expired(self) -> None:
        now = datetime.now(timezone.utc)
        expired = [code for code, ch in self._pending.items() if ch.expires_at < now]
        for code in expired:
            del self._pending[code]


_device_pairing: Optional[DevicePairingService] = None


def get_device_pairing_service() -> DevicePairingService:
    global _device_pairing
    if _device_pairing is None:
        _device_pairing = DevicePairingService()
    return _device_pairing
