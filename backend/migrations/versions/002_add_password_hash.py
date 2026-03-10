"""Add password_hash column to users table.

Revision ID: 002
Revises: 001
Create Date: Stage 4 — Authentication

Email/password users need a stored bcrypt hash. The column is nullable
because Google OAuth users authenticate without a password.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("password_hash", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "password_hash")
