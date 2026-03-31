"""Tests for traceability chain completeness on SignalResult.

Validates the 5-link traceability chain (DATA_SOURCE, EXTRACTION,
EVALUATION, OUTPUT, SCORING) and the traceability_complete /
traceability_gaps helper properties.
"""

from __future__ import annotations

import pytest

from do_uw.stages.analyze.signal_results import SignalResult, SignalStatus


class TestTraceabilityFields:
    """Tests for the 5 trace fields and helper properties."""

    def test_all_fields_populated_is_complete(self) -> None:
        """SignalResult with all 5 trace fields -> traceability_complete True."""
        result = SignalResult(
            signal_id="FIN.LIQ.position",
            signal_name="Liquidity Position",
            status=SignalStatus.CLEAR,
            trace_data_source="SEC_10K:xbrl_current_ratio",
            trace_extraction="xbrl_extractor",
            trace_evaluation="tiered_threshold:clear",
            trace_output="SECT3:P1_WHAT_WRONG",
            trace_scoring="F1",
        )
        assert result.traceability_complete is True
        assert result.traceability_gaps == []

    def test_no_fields_populated_has_all_gaps(self) -> None:
        """SignalResult with 0 trace fields -> 5 gaps."""
        result = SignalResult(
            signal_id="test.empty",
            signal_name="No Trace",
            status=SignalStatus.CLEAR,
        )
        assert result.traceability_complete is False
        gaps = result.traceability_gaps
        assert len(gaps) == 5
        assert "DATA_SOURCE" in gaps
        assert "EXTRACTION" in gaps
        assert "EVALUATION" in gaps
        assert "OUTPUT" in gaps
        assert "SCORING" in gaps

    def test_partial_fields_correct_gaps(self) -> None:
        """SignalResult with 3 of 5 fields -> correct partial gaps."""
        result = SignalResult(
            signal_id="FIN.LEV.debt_equity",
            signal_name="Debt to Equity",
            status=SignalStatus.TRIGGERED,
            trace_data_source="SEC_10K:xbrl_debt_to_equity",
            trace_extraction="xbrl_extractor",
            trace_evaluation="tiered_threshold:red",
            # trace_output and trace_scoring intentionally omitted
        )
        assert result.traceability_complete is False
        gaps = result.traceability_gaps
        assert len(gaps) == 2
        assert "OUTPUT" in gaps
        assert "SCORING" in gaps
        assert "DATA_SOURCE" not in gaps
        assert "EXTRACTION" not in gaps
        assert "EVALUATION" not in gaps

    def test_empty_string_counts_as_gap(self) -> None:
        """Empty string '' should count as a gap (default value)."""
        result = SignalResult(
            signal_id="test.empty_str",
            signal_name="Empty Strings",
            status=SignalStatus.INFO,
            trace_data_source="",  # explicitly empty
            trace_extraction="xbrl_extractor",
            trace_evaluation="info_display:info",
            trace_output="SECT1:P1",
            trace_scoring="none:context_only",
        )
        assert result.traceability_complete is False
        assert result.traceability_gaps == ["DATA_SOURCE"]


