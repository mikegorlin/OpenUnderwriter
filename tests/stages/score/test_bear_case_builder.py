"""Tests for evidence-gated bear case builder.

Verifies:
- Evidence gate: only MODERATE/HIGH exposure theories produce bear cases
- Committee summary structure (2-3 sentences)
- Defense assessment (None unless company-specific)
- Evidence chain ordering (highest severity first)
- Clean company -> empty list
- Troubled company -> multiple bear cases
"""

from __future__ import annotations

import pytest

from do_uw.models.peril import PerilProbabilityBand, PerilSeverityBand
from do_uw.stages.score.bear_case_builder import (
    _assess_defense,
    _build_committee_summary,
    _get_evidence_for_theory,
    _infer_severity,
    _theory_label,
    build_bear_cases,
)


# -----------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------


def _make_theory(
    theory: str, exposure_level: str, factor_sources: list[str] | None = None,
) -> dict:
    return {
        "theory": theory,
        "exposure_level": exposure_level,
        "findings": [],
        "factor_sources": factor_sources or [],
    }


def _make_check(
    signal_id: str,
    status: str = "TRIGGERED",
    factors: list[str] | None = None,
    plaintiff_lenses: list[str] | None = None,
    threshold_level: str = "red",
    evidence: str = "Test finding",
    category: str = "DECISION_DRIVING",
    data_status: str = "EVALUATED",
) -> dict:
    return {
        "signal_id": signal_id,
        "signal_name": f"Check {signal_id}",
        "status": status,
        "factors": factors or [],
        "plaintiff_lenses": plaintiff_lenses or [],
        "threshold_level": threshold_level,
        "evidence": evidence,
        "source": "test",
        "category": category,
        "data_status": data_status,
    }


def _make_assessment(
    plaintiff_type: str,
    probability_band: str = "MODERATE",
    severity_band: str = "MODERATE",
) -> dict:
    return {
        "plaintiff_type": plaintiff_type,
        "probability_band": probability_band,
        "severity_band": severity_band,
        "triggered_signal_count": 3,
        "total_signal_count": 10,
        "evaluated_signal_count": 8,
        "key_findings": [],
        "modeling_depth": "FULL",
    }


def _clean_allegation_mapping() -> dict:
    """All theories LOW -> clean company."""
    return {
        "theories": [
            _make_theory("A_DISCLOSURE", "LOW"),
            _make_theory("B_GUIDANCE", "LOW"),
            _make_theory("C_PRODUCT_OPS", "LOW"),
            _make_theory("D_GOVERNANCE", "LOW"),
            _make_theory("E_MA", "LOW"),
        ],
        "primary_exposure": "A_DISCLOSURE",
        "concentration_analysis": "Low exposure across all theories.",
    }


def _troubled_allegation_mapping() -> dict:
    """3 theories MODERATE/HIGH -> troubled company."""
    return {
        "theories": [
            _make_theory("A_DISCLOSURE", "HIGH", ["F1", "F3", "F5"]),
            _make_theory("B_GUIDANCE", "MODERATE", ["F2", "F5"]),
            _make_theory("C_PRODUCT_OPS", "MODERATE", ["F7", "F8"]),
            _make_theory("D_GOVERNANCE", "LOW"),
            _make_theory("E_MA", "LOW"),
        ],
        "primary_exposure": "A_DISCLOSURE",
        "concentration_analysis": "HIGH in A_DISCLOSURE, MODERATE in B, C.",
    }


