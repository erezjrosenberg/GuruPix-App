from __future__ import annotations

import logging
import uuid
from collections.abc import Awaitable, Callable

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.schemas.system import ErrorResponse

logger = logging.getLogger("gurupix.error")


class ErrorMiddleware(BaseHTTPMiddleware):
    """Normalize error responses and attach request IDs.

    Ensures all errors follow the common shape:
    `{ "detail": string, "request_id": string }`
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = getattr(request.state, "request_id", None)
        if request_id is None:
            request_id = str(uuid.uuid4())
            request.state.request_id = request_id

        try:
            return await call_next(request)
        except RequestValidationError as exc:
            logger.warning(
                "Request validation error",
                extra={"request_id": request_id, "errors": exc.errors()},
            )
            return self._error_response(
                status_code=422,
                detail="Request validation failed",
                request_id=request_id,
            )
        except StarletteHTTPException as exc:
            logger.info(
                "HTTP error",
                extra={
                    "request_id": request_id,
                    "status_code": exc.status_code,
                    "detail": exc.detail,
                },
            )
            return self._error_response(
                status_code=exc.status_code,
                detail=str(exc.detail),
                request_id=request_id,
            )
        except Exception:  # pragma: no cover - defensive (catch-all)
            logger.exception(
                "Unhandled server error",
                extra={"request_id": request_id},
            )
            return self._error_response(
                status_code=500,
                detail="Internal server error",
                request_id=request_id,
            )

    @staticmethod
    def _error_response(status_code: int, detail: str, request_id: str) -> JSONResponse:
        body = ErrorResponse(detail=detail, request_id=request_id)
        return JSONResponse(status_code=status_code, content=body.model_dump())
