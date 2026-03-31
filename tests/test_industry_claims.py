"""Tests for industry claim patterns extractor (SECT6-10).

Tests SIC range matching, theory loading, contagion risk,
and the main extractor function.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import patch

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.state import AnalysisState
from do_uw.stages.analyze.industry_claims import (
    build_claim_pattern,
    extract_industry_claim_patterns,
    find_matching_industries,
)


def _make_state(sic_code: int | None = None) -> AnalysisState:
    """Create a state with an optional SIC code set."""
    state = AnalysisState(ticker="TEST")
    if sic_code is not None:
        from do_uw.models.company import CompanyIdentity, CompanyProfile

        identity = CompanyIdentity(ticker="TEST")
        identity.sic_code = SourcedValue[str](
            value=str(sic_code),
            source="SEC EDGAR",
            confidence=Confidence.HIGH,
            as_of=datetime.now(tz=UTC),
        )
        state.company = CompanyProfile(identity=identity)
    return state


_MOCK_CONFIG: dict[str, Any] = {
    "industry_theories": {
        "7370-7379": {
            "industry": "Software & SaaS",
            "theories": [
                {
                    "theory": "revenue_recognition",
                    "description": "Premature SaaS revenue recognition",
                    "legal_basis": "10b-5",
                },
                {
                    "theory": "subscriber_metrics",
                    "description": "Inflated user metrics",
                    "legal_basis": "10b-5",
                },
            ],
        },
        "2830-2836": {
            "industry": "Pharmaceuticals",
            "theories": [
                {
                    "theory": "clinical_trial_disclosure",
                    "description": "Failure to disclose adverse results",
                    "legal_basis": "10b-5",
                },
            ],
        },
    }
}


# ---------------------------------------------------------------------------
# SIC range matching tests
# ---------------------------------------------------------------------------


class TestSICRangeMatching:
    """Test SIC code to industry range matching."""

    def test_match_within_range(self) -> None:
        theories = _MOCK_CONFIG["industry_theories"]
        matches = find_matching_industries(7372, theories)
        assert len(matches) == 1
        assert matches[0][0] == "7370-7379"

    def test_match_range_boundary_start(self) -> None:
        theories = _MOCK_CONFIG["industry_theories"]
        matches = find_matching_industries(7370, theories)
        assert len(matches) == 1

    def test_match_range_boundary_end(self) -> None:
        theories = _MOCK_CONFIG["industry_theories"]
        matches = find_matching_industries(7379, theories)
        assert len(matches) == 1

    def test_no_match(self) -> None:
        theories = _MOCK_CONFIG["industry_theories"]
        matches = find_matching_industries(9999, theories)
        assert len(matches) == 0

    def test_multiple_industry_match(self) -> None:
        """Test SIC that could match overlapping ranges."""
        theories_overlap = {
            "7370-7380": {"industry": "A", "theories": []},
            "7375-7385": {"industry": "B", "theories": []},
        }
        matches = find_matching_industries(7377, theories_overlap)
        assert len(matches) == 2


# ---------------------------------------------------------------------------
# Theory loading tests
# ---------------------------------------------------------------------------


class TestBuildClaimPattern:
    """Test building IndustryClaimPattern from config entries."""

    def test_basic_pattern(self) -> None:
        theory = {
            "theory": "revenue_recognition",
            "description": "Premature revenue recognition",
            "legal_basis": "10b-5",
        }
        pattern = build_claim_pattern(theory, "7370-7379", "Software & SaaS")
        assert pattern.legal_theory is not None
        assert pattern.legal_theory.value == "revenue_recognition"
        assert pattern.sic_range is not None
        assert pattern.sic_range.value == "7370-7379"
        assert pattern.this_company_exposed is not None
        assert pattern.this_company_exposed.value is True
        assert pattern.contagion_risk is not None
        assert pattern.contagion_risk.value is True

    def test_description_includes_industry(self) -> None:
        theory = {
            "theory": "test_theory",
            "description": "Some description",
        }
        pattern = build_claim_pattern(theory, "1000-1999", "Mining")
        assert pattern.description is not None
        assert "Mining" in pattern.description.value


# ---------------------------------------------------------------------------
# Main extractor tests
# ---------------------------------------------------------------------------


class TestExtractIndustryClaimPatterns:
    """Test the main extract_industry_claim_patterns function."""

    @patch(
        "do_uw.stages.analyze.industry_claims._load_industry_theories",
        return_value=_MOCK_CONFIG,
    )
    def test_software_sic_matches(self, _mock: Any) -> None:
        state = _make_state(sic_code=7372)
        patterns, report = extract_industry_claim_patterns(state)
        assert len(patterns) == 2
        theories = [
            p.legal_theory.value
            for p in patterns
            if p.legal_theory is not None
        ]
        assert "revenue_recognition" in theories
        assert "subscriber_metrics" in theories
        assert report.coverage_pct >= 60.0

    @patch(
        "do_uw.stages.analyze.industry_claims._load_industry_theories",
        return_value=_MOCK_CONFIG,
    )
    def test_pharma_sic_matches(self, _mock: Any) -> None:
        state = _make_state(sic_code=2833)
        patterns, _report = extract_industry_claim_patterns(state)
        assert len(patterns) == 1
        assert patterns[0].legal_theory is not None
        assert patterns[0].legal_theory.value == "clinical_trial_disclosure"

    @patch(
        "do_uw.stages.analyze.industry_claims._load_industry_theories",
        return_value=_MOCK_CONFIG,
    )
    def test_no_match_returns_empty(self, _mock: Any) -> None:
        state = _make_state(sic_code=9999)
        patterns, report = extract_industry_claim_patterns(state)
        assert len(patterns) == 0
        assert len(report.warnings) >= 1

    def test_no_sic_code_returns_empty(self) -> None:
        state = _make_state(sic_code=None)
        patterns, report = extract_industry_claim_patterns(state)
        assert len(patterns) == 0
        assert len(report.warnings) >= 1

    @patch(
        "do_uw.stages.analyze.industry_claims._load_industry_theories",
        return_value=_MOCK_CONFIG,
    )
    def test_contagion_risk_flagged(self, _mock: Any) -> None:
        state = _make_state(sic_code=7375)
        patterns, _report = extract_industry_claim_patterns(state)
        for pattern in patterns:
            assert pattern.contagion_risk is not None
            assert pattern.contagion_risk.value is True
            assert pattern.contagion_risk.confidence == Confidence.LOW
