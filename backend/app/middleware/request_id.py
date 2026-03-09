from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Ensure every request/response has a stable request ID.

    - Accepts an incoming `X-Request-Id` header when provided.
    - Otherwise, generates a new UUID4.
    - Stores the ID on `request.state.request_id` for downstream use.
    - Echoes the ID back on the response header.
    """

    def __init__(self, app: Callable, header_name: str = "X-Request-Id") -> None:
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get(self.header_name) or str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers[self.header_name] = request_id
        return response
