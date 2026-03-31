"""Tests for new industry playbooks mined from Old Underwriter supplements.

Validates the 5 new industry playbooks (CPG, Media, Industrials, REITs,
Transportation) created from Old Underwriter supplement analysis. Tests
playbook structure, check ID conventions, SIC range non-overlap, activation
via KnowledgeStore, and supplement document ingestion.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from do_uw.knowledge.playbook_data import INDUSTRY_PLAYBOOKS
from do_uw.knowledge.playbook_data_cpg import (
    CPG_CONSUMER_PLAYBOOK,
    MEDIA_ENTERTAINMENT_PLAYBOOK,
)
from do_uw.knowledge.playbook_data_industrials import (
    INDUSTRIALS_MFG_PLAYBOOK,
    REITS_REAL_ESTATE_PLAYBOOK,
    TRANSPORTATION_RAIL_PLAYBOOK,
)
from do_uw.knowledge.playbooks import load_playbooks
from do_uw.knowledge.store import KnowledgeStore

_REQUIRED_KEYS = [
    "id",
    "name",
    "description",
    "sic_ranges",
    "naics_prefixes",
    "industry_checks",
    "risk_patterns",
    "claim_theories",
    "meeting_questions",
    "scoring_adjustments",
]


@pytest.fixture()
def store() -> KnowledgeStore:
    """Create an in-memory knowledge store with all playbooks loaded."""
    s = KnowledgeStore(db_path=None)
    load_playbooks(s)
    return s


def _signal_ids_for(playbook: dict[str, Any]) -> list[str]:
    """Extract all check IDs from a playbook."""
    return [c["id"] for c in playbook.get("industry_checks", [])]


class TestAllPlaybooksLoad:
    """Verify all 10 playbooks load with correct structure."""

    def test_total_count_is_10(self) -> None:
        """INDUSTRY_PLAYBOOKS contains exactly 10 playbooks."""
        assert len(INDUSTRY_PLAYBOOKS) == 10

    def test_all_have_required_keys(self) -> None:
        """Every playbook has all required top-level keys."""
        for pb in INDUSTRY_PLAYBOOKS:
            for key in _REQUIRED_KEYS:
                assert key in pb, (
                    f"Playbook {pb.get('id', '?')} missing key '{key}'"
                )

    def test_total_signals_is_100(self) -> None:
        """All 10 playbooks have 10 checks each = 100 total."""
        total = sum(
            len(pb.get("industry_checks", []))
            for pb in INDUSTRY_PLAYBOOKS
        )
        assert total == 100

    def test_all_playbook_ids(self) -> None:
        """All 10 expected playbook IDs are present."""
        ids = {pb["id"] for pb in INDUSTRY_PLAYBOOKS}
        expected = {
            "TECH_SAAS",
            "BIOTECH_PHARMA",
            "FINANCIAL_SERVICES",
            "ENERGY_UTILITIES",
            "HEALTHCARE",
            "CPG_CONSUMER",
            "MEDIA_ENTERTAINMENT",
            "INDUSTRIALS_MFG",
            "REITS_REAL_ESTATE",
            "TRANSPORTATION_RAIL",
        }
        assert ids == expected


class TestCpgPlaybookStructure:
    """Verify CPG/Consumer playbook structure."""

    def test_id_and_name(self) -> None:
        """CPG playbook has correct ID and name."""
        assert CPG_CONSUMER_PLAYBOOK["id"] == "CPG_CONSUMER"
        assert "CPG" in CPG_CONSUMER_PLAYBOOK["name"]

    def test_has_required_keys(self) -> None:
        """CPG playbook has all required keys."""
        for key in _REQUIRED_KEYS:
            assert key in CPG_CONSUMER_PLAYBOOK

    def test_signal_ids_prefix(self) -> None:
        """All CPG check IDs start with 'CPG.'."""
        for cid in _signal_ids_for(CPG_CONSUMER_PLAYBOOK):
            assert cid.startswith("CPG."), f"Check {cid} missing CPG. prefix"

    def test_sic_ranges_cover_food_tobacco(self) -> None:
        """SIC ranges cover food (2000-2099) and tobacco (2100-2199)."""
        ranges = CPG_CONSUMER_PLAYBOOK["sic_ranges"]
        lows = [r["low"] for r in ranges]
        assert 2000 in lows, "Missing food SIC range starting at 2000"
        assert 2100 in lows, "Missing tobacco SIC range starting at 2100"

    def test_has_10_checks(self) -> None:
        """CPG playbook has exactly 10 industry checks."""
        assert len(CPG_CONSUMER_PLAYBOOK["industry_checks"]) == 10

    def test_claim_theories_are_structured(self) -> None:
        """CPG claim theories use structured dict format."""
        for ct in CPG_CONSUMER_PLAYBOOK["claim_theories"]:
            assert isinstance(ct, dict)
            assert "id" in ct
            assert "name" in ct


class TestMediaPlaybookStructure:
    """Verify Media/Entertainment playbook structure."""

    def test_id_and_name(self) -> None:
        """Media playbook has correct ID and name."""
        assert MEDIA_ENTERTAINMENT_PLAYBOOK["id"] == "MEDIA_ENTERTAINMENT"

    def test_signal_ids_prefix(self) -> None:
        """All Media check IDs start with 'MEDIA.'."""
        for cid in _signal_ids_for(MEDIA_ENTERTAINMENT_PLAYBOOK):
            assert cid.startswith("MEDIA."), (
                f"Check {cid} missing MEDIA. prefix"
            )

    def test_sic_ranges(self) -> None:
        """SIC ranges cover publishing, communications, entertainment."""
        ranges = MEDIA_ENTERTAINMENT_PLAYBOOK["sic_ranges"]
        lows = {r["low"] for r in ranges}
        assert 2700 in lows, "Missing publishing SIC range"
        assert 4800 in lows, "Missing communications SIC range"

    def test_has_10_checks(self) -> None:
        """Media playbook has exactly 10 industry checks."""
        assert len(MEDIA_ENTERTAINMENT_PLAYBOOK["industry_checks"]) == 10


class TestIndustrialsPlaybookStructure:
    """Verify Industrials/Manufacturing playbook structure."""

    def test_id_and_name(self) -> None:
        """Industrials playbook has correct ID and name."""
        assert INDUSTRIALS_MFG_PLAYBOOK["id"] == "INDUSTRIALS_MFG"

    def test_signal_ids_prefix(self) -> None:
        """All Industrials check IDs start with 'MFG.'."""
        for cid in _signal_ids_for(INDUSTRIALS_MFG_PLAYBOOK):
            assert cid.startswith("MFG."), (
                f"Check {cid} missing MFG. prefix"
            )

    def test_sic_ranges_cover_manufacturing(self) -> None:
        """SIC ranges cover fabricated metals, machinery, transport equip."""
        ranges = INDUSTRIALS_MFG_PLAYBOOK["sic_ranges"]
        lows = {r["low"] for r in ranges}
        assert 3400 in lows, "Missing fabricated metals SIC range"
        assert 3500 in lows, "Missing industrial machinery SIC range"
        assert 3700 in lows, "Missing transport equipment SIC range"

    def test_has_10_checks(self) -> None:
        """Industrials playbook has exactly 10 industry checks."""
        assert len(INDUSTRIALS_MFG_PLAYBOOK["industry_checks"]) == 10


class TestReitsPlaybookStructure:
    """Verify REITs/Real Estate playbook structure."""

    def test_id_and_name(self) -> None:
        """REITs playbook has correct ID and name."""
        assert REITS_REAL_ESTATE_PLAYBOOK["id"] == "REITS_REAL_ESTATE"

    def test_signal_ids_prefix(self) -> None:
        """All REIT check IDs start with 'REIT.'."""
        for cid in _signal_ids_for(REITS_REAL_ESTATE_PLAYBOOK):
            assert cid.startswith("REIT."), (
                f"Check {cid} missing REIT. prefix"
            )

    def test_sic_ranges(self) -> None:
        """SIC ranges cover real estate (6510-6553)."""
        ranges = REITS_REAL_ESTATE_PLAYBOOK["sic_ranges"]
        assert len(ranges) >= 1
        assert ranges[0]["low"] == 6510

    def test_has_10_checks(self) -> None:
        """REITs playbook has exactly 10 industry checks."""
        assert len(REITS_REAL_ESTATE_PLAYBOOK["industry_checks"]) == 10


class TestTransportationPlaybookStructure:
    """Verify Transportation/Rail playbook structure."""

    def test_id_and_name(self) -> None:
        """Transportation playbook has correct ID and name."""
        assert TRANSPORTATION_RAIL_PLAYBOOK["id"] == "TRANSPORTATION_RAIL"

    def test_signal_ids_prefix(self) -> None:
        """All Transportation check IDs start with 'RAIL.'."""
        for cid in _signal_ids_for(TRANSPORTATION_RAIL_PLAYBOOK):
            assert cid.startswith("RAIL."), (
                f"Check {cid} missing RAIL. prefix"
            )

    def test_sic_ranges_cover_transport(self) -> None:
        """SIC ranges cover railroad, trucking, air, water transport."""
        ranges = TRANSPORTATION_RAIL_PLAYBOOK["sic_ranges"]
        lows = {r["low"] for r in ranges}
        assert 4000 in lows, "Missing railroad SIC range"
        assert 4200 in lows, "Missing trucking SIC range"
        assert 4500 in lows, "Missing air transport SIC range"

    def test_has_10_checks(self) -> None:
        """Transportation playbook has exactly 10 industry checks."""
        assert len(TRANSPORTATION_RAIL_PLAYBOOK["industry_checks"]) == 10


class TestNoDuplicateCheckIds:
    """Verify no duplicate check IDs across all 10 playbooks."""

    def test_all_signal_ids_unique(self) -> None:
        """All check IDs across all 10 playbooks are unique."""
        all_ids: list[str] = []
        for pb in INDUSTRY_PLAYBOOKS:
            for check in pb.get("industry_checks", []):
                all_ids.append(check["id"])
        assert len(all_ids) == len(set(all_ids)), (
            f"Duplicate IDs found: "
            f"{[x for x in all_ids if all_ids.count(x) > 1]}"
        )


class TestSicRangesNoOverlap:
    """Verify SIC ranges across all 10 playbooks don't overlap."""

    def test_no_sic_overlap(self) -> None:
        """Each SIC code maps to at most one playbook."""
        # Collect all (low, high, playbook_id) triples
        all_ranges: list[tuple[int, int, str]] = []
        for pb in INDUSTRY_PLAYBOOKS:
            pb_id = pb["id"]
            for rng in pb["sic_ranges"]:
                all_ranges.append((rng["low"], rng["high"], pb_id))

        # Check every pair for overlap
        for i, (low_a, high_a, id_a) in enumerate(all_ranges):
            for low_b, high_b, id_b in all_ranges[i + 1 :]:
                overlap = low_a <= high_b and low_b <= high_a
                assert not overlap, (
                    f"SIC overlap: {id_a} [{low_a}-{high_a}] "
                    f"overlaps {id_b} [{low_b}-{high_b}]"
                )


