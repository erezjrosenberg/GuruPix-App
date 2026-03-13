"""Integration tests for contexts API."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.integration.conftest import unique_email


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    """Sign up and return auth headers."""
    email = unique_email("context")
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "StrongPass1!"},
    )
    assert resp.status_code == 201
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_context_success(client: AsyncClient, auth_headers: dict) -> None:
    """POST /contexts creates context."""
    resp = await client.post(
        "/api/v1/contexts",
        headers=auth_headers,
        json={"label": "Date night", "attributes": {"mood": "cozy"}},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["label"] == "Date night"
    assert data["attributes"] == {"mood": "cozy"}
    assert "id" in data
    assert "user_id" in data


@pytest.mark.asyncio
async def test_list_contexts(client: AsyncClient, auth_headers: dict) -> None:
    """GET /contexts returns user's contexts."""
    # Create two contexts
    await client.post(
        "/api/v1/contexts",
        headers=auth_headers,
        json={"label": "Cozy", "attributes": None},
    )
    await client.post(
        "/api/v1/contexts",
        headers=auth_headers,
        json={"label": "Action", "attributes": {"intensity": "high"}},
    )
    resp = await client.get("/api/v1/contexts", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2
    labels = [c["label"] for c in data]
    assert "Cozy" in labels
    assert "Action" in labels


@pytest.mark.asyncio
async def test_delete_context(client: AsyncClient, auth_headers: dict) -> None:
    """DELETE /contexts/:id removes context."""
    create = await client.post(
        "/api/v1/contexts",
        headers=auth_headers,
        json={"label": "To delete", "attributes": None},
    )
    assert create.status_code == 201
    ctx_id = create.json()["id"]

    resp = await client.delete(f"/api/v1/contexts/{ctx_id}", headers=auth_headers)
    assert resp.status_code == 204

    list_resp = await client.get("/api/v1/contexts", headers=auth_headers)
    ids = [c["id"] for c in list_resp.json()]
    assert ctx_id not in ids


@pytest.mark.asyncio
async def test_delete_context_not_found_returns_404(
    client: AsyncClient, auth_headers: dict
) -> None:
    """DELETE /contexts/999999 returns 404."""
    resp = await client.delete(
        "/api/v1/contexts/999999",
        headers=auth_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_contexts_require_auth(client: AsyncClient) -> None:
    """GET /contexts without token returns 401."""
    resp = await client.get("/api/v1/contexts")
    assert resp.status_code == 401
