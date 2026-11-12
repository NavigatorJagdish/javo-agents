"""Folder watcher service with watchdog, file hashing, and duplicate detection."""

from __future__ import annotations

import hashlib
import logging
import mimetypes
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from watchdog.events import FileCreatedEvent, FileModifiedEvent, FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".gif",
    ".mp4", ".mov", ".mkv", ".avi", ".webm",
    ".mp3", ".wav", ".m4a", ".ogg",
    ".pdf", ".txt", ".md",
}


@dataclass
class DiscoveredAsset:
    file_path: str
    file_name: str
    file_hash: str
    file_size: int
    mime_type: str
    media_type: str
    is_duplicate: bool
    discovered_at: str


def compute_file_hash(file_path: str | Path, chunk_size: int = 65536) -> str:
    """Compute SHA-256 hash of a file for duplicate detection."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def classify_media_type(mime_type: str, extension: str) -> str:
    if mime_type.startswith("image/") or extension in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        return "image"
    if mime_type.startswith("video/") or extension in {".mp4", ".mov", ".mkv", ".avi", ".webm"}:
        return "video"
    if mime_type.startswith("audio/") or extension in {".mp3", ".wav", ".m4a", ".ogg"}:
        return "audio"
    return "document"


class _ContentEventHandler(FileSystemEventHandler):
    def __init__(self, watcher: ContentWatcher):
        self.watcher = watcher

    def on_created(self, event: FileCreatedEvent) -> None:
        if not event.is_directory:
            self.watcher.process_file(event.src_path)

    def on_modified(self, event: FileModifiedEvent) -> None:
        if not event.is_directory:
            self.watcher.process_file(event.src_path)


class ContentWatcher:
    """Watches configured content directories, hashes files, and tracks duplicates."""

    def __init__(self, on_asset_callback: Optional[Callable[[DiscoveredAsset], None]] = None):
        self._observer: Optional[Observer] = None
        self._watched_dirs: set[str] = set()
        self._known_hashes: dict[str, str] = {}  # hash -> first file_path
        self._on_asset = on_asset_callback

    def register_known_hash(self, file_hash: str, file_path: str) -> None:
        self._known_hashes[file_hash] = file_path

    def is_duplicate(self, file_hash: str) -> bool:
        return file_hash in self._known_hashes

    def process_file(self, file_path: str | Path) -> Optional[DiscoveredAsset]:
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            return None
        ext = path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            return None

        file_hash = compute_file_hash(path)
        duplicate = self.is_duplicate(file_hash) and self._known_hashes[file_hash] != str(path)
        if not duplicate:
            self._known_hashes[file_hash] = str(path)

        mime_type, _ = mimetypes.guess_type(str(path))
        mime_type = mime_type or "application/octet-stream"
        asset = DiscoveredAsset(
            file_path=str(path.resolve()),
            file_name=path.name,
            file_hash=file_hash,
            file_size=path.stat().st_size,
            mime_type=mime_type,
            media_type=classify_media_type(mime_type, ext),
            is_duplicate=duplicate,
            discovered_at=datetime.now(timezone.utc).isoformat(),
        )
        if self._on_asset:
            try:
                self._on_asset(asset)
            except Exception as exc:
                logger.error("Asset callback failed for %s: %s", path, exc)
        return asset

    def scan_folder(self, folder_path: str | Path, recursive: bool = True) -> list[DiscoveredAsset]:
        """Synchronously scan a folder and return all discovered assets."""
        root = Path(folder_path)
        if not root.exists():
            root.mkdir(parents=True, exist_ok=True)
            return []

        iterator = root.rglob("*") if recursive else root.glob("*")
        results: list[DiscoveredAsset] = []
        for entry in iterator:
            if entry.is_file():
                asset = self.process_file(entry)
                if asset is not None:
                    results.append(asset)
        logger.info("Scanned folder %s: found %d assets", root, len(results))
        return results

    def start_watching(self, folder_path: str | Path) -> None:
        """Start watchdog observer on the given folder."""
        root = Path(folder_path)
        root.mkdir(parents=True, exist_ok=True)
        resolved = str(root.resolve())
        if resolved in self._watched_dirs:
            return

        if self._observer is None:
            self._observer = Observer()
            self._observer.start()

        handler = _ContentEventHandler(self)
        self._observer.schedule(handler, resolved, recursive=True)
        self._watched_dirs.add(resolved)
        logger.info("Started watching content folder: %s", resolved)

    def stop(self) -> None:
        """Stop the watchdog observer."""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=5.0)
            self._observer = None
            self._watched_dirs.clear()
            logger.info("Stopped ContentWatcher")


_content_watcher: Optional[ContentWatcher] = None


def get_content_watcher() -> ContentWatcher:
    global _content_watcher
    if _content_watcher is None:
        _content_watcher = ContentWatcher()
    return _content_watcher
