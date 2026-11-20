"""Encrypted backup, restore, and verification service."""

from __future__ import annotations

import base64
import hashlib
import io
import json
import logging
import re
import sqlite3
import time
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from cryptography.fernet import Fernet

from app.config import get_settings

logger = logging.getLogger(__name__)


class BackupService:
    """Creates, verifies, and restores encrypted archive backups of local Javo data."""

    def __init__(self, backup_dir: Optional[str] = None, encryption_key: Optional[str] = None):
        settings = get_settings()
        self.backup_dir = Path(backup_dir or settings.backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        raw_secret = encryption_key or settings.encryption_key
        if not raw_secret:
            raise ValueError("Configure a persistent backup encryption key before creating or restoring backups")
        derived = base64.urlsafe_b64encode(hashlib.sha256(raw_secret.encode()).digest())
        self._fernet = Fernet(derived)

    def _backup_path(self, name: str) -> Path:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+\.jbackup", name):
            raise ValueError("Invalid backup filename")
        target = self.backup_dir / name
        if target.is_symlink() or target.resolve().parent != self.backup_dir.resolve():
            raise ValueError("Unsafe backup path")
        return target

    def _write_archive(self, raw_bytes: bytes, label: str, included_files: list[str]) -> dict:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", label):
            raise ValueError("Invalid backup label")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        backup_name = f"javo_backup_{label}_{timestamp}.jbackup"
        dest_path = self._backup_path(backup_name)
        encrypted = self._fernet.encrypt(raw_bytes)
        # Exclusive creation prevents overwriting an earlier checkpoint.
        with dest_path.open("xb") as handle:
            handle.write(encrypted)
        checksum = hashlib.sha256(raw_bytes).hexdigest()
        dest_path.with_suffix(".jbackup.sha256").write_text(checksum, encoding="utf-8")
        return {"backup_file": backup_name, "path": str(dest_path), "size_bytes": len(encrypted),
                "checksum": checksum, "files": included_files,
                "created_at": datetime.now(timezone.utc).isoformat()}

    def create_sqlite_backup(self, database_path: str | Path) -> dict:
        """Online snapshot, including committed WAL content, without a plaintext temp file."""
        source = Path(database_path).resolve()
        if not source.is_file():
            raise FileNotFoundError("Database file is unavailable")
        with sqlite3.connect(source.as_uri() + "?mode=ro", uri=True, timeout=5) as conn:
            with sqlite3.connect(":memory:") as snapshot:
                deadline = time.monotonic() + 10
                def progress(status, remaining, total):
                    if time.monotonic() > deadline:
                        raise TimeoutError("SQLite snapshot exceeded its deadline")
                conn.backup(snapshot, pages=256, progress=progress, sleep=0.05)
                data = snapshot.serialize()
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tar:
            info = tarfile.TarInfo(source.name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
        return self._write_archive(buf.getvalue(), "sqlite", [source.name])

    def create_backup(
        self,
        include_paths: Optional[list[str | Path]] = None,
        label: str = "manual",
    ) -> dict[str, Any]:
        """Bundle database and selected directories into an encrypted .jbackup archive."""
        targets = [Path(p) for p in (include_paths or ["javo_agents.db", "scheduler_jobs.db"])]
        buf = io.BytesIO()
        included_files: list[str] = []

        with tarfile.open(fileobj=buf, mode="w:gz") as tar:
            for target in targets:
                if not target.exists() or target.is_symlink():
                    raise ValueError("Backup input is missing or linked")
                tar.add(target, arcname=target.name)
                included_files.append(target.name)

            manifest = {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "label": label,
                "files": included_files,
                "version": "1.0",
            }
            manifest_bytes = json.dumps(manifest).encode("utf-8")
            info = tarfile.TarInfo(name="manifest.json")
            info.size = len(manifest_bytes)
            tar.addfile(info, io.BytesIO(manifest_bytes))

        return self._write_archive(buf.getvalue(), label, included_files)

    def verify_backup(self, backup_name: str) -> dict[str, Any]:
        """Decrypt and verify integrity of a backup file against its SHA-256 checksum."""
        try:
            target = self._backup_path(backup_name)
            if not target.exists():
                return {"valid": False, "error": "Backup file not found"}
            encrypted = target.read_bytes()
            decrypted = self._fernet.decrypt(encrypted)
            actual_hash = hashlib.sha256(decrypted).hexdigest()

            meta_path = target.with_suffix(".jbackup.sha256")
            expected_hash = meta_path.read_text(encoding="utf-8").strip() if meta_path.exists() else None
            if expected_hash and expected_hash != actual_hash:
                return {"valid": False, "error": "Checksum mismatch"}

            with tarfile.open(fileobj=io.BytesIO(decrypted), mode="r:gz") as tar:
                members = tar.getnames()
            return {"valid": True, "checksum": actual_hash, "members": members}
        except Exception as exc:
            return {"valid": False, "error": str(exc)}

    def restore_backup(self, backup_name: str, restore_dir: str | Path = ".") -> dict[str, Any]:
        """Verify and extract an encrypted backup into restore_dir."""
        verification = self.verify_backup(backup_name)
        if not verification.get("valid"):
            raise ValueError(f"Backup verification failed: {verification.get('error')}")

        target = self._backup_path(backup_name)
        decrypted = self._fernet.decrypt(target.read_bytes())
        dest = Path(restore_dir)
        if dest.is_symlink() or (dest.exists() and any(dest.iterdir())):
            raise ValueError("Restore requires an empty staging directory; stop runtime before offline installation")
        dest.mkdir(parents=True, exist_ok=True)

        extracted: list[str] = []
        with tarfile.open(fileobj=io.BytesIO(decrypted), mode="r:gz") as tar:
            members = tar.getmembers()
            seen = set()
            total = 0
            for member in members:
                name = member.name
                member_path = (dest / name).resolve()
                if (not (member.isfile() or member.isdir()) or "\\" in name or ":" in name
                        or name.startswith("/") or ".." in Path(name).parts
                        or not member_path.is_relative_to(dest.resolve())
                        or name.casefold() in seen):
                    raise ValueError("Unsafe path or member in backup archive")
                seen.add(name.casefold())
                total += member.size
                if len(seen) > 10000 or total > 512 * 1024 * 1024:
                    raise ValueError("Backup exceeds staging restore limits")
            # Validate the complete member list before writing any files.
            for member in members:
                if member.name == "manifest.json":
                    continue
                member_path = (dest / member.name).resolve()
                if member.isdir():
                    member_path.mkdir(parents=True, exist_ok=True)
                else:
                    member_path.parent.mkdir(parents=True, exist_ok=True)
                    with member_path.open("xb") as target_file:
                        import shutil
                        shutil.copyfileobj(tar.extractfile(member), target_file)
                extracted.append(member.name)

        logger.info("Restored backup %s (%d items)", backup_name, len(extracted))
        return {"restored": True, "backup_file": backup_name, "files": extracted}

    def list_backups(self) -> list[dict[str, Any]]:
        """List all available backup archives."""
        items: list[dict[str, Any]] = []
        for f in sorted(self.backup_dir.glob("*.jbackup"), reverse=True):
            stat = f.stat()
            items.append({
                "name": f.name,
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            })
        return items


_backup_service: Optional[BackupService] = None


def get_backup_service() -> BackupService:
    global _backup_service
    if _backup_service is None:
        _backup_service = BackupService()
    return _backup_service
