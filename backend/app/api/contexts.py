"""Contexts API — CRUD for user context presets (e.g. date night, cozy)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.contexts import ContextCreate, ContextResponse
from app.services.contexts import create_context, delete_context, list_contexts

router = APIRouter(prefix="/api/v1/contexts", tags=["contexts"])
logger = logging.getLogger("gurupix.contexts")


@router.post("", response_model=ContextResponse, status_code=201)
async def create_context_endpoint(
    body: ContextCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ContextResponse:
    """Create a context preset (e.g. date night, cozy)."""
    ctx = await create_context(db, current_user, body)
    logger.info("Context created", extra={"user_id": str(current_user.id), "context_id": ctx.id})
    return ctx


@router.get("", response_model=list[ContextResponse])
async def list_contexts_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ContextResponse]:
    """List current user's context presets."""
    return await list_contexts(db, current_user.id)


@router.delete("/{context_id}", status_code=204)
async def delete_context_endpoint(
    context_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a context preset. Returns 404 if not found or not owned."""
    deleted = await delete_context(db, current_user.id, context_id)
    if not deleted:
        logger.warning("Context delete failed: not found or not owned", extra={"context_id": context_id})
        raise HTTPException(status_code=404, detail="Context not found")
    logger.info("Context deleted", extra={"user_id": str(current_user.id), "context_id": context_id})
