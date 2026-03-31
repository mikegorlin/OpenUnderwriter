"""Tests for PipelineGapDetector (gap analysis across 3 levels)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from do_uw.knowledge.gap_detector import (
    ACQUIRED_SOURCES,
    GapReport,
    PipelineGap,
    detect_gaps,
)
from do_uw.knowledge.requirements import build_manifest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

CHECKS_JSON_PATH = Path(__file__).parents[2] / "src" / "do_uw" / "brain" / "config" / "signals.json"


@pytest.fixture()
def all_checks() -> list[dict[str, Any]]:
    """Load all signals from signals.json."""
    with open(CHECKS_JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["signals"]


@pytest.fixture()
def gap_report(all_checks: list[dict[str, Any]]) -> GapReport:
    """Build full gap report from real signals.json data."""
    manifest = build_manifest(all_checks)
    return detect_gaps(all_checks, manifest)


# ---------------------------------------------------------------------------
# Tests: Real signals.json
# ---------------------------------------------------------------------------


class TestDetectGapsReal:
    """Test gap detection against actual signals.json data."""

    def test_no_critical_gaps(self, gap_report: GapReport) -> None:
        """All source types needed by checks should be in ACQUIRED_SOURCES."""
        critical_count = gap_report.by_severity.get("CRITICAL", 0)
        assert critical_count == 0, (
            f"Found {critical_count} CRITICAL gaps: "
            + str([g for g in gap_report.gaps if g.severity == "CRITICAL"][:5])
        )

    def test_total_signals_matches(self, gap_report: GapReport) -> None:
        """Gap report total_signals should match AUTO check count."""
        assert gap_report.total_signals >= 370
        assert gap_report.total_signals <= 400

    def test_fully_supported_count(self, gap_report: GapReport) -> None:
        """Most checks should be fully supported (no gaps at any level)."""
        assert gap_report.fully_supported >= gap_report.total_signals * 0.8, (
            f"Only {gap_report.fully_supported}/{gap_report.total_signals} "
            "fully supported (expected >80%)"
        )

    def test_gap_types_valid(self, gap_report: GapReport) -> None:
        """All gap types should be recognized."""
        valid_types = {"SOURCE_NOT_ACQUIRED", "NO_FIELD_ROUTING", "NO_MAPPER_HANDLER"}
        for gap in gap_report.gaps:
            assert gap.gap_type in valid_types, f"Unknown gap type: {gap.gap_type}"

    def test_severity_levels_valid(self, gap_report: GapReport) -> None:
        """All severity levels should be valid."""
        valid_severities = {"CRITICAL", "WARNING", "INFO"}
        for gap in gap_report.gaps:
            assert gap.severity in valid_severities, f"Unknown severity: {gap.severity}"

    def test_aggregation_consistent(self, gap_report: GapReport) -> None:
        """by_type and by_severity should match the actual gap list."""
        type_counts: dict[str, int] = {}
        severity_counts: dict[str, int] = {}
        for gap in gap_report.gaps:
            type_counts[gap.gap_type] = type_counts.get(gap.gap_type, 0) + 1
            severity_counts[gap.severity] = severity_counts.get(gap.severity, 0) + 1

        assert type_counts == gap_report.by_type
        assert severity_counts == gap_report.by_severity


# ---------------------------------------------------------------------------
# Tests: Synthetic data
# ---------------------------------------------------------------------------


class TestDetectGapsSynthetic:
    """Test gap detection with synthetic check data."""

    def test_unknown_source_critical(self) -> None:
        """Check requiring unknown source produces CRITICAL gap."""
        checks = [
            {
                "id": "TEST.SOURCE.01",
                "name": "Unknown source check",
                "execution_mode": "AUTO",
                "required_data": ["PCAOB_INSPECTION"],
                "data_locations": {},
            }
        ]
        manifest = build_manifest(checks)
        report = detect_gaps(checks, manifest)

        assert len(report.gaps) >= 1
        source_gaps = [g for g in report.gaps if g.gap_type == "SOURCE_NOT_ACQUIRED"]
        assert len(source_gaps) == 1
        assert source_gaps[0].severity == "CRITICAL"
        assert "PCAOB_INSPECTION" in source_gaps[0].detail

    def test_no_field_routing_warning(self) -> None:
        """Check with no field routing produces WARNING gap."""
        checks = [
            {
                "id": "UNKNOWN_PREFIX.TEST.01",
                "name": "No field routing check",
                "execution_mode": "AUTO",
                "required_data": ["SEC_10K"],
                "data_locations": {},
                # No data_strategy, not in FIELD_FOR_CHECK, not Phase 26+ prefix
            }
        ]
        manifest = build_manifest(checks)
        report = detect_gaps(checks, manifest)

        field_gaps = [g for g in report.gaps if g.gap_type == "NO_FIELD_ROUTING"]
        assert len(field_gaps) == 1
        assert field_gaps[0].severity == "WARNING"

    def test_unknown_prefix_info(self) -> None:
        """Check with unknown prefix produces INFO gap."""
        checks = [
            {
                "id": "XYZZY.TEST.01",
                "name": "Unknown prefix check",
                "execution_mode": "AUTO",
                "required_data": ["SEC_10K"],
                "data_locations": {},
            }
        ]
        manifest = build_manifest(checks)
        report = detect_gaps(checks, manifest)

        mapper_gaps = [g for g in report.gaps if g.gap_type == "NO_MAPPER_HANDLER"]
        assert len(mapper_gaps) == 1
        assert mapper_gaps[0].severity == "INFO"
        assert "XYZZY" in mapper_gaps[0].detail

    def test_phase26_mapper_no_field_gap(self) -> None:
        """Phase 26+ mapper checks should NOT produce field routing gaps."""
        checks = [
            {
                "id": "EXEC.TENURE.ceo",
                "name": "CEO tenure (Phase 26)",
                "execution_mode": "AUTO",
                "required_data": ["SEC_DEF14A"],
                "data_locations": {},
                # No data_strategy, not in FIELD_FOR_CHECK, but IS Phase 26+
            }
        ]
        manifest = build_manifest(checks)
        report = detect_gaps(checks, manifest)

        field_gaps = [g for g in report.gaps if g.gap_type == "NO_FIELD_ROUTING"]
        assert len(field_gaps) == 0

    def test_field_key_covers_routing(self) -> None:
        """Check with data_strategy.field_key should not have field routing gap."""
        checks = [
            {
                "id": "NEW.TEST.01",
                "name": "Check with field_key",
                "execution_mode": "AUTO",
                "required_data": ["SEC_10K"],
                "data_locations": {},
                "data_strategy": {"field_key": "current_ratio"},
            }
        ]
        manifest = build_manifest(checks)
        report = detect_gaps(checks, manifest)

        field_gaps = [g for g in report.gaps if g.gap_type == "NO_FIELD_ROUTING"]
        assert len(field_gaps) == 0

    def test_fully_supported_check(self) -> None:
        """Check with known source, field_key, and handled prefix = fully supported."""
        checks = [
            {
                "id": "BIZ.SIZE.market_cap",
                "name": "Market cap check",
                "execution_mode": "AUTO",
                "required_data": ["SEC_10K"],
                "data_locations": {"SEC_10K": ["filing_summary"]},
                "data_strategy": {"field_key": "market_cap"},
            }
        ]
        manifest = build_manifest(checks)
        report = detect_gaps(checks, manifest)

        assert report.fully_supported == 1
        assert len(report.gaps) == 0

    def test_multiple_gaps_per_check(self) -> None:
        """A single check can have gaps at multiple levels."""
        checks = [
            {
                "id": "XYZZY.UNKNOWN.01",
                "name": "Totally unsupported check",
                "execution_mode": "AUTO",
                "required_data": ["PCAOB_INSPECTION"],
                "data_locations": {},
            }
        ]
        manifest = build_manifest(checks)
        report = detect_gaps(checks, manifest)

        # Should have 3 gaps: source (CRITICAL), field (WARNING), mapper (INFO)
        assert len(report.gaps) == 3
        gap_types = {g.gap_type for g in report.gaps}
        assert gap_types == {"SOURCE_NOT_ACQUIRED", "NO_FIELD_ROUTING", "NO_MAPPER_HANDLER"}

    def test_non_auto_excluded(self) -> None:
        """Non-AUTO signals should not appear in gap report."""
        checks = [
            {
                "id": "MANUAL.01",
                "name": "Manual check",
                "execution_mode": "MANUAL",
                "required_data": ["PCAOB_INSPECTION"],
            }
        ]
        manifest = build_manifest(checks)
        report = detect_gaps(checks, manifest)

        assert report.total_signals == 0
        assert len(report.gaps) == 0

    def test_empty_checks(self) -> None:
        """Empty check list produces empty gap report."""
        manifest = build_manifest([])
        report = detect_gaps([], manifest)

        assert report.total_signals == 0
        assert report.fully_supported == 0
        assert len(report.gaps) == 0
