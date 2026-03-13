"""
Review aggregates API for Stage 5.4 (legal-first, MVP-safe).

GET /reviews/aggregate returns list of sources + scores for an item.
No full review text — aggregate scores only.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.reviews import ReviewAggregateResponse
from app.services.reviews import get_reviews_for_item

router = APIRouter(prefix="/api/v1", tags=["reviews"])


def _normalize_score(score: float, scale: float) -> float:
    """Normalize score to 0-100 for display."""
    if scale <= 0:
        return 0.0
    return round((score / scale) * 100, 1)


@router.get("/reviews/aggregate", response_model=list[ReviewAggregateResponse])
async def get_reviews_aggregate(
    item_id: int = Query(..., description="Item ID"),
    db: AsyncSession = Depends(get_db),
) -> list[ReviewAggregateResponse]:
    """
    Get aggregate review scores by source for an item.

    Returns sources like RT_CRITICS, RT_AUDIENCE, NYT with scores.
    No full review text (legal-first).
    """
    rows = await get_reviews_for_item(db, item_id)
    return [
        ReviewAggregateResponse(
            source=r.source,
            score=r.score,
            scale=r.scale,
            normalized_score=_normalize_score(r.score, r.scale),
        )
        for r in rows
    ]
