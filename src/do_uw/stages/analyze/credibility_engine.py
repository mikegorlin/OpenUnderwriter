"""Management credibility scoring engine.

Computes a credibility score from historical earnings beat/miss records
(from yfinance EPS estimates vs actuals). Produces a CredibilityScore
model with per-quarter records and aggregate classification.

Credibility levels:
- HIGH: >80% beat rate
- MEDIUM: 50-80% beat rate
- LOW: <50% beat rate
- UNKNOWN: no data available

Usage:
    credibility = compute_credibility_score(state)
    state.forward_looking.credibility = credibility

Phase 117: Forward-Looking Risk Framework
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.forward_looking import (
    CredibilityQuarter,
    CredibilityScore,
)
from do_uw.models.market_events import (
    EarningsGuidanceAnalysis,
    EarningsQuarterRecord,
    EarningsResult,
)
from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)


def _get_earnings_guidance(state: AnalysisState) -> EarningsGuidanceAnalysis | None:
    """Safely retrieve earnings guidance from state."""
    try:
        if state.extracted is not None and state.extracted.market is not None:
            return state.extracted.market.earnings_guidance
    except AttributeError:
        pass
    return None


def _get_estimate_value(quarter: EarningsQuarterRecord) -> float | None:
    """Get the consensus estimate value from a quarter record.

    Uses the midpoint of consensus_eps_low and consensus_eps_high.
    """
    low = quarter.consensus_eps_low
    high = quarter.consensus_eps_high

    low_val: float | None = None
    high_val: float | None = None

    if low is not None:
        low_val = low.value if hasattr(low, "value") else None
    if high is not None:
        high_val = high.value if hasattr(high, "value") else None

    if low_val is not None and high_val is not None:
        return (low_val + high_val) / 2.0
    if low_val is not None:
        return low_val
    if high_val is not None:
        return high_val
    return None


def _get_actual_value(quarter: EarningsQuarterRecord) -> float | None:
    """Get the actual EPS value from a quarter record."""
    if quarter.actual_eps is not None:
        return quarter.actual_eps.value if hasattr(quarter.actual_eps, "value") else None
    return None


def _classify_beat_or_miss(
    estimate: float,
    actual: float,
    result: str,
) -> str:
    """Classify a quarter as BEAT, MISS, or INLINE.

    Uses the pre-computed result field (BEAT/MISS/MEET) from earnings extraction.
    MEET is mapped to INLINE for credibility assessment.
    """
    if result == EarningsResult.MEET:
        return "INLINE"
    if result == EarningsResult.BEAT:
        return "BEAT"
    if result == EarningsResult.MISS:
        return "MISS"

    # Fallback: compute from values if result not set.
    if abs(estimate) > 0:
        pct_diff = abs(actual - estimate) / abs(estimate) * 100
        if pct_diff <= 1.0:
            return "INLINE"
    if actual > estimate:
        return "BEAT"
    if actual < estimate:
        return "MISS"
    return "INLINE"


def _compute_magnitude_pct(estimate: float, actual: float) -> float:
    """Compute magnitude of beat/miss as percentage of estimate.

    Positive = beat (actual > estimate), negative = miss.
    """
    if abs(estimate) < 0.001:
        return 0.0
    return (actual - estimate) / abs(estimate) * 100


def compute_credibility_score(state: AnalysisState) -> CredibilityScore:
    """Compute management credibility score from earnings guidance history.

    Reads state.extracted.market.earnings_guidance, evaluates each quarter
    where both estimate and actual exist, and classifies overall credibility.

    Per CONTEXT.md: yfinance provides EPS estimates vs actuals as primary
    data source. If LLM-extracted company-specific guidance is available
    (from 8-K), prefer that. Falls back to yfinance consensus.

    Args:
        state: Analysis state with extracted earnings guidance.

    Returns:
        CredibilityScore with quarter records and aggregate classification.
    """
    guidance = _get_earnings_guidance(state)
    if guidance is None:
        logger.info("No earnings guidance data available for credibility scoring")
        return CredibilityScore(
            beat_rate_pct=0.0,
            quarters_assessed=0,
            credibility_level="UNKNOWN",
            source="no data",
        )

    quarters = guidance.quarters
    if not quarters:
        logger.info("No quarterly earnings records for credibility scoring")
        return CredibilityScore(
            beat_rate_pct=0.0,
            quarters_assessed=0,
            credibility_level="UNKNOWN",
            source="yfinance (no quarters)",
        )

    # Build credibility quarter records.
    quarter_records: list[CredibilityQuarter] = []
    beats = 0
    total_assessed = 0

    for q in quarters:
        estimate = _get_estimate_value(q)
        actual = _get_actual_value(q)

        if estimate is None or actual is None:
            continue

        beat_or_miss = _classify_beat_or_miss(estimate, actual, q.result)
        magnitude = _compute_magnitude_pct(estimate, actual)

        if beat_or_miss == "BEAT":
            beats += 1
        total_assessed += 1

        quarter_records.append(CredibilityQuarter(
            quarter=q.quarter,
            metric="EPS",
            guided_value=f"${estimate:.2f}",
            actual_value=f"${actual:.2f}",
            beat_or_miss=beat_or_miss,
            magnitude_pct=round(magnitude, 2),
            source="yfinance consensus",
        ))

    if total_assessed == 0:
        return CredibilityScore(
            beat_rate_pct=0.0,
            quarters_assessed=0,
            credibility_level="UNKNOWN",
            quarter_records=quarter_records,
            source="yfinance (no assessable quarters)",
        )

    beat_rate = beats / total_assessed * 100
    # Classification: >80 = HIGH, >=50 = MEDIUM, <50 = LOW
    if beat_rate > 80:
        level = "HIGH"
    elif beat_rate >= 50:
        level = "MEDIUM"
    else:
        level = "LOW"

    logger.info(
        "Credibility score: %.1f%% beat rate (%d/%d quarters) -> %s",
        beat_rate,
        beats,
        total_assessed,
        level,
    )

    return CredibilityScore(
        beat_rate_pct=round(beat_rate, 1),
        quarters_assessed=total_assessed,
        credibility_level=level,
        quarter_records=quarter_records,
        source="yfinance consensus EPS",
    )
