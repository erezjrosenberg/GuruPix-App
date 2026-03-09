"""
SQLAlchemy declarative base and shared setup for all DB models.

Why: Every table (users, profiles, items, etc.) is defined as a class that
inherits from Base. Base gives us:
- A standard way to create tables (metadata, column types)
- So Alembic can discover all models and generate migrations from them.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models in GuruPix.

    We don't add table names or other conventions here; each model
    defines __tablename__ and its columns explicitly.
    """

    pass
