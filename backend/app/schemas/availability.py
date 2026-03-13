"""
Pydantic schemas for where-to-watch availability (Stage 5.3).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class AvailabilityResponse(BaseModel):
    """Single availability record for an item in a region."""

    provider: str = Field(..., description="Streaming provider name")
    region: str = Field(..., description="Region code (e.g. US)")
    url: str | None = Field(default=None, description="Link to watch")
    availability_type: str = Field(
        ...,
        description="Type: stream, rent, buy, etc.",
    )
