"""
Namespaced cache service backed by Redis.

All keys are stored under ``gurupix:{namespace}:{key}`` to avoid
collisions between subsystems (recommendations, profiles, availability,
etc.).  Values are JSON-serialized so any dict/list/primitive can be
cached transparently.

Usage example (inside an async endpoint or service)::

    from app.clients.cache import CacheService

    cache = CacheService()
    await cache.set("recs", "user-123", {"items": [...]}, ttl_seconds=300)
    data = await cache.get("recs", "user-123")   # dict or None
    await cache.delete("recs", "user-123")
    await cache.invalidate_namespace("recs")      # wipe all recs cache
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.clients.redis import get_redis_client

logger = logging.getLogger("gurupix.cache")

_PREFIX = "gurupix"


class CacheService:
    """Thin wrapper around Redis providing namespaced JSON caching."""

    @staticmethod
    def _build_key(namespace: str, key: str) -> str:
        return f"{_PREFIX}:{namespace}:{key}"

    async def get(self, namespace: str, key: str) -> Any | None:
        """Return the cached value or ``None`` if missing / expired."""
        redis = get_redis_client()
        if redis is None:
            return None
        try:
            raw = await redis.get(self._build_key(namespace, key))
            if raw is None:
                return None
            return json.loads(raw)
        except Exception:
            logger.warning("Cache GET error — returning None", exc_info=True)
            return None

    async def set(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl_seconds: int = 300,
    ) -> None:
        """Store *value* as JSON with the given TTL."""
        redis = get_redis_client()
        if redis is None:
            return
        try:
            serialized = json.dumps(value)
            await redis.set(
                self._build_key(namespace, key),
                serialized,
                ex=ttl_seconds,
            )
        except Exception:
            logger.warning("Cache SET error — ignoring", exc_info=True)

    async def delete(self, namespace: str, key: str) -> None:
        """Remove a single cached entry."""
        redis = get_redis_client()
        if redis is None:
            return
        try:
            await redis.delete(self._build_key(namespace, key))
        except Exception:
            logger.warning("Cache DELETE error — ignoring", exc_info=True)

    async def invalidate_namespace(self, namespace: str) -> None:
        """Remove **all** keys under *namespace*.

        Uses SCAN so we never block Redis with a ``KEYS *`` command in
        production.
        """
        redis = get_redis_client()
        if redis is None:
            return
        pattern = f"{_PREFIX}:{namespace}:*"
        try:
            cursor: int = 0
            while True:
                cursor, keys = await redis.scan(cursor=cursor, match=pattern, count=200)
                if keys:
                    await redis.delete(*keys)
                if cursor == 0:
                    break
        except Exception:
            logger.warning("Cache INVALIDATE error — ignoring", exc_info=True)
