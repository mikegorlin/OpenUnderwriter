"""Tests for narrative composition: risk story grouping.

Tests cover:
- Composing narratives from fired checks
- Template activation threshold (>= 2 matching checks)
- Severity ordering (HIGH before MEDIUM)
- Available narrative listing
- New narrative suggestions from co-firing data
- Edge cases (no matches, empty inputs)
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from do_uw.knowledge.models import Check
from do_uw.knowledge.narrative import (
    NARRATIVE_TEMPLATES,
    NarrativeStory,
    compose_narrative,
    get_available_narratives,
    suggest_new_narrative,
)
from do_uw.knowledge.store import KnowledgeStore


@pytest.fixture
def store() -> KnowledgeStore:
    """Create an in-memory knowledge store with sample checks."""
    ks = KnowledgeStore(db_path=None)
    _populate_sample_checks(ks)
    return ks


def _populate_sample_checks(store: KnowledgeStore) -> None:
    """Insert sample checks matching narrative template patterns."""
    now = datetime.now(UTC)
    checks = [
        # Restatement risk checks
        Check(
            id="FIN.ACCT.restatement",
            name="Financial Restatement History",
            section=3,
            pillar="Financial",
            severity="HIGH",
            status="ACTIVE",
            required_data=[],
            data_locations=[],
            scoring_factor="F1",
            origin="brain_migration",
            created_at=now,
            modified_at=now,
        ),
        Check(
            id="FIN.ACCT.earnings_manipulation",
            name="Earnings Manipulation Indicators",
            section=3,
            pillar="Financial",
            severity="HIGH",
            status="ACTIVE",
            required_data=[],
            data_locations=[],
            scoring_factor="F1",
            origin="brain_migration",
            created_at=now,
            modified_at=now,
        ),
        Check(
            id="FIN.ACCT.internal_controls",
            name="Internal Control Weaknesses",
            section=3,
            pillar="Financial",
            severity="MEDIUM",
            status="ACTIVE",
            required_data=[],
            data_locations=[],
            scoring_factor="F1",
            origin="brain_migration",
            created_at=now,
            modified_at=now,
        ),
        Check(
            id="FIN.ACCT.auditor",
            name="Auditor Concerns",
            section=3,
            pillar="Financial",
            severity="MEDIUM",
            status="ACTIVE",
            required_data=[],
            data_locations=[],
            scoring_factor="F3",
            origin="brain_migration",
            created_at=now,
            modified_at=now,
        ),
        # Event-driven claim checks
        Check(
            id="STOCK.PRICE.single_day_events",
            name="Significant Single-Day Price Drops",
            section=4,
            pillar="Market",
            severity="HIGH",
            status="ACTIVE",
            required_data=[],
            data_locations=[],
            scoring_factor="F2",
            origin="brain_migration",
            created_at=now,
            modified_at=now,
        ),
        Check(
            id="STOCK.PRICE.recent_drop_alert",
            name="Recent Stock Drop Alert",
            section=4,
            pillar="Market",
            severity="HIGH",
            status="ACTIVE",
            required_data=[],
            data_locations=[],
            scoring_factor="F5",
            origin="brain_migration",
            created_at=now,
            modified_at=now,
        ),
        Check(
            id="FIN.GUIDE.earnings_reaction",
            name="Earnings Reaction Analysis",
            section=3,
            pillar="Financial",
            severity="MEDIUM",
            status="ACTIVE",
            required_data=[],
            data_locations=[],
            scoring_factor="F2",
            origin="brain_migration",
            created_at=now,
            modified_at=now,
        ),
        # Governance failure checks
        Check(
            id="GOV.BOARD.independence",
            name="Board Independence Assessment",
            section=5,
            pillar="Governance",
            severity="MEDIUM",
            status="ACTIVE",
            required_data=[],
            data_locations=[],
            scoring_factor="F7",
            origin="brain_migration",
            created_at=now,
            modified_at=now,
        ),
        Check(
            id="GOV.BOARD.ceo_chair",
            name="CEO-Chair Duality",
            section=5,
            pillar="Governance",
            severity="LOW",
            status="ACTIVE",
            required_data=[],
            data_locations=[],
            scoring_factor="F7",
            origin="brain_migration",
            created_at=now,
            modified_at=now,
        ),
        Check(
            id="GOV.BOARD.overboarding",
            name="Director Overboarding",
            section=5,
            pillar="Governance",
            severity="LOW",
            status="ACTIVE",
            required_data=[],
            data_locations=[],
            scoring_factor="F8",
            origin="brain_migration",
            created_at=now,
            modified_at=now,
        ),
        # Regulatory exposure checks
        Check(
            id="LIT.REG.sec_active",
            name="Active SEC Investigation",
            section=6,
            pillar="Litigation",
            severity="HIGH",
            status="ACTIVE",
            required_data=[],
            data_locations=[],
            scoring_factor="F9",
            origin="brain_migration",
            created_at=now,
            modified_at=now,
        ),
        Check(
            id="LIT.REG.wells_notice",
            name="Wells Notice Received",
            section=6,
            pillar="Litigation",
            severity="HIGH",
            status="ACTIVE",
            required_data=[],
            data_locations=[],
            scoring_factor="F10",
            origin="brain_migration",
            created_at=now,
            modified_at=now,
        ),
        # Financial distress checks
        Check(
            id="FIN.DEBT.covenants",
            name="Debt Covenant Compliance",
            section=3,
            pillar="Financial",
            severity="HIGH",
            status="ACTIVE",
            required_data=[],
            data_locations=[],
            scoring_factor="F4",
            origin="brain_migration",
            created_at=now,
            modified_at=now,
        ),
        Check(
            id="FIN.LIQ.cash_burn",
            name="Cash Burn Rate Analysis",
            section=3,
            pillar="Financial",
            severity="MEDIUM",
            status="ACTIVE",
            required_data=[],
            data_locations=[],
            scoring_factor="F4",
            origin="brain_migration",
            created_at=now,
            modified_at=now,
        ),
        # Insider trading checks
        Check(
            id="STOCK.INSIDER.cluster_timing",
            name="Insider Cluster Selling Timing",
            section=4,
            pillar="Market",
            severity="HIGH",
            status="ACTIVE",
            required_data=[],
            data_locations=[],
            scoring_factor="F1",
            origin="brain_migration",
            created_at=now,
            modified_at=now,
        ),
        Check(
            id="STOCK.INSIDER.notable_activity",
            name="Notable Insider Trading Activity",
            section=4,
            pillar="Market",
            severity="MEDIUM",
            status="ACTIVE",
            required_data=[],
            data_locations=[],
            scoring_factor="F3",
            origin="brain_migration",
            created_at=now,
            modified_at=now,
        ),
        # Acquisition risk checks
        Check(
            id="LIT.SCA.merger_obj",
            name="Merger Objection Litigation",
            section=6,
            pillar="Litigation",
            severity="MEDIUM",
            status="ACTIVE",
            required_data=[],
            data_locations=[],
            scoring_factor="F2",
            origin="brain_migration",
            created_at=now,
            modified_at=now,
        ),
        Check(
            id="STOCK.VALUATION.premium_discount",
            name="Valuation Premium/Discount",
            section=4,
            pillar="Market",
            severity="LOW",
            status="ACTIVE",
            required_data=[],
            data_locations=[],
            scoring_factor="F2",
            origin="brain_migration",
            created_at=now,
            modified_at=now,
        ),
    ]
    store.bulk_insert_checks(checks)


class TestComposeNarrative:
    """Tests for narrative composition from fired checks."""

    def test_restatement_risk_activates(
        self, store: KnowledgeStore
    ) -> None:
        """Restatement risk template activates with 2+ matching checks."""
        fired = [
            "FIN.ACCT.restatement",
            "FIN.ACCT.earnings_manipulation",
            "FIN.ACCT.internal_controls",
        ]
        stories = compose_narrative(store, fired)
        assert len(stories) >= 1
        story_ids = [s.story_id for s in stories]
        assert "restatement_risk" in story_ids

    def test_no_matching_template_returns_empty(
        self, store: KnowledgeStore
    ) -> None:
        """Checks not matching any template -> no stories."""
        fired = ["UNKNOWN.CHECK.xyz", "ANOTHER.RANDOM.check"]
        stories = compose_narrative(store, fired)
        assert stories == []

    def test_activation_threshold_below(
        self, store: KnowledgeStore
    ) -> None:
        """Single matching check does not activate template."""
        fired = ["FIN.ACCT.restatement"]
        stories = compose_narrative(store, fired)
        # Restatement risk should NOT activate with only 1 check
        story_ids = [s.story_id for s in stories]
        assert "restatement_risk" not in story_ids

    def test_activation_threshold_at_boundary(
        self, store: KnowledgeStore
    ) -> None:
        """Exactly 2 matching checks activates template."""
        fired = ["FIN.ACCT.restatement", "FIN.ACCT.auditor"]
        stories = compose_narrative(store, fired)
        story_ids = [s.story_id for s in stories]
        assert "restatement_risk" in story_ids

    def test_severity_ordering_high_before_medium(
        self, store: KnowledgeStore
    ) -> None:
        """HIGH severity stories come before MEDIUM severity."""
        fired = [
            # Governance failure (MEDIUM) + restatement (HIGH)
            "GOV.BOARD.independence",
            "GOV.BOARD.ceo_chair",
            "GOV.BOARD.overboarding",
            "FIN.ACCT.restatement",
            "FIN.ACCT.earnings_manipulation",
        ]
        stories = compose_narrative(store, fired)
        assert len(stories) >= 2
        severities = [s.severity for s in stories]
        # HIGH should come before MEDIUM
        if "HIGH" in severities and "MEDIUM" in severities:
            high_idx = severities.index("HIGH")
            medium_idx = severities.index("MEDIUM")
            assert high_idx < medium_idx

    def test_multiple_narratives_from_one_analysis(
        self, store: KnowledgeStore
    ) -> None:
        """Multiple narratives can activate from same fired checks."""
        fired = [
            # Restatement risk
            "FIN.ACCT.restatement",
            "FIN.ACCT.earnings_manipulation",
            # Insider trading (shares STOCK.INSIDER with restatement)
            "STOCK.INSIDER.cluster_timing",
            "STOCK.INSIDER.notable_activity",
        ]
        stories = compose_narrative(store, fired)
        story_ids = [s.story_id for s in stories]
        assert "restatement_risk" in story_ids
        assert "insider_trading_pattern" in story_ids

    def test_evidence_summary_includes_signal_names(
        self, store: KnowledgeStore
    ) -> None:
        """Evidence summary references fired check names."""
        fired = ["FIN.ACCT.restatement", "FIN.ACCT.auditor"]
        stories = compose_narrative(store, fired)
        restatement = next(
            s for s in stories if s.story_id == "restatement_risk"
        )
        assert "Financial Restatement History" in restatement.evidence_summary
        assert "Auditor Concerns" in restatement.evidence_summary

    def test_checks_sorted_in_story(
        self, store: KnowledgeStore
    ) -> None:
        """Checks within a story are sorted alphabetically."""
        fired = ["FIN.ACCT.restatement", "FIN.ACCT.auditor"]
        stories = compose_narrative(store, fired)
        restatement = next(
            s for s in stories if s.story_id == "restatement_risk"
        )
        assert restatement.checks == sorted(restatement.checks)

    def test_empty_fired_checks(self, store: KnowledgeStore) -> None:
        """Empty fired checks returns empty stories."""
        stories = compose_narrative(store, [])
        assert stories == []

    def test_regulatory_exposure_narrative(
        self, store: KnowledgeStore
    ) -> None:
        """Regulatory exposure activates with SEC checks."""
        fired = ["LIT.REG.sec_active", "LIT.REG.wells_notice"]
        stories = compose_narrative(store, fired)
        story_ids = [s.story_id for s in stories]
        assert "regulatory_exposure" in story_ids

    def test_financial_distress_narrative(
        self, store: KnowledgeStore
    ) -> None:
        """Financial distress activates with debt and liquidity checks."""
        fired = ["FIN.DEBT.covenants", "FIN.LIQ.cash_burn"]
        stories = compose_narrative(store, fired)
        story_ids = [s.story_id for s in stories]
        assert "financial_distress" in story_ids


class TestGetAvailableNarratives:
    """Tests for listing available narrative templates."""

    def test_returns_all_templates(self) -> None:
        """All 7 templates are returned."""
        narratives = get_available_narratives()
        assert len(narratives) == len(NARRATIVE_TEMPLATES)
        assert len(narratives) >= 7

    def test_each_has_required_fields(self) -> None:
        """Each narrative has all required metadata fields."""
        narratives = get_available_narratives()
        required_keys = {
            "story_id",
            "title",
            "description",
            "check_patterns",
            "factors",
            "allegation_types",
            "severity",
            "activation_threshold",
        }
        for narr in narratives:
            assert required_keys.issubset(narr.keys()), (
                f"Missing keys in {narr.get('story_id')}"
            )

    def test_activation_threshold_is_two(self) -> None:
        """All templates have activation threshold of 2."""
        narratives = get_available_narratives()
        for narr in narratives:
            assert narr["activation_threshold"] == 2


class TestSuggestNewNarrative:
    """Tests for narrative suggestions from co-firing data."""

    def test_empty_data_returns_empty(
        self, store: KnowledgeStore
    ) -> None:
        """No co-firing data -> no suggestions."""
        suggestions = suggest_new_narrative(store, [])
        assert suggestions == []

    def test_identifies_cluster_of_three(
        self, store: KnowledgeStore
    ) -> None:
        """Three mutually co-firing checks form a suggestion."""
        co_firing = [
            ("CHK-A", "CHK-B", 0.9),
            ("CHK-A", "CHK-C", 0.85),
            ("CHK-B", "CHK-C", 0.88),
        ]
        suggestions = suggest_new_narrative(store, co_firing)
        assert len(suggestions) >= 1
        first = suggestions[0]
        assert first["cluster_size"] >= 3
        assert "CHK-A" in first["signal_ids"]
        assert "CHK-B" in first["signal_ids"]
        assert "CHK-C" in first["signal_ids"]

    def test_pair_only_no_suggestion(
        self, store: KnowledgeStore
    ) -> None:
        """Two co-firing checks (no cluster of 3+) -> no suggestions."""
        co_firing = [("CHK-A", "CHK-B", 0.95)]
        suggestions = suggest_new_narrative(store, co_firing)
        assert suggestions == []

    def test_suggestion_includes_avg_rate(
        self, store: KnowledgeStore
    ) -> None:
        """Suggestion includes average co-occurrence rate."""
        co_firing = [
            ("CHK-A", "CHK-B", 0.9),
            ("CHK-A", "CHK-C", 0.8),
            ("CHK-B", "CHK-C", 0.7),
        ]
        suggestions = suggest_new_narrative(store, co_firing)
        assert len(suggestions) >= 1
        avg = suggestions[0]["average_co_occurrence_rate"]
        # Average of 0.9, 0.8, 0.7 = 0.8
        assert abs(avg - 0.8) < 0.01

    def test_larger_cluster_sorted_first(
        self, store: KnowledgeStore
    ) -> None:
        """Larger clusters appear before smaller ones."""
        co_firing = [
            # Cluster 1: A-B-C-D (4 nodes)
            ("CHK-A", "CHK-B", 0.9),
            ("CHK-A", "CHK-C", 0.85),
            ("CHK-A", "CHK-D", 0.8),
            ("CHK-B", "CHK-C", 0.88),
            ("CHK-B", "CHK-D", 0.82),
            ("CHK-C", "CHK-D", 0.87),
            # Cluster 2: X-Y-Z (3 nodes, disconnected)
            ("CHK-X", "CHK-Y", 0.95),
            ("CHK-X", "CHK-Z", 0.92),
            ("CHK-Y", "CHK-Z", 0.91),
        ]
        suggestions = suggest_new_narrative(store, co_firing)
        if len(suggestions) >= 2:
            assert suggestions[0]["cluster_size"] >= suggestions[1]["cluster_size"]


class TestNarrativeStoryDataclass:
    """Tests for the NarrativeStory dataclass."""

    def test_construction(self) -> None:
        """NarrativeStory can be constructed with all fields."""
        story = NarrativeStory(
            story_id="test",
            title="Test Story",
            description="A test narrative.",
            checks=["CHK-001", "CHK-002"],
            factors_affected=["F1"],
            allegation_types=["A"],
            severity="HIGH",
            evidence_summary="Test evidence.",
        )
        assert story.story_id == "test"
        assert len(story.checks) == 2
