from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class TimingMiddleware(BaseHTTPMiddleware):
    """Measure request handling time and surface it via response header.

    Adds `X-Response-Time-ms` with a millisecond duration (float as string).
    """

    header_name = "X-Response-Time-ms"

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        response.headers[self.header_name] = f"{duration_ms:.2f}"
        return response
