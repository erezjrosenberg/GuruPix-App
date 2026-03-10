"""Unit tests for AuthMiddleware — observability layer (does not block requests)."""

from __future__ import annotations

from unittest.mock import patch

from app.core.security import create_access_token
from app.middleware.auth import AuthMiddleware
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

TEST_SECRET = "test-middleware-secret-key-must-be-at-least-32-bytes-long"
TEST_ALG = "HS256"


def _app_with_auth_middleware() -> FastAPI:
    app = FastAPI()
    app.add_middleware(AuthMiddleware)

    @app.get("/test")
    def _test(request: Request) -> dict:
        return {"user_id": getattr(request.state, "user_id", None)}

    return app


def test_valid_token_sets_user_id() -> None:
    """A valid Bearer token should populate request.state.user_id."""
    token = create_access_token(
        {"sub": "abc-123"},
        secret_key=TEST_SECRET,
        algorithm=TEST_ALG,
    )
    app = _app_with_auth_middleware()
    client = TestClient(app)

    with patch("app.middleware.auth.decode_access_token") as mock_decode:
        mock_decode.return_value = {"sub": "abc-123"}
        resp = client.get("/test", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 200
    assert resp.json()["user_id"] == "abc-123"


def test_missing_auth_header_leaves_user_id_none() -> None:
    """Without an Authorization header, user_id is None — request is NOT blocked."""
    app = _app_with_auth_middleware()
    client = TestClient(app)
    resp = client.get("/test")
    assert resp.status_code == 200
    assert resp.json()["user_id"] is None


def test_invalid_token_leaves_user_id_none() -> None:
    """A bad token is silently ignored — user_id stays None."""
    app = _app_with_auth_middleware()
    client = TestClient(app)
    resp = client.get("/test", headers={"Authorization": "Bearer bad.token.here"})
    assert resp.status_code == 200
    assert resp.json()["user_id"] is None


def test_non_bearer_scheme_ignored() -> None:
    """Authorization headers that don't start with 'Bearer ' are ignored."""
    app = _app_with_auth_middleware()
    client = TestClient(app)
    resp = client.get("/test", headers={"Authorization": "Basic dXNlcjpwYXNz"})
    assert resp.status_code == 200
    assert resp.json()["user_id"] is None
