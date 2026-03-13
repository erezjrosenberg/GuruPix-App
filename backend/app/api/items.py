"""
Items API for Stage 5.3: Catalog listing.

GET /items returns a paginated list of catalog items.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Item
from app.db.session import get_db
from app.schemas.items import ItemResponse

router = APIRouter(prefix="/api/v1", tags=["items"])


@router.get("/items", response_model=list[ItemResponse])
async def list_items(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[ItemResponse]:
    """
    List catalog items (paginated).

    No auth required. Used by catalog/browse UI.
    """
    stmt = select(Item).order_by(Item.id).offset(offset).limit(limit)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [ItemResponse.model_validate(r) for r in rows]
