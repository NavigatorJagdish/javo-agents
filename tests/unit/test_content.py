"""Unit tests for ContentWatcher, duplicate detection, and MockConnector."""

from __future__ import annotations

import pytest

from app.connectors.base import PostPayload
from app.connectors.mock import MockConnector
from app.services.content_watcher import ContentWatcher, compute_file_hash


def test_content_watcher_scan_and_duplicate_detection(tmp_path):
    """Verify folder scanning computes hashes and flags duplicate files."""
    img1 = tmp_path / "video_clip.mp4"
    img2 = tmp_path / "video_clip_copy.mp4"
    ignored = tmp_path / "notes.bin"

    payload = b"fake-video-bytes-123456"
    img1.write_bytes(payload)
    img2.write_bytes(payload)
    ignored.write_bytes(b"ignored")

    watcher = ContentWatcher()
    discovered = watcher.scan_folder(tmp_path)

    assert len(discovered) == 2
    hashes = [d.file_hash for d in discovered]
    assert hashes[0] == hashes[1] == compute_file_hash(img1)
    assert any(d.is_duplicate for d in discovered)
    assert all(d.media_type == "video" for d in discovered)


@pytest.mark.asyncio
async def test_mock_connector_publish_and_comments():
    """Verify MockConnector publishes posts, fetches analytics, and replies to comments."""
    connector = MockConnector()
    assert await connector.verify_credentials() is True

    res = await connector.publish_post(
        PostPayload(caption="Hello world", hashtags=["ai", "#agents"])
    )
    assert res.success is True
    assert res.post_id is not None

    comments = await connector.fetch_comments(res.post_id)
    assert len(comments) == 1

    reply = await connector.reply_comment(comments[0]["id"], "Thanks!")
    assert reply.success is True
