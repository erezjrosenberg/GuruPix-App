"""Pydantic schemas for profile endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ProfileResponse(BaseModel):
    """Profile as returned by API. Email comes from user, not editable."""

    user_id: str
    display_name: str | None = None
    bio: str | None = None
    region: str | None = None
    languages: list[str] | None = None
    providers: list[str] | None = None
    preferences: dict[str, Any] | None = None
    consent: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class ProfileUpdate(BaseModel):
    """Fields user can update. Email is NOT included."""

    display_name: str | None = Field(None, max_length=100)
    bio: str | None = Field(None, max_length=500)
    region: str | None = Field(None, max_length=10)
    languages: list[str] | None = None
    providers: list[str] | None = None


class ProfileCreate(BaseModel):
    """Initial profile creation (onboarding). Includes consent."""

    display_name: str | None = Field(None, max_length=100)
    bio: str | None = Field(None, max_length=500)
    region: str | None = Field(None, max_length=10)
    languages: list[str] | None = None
    providers: list[str] | None = None
    consent_data_processing: bool = Field(..., description="User must accept to continue")
