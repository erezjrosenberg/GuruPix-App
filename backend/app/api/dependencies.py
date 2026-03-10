"""
FastAPI dependencies for request-scoped data (e.g. current authenticated user).

``get_current_user`` is injected into any route that requires authentication.
It reads the ``Authorization: Bearer <token>`` header, decodes the JWT, looks
up the user in the database, and raises 401 if anything is invalid.
"""

from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.models import User
from app.db.session import get_db
from app.services.auth import get_user_by_id


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
