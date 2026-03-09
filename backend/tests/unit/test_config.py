"""
Unit tests for app.core.config.Settings — specifically get_sync_database_url().

Three branches:
1. database_url_sync explicitly provided -> return it as-is
2. database_url_sync is None, database_url contains +asyncpg -> strip +asyncpg
3. database_url_sync is None, database_url has no +asyncpg -> return database_url unchanged
"""

from __future__ import annotations

from app.core.config import Settings


def test_get_sync_database_url_returns_explicit_sync_url() -> None:
    s = Settings(
        database_url="postgresql+asyncpg://host/db",
        database_url_sync="postgresql://custom-sync/db",
    )
    assert s.get_sync_database_url() == "postgresql://custom-sync/db"


def test_get_sync_database_url_strips_asyncpg_when_no_explicit_sync() -> None:
    s = Settings(
        database_url="postgresql+asyncpg://user:pw@host:5432/mydb",
        database_url_sync=None,
    )
    assert s.get_sync_database_url() == "postgresql://user:pw@host:5432/mydb"


def test_get_sync_database_url_returns_unchanged_when_no_asyncpg() -> None:
    s = Settings(
        database_url="postgresql://user:pw@host:5432/mydb",
        database_url_sync=None,
    )
    assert s.get_sync_database_url() == "postgresql://user:pw@host:5432/mydb"


def test_redis_url_has_sensible_default() -> None:
    s = Settings()
    assert s.redis_url.startswith("redis://")


def test_rate_limit_per_minute_default_is_100() -> None:
    s = Settings()
    assert s.rate_limit_per_minute == 100


def test_session_ttl_seconds_default_is_one_day() -> None:
    s = Settings()
    assert s.session_ttl_seconds == 86400
