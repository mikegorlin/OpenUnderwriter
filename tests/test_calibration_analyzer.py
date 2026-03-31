"""Unit tests for CheckAnalyzer and ImpactRanker.

Tests use synthetic calibration data constructed directly as simple
objects, avoiding dependency on Plan 01's CalibrationReport Pydantic
models which may not exist yet during parallel execution.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from do_uw.calibration.analyzer import CheckAnalyzer, CheckMetrics
from do_uw.calibration.impact_ranker import ImpactRanker

# -- Test fixture helpers --

_AAPL_SCA_EVIDENCE = (
    "Active securities class action filed 2024-01-15 in SDNY, "
    "Case No. 24-cv-1234, alleging Section 10(b) violations"
)
_AAPL_AUDIT_EVIDENCE = (
    "No restatement found in 10-K annual report "
    "for fiscal year 2024, auditor opinion clean"
)
_AAPL_ZSCORE_EVIDENCE = (
    "Altman Z-Score of 1.2 indicates distress zone (<1.8). "
    "Source: 10-K FY2024 Balance Sheet and Income Statement data."
)
_SMCI_SEC_EVIDENCE = (
    "SEC investigation initiated 2024-03-20 per 8-K filing, "
    "DOJ subpoena disclosed in 10-Q Q2 2024"
)
_SMCI_AUDIT_EVIDENCE = (
    "Clean audit history, no restatements in last 5 years "
    "per 10-K annual reports 2020-2024"
)
_SMCI_RATIO_EVIDENCE = (
    "Current ratio of 0.85 below 1.0 threshold. "
    "Debt-to-EBITDA elevated at 4.2x vs sector median 2.1x "
    "per 10-K FY2024."
)
_XOM_DERIV_EVIDENCE = (
    "Derivative lawsuit filed 2023-09-01 in Delaware Chancery "
    "Court regarding climate disclosure obligations"
)
_XOM_AUDITOR_EVIDENCE = (
    "Auditor PricewaterhouseCoopers has served since 1934. "
    "No material weaknesses reported in SOX 404 assessment."
)
_XOM_LEVERAGE_EVIDENCE = (
    "Leverage ratio 3.1x exceeds sector elevated threshold "
    "of 2.5x per 10-K FY2024 financial statements"
)
_XOM_FCF_EVIDENCE = (
    "Negative free cash flow of -$2.1B in Q4 2024 vs positive "
    "$1.8B in Q3. Cash runway analysis shows 14 months "
    "at current burn rate."
)


def _make_signal_result(
    *,
    status: str = "CLEAR",
    value: Any = None,
    threshold_level: str | None = None,
    evidence: str = "",
    factors: list[str] | None = None,
) -> SimpleNamespace:
    """Create a mock SignalResultSummary."""
    return SimpleNamespace(
        status=status,
        value=value,
        threshold_level=threshold_level,
        evidence=evidence,
        factors=factors or [],
    )


def _make_ticker_result(
    signal_results: dict[str, SimpleNamespace],
) -> SimpleNamespace:
    """Create a mock CalibrationTickerResult."""
    return SimpleNamespace(signal_results=signal_results)


def _make_report(
    tickers: dict[str, SimpleNamespace],
) -> SimpleNamespace:
    """Create a mock CalibrationReport."""
    return SimpleNamespace(tickers=tickers)


def _build_synthetic_report() -> SimpleNamespace:
    """Build a synthetic CalibrationReport with 3 tickers and 5 checks.

    Check behavior:
    - CHK.ALWAYS: fires for all 3 tickers (100% fire rate)
    - CHK.NEVER: fires for 0 tickers, all CLEAR (0% fire rate)
    - CHK.SKIP: skipped for 2/3 tickers (high skip rate)
    - CHK.GENERIC: fires with generic evidence (LOW quality)
    - CHK.GOOD: fires with good evidence (HIGH quality)
    """
    tickers = {
        "AAPL": _make_ticker_result({
            "CHK.ALWAYS": _make_signal_result(
                status="TRIGGERED",
                threshold_level="red",
                evidence=_AAPL_SCA_EVIDENCE,
                factors=["F1"],
            ),
            "CHK.NEVER": _make_signal_result(
                status="CLEAR",
                evidence=_AAPL_AUDIT_EVIDENCE,
                factors=["F3"],
            ),
            "CHK.SKIP": _make_signal_result(
                status="SKIPPED",
                evidence="",
                factors=["F8"],
            ),
            "CHK.GENERIC": _make_signal_result(
                status="TRIGGERED",
                threshold_level="yellow",
                evidence="Check value: 2.5",
                factors=["F10"],
            ),
            "CHK.GOOD": _make_signal_result(
                status="TRIGGERED",
                threshold_level="red",
                evidence=_AAPL_ZSCORE_EVIDENCE,
                factors=["F8"],
            ),
        }),
        "SMCI": _make_ticker_result({
            "CHK.ALWAYS": _make_signal_result(
                status="TRIGGERED",
                threshold_level="red",
                evidence=_SMCI_SEC_EVIDENCE,
                factors=["F1"],
            ),
            "CHK.NEVER": _make_signal_result(
                status="CLEAR",
                evidence=_SMCI_AUDIT_EVIDENCE,
                factors=["F3"],
            ),
            "CHK.SKIP": _make_signal_result(
                status="SKIPPED",
                evidence="",
                factors=["F8"],
            ),
            "CHK.GENERIC": _make_signal_result(
                status="TRIGGERED",
                threshold_level="yellow",
                evidence="Qualitative check: value=True",
                factors=["F10"],
            ),
            "CHK.GOOD": _make_signal_result(
                status="TRIGGERED",
                threshold_level="yellow",
                evidence=_SMCI_RATIO_EVIDENCE,
                factors=["F8"],
            ),
        }),
        "XOM": _make_ticker_result({
            "CHK.ALWAYS": _make_signal_result(
                status="TRIGGERED",
                threshold_level="yellow",
                evidence=_XOM_DERIV_EVIDENCE,
                factors=["F1"],
            ),
            "CHK.NEVER": _make_signal_result(
                status="CLEAR",
                evidence=_XOM_AUDITOR_EVIDENCE,
                factors=["F3"],
            ),
            "CHK.SKIP": _make_signal_result(
                status="TRIGGERED",
                threshold_level="yellow",
                evidence=_XOM_LEVERAGE_EVIDENCE,
                factors=["F8"],
            ),
            "CHK.GENERIC": _make_signal_result(
                status="TRIGGERED",
                threshold_level="yellow",
                evidence="N/A",
                factors=["F10"],
            ),
            "CHK.GOOD": _make_signal_result(
                status="TRIGGERED",
                threshold_level="red",
                evidence=_XOM_FCF_EVIDENCE,
                factors=["F8"],
            ),
        }),
    }
    return _make_report(tickers)


# -- CheckAnalyzer tests --


class TestCheckAnalyzer:
    """Tests for CheckAnalyzer with synthetic data."""

    def test_analyze_returns_all_checks(self) -> None:
        """analyze() returns metrics for all 5 unique checks."""
        report = _build_synthetic_report()
        analyzer = CheckAnalyzer()
        metrics = analyzer.analyze(report)
        assert len(metrics) == 5
        signal_ids = {m.signal_id for m in metrics}
        expected = {
            "CHK.ALWAYS", "CHK.NEVER",
            "CHK.SKIP", "CHK.GENERIC", "CHK.GOOD",
        }
        assert signal_ids == expected

    def test_always_fire_check(self) -> None:
        """CHK.ALWAYS has 100% fire rate across all 3 tickers."""
        report = _build_synthetic_report()
        analyzer = CheckAnalyzer()
        metrics = analyzer.analyze(report)
        always = next(
            m for m in metrics if m.signal_id == "CHK.ALWAYS"
        )
        assert always.fire_rate == 1.0
        assert always.times_triggered == 3
        assert always.total_tickers == 3
        assert len(always.tickers_triggered) == 3

    def test_never_fire_check(self) -> None:
        """CHK.NEVER has 0% fire rate (all CLEAR)."""
        report = _build_synthetic_report()
        analyzer = CheckAnalyzer()
        metrics = analyzer.analyze(report)
        never = next(
            m for m in metrics if m.signal_id == "CHK.NEVER"
        )
        assert never.fire_rate == 0.0
        assert never.times_clear == 3
        assert never.skip_rate == 0.0

    def test_high_skip_check(self) -> None:
        """CHK.SKIP is skipped for 2/3 tickers (high skip rate)."""
        report = _build_synthetic_report()
        analyzer = CheckAnalyzer()
        metrics = analyzer.analyze(report)
        skip = next(
            m for m in metrics if m.signal_id == "CHK.SKIP"
        )
        # 2 skipped out of 3 total
        assert skip.times_skipped == 2
        assert skip.skip_rate == pytest.approx(2.0 / 3.0)
        # 1 triggered out of 1 evaluable (3 - 2 = 1)
        assert skip.fire_rate == 1.0

    def test_generic_evidence_check(self) -> None:
        """CHK.GENERIC produces LOW evidence quality."""
        report = _build_synthetic_report()
        analyzer = CheckAnalyzer()
        metrics = analyzer.analyze(report)
        generic = next(
            m for m in metrics if m.signal_id == "CHK.GENERIC"
        )
        assert generic.evidence_quality == "LOW"

    def test_good_evidence_check(self) -> None:
        """CHK.GOOD produces HIGH evidence quality."""
        report = _build_synthetic_report()
        analyzer = CheckAnalyzer()
        metrics = analyzer.analyze(report)
        good = next(
            m for m in metrics if m.signal_id == "CHK.GOOD"
        )
        assert good.evidence_quality == "HIGH"

    def test_threshold_level_tracking(self) -> None:
        """Threshold levels are counted correctly."""
        report = _build_synthetic_report()
        analyzer = CheckAnalyzer()
        metrics = analyzer.analyze(report)
        always = next(
            m for m in metrics if m.signal_id == "CHK.ALWAYS"
        )
        # 2 red, 1 yellow
        assert always.threshold_levels.get("red", 0) == 2
        assert always.threshold_levels.get("yellow", 0) == 1

    def test_get_dead_checks(self) -> None:
        """get_dead_checks() returns the 0% fire rate check."""
        report = _build_synthetic_report()
        analyzer = CheckAnalyzer()
        analyzer.analyze(report)
        dead = analyzer.get_dead_checks()
        dead_ids = {m.signal_id for m in dead}
        assert "CHK.NEVER" in dead_ids
        # CHK.SKIP has high skip rate so NOT in dead checks
        assert "CHK.SKIP" not in dead_ids

    def test_get_always_fire_checks(self) -> None:
        """get_always_fire_checks() returns 100% fire rate checks."""
        report = _build_synthetic_report()
        analyzer = CheckAnalyzer()
        analyzer.analyze(report)
        always = analyzer.get_always_fire_checks()
        always_ids = {m.signal_id for m in always}
        assert "CHK.ALWAYS" in always_ids

    def test_get_low_evidence_signals(self) -> None:
        """get_low_evidence_signals() returns LOW quality checks."""
        report = _build_synthetic_report()
        analyzer = CheckAnalyzer()
        analyzer.analyze(report)
        low = analyzer.get_low_evidence_signals()
        low_ids = {m.signal_id for m in low}
        assert "CHK.GENERIC" in low_ids

    def test_get_high_skip_checks(self) -> None:
        """get_high_skip_checks() returns checks skipped >50%."""
        report = _build_synthetic_report()
        analyzer = CheckAnalyzer()
        analyzer.analyze(report)
        high_skip = analyzer.get_high_skip_checks()
        skip_ids = {m.signal_id for m in high_skip}
        assert "CHK.SKIP" in skip_ids

    def test_analyze_required_before_getters(self) -> None:
        """Calling getter before analyze() raises RuntimeError."""
        analyzer = CheckAnalyzer()
        with pytest.raises(RuntimeError, match="Call analyze"):
            analyzer.get_dead_checks()

    def test_signal_definitions_lookup(self) -> None:
        """Check definitions provide name and factors override."""
        signal_defs: list[dict[str, Any]] = [
            {
                "id": "CHK.ALWAYS",
                "name": "Always Fire Check",
                "factors": ["F1", "F2"],
            },
        ]
        report = _build_synthetic_report()
        analyzer = CheckAnalyzer(signal_definitions=signal_defs)
        metrics = analyzer.analyze(report)
        always = next(
            m for m in metrics if m.signal_id == "CHK.ALWAYS"
        )
        assert always.signal_name == "Always Fire Check"
        assert always.factors == ["F1", "F2"]


# -- ImpactRanker tests --


def _write_scoring_config(path: Path) -> None:
    """Write a minimal scoring.json for testing."""
    config = {
        "factors": {
            "F1_prior_litigation": {
                "factor_id": "F.1",
                "max_points": 20,
            },
            "F2_stock_decline": {
                "factor_id": "F.2",
                "max_points": 15,
            },
            "F3_restatement_audit": {
                "factor_id": "F.3",
                "max_points": 12,
            },
            "F8_financial_distress": {
                "factor_id": "F.8",
                "max_points": 8,
            },
            "F10_officer_stability": {
                "factor_id": "F.10",
                "max_points": 2,
            },
        }
    }
    with path.open("w") as f:
        json.dump(config, f)


class TestImpactRanker:
    """Tests for ImpactRanker with synthetic metrics."""

    @pytest.fixture()
    def scoring_path(self, tmp_path: Path) -> Path:
        """Create temporary scoring.json for tests."""
        path = tmp_path / "scoring.json"
        _write_scoring_config(path)
        return path

    def test_rank_by_impact_score(
        self, scoring_path: Path,
    ) -> None:
        """F1 check ranks higher than F10 despite lower fire rate.

        F1 (20 pts) * 0.5 fire_rate * 3.0 severity = 30.0
        F10 (2 pts) * 1.0 fire_rate * 2.0 severity = 4.0
        """
        ranker = ImpactRanker(scoring_config_path=scoring_path)
        metrics = [
            CheckMetrics(
                signal_id="CHK.F1",
                signal_name="F1 Check",
                total_tickers=10,
                times_triggered=5,
                times_clear=5,
                fire_rate=0.5,
                threshold_levels={"red": 5},
                factors=["F1"],
            ),
            CheckMetrics(
                signal_id="CHK.F10",
                signal_name="F10 Check",
                total_tickers=10,
                times_triggered=10,
                fire_rate=1.0,
                threshold_levels={"yellow": 10},
                factors=["F10"],
            ),
        ]
        ranked = ranker.rank(metrics, top_n=10)
        assert len(ranked) == 2
        assert ranked[0].signal_id == "CHK.F1"
        assert ranked[0].impact_score == pytest.approx(30.0)
        assert ranked[1].signal_id == "CHK.F10"
        assert ranked[1].impact_score == pytest.approx(4.0)

    def test_rank_assigns_1_based_ranks(
        self, scoring_path: Path,
    ) -> None:
        """Ranks are 1-based."""
        ranker = ImpactRanker(scoring_config_path=scoring_path)
        metrics = [
            CheckMetrics(
                signal_id="CHK.A",
                signal_name="A",
                total_tickers=3,
                times_triggered=3,
                fire_rate=1.0,
                threshold_levels={"red": 3},
                factors=["F1"],
            ),
        ]
        ranked = ranker.rank(metrics)
        assert ranked[0].rank == 1

    def test_rank_top_n_limits_results(
        self, scoring_path: Path,
    ) -> None:
        """rank(top_n=2) returns exactly 2 results."""
        ranker = ImpactRanker(scoring_config_path=scoring_path)
        metrics = [
            CheckMetrics(
                signal_id=f"CHK.{i}",
                signal_name=f"Check {i}",
                total_tickers=5,
                times_triggered=i,
                fire_rate=i / 5.0,
                threshold_levels={"red": i},
                factors=["F1"],
            )
            for i in range(1, 6)
        ]
        ranked = ranker.rank(metrics, top_n=2)
        assert len(ranked) == 2

    def test_get_unmapped_checks(
        self, scoring_path: Path,
    ) -> None:
        """get_unmapped_checks() returns checks with empty factors."""
        ranker = ImpactRanker(scoring_config_path=scoring_path)
        metrics = [
            CheckMetrics(
                signal_id="CHK.MAPPED",
                signal_name="Mapped",
                total_tickers=3,
                factors=["F1"],
            ),
            CheckMetrics(
                signal_id="CHK.UNMAPPED",
                signal_name="Unmapped",
                total_tickers=3,
                factors=[],
            ),
        ]
        unmapped = ranker.get_unmapped_checks(metrics)
        assert len(unmapped) == 1
        assert unmapped[0].signal_id == "CHK.UNMAPPED"

    def test_get_factor_distribution(
        self, scoring_path: Path,
    ) -> None:
        """get_factor_distribution() returns correct counts."""
        ranker = ImpactRanker(scoring_config_path=scoring_path)
        metrics = [
            CheckMetrics(
                signal_id="CHK.1", signal_name="1",
                total_tickers=3, factors=["F1"],
            ),
            CheckMetrics(
                signal_id="CHK.2", signal_name="2",
                total_tickers=3, factors=["F1"],
            ),
            CheckMetrics(
                signal_id="CHK.3", signal_name="3",
                total_tickers=3, factors=["F1", "F10"],
            ),
            CheckMetrics(
                signal_id="CHK.4", signal_name="4",
                total_tickers=3, factors=["F10"],
            ),
        ]
        dist = ranker.get_factor_distribution(metrics)
        assert dist["F1"] == 3
        assert dist["F10"] == 2

    def test_zero_impact_for_unmapped(
        self, scoring_path: Path,
    ) -> None:
        """Checks with no factors get impact_score = 0."""
        ranker = ImpactRanker(scoring_config_path=scoring_path)
        metrics = [
            CheckMetrics(
                signal_id="CHK.NOFACTOR",
                signal_name="No Factor",
                total_tickers=5,
                times_triggered=5,
                fire_rate=1.0,
                threshold_levels={"red": 5},
                factors=[],
            ),
        ]
        ranked = ranker.rank(metrics)
        assert ranked[0].impact_score == 0.0

    def test_severity_mixed_levels(
        self, scoring_path: Path,
    ) -> None:
        """Severity averages across red and yellow levels."""
        ranker = ImpactRanker(scoring_config_path=scoring_path)
        metrics = [
            CheckMetrics(
                signal_id="CHK.MIX",
                signal_name="Mixed",
                total_tickers=4,
                times_triggered=4,
                fire_rate=1.0,
                # avg = (3*2 + 2*2)/4 = 2.5
                threshold_levels={"red": 2, "yellow": 2},
                factors=["F1"],
            ),
        ]
        ranked = ranker.rank(metrics)
        # weight=20 * fire_rate=1.0 * severity=2.5 = 50.0
        assert ranked[0].impact_score == pytest.approx(50.0)
        assert ranked[0].severity == pytest.approx(2.5)

    def test_integration_with_analyzer(
        self, scoring_path: Path,
    ) -> None:
        """ImpactRanker works with CheckAnalyzer output."""
        report = _build_synthetic_report()
        analyzer = CheckAnalyzer()
        metrics = analyzer.analyze(report)
        ranker = ImpactRanker(scoring_config_path=scoring_path)
        ranked = ranker.rank(metrics, top_n=5)
        assert len(ranked) == 5
        # All 5 checks should be ranked
        assert ranked[0].rank == 1
        assert ranked[-1].rank == 5
        # Highest-impact check has non-zero score
        assert ranked[0].impact_score > 0
