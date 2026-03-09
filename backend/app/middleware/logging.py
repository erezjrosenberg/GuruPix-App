from __future__ import annotations

import json
import logging
import time
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("gurupix.request")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Structured per-request access logging.

    Logs a single JSON line per request, including:
    - method, path, status_code
    - request_id (from RequestIdMiddleware when available)
    - duration_ms
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        request_id = getattr(request.state, "request_id", None)

        payload = {
            "event": "http_request",
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "request_id": request_id,
        }

        logger.info(json.dumps(payload, sort_keys=True))
        return response
