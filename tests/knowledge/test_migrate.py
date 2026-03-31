"""Tests for migration of brain/ JSON files to the knowledge store."""

from __future__ import annotations

from pathlib import Path

import pytest

from do_uw.knowledge.migrate import MigrationResult, migrate_from_json
from do_uw.knowledge.store import KnowledgeStore

# Path to actual brain/ JSON files
BRAIN_DIR = Path(__file__).parent.parent.parent / "src" / "do_uw" / "brain"


@pytest.fixture()
def store() -> KnowledgeStore:
    """Create an in-memory KnowledgeStore."""
    return KnowledgeStore(db_path=None)


@pytest.fixture()
def migrated(store: KnowledgeStore) -> MigrationResult:
    """Run migration and return result."""
    return migrate_from_json(BRAIN_DIR, store)


class TestMigrationCounts:
    """Verify correct counts of migrated records."""

    def test_no_errors(self, migrated: MigrationResult) -> None:
        """Migration should complete with zero errors."""
        assert migrated.errors == [], f"Errors: {migrated.errors}"

    def test_400_checks_migrated(self, migrated: MigrationResult) -> None:
        """All 400 checks must be migrated (388 original - 4 stubs + 12 new Phase 33-03)."""
        assert migrated.checks_migrated == 400

    def test_19_patterns_migrated(self, migrated: MigrationResult) -> None:
        """All 19 patterns from patterns.json must be migrated."""
        assert migrated.patterns_migrated == 19

    def test_scoring_rules_migrated(
        self, migrated: MigrationResult
    ) -> None:
        """All scoring rules across 10 factors must be migrated."""
        # 55 rules across 10 factors (counted from scoring.json)
        assert migrated.rules_migrated == 55

    def test_17_red_flags_migrated(
        self, migrated: MigrationResult
    ) -> None:
        """All 17 red flags from red_flags.json must be migrated."""
        assert migrated.flags_migrated == 17

    def test_sector_baselines_migrated(
        self, migrated: MigrationResult
    ) -> None:
        """Sector baselines must be migrated (multiple entries)."""
        assert migrated.sectors_migrated > 0


class TestChecksMigration:
    """Verify check migration details."""

    def test_all_checks_active(
        self, store: KnowledgeStore, migrated: MigrationResult
    ) -> None:
        """All migrated checks must have ACTIVE status."""
        checks = store.query_checks(limit=500)
        assert len(checks) == 400
        assert all(c["status"] == "ACTIVE" for c in checks)

    def test_all_checks_have_origin(
        self, store: KnowledgeStore, migrated: MigrationResult
    ) -> None:
        """All migrated checks must have BRAIN_MIGRATION origin."""
        checks = store.query_checks(limit=500)
        assert all(c["origin"] == "BRAIN_MIGRATION" for c in checks)

    def test_check_sections(
        self, store: KnowledgeStore, migrated: MigrationResult
    ) -> None:
        """Checks should span sections 1-5 (section 6 merged into 4-5)."""
        sections = set()
        for c in store.query_checks(limit=500):
            sections.add(c["section"])
        assert sections == {1, 2, 3, 4, 5}

    def test_specific_check_lookup(
        self, store: KnowledgeStore, migrated: MigrationResult
    ) -> None:
        """Can look up a specific check by ID."""
        check = store.get_check("BIZ.CLASS.primary")
        assert check is not None
        assert check["name"] == "Primary D&O Risk Classification"
        assert check["section"] == 1

    def test_check_has_required_data(
        self, store: KnowledgeStore, migrated: MigrationResult
    ) -> None:
        """Check should have required_data preserved."""
        check = store.get_check("BIZ.CLASS.primary")
        assert check is not None
        assert "SEC_10K" in check["required_data"]

    def test_check_metadata_stored(
        self, store: KnowledgeStore, migrated: MigrationResult
    ) -> None:
        """Original check JSON should be stored in metadata_json."""
        check = store.get_check("BIZ.CLASS.primary")
        assert check is not None
        assert check["metadata_json"] is not None

    def test_search_checks(
        self, store: KnowledgeStore, migrated: MigrationResult
    ) -> None:
        """Full-text search should find checks by name."""
        results = store.search_checks("Revenue")
        assert len(results) > 0


