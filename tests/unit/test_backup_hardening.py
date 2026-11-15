"""Backup integrity and filesystem boundaries using temporary real SQLite data."""

import io
from pathlib import Path
import sqlite3
import tarfile
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from app.services.backup_service import BackupService
from app.api.routes import settings as routes
from app.agents.recovery_agent import RecoveryAgent


def finish(coro):
    try:
        coro.send(None)
    except StopIteration as result:
        return result.value
    finally:
        coro.close()
    raise AssertionError("Unexpected IO")


def test_persistent_key_required_no_ephemeral_fallback(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "app.services.backup_service.get_settings",
        lambda: SimpleNamespace(
            backup_dir=str(tmp_path), encryption_key=None, secret_key="random-on-each-restart"
        ),
    )
    with pytest.raises(ValueError, match="persistent"):
        BackupService()


def test_online_snapshot_includes_wal_and_new_service_can_restore(tmp_path):
    source = tmp_path / "runtime.db"
    with sqlite3.connect(source) as writer:
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("PRAGMA wal_autocheckpoint=0")
        writer.execute("CREATE TABLE original (value TEXT)")
        writer.execute("INSERT INTO original VALUES ('committed WAL value')")
        writer.commit()
        assert Path(str(source) + "-wal").is_file()
        backup = BackupService(
            str(tmp_path / "backups"), encryption_key="synthetic persistent test key"
        )
        created = backup.create_sqlite_backup(source)
    assert b"committed WAL value" not in Path(created["path"]).read_bytes()
    reloaded = BackupService(
        str(tmp_path / "backups"), encryption_key="synthetic persistent test key"
    )
    reloaded.restore_backup(created["backup_file"], tmp_path / "staging")
    with sqlite3.connect(tmp_path / "staging" / "runtime.db") as restored:
        assert restored.execute("SELECT value FROM original").fetchone()[0] == "committed WAL value"
        assert restored.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    wrong = BackupService(str(tmp_path / "backups"), encryption_key="another key")
    assert wrong.verify_backup(created["backup_file"])["valid"] is False


@pytest.mark.parametrize(
    "name", ["../escape", "../sibling/data", "/absolute", "C:/drive", "a\\windows", "linked"]
)
def test_malicious_restore_members_rejected_before_files_written(tmp_path, name):
    service = BackupService(str(tmp_path / "backups"), encryption_key="test key")
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w:gz") as tar:
        good = tarfile.TarInfo("good.txt")
        good.size = 4
        tar.addfile(good, io.BytesIO(b"good"))
        member = tarfile.TarInfo(name)
        if name == "linked":
            member.type, member.linkname = tarfile.SYMTYPE, "../outside"
        tar.addfile(member)
    archive = tmp_path / "backups" / "malicious.jbackup"
    archive.write_bytes(service._fernet.encrypt(stream.getvalue()))
    with pytest.raises(ValueError, match="Unsafe"):
        service.restore_backup(archive.name, tmp_path / "staging")
    assert not (tmp_path / "staging" / "good.txt").exists()


def test_restore_refuses_existing_data_and_rejects_unsafe_names(tmp_path):
    service = BackupService(str(tmp_path / "backups"), encryption_key="test key")
    source = tmp_path / "source.txt"
    source.write_text("original")
    created = service.create_backup([source])
    staging = tmp_path / "staging"
    staging.mkdir()
    owner_file = staging / "owner.txt"
    owner_file.write_text("preserved")
    with pytest.raises(ValueError, match="empty staging"):
        service.restore_backup(created["backup_file"], staging)
    assert owner_file.read_text() == "preserved"
    assert service.verify_backup("../outside.jbackup")["valid"] is False
    with pytest.raises(ValueError, match="label"):
        service.create_backup([source], label="../escape")


def test_api_requires_key_and_never_creates_empty_success_backup(tmp_path, monkeypatch):
    config = SimpleNamespace(encryption_key=None, backup_dir=str(tmp_path))
    monkeypatch.setattr(routes, "get_settings", lambda: config)
    with pytest.raises(HTTPException) as error:
        routes.create_backup(None)
    assert error.value.status_code == 503
    config.encryption_key = "synthetic-test-key-" * 3
    monkeypatch.setattr(routes, "_resolve_sqlite_path", lambda: tmp_path / "missing.db")
    with pytest.raises(HTTPException) as error:
        routes.create_backup(None)
    assert error.value.status_code == 409
    assert list(tmp_path.iterdir()) == []


def test_live_restore_and_agent_cannot_report_false_success(tmp_path):
    with pytest.raises(HTTPException) as error:
        finish(routes.restore_backup(routes.RestoreRequest(filename="any.db")))
    assert error.value.status_code == 409
    result = finish(RecoveryAgent().execute({"action": "restore_backup", "backup_id": "any"}))
    assert result["status"] == "blocked" and result["verified_checksum"] is False