def _make_signal_results() -> dict:
    """Check results with various severities and factor mappings."""
    return {
        "FIN.ACCT.restatement": _make_check(
            "FIN.ACCT.restatement",
            factors=["F1", "F3"],
            plaintiff_lenses=["SHAREHOLDERS"],
            threshold_level="red",
            evidence="Material restatement of Q3 revenue",
        ),
        "FIN.EARN.quality_decline": _make_check(
            "FIN.EARN.quality_decline",
            factors=["F3"],
            plaintiff_lenses=["SHAREHOLDERS"],
            threshold_level="yellow",
            evidence="Earnings quality declined 25%",
        ),
        "MKT.GUIDE.miss_pattern": _make_check(
            "MKT.GUIDE.miss_pattern",
            factors=["F2", "F5"],
            plaintiff_lenses=["SHAREHOLDERS"],
            threshold_level="yellow",
            evidence="3 consecutive guidance misses",
        ),
        "BIZ.REG.enforcement": _make_check(
            "BIZ.REG.enforcement",
            factors=["F7"],
            plaintiff_lenses=["REGULATORS"],
            threshold_level="red",
            evidence="SEC enforcement action pending",
        ),
        "GOV.BOARD.independence": _make_check(
            "GOV.BOARD.independence",
            status="CLEAR",
            factors=["F9"],
            threshold_level="",
            evidence="Board independence 80%",
        ),
    }


# -----------------------------------------------------------------------
# Test: Evidence gate
# -----------------------------------------------------------------------


class TestEvidenceGate:
    """Test that bear cases are only built for MODERATE/HIGH exposure."""

    def test_moderate_exposure_builds_bear_case(self) -> None:
        mapping = {
            "theories": [_make_theory("A_DISCLOSURE", "MODERATE", ["F1", "F3"])],
        }
        checks = {
            "FIN.ACCT.restatement": _make_check(
                "FIN.ACCT.restatement", factors=["F1"],
            ),
        }
        assessments = [_make_assessment("SHAREHOLDERS")]
        result = build_bear_cases(mapping, checks, assessments, None, "TestCo")
        assert len(result) == 1
        assert result[0].theory == "A_DISCLOSURE"

    def test_high_exposure_builds_bear_case(self) -> None:
        mapping = {
            "theories": [_make_theory("B_GUIDANCE", "HIGH", ["F2", "F5"])],
        }
        checks = {
            "MKT.GUIDE.miss": _make_check(
                "MKT.GUIDE.miss", factors=["F2"],
            ),
        }
        assessments = [_make_assessment("SHAREHOLDERS")]
        result = build_bear_cases(mapping, checks, assessments, None, "TestCo")
        assert len(result) == 1
        assert result[0].theory == "B_GUIDANCE"

    def test_low_exposure_no_bear_case(self) -> None:
        mapping = {
            "theories": [_make_theory("A_DISCLOSURE", "LOW")],
        }
        checks = _make_signal_results()
        assessments = [_make_assessment("SHAREHOLDERS")]
        result = build_bear_cases(mapping, checks, assessments, None, "TestCo")
        assert len(result) == 0

    def test_clean_company_empty_list(self) -> None:
        mapping = _clean_allegation_mapping()
        checks = _make_signal_results()
        assessments = [_make_assessment("SHAREHOLDERS")]
        result = build_bear_cases(mapping, checks, assessments, None, "CleanCo")
        assert result == []

    def test_troubled_company_multiple_bear_cases(self) -> None:
        mapping = _troubled_allegation_mapping()
        checks = _make_signal_results()
        assessments = [
            _make_assessment("SHAREHOLDERS", "ELEVATED", "SIGNIFICANT"),
            _make_assessment("REGULATORS", "MODERATE", "MODERATE"),
        ]
        result = build_bear_cases(mapping, checks, assessments, None, "TroubledCo")
        assert len(result) == 3
        theories = {bc.theory for bc in result}
        assert "A_DISCLOSURE" in theories
        assert "B_GUIDANCE" in theories
        assert "C_PRODUCT_OPS" in theories


# -----------------------------------------------------------------------
# Test: Committee summary
# -----------------------------------------------------------------------


