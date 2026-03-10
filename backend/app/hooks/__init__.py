"""
Internal event bus for GuruPix backend hooks.

Provides a lightweight publish/subscribe mechanism so that different parts of
the codebase can react to domain events (e.g. user logged in, item ingested)
without tight coupling.

Usage::

    from app.hooks import event_bus

    # Subscribe (usually at module or startup time)
    event_bus.subscribe("on_user_logged_in", my_handler)

    # Emit (from auth service, for example)
    await event_bus.emit("on_user_logged_in", user_id=str(user.id))
"""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class EventBus:
    """Simple async event bus — subscribe handlers to named events, then emit."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[..., Any]]] = defaultdict(list)

    def subscribe(self, event: str, handler: Callable[..., Any]) -> None:
        """Register *handler* to be called when *event* is emitted."""
        self._handlers[event].append(handler)

    async def emit(self, event: str, **kwargs: Any) -> None:
        """Call all handlers subscribed to *event* with **kwargs.

        Handlers may be sync or async. Errors are logged but do not propagate
        so that one broken handler cannot prevent others from running.
        """
        for handler in self._handlers.get(event, []):
            try:
                import asyncio

                result = handler(**kwargs)
                if asyncio.iscoroutine(result):
                    await result
            except Exception:
                logger.exception("Hook handler %s for event %s failed", handler, event)

    def clear(self) -> None:
        """Remove all subscriptions (useful in tests)."""
        self._handlers.clear()


event_bus = EventBus()
