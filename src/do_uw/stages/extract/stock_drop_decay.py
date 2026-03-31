"""Time-decay weighting for stock drop events.

Applies exponential decay with 180-day half-life so recent drops
carry more weight than older ones for D&O underwriting purposes.

A drop 180 days ago has ~50% weight; 360 days ago has ~25%.
"""

from __future__ import annotations

import math
from datetime import date

from do_uw.models.market_events import StockDropEvent

# 180-day half-life: weight halves every 180 days.
HALF_LIFE_DAYS = 180
DECAY_LAMBDA = math.log(2) / HALF_LIFE_DAYS  # ~0.003851


def compute_decay_weight(
    drop_date_str: str | None,
    reference_date: date | None = None,
) -> float:
    """Compute exponential decay weight for a drop date.

    Args:
        drop_date_str: Drop date as YYYY-MM-DD string, or None.
        reference_date: Reference date (defaults to today). Injectable for tests.

    Returns:
        Weight between 0.0 and 1.0. Returns 0.0 for None/invalid input.
    """
    if not drop_date_str:
        return 0.0

    if reference_date is None:
        reference_date = date.today()

    try:
        drop_date = date.fromisoformat(drop_date_str[:10])
    except (ValueError, TypeError):
        return 0.0

    days_ago = max((reference_date - drop_date).days, 0)
    return math.exp(-DECAY_LAMBDA * days_ago)


def compute_decay_weighted_severity(drop_pct: float, decay_weight: float) -> float:
    """Compute recency-adjusted severity: abs(drop_pct) * decay_weight.

    Args:
        drop_pct: Drop percentage (typically negative, e.g. -15.0).
        decay_weight: Decay weight from compute_decay_weight (0.0 to 1.0).

    Returns:
        Decay-weighted severity (always >= 0).
    """
    return abs(drop_pct) * decay_weight


def apply_decay_weights(
    drops: list[StockDropEvent],
    reference_date: date | None = None,
) -> list[StockDropEvent]:
    """Set decay_weight and decay_weighted_severity on each drop.

    Args:
        drops: List of StockDropEvent instances.
        reference_date: Reference date for decay computation (defaults to today).

    Returns:
        Drops sorted by decay_weighted_severity descending.
    """
    for drop in drops:
        date_str = drop.date.value[:10] if drop.date else None
        drop.decay_weight = compute_decay_weight(date_str, reference_date)

        drop_pct = drop.drop_pct.value if drop.drop_pct else 0.0
        drop.decay_weighted_severity = compute_decay_weighted_severity(
            drop_pct, drop.decay_weight,
        )

    drops.sort(
        key=lambda d: d.decay_weighted_severity if d.decay_weighted_severity else 0.0,
        reverse=True,
    )
    return drops


__all__ = [
    "DECAY_LAMBDA",
    "HALF_LIFE_DAYS",
    "apply_decay_weights",
    "compute_decay_weight",
    "compute_decay_weighted_severity",
]
