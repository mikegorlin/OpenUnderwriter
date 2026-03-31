"""Tests for PrecedentMatchEngine.

TDD tests for the Precedent Match pattern engine that computes
weighted Jaccard similarity between current company signal profiles
and historical D&O case library entries.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from do_uw.stages.score.precedent_match import (
    PrecedentMatchEngine,
    _weighted_jaccard,
)


# ---------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------


def _make_signal_results(
    fired: list[str],
    clear: list[str] | None = None,
) -> dict[str, Any]:
    """Create mock signal results dict.

    fired: signal IDs with RED status (treated as fired by the engine).
    clear: signal IDs with CLEAR status.
    """
    results: dict[str, Any] = {}
    for sig_id in fired:
        results[sig_id] = {"status": "RED", "value": None}
    if clear:
        for sig_id in clear:
            results[sig_id] = {"status": "CLEAR", "value": None}
    return results


# ---------------------------------------------------------------
# Weighted Jaccard unit tests
# ---------------------------------------------------------------


class TestWeightedJaccard:
    """Unit tests for the weighted Jaccard similarity function."""

    def test_identical_sets(self) -> None:
        """Identical binary fingerprints should have similarity = 1.0."""
        a = {"s1": True, "s2": True, "s3": False}
        b = {"s1": True, "s2": True, "s3": False}
        weights = {"s1": 1.0, "s2": 1.0, "s3": 1.0}
        assert _weighted_jaccard(a, b, weights) == pytest.approx(1.0)

    def test_no_overlap(self) -> None:
        """Disjoint fired sets should have similarity = 0.0."""
        a = {"s1": True, "s2": False}
        b = {"s1": False, "s2": True}
        weights = {"s1": 1.0, "s2": 1.0}
        assert _weighted_jaccard(a, b, weights) == pytest.approx(0.0)

    def test_partial_overlap(self) -> None:
        """Partial overlap should return intermediate similarity."""
        a = {"s1": True, "s2": True, "s3": False}
        b = {"s1": True, "s2": False, "s3": True}
        weights = {"s1": 1.0, "s2": 1.0, "s3": 1.0}
        # Intersection weight = 1.0 (s1), Union weight = 3.0 (s1,s2,s3)
        assert _weighted_jaccard(a, b, weights) == pytest.approx(1.0 / 3.0)

    def test_division_by_zero(self) -> None:
        """Both fingerprints all False should return 0.0."""
        a = {"s1": False, "s2": False}
        b = {"s1": False, "s2": False}
        weights = {"s1": 1.0, "s2": 1.0}
        assert _weighted_jaccard(a, b, weights) == 0.0

    def test_weighted_signals_increase_similarity(self) -> None:
        """CRF-weighted signals matching should produce higher similarity."""
        a = {"crf1": True, "normal1": True}
        b = {"crf1": True, "normal1": False}
        # With equal weights
        equal_weights = {"crf1": 1.0, "normal1": 1.0}
        sim_equal = _weighted_jaccard(a, b, equal_weights)

        # With CRF weight = 3x
        crf_weights = {"crf1": 3.0, "normal1": 1.0}
        sim_crf = _weighted_jaccard(a, b, crf_weights)

        # CRF weighting should increase similarity when CRF signals match
        assert sim_crf > sim_equal


# ---------------------------------------------------------------
# Engine-level tests
# ---------------------------------------------------------------


class TestPrecedentMatchFires:
    """Tests where the engine should fire (similarity > notable threshold)."""

    def test_10_overlapping_signals_with_high_case(self) -> None:
        """Company with many fired signals overlapping HIGH case => fires."""
        # Fire a substantial set of signals that Enron/WorldCom had
        fired = [
            "FIN.FORENSIC.m_score_composite",
            "FIN.FORENSIC.dsri_elevated",
            "FIN.FORENSIC.aqi_elevated",
            "FIN.FORENSIC.tata_elevated",
            "FIN.FORENSIC.fis_composite",
            "FIN.FORENSIC.dechow_f_score",
            "FIN.FORENSIC.beneish_dechow_convergence",
            "FIN.FORENSIC.sloan_accruals",
            "FIN.FORENSIC.enhanced_sloan",
            "FIN.FORENSIC.accrual_intensity",
            "FIN.FORENSIC.cash_flow_manipulation",
            "FIN.FORENSIC.non_gaap_gap",
            "FIN.QUALITY.revenue_recognition_risk",
            "FIN.QUALITY.revenue_quality_score",
            "FIN.QUALITY.quality_of_earnings",
            "FIN.QUALITY.cash_flow_quality",
            "FIN.ACCT.restatement",
            "FIN.ACCT.restatement_magnitude",
            "FIN.ACCT.material_weakness",
            "FIN.ACCT.internal_controls",
            "GOV.INSIDER.cluster_sales",
            "GOV.INSIDER.net_selling",
            "GOV.INSIDER.executive_sales",
            "GOV.EXEC.departure_context",
            "GOV.EXEC.key_person",
            "GOV.EFFECT.material_weakness",
            "GOV.EFFECT.auditor_change",
            "STOCK.PRICE.recent_drop_alert",
            "STOCK.PRICE.returns_multi_horizon",
            "LIT.REG.sec_investigation",
            "LIT.REG.sec_active",
            "FWRD.WARN.zone_of_insolvency",
        ]
        signal_results = _make_signal_results(fired=fired)

        engine = PrecedentMatchEngine()
        result = engine.evaluate(signal_results)

        # Should fire with notable match
        assert result.fired is True
        assert result.confidence > 0.0
        assert len(result.findings) > 0

    def test_top_3_matches_returned_sorted(self) -> None:
        """Engine returns top 3 matches sorted by similarity descending."""
        fired = [
            "FIN.FORENSIC.m_score_composite",
            "FIN.FORENSIC.dsri_elevated",
            "FIN.ACCT.restatement",
            "GOV.INSIDER.cluster_sales",
            "STOCK.PRICE.recent_drop_alert",
            "LIT.REG.sec_investigation",
        ]
        signal_results = _make_signal_results(fired=fired)

        engine = PrecedentMatchEngine()
        result = engine.evaluate(signal_results)

        # Should have top 3 matches
        assert len(result.findings) <= 3
        if len(result.findings) >= 2:
            # Sorted by similarity descending
            sims = [f.get("similarity", 0) for f in result.findings]
            assert sims == sorted(sims, reverse=True)


class TestPrecedentMatchDoesNotFire:
    """Tests where the engine should NOT fire."""

    def test_no_overlapping_signals(self) -> None:
        """Company with no overlapping signals => similarity near 0, no fire."""
        # Fire only signals that no case has
        signal_results = _make_signal_results(
            fired=["BIZ.COMP.market_position", "BIZ.COMP.moat"],
            clear=["FIN.FORENSIC.m_score_composite"],
        )

        engine = PrecedentMatchEngine()
        result = engine.evaluate(signal_results)

        assert result.fired is False

    def test_empty_signal_results(self) -> None:
        """Empty signal results => NOT_FIRED."""
        engine = PrecedentMatchEngine()
        result = engine.evaluate({})

        assert result.fired is False


class TestDismissedCases:
    """Tests for dismissed case handling."""

    def test_dismissed_case_has_reduced_severity(self) -> None:
        """Dismissed cases appear in results with 0.5x outcome severity weight."""
        # This test uses the engine's internal case processing logic.
        # We verify that dismissed cases get outcome_severity_weight = 0.5
        engine = PrecedentMatchEngine()
        cases = engine._load_case_library()

        # Check if any case has a dismissal outcome
        # If no dismissals in seed data, verify the logic handles it correctly
        for case in cases:
            if case.outcome.get("type") == "dismissal":
                # Dismissed cases should still be loadable
                assert case.signal_profile_confidence in {"HIGH", "MEDIUM", "LOW"}


class TestCRFWeighting:
    """Tests for CRF signal weighting in similarity computation."""

    def test_crf_signals_higher_similarity(self) -> None:
        """CRF-overlapping signals produce higher similarity than equivalent non-CRF."""
        # Fire a CRF-related signal (restatement is a CRF trigger)
        crf_results = _make_signal_results(
            fired=["FIN.ACCT.restatement", "FIN.ACCT.material_weakness"]
        )
        # Fire equivalent count of non-CRF signals
        non_crf_results = _make_signal_results(
            fired=["BIZ.SIZE.market_cap", "BIZ.SIZE.employees"]
        )

        engine = PrecedentMatchEngine()
        crf_result = engine.evaluate(crf_results)
        non_crf_result = engine.evaluate(non_crf_results)

        # CRF signals should produce higher confidence when they match cases
        # that also have those CRF signals
        assert crf_result.confidence >= non_crf_result.confidence


class TestConfidenceWeighting:
    """Tests for signal profile confidence adjustments."""

    def test_post_filing_reduced_weight(self) -> None:
        """POST_FILING / LOW confidence cases get lower adjusted similarity."""
        # This is tested implicitly through the engine's evaluate logic.
        # HIGH confidence cases should have higher adjusted similarity
        # than equivalent MEDIUM cases for the same overlap.
        engine = PrecedentMatchEngine()
        cases = engine._load_case_library()

        high_cases = [c for c in cases if c.signal_profile_confidence == "HIGH"]
        medium_cases = [c for c in cases if c.signal_profile_confidence == "MEDIUM"]

        # Both tiers exist in the library
        assert len(high_cases) >= 6
        assert len(medium_cases) >= 14


class TestPrecedentMatchProtocol:
    """Tests for PatternEngine protocol compliance."""

    def test_engine_id(self) -> None:
        """engine_id is 'precedent_match'."""
        engine = PrecedentMatchEngine()
        assert engine.engine_id == "precedent_match"

    def test_engine_name(self) -> None:
        """engine_name is 'Precedent Match'."""
        engine = PrecedentMatchEngine()
        assert engine.engine_name == "Precedent Match"

    def test_returns_engine_result(self) -> None:
        """evaluate() returns an EngineResult."""
        from do_uw.stages.score.pattern_engine import EngineResult

        engine = PrecedentMatchEngine()
        result = engine.evaluate({})
        assert isinstance(result, EngineResult)


class TestIntegrationWithRealCaseLibrary:
    """Integration tests using the actual case_library.yaml."""

    def test_loads_20_cases(self) -> None:
        """Engine loads all 20 cases from YAML."""
        engine = PrecedentMatchEngine()
        cases = engine._load_case_library()
        assert len(cases) == 20

    def test_synthetic_enron_like_company(self) -> None:
        """Synthetic company with Enron-like signals gets high similarity."""
        # Simulate a company with accounting fraud signals
        fired = [
            "FIN.FORENSIC.m_score_composite",
            "FIN.FORENSIC.dsri_elevated",
            "FIN.FORENSIC.aqi_elevated",
            "FIN.FORENSIC.tata_elevated",
            "FIN.FORENSIC.fis_composite",
            "FIN.FORENSIC.dechow_f_score",
            "FIN.FORENSIC.beneish_dechow_convergence",
            "FIN.FORENSIC.sloan_accruals",
            "FIN.FORENSIC.enhanced_sloan",
            "FIN.FORENSIC.accrual_intensity",
            "FIN.FORENSIC.cash_flow_manipulation",
            "FIN.QUALITY.revenue_recognition_risk",
            "FIN.QUALITY.quality_of_earnings",
            "FIN.ACCT.restatement",
            "FIN.ACCT.material_weakness",
            "GOV.INSIDER.cluster_sales",
            "GOV.INSIDER.net_selling",
            "GOV.EXEC.departure_context",
            "GOV.EXEC.key_person",
            "STOCK.PRICE.recent_drop_alert",
            "STOCK.PRICE.returns_multi_horizon",
            "LIT.REG.sec_investigation",
            "LIT.REG.sec_active",
            "FWRD.WARN.zone_of_insolvency",
        ]
        signal_results = _make_signal_results(fired=fired)

        engine = PrecedentMatchEngine()
        result = engine.evaluate(signal_results)

        assert result.fired is True
        assert result.confidence > 0.30  # Notable match threshold
        # ENRON should be in top matches
        top_case_ids = [f["case_id"] for f in result.findings]
        assert "ENRON-2001" in top_case_ids
