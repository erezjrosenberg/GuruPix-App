"""
Admin-only ingestion API for Stage 5.2.

POST /ingest/items reads seed files, validates, inserts into DB,
and emits on_item_ingested for each item.
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_admin_user
from app.db.models import User
from app.db.session import get_db
from app.hooks import event_bus
from app.schemas.items import ItemCreate
from app.services.ingestion import (
    _get_seed_dir,
    ingest_availability,
    ingest_items,
    ingest_reviews,
    normalize_to_canonical,
    parse_seed_availability,
    parse_seed_items,
    parse_seed_reviews,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ingest", tags=["ingest"])


class IngestItemsResponse(BaseModel):
    """Response for POST /ingest/items."""

    ingested: int = Field(..., description="Number of items ingested")
    item_ids: list[int] = Field(..., description="IDs of ingested items")


@router.post("/items", response_model=IngestItemsResponse, status_code=201)
async def ingest_items_endpoint(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> IngestItemsResponse:
    """
    Ingest items from data/seed/items.json (admin-only).

    Parses the seed file, validates against canonical schema, inserts into DB,
    stores raw payload in metadata, and emits on_item_ingested for each item.
    """
    seed_dir = _get_seed_dir()
    items_path = seed_dir / "items.json"

    if not items_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Seed file not found: {items_path}",
        )

    try:
        raw_list = parse_seed_items(items_path)
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=422, detail=f"Invalid seed file: {e}") from e

    if not raw_list:
        return IngestItemsResponse(ingested=0, item_ids=[])

    # Validate and normalize each item
    canonical_items: list[ItemCreate] = []
    for i, raw in enumerate(raw_list):
        try:
            canonical_items.append(normalize_to_canonical(raw))
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid item at index {i}: {e}",
            ) from e

    # Insert items and emit hooks
    item_ids = await ingest_items(db, canonical_items, raw_payloads=raw_list)

    for item_id in item_ids:
        await event_bus.emit("on_item_ingested", item_id=item_id)

    # Load availability seed if present
    avail_path = seed_dir / "item_availability.json"
    if avail_path.exists():
        try:
            avail_records = parse_seed_availability(avail_path)
            await ingest_availability(db, item_ids, avail_records)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Skipping availability seed: %s", e)

    # Load review aggregates seed if present
    reviews_path = seed_dir / "item_reviews_agg.json"
    if reviews_path.exists():
        try:
            review_records = parse_seed_reviews(reviews_path)
            await ingest_reviews(db, item_ids, review_records)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Skipping reviews seed: %s", e)

    logger.info("Ingested %d items (admin=%s)", len(item_ids), current_user.email)
    return IngestItemsResponse(ingested=len(item_ids), item_ids=item_ids)
