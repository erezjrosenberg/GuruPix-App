"""
FastAPI dependencies for request-scoped data (e.g. current authenticated user).

``get_current_user`` is injected into any route that requires authentication.
It reads the ``Authorization: Bearer <token>`` header, decodes the JWT, looks
up the user in the database, and raises 401 if anything is invalid.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.security import decode_access_token
from app.db.models import User
from app.db.session import get_db
from app.services.auth import get_user_by_id

logger = logging.getLogger("gurupix.auth")


def _extract_bearer_token(request: Request) -> str:
    """Pull the token string from the Authorization header or raise 401."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    return auth_header[len("Bearer ") :]


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI dependency that returns the authenticated User or raises 401."""
    token = _extract_bearer_token(request)
    try:
        payload = decode_access_token(token)
    except Exception:
        logger.warning("Auth failed: invalid or expired token")
        raise HTTPException(status_code=401, detail="Invalid or expired token") from None

    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(status_code=401, detail="Token missing subject")

    try:
        user_id = uuid.UUID(sub)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token subject") from None

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    request.state.user_id = str(user.id)
    return user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Require the current user to be an admin (email in ADMIN_EMAILS).

    Use for admin-only endpoints like POST /ingest/items.
    """
    settings = Settings()
    admin_emails = settings.get_admin_emails_set()
    if not admin_emails:
        raise HTTPException(
            status_code=503,
            detail="Admin access not configured (ADMIN_EMAILS empty)",
        )
    if current_user.email.lower() not in admin_emails:
        logger.warning("Admin access denied", extra={"user_id": str(current_user.id)})
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
