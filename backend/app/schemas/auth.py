"""Pydantic request/response schemas for authentication endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    """Body for POST /auth/signup."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    """Body for POST /auth/login."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """Returned on successful signup or login."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Public representation of a user (returned by /auth/me)."""

    id: uuid.UUID
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class GoogleStartResponse(BaseModel):
    """Returned by GET /auth/google/start."""

    authorization_url: str
