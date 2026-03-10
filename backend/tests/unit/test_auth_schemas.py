"""Unit tests for auth Pydantic schemas — input validation + output shape."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from app.schemas.auth import (
    GoogleStartResponse,
    LoginRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
)
from pydantic import ValidationError

# -- SignupRequest ------------------------------------------------------------


def test_signup_valid_input() -> None:
    req = SignupRequest(email="user@example.com", password="StrongP@ss1")
    assert req.email == "user@example.com"
    assert req.password == "StrongP@ss1"


def test_signup_password_too_short() -> None:
    with pytest.raises(ValidationError) as exc_info:
        SignupRequest(email="user@example.com", password="short")
    assert "password" in str(exc_info.value).lower()


def test_signup_password_too_long() -> None:
    with pytest.raises(ValidationError):
        SignupRequest(email="user@example.com", password="x" * 129)


def test_signup_invalid_email() -> None:
    with pytest.raises(ValidationError) as exc_info:
        SignupRequest(email="not-an-email", password="LongEnough1!")
    assert "email" in str(exc_info.value).lower()


def test_signup_missing_fields() -> None:
    with pytest.raises(ValidationError):
        SignupRequest()  # type: ignore[call-arg]


# -- LoginRequest -------------------------------------------------------------


def test_login_valid_input() -> None:
    req = LoginRequest(email="user@example.com", password="any")
    assert req.email == "user@example.com"


def test_login_empty_password_rejected() -> None:
    with pytest.raises(ValidationError):
        LoginRequest(email="user@example.com", password="")


# -- TokenResponse ------------------------------------------------------------


def test_token_response_shape() -> None:
    resp = TokenResponse(access_token="abc.def.ghi")
    assert resp.access_token == "abc.def.ghi"
    assert resp.token_type == "bearer"


# -- UserResponse -------------------------------------------------------------


def test_user_response_shape() -> None:
    now = datetime.now(UTC)
    uid = uuid.uuid4()
    resp = UserResponse(id=uid, email="a@b.com", created_at=now)
    assert resp.id == uid
    assert resp.email == "a@b.com"
    assert resp.created_at == now


# -- GoogleStartResponse ------------------------------------------------------


def test_google_start_response_shape() -> None:
    resp = GoogleStartResponse(authorization_url="https://accounts.google.com/o/oauth2/v2/auth?...")
    assert resp.authorization_url.startswith("https://accounts.google.com")
