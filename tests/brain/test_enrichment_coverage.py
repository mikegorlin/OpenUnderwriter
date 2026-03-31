"""Tests for v6 subsection ID coverage on all brain checks.

Validates that:
- Every check in signals.json has a non-empty v6_subsection_ids field
- All v6_subsection_ids use valid X.Y format (section 1-5, subsection 1-11)
- Every prefix.subdomain pattern has enrichment_data.py coverage
- Each of the 5 v6 sections has subsection coverage from checks
- DuckDB risk_questions match signals.json v6_subsection_ids
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from do_uw.brain.enrichment_data import (
    CHECK_TO_RISK_QUESTIONS,
    SUBDOMAIN_TO_RISK_QUESTIONS,
)

_CHECKS_JSON = Path(__file__).parent.parent.parent / "src" / "do_uw" / "brain" / "config" / "signals.json"

# v6 valid subsection IDs (36-subsection structure after reorganization).
# Sections 1 and 4 have non-contiguous numbering due to absorbed/merged subsections.
_V6_VALID_SUBSECTION_IDS = {
    "1.1", "1.2", "1.3", "1.4", "1.6", "1.8", "1.9", "1.11",
    "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "2.8",
    "3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "3.8",
    "4.1", "4.2", "4.3", "4.4",
    "5.1", "5.2", "5.3", "5.4", "5.5", "5.6", "5.7",
}

# v6 section ranges for general validation (section -> max subsection number)
_V6_SECTION_RANGES = {
    1: 11,  # 1.1 through 1.11 (non-contiguous: 1.5, 1.7, 1.10 removed)
    2: 8,   # 2.1 through 2.8
    3: 8,   # 3.1 through 3.8
    4: 4,   # 4.1 through 4.4 (reorganized from 4.1-4.9)
    5: 7,   # 5.1 through 5.7 (merged from 5.1-5.9)
}

# No zero-coverage subsections remaining after Plan 03 + Plan 04 reorganization
_PLAN_03_ZERO_COVERAGE: set[str] = set()


@pytest.fixture
def checks() -> list[dict]:
    """Load all signals from signals.json."""
    with open(_CHECKS_JSON) as f:
        data = json.load(f)
    return data["signals"]


class TestAllChecksHaveV6SubsectionIds:
    """Every check must have a non-empty v6_subsection_ids list."""

    def test_all_checks_have_v6_subsection_ids(self, checks: list[dict]) -> None:
        """All 384 checks must have non-empty v6_subsection_ids."""
        missing = [c["id"] for c in checks if not c.get("v6_subsection_ids")]
        assert len(missing) == 0, (
            f"{len(missing)} checks missing v6_subsection_ids: {missing[:10]}"
        )

    def test_signal_count_is_400(self, checks: list[dict]) -> None:
        """Verify total check count matches expected 400."""
        assert len(checks) == 400, f"Expected 400 checks, got {len(checks)}"


class TestV6SubsectionIdsAreValid:
    """All v6_subsection_ids must use valid X.Y format."""

    def test_v6_subsection_ids_are_valid(self, checks: list[dict]) -> None:
        """Every v6_subsection_id must be in the valid 36-subsection set."""
        invalid: list[tuple[str, str]] = []
        for check in checks:
            for sid in check.get("v6_subsection_ids", []):
                if not re.match(r"^\d+\.\d+$", sid):
                    invalid.append((check["id"], sid))
                elif sid not in _V6_VALID_SUBSECTION_IDS:
                    invalid.append((check["id"], sid))
        assert len(invalid) == 0, (
            f"{len(invalid)} invalid v6_subsection_ids: {invalid[:10]}"
        )

    def test_no_duplicate_ids_per_check(self, checks: list[dict]) -> None:
        """No check should have duplicate v6_subsection_ids."""
        duplicates: list[tuple[str, list[str]]] = []
        for check in checks:
            ids = check.get("v6_subsection_ids", [])
            if len(ids) != len(set(ids)):
                duplicates.append((check["id"], ids))
        assert len(duplicates) == 0, (
            f"{len(duplicates)} checks with duplicate v6_subsection_ids: {duplicates[:5]}"
        )


class TestEnrichmentDataCoversAllSubdomains:
    """Every prefix.subdomain pattern must have enrichment coverage."""

    def test_enrichment_data_covers_all_subdomains(self, checks: list[dict]) -> None:
        """Every unique prefix.subdomain has CHECK_TO_RISK_QUESTIONS or SUBDOMAIN_TO_RISK_QUESTIONS."""
        uncovered: list[str] = []
        seen_subdomains: set[str] = set()

        for check in checks:
            cid = check["id"]
            subdomain = ".".join(cid.split(".")[:2])
            if subdomain in seen_subdomains:
                continue
            seen_subdomains.add(subdomain)

            # Check if ANY check in this subdomain has explicit mapping
            subdomain_has_explicit = any(
                k.startswith(subdomain + ".") for k in CHECK_TO_RISK_QUESTIONS
            )
            subdomain_has_default = subdomain in SUBDOMAIN_TO_RISK_QUESTIONS

            if not subdomain_has_explicit and not subdomain_has_default:
                uncovered.append(subdomain)

        assert len(uncovered) == 0, (
            f"{len(uncovered)} subdomains without enrichment coverage: {uncovered}"
        )

    def test_no_empty_mappings_in_enrichment(self) -> None:
        """No enrichment mapping should resolve to empty list."""
        empty_subdomain = [
            k for k, v in SUBDOMAIN_TO_RISK_QUESTIONS.items() if not v
        ]
        empty_check = [
            k for k, v in CHECK_TO_RISK_QUESTIONS.items() if not v
        ]
        assert len(empty_subdomain) == 0, (
            f"Empty SUBDOMAIN mappings: {empty_subdomain}"
        )
        assert len(empty_check) == 0, (
            f"Empty CHECK mappings: {empty_check}"
        )


class TestSubsectionCoverageBySection:
    """Each v6 section should have reasonable subsection coverage."""

    def test_subsection_coverage_by_section(self, checks: list[dict]) -> None:
        """Each of the 5 sections has subsections with checks mapped."""
        covered_by_section: dict[int, set[str]] = {i: set() for i in range(1, 6)}

        for check in checks:
            for sid in check.get("v6_subsection_ids", []):
                section = int(sid.split(".")[0])
                if section in covered_by_section:
                    covered_by_section[section].add(sid)

        # Count expected subsections per section from valid set
        expected_by_section: dict[int, int] = {}
        for sid in _V6_VALID_SUBSECTION_IDS:
            sec = int(sid.split(".")[0])
            expected_by_section[sec] = expected_by_section.get(sec, 0) + 1

        for section, covered in covered_by_section.items():
            total = expected_by_section.get(section, 0)
            assert len(covered) > 0, (
                f"Section {section} has zero subsection coverage"
            )
            # Each section should cover at least 50% of its subsections
            assert len(covered) >= total * 0.5, (
                f"Section {section}: only {len(covered)}/{total} subsections covered"
            )

    def test_all_36_subsections_covered(self, checks: list[dict]) -> None:
        """All 36 subsections in the reorganized structure must be covered."""
        covered: set[str] = set()
        for check in checks:
            for sid in check.get("v6_subsection_ids", []):
                if sid in _V6_VALID_SUBSECTION_IDS:
                    covered.add(sid)

        uncovered = _V6_VALID_SUBSECTION_IDS - covered
        assert len(uncovered) == 0, (
            f"Uncovered subsections in 36-subsection structure: {sorted(uncovered)}"
        )

    def test_section_1_company(self, checks: list[dict]) -> None:
        """Section 1 (Company) should cover key subsections."""
        covered: set[str] = set()
        for check in checks:
            for sid in check.get("v6_subsection_ids", []):
                if sid.startswith("1."):
                    covered.add(sid)
        # Must have: 1.1, 1.2, 1.3, 1.8, 1.9, 1.11 (1.5, 1.7, 1.10 absorbed)
        for required in ["1.1", "1.2", "1.3", "1.8", "1.9", "1.11"]:
            assert required in covered, f"Section 1 missing required subsection {required}"

    def test_section_5_litigation(self, checks: list[dict]) -> None:
        """Section 5 (Litigation) should cover active subsections."""
        covered: set[str] = set()
        for check in checks:
            for sid in check.get("v6_subsection_ids", []):
                if sid.startswith("5."):
                    covered.add(sid)
        # Must have: 5.1, 5.2, 5.4, 5.6
        for required in ["5.1", "5.2", "5.4", "5.6"]:
            assert required in covered, f"Section 5 missing required subsection {required}"


class TestV6SubsectionIdsMatchEnrichmentData:
    """v6_subsection_ids in signals.json should match enrichment_data.py resolution."""

    def test_checks_json_matches_enrichment_resolution(self, checks: list[dict]) -> None:
        """For every check, v6_subsection_ids should match what _resolve_risk_questions returns."""
        from do_uw.brain.brain_enrich import _resolve_risk_questions

        mismatches: list[tuple[str, list[str], list[str]]] = []
        for check in checks:
            cid = check["id"]
            json_ids = check.get("v6_subsection_ids", [])
            resolved_ids = _resolve_risk_questions(cid)
            if json_ids != resolved_ids:
                mismatches.append((cid, json_ids, resolved_ids))

        assert len(mismatches) == 0, (
            f"{len(mismatches)} checks where signals.json v6_subsection_ids "
            f"differs from enrichment resolution: {mismatches[:5]}"
        )
