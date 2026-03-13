"""Events API — record user feedback (like, dislike, etc.) to Postgres."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.events import EventCreate, EventResponse
from app.services.events import record_event

logger = logging.getLogger("gurupix.events")
router = APIRouter(prefix="/api/v1/events", tags=["events"])


@router.post("", response_model=EventResponse, status_code=201)
async def create_event(
    body: EventCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EventResponse:
    """Record user feedback (like, dislike, watch_complete, skip). Persists to Postgres."""
    session_id = getattr(request.state, "session_id", None)
    request_id = getattr(request.state, "request_id", None)
    try:
        event = await record_event(
            db,
            current_user,
            body.item_id,
            body.type,
            session_id=session_id,
            request_id=request_id,
            context_id=body.context_id,
            metadata=body.metadata,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except IntegrityError as e:
        await db.rollback()
        logger.warning("Event create FK violation: %s", e)
        raise HTTPException(
            status_code=404,
            detail="Item or context not found. Ensure item_id exists in catalog.",
        ) from e
    logger.info(
        "Event recorded",
        extra={"user_id": str(current_user.id), "item_id": body.item_id, "type": body.type},
    )
    return EventResponse(
        id=event.id,
        user_id=str(event.user_id),
        item_id=event.item_id,
        type=event.type,
        timestamp=event.timestamp.isoformat(),
    )
