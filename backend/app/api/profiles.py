"""Profile API — GET, PATCH, POST for onboarding."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.profile import ProfileCreate, ProfileResponse, ProfileUpdate
from app.services.profile import create_profile, get_profile_response, update_profile

router = APIRouter(prefix="/api/v1/profiles", tags=["profiles"])
logger = logging.getLogger("gurupix.profiles")


@router.get("/me", response_model=ProfileResponse | None)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse | None:
    """Get current user's profile. Returns None if not yet onboarded."""
    return await get_profile_response(db, current_user)


@router.post("/me", response_model=ProfileResponse, status_code=201)
async def create_me(
    body: ProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    """Create profile (onboarding). Requires consent_data_processing=true."""
    if not body.consent_data_processing:
        logger.warning("Profile create rejected: consent not given")
        raise HTTPException(
            status_code=400,
            detail="You must accept data processing to continue",
        )
    try:
        profile = await create_profile(db, current_user, body)
        logger.info("Profile created", extra={"user_id": str(current_user.id)})
        return profile
    except ValueError as e:
        if "already exists" in str(e):
            raise HTTPException(status_code=409, detail="Profile already exists") from e
        if "data processing" in str(e).lower():
            raise HTTPException(status_code=400, detail=str(e)) from e
        raise


@router.patch("/me", response_model=ProfileResponse)
async def patch_me(
    body: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    """Update profile. Creates one if missing (upsert). When creating, consent_data_processing must be True."""
    try:
        profile = await update_profile(db, current_user, body)
        logger.info("Profile updated", extra={"user_id": str(current_user.id)})
        return profile
    except ValueError as e:
        if "data processing" in str(e).lower():
            logger.warning("Profile patch rejected: consent not given for new profile")
            raise HTTPException(status_code=400, detail=str(e)) from e
        raise
