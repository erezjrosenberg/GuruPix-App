"""Integration tests for profile API."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.integration.conftest import unique_email


@pytest.fixture
async def auth_headers(client: AsyncClient):
    """Sign up and return auth headers."""
    email = unique_email("profile")
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "password123"},
    )
    assert resp.status_code == 201
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_get_profile_returns_none_for_new_user(client: AsyncClient, auth_headers: dict):
    """New user has no profile."""
    resp = await client.get("/api/v1/profiles/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() is None


@pytest.mark.asyncio
async def test_create_profile_requires_consent(client: AsyncClient, auth_headers: dict):
    """POST without consent_data_processing returns 400."""
    resp = await client.post(
        "/api/v1/profiles/me",
        headers=auth_headers,
        json={
            "display_name": "Test",
            "consent_data_processing": False,
        },
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_create_profile_success(client: AsyncClient, auth_headers: dict):
    """POST with consent creates profile."""
    resp = await client.post(
        "/api/v1/profiles/me",
        headers=auth_headers,
        json={
            "display_name": "Test User",
            "bio": "Love sci-fi",
            "region": "US",
            "consent_data_processing": True,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["display_name"] == "Test User"
    assert data["bio"] == "Love sci-fi"
    assert data["region"] == "US"


@pytest.mark.asyncio
async def test_get_profile_after_create(client: AsyncClient, auth_headers: dict):
    """GET returns profile after create."""
    await client.post(
        "/api/v1/profiles/me",
        headers=auth_headers,
        json={"consent_data_processing": True},
    )
    resp = await client.get("/api/v1/profiles/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() is not None


@pytest.mark.asyncio
async def test_patch_profile_upserts(client: AsyncClient, auth_headers: dict):
    """PATCH creates or updates profile. Creating requires consent."""
    resp = await client.patch(
        "/api/v1/profiles/me",
        headers=auth_headers,
        json={
            "display_name": "Patched",
            "region": "UK",
            "consent_data_processing": True,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["display_name"] == "Patched"
    assert data["region"] == "UK"


@pytest.mark.asyncio
async def test_patch_profile_create_without_consent_returns_400(
    client: AsyncClient, auth_headers: dict
):
    """PATCH creating new profile without consent returns 400."""
    resp = await client.patch(
        "/api/v1/profiles/me",
        headers=auth_headers,
        json={"display_name": "No Consent", "consent_data_processing": False},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_profiles_require_auth(client: AsyncClient):
    """GET /profiles/me without token returns 401."""
    resp = await client.get("/api/v1/profiles/me")
    assert resp.status_code == 401
