"""Tests for relocated analytical functions in benchmark/."""

from __future__ import annotations

import pytest

from do_uw.stages.benchmark.risk_levels import (
    dim_score_threat,
    score_to_risk_level,
    score_to_threat_label,
)


# ---------------------------------------------------------------------------
# score_to_risk_level tests
# ---------------------------------------------------------------------------


class TestScoreToRiskLevel:
    """Test quality score -> risk level mapping."""

    def test_excellent_score(self) -> None:
        assert score_to_risk_level(90) == "LOW"

    def test_good_score(self) -> None:
        assert score_to_risk_level(75) == "MODERATE"

    def test_moderate_score(self) -> None:
        assert score_to_risk_level(55) == "ELEVATED"

    def test_concerning_score(self) -> None:
        assert score_to_risk_level(35) == "HIGH"

    def test_severe_score(self) -> None:
        assert score_to_risk_level(15) == "CRITICAL"

    def test_boundary_86(self) -> None:
        assert score_to_risk_level(86) == "LOW"
        assert score_to_risk_level(85.9) == "MODERATE"

    def test_boundary_71(self) -> None:
        assert score_to_risk_level(71) == "MODERATE"
        assert score_to_risk_level(70.9) == "ELEVATED"

    def test_boundary_51(self) -> None:
        assert score_to_risk_level(51) == "ELEVATED"
        assert score_to_risk_level(50.9) == "HIGH"

    def test_boundary_26(self) -> None:
        assert score_to_risk_level(26) == "HIGH"
        assert score_to_risk_level(25.9) == "CRITICAL"

    def test_zero(self) -> None:
        assert score_to_risk_level(0) == "CRITICAL"

    def test_100(self) -> None:
        assert score_to_risk_level(100) == "LOW"


# ---------------------------------------------------------------------------
# score_to_threat_label tests
# ---------------------------------------------------------------------------


class TestScoreToThreatLabel:
    """Test AI risk composite score -> threat label mapping."""

    def test_high_score(self) -> None:
        assert score_to_threat_label(80) == "HIGH"

    def test_medium_score(self) -> None:
        assert score_to_threat_label(50) == "ELEVATED"

    def test_low_score(self) -> None:
        assert score_to_threat_label(20) == "MODERATE"

    def test_boundary_70(self) -> None:
        assert score_to_threat_label(70) == "HIGH"
        assert score_to_threat_label(69.9) == "ELEVATED"

    def test_boundary_40(self) -> None:
        assert score_to_threat_label(40) == "ELEVATED"
        assert score_to_threat_label(39.9) == "MODERATE"

    def test_zero(self) -> None:
        assert score_to_threat_label(0) == "MODERATE"


# ---------------------------------------------------------------------------
# dim_score_threat tests
# ---------------------------------------------------------------------------


class TestDimScoreThreat:
    """Test AI risk sub-dimension score -> threat level mapping."""

    def test_high_dim(self) -> None:
        assert dim_score_threat(8.0) == "HIGH"

    def test_elevated_dim(self) -> None:
        assert dim_score_threat(5.0) == "ELEVATED"

    def test_moderate_dim(self) -> None:
        assert dim_score_threat(2.0) == "MODERATE"

    def test_boundary_7(self) -> None:
        assert dim_score_threat(7.0) == "HIGH"
        assert dim_score_threat(6.9) == "ELEVATED"

    def test_boundary_4(self) -> None:
        assert dim_score_threat(4.0) == "ELEVATED"
        assert dim_score_threat(3.9) == "MODERATE"

    def test_zero(self) -> None:
        assert dim_score_threat(0) == "MODERATE"


# ---------------------------------------------------------------------------
# Narrative builder smoke tests
# ---------------------------------------------------------------------------


class TestBuildThesisNarrative:
    """Smoke test: build_thesis_narrative returns non-empty string."""

    def test_returns_non_empty_for_minimal_state(self) -> None:
        from do_uw.models.state import AnalysisState

        state = AnalysisState(ticker="TEST")
        from do_uw.stages.benchmark.narrative_helpers import (
            build_thesis_narrative,
        )

        result = build_thesis_narrative(state)
        assert isinstance(result, str)
        assert len(result) > 0


class TestBuildRiskNarrative:
    """Smoke test: build_risk_narrative returns non-empty string."""

    def test_returns_non_empty_for_minimal_input(self) -> None:
        from do_uw.models.executive_summary import InherentRiskBaseline
        from do_uw.models.state import AnalysisState

        risk = InherentRiskBaseline(
            sector_base_rate_pct=4.0,
            market_cap_multiplier=1.2,
            market_cap_adjusted_rate_pct=4.8,
            score_multiplier=1.5,
            company_adjusted_rate_pct=7.2,
            sector_name="Technology",
            market_cap_tier="LARGE",
        )
        state = AnalysisState(ticker="TEST")
        from do_uw.stages.benchmark.narrative_helpers import (
            build_risk_narrative,
        )

        result = build_risk_narrative(risk, state)
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Technology" in result


# ---------------------------------------------------------------------------
# Backward compatibility tests
# ---------------------------------------------------------------------------


class TestBackwardCompat:
    """Verify re-exports from render/ still work."""

    def test_sect1_helpers_reexports(self) -> None:
        from do_uw.stages.render.sections.sect1_helpers import (
            build_claim_narrative,
            build_risk_narrative,
            build_thesis_narrative,
            market_cap_decile,
        )

        # Verify they are callable
        assert callable(build_thesis_narrative)
        assert callable(build_risk_narrative)
        assert callable(build_claim_narrative)
        assert callable(market_cap_decile)

    def test_sect7_score_to_risk_level_alias(self) -> None:
        from do_uw.stages.render.sections.sect7_scoring import (
            _score_to_risk_level,
        )

        assert _score_to_risk_level(90) == "LOW"
        assert _score_to_risk_level(50) == "HIGH"

    def test_sect8_threat_label_aliases(self) -> None:
        from do_uw.stages.render.sections.sect8_ai_risk import (
            _dim_score_threat,
            _score_to_threat_label,
        )

        assert _score_to_threat_label(80) == "HIGH"
        assert _dim_score_threat(8.0) == "HIGH"
