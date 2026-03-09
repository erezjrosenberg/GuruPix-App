from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class VersionResponse(BaseModel):
    version: str


class ErrorResponse(BaseModel):
    detail: str
    request_id: str
