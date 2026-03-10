"""
Integration tests for Stage 4.2: Google OAuth (mocked Google, real DB).

Require running Postgres and Redis (docker compose up -d in infra/).
Google HTTP calls are mocked — we verify user/oauth_account creation in DB.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import jwt as pyjwt
import pytest
from httpx import ASGITransport, AsyncClient


def _pg_available() -> bool:
    try:
        import psycopg2

        conn = psycopg2.connect(
            "postgresql://gurupix:gurupix_local@localhost:5432/gurupix"
        )
        conn.close()
        return True
    except Exception:
        return False


@pytest.fixture(scope="module")
def require_pg() -> None:
    if not _pg_available():
        pytest.skip("Postgres not available — start with: cd infra && docker compose up -d")


@pytest.fixture()
async def client(require_pg: None) -> AsyncClient:  # type: ignore[misc]
    import app.clients.redis as redis_mod
    from app.db.session import reset_engine
    from app.main import create_app

    reset_engine()
    test_app = create_app()
    transport = ASGITransport(app=test_app)
    await redis_mod.init_redis()
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c  # type: ignore[misc]
    await redis_mod.close_redis()
    reset_engine()


def _unique_email() -> str:
    return f"oauth-{uuid.uuid4().hex[:10]}@gmail.com"


def _fake_google_tokens(email: str, sub: str) -> dict:
    id_token = pyjwt.encode({"sub": sub, "email": email}, "test", algorithm="HS256")
    return {"id_token": id_token, "access_token": "fake-access"}


async def _do_google_callback(
    client: AsyncClient,
    email: str,
    google_sub: str,
) -> AsyncClient:
    """Simulate a full Google OAuth callback with mocked Google + valid state."""
    tokens = _fake_google_tokens(email, google_sub)
    mock_redis = AsyncMock()
    mock_redis.get.return_value = b"1"  # valid state

    with (
        patch("app.api.auth.get_redis_client", return_value=mock_redis),
        patch(
            "app.api.auth.google_oauth.exchange_code_for_tokens",
            new_callable=AsyncMock,
            return_value=tokens,
        ),
    ):
        resp = await client.get(
            "/api/v1/auth/google/callback?code=auth-code&state=valid-state"
        )
    return resp  # type: ignore[return-value]


# -- OAuth creates new user ---------------------------------------------------


@pytest.mark.asyncio
async def test_oauth_callback_creates_new_user(client: AsyncClient) -> None:
    email = _unique_email()
    resp = await _do_google_callback(client, email, f"g-{uuid.uuid4().hex[:8]}")

    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


# -- Same Google account returns same user (no duplicate) ---------------------


@pytest.mark.asyncio
async def test_oauth_same_google_account_no_duplicate(client: AsyncClient) -> None:
    email = _unique_email()
    google_sub = f"g-{uuid.uuid4().hex[:8]}"

    resp1 = await _do_google_callback(client, email, google_sub)
    assert resp1.status_code == 200
    token1 = resp1.json()["access_token"]

    resp2 = await _do_google_callback(client, email, google_sub)
    assert resp2.status_code == 200
    token2 = resp2.json()["access_token"]

    from app.core.security import decode_access_token

    uid1 = decode_access_token(token1)["sub"]
    uid2 = decode_access_token(token2)["sub"]
    assert uid1 == uid2


# -- OAuth user can access /auth/me -------------------------------------------


@pytest.mark.asyncio
async def test_oauth_user_can_access_me(client: AsyncClient) -> None:
    email = _unique_email()
    resp = await _do_google_callback(client, email, f"g-{uuid.uuid4().hex[:8]}")
    assert resp.status_code == 200
    token = resp.json()["access_token"]

    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == email


# -- Existing email/password user can link Google -----------------------------


@pytest.mark.asyncio
async def test_existing_email_user_links_google(client: AsyncClient) -> None:
    email = _unique_email()

    signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "StrongPass1!"},
    )
    assert signup.status_code == 201
    email_token = signup.json()["access_token"]
    from app.core.security import decode_access_token

    email_uid = decode_access_token(email_token)["sub"]

    oauth_resp = await _do_google_callback(client, email, f"g-{uuid.uuid4().hex[:8]}")
    assert oauth_resp.status_code == 200
    oauth_token = oauth_resp.json()["access_token"]
    oauth_uid = decode_access_token(oauth_token)["sub"]

    assert email_uid == oauth_uid
