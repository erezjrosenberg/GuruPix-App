"""
Integration tests for Stage 5.4: Review aggregates endpoint.

Requires Postgres. Verifies GET /reviews/aggregate returns expected
sources after seeding items and reviews.
"""

from __future__ import annotations

from typing import Any

import pytest
from httpx import AsyncClient

from tests.integration.conftest import unique_email


@pytest.fixture
def admin_email(monkeypatch: Any) -> str:
    """Set ADMIN_EMAILS for ingest."""
    email = unique_email("admin")
    monkeypatch.setenv("ADMIN_EMAILS", email)
    return email


@pytest.mark.asyncio
async def test_reviews_aggregate_returns_sources_for_seeded_item(
    client: AsyncClient,
    admin_email: str,
) -> None:
    """After ingest, GET /reviews/aggregate returns sources for an item."""
    signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": admin_email, "password": "StrongPass1!"},
    )
    assert signup.status_code == 201
    token = signup.json()["access_token"]

    ingest_resp = await client.post(
        "/api/v1/ingest/items",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert ingest_resp.status_code == 201
    item_ids = ingest_resp.json()["item_ids"]
    assert len(item_ids) >= 1

    item_id = item_ids[0]
    resp = await client.get(
        "/api/v1/reviews/aggregate",
        params={"item_id": item_id},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) >= 1
    for r in body:
        assert "source" in r
        assert "score" in r
        assert "scale" in r
        assert r["source"] in ("RT_CRITICS", "RT_AUDIENCE")


@pytest.mark.asyncio
async def test_reviews_aggregate_empty_for_unknown_item(client: AsyncClient) -> None:
    """GET /reviews/aggregate for non-existent item returns empty list."""
    resp = await client.get(
        "/api/v1/reviews/aggregate",
        params={"item_id": 999999},
    )
    assert resp.status_code == 200
    assert resp.json() == []
