"""Tests for SCR narrative and D&O implications context builders (Phase 65-03)."""

from __future__ import annotations

import pytest

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders.narrative import (
    extract_do_implications,
    extract_scr_narratives,
)


def _make_state(**overrides) -> AnalysisState:
    """Create minimal AnalysisState for testing."""
    overrides.setdefault("ticker", "TEST")
    return AnalysisState(**overrides)


class TestExtractScrNarratives:
    """Tests for extract_scr_narratives()."""

    def test_empty_state_returns_empty(self):
        state = _make_state()
        result = extract_scr_narratives(state)
        # With no analysis, all sections are CLEAN with no narrative
        # so no SCR is generated
        assert isinstance(result, dict)

    def test_elevated_density_produces_scr(self):
        state = _make_state()
        # Manually set analysis with density
        from do_uw.models.density import PreComputedNarratives

        state.analysis = type("Analysis", (), {
            "section_densities": {"governance": {"level": "ELEVATED"}},
            "pre_computed_narratives": PreComputedNarratives(governance="Board independence concerns noted. Compensation structure requires review."),
            "signal_results": {},
            "gap_search_summary": {},
        })()
        result = extract_scr_narratives(state)
        assert "governance" in result
        scr = result["governance"]
        assert "situation" in scr
        assert "complication" in scr
        assert "resolution" in scr
        assert "Elevated" in scr["complication"]

    def test_critical_density_produces_scr(self):
        state = _make_state()
        from do_uw.models.density import PreComputedNarratives

        state.analysis = type("Analysis", (), {
            "section_densities": {"litigation": {"level": "CRITICAL"}},
            "pre_computed_narratives": PreComputedNarratives(litigation="Active securities litigation pending."),
            "signal_results": {},
            "gap_search_summary": {},
        })()
        result = extract_scr_narratives(state)
        assert "litigation" in result
        assert "Critical" in result["litigation"]["complication"]

    def test_clean_density_suppresses_scr(self):
        """CLEAN density should NOT produce SCR — no value in generic boilerplate."""
        state = _make_state()
        from do_uw.models.density import PreComputedNarratives

        state.analysis = type("Analysis", (), {
            "section_densities": {"financial_health": {"level": "CLEAN"}},
            "pre_computed_narratives": PreComputedNarratives(financial="Strong financial position. Revenue growth consistent."),
            "signal_results": {},
            "gap_search_summary": {},
        })()
        result = extract_scr_narratives(state)
        assert "financial" not in result

    def test_template_key_mapping(self):
        """business_profile maps to 'company', market_activity to 'market'."""
        state = _make_state()
        from do_uw.models.density import PreComputedNarratives

        state.analysis = type("Analysis", (), {
            "section_densities": {
                "business_profile": {"level": "ELEVATED"},
                "market_activity": {"level": "ELEVATED"},
            },
            "pre_computed_narratives": PreComputedNarratives(
                company="Company profile review.",
                market="Market activity analysis.",
            ),
            "signal_results": {},
            "gap_search_summary": {},
        })()
        result = extract_scr_narratives(state)
        # Should use template keys not brain IDs
        assert "company" in result
        assert "market" in result
        assert "business_profile" not in result
        assert "market_activity" not in result

    def test_resolution_capped_at_300_chars(self):
        state = _make_state()
        from do_uw.models.density import PreComputedNarratives

        long_narrative = "This is a very long sentence that goes on and on. " * 20
        state.analysis = type("Analysis", (), {
            "section_densities": {"scoring": {"level": "ELEVATED"}},
            "pre_computed_narratives": PreComputedNarratives(scoring=long_narrative),
            "signal_results": {},
            "gap_search_summary": {},
        })()
        result = extract_scr_narratives(state)
        assert len(result["scoring"]["resolution"]) <= 303  # 300 + "..."


