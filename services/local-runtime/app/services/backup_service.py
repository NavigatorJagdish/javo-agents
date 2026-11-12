"""Encrypted backup, restore, and verification service."""

from __future__ import annotations

import base64
import hashlib
import io
import json
import logging
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
        raw_secret = encryption_key or settings.encryption_key or settings.secret_key
        derived = base64.urlsafe_b64encode(hashlib.sha256(raw_secret.encode()).digest())
        self._fernet = Fernet(derived)

    def create_backup(
        self,
        include_paths: Optional[list[str | Path]] = None,
        label: str = "manual",
    ) -> dict[str, Any]:
        """Bundle database and selected directories into an encrypted .jbackup archive."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_name = f"javo_backup_{label}_{timestamp}.jbackup"
        dest_path = self.backup_dir / backup_name

        targets = [Path(p) for p in (include_paths or ["javo_agents.db", "scheduler_jobs.db"])]
        buf = io.BytesIO()
        included_files: list[str] = []

        with tarfile.open(fileobj=buf, mode="w:gz") as tar:
            for target in targets:
                if target.exists():
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

        raw_bytes = buf.getvalue()
        checksum = hashlib.sha256(raw_bytes).hexdigest()
        encrypted = self._fernet.encrypt(raw_bytes)
        dest_path.write_bytes(encrypted)

        meta_path = dest_path.with_suffix(".jbackup.sha256")
        meta_path.write_text(checksum, encoding="utf-8")

        logger.info("Created encrypted backup %s (%d files)", dest_path, len(included_files))
        return {
            "backup_file": backup_name,
            "path": str(dest_path),
            "size_bytes": len(encrypted),
            "checksum": checksum,
            "files": included_files,
            "created_at": manifest["created_at"],
        }

    def verify_backup(self, backup_name: str) -> dict[str, Any]:
        """Decrypt and verify integrity of a backup file against its SHA-256 checksum."""
        target = self.backup_dir / backup_name
        if not target.exists():
            return {"valid": False, "error": "Backup file not found"}

        try:
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

        target = self.backup_dir / backup_name
        decrypted = self._fernet.decrypt(target.read_bytes())
        dest = Path(restore_dir)
        dest.mkdir(parents=True, exist_ok=True)

        extracted: list[str] = []
        with tarfile.open(fileobj=io.BytesIO(decrypted), mode="r:gz") as tar:
            for member in tar.getmembers():
                if member.name == "manifest.json":
                    continue
                # Prevent path traversal
                member_path = (dest / member.name).resolve()
                if not str(member_path).startswith(str(dest.resolve())):
                    raise ValueError(f"Unsafe path in backup archive: {member.name}")
                tar.extract(member, path=dest)
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
