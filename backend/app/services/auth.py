"""
Auth service — business logic for user creation, authentication, and OAuth linking.

All database operations for auth go through this module so that the API layer
stays thin and testable.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.db.models import OAuthAccount, User


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Look up a user by email (case-insensitive)."""
    result = await db.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    """Look up a user by primary key."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, email: str, password: str) -> User:
    """Create a new email/password user.  Caller must handle duplicate-email."""
    user = User(
        email=email.lower(),
        password_hash=hash_password(password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    """Return the user if email+password are correct, else None."""
    user = await get_user_by_email(db, email)
    if user is None or user.password_hash is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def find_or_create_oauth_user(
    db: AsyncSession,
    provider: str,
    provider_account_id: str,
    email: str,
    tokens_metadata: dict | None = None,
) -> User:
    """Find an existing user by OAuth link, or create a new one.

    If a user with the same email already exists (e.g. signed up with
    email/password first), the OAuth account is linked to that user.
    """
    result = await db.execute(
        select(OAuthAccount).where(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_account_id == provider_account_id,
        )
    )
    existing_link = result.scalar_one_or_none()
    if existing_link is not None:
        user = await get_user_by_id(db, existing_link.user_id)
        assert user is not None
        return user

    user = await get_user_by_email(db, email)
    if user is None:
        user = User(email=email.lower())
        db.add(user)
        await db.flush()

    oauth_account = OAuthAccount(
        user_id=user.id,
        provider=provider,
        provider_account_id=provider_account_id,
        email=email.lower(),
        tokens_metadata=tokens_metadata,
    )
    db.add(oauth_account)
    await db.commit()
    await db.refresh(user)
    return user
