"""Tests for the KnowledgeStore query API."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from do_uw.knowledge.models import (
    Check,
    IndustryPlaybook,
    Pattern,
    RedFlag,
    ScoringRule,
    Sector,
)
from do_uw.knowledge.store import KnowledgeStore


def _now() -> datetime:
    return datetime.now(UTC)


def _make_check(
    signal_id: str,
    name: str = "Test Check",
    section: int = 1,
    pillar: str = "P1_WHAT_WRONG",
    status: str = "ACTIVE",
    severity: str | None = None,
    scoring_factor: str | None = None,
) -> Check:
    """Create a Check ORM object for testing."""
    return Check(
        id=signal_id,
        name=name,
        section=section,
        pillar=pillar,
        severity=severity,
        execution_mode="AUTO",
        status=status,
        threshold_type="percentage",
        threshold_value="10",
        required_data=["SEC_10K"],
        data_locations={"SEC_10K": ["item_1"]},
        scoring_factor=scoring_factor,
        scoring_rule=None,
        output_section=None,
        origin="BRAIN_MIGRATION",
        created_at=_now(),
        modified_at=_now(),
        version=1,
        metadata_json=None,
    )


def _make_pattern(
    pattern_id: str,
    category: str = "stock",
    allegation_types: list[str] | None = None,
    status: str = "ACTIVE",
) -> Pattern:
    """Create a Pattern ORM object for testing."""
    return Pattern(
        id=pattern_id,
        name=f"Pattern {pattern_id}",
        category=category,
        description="Test pattern",
        allegation_types=allegation_types or ["A"],
        trigger_conditions=[{"field": "x", "operator": "gt", "value": 1}],
        score_impact={"F1": {"base": 2, "max": 5}},
        severity_modifier=None,
        status=status,
        created_at=_now(),
        modified_at=_now(),
    )


def _make_scoring_rule(
    rule_id: str,
    factor_id: str = "F1_prior_litigation",
    points: float = 10.0,
    triggers_crf: str | None = None,
) -> ScoringRule:
    """Create a ScoringRule ORM object for testing."""
    return ScoringRule(
        id=rule_id,
        factor_id=factor_id,
        condition="Test condition",
        points=points,
        triggers_crf=triggers_crf,
        created_at=_now(),
    )


def _make_red_flag(
    flag_id: str,
    max_tier: str = "WALK",
    max_quality_score: float = 30.0,
    status: str = "ACTIVE",
) -> RedFlag:
    """Create a RedFlag ORM object for testing."""
    return RedFlag(
        id=flag_id,
        name=f"Flag {flag_id}",
        condition="Test condition",
        detection_logic=None,
        max_tier=max_tier,
        max_quality_score=max_quality_score,
        status=status,
        created_at=_now(),
    )


def _make_playbook(
    playbook_id: str,
    sic_ranges: list[dict[str, int]] | None = None,
    status: str = "ACTIVE",
) -> IndustryPlaybook:
    """Create an IndustryPlaybook ORM object for testing."""
    return IndustryPlaybook(
        id=playbook_id,
        name=f"Playbook {playbook_id}",
        description="Test playbook",
        sic_ranges=sic_ranges or [{"low": 7370, "high": 7379}],
        naics_prefixes=["5112"],
        check_overrides=None,
        scoring_adjustments=None,
        risk_patterns=None,
        claim_theories=None,
        meeting_questions=None,
        status=status,
        created_at=_now(),
        modified_at=_now(),
    )


@pytest.fixture()
def store() -> KnowledgeStore:
    """Create an in-memory KnowledgeStore with test data."""
    ks = KnowledgeStore(db_path=None)
    return ks


@pytest.fixture()
def populated_store(store: KnowledgeStore) -> KnowledgeStore:
    """Populate the store with test data."""
    checks = [
        _make_check("CHK-01", "Revenue Growth", section=1, pillar="P1_WHAT_WRONG",
                     scoring_factor="F1"),
        _make_check("CHK-02", "Stock Decline", section=2, pillar="P2_HOW_LIKELY",
                     scoring_factor="F2"),
        _make_check("CHK-03", "Governance Board", section=3, pillar="P3_HOW_BAD",
                     status="DEPRECATED"),
        _make_check("CHK-04", "Litigation History", section=1, pillar="P1_WHAT_WRONG",
                     scoring_factor="F1"),
        _make_check("CHK-05", "Financial Distress", section=4, pillar="P2_HOW_LIKELY",
                     severity="HIGH"),
    ]
    store.bulk_insert_checks(checks)

    patterns = [
        _make_pattern("PAT-01", category="stock", allegation_types=["A", "B"]),
        _make_pattern("PAT-02", category="business", allegation_types=["C"]),
        _make_pattern("PAT-03", category="stock", allegation_types=["A"],
                      status="DEPRECATED"),
    ]
    store.bulk_insert_patterns(patterns)

    rules = [
        _make_scoring_rule("F1-001", "F1_prior_litigation", 20.0, "CRF-001"),
        _make_scoring_rule("F1-002", "F1_prior_litigation", 15.0),
        _make_scoring_rule("F2-001", "F2_stock_decline", 15.0),
    ]
    store.bulk_insert_scoring_rules(rules)

    flags = [
        _make_red_flag("CRF-01", "WALK", 30.0),
        _make_red_flag("CRF-02", "WALK", 30.0),
        _make_red_flag("CRF-04", "WATCH", 50.0, status="DEPRECATED"),
    ]
    store.bulk_insert_red_flags(flags)

    # Add sectors
    sectors = [
        Sector(
            sector_code="TECH", metric_name="short_interest",
            baseline_value=4.0,
            metadata_json='{"normal": 4, "elevated": 7, "high": 10}',
            created_at=_now(),
        ),
        Sector(
            sector_code="BIOT", metric_name="short_interest",
            baseline_value=6.0,
            metadata_json='{"normal": 6, "elevated": 10, "high": 15}',
            created_at=_now(),
        ),
        Sector(
            sector_code="TECH", metric_name="volatility_90d",
            baseline_value=2.5,
            metadata_json='{"typical": 2.5, "elevated": 4, "high": 6}',
            created_at=_now(),
        ),
    ]
    store.bulk_insert_sectors(sectors)

    # Add playbooks
    playbooks = [
        _make_playbook("PB-TECH", sic_ranges=[{"low": 7370, "high": 7379}]),
        _make_playbook("PB-BIOT", sic_ranges=[{"low": 2830, "high": 2836}]),
        _make_playbook("PB-DEAD", sic_ranges=[{"low": 1000, "high": 1099}],
                       status="DEPRECATED"),
    ]
    with store._session() as session:
        session.add_all(playbooks)
        session.flush()

    return store


# ---------------------------------------------------------------
# Check query tests
# ---------------------------------------------------------------

class TestQueryChecks:
    """Tests for query_checks multi-criteria filtering."""

    def test_query_all(self, populated_store: KnowledgeStore) -> None:
        results = populated_store.query_checks()
        assert len(results) == 5

    def test_query_by_section(self, populated_store: KnowledgeStore) -> None:
        results = populated_store.query_checks(section=1)
        assert len(results) == 2
        assert all(r["section"] == 1 for r in results)

    def test_query_by_status(self, populated_store: KnowledgeStore) -> None:
        results = populated_store.query_checks(status="DEPRECATED")
        assert len(results) == 1
        assert results[0]["id"] == "CHK-03"

    def test_query_by_factor(self, populated_store: KnowledgeStore) -> None:
        results = populated_store.query_checks(factor="F1")
        assert len(results) == 2

    def test_query_by_pillar(self, populated_store: KnowledgeStore) -> None:
        results = populated_store.query_checks(pillar="P2_HOW_LIKELY")
        assert len(results) == 2

    def test_query_by_severity(self, populated_store: KnowledgeStore) -> None:
        results = populated_store.query_checks(severity="HIGH")
        assert len(results) == 1
        assert results[0]["id"] == "CHK-05"

    def test_query_combined_filters(self, populated_store: KnowledgeStore) -> None:
        results = populated_store.query_checks(section=1, factor="F1")
        assert len(results) == 2

    def test_query_limit(self, populated_store: KnowledgeStore) -> None:
        results = populated_store.query_checks(limit=2)
        assert len(results) == 2

    def test_query_no_match(self, populated_store: KnowledgeStore) -> None:
        results = populated_store.query_checks(section=99)
        assert len(results) == 0


class TestGetCheck:
    """Tests for get_check single check lookup."""

    def test_get_existing(self, populated_store: KnowledgeStore) -> None:
        result = populated_store.get_check("CHK-01")
        assert result is not None
        assert result["name"] == "Revenue Growth"

    def test_get_nonexistent(self, populated_store: KnowledgeStore) -> None:
        result = populated_store.get_check("NONEXISTENT")
        assert result is None


class TestSearchChecks:
    """Tests for search_checks full-text / LIKE search."""

    def test_search_by_name(self, populated_store: KnowledgeStore) -> None:
        results = populated_store.search_checks("Revenue")
        assert len(results) >= 1
        assert any(r["id"] == "CHK-01" for r in results)

    def test_search_by_pillar(self, populated_store: KnowledgeStore) -> None:
        results = populated_store.search_checks("P1_WHAT_WRONG")
        assert len(results) >= 1

    def test_search_no_match(self, populated_store: KnowledgeStore) -> None:
        results = populated_store.search_checks("XYZNONEXISTENT")
        assert len(results) == 0


# ---------------------------------------------------------------
# Pattern query tests
# ---------------------------------------------------------------

class TestQueryPatterns:
    """Tests for query_patterns filtering."""

    def test_query_all_patterns(self, populated_store: KnowledgeStore) -> None:
        results = populated_store.query_patterns()
        assert len(results) == 3

    def test_query_by_category(self, populated_store: KnowledgeStore) -> None:
        results = populated_store.query_patterns(category="stock")
        assert len(results) == 2

    def test_query_by_allegation_type(self, populated_store: KnowledgeStore) -> None:
        results = populated_store.query_patterns(allegation_type="C")
        assert len(results) == 1
        assert results[0]["id"] == "PAT-02"

    def test_query_by_status(self, populated_store: KnowledgeStore) -> None:
        results = populated_store.query_patterns(status="ACTIVE")
        assert len(results) == 2


# ---------------------------------------------------------------
# Scoring rule tests
# ---------------------------------------------------------------

class TestGetScoringRules:
    """Tests for get_scoring_rules."""

    def test_get_all_rules(self, populated_store: KnowledgeStore) -> None:
        results = populated_store.get_scoring_rules()
        assert len(results) == 3

    def test_get_by_factor(self, populated_store: KnowledgeStore) -> None:
        results = populated_store.get_scoring_rules(factor_id="F1_prior_litigation")
        assert len(results) == 2

    def test_rule_fields(self, populated_store: KnowledgeStore) -> None:
        results = populated_store.get_scoring_rules(factor_id="F1_prior_litigation")
        rule = next(r for r in results if r["id"] == "F1-001")
        assert rule["points"] == 20.0
        assert rule["triggers_crf"] == "CRF-001"


# ---------------------------------------------------------------
# Red flag tests
# ---------------------------------------------------------------

class TestGetRedFlags:
    """Tests for get_red_flags."""

    def test_get_all_flags(self, populated_store: KnowledgeStore) -> None:
        results = populated_store.get_red_flags()
        assert len(results) == 3

    def test_get_active_only(self, populated_store: KnowledgeStore) -> None:
        results = populated_store.get_red_flags(status="ACTIVE")
        assert len(results) == 2


# ---------------------------------------------------------------
# Sector tests
# ---------------------------------------------------------------

class TestGetSectorBaselines:
    """Tests for get_sector_baselines."""

    def test_get_all_baselines(self, populated_store: KnowledgeStore) -> None:
        result = populated_store.get_sector_baselines()
        assert "short_interest" in result
        assert "volatility_90d" in result
        assert "TECH" in result["short_interest"]
        assert "BIOT" in result["short_interest"]

    def test_get_by_sector_code(self, populated_store: KnowledgeStore) -> None:
        result = populated_store.get_sector_baselines(sector_code="TECH")
        assert "short_interest" in result
        assert "volatility_90d" in result
        assert "TECH" in result["short_interest"]

    def test_metadata_parsed(self, populated_store: KnowledgeStore) -> None:
        result = populated_store.get_sector_baselines()
        tech_si = result["short_interest"]["TECH"]
        assert isinstance(tech_si, dict)
        assert tech_si["normal"] == 4


# ---------------------------------------------------------------
# Note tests
# ---------------------------------------------------------------

class TestNotes:
    """Tests for add_note and search_notes."""

    def test_add_and_search_note(self, store: KnowledgeStore) -> None:
        note_id = store.add_note(
            title="Biotech risk factors",
            content="Watch for Phase III trial failures and FDA rejections",
            tags="biotech,risk",
        )
        assert isinstance(note_id, int)
        results = store.search_notes("biotech")
        assert len(results) >= 1
        assert any(r["title"] == "Biotech risk factors" for r in results)

    def test_search_no_match(self, store: KnowledgeStore) -> None:
        store.add_note(title="Test", content="Nothing relevant")
        results = store.search_notes("XYZNONEXISTENT")
        assert len(results) == 0


# ---------------------------------------------------------------
# Playbook tests
# ---------------------------------------------------------------

class TestPlaybooks:
    """Tests for get_playbook and get_playbook_for_sic."""

    def test_get_playbook_by_id(self, populated_store: KnowledgeStore) -> None:
        result = populated_store.get_playbook("PB-TECH")
        assert result is not None
        assert result["name"] == "Playbook PB-TECH"

    def test_get_nonexistent_playbook(self, populated_store: KnowledgeStore) -> None:
        result = populated_store.get_playbook("PB-NONE")
        assert result is None

    def test_get_playbook_for_sic_match(
        self, populated_store: KnowledgeStore
    ) -> None:
        result = populated_store.get_playbook_for_sic("7372")
        assert result is not None
        assert result["id"] == "PB-TECH"

    def test_get_playbook_for_sic_no_match(
        self, populated_store: KnowledgeStore
    ) -> None:
        result = populated_store.get_playbook_for_sic("9999")
        assert result is None

    def test_get_playbook_for_sic_invalid(
        self, populated_store: KnowledgeStore
    ) -> None:
        result = populated_store.get_playbook_for_sic("abc")
        assert result is None

    def test_deprecated_playbook_not_matched(
        self, populated_store: KnowledgeStore
    ) -> None:
        """Deprecated playbooks should not be returned by SIC lookup."""
        result = populated_store.get_playbook_for_sic("1050")
        assert result is None


# ---------------------------------------------------------------
# Metadata tests
# ---------------------------------------------------------------

class TestMetadata:
    """Tests for store_metadata and get_metadata."""

    def test_store_and_retrieve(self, store: KnowledgeStore) -> None:
        data: dict[str, Any] = {"key": "value", "nested": {"a": 1}}
        store.store_metadata("test_key", data)
        result = store.get_metadata("test_key")
        assert result is not None
        assert result["key"] == "value"
        assert result["nested"]["a"] == 1

    def test_get_nonexistent(self, store: KnowledgeStore) -> None:
        result = store.get_metadata("no_such_key")
        assert result is None

    def test_overwrite(self, store: KnowledgeStore) -> None:
        store.store_metadata("k", {"v": 1})
        store.store_metadata("k", {"v": 2})
        result = store.get_metadata("k")
        assert result is not None
        assert result["v"] == 2


# ---------------------------------------------------------------
# Bulk insert tests
# ---------------------------------------------------------------

class TestBulkInsert:
    """Tests for bulk insert operations."""

    def test_bulk_insert_checks(self, store: KnowledgeStore) -> None:
        checks = [_make_check(f"BLK-{i}") for i in range(5)]
        count = store.bulk_insert_checks(checks)
        assert count == 5
        assert len(store.query_checks()) == 5

    def test_bulk_insert_patterns(self, store: KnowledgeStore) -> None:
        patterns = [_make_pattern(f"BPAT-{i}") for i in range(3)]
        count = store.bulk_insert_patterns(patterns)
        assert count == 3
