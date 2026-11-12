"""Media processor service with FFmpeg integration for validation, thumbnails, and conversion."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class MediaInfo:
    valid: bool
    width: Optional[int] = None
    height: Optional[int] = None
    duration_seconds: Optional[float] = None
    codec: Optional[str] = None
    bitrate: Optional[int] = None
    fps: Optional[float] = None
    has_audio: bool = False
    error: Optional[str] = None


class MediaProcessor:
    """Handles media probing, thumbnail extraction, and format conversion via FFmpeg/ffprobe."""

    def __init__(self, ffmpeg_path: Optional[str] = None):
        settings = get_settings()
        self.ffmpeg_path = ffmpeg_path or settings.ffmpeg_path
        self.ffprobe_path = (
            self.ffmpeg_path.replace("ffmpeg", "ffprobe")
            if "ffmpeg" in self.ffmpeg_path
            else "ffprobe"
        )

    def is_ffmpeg_available(self) -> bool:
        return shutil.which(self.ffmpeg_path) is not None

    def probe_media(self, file_path: str | Path) -> MediaInfo:
        """Validate a media file and extract dimensions, codec, duration, and audio presence."""
        path = Path(file_path)
        if not path.exists():
            return MediaInfo(valid=False, error=f"File not found: {file_path}")

        if not shutil.which(self.ffprobe_path):
            # Basic file validation fallback when ffprobe is not installed
            size = path.stat().st_size
            return MediaInfo(valid=size > 0, error=None if size > 0 else "Empty file")

        cmd = [
            self.ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(path),
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if proc.returncode != 0:
                return MediaInfo(valid=False, error=proc.stderr.strip() or "ffprobe failed")
            data = json.loads(proc.stdout)
        except Exception as exc:
            return MediaInfo(valid=False, error=str(exc))

        streams = data.get("streams", [])
        fmt = data.get("format", {})
        video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
        audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

        fps: Optional[float] = None
        if video_stream and video_stream.get("r_frame_rate"):
            num, _, den = video_stream["r_frame_rate"].partition("/")
            if den and float(den) != 0:
                fps = round(float(num) / float(den), 2)

        return MediaInfo(
            valid=True,
            width=video_stream.get("width") if video_stream else None,
            height=video_stream.get("height") if video_stream else None,
            duration_seconds=float(fmt["duration"]) if fmt.get("duration") else None,
            codec=video_stream.get("codec_name") if video_stream else (audio_stream.get("codec_name") if audio_stream else None),
            bitrate=int(fmt["bit_rate"]) if fmt.get("bit_rate") else None,
            fps=fps,
            has_audio=audio_stream is not None,
        )

    def generate_thumbnail(
        self,
        source_path: str | Path,
        output_path: Optional[str | Path] = None,
        timestamp_sec: float = 1.0,
        width: int = 480,
    ) -> Optional[str]:
        """Generate a JPEG thumbnail for a video or image file."""
        src = Path(source_path)
        if not src.exists():
            return None

        settings = get_settings()
        thumb_dir = Path(settings.thumbnail_dir)
        thumb_dir.mkdir(parents=True, exist_ok=True)
        out = Path(output_path) if output_path else thumb_dir / f"{src.stem}_thumb.jpg"

        if not self.is_ffmpeg_available():
            logger.warning("FFmpeg not found on PATH; skipping thumbnail generation for %s", src)
            return None

        cmd = [
            self.ffmpeg_path,
            "-y",
            "-ss", str(timestamp_sec),
            "-i", str(src),
            "-vframes", "1",
            "-vf", f"scale={width}:-1",
            str(out),
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if proc.returncode == 0 and out.exists():
                return str(out)
            logger.warning("FFmpeg thumbnail failed: %s", proc.stderr)
            return None
        except Exception as exc:
            logger.error("Thumbnail generation error: %s", exc)
            return None

    def convert_format(
        self,
        source_path: str | Path,
        output_path: str | Path,
        video_codec: str = "libx264",
        audio_codec: str = "aac",
    ) -> bool:
        """Convert media to a social-platform-ready format (e.g., MP4 H.264/AAC)."""
        if not self.is_ffmpeg_available():
            raise RuntimeError("FFmpeg executable not found")
        src = Path(source_path)
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", str(src),
            "-c:v", video_codec,
            "-c:a", audio_codec,
            "-movflags", "+faststart",
            str(out),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if proc.returncode != 0:
            logger.error("FFmpeg conversion failed: %s", proc.stderr)
            return False
        return out.exists()


_media_processor: Optional[MediaProcessor] = None


def get_media_processor() -> MediaProcessor:
    global _media_processor
    if _media_processor is None:
        _media_processor = MediaProcessor()
    return _media_processor
