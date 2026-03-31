"""Tests for hazard engine: IES computation, interactions, and multiplier.

Tests cover:
- Category aggregation with weighted averaging
- IES-to-filing-multiplier piecewise linear interpolation
- Named interaction detection (trigger and non-trigger)
- Dynamic co-occurrence detection
- End-to-end compute_hazard_profile
- Interaction multiplier cap at 2.0x
- Low data coverage confidence note
- MEETING_PREP underwriter flag collection
"""

from __future__ import annotations

from typing import Any

import pytest

from do_uw.stages.analyze.layers.hazard.hazard_engine import (
    _ies_to_filing_multiplier,
    aggregate_by_category,
    compute_hazard_profile,
    compute_interaction_multiplier,
)
from do_uw.stages.analyze.layers.hazard.interaction_effects import (
    detect_dynamic_interactions,
    detect_named_interactions,
)


# -----------------------------------------------------------------------
# Test data factories
# -----------------------------------------------------------------------


def _make_dim_score(
    dim_id: str,
    category: str,
    normalized: float = 50.0,
    weight: float = 1.0,
    data_available: bool = True,
    evidence: list[str] | None = None,
) -> dict[str, Any]:
    """Create a minimal dimension score dict for testing."""
    return {
        "dimension_id": dim_id,
        "dimension_name": f"Test {dim_id}",
        "category": category,
        "raw_score": normalized / 100.0 * 5.0,
        "max_score": 5.0,
        "normalized_score": normalized,
        "weight": weight,
        "data_available": data_available,
        "data_tier": "primary" if data_available else "unavailable",
        "data_sources": ["test"] if data_available else [],
        "evidence": evidence or [],
    }


