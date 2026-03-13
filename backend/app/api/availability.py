"""
Availability API for Stage 5.3: Where to watch.

GET /availability returns providers for an item in a region.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.availability import AvailabilityResponse
from app.services.availability import get_availability_for_item

router = APIRouter(prefix="/api/v1", tags=["availability"])


@router.get("/availability", response_model=list[AvailabilityResponse])
async def get_availability(
    item_id: int = Query(..., description="Item ID"),
    region: str = Query(..., description="Region code (e.g. US)"),
    preferred_providers: str | None = Query(
        default=None,
        description="Comma-separated provider names to rank first",
    ),
    db: AsyncSession = Depends(get_db),
) -> list[AvailabilityResponse]:
    """
    Get where to watch an item in a region.

    Returns providers filtered by region. If preferred_providers is given,
    those providers appear first (when available in the region).
    """
    prefs = (
        [p.strip() for p in preferred_providers.split(",") if p.strip()]
        if preferred_providers
        else None
    )
    rows = await get_availability_for_item(db, item_id, region, preferred_providers=prefs)
    return [
        AvailabilityResponse(
            provider=r.provider,
            region=r.region,
            url=r.url,
            availability_type=r.availability_type,
        )
        for r in rows
    ]
