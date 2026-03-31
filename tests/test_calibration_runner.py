"""Tests for calibration runner, config, and CLI wiring."""

from __future__ import annotations

from do_uw.calibration.config import (
    CALIBRATION_TICKERS,
    DEEP_VALIDATION_VERTICALS,
    LIGHT_VALIDATION_VERTICALS,
    get_calibration_tickers,
)
from do_uw.calibration.runner import (
    CalibrationReport,
    CalibrationTickerResult,
    SignalResultSummary,
)


class TestCalibrationConfig:
    """Tests for calibration ticker configuration."""

    def test_returns_12_tickers(self) -> None:
        """get_calibration_tickers() returns all 12 tickers."""
        tickers = get_calibration_tickers()
        assert len(tickers) == 12

    def test_filter_known_outcome(self) -> None:
        """Filtering by 'known_outcome' returns SMCI, PLUG, COIN."""
        tickers = get_calibration_tickers(category="known_outcome")
        symbols = [t["ticker"] for t in tickers]
        assert sorted(symbols) == ["COIN", "PLUG", "SMCI"]

    def test_all_tickers_have_required_fields(self) -> None:
        """Every calibration ticker has ticker, industry, expected_tier, playbook."""
        for t in CALIBRATION_TICKERS:
            assert "ticker" in t
            assert "industry" in t
            assert "expected_tier" in t
            assert "playbook" in t
            assert "category" in t

    def test_deep_validation_has_4_entries(self) -> None:
        """DEEP_VALIDATION_VERTICALS has 4 entries (Tech, Biotech, Energy, Financial)."""
        assert len(DEEP_VALIDATION_VERTICALS) == 4
        assert set(DEEP_VALIDATION_VERTICALS.keys()) == {
            "Tech",
            "Biotech",
            "Energy",
            "Financial",
        }

    def test_light_validation_verticals(self) -> None:
        """LIGHT_VALIDATION_VERTICALS covers CPG, Media, Industrials."""
        assert len(LIGHT_VALIDATION_VERTICALS) == 3
        assert set(LIGHT_VALIDATION_VERTICALS.keys()) == {
            "CPG",
            "Media",
            "Industrials",
        }

    def test_filter_nonexistent_category(self) -> None:
        """Filtering by nonexistent category returns empty list."""
        tickers = get_calibration_tickers(category="nonexistent")
        assert tickers == []


class TestCalibrationModels:
    """Tests for CalibrationTickerResult and CalibrationReport models."""

    def test_ticker_result_construction(self) -> None:
        """CalibrationTickerResult can be constructed with all fields."""
        result = CalibrationTickerResult(
            ticker="AAPL",
            expected_tier="WIN/WANT",
            actual_tier="WIN",
            quality_score=92.0,
            signal_results={
                "BIZ.CLASS.primary": SignalResultSummary(
                    signal_id="BIZ.CLASS.primary",
                    status="INFO",
                    value=3000000000000.0,
                    evidence="Market cap classification",
                    factors=[],
                ),
            },
            patterns_detected=["PATTERN.GROWTH"],
            factor_scores={"F1": 2.0, "F2": 0.0},
            duration_seconds=45.5,
        )
        assert result.ticker == "AAPL"
        assert result.actual_tier == "WIN"
        assert result.quality_score == 92.0
        assert len(result.signal_results) == 1
        assert result.error is None

    def test_ticker_result_with_error(self) -> None:
        """CalibrationTickerResult can represent a failed run."""
        result = CalibrationTickerResult(
            ticker="FAIL",
            expected_tier="WRITE/WATCH",
            error="Pipeline failed: Stage resolve failed",
            duration_seconds=5.0,
        )
        assert result.error is not None
        assert result.actual_tier is None

    def test_report_construction_and_json(self) -> None:
        """CalibrationReport can be constructed and serialized to JSON."""
        result = CalibrationTickerResult(
            ticker="TEST",
            expected_tier="WANT/WRITE",
            actual_tier="WANT",
            quality_score=78.0,
            duration_seconds=30.0,
        )
        report = CalibrationReport(
            tickers={"TEST": result},
            run_date="2026-02-11T12:00:00Z",
            total_duration=30.0,
            errors=[],
        )
        json_str = report.model_dump_json()
        assert "TEST" in json_str
        assert "WANT" in json_str

        # Round-trip: parse back from JSON.
        parsed = CalibrationReport.model_validate_json(json_str)
        assert parsed.tickers["TEST"].quality_score == 78.0


class TestCLIWiring:
    """Tests for CLI sub-app registration."""

    def test_calibrate_help_shows_commands(self) -> None:
        """CLI 'calibrate --help' shows run, report, enrich commands."""
        from typer.testing import CliRunner

        from do_uw.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["calibrate", "--help"])
        assert result.exit_code == 0
        assert "run" in result.output
        assert "report" in result.output
        assert "enrich" in result.output

    def test_calibrate_run_help(self) -> None:
        """CLI 'calibrate run --help' shows expected options."""
        from typer.testing import CliRunner

        from do_uw.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["calibrate", "run", "--help"])
        assert result.exit_code == 0
        assert "--fresh" in result.output
        assert "--no-llm" in result.output
        assert "--top-n" in result.output
