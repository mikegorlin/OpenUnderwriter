"""Tests for quick screen: nuclear triggers, trigger matrix, prospective checks.

Phase 117 Plan 03 Task 2.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.forward_looking import (
    NuclearTriggerCheck,
    ProspectiveCheck,
    QuickScreenResult,
    TriggerMatrixRow,
)
from do_uw.models.state import AnalysisState, AnalysisResults, ExtractedData
from do_uw.stages.benchmark.quick_screen import (
    build_quick_screen,
    build_trigger_matrix,
    check_nuclear_triggers,
    compute_prospective_checks,
)

_NOW = datetime.now(tz=UTC)


def _sv(val: object, source: str = "test") -> SourcedValue:
    return SourcedValue(value=val, source=source, confidence=Confidence.HIGH, as_of=_NOW)


# ---------------------------------------------------------------------------
# Nuclear trigger fixtures
# ---------------------------------------------------------------------------


def _clean_state() -> AnalysisState:
    """State with no litigation, no restatements, etc."""
    return AnalysisState(ticker="TEST")


def _state_with_active_sca() -> AnalysisState:
    """State with an active SCA in litigation."""
    from do_uw.models.litigation import CaseDetail, LitigationLandscape

    lit = LitigationLandscape(
        securities_class_actions=[
            CaseDetail(
                case_name=_sv("Smith v. Test Corp", "Stanford SCAC"),
            ),
        ]
    )
    return AnalysisState(
        ticker="TEST",
        extracted=ExtractedData(litigation=lit),
    )


def _state_with_going_concern() -> AnalysisState:
    """State with going concern flag."""
    from do_uw.models.financials import AuditProfile, ExtractedFinancials

    audit = AuditProfile(going_concern=_sv(True, "10-K audit opinion"))
    fin = ExtractedFinancials(audit=audit)
    return AnalysisState(
        ticker="TEST",
        extracted=ExtractedData(financials=fin),
    )


# ---------------------------------------------------------------------------
# Signal result fixtures for trigger matrix
# ---------------------------------------------------------------------------


def _make_signal_results_with_flags() -> dict[str, Any]:
    """Signal results with RED/YELLOW triggered signals."""
    return {
        "SCAC.ACTIVE_MATCH": {
            "status": "TRIGGERED",
            "threshold_level": "red",
            "value": True,
            "evidence": "Active SCA found",
            "source": "Stanford SCAC",
            "content_type": "EVALUATIVE_CHECK",
            "do_context": "Direct D&O loss exposure from pending litigation",
            "confidence": "HIGH",
        },
        "FIN.RESTATEMENT": {
            "status": "TRIGGERED",
            "threshold_level": "yellow",
            "value": True,
            "evidence": "Material weakness noted",
            "source": "10-K",
            "content_type": "EVALUATIVE_CHECK",
            "do_context": "Restatement creates 10b-5 exposure",
            "confidence": "HIGH",
        },
        "MKT.SHORT_ELEVATED": {
            "status": "TRIGGERED",
            "threshold_level": "yellow",
            "value": 12.5,
            "evidence": "Short interest 12.5% vs 3% sector avg",
            "source": "yfinance",
            "content_type": "EVALUATIVE_CHECK",
            "do_context": "Elevated short interest signals market skepticism",
            "confidence": "MEDIUM",
        },
        "GOV.CLEAN_AUDIT": {
            "status": "CLEAR",
            "threshold_level": "",
            "value": True,
            "evidence": "Clean audit",
            "source": "10-K",
            "content_type": "EVALUATIVE_CHECK",
            "do_context": "",
            "confidence": "HIGH",
        },
        "DISPLAY.HEADER": {
            "status": "TRIGGERED",
            "threshold_level": "red",
            "value": "header text",
            "evidence": "Display only",
            "source": "template",
            "content_type": "DISPLAY_ELEMENT",
            "do_context": "",
            "confidence": "HIGH",
        },
    }


def _make_clean_signal_results() -> dict[str, Any]:
    """Signal results with all CLEAR -- no RED/YELLOW."""
    return {
        "SCAC.ACTIVE_MATCH": {
            "status": "CLEAR",
            "threshold_level": "",
            "value": False,
            "evidence": "No match",
            "source": "Stanford SCAC",
            "content_type": "EVALUATIVE_CHECK",
            "do_context": "",
            "confidence": "HIGH",
        },
        "FIN.RESTATEMENT": {
            "status": "CLEAR",
            "threshold_level": "",
            "value": False,
            "evidence": "No restatement",
            "source": "10-K",
            "content_type": "EVALUATIVE_CHECK",
            "do_context": "",
            "confidence": "HIGH",
        },
    }


# ---------------------------------------------------------------------------
# Test: check_nuclear_triggers
# ---------------------------------------------------------------------------


class TestCheckNuclearTriggers:
    def test_clean_state_returns_five_checks_all_false(self) -> None:
        state = _clean_state()
        checks = check_nuclear_triggers(state)

        assert len(checks) == 5
        assert all(isinstance(c, NuclearTriggerCheck) for c in checks)
        assert all(not c.fired for c in checks)

    def test_active_sca_fires_nuc01(self) -> None:
        state = _state_with_active_sca()
        checks = check_nuclear_triggers(state)

        nuc01 = [c for c in checks if c.trigger_id == "NUC-01"]
        assert len(nuc01) == 1
        assert nuc01[0].fired is True
        assert nuc01[0].evidence != ""

    def test_going_concern_fires_nuc05(self) -> None:
        state = _state_with_going_concern()
        checks = check_nuclear_triggers(state)

        nuc05 = [c for c in checks if c.trigger_id == "NUC-05"]
        assert len(nuc05) == 1
        assert nuc05[0].fired is True
        assert "going concern" in nuc05[0].evidence.lower() or "Going concern" in nuc05[0].evidence

    def test_clean_state_has_positive_evidence(self) -> None:
        state = _clean_state()
        checks = check_nuclear_triggers(state)

        # Every clean check should have evidence explaining WHY it's clean
        for check in checks:
            assert check.evidence != "", f"{check.trigger_id} missing evidence"


# ---------------------------------------------------------------------------
# Test: build_trigger_matrix
# ---------------------------------------------------------------------------


class TestBuildTriggerMatrix:
    def test_filters_to_red_yellow_evaluative_only(self) -> None:
        signals = _make_signal_results_with_flags()
        matrix = build_trigger_matrix(signals)

        # Should include SCAC.ACTIVE_MATCH (red), FIN.RESTATEMENT (yellow),
        # MKT.SHORT_ELEVATED (yellow)
        # Should exclude GOV.CLEAN_AUDIT (CLEAR) and DISPLAY.HEADER (DISPLAY_ELEMENT)
        signal_ids = [r.signal_id for r in matrix]
        assert "SCAC.ACTIVE_MATCH" in signal_ids
        assert "FIN.RESTATEMENT" in signal_ids
        assert "MKT.SHORT_ELEVATED" in signal_ids
        assert "GOV.CLEAN_AUDIT" not in signal_ids
        assert "DISPLAY.HEADER" not in signal_ids

    def test_sorts_red_before_yellow(self) -> None:
        signals = _make_signal_results_with_flags()
        matrix = build_trigger_matrix(signals)

        if len(matrix) >= 2:
            assert matrix[0].flag_level == "RED"

    def test_clean_company_returns_empty(self) -> None:
        signals = _make_clean_signal_results()
        matrix = build_trigger_matrix(signals)

        assert len(matrix) == 0

    def test_matrix_rows_have_section(self) -> None:
        signals = _make_signal_results_with_flags()
        matrix = build_trigger_matrix(signals)

        for row in matrix:
            assert row.section != "", f"{row.signal_id} missing section"

    def test_groups_by_section_top3(self) -> None:
        """If many signals in same section, only top 3 per section."""
        signals = {}
        for i in range(6):
            signals[f"FIN.TEST_{i}"] = {
                "status": "TRIGGERED",
                "threshold_level": "yellow",
                "value": True,
                "evidence": f"Test {i}",
                "source": "test",
                "content_type": "EVALUATIVE_CHECK",
                "do_context": f"Test context {i}",
                "confidence": "MEDIUM",
            }
        matrix = build_trigger_matrix(signals)

        # Count signals per section
        from collections import Counter

        section_counts = Counter(r.section for r in matrix)
        for _section, count in section_counts.items():
            assert count <= 3, f"Section {_section} has {count} items, expected <=3"


# ---------------------------------------------------------------------------
# Test: compute_prospective_checks
# ---------------------------------------------------------------------------


class TestComputeProspectiveChecks:
    def test_returns_five_checks(self) -> None:
        state = _clean_state()
        checks = compute_prospective_checks(state)

        assert len(checks) == 5
        assert all(isinstance(c, ProspectiveCheck) for c in checks)

    def test_checks_have_names(self) -> None:
        state = _clean_state()
        checks = compute_prospective_checks(state)

        for check in checks:
            assert check.check_name != ""
            assert check.status in ("GREEN", "YELLOW", "RED", "UNKNOWN")


# ---------------------------------------------------------------------------
# Test: build_quick_screen
# ---------------------------------------------------------------------------


class TestBuildQuickScreen:
    def test_assembles_all_components(self) -> None:
        state = _clean_state()
        signals = _make_signal_results_with_flags()
        result = build_quick_screen(state, signals)

        assert isinstance(result, QuickScreenResult)
        assert len(result.nuclear_triggers) == 5
        assert len(result.prospective_checks) == 5
        assert len(result.trigger_matrix) >= 1

    def test_counts_correct(self) -> None:
        state = _clean_state()
        signals = _make_signal_results_with_flags()
        result = build_quick_screen(state, signals)

        assert result.red_count == sum(1 for r in result.trigger_matrix if r.flag_level == "RED")
        assert result.yellow_count == sum(
            1 for r in result.trigger_matrix if r.flag_level == "YELLOW"
        )

    def test_nuclear_fired_count_matches(self) -> None:
        state = _state_with_active_sca()
        signals = _make_clean_signal_results()
        result = build_quick_screen(state, signals)

        assert result.nuclear_fired_count == sum(
            1 for nt in result.nuclear_triggers if nt.fired
        )
        assert result.nuclear_fired_count >= 1  # NUC-01 should fire
