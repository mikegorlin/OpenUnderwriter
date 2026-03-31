"""Check analyzer for cross-ticker calibration metrics.

Computes per-check aggregate metrics (fire rate, skip rate, evidence quality)
across all calibration tickers. Identifies dead checks, always-fire checks,
high-skip checks, and low-evidence checks.

The analyzer consumes a CalibrationReport from the runner and produces
CheckMetrics for each unique check found across all ticker results.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Generic evidence patterns that indicate LOW quality output
_GENERIC_EVIDENCE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^Qualitative check:\s*value=", re.IGNORECASE),
    re.compile(r"^Check value:", re.IGNORECASE),
    re.compile(r"^Data not available", re.IGNORECASE),
    re.compile(r"^Not available", re.IGNORECASE),
    re.compile(r"^N/A$", re.IGNORECASE),
    re.compile(r"^None$", re.IGNORECASE),
    re.compile(r"^No data", re.IGNORECASE),
]

_MIN_SPECIFIC_EVIDENCE_LENGTH = 50
"""Minimum characters for evidence to be considered potentially specific."""

_MIN_NONGENERIC_EVIDENCE_LENGTH = 20
"""Evidence shorter than this is always considered generic."""


class CheckMetrics(BaseModel):
    """Aggregate metrics for a single check across all calibration tickers."""

    model_config = ConfigDict(frozen=False)

    signal_id: str = Field(description="Unique check identifier")
    signal_name: str = Field(description="Human-readable check name from signals.json")
    total_tickers: int = Field(description="Number of tickers where this check was evaluated")
    times_triggered: int = Field(default=0, description="Count of TRIGGERED status")
    times_clear: int = Field(default=0, description="Count of CLEAR status")
    times_skipped: int = Field(default=0, description="Count of SKIPPED status")
    times_info: int = Field(default=0, description="Count of INFO status")
    fire_rate: float = Field(
        default=0.0,
        description="triggered / (total - skipped) -- excludes skipped from denominator",
    )
    skip_rate: float = Field(
        default=0.0,
        description="skipped / total",
    )
    evidence_quality: str = Field(
        default="LOW",
        description="HIGH if >80% evidence is specific, MEDIUM if 50-80%, LOW if <50%",
    )
    threshold_levels: dict[str, int] = Field(
        default_factory=dict,
        description="Count of red/yellow/clear threshold levels across tickers",
    )
    tickers_triggered: list[str] = Field(
        default_factory=list,
        description="Tickers where this check was TRIGGERED",
    )
    tickers_skipped: list[str] = Field(
        default_factory=list,
        description="Tickers where this check was SKIPPED",
    )
    factors: list[str] = Field(
        default_factory=list,
        description="Scoring factors this check maps to",
    )


def _is_generic_evidence(evidence: str) -> bool:
    """Determine if an evidence string is generic (low quality).

    Generic evidence includes short strings, pattern-matched boilerplate,
    and strings that don't reference specific data points.

    Args:
        evidence: The evidence string to evaluate.

    Returns:
        True if evidence is generic/low-quality.
    """
    if not evidence or len(evidence) < _MIN_NONGENERIC_EVIDENCE_LENGTH:
        return True

    for pattern in _GENERIC_EVIDENCE_PATTERNS:
        if pattern.search(evidence):
            return True

    return False


def _compute_evidence_quality(evidence_strings: list[str]) -> str:
    """Compute evidence quality rating from a list of evidence strings.

    HIGH: >80% of evidence strings are specific (>50 chars and not generic)
    MEDIUM: 50-80% are specific
    LOW: <50% are specific

    Args:
        evidence_strings: All evidence strings for a check across tickers.

    Returns:
        Quality rating: "HIGH", "MEDIUM", or "LOW".
    """
    if not evidence_strings:
        return "LOW"

    specific_count = 0
    for ev in evidence_strings:
        is_long_enough = len(ev) >= _MIN_SPECIFIC_EVIDENCE_LENGTH
        is_not_generic = not _is_generic_evidence(ev)
        if is_long_enough and is_not_generic:
            specific_count += 1

    ratio = specific_count / len(evidence_strings)
    if ratio > 0.8:
        return "HIGH"
    if ratio >= 0.5:
        return "MEDIUM"
    return "LOW"


class CheckAnalyzer:
    """Analyzes calibration results to compute per-check aggregate metrics.

    Usage:
        analyzer = CheckAnalyzer()
        metrics = analyzer.analyze(calibration_report)
        dead = analyzer.get_dead_checks()
        always_fire = analyzer.get_always_fire_checks()
    """

    def __init__(self, signal_definitions: list[dict[str, Any]] | None = None) -> None:
        """Initialize with optional check definitions from signals.json.

        Args:
            signal_definitions: List of check dicts from signals.json["signals"].
                If provided, used to look up check names and factors.
                If None, names/factors come from the calibration report data.
        """
        self._check_lookup: dict[str, dict[str, Any]] = {}
        if signal_definitions:
            for signal_def in signal_definitions:
                signal_id = str(signal_def.get("id", ""))
                if signal_id:
                    self._check_lookup[signal_id] = signal_def

        self._metrics: list[CheckMetrics] = []
        self._analyzed = False

    def analyze(self, report: Any) -> list[CheckMetrics]:
        """Compute metrics for all checks found across all tickers.

        The report should be a CalibrationReport (from runner.py) with a
        ``tickers`` dict mapping ticker symbol to CalibrationTickerResult,
        each containing a ``signal_results`` dict of SignalResultSummary.

        Args:
            report: CalibrationReport with per-ticker check results.

        Returns:
            List of CheckMetrics for every unique check found.
        """
        # Accumulate per-check data across all tickers
        signal_data: dict[str, _CheckAccumulator] = {}

        tickers_dict: dict[str, Any] = getattr(report, "tickers", {})
        for ticker, ticker_result in tickers_dict.items():
            signal_results: dict[str, Any] = getattr(ticker_result, "signal_results", {})
            for signal_id, result_summary in signal_results.items():
                if signal_id not in signal_data:
                    signal_data[signal_id] = _CheckAccumulator(signal_id=signal_id)
                acc = signal_data[signal_id]
                acc.add_result(ticker, result_summary)

        # Build CheckMetrics from accumulated data
        metrics: list[CheckMetrics] = []
        for signal_id, acc in sorted(signal_data.items()):
            signal_def = self._check_lookup.get(signal_id, {})
            signal_name = str(signal_def.get("name", acc.best_name or signal_id))
            factors = list(signal_def.get("factors", acc.factors))

            evaluable = acc.total - acc.skipped
            fire_rate = acc.triggered / evaluable if evaluable > 0 else 0.0
            skip_rate = acc.skipped / acc.total if acc.total > 0 else 0.0
            evidence_quality = _compute_evidence_quality(acc.evidence_strings)

            cm = CheckMetrics(
                signal_id=signal_id,
                signal_name=signal_name,
                total_tickers=acc.total,
                times_triggered=acc.triggered,
                times_clear=acc.clear,
                times_skipped=acc.skipped,
                times_info=acc.info,
                fire_rate=fire_rate,
                skip_rate=skip_rate,
                evidence_quality=evidence_quality,
                threshold_levels=dict(acc.threshold_levels),
                tickers_triggered=list(acc.tickers_triggered),
                tickers_skipped=list(acc.tickers_skipped),
                factors=factors,
            )
            metrics.append(cm)

        self._metrics = metrics
        self._analyzed = True
        logger.info("Analyzed %d signals across %d tickers", len(metrics), len(tickers_dict))
        return metrics

    def get_dead_checks(self) -> list[CheckMetrics]:
        """Return checks with 0% fire rate that are not predominantly skipped.

        Dead checks have fire_rate == 0.0 and skip_rate < 0.5, meaning they
        ran on most tickers but never triggered -- the check may be broken
        or the threshold too strict.

        Returns:
            List of dead check metrics.
        """
        self._ensure_analyzed()
        return [m for m in self._metrics if m.fire_rate == 0.0 and m.skip_rate < 0.5]

    def get_always_fire_checks(self) -> list[CheckMetrics]:
        """Return checks with 100% fire rate.

        Always-fire checks trigger on every ticker they evaluate. The
        threshold may be too permissive, or the condition is universally true.

        Returns:
            List of always-fire check metrics.
        """
        self._ensure_analyzed()
        return [m for m in self._metrics if m.fire_rate == 1.0 and m.times_triggered > 0]

    def get_high_skip_checks(self) -> list[CheckMetrics]:
        """Return checks with skip rate above 50%.

        High skip rates indicate systematic data mapping issues -- the
        check's required data is missing for most tickers.

        Returns:
            List of high-skip check metrics.
        """
        self._ensure_analyzed()
        return [m for m in self._metrics if m.skip_rate > 0.5]

    def get_low_evidence_signals(self) -> list[CheckMetrics]:
        """Return checks with LOW evidence quality.

        These checks produce generic evidence strings that don't reference
        specific metrics, filing types, or dates.

        Returns:
            List of low-evidence check metrics.
        """
        self._ensure_analyzed()
        return [m for m in self._metrics if m.evidence_quality == "LOW"]

    def _ensure_analyzed(self) -> None:
        """Raise if analyze() has not been called yet."""
        if not self._analyzed:
            msg = "Call analyze() before querying check metrics"
            raise RuntimeError(msg)


class _CheckAccumulator:
    """Internal accumulator for building per-check metrics across tickers."""

    def __init__(self, signal_id: str) -> None:
        self.signal_id = signal_id
        self.total = 0
        self.triggered = 0
        self.clear = 0
        self.skipped = 0
        self.info = 0
        self.threshold_levels: dict[str, int] = {}
        self.tickers_triggered: list[str] = []
        self.tickers_skipped: list[str] = []
        self.evidence_strings: list[str] = []
        self.factors: list[str] = []
        self.best_name: str | None = None

    def add_result(self, ticker: str, result: Any) -> None:
        """Add a single ticker's result for this check.

        Args:
            ticker: The ticker symbol.
            result: A SignalResultSummary (or compatible object) with
                status, value, threshold_level, evidence, factors attributes.
        """
        self.total += 1

        status = str(getattr(result, "status", "")).upper()
        evidence = str(getattr(result, "evidence", "") or "")
        threshold_level = getattr(result, "threshold_level", None)
        factors = getattr(result, "factors", [])

        # Capture first non-empty factors list found
        if factors and not self.factors:
            self.factors = list(factors)

        if evidence:
            self.evidence_strings.append(evidence)

        if status == "TRIGGERED":
            self.triggered += 1
            self.tickers_triggered.append(ticker)
        elif status == "CLEAR":
            self.clear += 1
        elif status == "SKIPPED":
            self.skipped += 1
            self.tickers_skipped.append(ticker)
        elif status == "INFO":
            self.info += 1

        # Track threshold level distribution
        if threshold_level:
            level_str = str(threshold_level).lower()
            self.threshold_levels[level_str] = self.threshold_levels.get(level_str, 0) + 1


__all__ = ["CheckAnalyzer", "CheckMetrics"]
