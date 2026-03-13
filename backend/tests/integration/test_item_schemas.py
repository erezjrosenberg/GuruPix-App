"""
Integration tests for Stage 5.1: Canonical item schema with real DB.

Verifies that an item validated by ItemCreate can be inserted into the
database and read back with the expected shape.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import app.db.models  # noqa: F401
import pytest
from app.core.config import Settings
from app.schemas.items import ItemCreate, ItemResponse, ItemType
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _postgres_available() -> bool:
    try:
        settings = Settings()
        engine = create_engine(settings.get_sync_database_url())
        with engine.connect():
            return True
    except Exception:
        return False


@pytest.fixture(scope="module")
def require_postgres() -> None:
    if not _postgres_available():
        pytest.skip("Postgres not available. Start with: cd infra && docker compose up -d")


@pytest.fixture(scope="module")
def db_session(require_postgres: None) -> Any:
    settings = Settings()
    engine = create_engine(settings.get_sync_database_url())
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return session_factory


def test_insert_select_canonical_item(db_session: Any) -> None:
    """
    ItemCreate-validated data can be inserted and selected as canonical item.

    This proves the schema and ORM work together for the catalog.
    """
    item_create = ItemCreate(
        type=ItemType.movie,
        title="  Integration Test Movie  ",
        synopsis="A test film for schema validation.",
        genres=["Comedy", "Drama"],
        runtime=95,
        release_date=date(2024, 1, 15),
        language="en",
    )

    # Map ItemCreate to ORM Item
    item = app.db.models.Item(
        type=item_create.type.value,
        title=item_create.title,
        synopsis=item_create.synopsis,
        genres=item_create.genres,
        cast=item_create.cast,
        crew=item_create.crew,
        runtime=item_create.runtime,
        release_date=item_create.release_date,
        language=item_create.language,
        metadata_={"raw_payload": {"source": "test"}},
    )

    with db_session() as session:
        session.add(item)
        session.commit()
        session.refresh(item)
        item_id = item.id

    with db_session() as session:
        row = session.get(app.db.models.Item, item_id)
        assert row is not None
        assert row.title == "Integration Test Movie"  # trimmed
        assert row.genres == ["comedy", "drama"]  # normalized
        assert row.runtime == 95

        # ItemResponse can be built from ORM
        resp = ItemResponse.model_validate(row)
        assert resp.id == item_id
        assert resp.title == "Integration Test Movie"
        assert resp.genres == ["comedy", "drama"]
        assert "raw_payload" not in (resp.metadata or {})

    # Cleanup
    with db_session() as session:
        session.delete(session.get(app.db.models.Item, item_id))
        session.commit()
