"""Real encrypted per-account documents; synthetic values only, no OAuth calls."""

from datetime import datetime, timezone
from pathlib import Path
import sys

import pytest

from app.core.account_credentials import AccountCredentialStore, split_legacy_metadata
from app.core.provider_store import ProviderVault, VaultUnavailable

SECRET = "synthetic-account-credential-encryption-master-" * 2


def test_account_binding_and_key_domain_isolation(tmp_path):
    store = AccountCredentialStore(tmp_path, SECRET)
    value = "synthetic-account-a-private-value"
    store.stage_legacy(
        "account-a", value, "synthetic-refresh", datetime(2026, 12, 31, tzinfo=timezone.utc)
    )
    assert value.encode() not in store.vault("account-a").path.read_bytes()
    assert store.read("account-a").access_token.get_secret_value() == value
    assert store.read("account-b") is None
    assert store.vault("account-a")._key() != store.vault("account-b")._key()
    assert (
        store.vault("account-a")._key() != ProviderVault(tmp_path / "provider.enc", SECRET)._key()
    )
    target = store.vault("account-b").path
    target.write_bytes(store.vault("account-a").path.read_bytes())
    with pytest.raises(VaultUnavailable):
        store.read("account-b")
    meta = store.metadata("account-b")
    assert meta["credential_state"] == "unavailable" and meta["has_saved_credentials"] is None


def test_idempotent_stage_conflict_and_removal(tmp_path):
    store = AccountCredentialStore(tmp_path, SECRET)
    store.stage_legacy("account-a", "synthetic-original", None, None)
    before = store.vault("account-a").path.read_bytes()
    store.stage_legacy("account-a", "synthetic-original", None, None)
    with pytest.raises(VaultUnavailable):
        store.stage_legacy("account-a", "synthetic-different", None, None)
    assert store.read("account-a").access_token.get_secret_value() == "synthetic-original"
    assert before  # A verified ciphertext existed before any logical removal.
    store.clear("account-a")
    assert store.read("account-a") is None
    assert store.metadata("account-a")["has_saved_credentials"] is False


def test_failed_atomic_save_preserves_existing_document(tmp_path, monkeypatch):
    import os

    store = AccountCredentialStore(tmp_path, SECRET)
    store.stage_legacy("account-a", "synthetic-original", None, None)
    before = store.vault("account-a").path.read_bytes()
    monkeypatch.setattr(
        os, "replace", lambda *args: (_ for _ in ()).throw(OSError("Fixture disk error"))
    )
    with pytest.raises(VaultUnavailable):
        store.clear("account-a")
    assert store.vault("account-a").path.read_bytes() == before
    assert list(tmp_path.glob("*.tmp")) == []


def test_nested_metadata_only_secrets_merge_without_losing_existing_credentials(tmp_path):
    store = AccountCredentialStore(tmp_path, SECRET)
    store.stage_legacy("account-a", "synthetic-original", None, None)
    public, archived = split_legacy_metadata(
        {
            "channel_id": "public-id",
            "old/oauth": [{"client-secret": "synthetic-nested"}, {"note": "preserve"}],
            "credentials": {"refresh_token": "synthetic-archived"},
        }
    )
    assert public == {"channel_id": "public-id", "old/oauth": [{}, {"note": "preserve"}]}
    assert archived == {
        "/old~1oauth/0/client-secret": "synthetic-nested",
        "/credentials": {"refresh_token": "synthetic-archived"},
    }
    store.stage_legacy("account-a", None, None, None, archived)
    saved = store.read("account-a")
    assert saved.access_token.get_secret_value() == "synthetic-original"
    assert saved.legacy_metadata_secrets == archived
    store.stage_legacy("account-a", None, None, None, archived)
    with pytest.raises(VaultUnavailable):
        store.stage_legacy("account-a", None, None, None, {"/credentials": "synthetic-conflict"})
    assert store.read("account-a").legacy_metadata_secrets == archived


@pytest.mark.skipif(sys.platform != "win32", reason="Actual Windows current-user DPAPI")
def test_dpapi_reopen_and_cipher_plus_key_swap_still_rejects_wrong_account(tmp_path):
    store = AccountCredentialStore(tmp_path, None)
    store.stage_legacy("account-a", "synthetic-dpapi-value", None, None)
    assert (
        AccountCredentialStore(tmp_path, None).read("account-a").access_token.get_secret_value()
        == "synthetic-dpapi-value"
    )
    first, second = store.vault("account-a"), store.vault("account-b")
    second.path.write_bytes(first.path.read_bytes())
    second.key_path.write_bytes(first.key_path.read_bytes())
    with pytest.raises(VaultUnavailable, match="binding"):
        store.read("account-b")
    first.key_path.unlink()
    with pytest.raises(VaultUnavailable):
        store.read("account-a")
    assert not first.key_path.exists()


@pytest.mark.skipif(sys.platform == "win32", reason="Windows has OS-backed user protection")
def test_non_windows_never_falls_back_to_plaintext(tmp_path):
    with pytest.raises(VaultUnavailable):
        AccountCredentialStore(tmp_path, None).stage_legacy(
            "account-a", "synthetic-value", None, None
        )
    assert list(Path(tmp_path).glob("*.enc")) == []
