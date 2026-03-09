"""
Application settings loaded from environment variables.

Why: The backend needs to know the database URL, Redis URL, etc. We centralize
that here so every module (including Alembic) reads from one place. We use
pydantic-settings to validate and load from .env and env vars.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All configurable settings for the GuruPix backend.

    Values are read from environment variables (and optionally from a .env file).
    For example, DATABASE_URL is read from the env var DATABASE_URL.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database: async URL for the app (e.g. postgresql+asyncpg://...)
    database_url: str = "postgresql+asyncpg://gurupix:gurupix_local@localhost:5432/gurupix"

    # Sync URL for Alembic migrations (Alembic uses sync drivers by default).
    # If not set, we derive it from database_url by replacing +asyncpg with nothing.
    database_url_sync: str | None = None

    # Redis connection URL (used for caching, rate limiting, session tracking).
    redis_url: str = "redis://localhost:6379/0"

    # Maximum requests per IP per route within a 60-second window.
    rate_limit_per_minute: int = 100

    # Session TTL in seconds (how long an idle session lives in Redis).
    session_ttl_seconds: int = 86400

    def get_sync_database_url(self) -> str:
        """
        Return the database URL that Alembic and sync code use.

        - If DATABASE_URL_SYNC is set in the environment, use it.
        - Otherwise, convert DATABASE_URL from async form to sync:
          postgresql+asyncpg://... -> postgresql://... (psycopg2)
        """
        if self.database_url_sync:
            return self.database_url_sync
        url = self.database_url
        if "+asyncpg" in url:
            return url.replace("+asyncpg", "", 1)
        return url
