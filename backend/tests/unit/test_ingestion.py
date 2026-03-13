"""
Unit tests for Stage 5.2: Ingestion service (parser, normalizer).

Verifies parse_seed_items and normalize_to_canonical correctness
with various raw input shapes.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest
from app.schemas.items import ItemType
from app.services.ingestion import normalize_to_canonical, parse_seed_items

# -- parse_seed_items ---------------------------------------------------------


def test_parse_seed_items_valid_array() -> None:
    """Parse valid JSON array of items."""
    with NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(
            [
                {"type": "movie", "title": "A"},
                {"type": "series", "title": "B"},
            ],
            f,
        )
        path = Path(f.name)
    try:
        result = parse_seed_items(path)
        assert len(result) == 2
        assert result[0]["title"] == "A"
        assert result[1]["title"] == "B"
    finally:
        path.unlink()


def test_parse_seed_items_empty_array() -> None:
    """Parse empty array returns empty list."""
    with NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump([], f)
        path = Path(f.name)
    try:
        result = parse_seed_items(path)
        assert result == []
    finally:
        path.unlink()


def test_parse_seed_items_not_array_raises() -> None:
    """Non-array JSON raises ValueError."""
    with NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"items": []}, f)
        path = Path(f.name)
    try:
        with pytest.raises(ValueError, match="array"):
            parse_seed_items(path)
    finally:
        path.unlink()


def test_parse_seed_items_invalid_json_raises() -> None:
    """Invalid JSON raises JSONDecodeError."""
    with NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("{ invalid }")
        path = Path(f.name)
    try:
        with pytest.raises(json.JSONDecodeError):
            parse_seed_items(path)
    finally:
        path.unlink()


# -- normalize_to_canonical ----------------------------------------------------


def test_normalize_minimal() -> None:
    """Minimal raw dict maps to ItemCreate."""
    raw = {"type": "movie", "title": "Test"}
    item = normalize_to_canonical(raw)
    assert item.type == ItemType.movie
    assert item.title == "Test"
    assert item.synopsis is None
    assert item.genres is None


def test_normalize_overview_maps_to_synopsis() -> None:
    """Raw 'overview' maps to synopsis (common API convention)."""
    raw = {"type": "movie", "title": "T", "overview": "The plot"}
    item = normalize_to_canonical(raw)
    assert item.synopsis == "The plot"


def test_normalize_synopsis_overrides_overview() -> None:
    """Explicit synopsis takes precedence over overview."""
    raw = {"type": "movie", "title": "T", "synopsis": "S", "overview": "O"}
    item = normalize_to_canonical(raw)
    assert item.synopsis == "S"


def test_normalize_release_date_string() -> None:
    """release_date as ISO string is parsed to date."""
    raw = {"type": "movie", "title": "T", "release_date": "2020-05-15"}
    item = normalize_to_canonical(raw)
    assert item.release_date == date(2020, 5, 15)


def test_normalize_release_date_invalid_string() -> None:
    """Invalid release_date string becomes None."""
    raw = {"type": "movie", "title": "T", "release_date": "not-a-date"}
    item = normalize_to_canonical(raw)
    assert item.release_date is None


def test_normalize_type_series() -> None:
    """type 'series' maps to ItemType.series."""
    raw = {"type": "series", "title": "T"}
    item = normalize_to_canonical(raw)
    assert item.type == ItemType.series


def test_normalize_type_episode() -> None:
    """type 'episode' maps to ItemType.episode."""
    raw = {"type": "episode", "title": "T"}
    item = normalize_to_canonical(raw)
    assert item.type == ItemType.episode


def test_normalize_type_invalid_defaults_to_movie() -> None:
    """Invalid type defaults to movie."""
    raw = {"type": "unknown", "title": "T"}
    item = normalize_to_canonical(raw)
    assert item.type == ItemType.movie


def test_normalize_full_item() -> None:
    """Full raw item maps correctly with normalization."""
    raw = {
        "type": "movie",
        "title": "  Inception  ",
        "synopsis": "Dream heist",
        "genres": ["Sci-Fi", "sci-fi", "Action"],
        "runtime": 148,
        "release_date": "2010-07-16",
        "language": "en",
        "cast": {"lead": "DiCaprio"},
    }
    item = normalize_to_canonical(raw)
    assert item.title == "Inception"
    assert item.genres == ["sci-fi", "action"]
    assert item.runtime == 148
    assert item.release_date == date(2010, 7, 16)
    assert item.cast == {"lead": "DiCaprio"}
