"""Tests for sector risk classification extraction.

Phase 98: Tests for extract_sector_signals() and its component functions.
Covers GICS sub-industry lookup, sector fallback, SIC fallback, and defaults.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from do_uw.stages.extract.sector_classification import (
    extract_sector_signals,
    _compute_hazard_tier,
    _compute_claim_patterns,
    _compute_regulatory_overlay,
    _compute_peer_comparison,
)


def _make_state(
    gics_code: str | None = None,
    sic_code: str | None = None,
    composite_score: float | None = None,
    governance_total: float | None = None,
) -> MagicMock:
    """Create a minimal mock AnalysisState for sector tests."""
    state = MagicMock()

    # company.gics_code is SourcedValue[str] | None
    if gics_code is not None:
        gics_sv = MagicMock()
        gics_sv.value = gics_code
        state.company.gics_code = gics_sv
    else:
        state.company.gics_code = None

    # company.identity.sic_code is SourcedValue[str] | None
    if sic_code is not None:
        sic_sv = MagicMock()
        sic_sv.value = sic_code
        state.company.identity.sic_code = sic_sv
    else:
        state.company.identity.sic_code = None

    # scoring.composite_score
    if composite_score is not None:
        state.scoring.composite_score = composite_score
    else:
        state.scoring = None

    # extracted.governance.governance_score.total_score
    if governance_total is not None:
        total_sv = MagicMock()
        total_sv.value = governance_total
        state.extracted.governance.governance_score.total_score = total_sv
    else:
        state.extracted.governance = None

    # extracted.financials - leave None for simplicity
    state.extracted.financials = None

    return state


class TestHazardTier:
    """Tests for _compute_hazard_tier()."""

    def test_gics_sub_industry_match(self) -> None:
        """Known GICS sub-industry code maps to correct tier."""
        # 35203010 = Biotechnology -> Highest
        result = _compute_hazard_tier("35203010", None)
        assert result["tier"] == "Highest"
        assert result["filing_rate"] > 15
        assert "context" in result

    def test_gics_sector_fallback(self) -> None:
        """Unknown sub-industry falls back to GICS sector-level tier."""
        # 45999999 - not a real sub-industry, but sector 45 = IT -> High
        result = _compute_hazard_tier("45999999", None)
        assert result["tier"] == "High"
        assert "context" in result

    def test_sic_fallback(self) -> None:
        """When GICS is None, derives tier from SIC code via sic_gics_mapping."""
        # SIC 2836 maps to GICS 35203010 (Biotechnology) -> Highest
        result = _compute_hazard_tier(None, "2836")
        assert result["tier"] == "Highest"

    def test_no_match_default(self) -> None:
        """Completely unknown codes return Moderate default."""
        result = _compute_hazard_tier(None, None)
        assert result["tier"] == "Moderate"
        assert "default" in result.get("context", "").lower() or result["tier"] == "Moderate"

    def test_sic_fallback_sector_level(self) -> None:
        """SIC code that maps to a GICS code not in sub-industry tiers
        still falls back to sector-level."""
        # SIC 4911 -> GICS 55101010 (Electric Utilities) -> Lower
        result = _compute_hazard_tier(None, "4911")
        assert result["tier"] == "Lower"


class TestClaimPatterns:
    """Tests for _compute_claim_patterns()."""

    def test_known_industry_group(self) -> None:
        """Known GICS industry group returns claim theories."""
        # 3520 = Pharmaceuticals, Biotechnology & Life Sciences
        result = _compute_claim_patterns("35201010")
        assert "claim_theories" in result
        assert len(result["claim_theories"]) == 3
        assert "theory" in result["claim_theories"][0]

    def test_unknown_group_empty(self) -> None:
        """Unknown industry group returns empty list."""
        result = _compute_claim_patterns("99999999")
        assert result["claim_theories"] == []

    def test_claim_theory_structure(self) -> None:
        """Each claim theory has required fields."""
        result = _compute_claim_patterns("45100000")  # 4510 = Software & Services
        if result["claim_theories"]:
            theory = result["claim_theories"][0]
            assert "theory" in theory
            assert "legal_basis" in theory
            assert "frequency" in theory


class TestRegulatoryOverlay:
    """Tests for _compute_regulatory_overlay()."""

    def test_known_group_returns_regulators(self) -> None:
        """Known GICS industry group returns regulators and intensity."""
        # 3520 = Pharmaceuticals, Biotechnology & Life Sciences -> High
        result = _compute_regulatory_overlay("35201010")
        assert result["intensity"] in ("High", "Moderate", "Low")
        assert isinstance(result["regulators"], list)
        assert len(result["regulators"]) > 0
        assert "trend" in result

    def test_unknown_group_defaults(self) -> None:
        """Unknown industry group returns low-intensity defaults."""
        result = _compute_regulatory_overlay("99999999")
        assert result["intensity"] == "Low"
        assert result["regulators"] == []

    def test_high_intensity_group(self) -> None:
        """Pharma/biotech has High regulatory intensity."""
        result = _compute_regulatory_overlay("35203010")  # Biotech -> group 3520
        assert result["intensity"] == "High"
        assert "FDA" in result["regulators"]


class TestPeerComparison:
    """Tests for _compute_peer_comparison()."""

    def test_outlier_detection(self) -> None:
        """Company score far above sector median flagged as outlier."""
        # IT sector: overall median=62, std_dev=15
        # Score 90 is (90-62)/15 = 1.87 std devs -> outlier
        result = _compute_peer_comparison(
            gics_code="45103010",
            company_score=90.0,
            governance_score=None,
            financial_health=None,
        )
        assert result["outlier_count"] >= 1
        assert "overall_score" in [d["dimension"] for d in result["dimensions"]]

    def test_no_outliers(self) -> None:
        """Company within normal range shows 0 outliers."""
        # IT sector: overall median=62, std_dev=15
        # Score 65 is (65-62)/15 = 0.2 std devs -> not outlier
        result = _compute_peer_comparison(
            gics_code="45103010",
            company_score=65.0,
            governance_score=64.0,
            financial_health=4.0,
        )
        assert result["outlier_count"] == 0

    def test_no_data_no_outliers(self) -> None:
        """When no company data available, returns 0 outliers."""
        result = _compute_peer_comparison(
            gics_code="45103010",
            company_score=None,
            governance_score=None,
            financial_health=None,
        )
        assert result["outlier_count"] == 0

    def test_unknown_sector_empty(self) -> None:
        """Unknown GICS sector returns 0 outliers with no dimensions."""
        result = _compute_peer_comparison(
            gics_code="99999999",
            company_score=90.0,
            governance_score=None,
            financial_health=None,
        )
        assert result["outlier_count"] == 0


class TestFullExtraction:
    """Integration test for extract_sector_signals()."""

    def test_full_extraction_returns_all_keys(self) -> None:
        """extract_sector_signals returns dict with all 4 field keys."""
        state = _make_state(gics_code="45103010", sic_code="7372", composite_score=75.0)
        result = extract_sector_signals(state)

        assert "sector_hazard_tier" in result
        assert "sector_claim_patterns" in result
        assert "sector_regulatory_overlay" in result
        assert "sector_peer_comparison" in result

        # Hazard tier should have tier key
        assert "tier" in result["sector_hazard_tier"]

        # Claim patterns should have theories
        assert "claim_theories" in result["sector_claim_patterns"]

        # Regulatory overlay should have intensity
        assert "intensity" in result["sector_regulatory_overlay"]

        # Peer comparison should have outlier_count
        assert "outlier_count" in result["sector_peer_comparison"]

    def test_full_extraction_with_none_gics(self) -> None:
        """extract_sector_signals handles None GICS gracefully."""
        state = _make_state(gics_code=None, sic_code="2836")
        result = extract_sector_signals(state)
        assert "sector_hazard_tier" in result
        # SIC 2836 -> Biotech -> Highest
        assert result["sector_hazard_tier"]["tier"] == "Highest"

    def test_full_extraction_with_nothing(self) -> None:
        """extract_sector_signals with no codes returns defaults."""
        state = _make_state(gics_code=None, sic_code=None)
        result = extract_sector_signals(state)
        assert result["sector_hazard_tier"]["tier"] == "Moderate"
