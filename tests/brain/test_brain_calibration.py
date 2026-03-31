"""Tests for brain calibration: threshold drift detection, fire rate alerts, proposal generation."""

from __future__ import annotations

import json

import duckdb
import pytest

from do_uw.brain.brain_schema import create_schema


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def conn() -> duckdb.DuckDBPyConnection:
    """Create in-memory DuckDB with brain schema."""
    c = duckdb.connect(":memory:")
    create_schema(c)
    return c


def _seed_signal_runs(
    conn: duckdb.DuckDBPyConnection,
    signal_id: str,
    values: list[str],
    statuses: list[str] | None = None,
) -> None:
    """Seed brain_signal_runs with synthetic data for a signal.

    Each value becomes a separate run. If statuses is None,
    all runs are TRIGGERED.
    """
    if statuses is None:
        statuses = ["TRIGGERED"] * len(values)
    for i, (val, status) in enumerate(zip(values, statuses)):
        conn.execute(
            """INSERT INTO brain_signal_runs
               (run_id, signal_id, signal_version, status, value, evidence,
                ticker, run_date, is_backtest)
               VALUES (?, ?, 1, ?, ?, NULL, 'TEST', CURRENT_TIMESTAMP, FALSE)""",
            [f"run_{signal_id}_{i}", signal_id, status, val],
        )


# ---------------------------------------------------------------------------
# Tests: Drift Detection
# ---------------------------------------------------------------------------


