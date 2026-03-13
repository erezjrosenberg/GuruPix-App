"""GuruPix FastAPI application entrypoint."""

from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.auth import router as auth_router
from app.api.availability import router as availability_router
from app.api.ingest import router as ingest_router
from app.api.items import router as items_router
from app.api.profiles import router as profiles_router
from app.api.reviews import router as reviews_router
from app.api.system import router as system_router
from app.clients.redis import close_redis, init_redis
from app.core.version import get_app_version
from app.middleware import (
    AuthMiddleware,
    ErrorMiddleware,
    LoggingMiddleware,
    RateLimitMiddleware,
    RequestIdMiddleware,
    SessionMiddleware,
    TimingMiddleware,
)
from app.schemas.system import ErrorResponse


def _build_error_response(status_code: int, detail: str, request: Request) -> JSONResponse:
    """Shared helper to build normalized error responses."""
    request_id = getattr(request.state, "request_id", None)
    if request_id is None:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

    body = ErrorResponse(detail=detail, request_id=request_id)
    response = JSONResponse(status_code=status_code, content=body.model_dump())
    response.headers["X-Request-Id"] = request_id
    return response


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application-wide startup / shutdown resources."""
    await init_redis()
    yield
    await close_redis()


def create_app() -> FastAPI:
    """Application factory used by uvicorn and tests."""
    logging.basicConfig(level=logging.INFO)

    app = FastAPI(
        title="GuruPix API",
        description="Hyper-personalized movie & TV recommendations",
        version=get_app_version(),
        lifespan=_lifespan,
    )

    # CORS — allow frontend (e.g. localhost:5173) to call API
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Middleware stack — last added = outermost (runs first on incoming request):
    #   RequestIdMiddleware → TimingMiddleware → AuthMiddleware → SessionMiddleware
    #   → RateLimitMiddleware → LoggingMiddleware → ErrorMiddleware → App
    app.add_middleware(ErrorMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(SessionMiddleware)
    app.add_middleware(AuthMiddleware)
    app.add_middleware(TimingMiddleware)
    app.add_middleware(RequestIdMiddleware)

    # Global exception handlers so even 404/validation errors use the standard error shape.
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        return _build_error_response(
            status_code=exc.status_code, detail=str(exc.detail), request=request
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return _build_error_response(
            status_code=422,
            detail="Request validation failed",
            request=request,
        )

    # System endpoints: health + version under /api/v1
    app.include_router(system_router)

    # Auth endpoints: signup, login, me under /api/v1/auth
    app.include_router(auth_router)

    # Profile endpoints: GET/PATCH/POST /profiles/me
    app.include_router(profiles_router)

    # Ingest endpoints: admin-only seed loading under /api/v1/ingest
    app.include_router(ingest_router)

    # Catalog, availability, reviews (Stage 5.3–5.4)
    app.include_router(items_router)
    app.include_router(availability_router)
    app.include_router(reviews_router)

    @app.get("/")
    def root() -> dict[str, str]:
        """Simple root endpoint pointing to docs."""
        return {"message": "GuruPix API — see /docs for OpenAPI"}

    return app


app = create_app()
