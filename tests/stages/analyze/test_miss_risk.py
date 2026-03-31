"""Tests for miss risk computation and SCA relevance mapping.

Tests cover:
- Gap-based miss risk computation (HIGH >10%, MEDIUM 5-10%, LOW <5%)
- Credibility adjustment (+1 for LOW, -1 for HIGH credibility)
- SCA relevance deterministic mapping
- Forward statement enrichment combining miss risk + SCA
- Edge cases: None values, UNKNOWN credibility
"""

from __future__ import annotations

import pytest

from do_uw.models.forward_looking import (
    CredibilityScore,
    ForwardStatement,
)
from do_uw.stages.analyze.miss_risk import (
    compute_miss_risk,
    enrich_forward_statements,
    map_sca_relevance,
)


class TestComputeMissRisk:
    """Tests for compute_miss_risk gap-based algorithm."""

    def test_medium_gap_10_pct(self) -> None:
        """10% gap with MEDIUM credibility returns MEDIUM."""
        result = compute_miss_risk(
            current_value=90.0,
            guidance_midpoint=100.0,
            credibility_level="MEDIUM",
        )
        assert result == "MEDIUM"

    def test_high_gap_15_pct(self) -> None:
        """15% gap with MEDIUM credibility returns HIGH."""
        result = compute_miss_risk(
            current_value=85.0,
            guidance_midpoint=100.0,
            credibility_level="MEDIUM",
        )
        assert result == "HIGH"

    def test_low_gap_3_pct(self) -> None:
        """3% gap with MEDIUM credibility returns LOW."""
        result = compute_miss_risk(
            current_value=97.0,
            guidance_midpoint=100.0,
            credibility_level="MEDIUM",
        )
        assert result == "LOW"

    def test_low_credibility_bumps_medium_to_high(self) -> None:
        """LOW credibility (<50% beat) bumps MEDIUM to HIGH."""
        # 8% gap = MEDIUM base, +1 for LOW credibility = HIGH
        result = compute_miss_risk(
            current_value=92.0,
            guidance_midpoint=100.0,
            credibility_level="LOW",
        )
        assert result == "HIGH"

    def test_high_credibility_bumps_medium_to_low(self) -> None:
        """HIGH credibility (>80% beat) bumps MEDIUM to LOW."""
        # 8% gap = MEDIUM base, -1 for HIGH credibility = LOW
        result = compute_miss_risk(
            current_value=92.0,
            guidance_midpoint=100.0,
            credibility_level="HIGH",
        )
        assert result == "LOW"

    def test_none_current_value_returns_unknown(self) -> None:
        """None current_value returns UNKNOWN."""
        result = compute_miss_risk(
            current_value=None,
            guidance_midpoint=100.0,
            credibility_level="MEDIUM",
        )
        assert result == "UNKNOWN"

    def test_none_guidance_returns_unknown(self) -> None:
        """None guidance_midpoint returns UNKNOWN."""
        result = compute_miss_risk(
            current_value=90.0,
            guidance_midpoint=None,
            credibility_level="MEDIUM",
        )
        assert result == "UNKNOWN"

    def test_both_none_returns_unknown(self) -> None:
        """Both values None returns UNKNOWN."""
        result = compute_miss_risk(
            current_value=None,
            guidance_midpoint=None,
            credibility_level="MEDIUM",
        )
        assert result == "UNKNOWN"

    def test_low_credibility_caps_at_high(self) -> None:
        """LOW credibility on already HIGH base stays at HIGH (cap)."""
        # 20% gap = HIGH base (2), +1 for LOW credibility = still HIGH (capped at 2)
        result = compute_miss_risk(
            current_value=80.0,
            guidance_midpoint=100.0,
            credibility_level="LOW",
        )
        assert result == "HIGH"

    def test_high_credibility_floors_at_low(self) -> None:
        """HIGH credibility on already LOW base stays at LOW (floor)."""
        # 2% gap = LOW base (0), -1 for HIGH credibility = still LOW (floored at 0)
        result = compute_miss_risk(
            current_value=98.0,
            guidance_midpoint=100.0,
            credibility_level="HIGH",
        )
        assert result == "LOW"

    def test_unknown_credibility_no_adjustment(self) -> None:
        """UNKNOWN credibility applies no adjustment."""
        result = compute_miss_risk(
            current_value=92.0,
            guidance_midpoint=100.0,
            credibility_level="UNKNOWN",
        )
        assert result == "MEDIUM"

    def test_exact_5_pct_gap_is_medium(self) -> None:
        """Exactly 5% gap is MEDIUM (threshold is > 5 for MEDIUM)."""
        result = compute_miss_risk(
            current_value=95.0,
            guidance_midpoint=100.0,
            credibility_level="MEDIUM",
        )
        assert result == "MEDIUM"

    def test_exact_10_pct_gap_is_high(self) -> None:
        """Exactly 10% gap boundary: >10 for HIGH."""
        # 10% gap is at the boundary -- should be MEDIUM (not > 10)
        result = compute_miss_risk(
            current_value=90.0,
            guidance_midpoint=100.0,
            credibility_level="MEDIUM",
        )
        assert result == "MEDIUM"