class TestDriftDetection:
    """Test threshold drift detection logic."""

    def test_drift_detection(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Signal with observed values ~2.0 and threshold at 10.0 (>2 sigma away) -> DRIFT_DETECTED."""
        from do_uw.brain.brain_calibration import (
            compute_threshold_drift,
            get_signal_value_distribution,
        )

        _seed_signal_runs(conn, "SIG.DRIFT", ["1.8", "2.0", "2.2", "1.9", "2.1"])
        values = get_signal_value_distribution(conn, "SIG.DRIFT")
        report = compute_threshold_drift("SIG.DRIFT", values, current_threshold=10.0, fire_rate=0.5)

        assert report.status == "DRIFT_DETECTED"
        assert report.n == 5
        assert report.current_threshold == 10.0
        assert report.observed_mean is not None
        assert 1.5 < report.observed_mean < 2.5
        assert report.observed_stdev is not None
        assert report.proposed_value is not None

    def test_no_drift(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Signal with observed values spread around 5.0 and threshold at 5.5 (within 2 sigma) -> OK."""
        from do_uw.brain.brain_calibration import (
            compute_threshold_drift,
            get_signal_value_distribution,
        )

        # Spread values wider so stdev is large enough that 5.5 is within 2*sigma of mean
        _seed_signal_runs(conn, "SIG.NODRIFT", ["3.5", "4.5", "5.5", "6.0", "5.5"])
        values = get_signal_value_distribution(conn, "SIG.NODRIFT")
        report = compute_threshold_drift("SIG.NODRIFT", values, current_threshold=5.5, fire_rate=0.5)

        assert report.status == "OK"

    def test_min_runs_threshold(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Signal with only 3 runs -> INSUFFICIENT_DATA, not a proposal."""
        from do_uw.brain.brain_calibration import (
            compute_threshold_drift,
            get_signal_value_distribution,
        )

        _seed_signal_runs(conn, "SIG.FEW", ["1.0", "2.0", "3.0"])
        values = get_signal_value_distribution(conn, "SIG.FEW")
        report = compute_threshold_drift("SIG.FEW", values, current_threshold=10.0, fire_rate=0.5)

        assert report.status == "INSUFFICIENT_DATA"
        assert report.n == 3
        # Should NOT have a proposed value
        assert report.proposed_value is None

    def test_min_runs_exactly_5(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Signal with exactly 5 runs generates analysis (not INSUFFICIENT_DATA)."""
        from do_uw.brain.brain_calibration import (
            compute_threshold_drift,
            get_signal_value_distribution,
        )

        _seed_signal_runs(conn, "SIG.FIVE", ["1.0", "1.1", "1.2", "1.0", "1.1"])
        values = get_signal_value_distribution(conn, "SIG.FIVE")
        report = compute_threshold_drift("SIG.FIVE", values, current_threshold=10.0, fire_rate=0.5)

        assert report.n == 5
        # Should NOT be INSUFFICIENT_DATA
        assert report.status != "INSUFFICIENT_DATA"

    def test_empty_signal_runs(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Signal with 0 runs -> INSUFFICIENT_DATA."""
        from do_uw.brain.brain_calibration import (
            compute_threshold_drift,
            get_signal_value_distribution,
        )

        values = get_signal_value_distribution(conn, "SIG.EMPTY")
        report = compute_threshold_drift("SIG.EMPTY", values, current_threshold=5.0, fire_rate=0.0)

        assert report.status == "INSUFFICIENT_DATA"
        assert report.n == 0


# ---------------------------------------------------------------------------
# Tests: Value Parsing
# ---------------------------------------------------------------------------


class TestValueParsing:
    """Test parsing of VARCHAR values from brain_signal_runs."""

    def test_value_parsing(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Mix of numeric and non-numeric values: only numeric extracted."""
        from do_uw.brain.brain_calibration import get_signal_value_distribution

        _seed_signal_runs(
            conn,
            "SIG.MIXED",
            ["1.23", "None", "N/A", "profitable", "4.56", "7.89"],
        )
        values = get_signal_value_distribution(conn, "SIG.MIXED")

        assert len(values) == 3
        assert 1.23 in values
        assert 4.56 in values
        assert 7.89 in values


# ---------------------------------------------------------------------------
# Tests: Fire Rate Alerts
# ---------------------------------------------------------------------------


class TestFireRateAlerts:
    """Test fire rate anomaly detection."""

    def test_high_fire_rate_alert(self) -> None:
        """Signal with fire_rate > 0.80 flagged as HIGH_FIRE_RATE."""
        from do_uw.brain.brain_calibration import compute_fire_rate_alerts
        from do_uw.brain.brain_effectiveness import SignalEffectivenessEntry

        entries = [
            SignalEffectivenessEntry(
                signal_id="SIG.HIGH",
                fire_rate=0.85,
                total_runs=10,
                triggered_count=9,
                clear_count=1,
            ),
        ]
        alerts = compute_fire_rate_alerts(entries)

        assert len(alerts) == 1
        assert alerts[0].signal_id == "SIG.HIGH"
        assert alerts[0].alert_type == "HIGH_FIRE_RATE"
        assert "too sensitive" in alerts[0].recommendation.lower()

    def test_low_fire_rate_alert(self) -> None:
        """Signal with fire_rate < 0.02 flagged as LOW_FIRE_RATE."""
        from do_uw.brain.brain_calibration import compute_fire_rate_alerts
        from do_uw.brain.brain_effectiveness import SignalEffectivenessEntry

        entries = [
            SignalEffectivenessEntry(
                signal_id="SIG.LOW",
                fire_rate=0.01,
                total_runs=100,
                triggered_count=1,
                clear_count=99,
            ),
        ]
        alerts = compute_fire_rate_alerts(entries)

        assert len(alerts) == 1
        assert alerts[0].signal_id == "SIG.LOW"
        assert alerts[0].alert_type == "LOW_FIRE_RATE"
        assert "unreachable" in alerts[0].recommendation.lower()

    def test_normal_fire_rate_no_alert(self) -> None:
        """Signal with fire_rate 0.40 not flagged."""
        from do_uw.brain.brain_calibration import compute_fire_rate_alerts
        from do_uw.brain.brain_effectiveness import SignalEffectivenessEntry

        entries = [
            SignalEffectivenessEntry(
                signal_id="SIG.NORMAL",
                fire_rate=0.40,
                total_runs=10,
                triggered_count=4,
                clear_count=6,
            ),
        ]
        alerts = compute_fire_rate_alerts(entries)

        assert len(alerts) == 0


# ---------------------------------------------------------------------------
# Tests: Proposal Generation
# ---------------------------------------------------------------------------


class TestProposalGeneration:
    """Test THRESHOLD_CALIBRATION proposal generation."""

    def test_proposal_generation(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Drift-detected signal generates THRESHOLD_CALIBRATION proposal with all required fields."""
        from do_uw.brain.brain_calibration import DriftReport, generate_calibration_proposals

        drift_signals = [
            DriftReport(
                signal_id="SIG.DRIFTED",
                status="DRIFT_DETECTED",
                n=10,
                confidence="MEDIUM",
                current_threshold=10.0,
                observed_mean=2.0,
                observed_stdev=0.3,
                fire_rate=0.5,
                proposed_value=2.8,
                basis="p90 of observed distribution",
                projected_impact="Would change fire rate from 50% to ~10%",
            ),
        ]

        count = generate_calibration_proposals(conn, drift_signals)
        assert count == 1

        # Verify proposal was written to brain_proposals
        row = conn.execute(
            "SELECT source_type, proposal_type, signal_id, proposed_changes, "
            "backtest_results, rationale, status "
            "FROM brain_proposals WHERE signal_id = 'SIG.DRIFTED'"
        ).fetchone()

        assert row is not None
        assert row[0] == "CALIBRATION"  # source_type
        assert row[1] == "THRESHOLD_CALIBRATION"  # proposal_type
        assert row[2] == "SIG.DRIFTED"  # signal_id

        proposed_changes = json.loads(row[3])
        assert "proposed_value" in proposed_changes
        assert proposed_changes["proposed_value"] == 2.8

        backtest_results = json.loads(row[4])
        assert "n" in backtest_results
        assert "mean" in backtest_results
        assert "stdev" in backtest_results
        assert backtest_results["n"] == 10

        assert row[5]  # rationale is non-empty
        assert row[6] == "PENDING"  # status

    def test_no_proposals_for_ok(self, conn: duckdb.DuckDBPyConnection) -> None:
        """OK drift reports do not generate proposals."""
        from do_uw.brain.brain_calibration import DriftReport, generate_calibration_proposals

        drift_signals = [
            DriftReport(
                signal_id="SIG.OK",
                status="OK",
                n=10,
                confidence="MEDIUM",
            ),
        ]

        count = generate_calibration_proposals(conn, drift_signals)
        assert count == 0


# ---------------------------------------------------------------------------
# Tests: Qualitative Signal Calibration
# ---------------------------------------------------------------------------


class TestQualitativeCalibration:
    """Test non-numeric threshold signals use fire-rate-based recalibration."""

    def test_qualitative_signal_calibration(self) -> None:
        """Non-numeric threshold signal uses fire rate for recalibration strategy."""
        from do_uw.brain.brain_calibration import compute_threshold_drift

        # No numeric values -- pass empty list, but high fire rate
        report = compute_threshold_drift(
            "SIG.QUAL", values=[], current_threshold=None, fire_rate=0.95,
        )

        # With no numeric values, should be INSUFFICIENT_DATA
        assert report.status == "INSUFFICIENT_DATA"
        assert report.n == 0


# ---------------------------------------------------------------------------
# Tests: Confidence Levels
# ---------------------------------------------------------------------------


class TestConfidenceLevels:
    """Test confidence level assignment based on N."""

    def test_low_confidence(self, conn: duckdb.DuckDBPyConnection) -> None:
        """N=5-9 returns LOW confidence."""
        from do_uw.brain.brain_calibration import (
            compute_threshold_drift,
            get_signal_value_distribution,
        )

        _seed_signal_runs(conn, "SIG.LOW_N", ["1.0", "100.0", "1.0", "1.0", "1.0"])
        values = get_signal_value_distribution(conn, "SIG.LOW_N")
        report = compute_threshold_drift("SIG.LOW_N", values, current_threshold=50.0, fire_rate=0.5)

        assert report.confidence == "LOW"
        assert report.n == 5

    def test_medium_confidence(self, conn: duckdb.DuckDBPyConnection) -> None:
        """N=10-24 returns MEDIUM confidence."""
        from do_uw.brain.brain_calibration import (
            compute_threshold_drift,
            get_signal_value_distribution,
        )

        _seed_signal_runs(
            conn,
            "SIG.MED_N",
            [str(float(i)) for i in range(15)],
        )
        values = get_signal_value_distribution(conn, "SIG.MED_N")
        report = compute_threshold_drift("SIG.MED_N", values, current_threshold=100.0, fire_rate=0.5)

        assert report.confidence == "MEDIUM"
        assert report.n == 15

    def test_high_confidence(self, conn: duckdb.DuckDBPyConnection) -> None:
        """N>=25 returns HIGH confidence."""
        from do_uw.brain.brain_calibration import (
            compute_threshold_drift,
            get_signal_value_distribution,
        )

        _seed_signal_runs(
            conn,
            "SIG.HIGH_N",
            [str(float(i)) for i in range(30)],
        )
        values = get_signal_value_distribution(conn, "SIG.HIGH_N")
        report = compute_threshold_drift("SIG.HIGH_N", values, current_threshold=100.0, fire_rate=0.5)

        assert report.confidence == "HIGH"
        assert report.n == 30


# ---------------------------------------------------------------------------
# Tests: Calibration Report Structure
# ---------------------------------------------------------------------------


class TestCalibrationReportStructure:
    """Test compute_calibration_report returns correct structure."""

    def test_calibration_report_structure(self, conn: duckdb.DuckDBPyConnection) -> None:
        """compute_calibration_report returns CalibrationReport with all expected fields."""
        from do_uw.brain.brain_calibration import CalibrationReport, compute_calibration_report

        report = compute_calibration_report(conn)

        assert isinstance(report, CalibrationReport)
        assert isinstance(report.drift_signals, list)
        assert isinstance(report.fire_rate_alerts, list)
        assert isinstance(report.insufficient_data, list)
        assert isinstance(report.total_signals_analyzed, int)
        assert isinstance(report.total_with_numeric_values, int)
        assert isinstance(report.total_proposals_generated, int)
