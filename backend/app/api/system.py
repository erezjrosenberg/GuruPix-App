from __future__ import annotations

from fastapi import APIRouter

from app.core.version import get_app_version
from app.schemas.system import HealthResponse, VersionResponse

router = APIRouter(prefix="/api/v1", tags=["system"])


@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    """Simple liveness probe."""
    return HealthResponse(status="ok")


@router.get("/version", response_model=VersionResponse)
async def get_version() -> VersionResponse:
    """Backend version information used by clients and monitoring."""
    return VersionResponse(version=get_app_version())
