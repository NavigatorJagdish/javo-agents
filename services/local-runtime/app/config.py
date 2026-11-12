"""Application configuration using Pydantic Settings."""

from __future__ import annotations

import os
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


def _default_secret_key() -> str:
    """Provision a durable per-installation 256-bit secret key if JAVO_SECRET_KEY is not set."""
    env_val = os.environ.get("JAVO_SECRET_KEY")
    if env_val and env_val != "change-me-in-production-use-a-real-secret-key":
        return env_val
    from app.core.security import get_durable_app_secret

    return get_durable_app_secret()


class Settings(BaseSettings):
    """Central configuration loaded from environment variables."""

    # Application
    app_name: str = "Javo Agents"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"
    host: str = "127.0.0.1"
    port: int = 8000
    secret_key: str = Field(default_factory=_default_secret_key)
    allowed_origins: list[str] = Field(default=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"])

    # Database
    database_url: str = Field(default="sqlite+aiosqlite:///./javo_agents.db")
    database_echo: bool = False

    # Content paths
    content_root: str = Field(default="./content")
    upload_dir: str = Field(default="./uploads")
    backup_dir: str = Field(default="./backups")
    thumbnail_dir: str = Field(default="./thumbnails")

    # AI Providers
    ollama_base_url: str = "http://localhost:11434"
    ollama_default_model: str = "llama3.2"

    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.0-flash"

    openai_api_key: Optional[str] = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    default_ai_provider: str = "ollama"  # ollama | gemini | openai

    # AI Budget (Zero-Cost Default per Budget Guardian)
    ai_daily_budget: float = 0.0  # USD
    ai_monthly_budget: float = 0.0
    max_tokens_per_request: int = 4096

    # Scheduler
    scheduler_db_url: str = Field(default="sqlite:///./scheduler_jobs.db")
    scheduler_check_interval: int = 30  # seconds

    # Telegram
    telegram_bot_token: Optional[str] = None
    telegram_mode: str = Field(default="disabled")  # "webhook" | "polling" | "disabled"
    telegram_webhook_url: Optional[str] = None
    telegram_webhook_secret: Optional[str] = None
    telegram_allowed_users: list[str] = Field(default=[])

    # Security
    encryption_key: Optional[str] = None
    owner_token: Optional[str] = None
    token_expiry_hours: int = 24
    max_sessions_per_user: int = 5
    require_device_approval: bool = True

    # Resource limits
    max_concurrent_agents: int = 5
    max_queue_size: int = 100
    cpu_limit_percent: float = 80.0
    memory_limit_percent: float = 80.0

    # FFmpeg
    ffmpeg_path: str = "ffmpeg"

    model_config = {
        "env_prefix": "JAVO_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get cached settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
