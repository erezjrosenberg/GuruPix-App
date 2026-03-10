"""Unit tests for Google OAuth endpoints and client — all Google calls are mocked."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.clients.google_oauth import build_authorization_url, extract_user_info_from_id_token
from httpx import ASGITransport, AsyncClient

# -- google_oauth client helpers ----------------------------------------------


def test_build_authorization_url_includes_state() -> None:
    url = build_authorization_url("test-state-abc")
    assert "state=test-state-abc" in url
    assert "accounts.google.com" in url
    assert "response_type=code" in url


def test_extract_user_info_from_id_token() -> None:
    """Create a minimal JWT to decode (no signature verification)."""
    import jwt as pyjwt

    payload = {"sub": "google-123", "email": "user@gmail.com", "email_verified": True}
    token = pyjwt.encode(payload, "not-verified", algorithm="HS256")
    info = extract_user_info_from_id_token(token)
    assert info["sub"] == "google-123"
    assert info["email"] == "user@gmail.com"


# -- /auth/google/start -------------------------------------------------------


@pytest.mark.asyncio
async def test_google_start_returns_url_with_state() -> None:
    from app.main import create_app

    app = create_app()
    transport = ASGITransport(app=app)

    mock_redis = AsyncMock()
    with patch("app.api.auth.get_redis_client", return_value=mock_redis):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/auth/google/start")

    assert resp.status_code == 200
    body = resp.json()
    assert "authorization_url" in body
    assert "accounts.google.com" in body["authorization_url"]
    assert "state=" in body["authorization_url"]
    mock_redis.setex.assert_awaited_once()


# -- /auth/google/callback ----------------------------------------------------


def _mock_google_tokens(email: str = "user@gmail.com", sub: str = "g-sub-1") -> dict:
    """Build a fake Google token response."""
    import jwt as pyjwt

    id_token = pyjwt.encode({"sub": sub, "email": email}, "test", algorithm="HS256")
    return {"id_token": id_token, "access_token": "fake-access"}


@pytest.mark.asyncio
async def test_google_callback_missing_code_returns_400() -> None:
    from app.main import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/auth/google/callback?state=abc")
    assert resp.status_code == 400
    assert "code" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_google_callback_missing_state_returns_400() -> None:
    from app.main import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/auth/google/callback?code=abc")
    assert resp.status_code == 400
    assert "state" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_google_callback_invalid_state_returns_400() -> None:
    from app.main import create_app

    app = create_app()
    transport = ASGITransport(app=app)

    mock_redis = AsyncMock()
    mock_redis.get.return_value = None  # state not found

    with patch("app.api.auth.get_redis_client", return_value=mock_redis):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/auth/google/callback?code=abc&state=bad-state")

    assert resp.status_code == 400
    assert "state" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_google_callback_success_returns_jwt() -> None:
    from app.main import create_app

    app = create_app()
    transport = ASGITransport(app=app)

    mock_redis = AsyncMock()
    mock_redis.get.return_value = b"1"  # valid state

    user_mock = MagicMock()
    user_mock.id = uuid.uuid4()

    tokens = _mock_google_tokens()

    with (
        patch("app.api.auth.get_redis_client", return_value=mock_redis),
        patch(
            "app.api.auth.google_oauth.exchange_code_for_tokens",
            new_callable=AsyncMock,
            return_value=tokens,
        ),
        patch(
            "app.api.auth.find_or_create_oauth_user", new_callable=AsyncMock, return_value=user_mock
        ),
    ):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/auth/google/callback?code=auth-code&state=valid")

    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
