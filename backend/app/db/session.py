"""
Async SQLAlchemy engine, session factory, and FastAPI dependency.

Provides ``get_db`` — a FastAPI dependency that yields one async session
per request and ensures it is closed afterwards.

The engine is created lazily on first use so that importing this module
during unit tests (where Postgres may not be running) does not fail.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings

_engine = None
_session_factory = None


def _get_engine():  # type: ignore[no-untyped-def]
    global _engine
    if _engine is None:
        settings = Settings()
        _engine = create_async_engine(settings.database_url, echo=False, future=True)
    return _engine


def _get_session_factory():  # type: ignore[no-untyped-def]
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            _get_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _session_factory


async def get_db() -> AsyncIterator[AsyncSession]:
    """Yield an async SQLAlchemy session scoped to one request."""
    factory = _get_session_factory()
    async with factory() as session:
        try:
            yield session
        finally:
            await session.close()


def reset_engine() -> None:
    """Dispose of the current engine (useful between test runs)."""
    global _engine, _session_factory
    if _engine is not None:
        import asyncio

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_engine.dispose())
        except RuntimeError:
            pass
    _engine = None
    _session_factory = None
