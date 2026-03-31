"""Tests for DataStatus enum and data_status fields on SignalResult.

Phase 27 Plan 01 Task 1: Three-state data pipeline status.
"""

from __future__ import annotations

import pytest

from do_uw.stages.analyze.signal_results import (
    SignalResult,
    SignalStatus,
    DataStatus,
)


class TestDataStatusEnum:
    """DataStatus enum has all 3 values."""

    def test_enum_has_evaluated(self) -> None:
        assert DataStatus.EVALUATED == "EVALUATED"

    def test_enum_has_data_unavailable(self) -> None:
        assert DataStatus.DATA_UNAVAILABLE == "DATA_UNAVAILABLE"

    def test_enum_has_not_applicable(self) -> None:
        assert DataStatus.NOT_APPLICABLE == "NOT_APPLICABLE"

    def test_enum_has_exactly_three_members(self) -> None:
        assert len(DataStatus) == 3

    def test_is_str_enum(self) -> None:
        """DataStatus values are strings (for JSON serialization)."""
        assert isinstance(DataStatus.EVALUATED, str)
        assert isinstance(DataStatus.DATA_UNAVAILABLE, str)
        assert isinstance(DataStatus.NOT_APPLICABLE, str)


class TestSignalResultDataStatus:
    """SignalResult.data_status field with backward-compatible defaults."""

    def test_default_data_status_is_evaluated(self) -> None:
        """New SignalResult defaults to EVALUATED."""
        result = SignalResult(
            signal_id="TEST.001",
            signal_name="Test Check",
            status=SignalStatus.TRIGGERED,
        )
        assert result.data_status == "EVALUATED"
        assert result.data_status_reason == ""

    def test_backward_compatibility_no_data_status(self) -> None:
        """Existing SignalResult construction (without data_status) still works."""
        result = SignalResult(
            signal_id="FIN.LIQ.position",
            signal_name="Liquidity Position",
            status=SignalStatus.CLEAR,
            value=1.8,
            threshold_level="clear",
            evidence="Value 1.8 above thresholds",
            source="current_ratio",
            factors=["F1"],
            section=3,
        )
        assert result.data_status == "EVALUATED"
        assert result.data_status_reason == ""
        # Original fields unaffected
        assert result.signal_id == "FIN.LIQ.position"
        assert result.value == 1.8

    def test_skipped_with_data_unavailable(self) -> None:
        """SKIPPED result can have data_status=DATA_UNAVAILABLE."""
        result = SignalResult(
            signal_id="FIN.LIQ.position",
            signal_name="Liquidity Position",
            status=SignalStatus.SKIPPED,
            data_status=DataStatus.DATA_UNAVAILABLE,
            data_status_reason="Required field 'current_ratio' not available",
        )
        assert result.status == SignalStatus.SKIPPED
        assert result.data_status == "DATA_UNAVAILABLE"
        assert "current_ratio" in result.data_status_reason

    def test_not_applicable_status(self) -> None:
        """Check marked NOT_APPLICABLE for wrong sector."""
        result = SignalResult(
            signal_id="FIN.SECTOR.biotech",
            signal_name="Biotech R&D Burn",
            status=SignalStatus.SKIPPED,
            data_status=DataStatus.NOT_APPLICABLE,
            data_status_reason="Sector filter biotech does not match SIC 7372",
        )
        assert result.data_status == "NOT_APPLICABLE"
        assert "biotech" in result.data_status_reason

    def test_model_dump_includes_data_status(self) -> None:
        """data_status fields appear in model_dump() for storage."""
        result = SignalResult(
            signal_id="TEST.001",
            signal_name="Test",
            status=SignalStatus.CLEAR,
            data_status=DataStatus.DATA_UNAVAILABLE,
            data_status_reason="No data",
        )
        dumped = result.model_dump()
        assert "data_status" in dumped
        assert dumped["data_status"] == "DATA_UNAVAILABLE"
        assert dumped["data_status_reason"] == "No data"


