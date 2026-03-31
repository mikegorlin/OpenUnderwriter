"""Comprehensive tests for BMOD (Business Model) signal evaluation.

Tests cover all 6 business model dimensions: revenue type, concentration risk,
key person dependency, lifecycle risk, disruption risk, and segment margins.
Validates field resolution, signal evaluation, and context builder output.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest

from do_uw.brain.field_registry import _reset_cache
from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.company import CompanyIdentity, CompanyProfile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW = datetime.now(tz=timezone.utc)


def _sv(val: Any, src: str = "test", conf: Confidence = Confidence.MEDIUM) -> SourcedValue:
    """Create a SourcedValue with default metadata."""
    return SourcedValue(value=val, source=src, confidence=conf, as_of=_NOW)


def _make_company(**kwargs: Any) -> CompanyProfile:
    """Build a CompanyProfile with sensible defaults and custom overrides."""
    defaults: dict[str, Any] = {"identity": CompanyIdentity(ticker="TEST")}
    defaults.update(kwargs)
    return CompanyProfile(**defaults)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clear_registry_cache() -> None:
    """Clear field registry cache before each test."""
    _reset_cache()


@pytest.fixture()
def concentrated_company() -> CompanyProfile:
    """Company with high concentration across all 3 dimensions."""
    return _make_company(
        revenue_model_type=_sv("TRANSACTION"),
        revenue_segments=[
            _sv({"name": "Core", "percentage": 80.0, "revenue": 8000}),
            _sv({"name": "Other", "percentage": 20.0, "revenue": 2000}),
        ],
        customer_concentration=[
            _sv({"customer": "BigCo", "revenue_pct": 25.0}),
            _sv({"customer": "MedCo", "revenue_pct": 8.0}),
        ],
        geographic_footprint=[
            _sv({"region": "US", "percentage": 85.0}),
            _sv({"region": "Europe", "percentage": 15.0}),
        ],
        key_person_risk=_sv({
            "is_founder_led": True, "ceo_tenure_years": 20,
            "has_succession_plan": False, "risk_score": 3,
        }),
        disruption_risk=_sv({
            "level": "HIGH", "threats": ["AI", "Regulation", "Competition"],
            "threat_count": 3,
        }),
        segment_lifecycle=[
            _sv({"name": "Core", "stage": "DECLINING", "growth_rate": -8.0, "revenue": 8000}),
            _sv({"name": "Other", "stage": "GROWTH", "growth_rate": 15.0, "revenue": 2000}),
        ],
        segment_margins=[
            _sv({"name": "Core", "margin_pct": 15.0, "prior_margin_pct": 22.0, "change_bps": -700}),
            _sv({"name": "Other", "margin_pct": 30.0, "prior_margin_pct": 28.0, "change_bps": 200}),
        ],
    )


@pytest.fixture()
def diversified_company() -> CompanyProfile:
    """Company with low concentration, professional management, stable margins."""
    return _make_company(
        revenue_model_type=_sv("RECURRING"),
        revenue_segments=[
            _sv({"name": "A", "percentage": 35.0, "revenue": 3500}),
            _sv({"name": "B", "percentage": 35.0, "revenue": 3500}),
            _sv({"name": "C", "percentage": 30.0, "revenue": 3000}),
        ],
        customer_concentration=[
            _sv({"customer": "Cust1", "revenue_pct": 5.0}),
            _sv({"customer": "Cust2", "revenue_pct": 4.0}),
        ],
        geographic_footprint=[
            _sv({"region": "US", "percentage": 35.0}),
            _sv({"region": "Europe", "percentage": 35.0}),
            _sv({"region": "Asia", "percentage": 30.0}),
        ],
        key_person_risk=_sv({
            "is_founder_led": False, "ceo_tenure_years": 3,
            "has_succession_plan": True, "risk_score": 0,
        }),
        disruption_risk=_sv({
            "level": "LOW", "threats": [], "threat_count": 0,
        }),
        segment_lifecycle=[
            _sv({"name": "A", "stage": "GROWTH", "growth_rate": 12.0, "revenue": 3500}),
            _sv({"name": "B", "stage": "MATURE", "growth_rate": 3.0, "revenue": 3500}),
            _sv({"name": "C", "stage": "GROWTH", "growth_rate": 8.0, "revenue": 3000}),
        ],
        segment_margins=[
            _sv({"name": "A", "margin_pct": 25.0, "prior_margin_pct": 24.0, "change_bps": 100}),
            _sv({"name": "B", "margin_pct": 20.0, "prior_margin_pct": 20.5, "change_bps": -50}),
        ],
    )


# ---------------------------------------------------------------------------
# Test 1-2: Revenue model type evaluation
# ---------------------------------------------------------------------------


class TestRevenueModelType:
    """BIZ.MODEL.revenue_type signal evaluation."""

# ---------------------------------------------------------------------------
# Test 3-4: Concentration risk composite
# ---------------------------------------------------------------------------


class TestConcentrationRisk:
    """BIZ.MODEL.concentration_risk signal evaluation."""

    def test_high_score_when_all_concentrated(self, concentrated_company: CompanyProfile) -> None:
        """Score should be 3 when all 3 dimensions are concentrated."""
        from do_uw.stages.analyze.declarative_mapper import resolve_field

        val, _, _ = resolve_field("concentration_risk_composite", None, concentrated_company)
        assert val == 3

    def test_zero_score_when_diversified(self, diversified_company: CompanyProfile) -> None:
        """Score should be 0 when well-diversified."""
        from do_uw.stages.analyze.declarative_mapper import resolve_field

        val, _, _ = resolve_field("concentration_risk_composite", None, diversified_company)
        assert val == 0

    def test_partial_concentration(self) -> None:
        """Score should reflect partial concentration (1 dimension only)."""
        from do_uw.stages.analyze.declarative_mapper import resolve_field

        company = _make_company(
            revenue_segments=[_sv({"name": "Main", "percentage": 60.0})],
            customer_concentration=[_sv({"customer": "Small", "revenue_pct": 3.0})],
            geographic_footprint=[_sv({"region": "US", "percentage": 30.0})],
        )
        val, _, _ = resolve_field("concentration_risk_composite", None, company)
        assert val == 1  # Only segment > 50%

    def test_empty_data_returns_zero(self) -> None:
        """Score should be 0 with no concentration data."""
        from do_uw.stages.analyze.declarative_mapper import resolve_field

        company = _make_company()
        val, _, _ = resolve_field("concentration_risk_composite", None, company)
        assert val == 0


# ---------------------------------------------------------------------------
# Test 5-6: Key person risk score
# ---------------------------------------------------------------------------


class TestKeyPersonRisk:
    """BIZ.MODEL.key_person signal evaluation."""

    def test_high_risk_founder_led(self, concentrated_company: CompanyProfile) -> None:
        """Score 3 for founder-led, long tenure, no succession."""
        from do_uw.stages.analyze.declarative_mapper import resolve_field

        val, _, _ = resolve_field("key_person_risk_score", None, concentrated_company)
        assert val == 3

    def test_low_risk_professional_management(self, diversified_company: CompanyProfile) -> None:
        """Score 0 for professional management with succession plan."""
        from do_uw.stages.analyze.declarative_mapper import resolve_field

        val, _, _ = resolve_field("key_person_risk_score", None, diversified_company)
        assert val == 0

    def test_missing_data_returns_none(self) -> None:
        """No key person data -> None (signal SKIPPED)."""
        from do_uw.stages.analyze.declarative_mapper import resolve_field

        company = _make_company()
        val, _, _ = resolve_field("key_person_risk_score", None, company)
        assert val is None


# ---------------------------------------------------------------------------
# Test 7: Disruption risk level
# ---------------------------------------------------------------------------


class TestDisruptionRisk:
    """BIZ.MODEL.disruption signal evaluation."""

# ---------------------------------------------------------------------------
# Test 8: Segment margin risk
# ---------------------------------------------------------------------------


class TestSegmentMarginRisk:
    """BIZ.MODEL.segment_margins signal evaluation."""

    def test_stable_margins_are_clear(self, diversified_company: CompanyProfile) -> None:
        """Stable margins (decline <200bps) should be CLEAR."""
        from do_uw.stages.analyze.declarative_mapper import resolve_field

        val, _, _ = resolve_field("segment_margin_risk", None, diversified_company)
        assert val == 50.0  # B has -50bps decline

    def test_no_margin_data_returns_none(self) -> None:
        """No segment margin data -> None (SKIPPED)."""
        from do_uw.stages.analyze.declarative_mapper import resolve_field

        company = _make_company()
        val, _, _ = resolve_field("segment_margin_risk", None, company)
        assert val is None


# ---------------------------------------------------------------------------
# Test 9: Segment lifecycle risk
# ---------------------------------------------------------------------------


class TestSegmentLifecycleRisk:
    """BIZ.MODEL.lifecycle signal evaluation."""

    def test_declining_segments_compute_correctly(
        self, concentrated_company: CompanyProfile,
    ) -> None:
        """80% from declining segment -> 80% lifecycle risk."""
        from do_uw.stages.analyze.declarative_mapper import resolve_field

        val, _, _ = resolve_field("segment_lifecycle_risk", None, concentrated_company)
        assert val == 80.0  # Core=8000 DECLINING / total=10000

    def test_no_declining_segments(self, diversified_company: CompanyProfile) -> None:
        """All growth/mature segments -> 0% lifecycle risk."""
        from do_uw.stages.analyze.declarative_mapper import resolve_field

        val, _, _ = resolve_field("segment_lifecycle_risk", None, diversified_company)
        assert val == 0.0

    def test_no_lifecycle_data(self) -> None:
        """No lifecycle data -> None."""
        from do_uw.stages.analyze.declarative_mapper import resolve_field

        company = _make_company()
        val, _, _ = resolve_field("segment_lifecycle_risk", None, company)
        assert val is None


# ---------------------------------------------------------------------------
# Test 10: Context builder extract_business_model()
# ---------------------------------------------------------------------------


class TestExtractBusinessModel:
    """extract_business_model() context builder produces complete output."""

    def test_complete_output_keys(self, concentrated_company: CompanyProfile) -> None:
        """Output dict has all expected keys."""
        from do_uw.models.state import AnalysisState

        from do_uw.stages.render.context_builders.company import extract_business_model

        state = AnalysisState(ticker="TEST")
        state.company = concentrated_company
        result = extract_business_model(state)

        expected_keys = {
            "revenue_model_type", "concentration_score", "concentration_level",
            "concentration_flags", "key_person", "lifecycle", "disruption",
            "segment_margins",
        }
        assert set(result.keys()) == expected_keys

    def test_values_populated(self, concentrated_company: CompanyProfile) -> None:
        """All values populated from concentrated company data."""
        from do_uw.models.state import AnalysisState

        from do_uw.stages.render.context_builders.company import extract_business_model

        state = AnalysisState(ticker="TEST")
        state.company = concentrated_company
        result = extract_business_model(state)

        assert result["revenue_model_type"] == "TRANSACTION"
        assert result["concentration_score"] == 3
        assert result["concentration_level"] == "HIGH"
        assert len(result["concentration_flags"]) == 3
        assert result["key_person"]["risk_score"] == 3
        assert result["key_person"]["risk_level"] == "HIGH"
        assert len(result["lifecycle"]) == 2
        assert result["disruption"]["level"] == "HIGH"
        assert len(result["segment_margins"]) == 2

    def test_empty_company_returns_empty(self) -> None:
        """No company data -> empty dict."""
        from do_uw.models.state import AnalysisState

        from do_uw.stages.render.context_builders.company import extract_business_model

        state = AnalysisState(ticker="TEST")
        result = extract_business_model(state)
        assert result == {}

    def test_minimal_company(self) -> None:
        """Company with no BMOD data produces dict with None/empty values."""
        from do_uw.models.state import AnalysisState

        from do_uw.stages.render.context_builders.company import extract_business_model

        state = AnalysisState(ticker="TEST")
        state.company = _make_company()
        result = extract_business_model(state)

        assert result["revenue_model_type"] is None
        assert result["concentration_score"] == 0
        assert result["concentration_level"] == "NONE"
        assert result["key_person"] is None
        assert result["lifecycle"] == []
        assert result["disruption"] is None
        assert result["segment_margins"] == []

    def test_business_model_in_extract_company(
        self, concentrated_company: CompanyProfile,
    ) -> None:
        """extract_company() includes business_model key."""
        from do_uw.models.state import AnalysisState

        from do_uw.stages.render.context_builders.company import extract_company

        state = AnalysisState(ticker="TEST")
        state.company = concentrated_company
        result = extract_company(state)

        assert "business_model" in result
        assert result["business_model"]["revenue_model_type"] == "TRANSACTION"
