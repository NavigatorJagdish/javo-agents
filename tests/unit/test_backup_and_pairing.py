"""Unit tests for encrypted backup/restore verification and device pairing security."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from app.services.backup_service import BackupService
from app.services.device_pairing import DevicePairingService


def test_encrypted_backup_verify_and_restore_roundtrip(tmp_path: Path):
    src_file = tmp_path / "javo_agents.db"
    src_file.write_bytes(b"SQLite format 3\x00test-data-payload")

    backup_dir = tmp_path / "backups"
    restore_dir = tmp_path / "restored"

    svc = BackupService(backup_dir=str(backup_dir), encryption_key="unit-test-backup-secret")
    created = svc.create_backup(include_paths=[src_file], label="ci")

    assert created["backup_file"].endswith(".jbackup")
    assert Path(created["path"]).exists()
    assert len(created["checksum"]) == 64

    # Verify authentic backup
    check = svc.verify_backup(created["backup_file"])
    assert check["valid"] is True
    assert "javo_agents.db" in check["members"]

    # Restore and verify exact bytes match
    restored = svc.restore_backup(created["backup_file"], restore_dir=restore_dir)
    assert restored["restored"] is True
    assert (restore_dir / "javo_agents.db").read_bytes() == b"SQLite format 3\x00test-data-payload"

    # Tampering with encrypted archive fails verification
    Path(created["path"]).write_bytes(b"corrupted-cipher-bytes")
    bad_check = svc.verify_backup(created["backup_file"])
    assert bad_check["valid"] is False


def test_device_pairing_challenge_confirm_sync_and_revoke():
    svc = DevicePairingService(ttl_minutes=5)
    challenge = svc.initiate_pairing(device_name="Pixel 9", device_type="mobile", platform="android")
    code = challenge["pairing_code"]
    assert len(code) == 6

    confirmed = svc.confirm_pairing(code=code, user_id="owner-1")
    device_id = confirmed["device"]["id"]
    assert confirmed["device"]["is_trusted"] is True
    assert confirmed["access_token"]

    # Reusing the same pairing code must fail
    with pytest.raises(ValueError):
        svc.confirm_pairing(code=code, user_id="owner-1")

    sync_res = svc.sync_device(device_id, payload={"drafts": 1})
    assert sync_res["sync_cursor"] == 1
    assert sync_res["ack"] is True

    assert svc.revoke_device(device_id) is True
    assert svc.list_devices() == []
    with pytest.raises(KeyError):
        svc.sync_device(device_id)