class TestScoringMigration:
    """Verify scoring rules migration."""

    def test_factor_coverage(
        self, store: KnowledgeStore, migrated: MigrationResult
    ) -> None:
        """Rules should exist for all 10 factors."""
        all_rules = store.get_scoring_rules()
        factor_ids = {r["factor_id"] for r in all_rules}
        expected_factors = {
            "F1_prior_litigation",
            "F2_stock_decline",
            "F3_restatement_audit",
            "F4_ipo_spac_ma",
            "F5_guidance_misses",
            "F6_short_interest",
            "F7_volatility",
            "F8_financial_distress",
            "F9_governance",
            "F10_officer_stability",
        }
        assert factor_ids == expected_factors

    def test_f1_rules(
        self, store: KnowledgeStore, migrated: MigrationResult
    ) -> None:
        """F1 prior litigation should have 7 rules."""
        rules = store.get_scoring_rules(
            factor_id="F1_prior_litigation"
        )
        assert len(rules) == 7

    def test_crf_trigger(
        self, store: KnowledgeStore, migrated: MigrationResult
    ) -> None:
        """F1-001 should trigger CRF-001."""
        rules = store.get_scoring_rules(
            factor_id="F1_prior_litigation"
        )
        f1_001 = next(r for r in rules if r["id"] == "F1-001")
        assert f1_001["triggers_crf"] == "CRF-001"
        assert f1_001["points"] == 20.0


class TestPatternsMigration:
    """Verify pattern migration details."""

    def test_pattern_categories(
        self, store: KnowledgeStore, migrated: MigrationResult
    ) -> None:
        """Patterns should span expected categories."""
        patterns = store.query_patterns()
        categories = {p["category"] for p in patterns}
        assert "stock" in categories
        assert "business" in categories

    def test_specific_pattern(
        self, store: KnowledgeStore, migrated: MigrationResult
    ) -> None:
        """Can retrieve specific pattern with full data."""
        patterns = store.query_patterns(category="stock")
        event_collapse = next(
            (p for p in patterns
             if p["id"] == "PATTERN.STOCK.EVENT_COLLAPSE"),
            None,
        )
        assert event_collapse is not None
        assert "A" in event_collapse["allegation_types"]


class TestRedFlagsMigration:
    """Verify red flag migration details."""

    def test_all_flags_active(
        self, store: KnowledgeStore, migrated: MigrationResult
    ) -> None:
        """All migrated red flags must be ACTIVE."""
        flags = store.get_red_flags()
        assert len(flags) == 17  # CRF-1 through CRF-17
        assert all(f["status"] == "ACTIVE" for f in flags)

    def test_crf01_details(
        self, store: KnowledgeStore, migrated: MigrationResult
    ) -> None:
        """CRF-01 should have correct max tier and score."""
        flags = store.get_red_flags()
        crf01 = next(f for f in flags if f["id"] == "CRF-01")
        assert crf01["max_tier"] == "WALK"
        assert crf01["max_quality_score"] == 30.0


class TestSectorsMigration:
    """Verify sector baseline migration."""

    def test_major_sections_present(
        self, store: KnowledgeStore, migrated: MigrationResult
    ) -> None:
        """Key sector sections should be present."""
        baselines = store.get_sector_baselines()
        assert "short_interest" in baselines
        assert "volatility_90d" in baselines
        assert "leverage_debt_ebitda" in baselines

    def test_tech_short_interest(
        self, store: KnowledgeStore, migrated: MigrationResult
    ) -> None:
        """TECH short interest should have correct baseline."""
        baselines = store.get_sector_baselines(sector_code="TECH")
        si = baselines.get("short_interest", {})
        tech_si = si.get("TECH", {})
        assert isinstance(tech_si, dict)
        assert tech_si["normal"] == 4


class TestMetadataStorage:
    """Verify raw JSON metadata is stored for reconstruction."""

    def test_checks_raw_stored(
        self, store: KnowledgeStore, migrated: MigrationResult
    ) -> None:
        """Full signals.json should be stored as metadata."""
        raw = store.get_metadata("checks_raw")
        assert raw is not None
        assert "signals" in raw
        assert len(raw["signals"]) == 400

    def test_scoring_raw_stored(
        self, store: KnowledgeStore, migrated: MigrationResult
    ) -> None:
        """Full scoring.json should be stored as metadata."""
        raw = store.get_metadata("scoring_raw")
        assert raw is not None
        assert "factors" in raw
        assert len(raw["factors"]) == 10

    def test_patterns_raw_stored(
        self, store: KnowledgeStore, migrated: MigrationResult
    ) -> None:
        """Full patterns.json should be stored as metadata."""
        raw = store.get_metadata("patterns_raw")
        assert raw is not None
        assert raw.get("total_patterns") == 19

    def test_red_flags_raw_stored(
        self, store: KnowledgeStore, migrated: MigrationResult
    ) -> None:
        """Full red_flags.json should be stored as metadata."""
        raw = store.get_metadata("red_flags_raw")
        assert raw is not None
        assert len(raw["escalation_triggers"]) == 17

    def test_sectors_raw_stored(
        self, store: KnowledgeStore, migrated: MigrationResult
    ) -> None:
        """Full sectors.json should be stored as metadata."""
        raw = store.get_metadata("sectors_raw")
        assert raw is not None
        assert "short_interest" in raw