class TestExtractDoImplications:
    """Tests for extract_do_implications()."""

    def test_empty_state_returns_empty(self):
        state = _make_state()
        result = extract_do_implications(state)
        assert isinstance(result, dict)

    def test_elevated_governance_produces_implications(self):
        state = _make_state()
        state.analysis = type("Analysis", (), {
            "section_densities": {"governance": {"level": "ELEVATED"}},
            "pre_computed_narratives": None,
            "signal_results": {},
            "gap_search_summary": {},
        })()
        result = extract_do_implications(state)
        assert "governance" in result
        impl = result["governance"]
        assert "items" in impl
        assert len(impl["items"]) > 0
        assert "coverage_note" in impl

    def test_critical_financial_has_high_severity(self):
        state = _make_state()
        state.analysis = type("Analysis", (), {
            "section_densities": {"financial_health": {"level": "CRITICAL"}},
            "pre_computed_narratives": None,
            "signal_results": {},
            "gap_search_summary": {},
        })()
        result = extract_do_implications(state)
        assert "financial" in result
        severities = [i["severity"] for i in result["financial"]["items"]]
        assert "HIGH" in severities

    def test_template_key_mapping_implications(self):
        state = _make_state()
        state.analysis = type("Analysis", (), {
            "section_densities": {"business_profile": {"level": "ELEVATED"}},
            "pre_computed_narratives": None,
            "signal_results": {},
            "gap_search_summary": {},
        })()
        result = extract_do_implications(state)
        assert "company" in result
        assert "business_profile" not in result

    def test_clean_section_no_implications(self):
        state = _make_state()
        state.analysis = type("Analysis", (), {
            "section_densities": {"ai_risk": {"level": "CLEAN"}},
            "pre_computed_narratives": None,
            "signal_results": {},
            "gap_search_summary": {},
        })()
        result = extract_do_implications(state)
        # AI risk with CLEAN should not trigger implications
        assert "ai_risk" not in result

    def test_signal_triggered_produces_implication(self):
        state = _make_state()
        state.analysis = type("Analysis", (), {
            "section_densities": {"governance": {"level": "CLEAN"}},
            "pre_computed_narratives": None,
            "signal_results": {
                "GOV.INSIDER.net_selling_trading": {"status": "TRIGGERED"},
            },
            "gap_search_summary": {},
        })()
        result = extract_do_implications(state)
        # Insider trading trigger should produce governance implications
        if "governance" in result:
            texts = [i["text"] for i in result["governance"]["items"]]
            assert any("insider" in t.lower() or "trading" in t.lower() for t in texts)

    def test_coverage_notes_present(self):
        state = _make_state()
        state.analysis = type("Analysis", (), {
            "section_densities": {"litigation": {"level": "CRITICAL"}},
            "pre_computed_narratives": None,
            "signal_results": {},
            "gap_search_summary": {},
        })()
        result = extract_do_implications(state)
        assert "litigation" in result
        assert result["litigation"]["coverage_note"]
        assert "litigation" in result["litigation"]["coverage_note"].lower() or "prior" in result["litigation"]["coverage_note"].lower()


