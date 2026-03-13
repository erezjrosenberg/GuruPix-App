"""
Review aggregates service for Stage 5.4.

Fetches aggregate scores by source for an item (legal-first: scores only).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ItemReviewsAgg


async def get_reviews_for_item(db: AsyncSession, item_id: int) -> list[ItemReviewsAgg]:
    """Get all review aggregates for an item."""
    stmt = select(ItemReviewsAgg).where(ItemReviewsAgg.item_id == item_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())