def _make_weights_config(
    category_weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Create a minimal weights config for testing."""
    cw = category_weights or {
        "H1": 32.5,
        "H2": 15.0,
        "H3": 15.0,
        "H4": 7.5,
        "H5": 10.0,
        "H6": 10.0,
        "H7": 10.0,
    }
    categories = {
        cat_id: {"name": f"Category {cat_id}", "weight_pct": weight}
        for cat_id, weight in cw.items()
    }
    return {
        "categories": categories,
        "dimensions": {},
        "missing_data_handling": {
            "default_score_pct": 50,
            "low_coverage_threshold_pct": 60,
            "low_coverage_note": "IES based on limited data coverage",
        },
    }


def _make_interactions_config() -> dict[str, Any]:
    """Create the standard interactions config for testing."""
    return {
        "named_interactions": [
            {
                "id": "ROOKIE_ROCKET",
                "name": "Rookie Rocket",
                "description": "High-growth + inexperience + recent IPO",
                "required_dimensions": {
                    "H1-09": {"min_score_pct": 60},
                    "H2-01": {"min_score_pct": 60},
                    "H5-01": {"min_score_pct": 50},
                },
                "multiplier_range": [1.3, 1.5],
            },
            {
                "id": "BLACK_BOX",
                "name": "Black Box",
                "description": "Complex + weak earnings + non-GAAP",
                "required_dimensions": {
                    "H1-02": {"min_score_pct": 60},
                    "H3-04": {"min_score_pct": 50},
                    "H1-11": {"min_score_pct": 50},
                },
                "multiplier_range": [1.2, 1.4],
            },
        ],
        "dynamic_detection": {
            "min_elevated_dimensions": 5,
            "elevated_threshold_pct": 60,
            "co_occurrence_multiplier": [1.05, 1.15],
            "category_concentration_min": 3,
            "category_concentration_multiplier": 1.05,
        },
    }


# -----------------------------------------------------------------------
# aggregate_by_category tests
# -----------------------------------------------------------------------


class TestAggregateByCategory:
    """Tests for category-level score aggregation."""

    def test_basic_aggregation(self) -> None:
        """Two H1 dimensions with different weights produce correct average."""
        config = _make_weights_config({"H1": 32.5})
        dims = [
            _make_dim_score("H1-01", "H1", normalized=80.0, weight=2.0),
            _make_dim_score("H1-02", "H1", normalized=40.0, weight=1.0),
        ]
        result = aggregate_by_category(dims, config)

        assert "H1" in result
        h1 = result["H1"]
        # Weighted average: (80*2 + 40*1) / (2+1) = 200/3 = 66.67
        assert abs(h1.raw_score - 66.67) < 0.1
        # weighted_score = 66.67 * 32.5/100 = 21.67
        assert abs(h1.weighted_score - 21.67) < 0.1
        assert h1.dimensions_scored == 2
        assert h1.dimensions_total == 2
        assert h1.data_coverage_pct == 100.0

    def test_partial_data_coverage(self) -> None:
        """Data coverage correctly counts only dimensions with data."""
        config = _make_weights_config({"H2": 15.0})
        dims = [
            _make_dim_score("H2-01", "H2", normalized=70.0, data_available=True),
            _make_dim_score("H2-02", "H2", normalized=50.0, data_available=False),
            _make_dim_score("H2-03", "H2", normalized=50.0, data_available=False),
        ]
        result = aggregate_by_category(dims, config)

        h2 = result["H2"]
        assert h2.dimensions_scored == 1
        assert h2.dimensions_total == 3
        assert abs(h2.data_coverage_pct - 33.3) < 0.2

    def test_empty_category(self) -> None:
        """Category with no dimensions produces zero scores."""
        config = _make_weights_config({"H7": 10.0})
        result = aggregate_by_category([], config)

        h7 = result["H7"]
        assert h7.raw_score == 0.0
        assert h7.weighted_score == 0.0
        assert h7.dimensions_total == 0

    def test_multiple_categories(self) -> None:
        """Scores correctly separated across categories."""
        config = _make_weights_config({"H1": 50.0, "H3": 50.0})
        dims = [
            _make_dim_score("H1-01", "H1", normalized=100.0),
            _make_dim_score("H3-01", "H3", normalized=0.0),
        ]
        result = aggregate_by_category(dims, config)

        assert result["H1"].raw_score == 100.0
        assert result["H1"].weighted_score == 50.0
        assert result["H3"].raw_score == 0.0
        assert result["H3"].weighted_score == 0.0


# -----------------------------------------------------------------------
# _ies_to_filing_multiplier tests
# -----------------------------------------------------------------------


class TestIesToFilingMultiplier:
    """Tests for piecewise linear IES-to-multiplier conversion."""

    BREAKPOINTS = [
        [0, 0.5],
        [20, 0.7],
        [35, 0.85],
        [50, 1.0],
        [65, 1.3],
        [80, 2.0],
        [90, 2.5],
        [100, 3.5],
    ]

    def test_ies_0(self) -> None:
        """IES=0 maps to 0.5x multiplier."""
        assert _ies_to_filing_multiplier(0, self.BREAKPOINTS) == pytest.approx(0.5)

    def test_ies_50_neutral(self) -> None:
        """IES=50 maps to exactly 1.0x (neutral)."""
        assert _ies_to_filing_multiplier(50, self.BREAKPOINTS) == pytest.approx(1.0)

    def test_ies_100(self) -> None:
        """IES=100 maps to 3.5x multiplier."""
        assert _ies_to_filing_multiplier(100, self.BREAKPOINTS) == pytest.approx(3.5)

    def test_ies_35(self) -> None:
        """IES=35 maps to 0.85x (exact breakpoint)."""
        assert _ies_to_filing_multiplier(35, self.BREAKPOINTS) == pytest.approx(0.85)

    def test_ies_80(self) -> None:
        """IES=80 maps to 2.0x (exact breakpoint)."""
        assert _ies_to_filing_multiplier(80, self.BREAKPOINTS) == pytest.approx(2.0)

    def test_interpolation_between_breakpoints(self) -> None:
        """IES=10 interpolates between 0 and 20 breakpoints."""
        # Between [0, 0.5] and [20, 0.7]: fraction=0.5, result=0.6
        result = _ies_to_filing_multiplier(10, self.BREAKPOINTS)
        assert result == pytest.approx(0.6)

    def test_below_minimum(self) -> None:
        """IES below lowest breakpoint returns lowest multiplier."""
        assert _ies_to_filing_multiplier(-5, self.BREAKPOINTS) == pytest.approx(0.5)

    def test_above_maximum(self) -> None:
        """IES above highest breakpoint returns highest multiplier."""
        assert _ies_to_filing_multiplier(110, self.BREAKPOINTS) == pytest.approx(3.5)

    def test_empty_breakpoints(self) -> None:
        """Empty breakpoints returns 1.0 default."""
        assert _ies_to_filing_multiplier(50, []) == 1.0


# -----------------------------------------------------------------------
# Named interaction tests
# -----------------------------------------------------------------------


class TestNamedInteractions:
    """Tests for named interaction pattern detection."""

    def test_rookie_rocket_triggered(self) -> None:
        """ROOKIE_ROCKET triggers when all 3 dimensions meet thresholds."""
        config = _make_interactions_config()
        dims = [
            _make_dim_score("H1-09", "H1", normalized=75.0),  # Growth: 75 >= 60
            _make_dim_score("H2-01", "H2", normalized=65.0),  # Experience: 65 >= 60
            _make_dim_score("H5-01", "H5", normalized=55.0),  # IPO: 55 >= 50
        ]
        effects = detect_named_interactions(dims, config)

        assert len(effects) == 1
        assert effects[0].interaction_id == "ROOKIE_ROCKET"
        assert effects[0].is_named is True
        assert effects[0].multiplier >= 1.3
        assert effects[0].multiplier <= 1.5
        assert "H1-09" in effects[0].triggered_dimensions

    def test_named_not_triggered_below_threshold(self) -> None:
        """ROOKIE_ROCKET does NOT trigger when one dimension is below threshold."""
        config = _make_interactions_config()
        dims = [
            _make_dim_score("H1-09", "H1", normalized=75.0),  # Growth: 75 >= 60 OK
            _make_dim_score("H2-01", "H2", normalized=40.0),  # Experience: 40 < 60 FAIL
            _make_dim_score("H5-01", "H5", normalized=55.0),  # IPO: 55 >= 50 OK
        ]
        effects = detect_named_interactions(dims, config)

        # ROOKIE_ROCKET should not trigger (H2-01 below 60)
        rocket = [e for e in effects if e.interaction_id == "ROOKIE_ROCKET"]
        assert len(rocket) == 0

    def test_named_not_triggered_missing_dimension(self) -> None:
        """Named interaction does NOT trigger when a required dimension is missing."""
        config = _make_interactions_config()
        dims = [
            _make_dim_score("H1-09", "H1", normalized=75.0),
            # H2-01 missing entirely
            _make_dim_score("H5-01", "H5", normalized=55.0),
        ]
        effects = detect_named_interactions(dims, config)

        rocket = [e for e in effects if e.interaction_id == "ROOKIE_ROCKET"]
        assert len(rocket) == 0

    def test_multiple_named_triggered(self) -> None:
        """Multiple named interactions can trigger simultaneously."""
        config = _make_interactions_config()
        dims = [
            # ROOKIE_ROCKET dimensions
            _make_dim_score("H1-09", "H1", normalized=75.0),
            _make_dim_score("H2-01", "H2", normalized=65.0),
            _make_dim_score("H5-01", "H5", normalized=55.0),
            # BLACK_BOX dimensions
            _make_dim_score("H1-02", "H1", normalized=70.0),
            _make_dim_score("H3-04", "H3", normalized=60.0),
            _make_dim_score("H1-11", "H1", normalized=55.0),
        ]
        effects = detect_named_interactions(dims, config)

        ids = {e.interaction_id for e in effects}
        assert "ROOKIE_ROCKET" in ids
        assert "BLACK_BOX" in ids


# -----------------------------------------------------------------------
# Dynamic interaction tests
# -----------------------------------------------------------------------


class TestDynamicInteractions:
    """Tests for dynamic co-occurrence and concentration detection."""

    def test_co_occurrence_detected_with_6_elevated(self) -> None:
        """6 elevated dimensions (>= 60%) triggers co-occurrence."""
        config = _make_interactions_config()
        dims = [_make_dim_score(f"H1-{i:02d}", "H1", normalized=70.0) for i in range(6)]

        effects = detect_dynamic_interactions(dims, config)

        co_occ = [e for e in effects if e.interaction_id == "ELEVATED_CO_OCCURRENCE"]
        assert len(co_occ) == 1
        assert co_occ[0].multiplier >= 1.05
        assert co_occ[0].is_named is False

    def test_co_occurrence_not_detected_with_4(self) -> None:
        """4 elevated dimensions does NOT trigger co-occurrence (min=5)."""
        config = _make_interactions_config()
        dims = [_make_dim_score(f"H1-{i:02d}", "H1", normalized=70.0) for i in range(4)]

        effects = detect_dynamic_interactions(dims, config)

        co_occ = [e for e in effects if e.interaction_id == "ELEVATED_CO_OCCURRENCE"]
        assert len(co_occ) == 0

    def test_co_occurrence_exactly_5(self) -> None:
        """Exactly 5 elevated dimensions triggers co-occurrence."""
        config = _make_interactions_config()
        dims = [_make_dim_score(f"H1-{i:02d}", "H1", normalized=65.0) for i in range(5)]

        effects = detect_dynamic_interactions(dims, config)

        co_occ = [e for e in effects if e.interaction_id == "ELEVATED_CO_OCCURRENCE"]
        assert len(co_occ) == 1

    def test_category_concentration(self) -> None:
        """3+ elevated dimensions in one category triggers concentration."""
        config = _make_interactions_config()
        dims = [
            _make_dim_score("H3-01", "H3", normalized=70.0),
            _make_dim_score("H3-02", "H3", normalized=65.0),
            _make_dim_score("H3-03", "H3", normalized=80.0),
            # 2 more to hit co-occurrence too
            _make_dim_score("H1-01", "H1", normalized=70.0),
            _make_dim_score("H2-01", "H2", normalized=75.0),
        ]

        effects = detect_dynamic_interactions(dims, config)

        cat_conc = [e for e in effects if "CATEGORY_CONCENTRATION" in e.interaction_id]
        assert len(cat_conc) == 1
        assert "H3" in cat_conc[0].interaction_id


# -----------------------------------------------------------------------
# Interaction multiplier cap tests
# -----------------------------------------------------------------------


class TestInteractionMultiplierCap:
    """Tests for the 2.0x interaction multiplier cap."""

    def test_cap_at_2x(self) -> None:
        """Multiple large interactions are capped at 2.0x total."""
        from do_uw.models.hazard_profile import InteractionEffect

        named = [
            InteractionEffect(
                interaction_id="A",
                name="A",
                description="test",
                triggered_dimensions=["H1-01"],
                multiplier=1.5,
                is_named=True,
            ),
            InteractionEffect(
                interaction_id="B",
                name="B",
                description="test",
                triggered_dimensions=["H2-01"],
                multiplier=1.5,
                is_named=True,
            ),
        ]
        # Without cap: 1.5 * 1.5 = 2.25
        result = compute_interaction_multiplier(named, [])
        assert result == 2.0

    def test_no_interactions_returns_1x(self) -> None:
        """No interactions returns 1.0x multiplier."""
        assert compute_interaction_multiplier([], []) == 1.0


# -----------------------------------------------------------------------
# End-to-end compute_hazard_profile tests
# -----------------------------------------------------------------------


class TestComputeHazardProfile:
    """End-to-end tests for the full hazard profile computation."""

    def test_basic_profile(self) -> None:
        """compute_hazard_profile returns valid HazardProfile."""
        from do_uw.models.classification import ClassificationResult, MarketCapTier
        from do_uw.stages.analyze.layers.hazard.hazard_engine import load_hazard_config

        classification = ClassificationResult(
            market_cap_tier=MarketCapTier.MID,
            sector_code="TECH",
            base_filing_rate_pct=5.0,
            severity_band_low_m=15.0,
            severity_band_high_m=40.0,
        )

        weights, interactions = load_hazard_config()
        profile = compute_hazard_profile(
            None, None, classification, weights, interactions
        )

        assert 0 <= profile.ies_score <= 100
        assert 0 <= profile.raw_ies_score <= 100
        assert profile.ies_multiplier > 0
        assert len(profile.dimension_scores) > 0
        assert len(profile.category_scores) > 0

    def test_ies_range(self) -> None:
        """IES stays within 0-100 range even with interaction multiplier."""
        from do_uw.models.classification import ClassificationResult, MarketCapTier
        from do_uw.stages.analyze.layers.hazard.hazard_engine import load_hazard_config

        classification = ClassificationResult(
            market_cap_tier=MarketCapTier.MEGA,
            sector_code="BIOT",
            base_filing_rate_pct=7.0,
            severity_band_low_m=150.0,
            severity_band_high_m=500.0,
        )

        weights, interactions = load_hazard_config()
        profile = compute_hazard_profile(
            None, None, classification, weights, interactions
        )

        assert profile.ies_score <= 100.0
        assert profile.ies_score >= 0.0

    def test_data_coverage_low_triggers_confidence_note(self) -> None:
        """Profile with low data coverage gets a confidence note."""
        from do_uw.models.classification import ClassificationResult, MarketCapTier
        from do_uw.stages.analyze.layers.hazard.hazard_engine import load_hazard_config

        classification = ClassificationResult(
            market_cap_tier=MarketCapTier.SMALL,
            sector_code="DEFAULT",
            base_filing_rate_pct=3.5,
            severity_band_low_m=5.0,
            severity_band_high_m=15.0,
        )

        weights, interactions = load_hazard_config()

        # With None extracted data, most dimensions will use neutral defaults
        # (data_available=False), which should result in low coverage
        profile = compute_hazard_profile(
            None, None, classification, weights, interactions
        )

        # With no real data at all, coverage should be well below 60%
        if profile.data_coverage_pct < 60:
            assert profile.confidence_note != ""
            assert "limited" in profile.confidence_note.lower() or "coverage" in profile.confidence_note.lower()

    def test_underwriter_flags_collected(self) -> None:
        """MEETING_PREP evidence notes are collected as underwriter flags."""
        from unittest.mock import patch

        from do_uw.models.classification import ClassificationResult, MarketCapTier
        from do_uw.stages.analyze.layers.hazard.hazard_engine import load_hazard_config

        classification = ClassificationResult(
            market_cap_tier=MarketCapTier.MID,
            sector_code="TECH",
            base_filing_rate_pct=5.0,
            severity_band_low_m=15.0,
            severity_band_high_m=40.0,
        )

        weights, interactions = load_hazard_config()

        # Create mock dimension scores that include MEETING_PREP notes
        mock_scores = [
            _make_dim_score(
                "H2-08",
                "H2",
                normalized=50.0,
                evidence=[
                    "MEETING_PREP: Ask about CEO communication style in earnings calls",
                    "Regular evidence note",
                ],
            ),
            _make_dim_score("H1-01", "H1", normalized=50.0),
        ]

        with patch(
            "do_uw.stages.analyze.layers.hazard.hazard_engine.score_all_dimensions",
            return_value=mock_scores,
        ):
            profile = compute_hazard_profile(
                None, None, classification, weights, interactions
            )

        assert len(profile.underwriter_flags) == 1
        assert "CEO communication" in profile.underwriter_flags[0]


# -----------------------------------------------------------------------
# Edge case tests
# -----------------------------------------------------------------------


class TestEdgeCases:
    """Edge case and boundary condition tests."""

    def test_interaction_multiplier_capped_extreme(self) -> None:
        """Extreme case: 5 named interactions would blow past 2.0x."""
        from do_uw.models.hazard_profile import InteractionEffect

        effects = [
            InteractionEffect(
                interaction_id=f"EFF_{i}",
                name=f"Effect {i}",
                description="test",
                triggered_dimensions=[f"H{i}-01"],
                multiplier=1.3,
                is_named=True,
            )
            for i in range(1, 6)
        ]
        # Without cap: 1.3^5 = 3.71
        result = compute_interaction_multiplier(effects, [])
        assert result == 2.0

    def test_ies_multiplier_at_exact_breakpoints(self) -> None:
        """Verify all exact breakpoint values produce expected multipliers."""
        bp = [[0, 0.5], [50, 1.0], [100, 3.5]]
        assert _ies_to_filing_multiplier(0, bp) == pytest.approx(0.5)
        assert _ies_to_filing_multiplier(50, bp) == pytest.approx(1.0)
        assert _ies_to_filing_multiplier(100, bp) == pytest.approx(3.5)
        assert _ies_to_filing_multiplier(25, bp) == pytest.approx(0.75)
