"""Tests for posture context builder.

Phase 117: Forward-Looking Risk Framework
"""

from __future__ import annotations

import pytest

from do_uw.models.forward_looking import (
    ForwardLookingData,
    PostureElement,
    PostureRecommendation,
    WatchItem,
)
from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders.posture_context import extract_posture


def _make_state(**kwargs: object) -> AnalysisState:
    """Build minimal AnalysisState with forward_looking data."""
    fl = ForwardLookingData(**kwargs)  # type: ignore[arg-type]
    return AnalysisState(ticker="TEST", forward_looking=fl)


class TestPostureContext:
    """Tests for extract_posture context builder."""

    def test_with_posture_data(self) -> None:
        """Populated posture returns correct tier and elements."""
        posture = PostureRecommendation(
            tier="WRITE",
            elements=[
                PostureElement(
                    element="decision",
                    recommendation="Accept with standard terms",
                    rationale="Moderate risk profile",
                ),
                PostureElement(
                    element="retention",
                    recommendation="$1M SIR",
                    rationale="Standard for this tier",
                ),
                PostureElement(
                    element="limit",
                    recommendation="Up to $10M",
                    rationale="Adequate for market cap",
                ),
            ],
        )
        state = _make_state(posture=posture)
        result = extract_posture(state, {})

        assert result["posture_available"] is True
        assert result["posture_tier"] == "WRITE"
        assert result["posture_tier_class"] == "posture-write"
        assert len(result["posture_elements"]) == 3
        assert result["posture_elements"][0]["recommendation"] == "Accept with standard terms"

    def test_element_name_humanization(self) -> None:
        """Element keys are humanized correctly."""
        posture = PostureRecommendation(
            tier="WANT",
            elements=[
                PostureElement(element="decision", recommendation="Go"),
                PostureElement(element="retention", recommendation="$500K"),
                PostureElement(element="limit", recommendation="$15M"),
                PostureElement(element="pricing", recommendation="Standard"),
                PostureElement(element="exclusions", recommendation="None"),
                PostureElement(element="monitoring", recommendation="Quarterly"),
                PostureElement(element="re_evaluation", recommendation="Annual"),
            ],
        )
        state = _make_state(posture=posture)
        result = extract_posture(state, {})

        names = [e["element"] for e in result["posture_elements"]]
        assert names == [
            "Decision", "Retention", "Limit Capacity", "Pricing",
            "Exclusions", "Monitoring", "Re-evaluation",
        ]

    def test_with_overrides_applied(self) -> None:
        """Overrides list is populated and has_overrides is True."""
        posture = PostureRecommendation(
            tier="WATCH",
            overrides_applied=[
                "F.1>0: litigation exclusion added",
                "F.3>6: pricing surcharge applied",
            ],
        )
        state = _make_state(posture=posture)
        result = extract_posture(state, {})

        assert result["has_overrides"] is True
        assert len(result["overrides_applied"]) == 2
        assert "F.1>0" in result["overrides_applied"][0]

    def test_with_zero_verifications(self) -> None:
        """Zero verifications formatted from state dicts."""
        zero_vecs = [
            {"factor_id": "F.1", "factor_name": "Litigation History", "points": "0",
             "evidence": "No active litigation", "source": "CourtListener"},
            {"factor_id": "F.7", "factor_name": "Insider Trading", "points": "0",
             "evidence": "No suspicious transactions", "source": "SEC"},
        ]
        state = _make_state(
            posture=PostureRecommendation(tier="WIN"),
            zero_verifications=zero_vecs,
        )
        result = extract_posture(state, {})

        assert result["has_zero_verifications"] is True
        assert result["zero_verification_count"] == 2
        assert result["zero_verifications"][0]["factor_id"] == "F.1"
        assert result["zero_verifications"][1]["evidence"] == "No suspicious transactions"

    def test_with_watch_items(self) -> None:
        """Watch items formatted with all fields."""
        watch = [
            WatchItem(
                item="Revenue guidance",
                current_state="On track",
                threshold="Miss >5% triggers review",
                re_evaluation="Quarterly",
                source="8-K filings",
            ),
        ]
        state = _make_state(
            posture=PostureRecommendation(tier="WRITE"),
            watch_items=watch,
        )
        result = extract_posture(state, {})

        assert result["has_watch_items"] is True
        assert result["watch_item_count"] == 1
        assert result["watch_items"][0]["item"] == "Revenue guidance"
        assert result["watch_items"][0]["threshold"] == "Miss >5% triggers review"

    def test_no_posture_data(self) -> None:
        """No posture data returns posture_available=False."""
        state = _make_state()
        result = extract_posture(state, {})

        assert result["posture_available"] is False
        assert result["posture_tier"] == "UNKNOWN"
        assert result["posture_tier_class"] == "posture-unknown"
        assert result["posture_elements"] == []
        assert result["has_overrides"] is False
        assert result["has_zero_verifications"] is False
        assert result["has_watch_items"] is False

    def test_all_tier_css_classes(self) -> None:
        """All 6 tiers map to correct CSS classes."""
        for tier, expected_class in [
            ("WIN", "posture-win"),
            ("WANT", "posture-want"),
            ("WRITE", "posture-write"),
            ("WATCH", "posture-watch"),
            ("WALK", "posture-walk"),
            ("NO_TOUCH", "posture-no-touch"),
        ]:
            posture = PostureRecommendation(tier=tier)
            state = _make_state(posture=posture)
            result = extract_posture(state, {})
            assert result["posture_tier_class"] == expected_class, f"Failed for tier {tier}"
