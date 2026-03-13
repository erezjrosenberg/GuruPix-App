"""Pydantic schemas for user feedback events."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

VALID_EVENT_TYPES = frozenset({"like", "dislike", "watch_complete", "skip", "click"})


class EventCreate(BaseModel):
    """Create a user feedback event (like, dislike, watch_complete, skip)."""

    item_id: int = Field(..., description="Catalog item ID")
    type: str = Field(..., description="Event type: like, dislike, watch_complete, skip, click")
    context_id: int | None = Field(None, description="Optional context preset ID")
    metadata: dict | None = Field(None, description="Extra metadata")

    @field_validator("type")
    @classmethod
    def type_must_be_valid(cls, v: str) -> str:
        if v not in VALID_EVENT_TYPES:
            raise ValueError(f"Invalid event type: {v!r}. Must be one of: {sorted(VALID_EVENT_TYPES)}")
        return v


class EventResponse(BaseModel):
    """Event as returned by API."""

    id: int
    user_id: str
    item_id: int
    type: str
    timestamp: str
