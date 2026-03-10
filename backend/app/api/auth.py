"""
Auth API router — signup, login, Google OAuth, and current-user endpoints.

All endpoints live under ``/api/v1/auth/``.
"""

from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.clients import google_oauth
from app.clients.redis import get_redis_client
from app.core.security import create_access_token
from app.db.models import User
from app.db.session import get_db
from app.hooks import event_bus
from app.schemas.auth import (
    GoogleStartResponse,
    LoginRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth import authenticate_user, create_user, find_or_create_oauth_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

OAUTH_STATE_TTL = 600  # 10 minutes


# -- Email/password -----------------------------------------------------------


@router.post("/signup", response_model=TokenResponse, status_code=201)
async def signup(body: SignupRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Create a new email/password account and return a JWT."""
    try:
        user = await create_user(db, body.email, body.password)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered") from None

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Authenticate with email/password and return a JWT."""
    user = await authenticate_user(db, body.email, body.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(user.id)})
    await event_bus.emit("on_user_logged_in", user_id=str(user.id), method="email")
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Return the currently authenticated user's info."""
    return UserResponse.model_validate(current_user)


# -- Google OAuth -------------------------------------------------------------


@router.get("/google/start", response_model=GoogleStartResponse)
async def google_start() -> GoogleStartResponse:
    """Generate a state token and return the Google OAuth consent URL."""
    state = secrets.token_urlsafe(32)

    redis = get_redis_client()
    if redis is not None:
        await redis.setex(f"oauth_state:{state}", OAUTH_STATE_TTL, "1")

    url = google_oauth.build_authorization_url(state)
    return GoogleStartResponse(authorization_url=url)


@router.get("/google/callback", response_model=TokenResponse)
async def google_callback(
    code: str = Query(default=None),
    state: str = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Handle Google OAuth callback — exchange code, create/link user, return JWT."""
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")
    if not state:
        raise HTTPException(status_code=400, detail="Missing state parameter")

    redis = get_redis_client()
    if redis is not None:
        stored = await redis.get(f"oauth_state:{state}")
        if stored is None:
            raise HTTPException(status_code=400, detail="Invalid or expired state")
        await redis.delete(f"oauth_state:{state}")

    token_data = await google_oauth.exchange_code_for_tokens(code)

    id_token = token_data.get("id_token")
    if not id_token:
        raise HTTPException(status_code=400, detail="No id_token in Google response")

    user_info = google_oauth.extract_user_info_from_id_token(id_token)
    google_email = user_info.get("email")
    google_sub = user_info.get("sub")
    if not google_email or not google_sub:
        raise HTTPException(status_code=400, detail="Could not extract user info from Google")

    user = await find_or_create_oauth_user(
        db,
        provider="google",
        provider_account_id=google_sub,
        email=google_email,
        tokens_metadata={
            "id_token_claims": {k: user_info[k] for k in ("sub", "email") if k in user_info}
        },
    )

    jwt_token = create_access_token({"sub": str(user.id)})
    await event_bus.emit("on_user_logged_in", user_id=str(user.id), method="google")
    return TokenResponse(access_token=jwt_token)
