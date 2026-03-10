"""
Integration tests for Stage 4.1: email/password authentication.

Require running Postgres and Redis (docker compose up -d in infra/).
Tests verify signup, login, protected /auth/me, duplicate handling,
and the on_user_logged_in hook — all against the real database.
"""

from __future__ import annotations

from typing import Any

import pytest
from app.hooks import event_bus
from httpx import AsyncClient

from tests.integration.conftest import unique_email

# -- Signup -------------------------------------------------------------------


@pytest.mark.asyncio
async def test_signup_creates_user_and_returns_jwt(client: AsyncClient) -> None:
    email = unique_email()
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "StrongPass1!"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_signup_duplicate_email_returns_409(client: AsyncClient) -> None:
    email = unique_email()
    resp1 = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "StrongPass1!"},
    )
    assert resp1.status_code == 201

    resp2 = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "AnotherPass1!"},
    )
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_signup_invalid_email_returns_422(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": "not-an-email", "password": "StrongPass1!"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_signup_short_password_returns_422(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": unique_email(), "password": "short"},
    )
    assert resp.status_code == 422


# -- Login --------------------------------------------------------------------


@pytest.mark.asyncio
async def test_login_correct_credentials(client: AsyncClient) -> None:
    email = unique_email()
    signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "StrongPass1!"},
    )
    assert signup.status_code == 201

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPass1!"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(client: AsyncClient) -> None:
    email = unique_email()
    signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "StrongPass1!"},
    )
    assert signup.status_code == 201

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "WrongPassword!"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_email_returns_401(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "anything"},
    )
    assert resp.status_code == 401


# -- /auth/me (protected endpoint) -------------------------------------------


@pytest.mark.asyncio
async def test_me_with_valid_token(client: AsyncClient) -> None:
    email = unique_email()
    signup_resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "StrongPass1!"},
    )
    assert signup_resp.status_code == 201
    token = signup_resp.json()["access_token"]

    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == email
    assert "id" in body
    assert "created_at" in body


@pytest.mark.asyncio
async def test_me_without_token_returns_401(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_with_invalid_token_returns_401(client: AsyncClient) -> None:
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer bad.token.here"},
    )
    assert resp.status_code == 401


# -- on_user_logged_in hook ---------------------------------------------------


@pytest.mark.asyncio
async def test_signup_fires_on_user_logged_in_hook(client: AsyncClient) -> None:
    calls: list[dict[str, Any]] = []

    def handler(**kw: Any) -> None:
        calls.append(kw)

    event_bus.subscribe("on_user_logged_in", handler)
    try:
        email = unique_email()
        resp = await client.post(
            "/api/v1/auth/signup",
            json={"email": email, "password": "StrongPass1!"},
        )
        assert resp.status_code == 201

        assert len(calls) == 1
        assert calls[0]["method"] == "signup"
        assert "user_id" in calls[0]
    finally:
        event_bus.clear()


@pytest.mark.asyncio
async def test_login_fires_on_user_logged_in_hook(client: AsyncClient) -> None:
    calls: list[dict[str, Any]] = []

    def handler(**kw: Any) -> None:
        calls.append(kw)

    event_bus.subscribe("on_user_logged_in", handler)
    try:
        email = unique_email()
        signup = await client.post(
            "/api/v1/auth/signup",
            json={"email": email, "password": "StrongPass1!"},
        )
        assert signup.status_code == 201

        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "StrongPass1!"},
        )
        assert login_resp.status_code == 200

        # signup fires once, login fires once => at least 2 total
        assert len(calls) >= 2
        assert calls[-1]["method"] == "email"
        assert "user_id" in calls[-1]
    finally:
        event_bus.clear()


# -- Regression: email/password still works (Stage 4.2 requirement) -----------


@pytest.mark.asyncio
async def test_email_password_regression_after_oauth(client: AsyncClient) -> None:
    """Full email/password cycle: signup -> login -> /me -- must still work."""
    email = unique_email()

    signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "Regr3ss1on!"},
    )
    assert signup.status_code == 201
    token_from_signup = signup.json()["access_token"]

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Regr3ss1on!"},
    )
    assert login.status_code == 200
    token_from_login = login.json()["access_token"]

    me1 = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token_from_signup}"},
    )
    assert me1.status_code == 200
    assert me1.json()["email"] == email

    me2 = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token_from_login}"},
    )
    assert me2.status_code == 200
    assert me2.json()["email"] == email
