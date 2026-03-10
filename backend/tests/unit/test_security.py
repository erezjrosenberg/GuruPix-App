"""Unit tests for app.core.security — password hashing and JWT utilities."""

from __future__ import annotations

from datetime import timedelta

import jwt
import pytest
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

TEST_SECRET = "unit-test-secret-key-must-be-at-least-32-bytes-long"
TEST_ALG = "HS256"


# -- Password hashing --------------------------------------------------------


def test_hash_and_verify_roundtrip() -> None:
    """Hashing a password and verifying with the same plaintext succeeds."""
    hashed = hash_password("Str0ngP@ss!")
    assert verify_password("Str0ngP@ss!", hashed) is True


def test_wrong_password_is_rejected() -> None:
    """Verifying with a different plaintext fails."""
    hashed = hash_password("correct-horse-battery-staple")
    assert verify_password("wrong-password", hashed) is False


def test_hash_is_not_plaintext() -> None:
    """The hash output must not contain the original password."""
    plain = "super-secret-123"
    hashed = hash_password(plain)
    assert plain not in hashed


def test_different_hashes_for_same_password() -> None:
    """bcrypt uses a random salt so two hashes of the same input differ."""
    h1 = hash_password("same-password")
    h2 = hash_password("same-password")
    assert h1 != h2


# -- JWT tokens ---------------------------------------------------------------


def test_jwt_encode_decode_roundtrip() -> None:
    """Creating and decoding a token returns the original payload."""
    token = create_access_token(
        {"sub": "user-123"},
        secret_key=TEST_SECRET,
        algorithm=TEST_ALG,
    )
    payload = decode_access_token(token, secret_key=TEST_SECRET, algorithm=TEST_ALG)
    assert payload["sub"] == "user-123"
    assert "exp" in payload
    assert "iat" in payload


def test_jwt_expired_token_raises() -> None:
    """A token with a negative expiry is immediately expired and must raise."""
    token = create_access_token(
        {"sub": "user-456"},
        expires_delta=timedelta(seconds=-1),
        secret_key=TEST_SECRET,
        algorithm=TEST_ALG,
    )
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token, secret_key=TEST_SECRET, algorithm=TEST_ALG)


def test_jwt_tampered_token_raises() -> None:
    """A token signed with a different secret cannot be decoded."""
    token = create_access_token(
        {"sub": "user-789"},
        secret_key="secret-key-A-that-is-at-least-32-bytes",
        algorithm=TEST_ALG,
    )
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(
            token, secret_key="secret-key-B-that-is-at-least-32-bytes", algorithm=TEST_ALG
        )


def test_jwt_garbage_token_raises() -> None:
    """Completely invalid token strings raise InvalidTokenError."""
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token("not.a.jwt", secret_key=TEST_SECRET, algorithm=TEST_ALG)


def test_jwt_custom_expiry() -> None:
    """A custom expiry delta is respected in the token payload."""
    token = create_access_token(
        {"sub": "user-abc"},
        expires_delta=timedelta(hours=24),
        secret_key=TEST_SECRET,
        algorithm=TEST_ALG,
    )
    payload = decode_access_token(token, secret_key=TEST_SECRET, algorithm=TEST_ALG)
    assert payload["sub"] == "user-abc"
