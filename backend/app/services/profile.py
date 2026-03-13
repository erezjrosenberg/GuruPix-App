"""Profile service — get, create, update profiles."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Profile, User
from app.schemas.profile import ProfileCreate, ProfileResponse, ProfileUpdate


def _profile_to_response(profile: Profile, user: User) -> ProfileResponse:
    """Build ProfileResponse from Profile + User."""
    prefs = profile.preferences or {}
    return ProfileResponse(
        user_id=str(profile.user_id),
        display_name=prefs.get("display_name"),
        bio=prefs.get("bio"),
        region=profile.region,
        languages=profile.languages,
        providers=profile.providers,
        preferences=profile.preferences,
        consent=profile.consent,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


async def get_profile(db: AsyncSession, user_id: uuid.UUID) -> Profile | None:
    """Get profile by user_id, or None if not found."""
    result = await db.execute(select(Profile).where(Profile.user_id == user_id))
    return result.scalar_one_or_none()


async def get_profile_response(db: AsyncSession, user: User) -> ProfileResponse | None:
    """Get profile as ProfileResponse, or None if no profile."""
    profile = await get_profile(db, user.id)
    if profile is None:
        return None
    return _profile_to_response(profile, user)


async def create_profile(
    db: AsyncSession,
    user: User,
    data: ProfileCreate,
) -> ProfileResponse:
    """Create profile (onboarding). Fails if profile already exists."""
    existing = await get_profile(db, user.id)
    if existing is not None:
        raise ValueError("Profile already exists")

    prefs = {
        "display_name": data.display_name,
        "bio": data.bio,
    }
    profile = Profile(
        user_id=user.id,
        preferences=prefs,
        region=data.region,
        languages=data.languages,
        providers=data.providers,
        consent={"data_processing": data.consent_data_processing}
        if data.consent_data_processing
        else None,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return _profile_to_response(profile, user)


async def update_profile(
    db: AsyncSession,
    user: User,
    data: ProfileUpdate,
) -> ProfileResponse:
    """Update profile. Creates one if missing (upsert)."""
    profile = await get_profile(db, user.id)
    if profile is None:
        prefs = {"display_name": data.display_name, "bio": data.bio}
        profile = Profile(
            user_id=user.id,
            preferences=prefs,
            region=data.region,
            languages=data.languages,
            providers=data.providers,
        )
        db.add(profile)
    else:
        prefs = dict(profile.preferences or {})
        if data.display_name is not None:
            prefs["display_name"] = data.display_name
        if data.bio is not None:
            prefs["bio"] = data.bio
        profile.preferences = prefs
        if data.region is not None:
            profile.region = data.region
        if data.languages is not None:
            profile.languages = data.languages
        if data.providers is not None:
            profile.providers = data.providers
    await db.commit()
    await db.refresh(profile)
    return _profile_to_response(profile, user)
