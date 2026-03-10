"""Initial schema: users, oauth_accounts, profiles, items, availability, reviews, events, models, contexts.

Revision ID: 001
Revises:
Create Date: Stage 2 — Database + Migrations

Creates all tables per ROADMAP_GuruPix_System_Design.md Stage 2.1.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # Auth
    # -------------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "oauth_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("provider_account_id", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("tokens_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "provider_account_id", name="uq_oauth_provider_account"),
    )
    op.create_index(
        op.f("ix_oauth_accounts_provider"), "oauth_accounts", ["provider"], unique=False
    )
    op.create_index(
        op.f("ix_oauth_accounts_provider_account_id"),
        "oauth_accounts",
        ["provider_account_id"],
        unique=False,
    )
    op.create_index(op.f("ix_oauth_accounts_user_id"), "oauth_accounts", ["user_id"], unique=False)

    # -------------------------------------------------------------------------
    # Profiles
    # -------------------------------------------------------------------------
    op.create_table(
        "profiles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("preferences", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("embedding_id", sa.Text(), nullable=True),
        sa.Column("region", sa.Text(), nullable=True),
        sa.Column("languages", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("providers", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("consent", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )

    # -------------------------------------------------------------------------
    # Catalog
    # -------------------------------------------------------------------------
    op.create_table(
        "items",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("synopsis", sa.Text(), nullable=True),
        sa.Column("genres", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("cast", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("crew", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("runtime", sa.BigInteger(), nullable=True),
        sa.Column("release_date", sa.Date(), nullable=True),
        sa.Column("language", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_items_title"), "items", ["title"], unique=False)
    op.create_index(op.f("ix_items_type"), "items", ["type"], unique=False)

    # -------------------------------------------------------------------------
    # Availability
    # -------------------------------------------------------------------------
    op.create_table(
        "item_availability",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("item_id", sa.BigInteger(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("region", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("availability_type", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_item_availability_item_id"), "item_availability", ["item_id"], unique=False
    )
    op.create_index(
        op.f("ix_item_availability_provider"), "item_availability", ["provider"], unique=False
    )
    op.create_index(
        op.f("ix_item_availability_region"), "item_availability", ["region"], unique=False
    )
    op.create_index(
        op.f("ix_item_availability_availability_type"),
        "item_availability",
        ["availability_type"],
        unique=False,
    )

    # -------------------------------------------------------------------------
    # Review signals
    # -------------------------------------------------------------------------
    op.create_table(
        "item_reviews_agg",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("item_id", sa.BigInteger(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("scale", sa.Float(), nullable=False),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_item_reviews_agg_item_id"), "item_reviews_agg", ["item_id"], unique=False
    )
    op.create_index(
        op.f("ix_item_reviews_agg_source"), "item_reviews_agg", ["source"], unique=False
    )

    # -------------------------------------------------------------------------
    # Contexts (before events / context_events which reference contexts.id)
    # -------------------------------------------------------------------------
    op.create_table(
        "contexts",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("attributes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_contexts_user_id"), "contexts", ["user_id"], unique=False)

    # -------------------------------------------------------------------------
    # Model registry (uses PostgreSQL ENUM)
    # -------------------------------------------------------------------------
    model_status = postgresql.ENUM("candidate", "promoted", name="model_status", create_type=True)
    model_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "models",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM("candidate", "promoted", name="model_status", create_type=False),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_models_version"), "models", ["version"], unique=True)
    op.create_index(op.f("ix_models_status"), "models", ["status"], unique=False)

    # -------------------------------------------------------------------------
    # Learning loop (events) — references users, items, contexts
    # -------------------------------------------------------------------------
    op.create_table(
        "events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", sa.BigInteger(), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("session_id", sa.Text(), nullable=True),
        sa.Column("request_id", sa.Text(), nullable=True),
        sa.Column("context_id", sa.BigInteger(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["context_id"], ["contexts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_events_user_id"), "events", ["user_id"], unique=False)
    op.create_index(op.f("ix_events_item_id"), "events", ["item_id"], unique=False)
    op.create_index(op.f("ix_events_type"), "events", ["type"], unique=False)
    op.create_index(op.f("ix_events_session_id"), "events", ["session_id"], unique=False)
    op.create_index(op.f("ix_events_request_id"), "events", ["request_id"], unique=False)
    op.create_index(op.f("ix_events_context_id"), "events", ["context_id"], unique=False)

    # -------------------------------------------------------------------------
    # Context events
    # -------------------------------------------------------------------------
    op.create_table(
        "context_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("context_id", sa.BigInteger(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("prompt_text", sa.Text(), nullable=True),
        sa.Column("parsed", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("retention_opt_in", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["context_id"], ["contexts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_context_events_user_id"), "context_events", ["user_id"], unique=False)
    op.create_index(
        op.f("ix_context_events_context_id"), "context_events", ["context_id"], unique=False
    )


def downgrade() -> None:
    # Context events
    op.drop_index(op.f("ix_context_events_context_id"), table_name="context_events")
    op.drop_index(op.f("ix_context_events_user_id"), table_name="context_events")
    op.drop_table("context_events")

    # Events
    op.drop_index(op.f("ix_events_context_id"), table_name="events")
    op.drop_index(op.f("ix_events_request_id"), table_name="events")
    op.drop_index(op.f("ix_events_session_id"), table_name="events")
    op.drop_index(op.f("ix_events_type"), table_name="events")
    op.drop_index(op.f("ix_events_item_id"), table_name="events")
    op.drop_index(op.f("ix_events_user_id"), table_name="events")
    op.drop_table("events")

    # Models + enum
    op.drop_index(op.f("ix_models_status"), table_name="models")
    op.drop_index(op.f("ix_models_version"), table_name="models")
    op.drop_table("models")
    postgresql.ENUM(name="model_status").drop(op.get_bind(), checkfirst=True)

    # Contexts
    op.drop_index(op.f("ix_contexts_user_id"), table_name="contexts")
    op.drop_table("contexts")

    # Item reviews agg
    op.drop_index(op.f("ix_item_reviews_agg_source"), table_name="item_reviews_agg")
    op.drop_index(op.f("ix_item_reviews_agg_item_id"), table_name="item_reviews_agg")
    op.drop_table("item_reviews_agg")

    # Item availability
    op.drop_index(op.f("ix_item_availability_availability_type"), table_name="item_availability")
    op.drop_index(op.f("ix_item_availability_region"), table_name="item_availability")
    op.drop_index(op.f("ix_item_availability_provider"), table_name="item_availability")
    op.drop_index(op.f("ix_item_availability_item_id"), table_name="item_availability")
    op.drop_table("item_availability")

    # Items
    op.drop_index(op.f("ix_items_type"), table_name="items")
    op.drop_index(op.f("ix_items_title"), table_name="items")
    op.drop_table("items")

    # Profiles
    op.drop_table("profiles")

    # OAuth accounts
    op.drop_index(op.f("ix_oauth_accounts_user_id"), table_name="oauth_accounts")
    op.drop_index(op.f("ix_oauth_accounts_provider_account_id"), table_name="oauth_accounts")
    op.drop_index(op.f("ix_oauth_accounts_provider"), table_name="oauth_accounts")
    op.drop_table("oauth_accounts")

    # Users
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
