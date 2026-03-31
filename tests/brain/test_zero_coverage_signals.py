"""Tests for Phase 33-03: zero-coverage subsection checks.

Validates that checks created in Plan 03 exist with proper metadata.
After Plan 04 reorganization: 4.9->1.9 (absorbed), 5.8->5.7, 5.9->5.7 (merged).
The checks still exist -- only their v6_subsection_ids changed.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from do_uw.stages.analyze.signal_field_routing import FIELD_FOR_CHECK

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

CHECKS_JSON = Path("src/do_uw/brain/config/signals.json")


@pytest.fixture(scope="module")
def all_checks() -> list[dict]:
    """Load all signals from signals.json."""
    data = json.loads(CHECKS_JSON.read_text())
    return data["signals"]


# IDs created/updated in Phase 33-03
NEW_CHECK_IDS = [
    "BIZ.STRUCT.subsidiary_count",
    "BIZ.STRUCT.vie_spe",
    "BIZ.STRUCT.related_party",
    "LIT.DEFENSE.forum_selection",
    "LIT.DEFENSE.contingent_liabilities",
    "LIT.DEFENSE.pslra_safe_harbor",
    "LIT.PATTERN.sol_windows",
    "LIT.PATTERN.industry_theories",
    "LIT.PATTERN.peer_contagion",
    "LIT.PATTERN.temporal_correlation",
    "LIT.SECTOR.industry_patterns",
    "LIT.SECTOR.regulatory_databases",
]

# Updated checks (already existed, v6_subsection_ids extended)
UPDATED_CHECK_IDS = [
    "FWRD.WARN.social_sentiment",
    "FWRD.WARN.journalism_activity",
]

REQUIRED_FIELDS = [
    "id",
    "name",
    "section",
    "threshold",
    "execution_mode",
    "v6_subsection_ids",
    "content_type",
]

# After Plan 04 reorganization:
# - 4.9 absorbed into 1.9 (Early Warning Signals)
# - 5.8 merged into 5.7 (Litigation Risk Analysis)
# - 5.9 merged into 5.7 (Litigation Risk Analysis)
# The checks themselves still exist, just with remapped subsection IDs.
ZERO_COVERAGE_SUBSECTIONS = ["1.4", "1.9", "5.7"]

# Minimum checks per subsection (updated for merged structure)
MIN_CHECKS_PER_SUBSECTION = {
    "1.4": 3,   # BIZ.STRUCT (3 new)
    "1.9": 2,   # Early Warning: media absorbed from 4.9 + employee/customer signals
    "5.7": 9,   # Merged: LIT.DEFENSE(3) + LIT.PATTERN(4) + LIT.SECTOR(2)
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestNewChecksExist:
    """Verify all new check IDs exist in signals.json."""

    def test_new_checks_exist_in_checks_json(self, all_checks: list[dict]) -> None:
        """All 12 new check IDs must be present in signals.json."""
        existing_ids = {c["id"] for c in all_checks}
        for signal_id in NEW_CHECK_IDS:
            assert signal_id in existing_ids, f"Missing new check: {signal_id}"

    def test_updated_checks_have_1_9(self, all_checks: list[dict]) -> None:
        """FWRD.WARN.social_sentiment and journalism_activity must include 1.9.

        After Plan 04 reorganization: old 4.9 (Media) absorbed into 1.9 (Early Warning).
        """
        for signal_id in UPDATED_CHECK_IDS:
            check = next(c for c in all_checks if c["id"] == signal_id)
            assert "1.9" in check.get("v6_subsection_ids", []), (
                f"{signal_id} missing v6_subsection_ids '1.9' (old 4.9 -> 1.9)"
            )


class TestNewChecksMetadata:
    """Verify each new check has valid metadata structure."""

    @pytest.mark.parametrize("signal_id", NEW_CHECK_IDS)
    def test_new_checks_have_valid_metadata(
        self, all_checks: list[dict], signal_id: str
    ) -> None:
        """Each new check must have all required metadata fields."""
        check = next((c for c in all_checks if c["id"] == signal_id), None)
        assert check is not None, f"Check {signal_id} not found"
        for field in REQUIRED_FIELDS:
            assert field in check, f"{signal_id} missing required field: {field}"

    @pytest.mark.parametrize("signal_id", NEW_CHECK_IDS)
    def test_new_checks_have_data_strategy(
        self, all_checks: list[dict], signal_id: str
    ) -> None:
        """Each new check must have a data_strategy with field_key."""
        check = next(c for c in all_checks if c["id"] == signal_id)
        ds = check.get("data_strategy", {})
        assert isinstance(ds, dict), f"{signal_id} data_strategy not a dict"
        assert "field_key" in ds, f"{signal_id} data_strategy missing field_key"

    @pytest.mark.parametrize("signal_id", NEW_CHECK_IDS)
    def test_new_checks_are_auto(
        self, all_checks: list[dict], signal_id: str
    ) -> None:
        """Each new check must have execution_mode AUTO."""
        check = next(c for c in all_checks if c["id"] == signal_id)
        assert check["execution_mode"] == "AUTO", (
            f"{signal_id} execution_mode is {check['execution_mode']}, expected AUTO"
        )


class TestFieldRouting:
    """Verify field routing covers all new checks."""

    @pytest.mark.parametrize("signal_id", NEW_CHECK_IDS)
    def test_new_checks_have_field_routing(
        self, all_checks: list[dict], signal_id: str
    ) -> None:
        """Each new check ID is handled by FIELD_FOR_CHECK or data_strategy.field_key."""
        check = next(c for c in all_checks if c["id"] == signal_id)
        # Phase 31 declarative routing via data_strategy.field_key
        ds = check.get("data_strategy", {})
        has_declarative = isinstance(ds, dict) and "field_key" in ds
        # Legacy routing via FIELD_FOR_CHECK
        has_legacy = signal_id in FIELD_FOR_CHECK
        assert has_declarative or has_legacy, (
            f"{signal_id} has no field routing (neither data_strategy.field_key nor FIELD_FOR_CHECK)"
        )


class TestSubsectionCoverage:
    """Verify all 5 zero-coverage subsections now have check coverage."""

    @pytest.mark.parametrize("subsection", ZERO_COVERAGE_SUBSECTIONS)
    def test_zero_coverage_subsections_now_covered(
        self, all_checks: list[dict], subsection: str
    ) -> None:
        """Each previously zero-coverage subsection must have >= 2 checks."""
        matching = [
            c["id"]
            for c in all_checks
            if subsection in c.get("v6_subsection_ids", [])
        ]
        min_count = MIN_CHECKS_PER_SUBSECTION[subsection]
        assert len(matching) >= min_count, (
            f"Subsection {subsection} has {len(matching)} checks (need >= {min_count}): {matching}"
        )

    def test_total_new_signal_count(self, all_checks: list[dict]) -> None:
        """Total checks covering the tracked subsections should be >= 12.

        After reorganization: 1.4(3) + 1.9(many) + 5.7(9+) = well above 12.
        """
        all_zero_cov = set()
        for c in all_checks:
            for sub in ZERO_COVERAGE_SUBSECTIONS:
                if sub in c.get("v6_subsection_ids", []):
                    all_zero_cov.add(c["id"])
        assert len(all_zero_cov) >= 12, (
            f"Expected >= 12 checks covering tracked subsections, got {len(all_zero_cov)}"
        )


class TestEnrichmentMappings:
    """Verify enrichment_data.py has mappings for new checks."""

    def test_subdomain_mappings(self) -> None:
        """New subdomains must be in SUBDOMAIN_TO_RISK_QUESTIONS."""
        from do_uw.brain.enrichment_data import SUBDOMAIN_TO_RISK_QUESTIONS

        new_subdomains = ["BIZ.STRUCT", "LIT.DEFENSE", "LIT.PATTERN", "LIT.SECTOR"]
        for subdomain in new_subdomains:
            assert subdomain in SUBDOMAIN_TO_RISK_QUESTIONS, (
                f"Missing subdomain: {subdomain}"
            )

    def test_check_to_risk_questions(self) -> None:
        """All new checks must have entries in CHECK_TO_RISK_QUESTIONS."""
        from do_uw.brain.enrichment_data import CHECK_TO_RISK_QUESTIONS

        for signal_id in NEW_CHECK_IDS:
            assert signal_id in CHECK_TO_RISK_QUESTIONS, (
                f"Missing CHECK_TO_RISK_QUESTIONS entry: {signal_id}"
            )

    def test_framework_layer_entries(self) -> None:
        """All new checks must have framework layer assignments."""
        from do_uw.brain.enrichment_data import CHECK_TO_RISK_FRAMEWORK_LAYER

        for signal_id in NEW_CHECK_IDS:
            assert signal_id in CHECK_TO_RISK_FRAMEWORK_LAYER, (
                f"Missing CHECK_TO_RISK_FRAMEWORK_LAYER entry: {signal_id}"
            )
