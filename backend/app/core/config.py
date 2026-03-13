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
    # Higher in development to avoid 429s during hot reload and rapid navigation.
    rate_limit_per_minute: int = 500

    # Session TTL in seconds (how long an idle session lives in Redis).
    session_ttl_seconds: int = 86400

    # --- JWT auth (Stage 4) ---
    secret_key: str = "change-me-in-production-use-long-random-string"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # --- Google OAuth (Stage 4) ---
    google_client_id: str = ""
    google_client_secret: str = ""
    # Where Google redirects after sign-in. Must match exactly what you configure in
    # Google Cloud Console. For local dev with frontend on 5173, use:
    #   OAUTH_REDIRECT_URI=http://localhost:5173/auth/google/callback
    # If unset, falls back to oauth_callback_base_url + /api/v1/auth/google/callback
    # (user lands on backend and sees JSON; frontend GoogleCallbackPage won't be used).
    oauth_redirect_uri: str | None = None
    oauth_callback_base_url: str = "http://localhost:8000"

    def get_oauth_redirect_uri(self) -> str:
        """Return the OAuth redirect URI (must match Google Console config)."""
        if self.oauth_redirect_uri:
            return self.oauth_redirect_uri
        return f"{self.oauth_callback_base_url}/api/v1/auth/google/callback"

    # --- Admin (Stage 5) ---
    # Comma-separated list of emails allowed to call admin endpoints (e.g. /ingest/items).
    admin_emails: str = ""

    def get_admin_emails_set(self) -> set[str]:
        """Return set of admin emails (lowercase, stripped, non-empty)."""
        if not self.admin_emails:
            return set()
        return {e.strip().lower() for e in self.admin_emails.split(",") if e.strip()}

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
