"""
Unit tests for RateLimitMiddleware.

Redis is mocked so no external service is required.  Tests verify:
- Requests below the limit pass through normally.
- The (N+1)th request returns 429 when the limit is N.
- Rate-limit headers are present on every response.
- When Redis is unavailable the middleware fails open (request allowed).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_id import RequestIdMiddleware
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _make_app(limit: int = 3) -> FastAPI:
    """Build a minimal FastAPI app with only RateLimitMiddleware."""
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestIdMiddleware)

    @app.get("/ping")
    def ping() -> dict[str, str]:
        return {"pong": "ok"}

    return app


def _mock_redis(counter: dict[str, int], ttl_val: int = 58):
    """Return an AsyncMock that simulates Redis INCR / EXPIRE / TTL."""
    mock = AsyncMock()

    async def _incr(key: str) -> int:
        counter[key] = counter.get(key, 0) + 1
        return counter[key]

    async def _expire(key: str, seconds: int) -> None:
        pass

    async def _ttl(key: str) -> int:
        return ttl_val

    mock.incr = AsyncMock(side_effect=_incr)
    mock.expire = AsyncMock(side_effect=_expire)
    mock.ttl = AsyncMock(side_effect=_ttl)
    return mock


@patch("app.middleware.rate_limit.Settings")
@patch("app.middleware.rate_limit.get_redis_client")
def test_requests_below_limit_pass_through(mock_get_redis, mock_settings_cls) -> None:
    mock_settings_cls.return_value.rate_limit_per_minute = 5
    counter: dict[str, int] = {}
    mock_get_redis.return_value = _mock_redis(counter)

    app = _make_app(limit=5)
    client = TestClient(app)

    for _ in range(5):
        resp = client.get("/ping")
        assert resp.status_code == 200


@patch("app.middleware.rate_limit.Settings")
@patch("app.middleware.rate_limit.get_redis_client")
def test_exceeding_limit_returns_429(mock_get_redis, mock_settings_cls) -> None:
    mock_settings_cls.return_value.rate_limit_per_minute = 3
    counter: dict[str, int] = {}
    mock_get_redis.return_value = _mock_redis(counter)

    app = _make_app(limit=3)
    client = TestClient(app)

    for _ in range(3):
        resp = client.get("/ping")
        assert resp.status_code == 200

    resp = client.get("/ping")
    assert resp.status_code == 429
    body = resp.json()
    assert "rate limit" in body["detail"].lower()


@patch("app.middleware.rate_limit.Settings")
@patch("app.middleware.rate_limit.get_redis_client")
def test_rate_limit_headers_present(mock_get_redis, mock_settings_cls) -> None:
    mock_settings_cls.return_value.rate_limit_per_minute = 10
    counter: dict[str, int] = {}
    mock_get_redis.return_value = _mock_redis(counter)

    app = _make_app(limit=10)
    client = TestClient(app)
    resp = client.get("/ping")

    assert resp.headers.get("X-RateLimit-Limit") == "10"
    assert resp.headers.get("X-RateLimit-Remaining") is not None
    assert resp.headers.get("X-RateLimit-Reset") is not None


@patch("app.middleware.rate_limit.Settings")
@patch("app.middleware.rate_limit.get_redis_client")
def test_fail_open_when_redis_unavailable(mock_get_redis, mock_settings_cls) -> None:
    mock_settings_cls.return_value.rate_limit_per_minute = 5
    mock_get_redis.return_value = None

    app = _make_app(limit=5)
    client = TestClient(app)

    resp = client.get("/ping")
    assert resp.status_code == 200
    assert "X-RateLimit-Limit" not in resp.headers


@patch("app.middleware.rate_limit.Settings")
@patch("app.middleware.rate_limit.get_redis_client")
def test_fail_open_when_redis_raises(mock_get_redis, mock_settings_cls) -> None:
    mock_settings_cls.return_value.rate_limit_per_minute = 5
    broken = AsyncMock()
    broken.incr = AsyncMock(side_effect=ConnectionError("gone"))
    mock_get_redis.return_value = broken

    app = _make_app(limit=5)
    client = TestClient(app)

    resp = client.get("/ping")
    assert resp.status_code == 200
