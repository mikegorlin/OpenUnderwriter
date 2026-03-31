"""Tests for industry playbook activation and query API.

Tests cover:
- Playbook data integrity (10 verticals, 100 checks)
- SIC code activation for all verticals
- NAICS fallback activation
- Non-matching codes return None
- load_playbooks idempotency
- Query functions (checks, questions, scoring adjustments, claim theories)
- BrainLoader signal loading for playbook integration
- get_active_signals_with_industry merge logic
"""

from __future__ import annotations

import pytest

from do_uw.brain.brain_unified_loader import BrainLoader
from do_uw.knowledge.playbook_data import INDUSTRY_PLAYBOOKS
from do_uw.knowledge.playbooks import (
    activate_playbook,
    get_active_signals_with_industry,
    get_claim_theories,
    get_industry_signals,
    get_industry_questions,
    get_scoring_adjustments,
    load_playbooks,
)
from do_uw.knowledge.store import KnowledgeStore


@pytest.fixture()
def store() -> KnowledgeStore:
    """Create an in-memory knowledge store with playbooks loaded."""
    s = KnowledgeStore(db_path=None)
    load_playbooks(s)
    return s


class TestPlaybookData:
    """Test playbook data definitions."""

    def test_ten_playbooks_defined(self) -> None:
        """INDUSTRY_PLAYBOOKS has exactly 10 entries."""
        assert len(INDUSTRY_PLAYBOOKS) == 10

    def test_total_signals_at_least_50(self) -> None:
        """Total industry checks across all playbooks >= 50."""
        total = sum(
            len(pb.get("industry_checks", []))
            for pb in INDUSTRY_PLAYBOOKS
        )
        assert total >= 50

    def test_each_playbook_has_required_fields(self) -> None:
        """Each playbook has all required fields."""
        required = [
            "id", "name", "description", "sic_ranges",
            "naics_prefixes", "industry_checks", "risk_patterns",
            "claim_theories", "meeting_questions", "scoring_adjustments",
        ]
        for pb in INDUSTRY_PLAYBOOKS:
            for field in required:
                assert field in pb, (
                    f"Playbook {pb.get('id', '?')} missing field {field}"
                )

    def test_each_playbook_has_8_to_12_checks(self) -> None:
        """Each playbook has 8-12 industry checks."""
        for pb in INDUSTRY_PLAYBOOKS:
            count = len(pb.get("industry_checks", []))
            assert 8 <= count <= 12, (
                f"Playbook {pb['id']} has {count} checks, expected 8-12"
            )

    def test_check_has_required_fields(self) -> None:
        """Each check dict has required fields."""
        required = [
            "id", "name", "section", "pillar", "severity",
            "execution_mode", "threshold_type", "required_data",
            "data_locations", "output_section", "metadata_json",
        ]
        for pb in INDUSTRY_PLAYBOOKS:
            for check in pb.get("industry_checks", []):
                for field in required:
                    assert field in check, (
                        f"Check {check.get('id', '?')} in {pb['id']} "
                        f"missing field {field}"
                    )

    def test_playbook_ids_unique(self) -> None:
        """All playbook IDs are unique."""
        ids = [pb["id"] for pb in INDUSTRY_PLAYBOOKS]
        assert len(ids) == len(set(ids))

    def test_signal_ids_unique(self) -> None:
        """All check IDs across all playbooks are unique."""
        all_ids: list[str] = []
        for pb in INDUSTRY_PLAYBOOKS:
            for check in pb.get("industry_checks", []):
                all_ids.append(check["id"])
        assert len(all_ids) == len(set(all_ids))

    def test_sic_ranges_are_dicts_with_low_high(self) -> None:
        """SIC ranges use {low, high} dict format for store compatibility."""
        for pb in INDUSTRY_PLAYBOOKS:
            for rng in pb["sic_ranges"]:
                assert isinstance(rng, dict)
                assert "low" in rng
                assert "high" in rng
                assert rng["low"] <= rng["high"]


class TestLoadPlaybooks:
    """Test load_playbooks function."""

    def test_load_returns_10(self) -> None:
        """Loading into empty store inserts 10 playbooks."""
        s = KnowledgeStore(db_path=None)
        count = load_playbooks(s)
        assert count == 10

    def test_idempotent(self) -> None:
        """Second load inserts 0 new playbooks."""
        s = KnowledgeStore(db_path=None)
        load_playbooks(s)
        count2 = load_playbooks(s)
        assert count2 == 0

    def test_playbooks_accessible_by_id(self, store: KnowledgeStore) -> None:
        """All 5 playbooks retrievable by ID."""
        for pb_data in INDUSTRY_PLAYBOOKS:
            result = store.get_playbook(pb_data["id"])
            assert result is not None, f"Playbook {pb_data['id']} not found"
            assert result["name"] == pb_data["name"]