class TestCommitteeSummary:
    """Test committee summary is 2-3 structured sentences."""

    def test_summary_two_sentences_low_severity(self) -> None:
        from do_uw.models.peril import EvidenceItem

        evidence = [
            EvidenceItem(
                signal_id="FIN.1", description="Revenue declined",
                source="10-K", severity="HIGH", data_status="EVALUATED",
            ),
        ]
        summary = _build_committee_summary(
            "A_DISCLOSURE", evidence, "MODERATE", "MINOR", "TestCo",
        )
        sentences = [s.strip() for s in summary.split(".") if s.strip()]
        assert len(sentences) == 2

    def test_summary_three_sentences_moderate_severity(self) -> None:
        from do_uw.models.peril import EvidenceItem

        evidence = [
            EvidenceItem(
                signal_id="FIN.1", description="Material restatement",
                source="10-K", severity="CRITICAL", data_status="EVALUATED",
            ),
            EvidenceItem(
                signal_id="FIN.2", description="Earnings quality declined",
                source="10-Q", severity="HIGH", data_status="EVALUATED",
            ),
        ]
        summary = _build_committee_summary(
            "A_DISCLOSURE", evidence, "ELEVATED",
            PerilSeverityBand.MODERATE, "TestCo",
        )
        # Should have 3 sentences (severity >= MODERATE triggers third)
        assert "warranting detailed underwriter review" in summary

    def test_summary_starts_with_company_name(self) -> None:
        summary = _build_committee_summary(
            "B_GUIDANCE", [], "LOW", "NUISANCE", "AcmeCorp",
        )
        assert summary.startswith("AcmeCorp faces")

    def test_summary_contains_theory_label(self) -> None:
        summary = _build_committee_summary(
            "D_GOVERNANCE", [], "MODERATE", "MINOR", "TestCo",
        )
        assert "governance breach" in summary


# -----------------------------------------------------------------------
# Test: Defense assessment
# -----------------------------------------------------------------------


class TestDefenseAssessment:
    """Test defense assessment returns None unless company-specific."""

    def test_none_when_no_extracted_data(self) -> None:
        result = _assess_defense("A_DISCLOSURE", None)
        assert result is None

    def test_none_when_no_relevant_defense(self) -> None:
        from do_uw.models.state import ExtractedData

        extracted = ExtractedData()
        result = _assess_defense("B_GUIDANCE", extracted)
        assert result is None

    def test_section_11_defense_when_no_active_windows(self) -> None:
        """Section 11 defense when no active windows (statute expired)."""
        from do_uw.models.market import MarketSignals
        from do_uw.models.market_events import CapitalMarketsActivity
        from do_uw.models.state import ExtractedData

        cm = CapitalMarketsActivity(active_section_11_windows=0)
        market = MarketSignals(capital_markets=cm)
        extracted = ExtractedData(market=market)
        result = _assess_defense("A_DISCLOSURE", extracted)
        assert result is not None
        assert "Section 11" in result

    def test_no_section_11_defense_with_active_windows(self) -> None:
        """No Section 11 defense when windows are active."""
        from do_uw.models.market import MarketSignals
        from do_uw.models.market_events import CapitalMarketsActivity
        from do_uw.models.state import ExtractedData

        cm = CapitalMarketsActivity(active_section_11_windows=2)
        market = MarketSignals(capital_markets=cm)
        extracted = ExtractedData(market=market)
        result = _assess_defense("A_DISCLOSURE", extracted)
        # Should be None because active Section 11 windows = NOT a defense
        assert result is None


# -----------------------------------------------------------------------
# Test: Evidence chain ordering
# -----------------------------------------------------------------------


