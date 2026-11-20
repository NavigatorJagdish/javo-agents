"""Actual API/SQLite/encryption restart and failure checks; no real platform calls."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3

import pytest


def create(client, **changes):
    response = client.post(
        "/api/accounts/", json={"platform": "youtube", "username": "@saved-owner", **changes}
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_account_brand_reload_scope_and_no_fake_connection(owner_runtime):
    factory, path = owner_runtime
    with factory() as client:
        assert client.get("/api/accounts/").json() == []
        account = create(client)
        prefix = "/api/accounts/" + account["id"]
        assert account["status"] == "disconnected" and account["connection_verified"] is False
        assert account["credential_state"] == "none"
        assert client.post(prefix + "/oauth/initiate", json={}).status_code == 501
        assert client.put(prefix, json={"status": "connected"}).status_code == 422
        assert client.get(prefix + "/brand-profile").status_code == 404
        brand = client.put(
            prefix + "/brand-profile",
            json={
                "brand_name": "Saved brand",
                "brand_voice": "Clear Hinglish",
                "content_pillars": ["Local tools", "Creator education"],
            },
        )
        assert brand.status_code == 200
        assert client.put(prefix, json={"display_name": "Owner channel"}).status_code == 200
        assert (
            client.post(
                "/api/accounts/",
                json={"platform": "youtube", "username": "Other", "user_id": "foreign-owner"},
            ).status_code
            == 403
        )
    with factory() as client:
        assert client.get(prefix).json()["display_name"] == "Owner channel"
        assert client.get(prefix + "/brand-profile").json()["content_pillars"] == [
            "Local tools",
            "Creator education",
        ]
        with sqlite3.connect(path) as db:
            db.execute(
                "UPDATE social_accounts SET user_id=? WHERE id=?", ("foreign-owner", account["id"])
            )
        assert client.get("/api/accounts/").json() == []
        for url in (prefix, prefix + "/brand-profile"):
            assert client.get(url).status_code == 404
        assert client.post(prefix + "/credentials/migrate").status_code == 404
        assert client.delete(prefix + "/credentials").status_code == 404
        assert client.get("/api/accounts/", headers={"Authorization": ""}).status_code == 401


def test_legacy_credentials_are_verified_encrypted_then_cleared_after_restart(owner_runtime):
    factory, path = owner_runtime
    access, refresh = (
        "synthetic-access-private-migration-value",
        "synthetic-refresh-private-migration-value",
    )
    with factory() as client:
        account = create(client)
        prefix = "/api/accounts/" + account["id"]
    with sqlite3.connect(path) as db:
        db.execute(
            "UPDATE social_accounts SET access_token=?,refresh_token=?,status=?,metadata=? WHERE id=?",
            (
                access,
                refresh,
                "CONNECTED",
                json.dumps(
                    {
                        "access_token": access,
                        "channel_id": "public-id",
                        "invented_followers": 1000000,
                    }
                ),
                account["id"],
            ),
        )
    with factory() as client:
        response = client.get(prefix)
        saved = response.json()
        assert saved["credential_state"] == "saved_unverified"
        assert saved["status"] == "disconnected" and not saved["connection_verified"]
        assert saved["has_saved_credentials"] and saved["has_refresh_token"]
        assert access not in response.text and refresh not in response.text
        assert saved["metadata"] == {"channel_id": "public-id"}
        with sqlite3.connect(path) as db:
            assert db.execute(
                "SELECT access_token,refresh_token FROM social_accounts WHERE id=?",
                (account["id"],),
            ).fetchone() == (None, None)
        # Known token columns and recognized credential metadata are protected;
        # unrelated old metadata is preserved, not invented as live analytics.
        with sqlite3.connect(path) as db:
            metadata = json.loads(
                db.execute(
                    "SELECT metadata FROM social_accounts WHERE id=?", (account["id"],)
                ).fetchone()[0]
            )
            assert "access_token" not in metadata and metadata["invented_followers"] == 1000000
        assert access.encode() not in Path(path).read_bytes()
        vaults = list((path.parent / "account-credentials").glob("*.enc"))
        assert len(vaults) == 1 and access.encode() not in vaults[0].read_bytes()
        result = client.delete(prefix + "/credentials")
        assert result.status_code == 200 and result.json()["has_saved_credentials"] is False


def test_failed_migration_keeps_legacy_source_and_never_logs_values(
    owner_runtime, monkeypatch, caplog
):
    from app.core.account_credentials import AccountCredentialStore
    from app.core.provider_store import VaultUnavailable

    factory, path = owner_runtime
    value = "synthetic-migration-failure-private-value"
    with factory() as client:
        account = create(client)
    with sqlite3.connect(path) as db:
        db.execute("UPDATE social_accounts SET access_token=? WHERE id=?", (value, account["id"]))

    def fail(*args):
        raise VaultUnavailable("Fixture unavailable")

    monkeypatch.setattr(AccountCredentialStore, "stage_legacy", fail)
    with factory() as client:
        prefix = "/api/accounts/" + account["id"]
        assert client.get(prefix).json()["credential_state"] == "legacy_unprotected"
        assert client.post(prefix + "/credentials/migrate").status_code == 503
        with sqlite3.connect(path) as db:
            assert (
                db.execute(
                    "SELECT access_token FROM social_accounts WHERE id=?", (account["id"],)
                ).fetchone()[0]
                == value
            )
        assert value not in caplog.text


def test_conflicting_encrypted_copy_cannot_be_overwritten_by_legacy_migration(owner_runtime):
    from app.core.account_credentials import credential_store

    factory, path = owner_runtime
    with factory() as client:
        account = create(client)
        credential_store().stage_legacy(account["id"], "synthetic-encrypted-existing", None, None)
    with sqlite3.connect(path) as db:
        db.execute(
            "UPDATE social_accounts SET access_token=? WHERE id=?",
            ("synthetic-different-legacy", account["id"]),
        )
    with factory() as client:
        assert (
            client.post("/api/accounts/" + account["id"] + "/credentials/migrate").status_code
            == 503
        )
        assert (
            credential_store().read(account["id"]).access_token.get_secret_value()
            == "synthetic-encrypted-existing"
        )
        with sqlite3.connect(path) as db:
            assert (
                db.execute(
                    "SELECT access_token FROM social_accounts WHERE id=?", (account["id"],)
                ).fetchone()[0]
                == "synthetic-different-legacy"
            )


def test_metadata_only_migration_and_removal_preserve_unrelated_values(owner_runtime):
    from app.core.account_credentials import credential_store

    factory, path = owner_runtime
    value = "synthetic-metadata-only-secret"
    with factory() as client:
        account = create(client)
        prefix = "/api/accounts/" + account["id"]
        with sqlite3.connect(path) as db:
            db.execute(
                "UPDATE social_accounts SET metadata=? WHERE id=?",
                (
                    json.dumps({"nested": [{"api_key": value}], "owner_note": "Keep this"}),
                    account["id"],
                ),
            )
        # An edit cannot overwrite unprotected values before protection.
        assert (
            client.put(prefix, json={"metadata": {"channel_id": "replacement"}}).status_code == 409
        )
        result = client.post(prefix + "/credentials/migrate")
        assert result.status_code == 200 and result.json()["has_saved_credentials"] is True
        assert value not in result.text
        assert credential_store().read(account["id"]).legacy_metadata_secrets == {
            "/nested/0/api_key": value
        }
        assert client.delete(prefix + "/credentials").json()["credential_state"] == "none"
        with sqlite3.connect(path) as db:
            assert json.loads(
                db.execute(
                    "SELECT metadata FROM social_accounts WHERE id=?", (account["id"],)
                ).fetchone()[0]
            ) == {"nested": [{}], "owner_note": "Keep this"}


def test_account_removal_preserves_linked_execution_history(owner_runtime):
    factory, path = owner_runtime
    with factory() as client:
        account = create(client)
        prefix = "/api/accounts/" + account["id"]
        task = client.post(
            "/api/tasks/", json={"title": "Retained work", "account_id": account["id"]}
        )
        assert task.status_code == 201, task.text
        assert client.delete(prefix).status_code == 409
        assert client.get(prefix).status_code == 200
        assert client.delete(prefix + "/credentials").status_code == 200


def test_old_owner_content_can_use_new_account_but_foreign_owner_cannot(owner_runtime):
    factory, path = owner_runtime
    incoming = path.parent / "legacy-content"
    incoming.mkdir()
    (incoming / "caption.txt").write_text("Synthetic owner-alias content", encoding="utf-8")
    with factory() as client:
        asset = client.post("/api/content/scan-folder", json={"folder_path": str(incoming)}).json()[
            "imported_assets"
        ][0]
        account = create(client)
        with sqlite3.connect(path) as db:
            db.execute(
                "UPDATE content_assets SET user_id=? WHERE id=?", ("default-user", asset["id"])
            )
        request = {
            "asset_id": asset["id"],
            "account_id": account["id"],
            "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        }
        schedule = client.post("/api/content/schedule", json=request)
        assert schedule.status_code == 201
        assert (
            client.get("/api/content/schedule/" + schedule.json()["id"] + "/preview").status_code
            == 200
        )
        with sqlite3.connect(path) as db:
            db.execute(
                "UPDATE content_assets SET user_id=? WHERE id=?", ("foreign-owner", asset["id"])
            )
        assert client.post("/api/content/schedule", json=request).status_code == 403
        assert (
            client.get("/api/content/schedule/" + schedule.json()["id"] + "/preview").status_code
            == 403
        )


def test_secure_delete_clears_known_sql_token_bytes_without_claiming_forensic_erasure(
    owner_runtime,
):
    factory, path = owner_runtime
    value = "synthetic-unique-column-value-623ab70c"
    with factory() as client:
        account = create(client)
        with sqlite3.connect(path) as db:
            db.execute(
                "UPDATE social_accounts SET access_token=? WHERE id=?", (value, account["id"])
            )
        assert value.encode() in Path(path).read_bytes()
        assert (
            client.post("/api/accounts/" + account["id"] + "/credentials/migrate").status_code
            == 200
        )
        assert value.encode() not in Path(path).read_bytes()


@pytest.mark.parametrize(
    "changes",
    [
        {"username": "  "},
        {"access_token": "synthetic-must-not-be-echoed"},
        {"metadata": {"refresh_token": "synthetic-must-not-be-echoed"}},
    ],
)
def test_invalid_and_secret_record_fields_are_rejected_without_echo(owner_runtime, changes):
    factory, _ = owner_runtime
    with factory() as client:
        response = client.post(
            "/api/accounts/", json={"platform": "youtube", "username": "@saved", **changes}
        )
        assert response.status_code == 422
        assert "synthetic-must-not-be-echoed" not in response.text
        assert client.get("/api/accounts/").json() == []
