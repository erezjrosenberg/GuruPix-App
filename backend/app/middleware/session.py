"""
Session tracking middleware.

Ensures every request/response carries a stable ``session_id``:

1. If the client sends an ``X-Session-Id`` header, that value is reused.
2. Otherwise a new UUID-4 is generated.
3. The session_id is stored on ``request.state.session_id`` for downstream
   code (logging, event recording, etc.).
4. The session_id is echoed back via the ``X-Session-Id`` response header.
5. If Redis is available the session is "touched" (SET with TTL) so we
   can track active sessions and expire stale ones.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.clients.redis import get_redis_client
from app.core.config import Settings

logger = logging.getLogger("gurupix.session")

_HEADER = "X-Session-Id"


class SessionMiddleware(BaseHTTPMiddleware):
    """Attach and propagate a session identifier on every request."""

    def __init__(self, app: Callable) -> None:
        super().__init__(app)
        settings = Settings()
        self.session_ttl: int = settings.session_ttl_seconds

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        session_id = request.headers.get(_HEADER) or str(uuid.uuid4())
        request.state.session_id = session_id

        await self._touch_session(session_id)

        response = await call_next(request)
        response.headers[_HEADER] = session_id
        return response

    async def _touch_session(self, session_id: str) -> None:
        """Record the session in Redis with a sliding TTL."""
        redis = get_redis_client()
        if redis is None:
            return
        try:
            await redis.set(
                f"session:{session_id}",
                "active",
                ex=self.session_ttl,
            )
        except Exception:
            logger.warning("Redis error while touching session — ignoring", exc_info=True)
