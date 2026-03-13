"""
Unit tests for Stage 5.1: Canonical item schema validation.

Verifies that ItemCreate and ItemResponse correctly validate and normalize
item data (title trim, genre normalization, runtime constraints).
"""

from __future__ import annotations

from datetime import date

import pytest
from app.schemas.items import ItemCreate, ItemResponse, ItemType
from pydantic import ValidationError

# -- Valid fixtures -----------------------------------------------------------


def test_item_create_valid_movie() -> None:
    """A minimal valid movie item passes validation."""
    item = ItemCreate(
        type=ItemType.movie,
        title="The Shawshank Redemption",
        synopsis="Two imprisoned men bond over a number of years.",
        genres=["Drama"],
        runtime=142,
        release_date=date(1994, 9, 23),
    )
    assert item.type == ItemType.movie
    assert item.title == "The Shawshank Redemption"
    assert item.genres == ["drama"]  # normalized to lowercase
    assert item.runtime == 142


def test_item_create_valid_series() -> None:
    """A valid series item passes validation."""
    item = ItemCreate(
        type=ItemType.series,
        title="Breaking Bad",
        synopsis="A chemistry teacher turns to cooking meth.",
        genres=["Crime", "Drama", "Thriller"],
    )
    assert item.type == ItemType.series
    assert item.genres == ["crime", "drama", "thriller"]


def test_item_create_valid_episode() -> None:
    """A valid episode item passes validation."""
    item = ItemCreate(
        type=ItemType.episode,
        title="Pilot",
        synopsis="The first episode.",
        genres=["Drama"],
    )
    assert item.type == ItemType.episode


def test_item_create_title_trimmed() -> None:
    """Leading and trailing whitespace in title is trimmed."""
    item = ItemCreate(type=ItemType.movie, title="  Inception  ")
    assert item.title == "Inception"


def test_item_create_genres_normalized() -> None:
    """Genres are lowercased and deduplicated."""
    item = ItemCreate(
        type=ItemType.movie,
        title="Test",
        genres=["Comedy", "comedy", "COMEDY", "Drama"],
    )
    assert item.genres == ["comedy", "drama"]


def test_item_create_genres_empty_strings_filtered() -> None:
    """Empty genre strings are filtered out."""
    item = ItemCreate(
        type=ItemType.movie,
        title="Test",
        genres=["Comedy", "", "  ", "Drama"],
    )
    assert item.genres == ["comedy", "drama"]


def test_item_create_runtime_zero_allowed() -> None:
    """Runtime of 0 is allowed (e.g. short film)."""
    item = ItemCreate(type=ItemType.movie, title="Short", runtime=0)
    assert item.runtime == 0


def test_item_create_optional_fields_none() -> None:
    """All optional fields can be None."""
    item = ItemCreate(type=ItemType.movie, title="Minimal")
    assert item.synopsis is None
    assert item.genres is None
    assert item.cast is None
    assert item.crew is None
    assert item.runtime is None
    assert item.release_date is None
    assert item.language is None
    assert item.metadata is None


# -- Invalid data raises ValidationError --------------------------------------


def test_item_create_empty_title_raises() -> None:
    """Empty title raises ValidationError."""
    with pytest.raises(ValidationError):
        ItemCreate(type=ItemType.movie, title="")


def test_item_create_whitespace_only_title_raises() -> None:
    """Whitespace-only title raises ValidationError."""
    with pytest.raises(ValidationError):
        ItemCreate(type=ItemType.movie, title="   ")


def test_item_create_negative_runtime_raises() -> None:
    """Negative runtime raises ValidationError."""
    with pytest.raises(ValidationError):
        ItemCreate(type=ItemType.movie, title="Bad", runtime=-1)


def test_item_create_invalid_type_raises() -> None:
    """Invalid item type raises ValidationError."""
    with pytest.raises(ValidationError):
        ItemCreate(type="invalid", title="Test")  # type: ignore[arg-type]


def test_item_create_title_too_long_raises() -> None:
    """Title exceeding max length raises ValidationError."""
    with pytest.raises(ValidationError):
        ItemCreate(type=ItemType.movie, title="x" * 501)


# -- ItemResponse -------------------------------------------------------------


def test_item_response_from_attributes() -> None:
    """ItemResponse can be built from ORM-like object with metadata_."""

    class FakeItem:
        id = 1
        type = "movie"
        title = "Test"
        synopsis = None
        genres = ["comedy"]
        cast = None
        crew = None
        runtime = 90
        release_date = date(2020, 1, 1)
        language = "en"
        metadata_ = {"extra": "value"}

    resp = ItemResponse.model_validate(FakeItem())
    assert resp.id == 1
    assert resp.title == "Test"
    assert resp.metadata == {"extra": "value"}


def test_item_response_strips_raw_payload() -> None:
    """ItemResponse excludes raw_payload from metadata in API output."""

    class FakeItem:
        id = 1
        type = "movie"
        title = "Test"
        synopsis = None
        genres = None
        cast = None
        crew = None
        runtime = None
        release_date = None
        language = None
        metadata_ = {"raw_payload": {"secret": "data"}, "public": "ok"}

    resp = ItemResponse.model_validate(FakeItem())
    assert "raw_payload" not in (resp.metadata or {})
    assert resp.metadata == {"public": "ok"}
