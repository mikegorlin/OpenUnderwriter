"""XBRL/LLM reconciler -- enforces XBRL-wins precedence for numeric data.

Anti-hallucination guarantee: XBRL for numbers, LLM for words.
All divergences logged for audit trail and data quality monitoring.

Exports:
    reconcile_value: Single-value reconciliation (XBRL vs LLM)
    reconcile_quarterly: Full quarterly reconciliation across periods
    cross_validate_yfinance: Cross-validate XBRL against yfinance data
    ReconciliationReport: Aggregate reconciliation statistics
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.financials import QuarterlyPeriod, QuarterlyStatements, QuarterlyUpdate

logger = logging.getLogger(__name__)

# Divergence threshold -- values within this percentage are considered matching
_DIVERGENCE_THRESHOLD_PCT = 1.0

# Hallucination threshold -- values diverging by more than this ratio are flagged
_HALLUCINATION_THRESHOLD_RATIO = 2.0


@dataclass
class DiscrepancyWarning:
    """Warning for >2x divergence between LLM and XBRL values."""

    concept: str
    period: str
    xbrl_value: float
    llm_value: float
    ratio: float  # llm/xbrl or xbrl/llm (whichever is larger)
    resolution: str  # "XBRL_WINS" always for financials
    message: str


@dataclass
class ReconciliationReport:
    """Aggregate statistics from a reconciliation pass."""

    total_comparisons: int = 0
    divergences: int = 0
    xbrl_wins: int = 0
    llm_fallbacks: int = 0
    messages: list[str] = field(default_factory=lambda: [])
    discrepancy_warnings: list[DiscrepancyWarning] = field(default_factory=lambda: [])


def reconcile_value(
    xbrl_value: SourcedValue[float] | None,
    llm_value: float | None,
    concept: str,
    period: str,
) -> tuple[SourcedValue[float] | None, list[str], list[DiscrepancyWarning]]:
    """Reconcile a single value -- XBRL always wins.

    Returns:
        Tuple of (winning SourcedValue or None, list of divergence messages,
        list of DiscrepancyWarning for >2x divergences).
    """
    messages: list[str] = []
    warnings: list[DiscrepancyWarning] = []

    if xbrl_value is not None and llm_value is not None:
        # XBRL wins -- check for divergence
        pct_diff = _pct_difference(xbrl_value.value, llm_value)
        if pct_diff is not None and abs(pct_diff) > _DIVERGENCE_THRESHOLD_PCT:
            messages.append(
                f"DIVERGENCE: {concept} [{period}] "
                f"XBRL={xbrl_value.value:,.2f} vs LLM={llm_value:,.2f} "
                f"({pct_diff:+.1f}%)"
            )

        # Check for hallucination-level divergence (>2x ratio)
        xv = xbrl_value.value
        if abs(xv) < 1e-10:
            # XBRL is zero but LLM is non-zero -- always flag
            if abs(llm_value) > 1e-10:
                msg = (
                    f"HALLUCINATION_FLAG: {concept} {period}: "
                    f"LLM={llm_value:,.2f} vs XBRL={xv:,.2f} "
                    f"(inf divergence). XBRL value used."
                )
                messages.append(msg)
                warnings.append(DiscrepancyWarning(
                    concept=concept, period=period,
                    xbrl_value=xv, llm_value=llm_value,
                    ratio=float("inf"), resolution="XBRL_WINS",
                    message=msg,
                ))
        elif abs(llm_value) > 1e-10:
            ratio = max(abs(llm_value / xv), abs(xv / llm_value))
            if ratio > _HALLUCINATION_THRESHOLD_RATIO:
                msg = (
                    f"HALLUCINATION_FLAG: {concept} {period}: "
                    f"LLM={llm_value:,.2f} vs XBRL={xv:,.2f} "
                    f"({ratio:.1f}x divergence). XBRL value used."
                )
                messages.append(msg)
                warnings.append(DiscrepancyWarning(
                    concept=concept, period=period,
                    xbrl_value=xv, llm_value=llm_value,
                    ratio=ratio, resolution="XBRL_WINS",
                    message=msg,
                ))

        return xbrl_value, messages, warnings

    if xbrl_value is not None:
        return xbrl_value, messages, warnings

    if llm_value is not None:
        # LLM fallback at MEDIUM confidence
        fallback = SourcedValue(
            value=llm_value,
            source="LLM fallback (no XBRL available)",
            confidence=Confidence.MEDIUM,
            as_of=datetime.now(tz=UTC),
        )
        messages.append(
            f"LLM FALLBACK: {concept} [{period}] "
            f"value={llm_value:,.2f} (XBRL absent)"
        )
        return fallback, messages, warnings

    # Both absent
    return None, messages, warnings


def reconcile_quarterly(
    xbrl_quarters: QuarterlyStatements | None,
    llm_updates: list[QuarterlyUpdate],
) -> ReconciliationReport:
    """Reconcile XBRL quarterly data against LLM-extracted updates.

    Matches periods by fiscal quarter label. For each overlapping period,
    reconciles revenue, net_income, eps.
    """
    report = ReconciliationReport()

    if xbrl_quarters is None or not xbrl_quarters.quarters:
        # Nothing to reconcile -- all LLM values are fallbacks
        for update in llm_updates:
            for concept, llm_val in _llm_update_values(update):
                _, msgs, warns = reconcile_value(None, llm_val, concept, update.quarter)
                report.llm_fallbacks += 1
                report.total_comparisons += 1
                report.messages.extend(msgs)
                report.discrepancy_warnings.extend(warns)
        return report

    # Build lookup: fiscal_label -> QuarterlyPeriod
    xbrl_by_label: dict[str, QuarterlyPeriod] = {
        q.fiscal_label: q for q in xbrl_quarters.quarters
    }

    for update in llm_updates:
        xbrl_q = xbrl_by_label.get(update.quarter)
        if xbrl_q is None:
            # No matching XBRL quarter -- all LLM fallbacks
            for concept, llm_val in _llm_update_values(update):
                _, msgs, warns = reconcile_value(None, llm_val, concept, update.quarter)
                report.llm_fallbacks += 1
                report.total_comparisons += 1
                report.messages.extend(msgs)
                report.discrepancy_warnings.extend(warns)
            continue

        # Reconcile each concept
        concept_pairs = _build_concept_pairs(xbrl_q, update)
        for concept, xbrl_sv, llm_val in concept_pairs:
            result, msgs, warns = reconcile_value(xbrl_sv, llm_val, concept, update.quarter)
            report.total_comparisons += 1
            if result is not None and xbrl_sv is not None:
                report.xbrl_wins += 1
            elif result is not None and xbrl_sv is None:
                report.llm_fallbacks += 1
            report.messages.extend(msgs)
            report.discrepancy_warnings.extend(warns)
            report.divergences += len(msgs) - sum(
                1 for m in msgs if "FALLBACK" in m
            )

    # Reset divergence count to only count actual divergences across all messages
    report.divergences = sum(1 for m in report.messages if "DIVERGENCE" in m)
    return report


def cross_validate_yfinance(
    xbrl_quarters: QuarterlyStatements | None,
    yfinance_data: list[dict[str, object]],
) -> ReconciliationReport:
    """Cross-validate XBRL quarterly data against yfinance.

    Matches periods by date proximity (7-day window).
    Logs discrepancies exceeding 1% threshold.
    """
    report = ReconciliationReport()

    if xbrl_quarters is None or not xbrl_quarters.quarters:
        return report

    # Extract yfinance dates
    yf_dates = [str(d.get("period_end", "")) for d in yfinance_data]

    for quarter in xbrl_quarters.quarters:
        matched_date = _match_period_by_date(quarter.period_end, yf_dates)
        if matched_date is None:
            continue

        # Find matching yfinance record
        yf_record = next(
            (d for d in yfinance_data if str(d.get("period_end", "")) == matched_date),
            None,
        )
        if yf_record is None:
            continue

        # Compare revenue
        xbrl_revenue = quarter.income.get("revenue")
        yf_revenue = _get_yf_value(yf_record, ["Total Revenue", "revenue"])
        if xbrl_revenue is not None and yf_revenue is not None:
            report.total_comparisons += 1
            pct = _pct_difference(xbrl_revenue.value, yf_revenue)
            if pct is not None and abs(pct) > _DIVERGENCE_THRESHOLD_PCT:
                report.divergences += 1
                msg = (
                    f"YF DISCREPANCY: revenue [{quarter.fiscal_label}] "
                    f"XBRL={xbrl_revenue.value:,.2f} vs yfinance={yf_revenue:,.2f} "
                    f"({pct:+.1f}%)"
                )
                report.messages.append(msg)
                logger.warning(msg)

        # Compare net income
        xbrl_ni = quarter.income.get("net_income")
        yf_ni = _get_yf_value(yf_record, ["Net Income", "net_income"])
        if xbrl_ni is not None and yf_ni is not None:
            report.total_comparisons += 1
            pct = _pct_difference(xbrl_ni.value, yf_ni)
            if pct is not None and abs(pct) > _DIVERGENCE_THRESHOLD_PCT:
                report.divergences += 1
                msg = (
                    f"YF DISCREPANCY: net_income [{quarter.fiscal_label}] "
                    f"XBRL={xbrl_ni.value:,.2f} vs yfinance={yf_ni:,.2f} "
                    f"({pct:+.1f}%)"
                )
                report.messages.append(msg)
                logger.warning(msg)

    return report


def _match_period_by_date(
    xbrl_end: str,
    yf_dates: list[str],
    tolerance_days: int = 7,
) -> str | None:
    """Find closest yfinance date within tolerance window."""
    try:
        xbrl_dt = datetime.strptime(xbrl_end, "%Y-%m-%d")
    except ValueError:
        return None

    best_match: str | None = None
    best_delta = timedelta(days=tolerance_days + 1)

    for yf_date_str in yf_dates:
        try:
            yf_dt = datetime.strptime(yf_date_str, "%Y-%m-%d")
        except ValueError:
            continue
        delta = abs(xbrl_dt - yf_dt)
        if delta <= timedelta(days=tolerance_days) and delta < best_delta:
            best_delta = delta
            best_match = yf_date_str

    return best_match


def _pct_difference(base: float, compare: float) -> float | None:
    """Calculate percentage difference relative to base. Returns None if base is zero."""
    if abs(base) < 1e-10:
        return None
    return ((compare - base) / abs(base)) * 100.0


def _llm_update_values(
    update: QuarterlyUpdate,
) -> list[tuple[str, float | None]]:
    """Extract concept/value pairs from an LLM QuarterlyUpdate."""
    pairs: list[tuple[str, float | None]] = []
    if update.revenue is not None:
        pairs.append(("revenue", update.revenue.value))
    if update.net_income is not None:
        pairs.append(("net_income", update.net_income.value))
    if update.eps is not None:
        pairs.append(("eps", update.eps.value))
    return pairs


def _build_concept_pairs(
    xbrl_q: QuarterlyPeriod,
    update: QuarterlyUpdate,
) -> list[tuple[str, SourcedValue[float] | None, float | None]]:
    """Build aligned concept pairs between XBRL quarter and LLM update."""
    pairs: list[tuple[str, SourcedValue[float] | None, float | None]] = []

    # Revenue
    xbrl_rev = xbrl_q.income.get("revenue")
    llm_rev = update.revenue.value if update.revenue else None
    if xbrl_rev is not None or llm_rev is not None:
        pairs.append(("revenue", xbrl_rev, llm_rev))

    # Net income
    xbrl_ni = xbrl_q.income.get("net_income")
    llm_ni = update.net_income.value if update.net_income else None
    if xbrl_ni is not None or llm_ni is not None:
        pairs.append(("net_income", xbrl_ni, llm_ni))

    # EPS
    xbrl_eps = xbrl_q.income.get("eps")
    llm_eps = update.eps.value if update.eps else None
    if xbrl_eps is not None or llm_eps is not None:
        pairs.append(("eps", xbrl_eps, llm_eps))

    return pairs


def _get_yf_value(record: dict[str, object], keys: list[str]) -> float | None:
    """Get numeric value from yfinance record, trying multiple key names."""
    for key in keys:
        val = record.get(key)
        if val is not None:
            try:
                return float(val)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                continue
    return None