class TestDetermineDataStatus:
    """_determine_data_status helper logic in signal_engine."""

    def test_skipped_result_gets_data_unavailable(self) -> None:
        """SKIPPED results are marked DATA_UNAVAILABLE."""
        from do_uw.stages.analyze.signal_engine import _determine_data_status

        result = SignalResult(
            signal_id="TEST.001",
            signal_name="Test",
            status=SignalStatus.SKIPPED,
            evidence="Required data unavailable",
        )
        check: dict = {"id": "TEST.001", "name": "Test"}
        data: dict = {"field_a": None, "field_b": None}
        _determine_data_status(check, data, result)
        assert result.data_status == "DATA_UNAVAILABLE"

    def test_triggered_result_stays_evaluated(self) -> None:
        """TRIGGERED results remain EVALUATED."""
        from do_uw.stages.analyze.signal_engine import _determine_data_status

        result = SignalResult(
            signal_id="TEST.002",
            signal_name="Test",
            status=SignalStatus.TRIGGERED,
        )
        check: dict = {"id": "TEST.002", "name": "Test"}
        data: dict = {"field_a": 42}
        _determine_data_status(check, data, result)
        assert result.data_status == "EVALUATED"

    def test_clear_result_stays_evaluated(self) -> None:
        """CLEAR results remain EVALUATED."""
        from do_uw.stages.analyze.signal_engine import _determine_data_status

        result = SignalResult(
            signal_id="TEST.003",
            signal_name="Test",
            status=SignalStatus.CLEAR,
        )
        check: dict = {"id": "TEST.003", "name": "Test"}
        data: dict = {"field_a": 1.5}
        _determine_data_status(check, data, result)
        assert result.data_status == "EVALUATED"

    def test_info_result_stays_evaluated(self) -> None:
        """INFO results remain EVALUATED."""
        from do_uw.stages.analyze.signal_engine import _determine_data_status

        result = SignalResult(
            signal_id="TEST.004",
            signal_name="Test",
            status=SignalStatus.INFO,
        )
        check: dict = {"id": "TEST.004", "name": "Test"}
        data: dict = {"field_a": "some_value"}
        _determine_data_status(check, data, result)
        assert result.data_status == "EVALUATED"


class TestCheckSectorApplicability:
    """_check_sector_applicability helper for NOT_APPLICABLE detection."""

    def test_no_sector_filter_is_applicable(self) -> None:
        from do_uw.stages.analyze.signal_engine import _check_sector_applicability

        assert _check_sector_applicability({"id": "TEST"}, "7372") is True

    def test_matching_sector_filter_is_applicable(self) -> None:
        from do_uw.stages.analyze.signal_engine import _check_sector_applicability

        check = {"id": "TEST", "sector_filter": ["7372", "7371"]}
        assert _check_sector_applicability(check, "7372") is True

    def test_non_matching_sector_filter_not_applicable(self) -> None:
        from do_uw.stages.analyze.signal_engine import _check_sector_applicability

        check = {"id": "TEST", "sector_filter": ["2834", "2836"]}
        assert _check_sector_applicability(check, "7372") is False

    def test_no_company_sic_is_applicable(self) -> None:
        from do_uw.stages.analyze.signal_engine import _check_sector_applicability

        check = {"id": "TEST", "sector_filter": ["2834"]}
        assert _check_sector_applicability(check, None) is True

    def test_string_sector_filter_match(self) -> None:
        from do_uw.stages.analyze.signal_engine import _check_sector_applicability

        check = {"id": "TEST", "sector_filter": "7372"}
        assert _check_sector_applicability(check, "7372") is True

    def test_string_sector_filter_no_match(self) -> None:
        from do_uw.stages.analyze.signal_engine import _check_sector_applicability

        check = {"id": "TEST", "sector_filter": "2834"}
        assert _check_sector_applicability(check, "7372") is False


class TestMakeSkippedSetsDataStatus:
    """_make_skipped helper sets data_status=DATA_UNAVAILABLE."""

    def test_make_skipped_with_mapped_fields(self) -> None:
        from do_uw.stages.analyze.signal_engine import _make_skipped

        check = {"id": "FIN.LIQ.position", "name": "Liquidity", "section": 3}
        data = {"current_ratio": None, "quick_ratio": None}
        result = _make_skipped(check, data)
        assert result.status == SignalStatus.SKIPPED
        assert result.data_status == "DATA_UNAVAILABLE"
        assert "Required data not available from filings" in result.data_status_reason

    def test_make_skipped_with_no_fields(self) -> None:
        from do_uw.stages.analyze.signal_engine import _make_skipped

        check = {"id": "FWRD.WARN.unknown", "name": "Unknown", "section": 0}
        data: dict = {}
        result = _make_skipped(check, data)
        assert result.data_status == "DATA_UNAVAILABLE"
        assert "Data mapping not configured" in result.data_status_reason
