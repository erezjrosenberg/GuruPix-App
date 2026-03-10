"""
Integration tests for Stage 2: Database and Alembic migrations.

These tests require a running Postgres (e.g. docker compose up -d in infra/).
They verify:
1. alembic upgrade head runs from an empty DB (downgrade base then upgrade head).
2. All tables exist and accept insert/select (smoke per table).

Run with: pytest tests/integration/test_db_migrations.py -v
"""

from __future__ import annotations

import uuid
from typing import Any

import app.db.models  # noqa: F401
import pytest
from alembic import command
from alembic.config import Config
from app.core.config import Settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# Skip all tests in this module if Postgres is not reachable (e.g. docker compose not up).
def _postgres_available() -> bool:
    try:
        settings = Settings()
        engine = create_engine(settings.get_sync_database_url())
        with engine.connect():
            return True
    except Exception:
        return False


def _get_alembic_config() -> Config:
    """Build Alembic config with sync DB URL from settings (for current process)."""
    settings = Settings()
    sync_url = settings.get_sync_database_url()
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", sync_url)
    return config


def _make_engine_and_session():
    """Create sync engine and session factory from settings."""
    settings = Settings()
    sync_url = settings.get_sync_database_url()
    engine = create_engine(sync_url)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, session_factory


@pytest.fixture(scope="module")
def require_postgres():
    """Skip the whole module if Postgres is not available."""
    if not _postgres_available():
        pytest.skip("Postgres not available. Start with: cd infra && docker compose up -d")


@pytest.fixture(scope="module")
def alembic_config(require_postgres: None) -> Config:
    """Alembic config with test DB URL (from env / .env)."""
    return _get_alembic_config()


@pytest.fixture(scope="module")
def db_engine_and_session(require_postgres: None):
    """Sync engine and session factory; used for insert/select smoke tests."""
    return _make_engine_and_session()


def test_alembic_upgrade_head_from_empty_db(alembic_config: Config) -> None:
    """
    Run downgrade base then upgrade head to simulate migrating an empty DB.

    This proves that the initial migration applies cleanly from scratch.
    We first ensure we're at head, then downgrade to base (empty), then upgrade again.
    """
    # Ensure we're at head so there is something to downgrade.
    command.upgrade(alembic_config, "head")
    # Downgrade to base (drops all tables).
    command.downgrade(alembic_config, "base")
    # Apply all migrations from empty state.
    command.upgrade(alembic_config, "head")


def test_alembic_upgrade_idempotent(alembic_config: Config) -> None:
    """Running upgrade head again (already at head) should not fail."""
    command.upgrade(alembic_config, "head")


def test_smoke_users(db_engine_and_session: tuple[Any, Any]) -> None:
    """Insert and select a user."""
    _, session_factory = db_engine_and_session
    user_id = uuid.uuid4()
    with session_factory() as session:
        user = app.db.models.User(id=user_id, email="smoke@example.com")
        session.add(user)
        session.commit()
        session.refresh(user)
    with session_factory() as session:
        row = session.get(app.db.models.User, user_id)
        assert row is not None
        assert row.email == "smoke@example.com"
    with session_factory() as session:
        session.delete(session.get(app.db.models.User, user_id))
        session.commit()


def test_smoke_oauth_accounts(db_engine_and_session: tuple[Any, Any]) -> None:
    """Insert and select an oauth_account (requires a user)."""
    _, session_factory = db_engine_and_session
    user_id = uuid.uuid4()
    oauth_id = uuid.uuid4()
    with session_factory() as session:
        session.add(app.db.models.User(id=user_id, email="oauth-smoke@example.com"))
        session.add(
            app.db.models.OAuthAccount(
                id=oauth_id,
                user_id=user_id,
                provider="google",
                provider_account_id="google-123",
            )
        )
        session.commit()
    with session_factory() as session:
        row = session.get(app.db.models.OAuthAccount, oauth_id)
        assert row is not None
        assert row.provider == "google"
    with session_factory() as session:
        session.delete(session.get(app.db.models.OAuthAccount, oauth_id))
        session.delete(session.get(app.db.models.User, user_id))
        session.commit()


def test_smoke_profiles(db_engine_and_session: tuple[Any, Any]) -> None:
    """Insert and select a profile (requires a user)."""
    _, session_factory = db_engine_and_session
    user_id = uuid.uuid4()
    with session_factory() as session:
        user = app.db.models.User(id=user_id, email="profile-smoke@example.com")
        session.add(user)
        session.flush()  # ensure user is inserted before profile (FK)
        session.add(
            app.db.models.Profile(
                user_id=user_id,
                preferences={"genres": ["comedy"]},
                region="US",
            )
        )
        session.commit()
    with session_factory() as session:
        row = session.get(app.db.models.Profile, user_id)
        assert row is not None
        assert row.region == "US"
    with session_factory() as session:
        session.delete(session.get(app.db.models.Profile, user_id))
        session.delete(session.get(app.db.models.User, user_id))
        session.commit()


