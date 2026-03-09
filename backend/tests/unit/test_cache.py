"""
Unit tests for CacheService.

Redis is mocked so no external service is required.  Tests verify:
- get / set / delete operate on correctly namespaced keys.
- Values are JSON round-tripped.
- TTL is forwarded to Redis SET.
- When Redis is None every method returns gracefully.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from app.clients.cache import CacheService


@pytest.fixture()
def cache() -> CacheService:
    return CacheService()


def test_build_key_format() -> None:
    assert CacheService._build_key("recs", "user-1") == "gurupix:recs:user-1"


@pytest.mark.asyncio
@patch("app.clients.cache.get_redis_client")
async def test_set_stores_json_with_ttl(mock_redis, cache: CacheService) -> None:
    redis_mock = AsyncMock()
    mock_redis.return_value = redis_mock

    await cache.set("recs", "u1", {"items": [1, 2]}, ttl_seconds=120)

    redis_mock.set.assert_called_once()
    args, kwargs = redis_mock.set.call_args
    assert args[0] == "gurupix:recs:u1"
    assert json.loads(args[1]) == {"items": [1, 2]}
    assert kwargs["ex"] == 120


@pytest.mark.asyncio
@patch("app.clients.cache.get_redis_client")
async def test_get_returns_deserialized_value(mock_redis, cache: CacheService) -> None:
    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(return_value=json.dumps({"a": 1}))
    mock_redis.return_value = redis_mock

    result = await cache.get("ns", "k")
    assert result == {"a": 1}
    redis_mock.get.assert_called_once_with("gurupix:ns:k")


@pytest.mark.asyncio
@patch("app.clients.cache.get_redis_client")
async def test_get_returns_none_on_miss(mock_redis, cache: CacheService) -> None:
    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    mock_redis.return_value = redis_mock

    assert await cache.get("ns", "missing") is None


@pytest.mark.asyncio
@patch("app.clients.cache.get_redis_client")
async def test_delete_calls_redis_delete(mock_redis, cache: CacheService) -> None:
    redis_mock = AsyncMock()
    mock_redis.return_value = redis_mock

    await cache.delete("recs", "u1")
    redis_mock.delete.assert_called_once_with("gurupix:recs:u1")


@pytest.mark.asyncio
@patch("app.clients.cache.get_redis_client")
async def test_all_methods_noop_when_redis_is_none(mock_redis, cache: CacheService) -> None:
    mock_redis.return_value = None

    assert await cache.get("ns", "k") is None
    await cache.set("ns", "k", "v")
    await cache.delete("ns", "k")
    await cache.invalidate_namespace("ns")


@pytest.mark.asyncio
@patch("app.clients.cache.get_redis_client")
async def test_invalidate_namespace_uses_scan(mock_redis, cache: CacheService) -> None:
    redis_mock = AsyncMock()
    redis_mock.scan = AsyncMock(return_value=(0, ["gurupix:ns:a", "gurupix:ns:b"]))
    mock_redis.return_value = redis_mock

    await cache.invalidate_namespace("ns")

    redis_mock.scan.assert_called_once()
    redis_mock.delete.assert_called_once_with("gurupix:ns:a", "gurupix:ns:b")
