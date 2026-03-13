"""Profile API — GET, PATCH, POST for onboarding."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.profile import ProfileCreate, ProfileResponse, ProfileUpdate
from app.services.profile import create_profile, get_profile_response, update_profile

router = APIRouter(prefix="/api/v1/profiles", tags=["profiles"])


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
        raise HTTPException(
            status_code=400,
            detail="You must accept data processing to continue",
        )
    try:
        return await create_profile(db, current_user, body)
    except ValueError as e:
        if "already exists" in str(e):
            raise HTTPException(status_code=409, detail="Profile already exists") from e
        raise


@router.patch("/me", response_model=ProfileResponse)
async def patch_me(
    body: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    """Update profile. Creates one if missing (upsert)."""
    return await update_profile(db, current_user, body)
