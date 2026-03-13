"""
Unit tests for Stage 5.4: Review aggregate schema validation.
"""

from __future__ import annotations

from app.schemas.reviews import ReviewAggregateResponse


def test_review_aggregate_response_valid() -> None:
    """ReviewAggregateResponse accepts valid data."""
    resp = ReviewAggregateResponse(
        source="RT_CRITICS",
        score=85.0,
        scale=100.0,
        normalized_score=85.0,
    )
    assert resp.source == "RT_CRITICS"
    assert resp.score == 85.0
    assert resp.normalized_score == 85.0


def test_review_aggregate_response_normalized_optional() -> None:
    """normalized_score can be None."""
    resp = ReviewAggregateResponse(
        source="RT_AUDIENCE",
        score=91,
        scale=100,
    )
    assert resp.normalized_score is None
