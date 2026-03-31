"""Earnings guidance beat/miss classification logic.

Split from earnings_guidance.py (Phase 45, 500-line rule).
Contains classification and scoring functions:
- classify_result: BEAT/MISS/MEET classification from estimate vs actual
- compute_consecutive_misses: trailing miss streak counter
- compute_philosophy: guidance philosophy from beat rate
- _consensus_from_mean: analyst consensus label from recommendation mean
"""

from __future__ import annotations

from do_uw.models.market_events import (
    EarningsQuarterRecord,
    EarningsResult,
    GuidancePhilosophy,
)

# Thresholds for guidance philosophy classification.
_CONSERVATIVE_THRESHOLD = 0.75
_AGGRESSIVE_THRESHOLD = 0.50

# Tolerance for MEET classification: within +/- 1% of estimate.
_MEET_TOLERANCE = 0.01


def classify_result(
    estimate: float | None,
    actual: float | None,
) -> tuple[str, float | None]:
    """Classify earnings result as BEAT, MISS, or MEET.

    Returns (result_str, miss_magnitude_pct). miss_magnitude_pct is
    only populated for MISS results and is the magnitude as a percentage
    of the estimate.
    """
    if estimate is None or actual is None:
        return "", None
    if estimate == 0.0:
        # Avoid division by zero -- classify by sign of actual.
        if actual > 0:
            return EarningsResult.BEAT, None
        if actual < 0:
            return EarningsResult.MISS, None
        return EarningsResult.MEET, None

    surprise_pct = (actual - estimate) / abs(estimate)
    if surprise_pct > _MEET_TOLERANCE:
        return EarningsResult.BEAT, None
    if surprise_pct < -_MEET_TOLERANCE:
        miss_magnitude = abs(surprise_pct) * 100.0
        return EarningsResult.MISS, round(miss_magnitude, 2)
    return EarningsResult.MEET, None


def compute_consecutive_misses(records: list[EarningsQuarterRecord]) -> int:
    """Count consecutive misses from most recent quarter backwards."""
    count = 0
    for record in records:
        if record.result == EarningsResult.MISS:
            count += 1
        else:
            break
    return count


def compute_philosophy(beat_rate: float | None) -> str:
    """Classify guidance philosophy from beat rate."""
    if beat_rate is None:
        return GuidancePhilosophy.NO_GUIDANCE
    if beat_rate >= _CONSERVATIVE_THRESHOLD:
        return GuidancePhilosophy.CONSERVATIVE
    if beat_rate < _AGGRESSIVE_THRESHOLD:
        return GuidancePhilosophy.AGGRESSIVE
    return GuidancePhilosophy.MIXED


def _consensus_from_mean(rec_mean: float) -> str:
    """Map recommendation mean score to consensus label.

    yfinance scale: 1=Strong Buy, 2=Buy, 3=Hold, 4=Sell, 5=Strong Sell.
    """
    if rec_mean <= 1.5:
        return "STRONG_BUY"
    if rec_mean <= 2.5:
        return "BUY"
    if rec_mean <= 3.5:
        return "HOLD"
    if rec_mean <= 4.5:
        return "SELL"
    return "STRONG_SELL"


__all__ = [
    "_consensus_from_mean",
    "classify_result",
    "compute_consecutive_misses",
    "compute_philosophy",
]
