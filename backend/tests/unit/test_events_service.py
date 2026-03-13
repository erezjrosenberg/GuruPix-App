"""Unit tests for app.services.events — record_event."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.db.models import Event, User
from app.schemas.events import VALID_EVENT_TYPES
from app.services.events import record_event


def _make_user() -> MagicMock:
    user = MagicMock(spec=User)
    user.id = uuid.UUID("123e4567-e89b-12d3-a456-426614174000")
    return user


@pytest.mark.asyncio
async def test_record_event_success() -> None:
    """record_event creates and returns event."""
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    user = _make_user()
    event = await record_event(db, user, item_id=1, event_type="like")

    assert event is not None
    db.add.assert_called_once()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once()
    added = db.add.call_args[0][0]
    assert isinstance(added, Event)
    assert added.item_id == 1
    assert added.type == "like"
    assert added.user_id == user.id


@pytest.mark.asyncio
async def test_record_event_invalid_type_raises() -> None:
    """record_event raises ValueError for invalid event type."""
    db = AsyncMock()
    user = _make_user()

    with pytest.raises(ValueError, match="Invalid event type"):
        await record_event(db, user, item_id=1, event_type="invalid")


@pytest.mark.asyncio
async def test_record_event_all_valid_types() -> None:
    """All VALID_EVENT_TYPES are accepted."""
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    user = _make_user()

    for t in VALID_EVENT_TYPES:
        event = await record_event(db, user, item_id=1, event_type=t)
        assert event.type == t
