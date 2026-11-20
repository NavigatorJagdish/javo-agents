"""Per-account authenticated credential storage with account-bound keys.

Reuses the existing tested atomic encrypted-document/Windows DPAPI primitive.
Only protected internal connector code can read token values; owner APIs expose
availability flags, never the credentials. No platform request happens here.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, SecretStr

from app.config import get_settings
from app.core.provider_store import ProviderVault, VaultUnavailable


class CredentialRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    access_token: SecretStr | None = Field(default=None, max_length=16384)
    refresh_token: SecretStr | None = Field(default=None, max_length=16384)
    expires_at: AwareDatetime | None = None
    source: Literal["legacy_unverified"] = "legacy_unverified"
    legacy_metadata_secrets: dict[str, Any] = Field(default_factory=dict, repr=False)


def _plain(record: CredentialRecord) -> dict:
    return {
        "access_token": record.access_token.get_secret_value() if record.access_token else None,
        "refresh_token": record.refresh_token.get_secret_value() if record.refresh_token else None,
        "expires_at": record.expires_at.isoformat() if record.expires_at else None,
        "source": record.source,
        "legacy_metadata_secrets": record.legacy_metadata_secrets,
    }


def split_legacy_metadata(metadata):
    """Move recognized credential keys into an encrypted JSON-pointer archive.

    Unknown noncredential metadata stays in the source. Free-form text is not
    claimed to be comprehensively classified or forensically erased.
    """
    sensitive = {
        "accesstoken",
        "refreshtoken",
        "clientsecret",
        "apikey",
        "authorization",
        "password",
        "secret",
        "token",
        "tokens",
        "credentials",
        "oauthtoken",
        "idtoken",
        "oauthcode",
        "authorizationcode",
    }
    found = {}

    def visit(value, pointer, depth):
        if depth > 20:
            raise VaultUnavailable("Legacy metadata needs owner recovery")
        if isinstance(value, dict):
            result = {}
            for key, item in value.items():
                path = pointer + "/" + key.replace("~", "~0").replace("/", "~1")
                if key.lower().replace("_", "").replace("-", "") in sensitive:
                    found[path] = item
                else:
                    result[key] = visit(item, path, depth + 1)
            return result
        if isinstance(value, list):
            return [visit(item, pointer + "/" + str(i), depth + 1) for i, item in enumerate(value)]
        return value

    if metadata is not None and not isinstance(metadata, dict):
        raise VaultUnavailable("Legacy metadata needs owner recovery")
    cleaned = visit(metadata, "", 0)
    try:
        if len(json.dumps(found, allow_nan=False)) > 32768:
            raise ValueError("Oversized legacy secrets")
    except (ValueError, TypeError):
        raise VaultUnavailable("Legacy metadata needs owner recovery") from None
    return cleaned, found


class AccountCredentialStore:
    def __init__(self, root: str | Path, secret: str | None):
        self.root = Path(root)
        self.secret = secret

    def vault(self, account_id: str) -> ProviderVault:
        if not isinstance(account_id, str) or not 1 <= len(account_id) <= 128:
            raise VaultUnavailable("Invalid credential account identity")
        digest = hashlib.sha256(account_id.encode()).digest()
        return ProviderVault(
            self.root / (digest.hex() + ".enc"),
            self.secret,
            key_domain=b"javo-social-v1\0" + digest,
        )

    @staticmethod
    def _decode(document, account_id):
        settings = document["settings"]
        if not settings and not document["providers"]:
            return None
        if (
            document["providers"]
            or settings.get("account_id") != account_id
            or type(settings.get("social_version")) is not int
            or settings.get("social_version") != 1
            or set(settings) != {"account_id", "social_version", "credentials"}
        ):
            raise VaultUnavailable("Account credential binding is invalid")
        try:
            return (
                CredentialRecord.model_validate(settings["credentials"])
                if settings["credentials"] is not None
                else None
            )
        except Exception:
            raise VaultUnavailable("Account credential data is invalid") from None

    def read(self, account_id: str) -> CredentialRecord | None:
        return self._decode(self.vault(account_id).read(), account_id)

    def stage_legacy(
        self,
        account_id: str,
        access_token: str | None,
        refresh_token: str | None,
        expires_at: datetime | None,
        legacy_metadata_secrets: dict | None = None,
    ):
        if not access_token and not refresh_token and not legacy_metadata_secrets:
            raise VaultUnavailable("No legacy credential value is present")
        if expires_at:
            expires_at = (
                expires_at.replace(tzinfo=timezone.utc)
                if expires_at.tzinfo is None
                else expires_at.astimezone(timezone.utc)
            )
        try:
            record = CredentialRecord(
                access_token=access_token or None,
                refresh_token=refresh_token or None,
                expires_at=expires_at,
                legacy_metadata_secrets=legacy_metadata_secrets or {},
            )
            raw = _plain(record)
        except Exception:
            raise VaultUnavailable("Legacy credentials cannot be safely converted") from None

        expected = [None]

        def mutate(document):
            current = self._decode(document, account_id)
            merged = dict(raw)
            if current is not None:
                saved = _plain(current)
                for key in ("access_token", "refresh_token", "expires_at"):
                    if saved[key] is not None and raw[key] is not None and saved[key] != raw[key]:
                        raise VaultUnavailable(
                            "Saved credentials differ from the legacy copy; owner recovery is required"
                        )
                    merged[key] = raw[key] if raw[key] is not None else saved[key]
                archived = dict(saved["legacy_metadata_secrets"])
                for key, value in raw["legacy_metadata_secrets"].items():
                    if key in archived and archived[key] != value:
                        raise VaultUnavailable(
                            "Legacy secret copies conflict; owner recovery is required"
                        )
                    archived[key] = value
                merged["legacy_metadata_secrets"] = archived
            expected[0] = merged
            document["settings"] = {
                "account_id": account_id,
                "social_version": 1,
                "credentials": merged,
            }

        self.vault(account_id).update(mutate)
        reopened = self.read(account_id)
        if reopened is None or _plain(reopened) != expected[0]:
            raise VaultUnavailable("Encrypted credential readback could not be verified")

    def clear(self, account_id: str):
        vault = self.vault(account_id)
        if not vault.path.exists():
            return

        def mutate(document):
            self._decode(document, account_id)  # Never silently reset a locked/damaged store.
            document["settings"] = {
                "account_id": account_id,
                "social_version": 1,
                "credentials": None,
            }

        vault.update(mutate)

    def metadata(self, account_id: str, *, legacy_present=False):
        vault = self.vault(account_id)
        try:
            record = self.read(account_id)
            return {
                "credential_state": "legacy_unprotected"
                if legacy_present
                else "saved_unverified"
                if record
                else "none",
                "has_saved_credentials": record is not None,
                "credentials_protection": vault.protection,
                "has_refresh_token": bool(record and record.refresh_token),
                "credential_expires_at": record.expires_at if record else None,
            }
        except VaultUnavailable:
            return {
                "credential_state": "unavailable",
                "has_saved_credentials": None,
                "credentials_protection": "locked",
                "has_refresh_token": None,
                "credential_expires_at": None,
            }


def credential_store() -> AccountCredentialStore:
    settings = get_settings()
    root = (
        settings.account_credentials_dir
        or Path(settings.provider_config_path).parent / "account-credentials"
    )
    return AccountCredentialStore(root, settings.encryption_key)
