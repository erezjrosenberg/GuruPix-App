"""Shared fixtures for integration tests (require Postgres + Redis via docker compose)."""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient


def _pg_available() -> bool:
    """Use Settings so CI (port 5433) and local (5432) both work."""
    try:
        import psycopg2

        from app.core.config import Settings

        settings = Settings()
        url = settings.get_sync_database_url()
        conn = psycopg2.connect(url)
        conn.close()
        return True
    except Exception:
        return False


@pytest.fixture(scope="module")
def require_pg() -> None:
    if not _pg_available():
        pytest.skip("Postgres not available — start with: cd infra && docker compose up -d")


@pytest.fixture()
async def client(require_pg: None) -> AsyncClient:  # type: ignore[misc]
    import app.clients.redis as redis_mod
    from app.db.session import reset_engine
    from app.main import create_app

    reset_engine()
    test_app = create_app()
    transport = ASGITransport(app=test_app)
    await redis_mod.init_redis()
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c  # type: ignore[misc]
    await redis_mod.close_redis()
    reset_engine()


def unique_email(prefix: str = "test") -> str:
    """Generate a unique email address for test isolation."""
    return f"{prefix}-{uuid.uuid4().hex[:12]}@example.com"
