"""
Per-IP, per-route rate limiting backed by Redis.

Uses a fixed-window counter:  for each (IP, route) pair a Redis key is
incremented on every request.  The key auto-expires after the window
(default 60 s).  When the counter exceeds the configured limit the
middleware returns 429 Too Many Requests with the standard error shape.

If Redis is unavailable the request is allowed through (fail-open) so
local development without Redis still works.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.clients.redis import get_redis_client
from app.core.config import Settings
from app.schemas.system import ErrorResponse

logger = logging.getLogger("gurupix.rate_limit")

_WINDOW_SECONDS = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Fixed-window rate limiter.

    Adds response headers on every request so clients can track their
    remaining quota:

    - ``X-RateLimit-Limit``     – max requests allowed in the window
    - ``X-RateLimit-Remaining`` – requests left in the current window
    - ``X-RateLimit-Reset``     – epoch second when the window resets
    """

    def __init__(self, app: Callable, **kwargs: object) -> None:
        super().__init__(app, **kwargs)
        settings = Settings()
        self.max_requests: int = settings.rate_limit_per_minute
        self.window: int = _WINDOW_SECONDS

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        redis = get_redis_client()
        if redis is None:
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        route = request.url.path
        redis_key = f"rl:{client_ip}:{route}"

        try:
            current_count = await redis.incr(redis_key)
            if current_count == 1:
                await redis.expire(redis_key, self.window)

            ttl = await redis.ttl(redis_key)
            reset_at = int(time.time()) + max(ttl, 0)
            remaining = max(self.max_requests - current_count, 0)

            if current_count > self.max_requests:
                body = ErrorResponse(
                    detail="Rate limit exceeded. Try again later.",
                    request_id=getattr(request.state, "request_id", ""),
                )
                response = JSONResponse(
                    status_code=429, content=body.model_dump()
                )
                self._set_rate_headers(response, remaining, reset_at)
                return response

            response = await call_next(request)
            self._set_rate_headers(response, remaining, reset_at)
            return response

        except Exception:
            logger.warning("Redis error in rate limiter — fail-open", exc_info=True)
            return await call_next(request)

    def _set_rate_headers(
        self, response: Response, remaining: int, reset_at: int
    ) -> None:
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_at)

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
