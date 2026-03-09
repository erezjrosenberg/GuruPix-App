"""
Integration tests for Stage 3: Redis — rate limiting, sessions, cache.

These tests require a running Redis (e.g. docker compose up -d in infra/).
They verify:
1. The Redis client connects and can ping.
2. Rate limiting triggers 429 after exceeding the configured limit.
3. Every response includes an X-Session-Id header.
4. A client-provided X-Session-Id is echoed back.
5. CacheService round-trips values through real Redis.

Run with: pytest tests/integration/test_redis_integration.py -v
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest
import redis as sync_redis
from app.clients.cache import CacheService
from app.core.config import Settings


def _redis_available() -> bool:
    """Return True if we can reach Redis at the configured URL."""
    try:
        settings = Settings()
        r = sync_redis.from_url(settings.redis_url)
        r.ping()
        r.close()
        return True
    except Exception:
        return False


@pytest.fixture(scope="module")
def require_redis() -> None:
    if not _redis_available():
        pytest.skip(
            "Redis not available. Start with: cd infra && docker compose up -d"
        )


@pytest.fixture(scope="module")
def settings() -> Settings:
    return Settings()


@pytest.fixture()
def sync_client(require_redis: None, settings: Settings) -> Any:
    """Provide a sync Redis client for direct verification."""
    r = sync_redis.from_url(settings.redis_url, decode_responses=True)
    yield r
    r.close()


# ── Redis connectivity ────────────────────────────────────────────────────


def test_redis_ping(require_redis: None, settings: Settings) -> None:
    r = sync_redis.from_url(settings.redis_url)
    assert r.ping() is True
    r.close()


# ── Rate limiting ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_rate_limit_triggers_after_n_requests(
    require_redis: None, sync_client: Any
) -> None:
    """Send more requests than the limit and verify we get 429."""
    import os

    from httpx import ASGITransport, AsyncClient

    os.environ["RATE_LIMIT_PER_MINUTE"] = "5"

    try:
        from app.main import create_app

        test_app = create_app()
        unique_ip = f"10.99.{uuid.uuid4().int % 256}.{uuid.uuid4().int % 256}"

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            import app.clients.redis as redis_mod

            await redis_mod.init_redis()

            statuses: list[int] = []
            for _ in range(7):
                resp = await client.get(
                    "/api/v1/health",
                    headers={"X-Forwarded-For": unique_ip},
                )
                statuses.append(resp.status_code)

            assert 429 in statuses, f"Expected a 429 in {statuses}"
            first_429_idx = statuses.index(429)
            assert first_429_idx >= 5, "429 should appear after the 5th request"

            await redis_mod.close_redis()
    finally:
        os.environ.pop("RATE_LIMIT_PER_MINUTE", None)


# ── Session headers ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_session_id_present_in_response(require_redis: None) -> None:
    from app.main import create_app
    from httpx import ASGITransport, AsyncClient

    test_app = create_app()
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    sid = resp.headers.get("X-Session-Id")
    assert sid is not None
    uuid.UUID(sid)


@pytest.mark.asyncio
async def test_session_id_echoed_when_provided(require_redis: None) -> None:
    from app.main import create_app
    from httpx import ASGITransport, AsyncClient

    test_app = create_app()
    transport = ASGITransport(app=test_app)
    custom = f"integration-{uuid.uuid4()}"
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/health", headers={"X-Session-Id": custom}
        )
    assert resp.headers.get("X-Session-Id") == custom


# ── CacheService round-trip ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cache_set_get_delete_roundtrip(
    require_redis: None, sync_client: Any
) -> None:
    import app.clients.redis as redis_mod

    await redis_mod.init_redis()

    cache = CacheService()
    ns = "test"
    key = f"roundtrip-{uuid.uuid4()}"
    value = {"items": [1, 2, 3], "nested": {"ok": True}}

    await cache.set(ns, key, value, ttl_seconds=30)
    result = await cache.get(ns, key)
    assert result == value

    await cache.delete(ns, key)
    assert await cache.get(ns, key) is None

    await redis_mod.close_redis()


@pytest.mark.asyncio
async def test_cache_invalidate_namespace(
    require_redis: None, sync_client: Any
) -> None:
    import app.clients.redis as redis_mod

    await redis_mod.init_redis()

    cache = CacheService()
    ns = f"inv-{uuid.uuid4().hex[:8]}"

    await cache.set(ns, "a", "val-a", ttl_seconds=30)
    await cache.set(ns, "b", "val-b", ttl_seconds=30)

    assert await cache.get(ns, "a") == "val-a"
    assert await cache.get(ns, "b") == "val-b"

    await cache.invalidate_namespace(ns)

    assert await cache.get(ns, "a") is None
    assert await cache.get(ns, "b") is None

    await redis_mod.close_redis()
