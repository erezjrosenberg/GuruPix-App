"""
Google OAuth client — token exchange and user-info extraction.

Encapsulates all HTTP calls to Google so the auth router stays thin.
In production, these functions call Google's real endpoints; in tests,
they are mocked.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

import httpx
import jwt as pyjwt

from app.core.config import Settings

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"

_settings = Settings()


def build_authorization_url(state: str) -> str:
    """Return the full Google OAuth consent screen URL."""
    params = {
        "client_id": _settings.google_client_id,
        "redirect_uri": _settings.get_oauth_redirect_uri(),
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "state": state,
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def exchange_code_for_tokens(code: str) -> dict[str, Any]:
    """Exchange an authorization code for Google tokens.

    Returns the raw JSON response which includes ``id_token``,
    ``access_token``, and optionally ``refresh_token``.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": _settings.google_client_id,
                "client_secret": _settings.google_client_secret,
                "redirect_uri": _settings.get_oauth_redirect_uri(),
                "grant_type": "authorization_code",
            },
        )
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
        return data


def extract_user_info_from_id_token(id_token: str) -> dict[str, Any]:
    """Decode Google's id_token WITHOUT verifying the signature.

    In production you should verify against Google's JWKS. For MVP we
    rely on the fact that we received this token directly from Google
    over HTTPS in ``exchange_code_for_tokens``. The decoded payload
    contains ``sub``, ``email``, ``email_verified``, ``name``, etc.
    """
    return pyjwt.decode(id_token, options={"verify_signature": False})
