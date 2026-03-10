"""
AuthMiddleware — lightweight observability layer for authentication.

This middleware does NOT enforce authentication (that is the job of the
``get_current_user`` dependency on individual routes). Instead it:

1. Reads the JWT from the Authorization header (if present).
2. Decodes it to extract the ``sub`` (user id).
3. Attaches ``request.state.user_id`` so downstream middleware
   (e.g. LoggingMiddleware) can include the user id in structured logs.

If the header is missing or the token is invalid the request still proceeds
— the user_id is simply left as None.
"""

from __future__ import annotations

import logging

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.security import decode_access_token

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request.state.user_id = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[len("Bearer "):]
            try:
                payload = decode_access_token(token)
                request.state.user_id = payload.get("sub")
            except Exception:
                pass  # invalid/expired — leave user_id as None
        return await call_next(request)
