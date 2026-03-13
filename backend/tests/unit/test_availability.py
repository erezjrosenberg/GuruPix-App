"""
Unit tests for Stage 5.3: Availability filtering logic.

Verifies preferred-provider ranking (region filtering is in SQL).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from app.db.models import ItemAvailability
from app.services.availability import get_availability_for_item


def _make_row(provider: str, region: str = "US") -> ItemAvailability:
    """Create a mock ItemAvailability row."""
    row = MagicMock(spec=ItemAvailability)
    row.provider = provider
    row.region = region
    row.url = f"https://{provider.lower().replace(' ', '')}.com"
    row.availability_type = "stream"
    return row


@pytest.mark.asyncio
async def test_get_availability_ranks_preferred_first() -> None:
    """When preferred_providers given, those providers appear first."""
    db = AsyncMock()
    rows = [
        _make_row("Amazon"),
        _make_row("Netflix"),
        _make_row("HBO Max"),
    ]

    async def mock_execute(stmt):
        result = MagicMock()
        result.scalars.return_value.all.return_value = rows
        return result

    db.execute = mock_execute

    result = await get_availability_for_item(
        db, item_id=1, region="US", preferred_providers=["Netflix", "HBO Max"]
    )
    assert len(result) == 3
    assert result[0].provider == "Netflix"
    assert result[1].provider == "HBO Max"
    assert result[2].provider == "Amazon"


@pytest.mark.asyncio
async def test_get_availability_no_preferred_returns_original_order() -> None:
    """Without preferred_providers, order is unchanged."""
    db = AsyncMock()
    rows = [_make_row("HBO Max"), _make_row("Netflix")]

    async def mock_execute(stmt):
        result = MagicMock()
        result.scalars.return_value.all.return_value = rows
        return result

    db.execute = mock_execute

    result = await get_availability_for_item(db, item_id=1, region="US")
    assert [r.provider for r in result] == ["HBO Max", "Netflix"]
