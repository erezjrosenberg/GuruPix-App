"""Seed admin user for local development (idempotent).

Revision ID: 003
Revises: 002
Create Date: Stage 5 — Admin always in DB

Inserts admin@gurupix.com / admin123 if not present. Safe to run multiple times.
Postgres volume persists data across container restarts.
"""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    conn = op.get_bind()
    # Remove erez user if present (one-time cleanup)
    conn.execute(sa.text("DELETE FROM users WHERE email = 'erez@gurupix.com'"))

    # Create admin if not present (idempotent)
    result = conn.execute(
        sa.text("SELECT 1 FROM users WHERE email = 'admin@gurupix.com' LIMIT 1")
    )
    if result.fetchone():
        return

    from app.core.security import hash_password

    pwd_hash = hash_password("admin123")
    user_id = str(uuid.uuid4())
    conn.execute(
        sa.text(
            "INSERT INTO users (id, email, password_hash, created_at) "
            "VALUES (CAST(:id AS uuid), :email, :ph, NOW() AT TIME ZONE 'UTC')"
        ),
        {"id": user_id, "email": "admin@gurupix.com", "ph": pwd_hash},
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM users WHERE email = 'admin@gurupix.com'"))