class TestEngineTracePopulation:
    """Tests that the check engine populates trace fields."""

    def test_evaluate_signal_populates_trace_evaluation(self) -> None:
        """evaluate_signal should set trace_evaluation from threshold type."""
        from do_uw.stages.analyze.signal_engine import evaluate_signal

        check = {
            "id": "FIN.LIQ.test",
            "name": "Test Liquidity",
            "section": 3,
            "pillar": "P1_WHAT_WRONG",
            "factors": ["F1"],
            "required_data": ["SEC_10K"],
            "data_locations": {"SEC_10K": ["xbrl_data"]},
            "threshold": {"type": "tiered", "red": "<1.0", "yellow": "<1.5"},
            "execution_mode": "AUTO",
        }
        data = {"current_ratio": 0.5}

        result = evaluate_signal(check, data)

        assert result.trace_evaluation != ""
        assert "tiered" in result.trace_evaluation

    def test_evaluate_signal_populates_trace_scoring(self) -> None:
        """evaluate_signal should set trace_scoring from factors."""
        from do_uw.stages.analyze.signal_engine import evaluate_signal

        check = {
            "id": "FIN.LEV.test",
            "name": "Test Leverage",
            "section": 3,
            "pillar": "P1_WHAT_WRONG",
            "factors": ["F1", "F3"],
            "required_data": ["SEC_10K"],
            "data_locations": {"SEC_10K": ["xbrl_data"]},
            "threshold": {"type": "tiered", "red": ">5.0"},
            "execution_mode": "AUTO",
        }
        data = {"debt_equity": 6.0}

        result = evaluate_signal(check, data)

        assert result.trace_scoring == "F1,F3"

    def test_evaluate_signal_populates_trace_output(self) -> None:
        """evaluate_signal should set trace_output from section + pillar."""
        from do_uw.stages.analyze.signal_engine import evaluate_signal

        check = {
            "id": "GOV.BOARD.test",
            "name": "Test Board",
            "section": 5,
            "pillar": "P2_WHO_SUE",
            "factors": [],
            "required_data": ["SEC_PROXY"],
            "data_locations": {"SEC_PROXY": ["proxy_data"]},
            "threshold": {"type": "info"},
            "execution_mode": "AUTO",
        }
        data = {"board_size": 9}

        result = evaluate_signal(check, data)

        assert result.trace_output == "SECT5:P2_WHO_SUE"

    def test_evaluate_signal_populates_trace_data_source(self) -> None:
        """evaluate_signal should set trace_data_source from data_locations."""
        from do_uw.stages.analyze.signal_engine import evaluate_signal

        check = {
            "id": "LIT.SCA.test",
            "name": "Test Litigation",
            "section": 6,
            "pillar": "P3_HOW_BAD",
            "factors": ["F5"],
            "required_data": ["SCAC_SEARCH", "SEC_10K"],
            "data_locations": {
                "SCAC_SEARCH": ["search_results"],
                "SEC_10K": ["item_3_legal"],
            },
            "threshold": {"type": "tiered", "red": "Active SCA"},
            "execution_mode": "AUTO",
        }
        data = {"sca_count": 2}

        result = evaluate_signal(check, data)

        assert "SCAC_SEARCH" in result.trace_data_source
        assert "SEC_10K" in result.trace_data_source

    def test_context_only_check_scoring_trace(self) -> None:
        """CONTEXT_DISPLAY check with no factors -> 'none:context_only'."""
        from do_uw.stages.analyze.signal_engine import evaluate_signal

        check = {
            "id": "BIZ.CLASS.test",
            "name": "Test Classification",
            "section": 1,
            "pillar": "P1_WHAT_WRONG",
            "factors": [],
            "required_data": ["SEC_10K"],
            "data_locations": {"SEC_10K": ["item_1"]},
            "threshold": {"type": "classification"},
            "execution_mode": "AUTO",
            "category": "CONTEXT_DISPLAY",
        }
        data = {"classification": "STABLE_MATURE"}

        result = evaluate_signal(check, data)

        assert result.trace_scoring == "none:context_only"

    def test_skipped_check_still_has_trace(self) -> None:
        """SKIPPED checks should still have trace fields populated."""
        from do_uw.stages.analyze.signal_engine import evaluate_signal

        check = {
            "id": "FIN.DIST.test",
            "name": "Test Distress",
            "section": 3,
            "pillar": "P1_WHAT_WRONG",
            "factors": ["F1"],
            "required_data": ["SEC_10K"],
            "data_locations": {"SEC_10K": ["xbrl_data"]},
            "threshold": {"type": "tiered", "red": "<1.8"},
            "execution_mode": "AUTO",
        }
        data = {}  # No data -> SKIPPED

        result = evaluate_signal(check, data)

        assert result.status == SignalStatus.SKIPPED
        assert result.trace_evaluation != ""
        assert "skipped" in result.trace_evaluation
        assert result.trace_output == "SECT3:P1_WHAT_WRONG"
        assert result.trace_scoring == "F1"

    def test_list_data_locations_handled(self) -> None:
        """Industry playbook checks with list data_locations should work."""
        from do_uw.stages.analyze.signal_engine import evaluate_signal

        check = {
            "id": "TECH.REV.test",
            "name": "Test Tech Revenue",
            "section": 3,
            "pillar": "P1_WHAT_WRONG",
            "factors": [],
            "required_data": ["SEC_10K"],
            "data_locations": ["extracted.financials"],  # list, not dict
            "threshold": {"type": "info"},
            "execution_mode": "AUTO",
        }
        data = {"revenue": 1000}

        result = evaluate_signal(check, data)

        assert "extracted.financials" in result.trace_data_source


class TestTraceabilityDefaults:
    """Test backward compatibility of trace fields."""

    def test_existing_signal_result_no_trace(self) -> None:
        """Pre-Phase30 SignalResults should still work with empty trace."""
        result = SignalResult(
            signal_id="old.check",
            signal_name="Old Check",
            status=SignalStatus.CLEAR,
            value=42.0,
            evidence="Some evidence",
        )
        # All trace fields default to empty
        assert result.trace_data_source == ""
        assert result.trace_extraction == ""
        assert result.trace_evaluation == ""
        assert result.trace_output == ""
        assert result.trace_scoring == ""
        assert result.traceability_complete is False
        assert len(result.traceability_gaps) == 5

    def test_model_dump_includes_trace_fields(self) -> None:
        """model_dump should include all trace fields."""
        result = SignalResult(
            signal_id="test",
            signal_name="Test",
            status=SignalStatus.INFO,
            trace_data_source="SEC_10K:item_1",
        )
        dumped = result.model_dump()
        assert "trace_data_source" in dumped
        assert "trace_extraction" in dumped
        assert "trace_evaluation" in dumped
        assert "trace_output" in dumped
        assert "trace_scoring" in dumped
        assert dumped["trace_data_source"] == "SEC_10K:item_1"
