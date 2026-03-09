"""
Alembic environment: run migrations with sync Postgres URL and our models.

Why: When you run `alembic upgrade head`, this file:
1. Loads the sync DATABASE_URL from app.core.config (which reads .env).
2. Sets target_metadata to our Base.metadata so Alembic knows all tables.
3. Runs migrations in a transaction.

We must import all models (via app.db) so that Base.metadata includes every table.
"""

from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Add the backend root to the path so "app" is importable when running from backend/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import Settings
from app.db.base import Base

# Import all models so that Base.metadata has every table (required for autogenerate).
import app.db.models  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Set sqlalchemy.url from our settings (sync URL for psycopg2).
settings = Settings()
sync_url = settings.get_sync_database_url()
config.set_main_option("sqlalchemy.url", sync_url)


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Only generates SQL; does not connect to the database. Useful for
    inspecting what would be applied.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    Creates a real connection and runs migrations inside a transaction.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
