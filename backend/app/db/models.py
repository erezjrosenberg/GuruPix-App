"""
SQLAlchemy ORM models for all GuruPix tables (Stage 2).

Why: Each class below maps to one database table. The columns match the
ROADMAP_GuruPix_System_Design.md schema so that:
- Auth: users, oauth_accounts
- Profiles: profiles
- Catalog: items
- Availability: item_availability
- Review signals: item_reviews_agg
- Learning loop: events
- Model registry: models
- Context prompts: contexts, context_events

We use PostgreSQL types (JSONB, ARRAY, UUID, ENUM) where specified.
"""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


# -----------------------------------------------------------------------------
# Enums (stored as PostgreSQL ENUMs where used)
# -----------------------------------------------------------------------------


class ModelStatus(str, enum.Enum):
    """Status of a model in the registry (candidate vs promoted)."""

    candidate = "candidate"
    promoted = "promoted"


# -----------------------------------------------------------------------------
# Auth
# -----------------------------------------------------------------------------


class User(Base):
    """
    User account (email-based or linked via OAuth).

    id: UUID primary key.
    email: Unique; used for login and identity.
    created_at: When the account was created.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    oauth_accounts: Mapped[List["OAuthAccount"]] = relationship(
        "OAuthAccount", back_populates="user", cascade="all, delete-orphan"
    )


class OAuthAccount(Base):
    """
    OAuth provider link (e.g. Google) for a user.

    user_id: References users.id.
    provider: e.g. "google".
    provider_account_id: Id from the provider.
    tokens_metadata: JSON blob for tokens (refresh, etc.); structure is provider-specific.
    """

    __tablename__ = "oauth_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    provider_account_id: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tokens_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="oauth_accounts")

    __table_args__ = (
        UniqueConstraint("provider", "provider_account_id", name="uq_oauth_provider_account"),
    )


# -----------------------------------------------------------------------------
# Profiles
# -----------------------------------------------------------------------------


class Profile(Base):
    """
    User profile: preferences, region, providers, consent, embedding ref.

    user_id: PK and FK to users.id (one profile per user).
    preferences: JSON (quiz answers, likes, etc.).
    embedding_id: Optional reference to vector/embedding.
    region, languages, providers: For where-to-watch and localization.
    consent: JSON for consent flags (e.g. prompt retention, imports).
    """

    __tablename__ = "profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    preferences: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    embedding_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    region: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    languages: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text), nullable=True)
    providers: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text), nullable=True)
    consent: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )


# -----------------------------------------------------------------------------
# Catalog
# -----------------------------------------------------------------------------


class Item(Base):
    """
    Catalog item: movie, series, or episode.

    type: e.g. "movie", "series", "episode".
    title, synopsis, genres[], cast/crew JSON, runtime, release_date, language.
    metadata: Extra JSON for flexibility.
    """

    __tablename__ = "items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    synopsis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    genres: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text), nullable=True)
    cast: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    crew: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    runtime: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)  # minutes
    release_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    language: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )


# -----------------------------------------------------------------------------
# Availability
# -----------------------------------------------------------------------------


class ItemAvailability(Base):
    """
    Where to watch: provider + region + url + type.

    item_id: FK to items.id.
    provider, region, url, availability_type (e.g. stream, rent).
    """

    __tablename__ = "item_availability"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    region: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    availability_type: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


# -----------------------------------------------------------------------------
# Review signals
# -----------------------------------------------------------------------------


class ItemReviewsAgg(Base):
    """
    Aggregate review score per item per source (e.g. RT_CRITICS, RT_AUDIENCE, NYT).

    source: Identifier for the review source.
    score: Numeric score.
    scale: e.g. 100 or 5 (so clients can normalize).
    metadata: Confidence/attribution without storing prohibited content.
    """

    __tablename__ = "item_reviews_agg"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    score: Mapped[float] = mapped_column(nullable=False)
    scale: Mapped[float] = mapped_column(nullable=False)  # e.g. 100.0 or 5.0
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    metadata_: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSONB, nullable=True)


# -----------------------------------------------------------------------------
# Learning loop (events)
# -----------------------------------------------------------------------------


class Event(Base):
    """
    User feedback event: like, dislike, watch_complete, skip, etc.

    user_id, item_id, type, timestamp, session_id, request_id.
    context_id: Optional link to a context prompt.
    metadata: Extra JSON.
    """

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    session_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True, index=True)
    request_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True, index=True)
    context_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("contexts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    metadata_: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSONB, nullable=True)


# -----------------------------------------------------------------------------
# Model registry
# -----------------------------------------------------------------------------


class Model(Base):
    """
    Trained model version: version string, metrics, status (candidate/promoted).
    """

    __tablename__ = "models"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    version: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    status: Mapped[ModelStatus] = mapped_column(
        Enum(ModelStatus, name="model_status", create_constraint=True),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


# -----------------------------------------------------------------------------
# Context prompts
# -----------------------------------------------------------------------------


class Context(Base):
    """
    Saved context preset: label + parsed attributes (e.g. date night, cozy).
    """

    __tablename__ = "contexts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    label: Mapped[str] = mapped_column(Text, nullable=False)
    attributes: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ContextEvent(Base):
    """
    Log of a context/vibe prompt use: parsed result, optional raw text (if opt-in).
    """

    __tablename__ = "context_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    context_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("contexts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    prompt_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parsed: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    retention_opt_in: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSONB, nullable=True)
