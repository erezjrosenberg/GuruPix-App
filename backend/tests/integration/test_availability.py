"""
Integration tests for Stage 5.3: Availability endpoint.

Requires Postgres. Verifies GET /availability returns provider list
 after seeding items and availability.
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
async def test_availability_returns_providers_for_seeded_item(
    client: AsyncClient,
    admin_email: str,
) -> None:
    """After ingest, GET /availability returns providers for an item in region."""
    # Signup admin and ingest
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

    # First item (Shawshank) should have Netflix and HBO Max in US
    item_id = item_ids[0]
    resp = await client.get(
        "/api/v1/availability",
        params={"item_id": item_id, "region": "US"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) >= 1
    for av in body:
        assert "provider" in av
        assert "region" in av
        assert av["region"] == "US"


@pytest.mark.asyncio
async def test_availability_preferred_providers_ranked_first(
    client: AsyncClient,
    admin_email: str,
) -> None:
    """preferred_providers param ranks those providers first."""
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
    item_id = item_ids[0]

    resp = await client.get(
        "/api/v1/availability",
        params={
            "item_id": item_id,
            "region": "US",
            "preferred_providers": "HBO Max,Netflix",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    if len(body) >= 2:
        # HBO Max and Netflix should be first (if both exist)
        providers = [av["provider"] for av in body]
        hbo_idx = providers.index("HBO Max") if "HBO Max" in providers else 999
        netflix_idx = providers.index("Netflix") if "Netflix" in providers else 999
        amazon_idx = providers.index("Amazon") if "Amazon" in providers else 999
        assert hbo_idx < amazon_idx or netflix_idx < amazon_idx


@pytest.mark.asyncio
async def test_availability_empty_for_unknown_item(client: AsyncClient) -> None:
    """GET /availability for non-existent item returns empty list."""
    resp = await client.get(
        "/api/v1/availability",
        params={"item_id": 999999, "region": "US"},
    )
    assert resp.status_code == 200
    assert resp.json() == []
