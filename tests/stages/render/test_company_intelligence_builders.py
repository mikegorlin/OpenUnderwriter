"""Tests for company intelligence context builders (Phase 134-02)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from do_uw.models.state import AnalysisState, ExtractedData, RiskFactorProfile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _minimal_state(**kwargs) -> AnalysisState:
    """Create a minimal AnalysisState for testing."""
    kwargs.setdefault("ticker", "TEST")
    return AnalysisState(**kwargs)


# ---------------------------------------------------------------------------
# Risk Factor Review
# ---------------------------------------------------------------------------


class TestBuildRiskFactorReview:
    """Tests for build_risk_factor_review."""

    def test_empty_state_returns_false(self):
        from do_uw.stages.render.context_builders._company_intelligence import (
            build_risk_factor_review,
        )
        state = _minimal_state()
        result = build_risk_factor_review(state)
        assert result["has_risk_factor_review"] is False

    def test_with_risk_factors_returns_rows(self):
        from do_uw.stages.render.context_builders._company_intelligence import (
            build_risk_factor_review,
        )
        state = _minimal_state()
        state.extracted = ExtractedData()
        state.extracted.risk_factors = [
            RiskFactorProfile(
                title="Cybersecurity Breach Risk",
                category="CYBER",
                severity="HIGH",
                is_new_this_year=True,
            ),
            RiskFactorProfile(
                title="Market Competition",
                category="OPERATIONAL",
                severity="MEDIUM",
            ),
        ]
        result = build_risk_factor_review(state)
        assert result["has_risk_factor_review"] is True
        assert len(result["risk_factor_review"]) == 2
        assert result["risk_factor_summary"]["total"] == 2
        assert result["risk_factor_summary"]["novel"] >= 1  # Cyber is new

    def test_sort_order_elevated_first(self):
        from do_uw.stages.render.context_builders._company_intelligence import (
            build_risk_factor_review,
        )
        state = _minimal_state()
        state.extracted = ExtractedData()
        state.extracted.risk_factors = [
            RiskFactorProfile(title="Low Risk", severity="LOW", category="OTHER"),
            RiskFactorProfile(title="High New Risk", severity="HIGH", is_new_this_year=True, category="LITIGATION"),
            RiskFactorProfile(title="Elevated Risk", severity="HIGH", category="FINANCIAL"),
        ]
        result = build_risk_factor_review(state)
        rows = result["risk_factor_review"]
        # ELEVATED/NOVEL should come before STANDARD
        classifications = [r["classification"] for r in rows]
        # NOVEL and ELEVATED should be first
        assert classifications[0] in ("ELEVATED", "NOVEL")


# ---------------------------------------------------------------------------
# Peer SCA Contagion
# ---------------------------------------------------------------------------


class TestBuildPeerSCAContagion:
    """Tests for build_peer_sca_contagion."""

    def test_no_peers_returns_empty(self):
        from do_uw.stages.render.context_builders._company_intelligence import (
            build_peer_sca_contagion,
        )
        state = _minimal_state()
        result = build_peer_sca_contagion(state)
        assert result["has_peer_sca"] is True  # Always true, shows positive signal
        assert result["peer_sca_records"] == []
        assert "No peer group" in result["peer_sca_summary"]


# ---------------------------------------------------------------------------
# Concentration Assessment
# ---------------------------------------------------------------------------


class TestBuildConcentrationAssessment:
    """Tests for build_concentration_assessment."""

    def test_empty_state_returns_4_dims(self):
        from do_uw.stages.render.context_builders._company_intelligence import (
            build_concentration_assessment,
        )
        state = _minimal_state()
        result = build_concentration_assessment(state)
        assert result["has_concentration"] is True
        assert len(result["concentration_dims"]) == 4
        dims = {d["dimension"] for d in result["concentration_dims"]}
        assert dims == {"Customer", "Geographic", "Product/Service", "Channel"}

    def test_concentration_risk_level_present(self):
        from do_uw.stages.render.context_builders._company_intelligence import (
            build_concentration_assessment,
        )
        state = _minimal_state()
        result = build_concentration_assessment(state)
        assert result["concentration_risk_level"] in ("HIGH", "MEDIUM", "LOW")


# ---------------------------------------------------------------------------
# Supply Chain Context
# ---------------------------------------------------------------------------


class TestBuildSupplyChainContext:
    """Tests for build_supply_chain_context."""

    def test_no_text_returns_false(self):
        from do_uw.stages.render.context_builders._company_intelligence import (
            build_supply_chain_context,
        )
        state = _minimal_state()
        result = build_supply_chain_context(state)
        assert result.get("has_supply_chain") is False


# ---------------------------------------------------------------------------
# Sector D&O Concerns
# ---------------------------------------------------------------------------


class TestBuildSectorDOConcerns:
    """Tests for build_sector_do_concerns."""

    def test_no_sic_returns_false(self):
        from do_uw.stages.render.context_builders._company_intelligence import (
            build_sector_do_concerns,
        )
        state = _minimal_state()
        result = build_sector_do_concerns(state)
        assert result["has_sector_concerns"] is False

    def test_with_tech_sic_returns_concerns(self):
        from do_uw.stages.render.context_builders._company_intelligence import (
            build_sector_do_concerns,
        )
        from do_uw.models.company import CompanyProfile, CompanyIdentity
        from do_uw.models.common import Confidence, SourcedValue
        state = _minimal_state()
        state.company = CompanyProfile(
            identity=CompanyIdentity(
                ticker="TEST",
                sic_code=SourcedValue(value="7372", source="SEC", confidence=Confidence.HIGH, as_of="2026-01-01T00:00:00Z"),
            ),
        )
        result = build_sector_do_concerns(state)
        assert result["has_sector_concerns"] is True
        assert result["matched_sector"] == "Technology"
        assert len(result["sector_concerns"]) > 0


# ---------------------------------------------------------------------------
# Regulatory Map
# ---------------------------------------------------------------------------


class TestBuildRegulatoryMap:
    """Tests for build_regulatory_map."""

    def test_no_litigation_returns_false(self):
        from do_uw.stages.render.context_builders._company_intelligence import (
            build_regulatory_map,
        )
        state = _minimal_state()
        result = build_regulatory_map(state)
        assert result["has_regulatory_map"] is False


# ---------------------------------------------------------------------------
# Integration: extract_company includes CI keys
# ---------------------------------------------------------------------------


class TestExtractCompanyIntegration:
    """Verify extract_company merges company intelligence data."""

    def test_extract_company_includes_ci_keys(self):
        from do_uw.stages.render.context_builders.company_profile import (
            extract_company,
        )
        from do_uw.models.company import CompanyProfile, CompanyIdentity
        from do_uw.models.common import Confidence, SourcedValue
        state = _minimal_state()
        state.company = CompanyProfile(
            identity=CompanyIdentity(
                ticker="TEST",
                legal_name=SourcedValue(value="Test Corp", source="SEC", confidence=Confidence.HIGH, as_of="2026-01-01T00:00:00Z"),
                sic_code=SourcedValue(value="7372", source="SEC", confidence=Confidence.HIGH, as_of="2026-01-01T00:00:00Z"),
            ),
        )
        result = extract_company(state)
        # Should include company intelligence keys
        assert "has_concentration" in result
        assert "has_risk_factor_review" in result
        assert "has_sector_concerns" in result