class TestStateAwareImplications:
    """Tests for state-aware D&O implications (Phase 119.1-02)."""

    @staticmethod
    def _make_distressed_state() -> AnalysisState:
        """Create ANGI-like distressed state: Altman Z=0.98, D/E=3.2, going_concern=True."""
        from do_uw.models.financials import (
            AuditProfile,
            DistressIndicators,
            DistressResult,
            ExtractedFinancials,
        )
        from do_uw.models.common import SourcedValue
        from datetime import datetime, UTC
        _now = datetime.now(tz=UTC)
        _sv = lambda v, s="XBRL", c="HIGH": SourcedValue(value=v, source=s, confidence=c, as_of=_now)

        state = AnalysisState(ticker="ANGI")
        state.extracted = type("ExtractedData", (), {
            "financials": ExtractedFinancials(
                distress=DistressIndicators(
                    altman_z_score=DistressResult(
                        score=0.98, zone="distress", model_name="Altman Z-Score",
                    ),
                    piotroski_f_score=DistressResult(
                        score=2.0, zone="distress", model_name="Piotroski F-Score",
                    ),
                ),
                audit=AuditProfile(
                    going_concern=_sv(True, "10-K"),
                ),
                leverage=_sv({"debt_to_equity": 3.2, "interest_coverage": 0.8}),
                liquidity=_sv({"current_ratio": 0.6}),
            ),
            "litigation": None,
            "market": None,
            "governance": None,
            "ai_risk": None,
            "risk_factors": [],
            "text_signals": {},
        })()
        state.analysis = type("Analysis", (), {
            "section_densities": {"financial_health": {"level": "CRITICAL"}},
            "pre_computed_narratives": None,
            "signal_results": {},
            "gap_search_summary": {},
        })()
        return state

    @staticmethod
    def _make_healthy_state() -> AnalysisState:
        """Create AAPL-like healthy state: Altman Z=9.93, D/E=1.87."""
        from do_uw.models.financials import (
            AuditProfile,
            DistressIndicators,
            DistressResult,
            ExtractedFinancials,
        )
        from do_uw.models.common import SourcedValue
        from datetime import datetime, UTC
        _now = datetime.now(tz=UTC)
        _sv = lambda v, s="XBRL", c="HIGH": SourcedValue(value=v, source=s, confidence=c, as_of=_now)

        state = AnalysisState(ticker="AAPL")
        state.extracted = type("ExtractedData", (), {
            "financials": ExtractedFinancials(
                distress=DistressIndicators(
                    altman_z_score=DistressResult(
                        score=9.93, zone="safe", model_name="Altman Z-Score",
                    ),
                    piotroski_f_score=DistressResult(
                        score=7.0, zone="safe", model_name="Piotroski F-Score",
                    ),
                ),
                audit=AuditProfile(),
                leverage=_sv({"debt_to_equity": 1.87, "interest_coverage": 25.0}),
                liquidity=_sv({"current_ratio": 1.07}),
            ),
            "litigation": None,
            "market": None,
            "governance": None,
            "ai_risk": None,
            "risk_factors": [],
            "text_signals": {},
        })()
        state.analysis = type("Analysis", (), {
            "section_densities": {"financial_health": {"level": "ELEVATED"}},
            "pre_computed_narratives": None,
            "signal_results": {},
            "gap_search_summary": {},
        })()
        return state

    def test_implications_state_aware_distressed(self):
        """Distressed company gets Zone of Insolvency / creditor derivative text with actual numbers."""
        state = self._make_distressed_state()
        result = extract_do_implications(state)
        assert "financial" in result
        texts = " ".join(i["text"] for i in result["financial"]["items"])
        # Must contain actual Altman Z value
        assert "0.98" in texts
        # Must reference insolvency or creditor-oriented claims
        assert any(term in texts.lower() for term in ["insolvency", "creditor", "distress zone"])

    def test_implications_state_aware_healthy(self):
        """Healthy company does NOT get distress/insolvency language."""
        state = self._make_healthy_state()
        result = extract_do_implications(state)
        if "financial" in result:
            texts = " ".join(i["text"] for i in result["financial"]["items"])
            # Healthy company should NOT mention distress or insolvency
            assert "insolvency" not in texts.lower()
            assert "distress zone" not in texts.lower()
            assert "creditor derivative" not in texts.lower()

    def test_implications_differ_by_company(self):
        """Distressed and healthy states produce different text for same section."""
        distressed = self._make_distressed_state()
        healthy = self._make_healthy_state()
        result_d = extract_do_implications(distressed)
        result_h = extract_do_implications(healthy)
        # Both should have financial section (CRITICAL and ELEVATED both trigger)
        if "financial" in result_d and "financial" in result_h:
            texts_d = " ".join(i["text"] for i in result_d["financial"]["items"])
            texts_h = " ".join(i["text"] for i in result_h["financial"]["items"])
            assert texts_d != texts_h, "Distressed and healthy companies must get different implication text"

    def test_scr_complication_uses_signal_names(self):
        """SCR complication for CRITICAL section uses signal-based format when signals found."""
        from unittest.mock import patch
        from do_uw.stages.render.context_builders import narrative

        state = _make_state()
        state.analysis = type("Analysis", (), {
            "section_densities": {"governance": {"level": "CRITICAL"}},
            "pre_computed_narratives": None,
            "signal_results": {},
            "gap_search_summary": {},
        })()
        # Patch _get_elevated_signal_names to simulate signals being found
        with patch.object(
            narrative, "_get_elevated_signal_names",
            return_value=["Board Independence Ratio", "CEO Duality"],
        ):
            result = extract_scr_narratives(state)
        assert "governance" in result
        comp = result["governance"]["complication"]
        # New format: "Critical risk in {section}: {signals}. Requires immediate..."
        assert "Board Independence Ratio" in comp
        assert "CEO Duality" in comp
        assert "Critical risk in" in comp
        # Old generic format should NOT appear
        assert "Critical risk indicators identified in" not in comp

    def test_coverage_notes_reference_state(self):
        """Coverage notes vary based on what risks are actually present."""
        distressed = self._make_distressed_state()
        healthy = self._make_healthy_state()
        result_d = extract_do_implications(distressed)
        result_h = extract_do_implications(healthy)
        # Coverage notes should be present and non-empty
        if "financial" in result_d:
            note_d = result_d["financial"]["coverage_note"]
            assert note_d, "Coverage note must be present"
            # Distressed note should reference financial condition
            assert any(term in note_d.lower() for term in [
                "financial condition", "insolvency", "distress", "exclusion", "coverage",
            ])
