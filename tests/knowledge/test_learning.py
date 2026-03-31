"""Tests for learning infrastructure: effectiveness tracking and analysis.

Tests cover:
- Recording analysis outcomes as notes
- Computing check fire rates
- Identifying co-firing partners
- Detecting redundant check pairs
- Learning summary generation
- Graceful handling of zero runs
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from do_uw.knowledge.learning import (
    AnalysisOutcome,
    SignalEffectiveness,
    find_redundant_pairs,
    get_signal_effectiveness,
    get_learning_summary,
    record_analysis_run,
)
from do_uw.knowledge.store import KnowledgeStore


@pytest.fixture
def store() -> KnowledgeStore:
    """Create an in-memory knowledge store for testing."""
    return KnowledgeStore(db_path=None)


@pytest.fixture
def outcome_a() -> AnalysisOutcome:
    """Analysis outcome for ticker AAPL."""
    return AnalysisOutcome(
        ticker="AAPL",
        run_date=datetime(2025, 6, 1, tzinfo=UTC),
        checks_fired=["CHK-001", "CHK-002", "CHK-003"],
        checks_clear=["CHK-004", "CHK-005"],
        quality_score=75.0,
        tier="WRITE",
    )


@pytest.fixture
def outcome_b() -> AnalysisOutcome:
    """Analysis outcome for ticker MSFT."""
    return AnalysisOutcome(
        ticker="MSFT",
        run_date=datetime(2025, 7, 1, tzinfo=UTC),
        checks_fired=["CHK-001", "CHK-002", "CHK-006"],
        checks_clear=["CHK-003", "CHK-004", "CHK-005"],
        quality_score=82.0,
        tier="WIN",
    )


@pytest.fixture
def outcome_c() -> AnalysisOutcome:
    """Analysis outcome for ticker GOOG."""
    return AnalysisOutcome(
        ticker="GOOG",
        run_date=datetime(2025, 8, 1, tzinfo=UTC),
        checks_fired=["CHK-001", "CHK-003", "CHK-007"],
        checks_clear=["CHK-002", "CHK-004"],
        quality_score=60.0,
        tier="WATCH",
    )


class TestRecordAnalysisRun:
    """Tests for recording analysis run outcomes."""

    def test_record_stores_note(
        self, store: KnowledgeStore, outcome_a: AnalysisOutcome
    ) -> None:
        """Record stores a note with analysis_run tag."""
        record_analysis_run(store, outcome_a)
        # Verify note was stored by searching
        results = store.search_notes("Analysis Run")
        assert len(results) >= 1

    def test_record_multiple_runs(
        self,
        store: KnowledgeStore,
        outcome_a: AnalysisOutcome,
        outcome_b: AnalysisOutcome,
    ) -> None:
        """Multiple runs create separate notes."""
        record_analysis_run(store, outcome_a)
        record_analysis_run(store, outcome_b)
        results = store.search_notes("Analysis Run")
        assert len(results) >= 2

    def test_record_content_is_valid_json(
        self, store: KnowledgeStore, outcome_a: AnalysisOutcome
    ) -> None:
        """Stored content deserializes back to the same data."""
        record_analysis_run(store, outcome_a)
        # Retrieve the effectiveness to verify data was stored correctly
        eff = get_signal_effectiveness(store, "CHK-001")
        assert eff.times_fired == 1
        assert eff.total_runs == 1


class TestGetSignalEffectiveness:
    """Tests for computing check effectiveness metrics."""

    def test_zero_runs_returns_zero_fire_rate(
        self, store: KnowledgeStore
    ) -> None:
        """No analysis runs -> zero fire rate, no error."""
        eff = get_signal_effectiveness(store, "CHK-001")
        assert eff.signal_id == "CHK-001"
        assert eff.total_runs == 0
        assert eff.times_fired == 0
        assert eff.fire_rate == 0.0
        assert eff.co_firing_partners == []
        assert eff.last_fired is None

    def test_fire_rate_single_run(
        self, store: KnowledgeStore, outcome_a: AnalysisOutcome
    ) -> None:
        """Single run where check fires -> fire_rate = 1.0."""
        record_analysis_run(store, outcome_a)
        eff = get_signal_effectiveness(store, "CHK-001")
        assert eff.total_runs == 1
        assert eff.times_fired == 1
        assert eff.fire_rate == 1.0

    def test_fire_rate_partial(
        self,
        store: KnowledgeStore,
        outcome_a: AnalysisOutcome,
        outcome_b: AnalysisOutcome,
        outcome_c: AnalysisOutcome,
    ) -> None:
        """Check fires in 2 of 3 runs -> fire_rate = 2/3."""
        record_analysis_run(store, outcome_a)
        record_analysis_run(store, outcome_b)
        record_analysis_run(store, outcome_c)
        # CHK-003 fires in outcome_a and outcome_c, not outcome_b
        eff = get_signal_effectiveness(store, "CHK-003")
        assert eff.total_runs == 3
        assert eff.times_fired == 2
        assert abs(eff.fire_rate - 2 / 3) < 0.01

    def test_check_never_fires(
        self,
        store: KnowledgeStore,
        outcome_a: AnalysisOutcome,
    ) -> None:
        """Check that never fires has fire_rate = 0.0."""
        record_analysis_run(store, outcome_a)
        eff = get_signal_effectiveness(store, "CHK-999")
        assert eff.total_runs == 1
        assert eff.times_fired == 0
        assert eff.fire_rate == 0.0
        assert eff.last_fired is None

    def test_co_firing_partners_identified(
        self, store: KnowledgeStore, outcome_a: AnalysisOutcome
    ) -> None:
        """Co-firing partners are the other checks that fired in same runs."""
        record_analysis_run(store, outcome_a)
        eff = get_signal_effectiveness(store, "CHK-001")
        partner_ids = [p[0] for p in eff.co_firing_partners]
        assert "CHK-002" in partner_ids
        assert "CHK-003" in partner_ids

    def test_co_firing_rates_computed(
        self,
        store: KnowledgeStore,
        outcome_a: AnalysisOutcome,
        outcome_b: AnalysisOutcome,
        outcome_c: AnalysisOutcome,
    ) -> None:
        """Co-firing rates reflect how often partners co-fire with this check."""
        record_analysis_run(store, outcome_a)
        record_analysis_run(store, outcome_b)
        record_analysis_run(store, outcome_c)
        # CHK-001 fires in all 3 runs
        eff = get_signal_effectiveness(store, "CHK-001")
        assert eff.times_fired == 3
        # CHK-002 co-fires in runs a and b (2/3 of CHK-001's fires)
        partner_dict = dict(eff.co_firing_partners)
        assert abs(partner_dict.get("CHK-002", 0) - 2 / 3) < 0.01
        # CHK-003 co-fires in runs a and c (2/3 of CHK-001's fires)
        assert abs(partner_dict.get("CHK-003", 0) - 2 / 3) < 0.01

    def test_co_firing_sorted_descending(
        self,
        store: KnowledgeStore,
        outcome_a: AnalysisOutcome,
        outcome_b: AnalysisOutcome,
    ) -> None:
        """Co-firing partners are sorted by rate descending."""
        record_analysis_run(store, outcome_a)
        record_analysis_run(store, outcome_b)
        eff = get_signal_effectiveness(store, "CHK-001")
        rates = [p[1] for p in eff.co_firing_partners]
        assert rates == sorted(rates, reverse=True)

    def test_last_fired_tracks_most_recent(
        self,
        store: KnowledgeStore,
        outcome_a: AnalysisOutcome,
        outcome_c: AnalysisOutcome,
    ) -> None:
        """last_fired reflects the most recent run where check fired."""
        record_analysis_run(store, outcome_a)
        record_analysis_run(store, outcome_c)
        eff = get_signal_effectiveness(store, "CHK-001")
        assert eff.last_fired is not None
        # outcome_c has later date (2025-08-01) than outcome_a (2025-06-01)
        assert eff.last_fired.year == 2025
        assert eff.last_fired.month == 8


class TestFindRedundantPairs:
    """Tests for redundancy detection via co-occurrence analysis."""

    def test_no_runs_returns_empty(self, store: KnowledgeStore) -> None:
        """No analysis runs -> no redundant pairs."""
        result = find_redundant_pairs(store)
        assert result == []

    def test_perfectly_redundant_pair(
        self, store: KnowledgeStore
    ) -> None:
        """Checks that always fire together have co-occurrence 1.0."""
        # Create runs where CHK-A and CHK-B always co-fire
        for i in range(5):
            outcome = AnalysisOutcome(
                ticker=f"T{i}",
                run_date=datetime(2025, 1, i + 1, tzinfo=UTC),
                checks_fired=["CHK-A", "CHK-B"],
                checks_clear=["CHK-C"],
                quality_score=70.0,
                tier="WRITE",
            )
            record_analysis_run(store, outcome)
        pairs = find_redundant_pairs(store, threshold=0.85)
        assert len(pairs) >= 1
        # The pair CHK-A, CHK-B should be found
        pair_checks = [(a, b) for a, b, _ in pairs]
        assert ("CHK-A", "CHK-B") in pair_checks
        # Co-occurrence should be 1.0
        for a, b, rate in pairs:
            if a == "CHK-A" and b == "CHK-B":
                assert rate == 1.0

    def test_below_threshold_excluded(
        self, store: KnowledgeStore
    ) -> None:
        """Pairs below threshold are not returned."""
        # Run 1: A and B fire together
        record_analysis_run(
            store,
            AnalysisOutcome(
                ticker="T1",
                run_date=datetime(2025, 1, 1, tzinfo=UTC),
                checks_fired=["CHK-A", "CHK-B"],
                checks_clear=[],
                quality_score=70.0,
                tier="WRITE",
            ),
        )
        # Runs 2-4: Only A fires
        for i in range(2, 5):
            record_analysis_run(
                store,
                AnalysisOutcome(
                    ticker=f"T{i}",
                    run_date=datetime(2025, 1, i, tzinfo=UTC),
                    checks_fired=["CHK-A"],
                    checks_clear=["CHK-B"],
                    quality_score=70.0,
                    tier="WRITE",
                ),
            )
        # Jaccard: 1 / 4 = 0.25, below default 0.85
        pairs = find_redundant_pairs(store, threshold=0.85)
        assert len(pairs) == 0

    def test_threshold_boundary(self, store: KnowledgeStore) -> None:
        """Pairs exactly at threshold are included."""
        # Need Jaccard >= 0.5 with threshold=0.5
        # 2 runs: both have A, one has B -> Jaccard = 1/2 = 0.5
        record_analysis_run(
            store,
            AnalysisOutcome(
                ticker="T1",
                run_date=datetime(2025, 1, 1, tzinfo=UTC),
                checks_fired=["CHK-A", "CHK-B"],
                checks_clear=[],
                quality_score=70.0,
                tier="WRITE",
            ),
        )
        record_analysis_run(
            store,
            AnalysisOutcome(
                ticker="T2",
                run_date=datetime(2025, 1, 2, tzinfo=UTC),
                checks_fired=["CHK-A"],
                checks_clear=["CHK-B"],
                quality_score=70.0,
                tier="WRITE",
            ),
        )
        pairs = find_redundant_pairs(store, threshold=0.5)
        assert len(pairs) == 1
        assert pairs[0][2] == 0.5

    def test_sorted_by_rate_descending(
        self, store: KnowledgeStore
    ) -> None:
        """Pairs are sorted by co-occurrence rate, highest first."""
        # Create runs with varying co-occurrence
        for i in range(10):
            fired = ["CHK-A", "CHK-B"]
            if i < 8:
                fired.append("CHK-C")  # C co-fires with A in 8/10
            record_analysis_run(
                store,
                AnalysisOutcome(
                    ticker=f"T{i}",
                    run_date=datetime(2025, 1, i + 1, tzinfo=UTC),
                    checks_fired=fired,
                    checks_clear=[],
                    quality_score=70.0,
                    tier="WRITE",
                ),
            )
        pairs = find_redundant_pairs(store, threshold=0.0)
        rates = [r for _, _, r in pairs]
        assert rates == sorted(rates, reverse=True)


class TestGetLearningSummary:
    """Tests for learning summary generation."""

    def test_empty_summary(self, store: KnowledgeStore) -> None:
        """No runs -> zeroed summary."""
        summary = get_learning_summary(store)
        assert summary["total_runs"] == 0
        assert summary["top_fired_checks"] == []
        assert summary["top_redundant_pairs"] == []
        assert summary["average_quality_score"] == 0.0
        assert summary["tier_distribution"] == {}

    def test_summary_with_multiple_runs(
        self,
        store: KnowledgeStore,
        outcome_a: AnalysisOutcome,
        outcome_b: AnalysisOutcome,
        outcome_c: AnalysisOutcome,
    ) -> None:
        """Summary with 3 runs reflects correct aggregates."""
        record_analysis_run(store, outcome_a)
        record_analysis_run(store, outcome_b)
        record_analysis_run(store, outcome_c)

        summary = get_learning_summary(store)
        assert summary["total_runs"] == 3

        # Average quality: (75 + 82 + 60) / 3 = 72.33...
        assert abs(summary["average_quality_score"] - 72.333) < 0.01

        # Tier distribution
        tiers = summary["tier_distribution"]
        assert tiers["WRITE"] == 1
        assert tiers["WIN"] == 1
        assert tiers["WATCH"] == 1

    def test_top_fired_checks_ordered(
        self,
        store: KnowledgeStore,
        outcome_a: AnalysisOutcome,
        outcome_b: AnalysisOutcome,
        outcome_c: AnalysisOutcome,
    ) -> None:
        """Top fired checks are ordered by times_fired descending."""
        record_analysis_run(store, outcome_a)
        record_analysis_run(store, outcome_b)
        record_analysis_run(store, outcome_c)

        summary = get_learning_summary(store)
        top = summary["top_fired_checks"]
        assert len(top) > 0
        # CHK-001 fires in all 3 runs, should be first
        assert top[0]["signal_id"] == "CHK-001"
        assert top[0]["times_fired"] == 3

    def test_summary_includes_redundant_pairs(
        self, store: KnowledgeStore
    ) -> None:
        """Summary includes top redundant pairs."""
        for i in range(5):
            record_analysis_run(
                store,
                AnalysisOutcome(
                    ticker=f"T{i}",
                    run_date=datetime(2025, 1, i + 1, tzinfo=UTC),
                    checks_fired=["CHK-A", "CHK-B"],
                    checks_clear=[],
                    quality_score=70.0,
                    tier="WRITE",
                ),
            )
        summary = get_learning_summary(store)
        assert len(summary["top_redundant_pairs"]) >= 1
        first_pair = summary["top_redundant_pairs"][0]
        assert first_pair["co_occurrence_rate"] == 1.0


class TestSignalEffectivenessDataclass:
    """Tests for the SignalEffectiveness dataclass."""

    def test_construction(self) -> None:
        """SignalEffectiveness can be constructed with all fields."""
        eff = SignalEffectiveness(
            signal_id="CHK-001",
            signal_name="Test Check",
            total_runs=10,
            times_fired=5,
            fire_rate=0.5,
            co_firing_partners=[("CHK-002", 0.8)],
            last_fired=datetime(2025, 6, 1, tzinfo=UTC),
        )
        assert eff.fire_rate == 0.5
        assert len(eff.co_firing_partners) == 1


class TestAnalysisOutcomeDataclass:
    """Tests for the AnalysisOutcome dataclass."""

    def test_construction(self) -> None:
        """AnalysisOutcome can be constructed with all fields."""
        outcome = AnalysisOutcome(
            ticker="AAPL",
            run_date=datetime(2025, 6, 1, tzinfo=UTC),
            checks_fired=["CHK-001"],
            checks_clear=["CHK-002"],
            quality_score=75.0,
            tier="WRITE",
        )
        assert outcome.ticker == "AAPL"
        assert len(outcome.checks_fired) == 1
