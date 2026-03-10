"""
Password hashing and JWT token utilities for GuruPix auth.

Uses bcrypt for password hashing and PyJWT for token encoding/decoding.
All auth-related cryptographic operations are centralised here so that the
rest of the codebase never handles raw passwords or token bytes directly.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import Settings

_settings = Settings()


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of *plain*."""
    pwd_bytes = plain.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches the bcrypt *hashed* value."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
    *,
    secret_key: str | None = None,
    algorithm: str | None = None,
) -> str:
    """Encode a JWT containing *data* with an expiry claim.

    Parameters
    ----------
    data:
        Payload dict -- typically ``{"sub": "<user-id>"}``.
    expires_delta:
        Custom lifetime; defaults to ``settings.jwt_expire_minutes``.
    secret_key / algorithm:
        Override settings (useful in tests).
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=_settings.jwt_expire_minutes))
    to_encode["exp"] = expire
    to_encode["iat"] = now
    return jwt.encode(
        to_encode,
        secret_key or _settings.secret_key,
        algorithm=algorithm or _settings.jwt_algorithm,
    )


def decode_access_token(
    token: str,
    *,
    secret_key: str | None = None,
    algorithm: str | None = None,
) -> dict:
    """Decode and validate a JWT, returning the payload dict.

    Raises ``jwt.ExpiredSignatureError`` if the token is expired and
    ``jwt.InvalidTokenError`` for any other validation failure.
    """
    return jwt.decode(
        token,
        secret_key or _settings.secret_key,
        algorithms=[algorithm or _settings.jwt_algorithm],
    )
