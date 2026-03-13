"""Pydantic schemas for context endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ContextCreate(BaseModel):
    """Create a context preset."""

    label: str = Field(..., min_length=1, max_length=100)
    attributes: dict[str, Any] | None = Field(
        None, description="Parsed attributes (e.g. mood, occasion)"
    )


class ContextResponse(BaseModel):
    """Context as returned by API."""

    id: int
    user_id: str
    label: str
    attributes: dict[str, Any] | None
    created_at: datetime
