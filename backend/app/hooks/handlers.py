"""
Event bus handlers — react to domain events (e.g. user logged in).

Registered at app startup. Profile is created via onboarding (POST /profiles/me)
with consent; we do not auto-create profiles here to avoid bypassing consent.
"""

from __future__ import annotations


def register_handlers() -> None:
    """Subscribe all production handlers to the event bus."""
    pass  # No handlers needed yet; profile created via onboarding flow