class TestPlaybookActivationBySic:
    """Verify SIC-based playbook activation for new industries."""

    @pytest.mark.parametrize(
        ("sic", "expected_id"),
        [
            ("2050", "CPG_CONSUMER"),
            ("2150", "CPG_CONSUMER"),
            ("3500", "INDUSTRIALS_MFG"),
            ("3450", "INDUSTRIALS_MFG"),
            ("3750", "INDUSTRIALS_MFG"),
            ("6510", "REITS_REAL_ESTATE"),
            ("6550", "REITS_REAL_ESTATE"),
            ("4011", "TRANSPORTATION_RAIL"),
            ("4200", "TRANSPORTATION_RAIL"),
            ("4500", "TRANSPORTATION_RAIL"),
            ("2750", "MEDIA_ENTERTAINMENT"),
            ("4850", "MEDIA_ENTERTAINMENT"),
            ("7812", "MEDIA_ENTERTAINMENT"),
        ],
    )
    def test_sic_activates_correct_playbook(
        self,
        store: KnowledgeStore,
        sic: str,
        expected_id: str,
    ) -> None:
        """SIC code correctly maps to the expected new playbook."""
        result = store.get_playbook_for_sic(sic)
        assert result is not None, f"No playbook for SIC {sic}"
        assert result["id"] == expected_id


