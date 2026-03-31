"""Tests for quick screen context builder.

Phase 117: Forward-Looking Risk Framework
"""

from __future__ import annotations

import pytest

from do_uw.models.forward_looking import (
    ForwardLookingData,
    NuclearTriggerCheck,
    ProspectiveCheck,
    QuickScreenResult,
    TriggerMatrixRow,
)
from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders.quick_screen_context import (
    extract_quick_screen,
)


def _make_state(**kwargs: object) -> AnalysisState:
    """Build minimal AnalysisState with forward_looking data."""
    fl = ForwardLookingData(**kwargs)  # type: ignore[arg-type]
    return AnalysisState(ticker="TEST", forward_looking=fl)


def _make_clean_nuclear() -> list[NuclearTriggerCheck]:
    """Build 5 clean nuclear triggers."""
    return [
        NuclearTriggerCheck(
            trigger_id=f"NUC-0{i}",
            name=f"Nuclear Trigger {i}",
            fired=False,
            evidence="Clean",
            source="computed",
        )
        for i in range(1, 6)
    ]


class TestQuickScreenNuclear:
    """Tests for nuclear trigger display in extract_quick_screen."""

    def test_clean_nuclear_display(self) -> None:
        """Zero fired nuclear triggers produce clean display string."""
        qs = QuickScreenResult(
            nuclear_triggers=_make_clean_nuclear(),
            nuclear_fired_count=0,
        )
        state = _make_state(quick_screen=qs)
        result = extract_quick_screen(state, {})

        assert result["quick_screen_available"] is True
        assert result["nuclear_clean"] is True
        assert result["nuclear_fired_count"] == 0
        assert result["nuclear_display"] == "0/5 nuclear triggers fired"

    def test_two_fired_nuclear_display(self) -> None:
        """Two fired nuclear triggers produce uppercase warning display."""
        triggers = _make_clean_nuclear()
        triggers[0] = NuclearTriggerCheck(
            trigger_id="NUC-01", name="Active SEC Investigation",
            fired=True, evidence="SEC subpoena served", source="10-K",
        )
        triggers[2] = NuclearTriggerCheck(
            trigger_id="NUC-03", name="Restatement Announced",
            fired=True, evidence="Material restatement of 3 quarters",
            source="8-K",
        )
        qs = QuickScreenResult(
            nuclear_triggers=triggers,
            nuclear_fired_count=2,
        )
        state = _make_state(quick_screen=qs)
        result = extract_quick_screen(state, {})

        assert result["nuclear_clean"] is False
        assert result["nuclear_fired_count"] == 2
        assert result["nuclear_display"] == "2/5 NUCLEAR TRIGGERS FIRED"
        # Check fired/clean icons
        assert result["nuclear_triggers"][0]["icon"] == "fired"
        assert result["nuclear_triggers"][1]["icon"] == "clean"
        assert result["nuclear_triggers"][2]["icon"] == "fired"


class TestQuickScreenTriggerMatrix:
    """Tests for trigger matrix in extract_quick_screen."""

    def test_trigger_matrix_section_grouping(self) -> None:
        """Trigger matrix rows are grouped by section."""
        rows = [
            TriggerMatrixRow(
                signal_id="FIN.REV.decline", signal_name="Revenue Decline",
                flag_level="RED", section="Financials", section_anchor="sect3",
                do_context="Revenue miss creates 10b-5 exposure",
            ),
            TriggerMatrixRow(
                signal_id="FIN.EPS.miss", signal_name="EPS Miss",
                flag_level="YELLOW", section="Financials", section_anchor="sect3",
                do_context="EPS guidance failure",
            ),
            TriggerMatrixRow(
                signal_id="GOV.BOARD.turnover", signal_name="Board Turnover",
                flag_level="RED", section="Governance", section_anchor="sect5",
                do_context="Director departure may signal internal issues",
            ),
        ]
        qs = QuickScreenResult(
            trigger_matrix=rows, red_count=2, yellow_count=1,
        )
        state = _make_state(quick_screen=qs)
        result = extract_quick_screen(state, {})

        assert len(result["trigger_matrix"]) == 3
        assert "Financials" in result["trigger_matrix_by_section"]
        assert "Governance" in result["trigger_matrix_by_section"]
        assert len(result["trigger_matrix_by_section"]["Financials"]) == 2
        assert len(result["trigger_matrix_by_section"]["Governance"]) == 1

    def test_flag_class_css_mapping(self) -> None:
        """Flag levels map to correct CSS classes."""
        rows = [
            TriggerMatrixRow(signal_id="A", flag_level="RED", section="S1"),
            TriggerMatrixRow(signal_id="B", flag_level="YELLOW", section="S1"),
        ]
        qs = QuickScreenResult(
            trigger_matrix=rows, red_count=1, yellow_count=1,
        )
        state = _make_state(quick_screen=qs)
        result = extract_quick_screen(state, {})

        assert result["trigger_matrix"][0]["flag_class"] == "flag-red"
        assert result["trigger_matrix"][1]["flag_class"] == "flag-yellow"
        assert result["red_count"] == 1
        assert result["yellow_count"] == 1
        assert result["total_flags"] == 2


class TestQuickScreenProspective:
    """Tests for prospective checks in extract_quick_screen."""

    def test_prospective_check_status_class(self) -> None:
        """Prospective check statuses map to correct CSS classes."""
        checks = [
            ProspectiveCheck(check_name="Guidance Track", finding="On track", status="GREEN"),
            ProspectiveCheck(check_name="Insider Activity", finding="Elevated sales", status="YELLOW"),
            ProspectiveCheck(check_name="SEC Investigation", finding="Active probe", status="RED"),
            ProspectiveCheck(check_name="Pending Item", finding="No data", status="UNKNOWN"),
        ]
        qs = QuickScreenResult(prospective_checks=checks)
        state = _make_state(quick_screen=qs)
        result = extract_quick_screen(state, {})

        assert result["has_prospective_checks"] is True
        assert result["prospective_checks"][0]["status_class"] == "status-green"
        assert result["prospective_checks"][1]["status_class"] == "status-yellow"
        assert result["prospective_checks"][2]["status_class"] == "status-red"
        assert result["prospective_checks"][3]["status_class"] == "status-unknown"

    def test_empty_quick_screen(self) -> None:
        """No quick screen data returns quick_screen_available=False."""
        state = _make_state()
        result = extract_quick_screen(state, {})

        assert result["quick_screen_available"] is False
        assert result["nuclear_clean"] is True
        assert result["nuclear_display"] == "0/5 nuclear triggers fired"
        assert result["trigger_matrix"] == []
        assert result["trigger_matrix_by_section"] == {}
        assert result["has_prospective_checks"] is False
        assert result["red_count"] == 0
        assert result["yellow_count"] == 0
        assert result["total_flags"] == 0
