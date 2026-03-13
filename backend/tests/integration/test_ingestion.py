"""
Integration tests for Stage 5.2: Admin ingest endpoint.

Requires Postgres and Redis. Verifies:
- Admin user can POST /ingest/items and get expected count
- Non-admin gets 403
- Unauthenticated gets 401
- on_item_ingested hook is emitted
"""

from __future__ import annotations

from typing import Any

import pytest
from app.hooks import event_bus
from httpx import AsyncClient

from tests.integration.conftest import unique_email


@pytest.fixture
def admin_email(monkeypatch: Any) -> str:
    """Set ADMIN_EMAILS so we can create an admin user for tests."""
    email = unique_email("admin")
    monkeypatch.setenv("ADMIN_EMAILS", email)
    return email


@pytest.mark.asyncio
async def test_ingest_without_token_returns_401(client: AsyncClient) -> None:
    """Unauthenticated request to /ingest/items returns 401."""
    resp = await client.post("/api/v1/ingest/items")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_ingest_non_admin_returns_403(
    client: AsyncClient,
    admin_email: str,
) -> None:
    """Non-admin user gets 403 when calling /ingest/items."""
    # Create a regular user (not in ADMIN_EMAILS)
    signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": unique_email(), "password": "StrongPass1!"},
    )
    assert signup.status_code == 201
    token = signup.json()["access_token"]

    resp = await client.post(
        "/api/v1/ingest/items",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_ingest_admin_succeeds_and_returns_count(
    client: AsyncClient,
    admin_email: str,
) -> None:
    """Admin user can ingest items and gets expected count."""
    signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": admin_email, "password": "StrongPass1!"},
    )
    assert signup.status_code == 201
    token = signup.json()["access_token"]

    resp = await client.post(
        "/api/v1/ingest/items",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "ingested" in body
    assert "item_ids" in body
    assert body["ingested"] == len(body["item_ids"])
    # Seed file has 5 items
    assert body["ingested"] >= 5


@pytest.mark.asyncio
async def test_ingest_emits_on_item_ingested_hook(
    client: AsyncClient,
    admin_email: str,
) -> None:
    """Ingest emits on_item_ingested for each item."""
    calls: list[dict[str, Any]] = []

    def handler(**kw: Any) -> None:
        calls.append(kw)

    event_bus.subscribe("on_item_ingested", handler)

    signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": admin_email, "password": "StrongPass1!"},
    )
    assert signup.status_code == 201
    token = signup.json()["access_token"]

    try:
        resp = await client.post(
            "/api/v1/ingest/items",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        ingested = resp.json()["ingested"]
        assert len(calls) == ingested
        for c in calls:
            assert "item_id" in c
    finally:
        event_bus.clear()
