"""
Pydantic schemas for review aggregate signals (Stage 5.4).

Legal-first: aggregate scores only, no full review text.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ReviewAggregateResponse(BaseModel):
    """Single review source aggregate for an item."""

    source: str = Field(..., description="Review source (e.g. RT_CRITICS)")
    score: float = Field(..., description="Aggregate score")
    scale: float = Field(..., description="Scale (e.g. 100 or 5)")
    normalized_score: float | None = Field(
        default=None,
        description="Score normalized to 0-100 for display",
    )
