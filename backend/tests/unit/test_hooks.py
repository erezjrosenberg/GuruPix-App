"""Unit tests for the internal event bus (app.hooks.EventBus)."""

from __future__ import annotations

import pytest
from app.hooks import EventBus


@pytest.fixture
def bus() -> EventBus:
    return EventBus()


@pytest.mark.asyncio
async def test_emit_calls_sync_handler(bus: EventBus) -> None:
    calls: list[dict] = []
    bus.subscribe("on_user_logged_in", lambda **kw: calls.append(kw))

    await bus.emit("on_user_logged_in", user_id="u1", method="email")

    assert len(calls) == 1
    assert calls[0] == {"user_id": "u1", "method": "email"}


@pytest.mark.asyncio
async def test_emit_calls_async_handler(bus: EventBus) -> None:
    calls: list[dict] = []

    async def handler(**kw: object) -> None:
        calls.append(kw)  # type: ignore[arg-type]

    bus.subscribe("on_user_logged_in", handler)
    await bus.emit("on_user_logged_in", user_id="u2", method="google")

    assert len(calls) == 1
    assert calls[0]["user_id"] == "u2"


@pytest.mark.asyncio
async def test_emit_multiple_handlers(bus: EventBus) -> None:
    results: list[str] = []
    bus.subscribe("on_test", lambda **kw: results.append("a"))
    bus.subscribe("on_test", lambda **kw: results.append("b"))

    await bus.emit("on_test")
    assert results == ["a", "b"]


@pytest.mark.asyncio
async def test_emit_unknown_event_does_nothing(bus: EventBus) -> None:
    await bus.emit("on_nonexistent_event")  # should not raise


@pytest.mark.asyncio
async def test_handler_error_does_not_propagate(bus: EventBus) -> None:
    calls: list[str] = []

    def bad_handler(**kw: object) -> None:
        raise RuntimeError("boom")

    bus.subscribe("on_test", bad_handler)
    bus.subscribe("on_test", lambda **kw: calls.append("ok"))

    await bus.emit("on_test")
    assert calls == ["ok"]


@pytest.mark.asyncio
async def test_clear_removes_all_handlers(bus: EventBus) -> None:
    calls: list[str] = []
    bus.subscribe("on_test", lambda **kw: calls.append("x"))
    bus.clear()
    await bus.emit("on_test")
    assert calls == []