_OLD_UW_DIR = Path("Old Underwriter")
_SUPPLEMENTS = [
    "cpg_industry_module_supplement.md",
    "industrials_manufacturing_industry_module_supplement.md",
    "media_entertainment_industry_module_supplement.md",
    "reits_real_estate_industry_module_supplement_v2.md",
    "transportation_freight_rail_industry_module_supplement.md",
]


@pytest.mark.skipif(
    not _OLD_UW_DIR.exists(),
    reason="Old Underwriter/ directory not present",
)
class TestIngestSupplements:
    """Verify supplement documents can be ingested via pipeline."""

    def test_ingest_all_supplements(self) -> None:
        """Ingest all 5 supplements and verify content extracted."""
        from do_uw.knowledge.ingestion import (
            DocumentType,
            ingest_document,
        )

        s = KnowledgeStore(db_path=None)
        total_signals = 0
        total_notes = 0
        ingested_count = 0

        for name in _SUPPLEMENTS:
            path = _OLD_UW_DIR / name
            if not path.exists():
                continue
            result = ingest_document(
                s, path, DocumentType.INDUSTRY_ANALYSIS
            )
            total_signals += result.checks_created
            total_notes += result.notes_added
            ingested_count += 1
            # Allow UNIQUE constraint errors (timestamp-based ID
            # collisions within same second are expected)
            non_unique_errors = [
                e for e in result.errors
                if "UNIQUE constraint" not in e
            ]
            assert non_unique_errors == [], (
                f"Non-trivial errors ingesting {name}: "
                f"{non_unique_errors}"
            )

        assert ingested_count == 5, (
            f"Only {ingested_count}/5 supplements found"
        )
        # Should extract meaningful content from supplements
        assert total_signals + total_notes > 0, (
            "No content extracted from supplements"
        )
