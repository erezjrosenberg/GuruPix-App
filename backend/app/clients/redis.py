"""
Async Redis client with lifecycle management.

Provides a singleton Redis connection pool that is initialized when the
FastAPI app starts and closed when it stops.  Other modules obtain the
shared client via ``get_redis_client()``.

If Redis is unreachable at startup the app still boots (fail-open) so
local development without Redis is possible; a warning is logged instead.
"""

from __future__ import annotations

import logging

import redis.asyncio as aioredis

from app.core.config import Settings

logger = logging.getLogger("gurupix.redis")

_redis_client: aioredis.Redis | None = None


async def init_redis(settings: Settings | None = None) -> None:
    """Create the shared async Redis connection pool.

    Called once during FastAPI startup.  Stores the client in module-level
    ``_redis_client`` so the rest of the app can retrieve it with
    ``get_redis_client()``.
    """
    global _redis_client
    if settings is None:
        settings = Settings()

    try:
        _redis_client = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
        await _redis_client.ping()
        logger.info("Redis connected at %s", settings.redis_url)
    except Exception:
        logger.warning(
            "Redis unavailable at %s — running in fail-open mode",
            settings.redis_url,
            exc_info=True,
        )
        _redis_client = None


async def close_redis() -> None:
    """Gracefully close the Redis connection pool.

    Called during FastAPI shutdown.
    """
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("Redis connection closed")


def get_redis_client() -> aioredis.Redis | None:
    """Return the current Redis client, or ``None`` if unavailable."""
    return _redis_client
