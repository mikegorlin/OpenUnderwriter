"""Tests for pipeline audit tooling.

Phase 27 Plan 01 Task 2: Identify unwired checks programmatically.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from do_uw.stages.analyze.pipeline_audit import (
    audit_all_checks,
    audit_check_pipeline,
    format_audit_report,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


class _FakeExtracted:
    """Minimal stub for ExtractedData."""

    financials = None
    market = None
    governance = None
    litigation = None


class _FakeCompany:
    """Minimal stub for CompanyProfile."""

    class identity:
        sic_code = None
        sector = None
        exchange = None
        state_of_incorporation = None

    market_cap = None
    years_public = None
    business_description = None
    subsidiary_count = None
    employee_count = None
    risk_classification = None
    section_summary = None
    industry_classification = None
    geographic_footprint = None
    customer_concentration = None


_MOCK_CLASSIFICATION = {
    "prefix_defaults": {
        "FIN.LIQ": {
            "category": "DECISION_DRIVING",
            "signal_type": "LEVEL",
            "hazard_or_signal": "SIGNAL",
        },
        "FWRD.WARN": {
            "category": "DECISION_DRIVING",
            "signal_type": "EVENT",
            "hazard_or_signal": "SIGNAL",
        },
        "BIZ.CLASS": {
            "category": "CONTEXT_DISPLAY",
            "signal_type": "STRUCTURAL",
            "hazard_or_signal": "HAZARD",
        },
    },
    "plaintiff_lens_defaults": {
        "FIN.LIQ": ["CREDITORS", "SHAREHOLDERS"],
        "FWRD.WARN": ["SHAREHOLDERS", "REGULATORS"],
        "BIZ.CLASS": ["SHAREHOLDERS"],
    },
    "override_decision_driving": {"signals": []},
}


# ---------------------------------------------------------------------------
# audit_check_pipeline tests
# ---------------------------------------------------------------------------


class TestAuditCheckPipeline:
    """Test audit_check_pipeline with mocked mappers."""

    def test_check_with_no_mapper_returns_no_mapper(self) -> None:
        """Check with empty mapper result is NO_MAPPER."""
        with patch(
            "do_uw.stages.analyze.signal_mappers.map_signal_data",
            return_value={},
        ):
            result = audit_check_pipeline(
                "FWRD.WARN.unknown",
                {"id": "FWRD.WARN.unknown", "execution_mode": "AUTO", "section": 0},
                _FakeExtracted(),  # type: ignore[arg-type]
                None,
                _MOCK_CLASSIFICATION,
            )

        assert result["signal_id"] == "FWRD.WARN.unknown"
        assert result["has_mapper"] is False
        assert result["data_status"] == "NO_MAPPER"
        assert result["mapped_fields"] == []
        assert result["non_none_fields"] == []

    def test_check_with_all_none_returns_all_none(self) -> None:
        """Check with mapper but all None values is ALL_NONE."""
        with patch(
            "do_uw.stages.analyze.signal_mappers.map_signal_data",
            return_value={"current_ratio": None, "quick_ratio": None},
        ):
            result = audit_check_pipeline(
                "FIN.LIQ.position",
                {"id": "FIN.LIQ.position", "execution_mode": "AUTO", "section": 3},
                _FakeExtracted(),  # type: ignore[arg-type]
                None,
                _MOCK_CLASSIFICATION,
            )

        assert result["has_mapper"] is True
        assert result["all_values_none"] is True
        assert result["data_status"] == "ALL_NONE"
        assert result["mapped_fields"] == ["current_ratio", "quick_ratio"]
        assert result["non_none_fields"] == []

    def test_check_with_data_returns_has_data(self) -> None:
        """Check with actual data is HAS_DATA."""
        with patch(
            "do_uw.stages.analyze.signal_mappers.map_signal_data",
            return_value={"current_ratio": 1.8, "quick_ratio": None},
        ):
            result = audit_check_pipeline(
                "FIN.LIQ.position",
                {"id": "FIN.LIQ.position", "execution_mode": "AUTO", "section": 3},
                _FakeExtracted(),  # type: ignore[arg-type]
                None,
                _MOCK_CLASSIFICATION,
            )

        assert result["has_mapper"] is True
        assert result["all_values_none"] is False
        assert result["data_status"] == "HAS_DATA"
        assert result["non_none_fields"] == ["current_ratio"]

    def test_category_resolved_from_classification(self) -> None:
        """Category is resolved from classification config."""
        with patch(
            "do_uw.stages.analyze.signal_mappers.map_signal_data",
            return_value={"current_ratio": 1.5},
        ):
            result = audit_check_pipeline(
                "FIN.LIQ.position",
                {"id": "FIN.LIQ.position", "execution_mode": "AUTO", "section": 3},
                _FakeExtracted(),  # type: ignore[arg-type]
                None,
                _MOCK_CLASSIFICATION,
            )

        assert result["check_category"] == "DECISION_DRIVING"
        assert result["plaintiff_lenses"] == ["CREDITORS", "SHAREHOLDERS"]

    def test_category_from_check_config_overrides(self) -> None:
        """Category from check_config takes priority over classification."""
        with patch(
            "do_uw.stages.analyze.signal_mappers.map_signal_data",
            return_value={},
        ):
            result = audit_check_pipeline(
                "FIN.LIQ.position",
                {
                    "id": "FIN.LIQ.position",
                    "execution_mode": "AUTO",
                    "section": 3,
                    "category": "CONTEXT_DISPLAY",
                },
                _FakeExtracted(),  # type: ignore[arg-type]
                None,
                _MOCK_CLASSIFICATION,
            )

        assert result["check_category"] == "CONTEXT_DISPLAY"


# ---------------------------------------------------------------------------
# audit_all_checks tests
# ---------------------------------------------------------------------------


class TestAuditAllChecks:
    """Test audit_all_checks aggregation logic."""

    def _make_checks(self) -> list[dict[str, object]]:
        """Create a small set of test checks."""
        return [
            {"id": "FIN.LIQ.position", "name": "Liquidity", "execution_mode": "AUTO", "section": 3},
            {"id": "FIN.LIQ.quick", "name": "Quick Ratio", "execution_mode": "AUTO", "section": 3},
            {"id": "FWRD.WARN.unknown", "name": "Forward Warning", "execution_mode": "AUTO", "section": 0},
            {"id": "BIZ.CLASS.industry", "name": "Industry", "execution_mode": "AUTO", "section": 1},
            {"id": "MANUAL.ONLY", "name": "Manual", "execution_mode": "MANUAL", "section": 0},
        ]

    def test_filters_to_auto_only(self) -> None:
        """Only AUTO signals are audited."""
        def mock_mapper(signal_id: str, *args: object, **kwargs: object) -> dict[str, object]:
            if signal_id == "FIN.LIQ.position":
                return {"current_ratio": 1.8}
            if signal_id == "FIN.LIQ.quick":
                return {"quick_ratio": None}
            if signal_id == "BIZ.CLASS.industry":
                return {"sector": "Technology"}
            return {}

        with patch(
            "do_uw.stages.analyze.signal_mappers.map_signal_data",
            side_effect=mock_mapper,
        ), patch(
            "do_uw.stages.analyze.pipeline_audit._load_classification",
            return_value=_MOCK_CLASSIFICATION,
        ):
            result = audit_all_checks(
                self._make_checks(),
                _FakeExtracted(),  # type: ignore[arg-type]
            )

        assert result["total_signals"] == 4  # MANUAL excluded
        assert "MANUAL.ONLY" not in result["details"]

    def test_aggregation_counts(self) -> None:
        """Counts are aggregated correctly."""
        def mock_mapper(signal_id: str, *args: object, **kwargs: object) -> dict[str, object]:
            if signal_id == "FIN.LIQ.position":
                return {"current_ratio": 1.8}
            if signal_id == "FIN.LIQ.quick":
                return {"quick_ratio": None}
            if signal_id == "BIZ.CLASS.industry":
                return {"sector": "Technology"}
            return {}  # FWRD.WARN.unknown: no mapper

        with patch(
            "do_uw.stages.analyze.signal_mappers.map_signal_data",
            side_effect=mock_mapper,
        ), patch(
            "do_uw.stages.analyze.pipeline_audit._load_classification",
            return_value=_MOCK_CLASSIFICATION,
        ):
            result = audit_all_checks(
                self._make_checks(),
                _FakeExtracted(),  # type: ignore[arg-type]
            )

        assert result["has_data"] == 2  # FIN.LIQ.position + BIZ.CLASS.industry
        assert result["no_mapper"] == 1  # FWRD.WARN.unknown
        assert result["all_none"] == 1  # FIN.LIQ.quick
        assert len(result["unwired_checks"]) == 2

    def test_by_category_breakdown(self) -> None:
        """Results are broken down by category."""
        def mock_mapper(signal_id: str, *args: object, **kwargs: object) -> dict[str, object]:
            if signal_id == "FIN.LIQ.position":
                return {"current_ratio": 1.8}
            if signal_id == "FIN.LIQ.quick":
                return {"quick_ratio": None}
            if signal_id == "BIZ.CLASS.industry":
                return {"sector": "Technology"}
            return {}

        with patch(
            "do_uw.stages.analyze.signal_mappers.map_signal_data",
            side_effect=mock_mapper,
        ), patch(
            "do_uw.stages.analyze.pipeline_audit._load_classification",
            return_value=_MOCK_CLASSIFICATION,
        ):
            result = audit_all_checks(
                self._make_checks(),
                _FakeExtracted(),  # type: ignore[arg-type]
            )

        assert "DECISION_DRIVING" in result["by_category"]
        assert "CONTEXT_DISPLAY" in result["by_category"]
        # FIN.LIQ.position + FIN.LIQ.quick + FWRD.WARN.unknown = 3 DECISION_DRIVING
        dd = result["by_category"]["DECISION_DRIVING"]
        assert dd["total"] == 3
        assert dd["has_data"] == 1  # FIN.LIQ.position

    def test_by_section_breakdown(self) -> None:
        """Results are broken down by section prefix."""
        def mock_mapper(signal_id: str, *args: object, **kwargs: object) -> dict[str, object]:
            if signal_id.startswith("FIN.LIQ"):
                return {"ratio": 1.0 if "position" in signal_id else None}
            if signal_id.startswith("BIZ"):
                return {"sector": "Tech"}
            return {}

        with patch(
            "do_uw.stages.analyze.signal_mappers.map_signal_data",
            side_effect=mock_mapper,
        ), patch(
            "do_uw.stages.analyze.pipeline_audit._load_classification",
            return_value=_MOCK_CLASSIFICATION,
        ):
            result = audit_all_checks(
                self._make_checks(),
                _FakeExtracted(),  # type: ignore[arg-type]
            )

        assert "FIN.LIQ" in result["by_section"]
        assert "FWRD.WARN" in result["by_section"]
        assert "BIZ.CLASS" in result["by_section"]


# ---------------------------------------------------------------------------
# format_audit_report tests
# ---------------------------------------------------------------------------


class TestFormatAuditReport:
    """Test format_audit_report produces readable output."""

    def _make_audit_result(self) -> dict[str, object]:
        return {
            "total_signals": 10,
            "has_data": 6,
            "no_mapper": 2,
            "all_none": 2,
            "by_category": {
                "DECISION_DRIVING": {"total": 7, "has_data": 5, "no_mapper": 1, "all_none": 1},
                "CONTEXT_DISPLAY": {"total": 3, "has_data": 1, "no_mapper": 1, "all_none": 1},
            },
            "by_section": {
                "FIN.LIQ": {"total": 3, "has_data": 2, "no_mapper": 0, "all_none": 1},
                "FWRD.WARN": {"total": 2, "has_data": 0, "no_mapper": 2, "all_none": 0},
            },
            "unwired_checks": ["FWRD.WARN.a", "FWRD.WARN.b", "FIN.LIQ.c", "BIZ.CLASS.d"],
            "details": {
                "FWRD.WARN.a": {"data_status": "NO_MAPPER", "check_category": "DECISION_DRIVING"},
                "FWRD.WARN.b": {"data_status": "NO_MAPPER", "check_category": "DECISION_DRIVING"},
                "FIN.LIQ.c": {"data_status": "ALL_NONE", "check_category": "DECISION_DRIVING"},
                "BIZ.CLASS.d": {"data_status": "ALL_NONE", "check_category": "CONTEXT_DISPLAY"},
            },
        }

    def test_report_contains_totals(self) -> None:
        report = format_audit_report(self._make_audit_result())
        assert "Total AUTO signals: 10" in report
        assert "Has data:" in report
        assert "60%" in report  # 6/10

    def test_report_contains_category_breakdown(self) -> None:
        report = format_audit_report(self._make_audit_result())
        assert "By Category:" in report
        assert "DECISION_DRIVING" in report
        assert "CONTEXT_DISPLAY" in report

    def test_report_contains_section_breakdown(self) -> None:
        report = format_audit_report(self._make_audit_result())
        assert "By Section Prefix:" in report
        assert "FIN.LIQ" in report
        assert "FWRD.WARN" in report

    def test_report_lists_unwired_checks(self) -> None:
        report = format_audit_report(self._make_audit_result())
        assert "Unwired Checks (4):" in report
        assert "FWRD.WARN.a" in report
        assert "NO_MAPPER" in report
        assert "ALL_NONE" in report

    def test_report_shows_all_wired_when_none_unwired(self) -> None:
        audit = self._make_audit_result()
        audit["unwired_checks"] = []
        report = format_audit_report(audit)  # type: ignore[arg-type]
        assert "All checks have data" in report

    def test_report_is_multiline_string(self) -> None:
        report = format_audit_report(self._make_audit_result())
        assert isinstance(report, str)
        assert report.count("\n") > 10