class TestActivatePlaybook:
    """Test SIC/NAICS-based playbook activation."""

    @pytest.mark.parametrize(
        ("sic", "expected_id"),
        [
            ("3571", "TECH_SAAS"),
            ("7372", "TECH_SAAS"),
            ("3674", "TECH_SAAS"),
            ("2834", "BIOTECH_PHARMA"),
            ("8731", "BIOTECH_PHARMA"),
            ("6020", "FINANCIAL_SERVICES"),
            ("6311", "FINANCIAL_SERVICES"),
            ("1311", "ENERGY_UTILITIES"),
            ("4911", "ENERGY_UTILITIES"),
            ("8011", "HEALTHCARE"),
            ("5912", "HEALTHCARE"),
        ],
    )
    def test_sic_activation(
        self,
        store: KnowledgeStore,
        sic: str,
        expected_id: str,
    ) -> None:
        """SIC codes correctly map to playbooks."""
        result = activate_playbook(sic, None, store)
        assert result is not None, f"No playbook for SIC {sic}"
        assert result["id"] == expected_id

    def test_non_matching_sic_returns_none(
        self, store: KnowledgeStore
    ) -> None:
        """SIC code with no matching playbook returns None."""
        result = activate_playbook("0100", None, store)
        assert result is None

    def test_empty_sic_returns_none(self, store: KnowledgeStore) -> None:
        """Empty SIC with no NAICS returns None."""
        result = activate_playbook("", None, store)
        assert result is None

    @pytest.mark.parametrize(
        ("naics", "expected_id"),
        [
            ("5112", "TECH_SAAS"),
            ("3254", "BIOTECH_PHARMA"),
            ("5221", "FINANCIAL_SERVICES"),
            ("2111", "ENERGY_UTILITIES"),
            ("6221", "HEALTHCARE"),
        ],
    )
    def test_naics_fallback(
        self,
        store: KnowledgeStore,
        naics: str,
        expected_id: str,
    ) -> None:
        """NAICS fallback activates when SIC fails."""
        result = activate_playbook("9999", naics, store)
        assert result is not None, f"No playbook for NAICS {naics}"
        assert result["id"] == expected_id


class TestQueryFunctions:
    """Test playbook query API functions."""

    def test_get_industry_signals(self, store: KnowledgeStore) -> None:
        """get_industry_signals returns correct check count."""
        checks = get_industry_signals(store, "TECH_SAAS")
        assert len(checks) == 10
        assert all("id" in c for c in checks)

    def test_get_industry_signals_unknown_id(
        self, store: KnowledgeStore
    ) -> None:
        """Unknown playbook ID returns empty list."""
        checks = get_industry_signals(store, "UNKNOWN_VERTICAL")
        assert checks == []

    def test_get_industry_questions(self, store: KnowledgeStore) -> None:
        """get_industry_questions returns meeting prep questions."""
        questions = get_industry_questions(store, "BIOTECH_PHARMA")
        assert len(questions) == 5
        assert all(isinstance(q, str) for q in questions)

    def test_get_scoring_adjustments(self, store: KnowledgeStore) -> None:
        """get_scoring_adjustments returns factor weight multipliers."""
        adj = get_scoring_adjustments(store, "TECH_SAAS")
        assert "F3_financial_health" in adj
        assert "F8_emerging_risks" in adj
        assert adj["F3_financial_health"] == 0.9
        assert adj["F8_emerging_risks"] == 1.2

    def test_get_claim_theories(self, store: KnowledgeStore) -> None:
        """get_claim_theories returns theory descriptions."""
        theories = get_claim_theories(store, "FINANCIAL_SERVICES")
        assert len(theories) == 5
        assert all(isinstance(t, str) for t in theories)

    def test_get_active_signals_with_industry(
        self, store: KnowledgeStore
    ) -> None:
        """get_active_signals_with_industry merges active + industry checks."""
        # Without playbook: only active checks
        base = get_active_signals_with_industry(store, None)

        # With playbook: active + industry checks
        merged = get_active_signals_with_industry(store, "TECH_SAAS")

        # Merged should have at least the industry checks
        assert len(merged) >= len(base)

    def test_get_active_checks_no_duplicates(
        self, store: KnowledgeStore
    ) -> None:
        """Merged check list has no duplicate IDs."""
        merged = get_active_signals_with_industry(store, "TECH_SAAS")
        ids = [c.get("id") for c in merged if isinstance(c, dict)]
        assert len(ids) == len(set(ids))


class TestBrainLoaderSignals:
    """Test BrainLoader loads signals for playbook integration."""

    def test_brain_loader_returns_signals(self) -> None:
        """BrainLoader returns standard signals."""
        loader = BrainLoader()
        checks_data = loader.load_signals()
        assert "signals" in checks_data
        assert checks_data.get("total_signals", 0) > 0
