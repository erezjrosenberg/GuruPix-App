"""Context service — create, list, delete user contexts."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Context, User
from app.schemas.contexts import ContextCreate, ContextResponse


def _context_to_response(ctx: Context) -> ContextResponse:
    return ContextResponse(
        id=ctx.id,
        user_id=str(ctx.user_id),
        label=ctx.label,
        attributes=ctx.attributes,
        created_at=ctx.created_at,
    )


async def create_context(
    db: AsyncSession,
    user: User,
    data: ContextCreate,
) -> ContextResponse:
    """Create a context preset for the user."""
    ctx = Context(
        user_id=user.id,
        label=data.label,
        attributes=data.attributes,
    )
    db.add(ctx)
    await db.commit()
    await db.refresh(ctx)
    return _context_to_response(ctx)


async def list_contexts(db: AsyncSession, user_id: uuid.UUID) -> list[ContextResponse]:
    """List all contexts for a user."""
    result = await db.execute(select(Context).where(Context.user_id == user_id).order_by(Context.created_at.desc()))
    contexts = result.scalars().all()
    return [_context_to_response(c) for c in contexts]


async def delete_context(
    db: AsyncSession,
    user_id: uuid.UUID,
    context_id: int,
) -> bool:
    """Delete a context if owned by user. Returns True if deleted, False if not found."""
    result = await db.execute(
        select(Context).where(Context.id == context_id, Context.user_id == user_id)
    )
    ctx = result.scalar_one_or_none()
    if ctx is None:
        return False
    await db.delete(ctx)
    await db.commit()
    return True
