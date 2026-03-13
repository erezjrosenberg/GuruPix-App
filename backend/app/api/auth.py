"""
Auth API router — signup, login, Google OAuth, and current-user endpoints.

All endpoints live under ``/api/v1/auth/``.
"""

from __future__ import annotations

import logging
import secrets

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.clients import google_oauth
from app.core.config import Settings
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
logger = logging.getLogger("gurupix.auth")

OAUTH_STATE_TTL = 600  # 10 minutes


async def _issue_token(user: User, method: str) -> TokenResponse:
    """Create JWT, emit login hook, return token response."""
    token = create_access_token({"sub": str(user.id)})
    await event_bus.emit("on_user_logged_in", user_id=str(user.id), method=method)
    return TokenResponse(access_token=token)


@router.post("/signup", response_model=TokenResponse, status_code=201)
async def signup(body: SignupRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Create a new email/password account and return a JWT."""
    try:
        user = await create_user(db, body.email, body.password)
    except IntegrityError:
        await db.rollback()
        logger.warning("Signup rejected: email already registered")
        raise HTTPException(status_code=409, detail="Email already registered") from None
    logger.info("User signed up", extra={"user_id": str(user.id)})
    return await _issue_token(user, "signup")


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Authenticate with email/password and return a JWT."""
    user = await authenticate_user(db, body.email, body.password)
    if user is None:
        logger.warning("Login failed: invalid credentials")
        raise HTTPException(status_code=401, detail="Invalid email or password")
    logger.info("User logged in", extra={"user_id": str(user.id), "method": "email"})
    return await _issue_token(user, "email")


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Return the currently authenticated user's info."""
    settings = Settings()
    admin_emails = settings.get_admin_emails_set()
    is_admin = current_user.email.lower() in admin_emails
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        created_at=current_user.created_at,
        is_admin=is_admin,
    )


# -- Google OAuth -------------------------------------------------------------


@router.get("/google/start", response_model=GoogleStartResponse)
async def google_start() -> GoogleStartResponse:
    """Generate a state token and return the Google OAuth consent URL."""
    redis = get_redis_client()
    if redis is None:
        logger.warning("OAuth start failed: Redis unavailable")
        raise HTTPException(
            status_code=503, detail="OAuth unavailable — state store is not reachable"
        )

    state = secrets.token_urlsafe(32)
    logger.info("OAuth flow started", extra={"provider": "google"})
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
        logger.warning("OAuth callback: missing authorization code")
        raise HTTPException(status_code=400, detail="Missing authorization code")
    if not state:
        logger.warning("OAuth callback: missing state parameter")
        raise HTTPException(status_code=400, detail="Missing state parameter")

    redis = get_redis_client()
    if redis is None:
        logger.warning("OAuth callback failed: Redis unavailable")
        raise HTTPException(
            status_code=503, detail="OAuth unavailable — state store is not reachable"
        )
    stored = await redis.get(f"oauth_state:{state}")
    if stored is None:
        logger.warning("OAuth callback: invalid or expired state")
        raise HTTPException(status_code=400, detail="Invalid or expired state")
    await redis.delete(f"oauth_state:{state}")

    token_data = await google_oauth.exchange_code_for_tokens(code)

    id_token = token_data.get("id_token")
    if not id_token:
        logger.warning("OAuth callback: no id_token in Google response")
        raise HTTPException(status_code=400, detail="No id_token in Google response")

    user_info = google_oauth.extract_user_info_from_id_token(id_token)
    google_email = user_info.get("email")
    google_sub = user_info.get("sub")
    if not google_email or not google_sub:
        logger.warning("OAuth callback: could not extract user info from id_token")
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
    logger.info("User logged in via OAuth", extra={"user_id": str(user.id), "provider": "google"})
    return await _issue_token(user, "google")
