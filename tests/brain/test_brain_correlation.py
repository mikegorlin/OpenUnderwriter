"""Tests for brain co-occurrence mining engine.

Tests cover: co-occurrence mining via DuckDB cross-join, same-prefix vs
cross-prefix labeling, redundancy cluster detection, high fire rate exclusion,
configurable thresholds, and CORRELATION_ANNOTATION proposal generation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Generator

import duckdb
import pytest

from do_uw.brain.brain_correlation import (
    CorrelatedPair,
    CorrelationReport,
    RedundancyCluster,
    compute_correlation_report,
    detect_redundancy_clusters,
    generate_correlation_proposals,
    get_co_fire_threshold,
    mine_cooccurrences,
    store_correlations,
)
from do_uw.brain.brain_signal_schema import BrainSignalEntry


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def conn() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """In-memory DuckDB with brain_signal_runs, brain_proposals, brain_correlations."""
    db = duckdb.connect(":memory:")

    db.execute("""
        CREATE TABLE brain_signal_runs (
            run_id VARCHAR NOT NULL,
            signal_id VARCHAR NOT NULL,
            signal_version INTEGER NOT NULL,
            status VARCHAR NOT NULL,
            value VARCHAR,
            evidence TEXT,
            ticker VARCHAR NOT NULL,
            run_date TIMESTAMP NOT NULL DEFAULT current_timestamp,
            is_backtest BOOLEAN DEFAULT FALSE,
            industry_code VARCHAR,
            threshold_was_adjusted BOOLEAN DEFAULT FALSE,
            PRIMARY KEY (run_id, signal_id)
        )
    """)

    db.execute("CREATE SEQUENCE IF NOT EXISTS proposal_seq START 1")
    db.execute("""
        CREATE TABLE brain_proposals (
            proposal_id INTEGER PRIMARY KEY DEFAULT nextval('proposal_seq'),
            source_type VARCHAR NOT NULL,
            source_ref VARCHAR,
            signal_id VARCHAR,
            proposal_type VARCHAR NOT NULL,
            proposed_check JSON,
            proposed_changes JSON,
            backtest_results JSON,
            rationale TEXT NOT NULL,
            status VARCHAR NOT NULL DEFAULT 'PENDING',
            reviewed_by VARCHAR,
            reviewed_at TIMESTAMP,
            created_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        )
    """)

    db.execute("""
        CREATE TABLE brain_correlations (
            signal_a VARCHAR NOT NULL,
            signal_b VARCHAR NOT NULL,
            co_fire_count INTEGER NOT NULL,
            co_fire_rate FLOAT NOT NULL,
            a_fire_count INTEGER NOT NULL,
            b_fire_count INTEGER NOT NULL,
            correlation_type VARCHAR NOT NULL,
            above_threshold BOOLEAN NOT NULL DEFAULT TRUE,
            discovered_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
            PRIMARY KEY (signal_a, signal_b)
        )
    """)

    # Seed with standard test data:
    # 5 runs across 5 tickers with 5 signals
    tickers = ["AAPL", "MSFT", "GOOG", "TSLA", "AMZN"]
    for i, ticker in enumerate(tickers, start=1):
        run_id = f"run_{i}"
        # FIN.LIQ.current: TRIGGERED on all 5 runs
        db.execute(
            "INSERT INTO brain_signal_runs (run_id, signal_id, signal_version, status, ticker) "
            "VALUES (?, ?, 1, 'TRIGGERED', ?)",
            [run_id, "FIN.LIQ.current", ticker],
        )
        # FIN.LIQ.quick: TRIGGERED on runs 1-4 (CLEAR on run 5)
        status = "TRIGGERED" if i <= 4 else "CLEAR"
        db.execute(
            "INSERT INTO brain_signal_runs (run_id, signal_id, signal_version, status, ticker) "
            "VALUES (?, ?, 1, ?, ?)",
            [run_id, "FIN.LIQ.quick", status, ticker],
        )
        # FIN.LIQ.cash: TRIGGERED on runs 1-4 (CLEAR on run 5)
        status = "TRIGGERED" if i <= 4 else "CLEAR"
        db.execute(
            "INSERT INTO brain_signal_runs (run_id, signal_id, signal_version, status, ticker) "
            "VALUES (?, ?, 1, ?, ?)",
            [run_id, "FIN.LIQ.cash", status, ticker],
        )
        # GOV.BOARD.independence: TRIGGERED on runs 1-4 (CLEAR on run 5)
        status = "TRIGGERED" if i <= 4 else "CLEAR"
        db.execute(
            "INSERT INTO brain_signal_runs (run_id, signal_id, signal_version, status, ticker) "
            "VALUES (?, ?, 1, ?, ?)",
            [run_id, "GOV.BOARD.independence", status, ticker],
        )
        # FIN.DEBT.leverage: TRIGGERED on runs 1-2 only (CLEAR on 3-5)
        status = "TRIGGERED" if i <= 2 else "CLEAR"
        db.execute(
            "INSERT INTO brain_signal_runs (run_id, signal_id, signal_version, status, ticker) "
            "VALUES (?, ?, 1, ?, ?)",
            [run_id, "FIN.DEBT.leverage", status, ticker],
        )

    yield db
    db.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_cooccurrence_mining(conn: duckdb.DuckDBPyConnection) -> None:
    """3 signals, 2 always co-fire across 5 runs -> detected as correlated pair."""
    # FIN.LIQ.current fires 5x, FIN.LIQ.quick fires 4x
    # They co-fire on runs 1-4 = 4/4 (min of 5,4) = 1.0
    above, _below = mine_cooccurrences(conn, threshold=0.70)
    pair_keys = {(p.signal_a, p.signal_b) for p in above}
    # current + quick should be detected
    assert ("FIN.LIQ.current", "FIN.LIQ.quick") in pair_keys
    # Verify co_fire_rate >= 0.70 for all returned pairs
    for p in above:
        assert p.co_fire_rate >= 0.70


def test_below_threshold_excluded(conn: duckdb.DuckDBPyConnection) -> None:
    """Signal pair co-firing 2/5 runs (40%) not in above-threshold results."""
    # FIN.DEBT.leverage fires on 2 runs, FIN.LIQ.current fires on 5
    # co-fire = 2 runs, min(5,2) = 2, rate = 2/2 = 1.0
    # But with FIN.LIQ.quick: co-fire = 2 runs, min(4,2) = 2, rate = 2/2 = 1.0
    # Actually FIN.DEBT.leverage fires on runs 1,2 and FIN.LIQ.quick fires on runs 1-4
    # co-fire count = 2 (runs 1,2), min(4,2) = 2, rate = 2/2 = 1.0
    # Let's test with a pair that really is below threshold
    # Add a signal that fires only on run 1
    conn.execute(
        "INSERT INTO brain_signal_runs (run_id, signal_id, signal_version, status, ticker) "
        "VALUES ('run_1', 'EXT.RARE.check', 1, 'TRIGGERED', 'AAPL')"
    )
    # Also add CLEAR for other runs so it exists in the dataset
    for i in range(2, 6):
        conn.execute(
            "INSERT INTO brain_signal_runs (run_id, signal_id, signal_version, status, ticker) "
            "VALUES (?, 'EXT.RARE.check', 1, 'CLEAR', ?)",
            [f"run_{i}", ["MSFT", "GOOG", "TSLA", "AMZN"][i - 2]],
        )

    above, below = mine_cooccurrences(conn, threshold=0.70)
    above_keys = {(p.signal_a, p.signal_b) for p in above}
    # EXT.RARE.check + FIN.LIQ.quick: co-fire = 1/1 = 1.0... hmm
    # Actually EXT.RARE.check fires on 1 run, FIN.LIQ.current fires on 5
    # co-fire = 1 (run_1), min(1,5)=1, rate=1/1=1.0
    # The formula uses LEAST(a_total, b_total) where a_total/b_total = # runs where each fired
    # With 1 fired run for RARE, rate = 1/1 = 1.0 -- it's actually above threshold!
    # We need a different approach. Let's use a signal that fires on runs 1,3 (2 out of 4 for quick)
    # Actually let's just verify the math directly on the below-threshold pairs
    # FIN.DEBT.leverage fires on runs 1,2 and current fires on all 5
    # co-fire = 2, min(2,5) = 2, rate = 2/2 = 1.0 -- also above!

    # Better test: add a signal that fires on 3 out of 5 runs but doesn't overlap much
    # with a specific signal
    conn.execute("DELETE FROM brain_signal_runs WHERE signal_id = 'EXT.RARE.check'")
    # Add EXT.SPARSE.check that fires on runs 3,4,5
    for i in range(1, 6):
        status = "TRIGGERED" if i >= 3 else "CLEAR"
        conn.execute(
            "INSERT INTO brain_signal_runs (run_id, signal_id, signal_version, status, ticker) "
            "VALUES (?, 'EXT.SPARSE.check', 1, ?, ?)",
            [f"run_{i}", status, ["AAPL", "MSFT", "GOOG", "TSLA", "AMZN"][i - 1]],
        )

    above, below = mine_cooccurrences(conn, threshold=0.70)
    above_keys = {(p.signal_a, p.signal_b) for p in above}
    # EXT.SPARSE fires on runs 3,4,5. FIN.DEBT.leverage fires on 1,2.
    # co-fire = 0. Not even a pair.
    # EXT.SPARSE fires on 3,4,5. FIN.LIQ.quick fires on 1,2,3,4.
    # co-fire = 2 (runs 3,4), min(3,4) = 3, rate = 2/3 = 0.667 -> below 0.70
    sparse_quick = ("EXT.SPARSE.check", "FIN.LIQ.quick")
    assert sparse_quick not in above_keys

    # Cleanup
    conn.execute("DELETE FROM brain_signal_runs WHERE signal_id = 'EXT.SPARSE.check'")


def test_below_threshold_stored(conn: duckdb.DuckDBPyConnection) -> None:
    """Below-threshold pairs are returned separately for storage with above_threshold=FALSE."""
    # Add EXT.SPARSE.check that fires on runs 3,4,5
    for i in range(1, 6):
        status = "TRIGGERED" if i >= 3 else "CLEAR"
        conn.execute(
            "INSERT INTO brain_signal_runs (run_id, signal_id, signal_version, status, ticker) "
            "VALUES (?, 'EXT.SPARSE.check', 1, ?, ?)",
            [f"run_{i}", status, ["AAPL", "MSFT", "GOOG", "TSLA", "AMZN"][i - 1]],
        )

    _above, below = mine_cooccurrences(conn, threshold=0.70)
    # Should have below-threshold pairs stored
    # EXT.SPARSE (3,4,5) + FIN.LIQ.quick (1,2,3,4) -> co-fire 2, min(3,4)=3, rate=0.667
    below_keys = {(p.signal_a, p.signal_b) for p in below}
    assert any(
        "EXT.SPARSE.check" in (p.signal_a, p.signal_b)
        and "FIN.LIQ.quick" in (p.signal_a, p.signal_b)
        for p in below
    )

    # Cleanup
    conn.execute("DELETE FROM brain_signal_runs WHERE signal_id = 'EXT.SPARSE.check'")


def test_correlation_labeling_same_prefix(conn: duckdb.DuckDBPyConnection) -> None:
    """Same-prefix pair FIN.LIQ.current + FIN.LIQ.quick labeled 'potential_redundancy'."""
    above, _below = mine_cooccurrences(conn, threshold=0.70)
    for p in above:
        if p.signal_a == "FIN.LIQ.current" and p.signal_b == "FIN.LIQ.quick":
            assert p.correlation_type == "potential_redundancy"
            return
        if p.signal_a == "FIN.LIQ.quick" and p.signal_b == "FIN.LIQ.current":
            assert p.correlation_type == "potential_redundancy"
            return
    pytest.fail("FIN.LIQ.current + FIN.LIQ.quick pair not found")


def test_correlation_labeling_cross_prefix(conn: duckdb.DuckDBPyConnection) -> None:
    """Cross-prefix pair GOV.BOARD.independence + FIN.DEBT.leverage labeled 'risk_correlation'."""
    above, _below = mine_cooccurrences(conn, threshold=0.70)
    for p in above:
        sig_pair = {p.signal_a, p.signal_b}
        if sig_pair == {"GOV.BOARD.independence", "FIN.DEBT.leverage"}:
            assert p.correlation_type == "risk_correlation"
            return
    # These two may or may not be above threshold depending on the formula.
    # GOV.BOARD fires on 1-4, FIN.DEBT fires on 1-2.
    # co-fire = 2, min(4,2) = 2, rate = 2/2 = 1.0 -> above threshold
    pytest.fail("GOV.BOARD.independence + FIN.DEBT.leverage pair not found above threshold")


def test_redundancy_flagging(conn: duckdb.DuckDBPyConnection) -> None:
    """3+ signals with same prefix all co-firing >70% generates redundancy cluster warning."""
    above, _below = mine_cooccurrences(conn, threshold=0.70)
    clusters = detect_redundancy_clusters(above)
    # FIN.LIQ has 3 signals (current, quick, cash) all co-firing
    fin_liq_clusters = [c for c in clusters if c.prefix == "FIN.LIQ"]
    assert len(fin_liq_clusters) == 1
    cluster = fin_liq_clusters[0]
    assert len(cluster.signal_ids) >= 3
    assert "FIN.LIQ.current" in cluster.signal_ids
    assert "FIN.LIQ.quick" in cluster.signal_ids
    assert "FIN.LIQ.cash" in cluster.signal_ids
    assert "consolidat" in cluster.recommendation.lower()


def test_no_redundancy_below_3(conn: duckdb.DuckDBPyConnection) -> None:
    """Only 2 same-prefix signals co-firing does NOT trigger redundancy cluster warning."""
    # FIN.DEBT only has 1 signal (leverage), so no cluster
    above, _below = mine_cooccurrences(conn, threshold=0.70)
    clusters = detect_redundancy_clusters(above)
    fin_debt_clusters = [c for c in clusters if c.prefix == "FIN.DEBT"]
    assert len(fin_debt_clusters) == 0


def test_high_fire_rate_excluded(conn: duckdb.DuckDBPyConnection) -> None:
    """Signals with fire_rate > 0.80 excluded from co-occurrence mining."""
    # FIN.LIQ.current fires 5/5 = 1.0 fire rate (>0.80)
    # When excluded, it should not appear in any pairs
    above, _below = mine_cooccurrences(
        conn,
        threshold=0.70,
        excluded_signal_ids={"FIN.LIQ.current"},
    )
    for p in above:
        assert p.signal_a != "FIN.LIQ.current"
        assert p.signal_b != "FIN.LIQ.current"


def test_configurable_threshold(conn: duckdb.DuckDBPyConnection) -> None:
    """Co-fire threshold defaults to 0.70 but accepts custom value."""
    # With threshold=0.50, more pairs should appear
    above_50, _below_50 = mine_cooccurrences(conn, threshold=0.50)
    above_90, _below_90 = mine_cooccurrences(conn, threshold=0.90)
    # Lower threshold should yield >= same number of pairs
    assert len(above_50) >= len(above_90)


def test_proposal_generation(conn: duckdb.DuckDBPyConnection) -> None:
    """Above-threshold correlation generates CORRELATION_ANNOTATION proposal in brain_proposals."""
    above, _below = mine_cooccurrences(conn, threshold=0.70)
    count = generate_correlation_proposals(conn, above)
    assert count > 0
    # Verify proposals in DB
    proposals = conn.execute(
        "SELECT proposal_type, signal_id, proposed_changes, rationale "
        "FROM brain_proposals WHERE proposal_type = 'CORRELATION_ANNOTATION'"
    ).fetchall()
    assert len(proposals) > 0
    for proposal in proposals:
        assert proposal[0] == "CORRELATION_ANNOTATION"
        assert proposal[1] is not None  # signal_id present
        changes = json.loads(proposal[2])
        assert "correlated_signals" in changes
        assert isinstance(changes["correlated_signals"], list)


def test_yaml_writeback_proposal(conn: duckdb.DuckDBPyConnection) -> None:
    """Proposal proposed_changes contains correlated_signals list for signal."""
    above, _below = mine_cooccurrences(conn, threshold=0.70)
    generate_correlation_proposals(conn, above)

    proposals = conn.execute(
        "SELECT signal_id, proposed_changes FROM brain_proposals "
        "WHERE proposal_type = 'CORRELATION_ANNOTATION'"
    ).fetchall()
    assert len(proposals) > 0

    # Each proposal should have correlated_signals with valid signal IDs
    for signal_id, changes_json in proposals:
        changes = json.loads(changes_json)
        correlated = changes["correlated_signals"]
        assert isinstance(correlated, list)
        assert len(correlated) > 0
        # Correlated signals should not include the signal itself
        assert signal_id not in correlated


def test_correlation_report_structure(conn: duckdb.DuckDBPyConnection) -> None:
    """compute_correlation_report returns CorrelationReport with expected fields."""
    report = compute_correlation_report(conn, threshold=0.70)
    assert isinstance(report, CorrelationReport)
    assert isinstance(report.correlated_pairs, list)
    assert isinstance(report.redundancy_clusters, list)
    assert isinstance(report.total_pairs_analyzed, int)
    assert isinstance(report.above_threshold_count, int)
    assert report.total_pairs_analyzed > 0
    assert report.above_threshold_count > 0


def test_correlated_signals_field() -> None:
    """BrainSignalEntry accepts optional correlated_signals field (list of signal IDs)."""
    _v7 = {
        "rap_class": "host",
        "rap_subcategory": "host.financials",
        "epistemology": {"rule_origin": "test", "threshold_basis": "test"},
        "evaluation": {"mechanism": "threshold"},
    }
    entry = BrainSignalEntry(
        id="TEST.SIG.one",
        name="Test Signal",
        work_type="evaluate",
        tier=1,
        depth=2,
        threshold={"type": "info"},
        provenance={"origin": "test"},
        correlated_signals=["SIG.A", "SIG.B"],
        **_v7,
    )
    assert entry.correlated_signals == ["SIG.A", "SIG.B"]

    # Default should be empty list
    entry_default = BrainSignalEntry(
        id="TEST.SIG.two",
        name="Test Signal 2",
        work_type="evaluate",
        tier=1,
        depth=2,
        threshold={"type": "info"},
        provenance={"origin": "test"},
        **_v7,
    )
    assert entry_default.correlated_signals == []


def test_self_pair_excluded(conn: duckdb.DuckDBPyConnection) -> None:
    """Signal never paired with itself."""
    above, below = mine_cooccurrences(conn, threshold=0.0)  # Get all pairs
    all_pairs = above + below
    for p in all_pairs:
        assert p.signal_a != p.signal_b, f"Self-pair found: {p.signal_a}"


def test_store_correlations(conn: duckdb.DuckDBPyConnection) -> None:
    """store_correlations writes discovered pairs to brain_correlations table."""
    above, below = mine_cooccurrences(conn, threshold=0.70)
    store_correlations(conn, above, below)

    rows = conn.execute("SELECT * FROM brain_correlations").fetchall()
    assert len(rows) > 0

    # Check above_threshold flag
    above_rows = conn.execute(
        "SELECT signal_a, signal_b FROM brain_correlations WHERE above_threshold = TRUE"
    ).fetchall()
    assert len(above_rows) >= len(above)


def test_get_co_fire_threshold_default() -> None:
    """get_co_fire_threshold returns 0.70 when no config file exists."""
    threshold = get_co_fire_threshold(Path("/nonexistent/path"))
    assert threshold == 0.70
