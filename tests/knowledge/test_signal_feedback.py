"""Tests for check feedback loop recording and stats queries.

Validates:
- write_signal_runs inserts records and returns correct count
- get_check_stats computes correct fire_rate and skip_rate
- get_dead_checks returns only never-fired checks
- Multiple runs for the same ticker aggregate correctly
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from do_uw.knowledge.models import CheckRun
from do_uw.knowledge.store import KnowledgeStore


@pytest.fixture
def store() -> KnowledgeStore:
    """In-memory KnowledgeStore for testing."""
    return KnowledgeStore(db_path=None)


def _make_run(
    run_id: str,
    ticker: str,
    signal_id: str,
    status: str,
    *,
    data_status: str = "EVALUATED",
    value: str | None = None,
) -> CheckRun:
    """Helper to create a CheckRun with defaults."""
    return CheckRun(
        run_id=run_id,
        ticker=ticker,
        run_date=datetime.now(UTC),
        signal_id=signal_id,
        status=status,
        value=value,
        data_status=data_status,
    )


class TestWriteCheckRuns:
    """Tests for write_signal_runs batch insert."""

    def test_insert_returns_count(self, store: KnowledgeStore) -> None:
        runs = [
            _make_run("run1", "AAPL", "FIN.LIQ.01", "TRIGGERED"),
            _make_run("run1", "AAPL", "FIN.LIQ.02", "CLEAR"),
            _make_run("run1", "AAPL", "FIN.LIQ.03", "SKIPPED"),
        ]
        count = store.write_signal_runs(runs)
        assert count == 3

    def test_empty_list_returns_zero(self, store: KnowledgeStore) -> None:
        count = store.write_signal_runs([])
        assert count == 0

    def test_multiple_batches_accumulate(
        self, store: KnowledgeStore
    ) -> None:
        batch1 = [
            _make_run("run1", "AAPL", "FIN.LIQ.01", "TRIGGERED"),
        ]
        batch2 = [
            _make_run("run2", "AAPL", "FIN.LIQ.01", "CLEAR"),
        ]
        store.write_signal_runs(batch1)
        store.write_signal_runs(batch2)

        stats = store.get_check_stats()
        assert len(stats) == 1
        assert stats[0]["total_runs"] == 2


class TestGetCheckStats:
    """Tests for get_check_stats aggregation."""

    def test_computes_fire_rate(self, store: KnowledgeStore) -> None:
        runs = [
            _make_run("r1", "AAPL", "CHK.01", "TRIGGERED"),
            _make_run("r2", "MSFT", "CHK.01", "CLEAR"),
            _make_run("r3", "GOOG", "CHK.01", "TRIGGERED"),
            _make_run("r4", "META", "CHK.01", "CLEAR"),
        ]
        store.write_signal_runs(runs)

        stats = store.get_check_stats()
        assert len(stats) == 1
        s = stats[0]
        assert s["signal_id"] == "CHK.01"
        assert s["total_runs"] == 4
        assert s["fired"] == 2
        assert s["clear"] == 2
        assert s["fire_rate"] == pytest.approx(0.5)
        assert s["skip_rate"] == pytest.approx(0.0)

    def test_computes_skip_rate(self, store: KnowledgeStore) -> None:
        runs = [
            _make_run("r1", "AAPL", "CHK.02", "SKIPPED"),
            _make_run("r2", "MSFT", "CHK.02", "SKIPPED"),
            _make_run("r3", "GOOG", "CHK.02", "CLEAR"),
        ]
        store.write_signal_runs(runs)

        stats = store.get_check_stats()
        s = stats[0]
        assert s["skip_rate"] == pytest.approx(2 / 3)
        assert s["fire_rate"] == pytest.approx(0.0)

    def test_filter_by_signal_id(self, store: KnowledgeStore) -> None:
        runs = [
            _make_run("r1", "AAPL", "CHK.01", "TRIGGERED"),
            _make_run("r1", "AAPL", "CHK.02", "CLEAR"),
        ]
        store.write_signal_runs(runs)

        stats = store.get_check_stats(signal_id="CHK.01")
        assert len(stats) == 1
        assert stats[0]["signal_id"] == "CHK.01"

    def test_min_runs_filter(self, store: KnowledgeStore) -> None:
        runs = [
            _make_run("r1", "AAPL", "CHK.01", "TRIGGERED"),
            _make_run("r2", "MSFT", "CHK.01", "CLEAR"),
            _make_run("r1", "AAPL", "CHK.02", "CLEAR"),
        ]
        store.write_signal_runs(runs)

        # CHK.01 has 2 runs, CHK.02 has 1 run
        stats = store.get_check_stats(min_runs=2)
        assert len(stats) == 1
        assert stats[0]["signal_id"] == "CHK.01"

    def test_info_status_counted(self, store: KnowledgeStore) -> None:
        runs = [
            _make_run("r1", "AAPL", "CHK.03", "INFO"),
            _make_run("r2", "MSFT", "CHK.03", "INFO"),
        ]
        store.write_signal_runs(runs)

        stats = store.get_check_stats()
        s = stats[0]
        assert s["info"] == 2
        assert s["total_runs"] == 2
        assert s["fire_rate"] == pytest.approx(0.0)


class TestGetDeadChecks:
    """Tests for get_dead_checks (never-fire detection)."""

    def test_returns_never_fired(self, store: KnowledgeStore) -> None:
        runs = [
            # CHK.01: fires sometimes
            _make_run("r1", "AAPL", "CHK.01", "TRIGGERED"),
            _make_run("r2", "MSFT", "CHK.01", "CLEAR"),
            _make_run("r3", "GOOG", "CHK.01", "CLEAR"),
            # CHK.02: never fires (always clear)
            _make_run("r1", "AAPL", "CHK.02", "CLEAR"),
            _make_run("r2", "MSFT", "CHK.02", "CLEAR"),
            _make_run("r3", "GOOG", "CHK.02", "CLEAR"),
            # CHK.03: always skipped
            _make_run("r1", "AAPL", "CHK.03", "SKIPPED"),
            _make_run("r2", "MSFT", "CHK.03", "SKIPPED"),
            _make_run("r3", "GOOG", "CHK.03", "SKIPPED"),
        ]
        store.write_signal_runs(runs)

        dead = store.get_dead_checks(min_runs=3)
        dead_ids = {d["signal_id"] for d in dead}
        # CHK.02 and CHK.03 never fire
        assert "CHK.02" in dead_ids
        assert "CHK.03" in dead_ids
        # CHK.01 fires -- not dead
        assert "CHK.01" not in dead_ids

    def test_min_runs_excludes_low_count(
        self, store: KnowledgeStore
    ) -> None:
        runs = [
            _make_run("r1", "AAPL", "CHK.01", "CLEAR"),
            _make_run("r2", "MSFT", "CHK.01", "CLEAR"),
        ]
        store.write_signal_runs(runs)

        # min_runs=3 should exclude CHK.01 (only 2 runs)
        dead = store.get_dead_checks(min_runs=3)
        assert len(dead) == 0

    def test_empty_when_all_fire(self, store: KnowledgeStore) -> None:
        runs = [
            _make_run("r1", "AAPL", "CHK.01", "TRIGGERED"),
            _make_run("r2", "MSFT", "CHK.01", "TRIGGERED"),
            _make_run("r3", "GOOG", "CHK.01", "TRIGGERED"),
        ]
        store.write_signal_runs(runs)

        dead = store.get_dead_checks(min_runs=3)
        assert len(dead) == 0


class TestMultiRunAggregation:
    """Tests for correct aggregation across multiple pipeline runs."""

    def test_same_ticker_different_runs(
        self, store: KnowledgeStore
    ) -> None:
        runs = [
            _make_run("AAPL_20260101", "AAPL", "CHK.01", "TRIGGERED"),
            _make_run("AAPL_20260102", "AAPL", "CHK.01", "CLEAR"),
            _make_run("AAPL_20260103", "AAPL", "CHK.01", "TRIGGERED"),
        ]
        store.write_signal_runs(runs)

        stats = store.get_check_stats()
        assert len(stats) == 1
        s = stats[0]
        assert s["total_runs"] == 3
        assert s["fired"] == 2
        assert s["clear"] == 1
        assert s["fire_rate"] == pytest.approx(2 / 3)

    def test_different_tickers_same_check(
        self, store: KnowledgeStore
    ) -> None:
        runs = [
            _make_run("r1", "AAPL", "CHK.01", "TRIGGERED"),
            _make_run("r2", "MSFT", "CHK.01", "CLEAR"),
            _make_run("r3", "GOOG", "CHK.01", "SKIPPED"),
        ]
        store.write_signal_runs(runs)

        stats = store.get_check_stats()
        s = stats[0]
        assert s["total_runs"] == 3
        assert s["fired"] == 1
        assert s["clear"] == 1
        assert s["skipped"] == 1

    def test_many_checks_stats(self, store: KnowledgeStore) -> None:
        """Verify stats work with many checks across many runs."""
        runs = []
        for i in range(10):
            for j in range(5):
                status = ["TRIGGERED", "CLEAR", "SKIPPED", "INFO"][
                    (i + j) % 4
                ]
                runs.append(
                    _make_run(
                        f"run_{i}",
                        "AAPL",
                        f"CHK.{j:02d}",
                        status,
                    )
                )
        store.write_signal_runs(runs)

        stats = store.get_check_stats()
        assert len(stats) == 5
        for s in stats:
            assert s["total_runs"] == 10