def test_smoke_items(db_engine_and_session: tuple[Any, Any]) -> None:
    """Insert and select an item."""
    _, session_factory = db_engine_and_session
    with session_factory() as session:
        item = app.db.models.Item(
            type="movie",
            title="Smoke Test Movie",
            synopsis="A test.",
            genres=["Comedy"],
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        item_id = item.id
    with session_factory() as session:
        row = session.get(app.db.models.Item, item_id)
        assert row is not None
        assert row.title == "Smoke Test Movie"
    with session_factory() as session:
        session.delete(session.get(app.db.models.Item, item_id))
        session.commit()


def test_smoke_item_availability(db_engine_and_session: tuple[Any, Any]) -> None:
    """Insert and select item_availability (requires an item)."""
    _, session_factory = db_engine_and_session
    with session_factory() as session:
        item = app.db.models.Item(type="movie", title="Avail Smoke")
        session.add(item)
        session.commit()
        session.refresh(item)
        item_id = item.id
        av = app.db.models.ItemAvailability(
            item_id=item_id,
            provider="Netflix",
            region="US",
            url="https://example.com",
            availability_type="stream",
        )
        session.add(av)
        session.commit()
        session.refresh(av)
        av_id = av.id
    with session_factory() as session:
        row = session.get(app.db.models.ItemAvailability, av_id)
        assert row is not None
        assert row.provider == "Netflix"
    with session_factory() as session:
        # Delete child before parent so CASCADE does not remove the child first.
        session.delete(session.get(app.db.models.ItemAvailability, av_id))
        session.flush()
        session.delete(session.get(app.db.models.Item, item_id))
        session.commit()


def test_smoke_item_reviews_agg(db_engine_and_session: tuple[Any, Any]) -> None:
    """Insert and select item_reviews_agg (requires an item)."""
    _, session_factory = db_engine_and_session
    with session_factory() as session:
        item = app.db.models.Item(type="movie", title="Review Smoke")
        session.add(item)
        session.commit()
        session.refresh(item)
        item_id = item.id
        rev = app.db.models.ItemReviewsAgg(
            item_id=item_id,
            source="RT_CRITICS",
            score=85.0,
            scale=100.0,
        )
        session.add(rev)
        session.commit()
        session.refresh(rev)
        rev_id = rev.id
    with session_factory() as session:
        row = session.get(app.db.models.ItemReviewsAgg, rev_id)
        assert row is not None
        assert row.source == "RT_CRITICS"
    with session_factory() as session:
        # Delete child before parent so CASCADE does not remove the child first.
        session.delete(session.get(app.db.models.ItemReviewsAgg, rev_id))
        session.flush()
        session.delete(session.get(app.db.models.Item, item_id))
        session.commit()


def test_smoke_contexts(db_engine_and_session: tuple[Any, Any]) -> None:
    """Insert and select a context (requires a user)."""
    _, session_factory = db_engine_and_session
    user_id = uuid.uuid4()
    with session_factory() as session:
        session.add(app.db.models.User(id=user_id, email="context-smoke@example.com"))
        session.commit()
        ctx = app.db.models.Context(
            user_id=user_id, label="Date night", attributes={"mood": "cozy"}
        )
        session.add(ctx)
        session.commit()
        session.refresh(ctx)
        ctx_id = ctx.id
    with session_factory() as session:
        row = session.get(app.db.models.Context, ctx_id)
        assert row is not None
        assert row.label == "Date night"
    with session_factory() as session:
        session.delete(session.get(app.db.models.Context, ctx_id))
        session.delete(session.get(app.db.models.User, user_id))
        session.commit()


def test_smoke_models(db_engine_and_session: tuple[Any, Any]) -> None:
    """Insert and select a model (registry)."""
    _, session_factory = db_engine_and_session
    with session_factory() as session:
        m = app.db.models.Model(
            version="v0.1.0-smoke",
            metrics={"ndcg@10": 0.5},
            status=app.db.models.ModelStatus.candidate,
        )
        session.add(m)
        session.commit()
        session.refresh(m)
        m_id = m.id
    with session_factory() as session:
        row = session.get(app.db.models.Model, m_id)
        assert row is not None
        assert row.version == "v0.1.0-smoke"
    with session_factory() as session:
        session.delete(session.get(app.db.models.Model, m_id))
        session.commit()


def test_smoke_events(db_engine_and_session: tuple[Any, Any]) -> None:
    """Insert and select an event (requires user and item)."""
    _, session_factory = db_engine_and_session
    user_id = uuid.uuid4()
    with session_factory() as session:
        session.add(app.db.models.User(id=user_id, email="event-smoke@example.com"))
        item = app.db.models.Item(type="movie", title="Event Smoke")
        session.add(item)
        session.commit()
        session.refresh(item)
        item_id = item.id
        ev = app.db.models.Event(
            user_id=user_id,
            item_id=item_id,
            type="like",
            session_id="s1",
            request_id="r1",
        )
        session.add(ev)
        session.commit()
        session.refresh(ev)
        ev_id = ev.id
    with session_factory() as session:
        row = session.get(app.db.models.Event, ev_id)
        assert row is not None
        assert row.type == "like"
    with session_factory() as session:
        session.delete(session.get(app.db.models.Event, ev_id))
        session.delete(session.get(app.db.models.Item, item_id))
        session.delete(session.get(app.db.models.User, user_id))
        session.commit()


def test_smoke_context_events(db_engine_and_session: tuple[Any, Any]) -> None:
    """Insert and select a context_event (requires a user)."""
    _, session_factory = db_engine_and_session
    user_id = uuid.uuid4()
    with session_factory() as session:
        session.add(app.db.models.User(id=user_id, email="ctxev-smoke@example.com"))
        session.commit()
        ce = app.db.models.ContextEvent(
            user_id=user_id,
            parsed={"mood": "cozy"},
            retention_opt_in=False,
        )
        session.add(ce)
        session.commit()
        session.refresh(ce)
        ce_id = ce.id
    with session_factory() as session:
        row = session.get(app.db.models.ContextEvent, ce_id)
        assert row is not None
        assert row.parsed == {"mood": "cozy"}
    with session_factory() as session:
        session.delete(session.get(app.db.models.ContextEvent, ce_id))
        session.delete(session.get(app.db.models.User, user_id))
        session.commit()
