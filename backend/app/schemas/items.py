"""
Pydantic schemas for catalog items (movie, series, episode).

These schemas define the canonical shape for items in GuruPix. Validators
ensure data is normalized (e.g., trimmed titles, lowercase genres) before
storage. Used by ingestion and API responses.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class ItemType(StrEnum):
    """Canonical item types supported by the catalog."""

    movie = "movie"
    series = "series"
    episode = "episode"


class ItemCreate(BaseModel):
    """
    Schema for creating an item (used during ingestion).

    All fields except title and type can be optional. Validators normalize
    strings (trim, lowercase genres) and enforce constraints (runtime >= 0).
    """

    type: ItemType
    title: str = Field(..., min_length=1, max_length=500)
    synopsis: str | None = None
    genres: list[str] | None = None
    cast: dict[str, Any] | None = None
    crew: dict[str, Any] | None = None
    runtime: int | None = Field(default=None, ge=0, description="Runtime in minutes")
    release_date: date | None = None
    language: str | None = None
    metadata: dict[str, Any] | None = None

    @field_validator("title", mode="before")
    @classmethod
    def trim_title(cls, v: str) -> str:
        """Trim leading/trailing whitespace from title."""
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("genres", mode="before")
    @classmethod
    def normalize_genres(cls, v: list[str] | None) -> list[str] | None:
        """Lowercase and deduplicate genres while preserving order."""
        if v is None:
            return None
        seen: set[str] = set()
        result: list[str] = []
        for g in v:
            if isinstance(g, str):
                normalized = g.strip().lower()
                if normalized and normalized not in seen:
                    seen.add(normalized)
                    result.append(normalized)
        return result if result else None

    @field_validator("synopsis", mode="before")
    @classmethod
    def trim_synopsis(cls, v: str | None) -> str | None:
        """Trim synopsis if present."""
        if isinstance(v, str):
            s = v.strip()
            return s if s else None
        return v

    @field_validator("language", mode="before")
    @classmethod
    def trim_language(cls, v: str | None) -> str | None:
        """Trim language if present."""
        if isinstance(v, str):
            s = v.strip()
            return s if s else None
        return v

    @model_validator(mode="after")
    def ensure_title_non_empty(self) -> ItemCreate:
        """Ensure title is non-empty after trimming."""
        if not self.title or not self.title.strip():
            raise ValueError("Title cannot be empty")
        return self


class ItemResponse(BaseModel):
    """
    Public representation of an item (returned by API).

    Includes all fields from the DB model. Does not expose raw_payload
    from metadata for security.
    """

    id: int
    type: str
    title: str
    synopsis: str | None = None
    genres: list[str] | None = None
    cast: dict[str, Any] | None = None
    crew: dict[str, Any] | None = None
    runtime: int | None = None
    release_date: date | None = None
    language: str | None = None
    metadata: dict[str, Any] | None = Field(
        default=None,
        validation_alias="metadata_",
        description="Extra metadata (raw_payload excluded from API)",
    )

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def strip_raw_payload(self) -> ItemResponse:
        """Remove raw_payload from metadata before exposing via API."""
        if self.metadata and "raw_payload" in self.metadata:
            metadata_copy = {k: v for k, v in self.metadata.items() if k != "raw_payload"}
            return self.model_copy(update={"metadata": metadata_copy or None})
        return self
