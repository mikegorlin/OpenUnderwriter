"""Tests for RequirementsAnalyzer (AcquisitionManifest from check declarations)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from do_uw.knowledge.requirements import AcquisitionManifest, build_manifest


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
def manifest(all_checks: list[dict[str, Any]]) -> AcquisitionManifest:
    """Build manifest from real signals.json."""
    return build_manifest(all_checks)


# ---------------------------------------------------------------------------
# Tests: Real signals.json
# ---------------------------------------------------------------------------


class TestBuildManifestReal:
    """Test build_manifest against actual signals.json data."""

    def test_required_sources_count(self, manifest: AcquisitionManifest) -> None:
        """Manifest should discover ~10 distinct source types."""
        assert len(manifest.required_sources) >= 9
        assert len(manifest.required_sources) <= 12

    def test_known_sources_present(self, manifest: AcquisitionManifest) -> None:
        """Critical source types must be in the manifest."""
        expected = {
            "SEC_10K", "SEC_10Q", "SEC_DEF14A", "MARKET_PRICE",
            "SCAC_SEARCH", "SEC_ENFORCEMENT",
        }
        for src in expected:
            assert src in manifest.required_sources, f"Missing source: {src}"

    def test_total_signals_auto_only(self, manifest: AcquisitionManifest) -> None:
        """Total checks should be AUTO-mode only (currently 381)."""
        assert manifest.total_signals >= 370
        assert manifest.total_signals <= 400

    def test_source_to_checks_covers_all_auto(
        self, manifest: AcquisitionManifest, all_checks: list[dict[str, Any]],
    ) -> None:
        """Every AUTO check with required_data should appear in source_to_checks."""
        auto_with_sources = set()
        for c in all_checks:
            if c.get("execution_mode") == "AUTO" and c.get("required_data"):
                auto_with_sources.add(c["id"])

        # Collect all check IDs from source_to_checks
        checks_in_manifest: set[str] = set()
        for signal_ids in manifest.source_to_checks.values():
            checks_in_manifest.update(signal_ids)

        assert auto_with_sources == checks_in_manifest

    def test_required_sections_populated(self, manifest: AcquisitionManifest) -> None:
        """Should have section-level requirements for multiple sources."""
        total_sections = sum(len(secs) for secs in manifest.required_sections.values())
        assert total_sections >= 100, f"Expected 100+ section pairs, got {total_sections}"

    def test_depth_distribution(self, manifest: AcquisitionManifest) -> None:
        """Should have checks across depth levels 1-4."""
        assert 1 in manifest.checks_by_depth
        assert 2 in manifest.checks_by_depth
        assert 3 in manifest.checks_by_depth
        assert 4 in manifest.checks_by_depth
        assert manifest.checks_by_depth[2] > 200  # Majority at depth 2

    def test_content_type_distribution(self, manifest: AcquisitionManifest) -> None:
        """Should have checks across all 3 content types."""
        assert "EVALUATIVE_CHECK" in manifest.checks_by_content_type
        assert "MANAGEMENT_DISPLAY" in manifest.checks_by_content_type
        assert "INFERENCE_PATTERN" in manifest.checks_by_content_type
        assert manifest.checks_by_content_type["EVALUATIVE_CHECK"] > 250


# ---------------------------------------------------------------------------
# Tests: Synthetic data (edge cases)
# ---------------------------------------------------------------------------


class TestBuildManifestSynthetic:
    """Test build_manifest with synthetic check data."""

    def test_empty_checks(self) -> None:
        """Empty check list produces empty manifest."""
        m = build_manifest([])
        assert m.total_signals == 0
        assert len(m.required_sources) == 0
        assert len(m.source_to_checks) == 0

    def test_single_check(self) -> None:
        """Single AUTO check produces correct manifest."""
        checks = [
            {
                "id": "TEST.SINGLE.01",
                "name": "Test check",
                "execution_mode": "AUTO",
                "depth": 2,
                "content_type": "EVALUATIVE_CHECK",
                "required_data": ["SEC_10K", "MARKET_PRICE"],
                "data_locations": {
                    "SEC_10K": ["item_1a_risk_factors", "item_7_mda"],
                    "MARKET_PRICE": ["daily_close"],
                },
            }
        ]
        m = build_manifest(checks)
        assert m.total_signals == 1
        assert m.required_sources == {"SEC_10K", "MARKET_PRICE"}
        assert "TEST.SINGLE.01" in m.source_to_checks["SEC_10K"]
        assert "TEST.SINGLE.01" in m.source_to_checks["MARKET_PRICE"]
        assert m.required_sections["SEC_10K"] == {"item_1a_risk_factors", "item_7_mda"}
        assert m.required_sections["MARKET_PRICE"] == {"daily_close"}
        assert m.checks_by_depth == {2: 1}
        assert m.checks_by_content_type == {"EVALUATIVE_CHECK": 1}

    def test_non_auto_excluded(self) -> None:
        """Non-AUTO signals should not appear in manifest."""
        checks = [
            {
                "id": "MANUAL.01",
                "name": "Manual check",
                "execution_mode": "MANUAL",
                "required_data": ["SEC_10K"],
                "data_locations": {"SEC_10K": ["item_1a"]},
            },
            {
                "id": "AUTO.01",
                "name": "Auto check",
                "execution_mode": "AUTO",
                "depth": 3,
                "content_type": "INFERENCE_PATTERN",
                "required_data": ["MARKET_PRICE"],
                "data_locations": {"MARKET_PRICE": ["daily_close"]},
            },
        ]
        m = build_manifest(checks)
        assert m.total_signals == 1
        assert m.required_sources == {"MARKET_PRICE"}
        assert "MANUAL.01" not in m.source_to_checks.get("SEC_10K", [])

    def test_no_required_data(self) -> None:
        """Check without required_data still counts but adds no sources."""
        checks = [
            {
                "id": "BARE.01",
                "name": "Bare check",
                "execution_mode": "AUTO",
                "depth": 1,
                "content_type": "MANAGEMENT_DISPLAY",
            }
        ]
        m = build_manifest(checks)
        assert m.total_signals == 1
        assert len(m.required_sources) == 0
        assert m.checks_by_depth == {1: 1}

    def test_malformed_data_locations(self) -> None:
        """Non-dict data_locations should be handled gracefully."""
        checks = [
            {
                "id": "BAD.01",
                "name": "Bad locations",
                "execution_mode": "AUTO",
                "depth": 2,
                "content_type": "EVALUATIVE_CHECK",
                "required_data": ["SEC_10K"],
                "data_locations": "not_a_dict",
            }
        ]
        m = build_manifest(checks)
        assert m.total_signals == 1
        assert "SEC_10K" in m.required_sources
        # No sections added because data_locations is not a dict
        assert len(m.required_sections) == 0
