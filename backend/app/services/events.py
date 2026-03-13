"""Event service — record user feedback (like, dislike, etc.) to Postgres."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Event, User
from app.schemas.events import VALID_EVENT_TYPES


async def record_event(
    db: AsyncSession,
    user: User,
    item_id: int,
    event_type: str,
    *,
    session_id: str | None = None,
    request_id: str | None = None,
    context_id: int | None = None,
    metadata: dict | None = None,
) -> Event:
    """Record a user feedback event. Persists to Postgres."""
    if event_type not in VALID_EVENT_TYPES:
        raise ValueError(f"Invalid event type: {event_type!r}")
    event = Event(
        user_id=user.id,
        item_id=item_id,
        type=event_type,
        session_id=session_id,
        request_id=request_id,
        context_id=context_id,
        metadata_=metadata,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event
