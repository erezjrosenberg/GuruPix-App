"""
Seed ingestion service for Stage 5.2.

Parses seed files from data/seed/, validates against canonical schema,
inserts into DB, and stores raw payload. Used by admin-only POST /ingest/items.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Item, ItemAvailability, ItemReviewsAgg
from app.schemas.items import ItemCreate, ItemType


def _get_seed_dir() -> Path:
    """Return path to data/seed directory (project root relative)."""
    # backend/app/services/ingestion.py -> 4 parents up = project root
    return Path(__file__).resolve().parent.parent.parent.parent / "data" / "seed"


def parse_seed_items(path: Path | None = None) -> list[dict[str, Any]]:
    """
    Read items from JSON seed file.

    Returns list of raw dicts. Path defaults to data/seed/items.json.
    Raises FileNotFoundError or json.JSONDecodeError on failure.
    """
    if path is None:
        path = _get_seed_dir() / "items.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Seed file must contain a JSON array")
    return data


def normalize_to_canonical(raw: dict[str, Any]) -> ItemCreate:
    """
    Map raw seed dict to canonical ItemCreate schema.

    Accepts common variations: "overview" -> synopsis, "release_date" as string.
    """
    # Normalize type
    raw_type = raw.get("type", "movie")
    if isinstance(raw_type, str):
        raw_type = raw_type.strip().lower()
        if raw_type not in ("movie", "series", "episode"):
            raw_type = "movie"
    item_type = ItemType(raw_type)

    # Normalize release_date (string "YYYY-MM-DD" -> date)
    release_date = raw.get("release_date")
    if isinstance(release_date, str):
        try:
            release_date = date.fromisoformat(release_date)
        except ValueError:
            release_date = None
    elif not isinstance(release_date, date):
        release_date = None

    # Map overview -> synopsis if present
    synopsis = raw.get("synopsis") or raw.get("overview")

    return ItemCreate(
        type=item_type,
        title=raw.get("title", ""),
        synopsis=synopsis,
        genres=raw.get("genres"),
        cast=raw.get("cast"),
        crew=raw.get("crew"),
        runtime=raw.get("runtime"),
        release_date=release_date,
        language=raw.get("language"),
        metadata=raw.get("metadata"),
    )


async def ingest_items(
    db: AsyncSession,
    items: list[ItemCreate],
    raw_payloads: list[dict[str, Any]] | None = None,
) -> list[int]:
    """
    Insert items into DB, storing raw payload in metadata.

    Returns list of inserted item IDs. raw_payloads[i] is stored with items[i];
    if not provided, no raw_payload is stored.
    """
    item_ids: list[int] = []
    for i, item in enumerate(items):
        raw = raw_payloads[i] if raw_payloads and i < len(raw_payloads) else None
        metadata: dict[str, Any] | None = None
        if raw is not None:
            metadata = {"raw_payload": raw}

        orm_item = Item(
            type=item.type.value,
            title=item.title,
            synopsis=item.synopsis,
            genres=item.genres,
            cast=item.cast,
            crew=item.crew,
            runtime=item.runtime,
            release_date=item.release_date,
            language=item.language,
            metadata_=metadata,
        )
        db.add(orm_item)
        await db.flush()  # get id
        item_ids.append(orm_item.id)
    await db.commit()
    return item_ids


def parse_seed_availability(path: Path | None = None) -> list[dict[str, Any]]:
    """
    Read availability from JSON seed file.

    Each record must have item_index (0-based), provider, region, url, availability_type.
    """
    if path is None:
        path = _get_seed_dir() / "item_availability.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Availability seed must be a JSON array")
    return data


async def ingest_availability(
    db: AsyncSession,
    item_ids: list[int],
    availability_records: list[dict[str, Any]],
) -> int:
    """
    Insert availability records. Uses item_index to map to item_ids.

    Returns count of inserted records.
    """
    count = 0
    for rec in availability_records:
        idx = rec.get("item_index")
        if idx is None or not isinstance(idx, int) or idx < 0 or idx >= len(item_ids):
            continue
        item_id = item_ids[idx]
        av = ItemAvailability(
            item_id=item_id,
            provider=str(rec.get("provider", "")),
            region=str(rec.get("region", "")),
            url=rec.get("url"),
            availability_type=str(rec.get("availability_type", "stream")),
        )
        db.add(av)
        count += 1
    await db.commit()
    return count


def parse_seed_reviews(path: Path | None = None) -> list[dict[str, Any]]:
    """Read review aggregates from JSON seed file."""
    if path is None:
        path = _get_seed_dir() / "item_reviews_agg.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Reviews seed must be a JSON array")
    return data


async def ingest_reviews(
    db: AsyncSession,
    item_ids: list[int],
    review_records: list[dict[str, Any]],
) -> int:
    """Insert review aggregates. Uses item_index to map to item_ids."""
    count = 0
    for rec in review_records:
        idx = rec.get("item_index")
        if idx is None or not isinstance(idx, int) or idx < 0 or idx >= len(item_ids):
            continue
        item_id = item_ids[idx]
        rev = ItemReviewsAgg(
            item_id=item_id,
            source=str(rec.get("source", "")),
            score=float(rec.get("score", 0)),
            scale=float(rec.get("scale", 100)),
        )
        db.add(rev)
        count += 1
    await db.commit()
    return count
