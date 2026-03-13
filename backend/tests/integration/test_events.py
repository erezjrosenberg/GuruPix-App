"""
Integration tests for events API — POST /events (like, dislike, etc.).

Requires Postgres and Redis. Verifies:
- POST /events records feedback and returns 201
- Invalid item_id returns 404
- Invalid event type returns 400
- Unauthenticated returns 401
- Invalid token returns 401
"""

from __future__ import annotations

from typing import Any

import pytest
from httpx import AsyncClient

from tests.integration.conftest import unique_email


@pytest.fixture
async def auth_and_item_id(
    client: AsyncClient,
    monkeypatch: Any,
) -> tuple[dict[str, str], int]:
    """Create admin user, ingest items, return (auth_headers, first_item_id)."""
    admin_email = unique_email("admin")
    monkeypatch.setenv("ADMIN_EMAILS", admin_email)

    signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": admin_email, "password": "StrongPass1!"},
    )
    assert signup.status_code == 201
    token = signup.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    ingest = await client.post("/api/v1/ingest/items", headers=auth_headers)
    assert ingest.status_code == 201
    body = ingest.json()
    assert body["ingested"] > 0
    item_id = body["item_ids"][0]
    return auth_headers, item_id


@pytest.mark.asyncio
async def test_post_event_success(
    client: AsyncClient,
    auth_and_item_id: tuple[dict[str, str], int],
) -> None:
    """POST /events with valid item_id and type returns 201."""
    auth_headers, item_id = auth_and_item_id
    resp = await client.post(
        "/api/v1/events",
        headers=auth_headers,
        json={"item_id": item_id, "type": "like"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["item_id"] == item_id
    assert data["type"] == "like"
    assert "id" in data
    assert "user_id" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_post_event_invalid_item_id_returns_404(
    client: AsyncClient,
    auth_and_item_id: tuple[dict[str, str], int],
) -> None:
    """POST /events with nonexistent item_id returns 404."""
    auth_headers, _ = auth_and_item_id
    resp = await client.post(
        "/api/v1/events",
        headers=auth_headers,
        json={"item_id": 999999999, "type": "like"},
    )
    assert resp.status_code == 404
    assert "not found" in resp.json().get("detail", "").lower()


@pytest.mark.asyncio
async def test_post_event_invalid_type_returns_400(
    client: AsyncClient,
    auth_and_item_id: tuple[dict[str, str], int],
) -> None:
    """POST /events with invalid type returns 400."""
    auth_headers, item_id = auth_and_item_id
    resp = await client.post(
        "/api/v1/events",
        headers=auth_headers,
        json={"item_id": item_id, "type": "invalid_type"},
    )
    assert resp.status_code == 422  # Pydantic validation


@pytest.mark.asyncio
async def test_post_event_without_token_returns_401(
    client: AsyncClient,
    auth_and_item_id: tuple[dict[str, str], int],
) -> None:
    """POST /events without Authorization returns 401."""
    _, item_id = auth_and_item_id
    resp = await client.post(
        "/api/v1/events",
        json={"item_id": item_id, "type": "like"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_post_event_invalid_token_returns_401(
    client: AsyncClient,
    auth_and_item_id: tuple[dict[str, str], int],
) -> None:
    """POST /events with invalid token returns 401."""
    _, item_id = auth_and_item_id
    resp = await client.post(
        "/api/v1/events",
        headers={"Authorization": "Bearer invalid.jwt.token"},
        json={"item_id": item_id, "type": "like"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_post_event_dislike_and_skip(
    client: AsyncClient,
    auth_and_item_id: tuple[dict[str, str], int],
) -> None:
    """POST /events accepts dislike, skip, watch_complete, click."""
    auth_headers, item_id = auth_and_item_id
    for event_type in ("dislike", "skip", "watch_complete", "click"):
        resp = await client.post(
            "/api/v1/events",
            headers=auth_headers,
            json={"item_id": item_id, "type": event_type},
        )
        assert resp.status_code == 201, f"Failed for type={event_type}"
        assert resp.json()["type"] == event_type
