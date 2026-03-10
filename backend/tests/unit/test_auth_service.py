"""Unit tests for app.services.auth — with mocked async DB session."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.db.models import User
from app.services.auth import (
    authenticate_user,
    create_user,
    find_or_create_oauth_user,
    get_user_by_email,
    get_user_by_id,
)


def _make_user(
    email: str = "test@example.com",
    password_hash: str | None = None,
) -> MagicMock:
    """Create a MagicMock that behaves like a User ORM instance."""
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.email = email
    user.password_hash = password_hash
    user.created_at = datetime.now(UTC)
    return user


def _mock_session(scalar_result: object = None) -> AsyncMock:
    """Return an AsyncMock session whose execute().scalar_one_or_none returns *scalar_result*."""
    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = scalar_result
    session.execute.return_value = result_mock
    session.add = MagicMock()
    return session


# -- get_user_by_email --------------------------------------------------------


@pytest.mark.asyncio
async def test_get_user_by_email_found() -> None:
    user = _make_user()
    db = _mock_session(user)
    result = await get_user_by_email(db, "test@example.com")
    assert result is user


@pytest.mark.asyncio
async def test_get_user_by_email_not_found() -> None:
    db = _mock_session(None)
    result = await get_user_by_email(db, "nope@example.com")
    assert result is None


# -- get_user_by_id -----------------------------------------------------------


@pytest.mark.asyncio
async def test_get_user_by_id_found() -> None:
    user = _make_user()
    db = _mock_session(user)
    result = await get_user_by_id(db, user.id)
    assert result is user


# -- create_user --------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_user_hashes_password() -> None:
    db = _mock_session()
    with patch("app.services.auth.hash_password", return_value="$bcrypt$hashed"):
        user = await create_user(db, "new@example.com", "password123")

    assert user.email == "new@example.com"
    assert user.password_hash == "$bcrypt$hashed"
    db.add.assert_called_once()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once()


# -- authenticate_user --------------------------------------------------------


@pytest.mark.asyncio
async def test_authenticate_user_success() -> None:
    user = _make_user(password_hash="$bcrypt$hashed")
    db = _mock_session(user)
    with patch("app.services.auth.verify_password", return_value=True):
        result = await authenticate_user(db, "test@example.com", "correct")
    assert result is user


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password() -> None:
    user = _make_user(password_hash="$bcrypt$hashed")
    db = _mock_session(user)
    with patch("app.services.auth.verify_password", return_value=False):
        result = await authenticate_user(db, "test@example.com", "wrong")
    assert result is None


@pytest.mark.asyncio
async def test_authenticate_user_no_such_email() -> None:
    db = _mock_session(None)
    result = await authenticate_user(db, "nobody@example.com", "any")
    assert result is None


@pytest.mark.asyncio
async def test_authenticate_user_oauth_only_no_password() -> None:
    """OAuth-only users have no password_hash — auth must return None."""
    user = _make_user(password_hash=None)
    db = _mock_session(user)
    result = await authenticate_user(db, "test@example.com", "any")
    assert result is None


# -- find_or_create_oauth_user ------------------------------------------------


@pytest.mark.asyncio
async def test_find_or_create_oauth_user_existing_link() -> None:
    """If the OAuth link already exists, return the linked user."""
    user = _make_user()
    link = MagicMock()
    link.user_id = user.id

    db = AsyncMock()
    db.add = MagicMock()
    link_result = MagicMock()
    link_result.scalar_one_or_none.return_value = link
    user_result = MagicMock()
    user_result.scalar_one_or_none.return_value = user
    db.execute.side_effect = [link_result, user_result]

    result = await find_or_create_oauth_user(db, "google", "g-123", "test@example.com")
    assert result is user


@pytest.mark.asyncio
async def test_find_or_create_oauth_user_new_user() -> None:
    """No existing link and no existing email — creates brand-new user."""
    db = AsyncMock()
    db.add = MagicMock()
    no_link = MagicMock()
    no_link.scalar_one_or_none.return_value = None
    no_user = MagicMock()
    no_user.scalar_one_or_none.return_value = None
    db.execute.side_effect = [no_link, no_user]

    result = await find_or_create_oauth_user(db, "google", "g-new", "brand@new.com")
    assert result.email == "brand@new.com"
    assert db.add.call_count == 2  # user + oauth_account
    db.commit.assert_awaited_once()