class TestMapScaRelevance:
    """Tests for deterministic SCA relevance mapping."""

    def test_high_miss_material_metric(self) -> None:
        """HIGH miss risk + material metric -> 10b-5 mapping."""
        result = map_sca_relevance(
            miss_risk="HIGH",
            is_material=True,
        )
        assert "10b-5" in result
        assert "misleading forward guidance" in result

    def test_medium_miss_financial_metric(self) -> None:
        """MEDIUM miss risk + financial metric -> earnings fraud theory."""
        result = map_sca_relevance(
            miss_risk="MEDIUM",
            is_financial=True,
        )
        assert "earnings fraud theory" in result.lower() or "Potential earnings fraud theory" in result

    def test_low_miss_no_relevance(self) -> None:
        """LOW miss risk returns empty string (no SCA relevance)."""
        result = map_sca_relevance(miss_risk="LOW")
        assert result == ""

    def test_unknown_miss_no_relevance(self) -> None:
        """UNKNOWN miss risk returns empty string."""
        result = map_sca_relevance(miss_risk="UNKNOWN")
        assert result == ""

    def test_high_miss_financial_metric(self) -> None:
        """HIGH miss risk + financial (not material) metric."""
        result = map_sca_relevance(
            miss_risk="HIGH",
            is_material=False,
            is_financial=True,
        )
        assert "10b-5" in result or "fraud" in result.lower()

    def test_medium_miss_material_non_financial(self) -> None:
        """MEDIUM miss risk + material non-financial -> operational misrepresentation."""
        result = map_sca_relevance(
            miss_risk="MEDIUM",
            is_material=True,
            is_financial=False,
        )
        assert "Section 11" in result or "operational misrepresentation" in result.lower()


class TestEnrichForwardStatements:
    """Tests for enriching ForwardStatements with miss risk and SCA."""

    def test_enrichment_applies_miss_risk(self) -> None:
        """enrich_forward_statements populates miss_risk on each statement."""
        statements = [
            ForwardStatement(
                metric_name="Revenue",
                current_value_numeric=90.0,
                guidance_midpoint=100.0,
                guidance_type="QUANTITATIVE",
            ),
        ]
        credibility = CredibilityScore(
            beat_rate_pct=75.0,
            quarters_assessed=8,
            credibility_level="MEDIUM",
        )

        enriched = enrich_forward_statements(statements, credibility)
        assert len(enriched) == 1
        assert enriched[0].miss_risk in ("HIGH", "MEDIUM", "LOW", "UNKNOWN")
        assert enriched[0].miss_risk != "UNKNOWN"  # Should be computed

    def test_enrichment_applies_sca_relevance(self) -> None:
        """enrich_forward_statements populates sca_relevance for high risk."""
        statements = [
            ForwardStatement(
                metric_name="Revenue",
                current_value_numeric=80.0,
                guidance_midpoint=100.0,
                guidance_type="QUANTITATIVE",
            ),
        ]
        credibility = CredibilityScore(
            beat_rate_pct=25.0,
            quarters_assessed=4,
            credibility_level="LOW",
        )

        enriched = enrich_forward_statements(statements, credibility)
        assert len(enriched) == 1
        assert enriched[0].miss_risk == "HIGH"
        assert enriched[0].sca_relevance != ""

    def test_qualitative_statement_gets_unknown(self) -> None:
        """Qualitative statements without numeric data get UNKNOWN miss risk."""
        statements = [
            ForwardStatement(
                metric_name="Cloud Growth",
                guidance_type="QUALITATIVE",
                guidance_midpoint=None,
                current_value_numeric=None,
            ),
        ]
        credibility = CredibilityScore(
            credibility_level="MEDIUM",
        )

        enriched = enrich_forward_statements(statements, credibility)
        assert enriched[0].miss_risk == "UNKNOWN"

    def test_enrichment_sets_rationale(self) -> None:
        """Enrichment sets miss_risk_rationale with gap and credibility info."""
        statements = [
            ForwardStatement(
                metric_name="EPS",
                current_value_numeric=4.20,
                guidance_midpoint=4.60,
                guidance_type="QUANTITATIVE",
            ),
        ]
        credibility = CredibilityScore(
            beat_rate_pct=60.0,
            quarters_assessed=8,
            credibility_level="MEDIUM",
        )

        enriched = enrich_forward_statements(statements, credibility)
        assert enriched[0].miss_risk_rationale != ""
        assert "gap" in enriched[0].miss_risk_rationale.lower() or "%" in enriched[0].miss_risk_rationale