class TestEvidenceChain:
    """Test evidence chain is sorted by severity (highest first)."""

    def test_sorted_by_severity_highest_first(self) -> None:
        checks = {
            "A": _make_check("A", factors=["F1"], threshold_level=""),
            "B": _make_check("B", factors=["F1"], threshold_level="red"),
            "C": _make_check("C", factors=["F1"], threshold_level="yellow"),
        }
        evidence = _get_evidence_for_theory("A_DISCLOSURE", checks, ["F1"])
        severities = [e.severity for e in evidence]
        assert severities == ["CRITICAL", "HIGH", "MODERATE"]

    def test_max_10_evidence_items(self) -> None:
        checks = {}
        for i in range(15):
            checks[f"CHK.{i}"] = _make_check(
                f"CHK.{i}", factors=["F1"], threshold_level="red",
            )
        evidence = _get_evidence_for_theory("A_DISCLOSURE", checks, ["F1"])
        assert len(evidence) <= 10

    def test_only_triggered_checks_included(self) -> None:
        checks = {
            "A": _make_check("A", status="TRIGGERED", factors=["F1"]),
            "B": _make_check("B", status="CLEAR", factors=["F1"]),
            "C": _make_check("C", status="SKIPPED", factors=["F1"]),
        }
        evidence = _get_evidence_for_theory("A_DISCLOSURE", checks, ["F1"])
        assert len(evidence) == 1
        assert evidence[0].signal_id == "A"

    def test_matches_by_factor_or_lens(self) -> None:
        checks = {
            "A": _make_check("A", factors=["F1"], plaintiff_lenses=[]),
            "B": _make_check("B", factors=[], plaintiff_lenses=["SHAREHOLDERS"]),
            "C": _make_check("C", factors=["F99"], plaintiff_lenses=["CREDITORS"]),
        }
        evidence = _get_evidence_for_theory("A_DISCLOSURE", checks, ["F1"])
        ids = {e.signal_id for e in evidence}
        assert "A" in ids  # factor match
        assert "B" in ids  # lens match
        assert "C" not in ids  # neither


# -----------------------------------------------------------------------
# Test: Severity inference
# -----------------------------------------------------------------------


class TestSeverityInference:
    """Test severity inference from check data."""

    def test_red_threshold_is_critical(self) -> None:
        assert _infer_severity({"threshold_level": "red"}) == "CRITICAL"

    def test_yellow_threshold_is_high(self) -> None:
        assert _infer_severity({"threshold_level": "yellow"}) == "HIGH"

    def test_decision_driving_is_moderate(self) -> None:
        assert _infer_severity(
            {"threshold_level": "", "category": "DECISION_DRIVING"},
        ) == "MODERATE"

    def test_default_is_low(self) -> None:
        assert _infer_severity({}) == "LOW"


# -----------------------------------------------------------------------
# Test: Theory labels
# -----------------------------------------------------------------------


class TestTheoryLabels:
    """Test human-readable theory labels."""

    def test_all_theories_have_labels(self) -> None:
        from do_uw.models.scoring_output import AllegationTheory

        for theory in AllegationTheory:
            label = _theory_label(theory.value)
            assert label  # Not empty
            assert "_" not in label  # Human readable

    def test_specific_labels(self) -> None:
        assert _theory_label("A_DISCLOSURE") == "securities disclosure fraud"
        assert _theory_label("E_MA") == "M&A-related"


# -----------------------------------------------------------------------
# Test: Integration scenarios
# -----------------------------------------------------------------------


class TestIntegration:
    """Integration tests combining multiple components."""

    def test_bear_case_has_all_required_fields(self) -> None:
        mapping = {
            "theories": [_make_theory("A_DISCLOSURE", "HIGH", ["F1"])],
        }
        checks = {
            "FIN.1": _make_check("FIN.1", factors=["F1"], threshold_level="red"),
        }
        assessments = [_make_assessment("SHAREHOLDERS", "HIGH", "SIGNIFICANT")]
        result = build_bear_cases(mapping, checks, assessments, None, "TestCo")
        assert len(result) == 1
        bc = result[0]
        assert bc.theory == "A_DISCLOSURE"
        assert bc.plaintiff_type == "SHAREHOLDERS"
        assert len(bc.committee_summary) > 0
        assert bc.probability_band == "HIGH"
        assert bc.severity_estimate == "SIGNIFICANT"
        assert bc.supporting_signal_count >= 1

    def test_empty_theories_returns_empty(self) -> None:
        result = build_bear_cases(
            {"theories": []}, {}, [], None, "TestCo",
        )
        assert result == []

    def test_empty_mapping_returns_empty(self) -> None:
        result = build_bear_cases({}, {}, [], None, "TestCo")
        assert result == []
