"""
Availability service for Stage 5.3: Where to watch.

Fetches availability for an item in a region, with optional
preferred-provider ranking.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ItemAvailability


async def get_availability_for_item(
    db: AsyncSession,
    item_id: int,
    region: str,
    preferred_providers: list[str] | None = None,
) -> list[ItemAvailability]:
    """
    Get availability for an item in a region.

    Filters by region. If preferred_providers is given, those providers
    are ranked first (still filtered by region).
    """
    stmt = select(ItemAvailability).where(
        ItemAvailability.item_id == item_id,
        ItemAvailability.region == region,
    )
    result = await db.execute(stmt)
    rows = list(result.scalars().all())

    if not preferred_providers:
        return rows

    # Rank: preferred first, then others
    preferred_set = {p.strip().lower() for p in preferred_providers if p.strip()}
    preferred_list: list[ItemAvailability] = []
    other_list: list[ItemAvailability] = []
    for row in rows:
        if row.provider.lower() in preferred_set:
            preferred_list.append(row)
        else:
            other_list.append(row)
    return preferred_list + other_list
