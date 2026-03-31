"""Volume spike detection from yfinance daily history.

Detects trading days where volume exceeds a threshold multiple of
the trailing N-day moving average. Used by STOCK.TRADE.volume_patterns
signal for D&O risk assessment -- volume spikes often coincide with
material events that trigger securities litigation.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Defaults per user decision
_DEFAULT_LOOKBACK = 20  # 20-trading-day moving average
_DEFAULT_THRESHOLD = 2.0  # Volume > 2x average = spike


def detect_volume_spikes(
    history_1y: dict[str, Any],
    lookback_days: int = _DEFAULT_LOOKBACK,
    spike_threshold: float = _DEFAULT_THRESHOLD,
) -> list[dict[str, Any]]:
    """Detect trading days where volume exceeds Nx the moving average.

    Args:
        history_1y: yfinance history dict-of-dicts with Volume, Close, Date columns.
        lookback_days: Number of trailing days for moving average (default: 20).
        spike_threshold: Multiple of moving average to flag as spike (default: 2.0).

    Returns:
        List of spike events, each with date, volume, avg_volume,
        volume_multiple, price_change_pct.
        Sorted chronologically (oldest first).
    """
    volumes = _extract_column(history_1y, "Volume")
    closes = _extract_column(history_1y, "Close")
    dates = _extract_dates(history_1y)

    if len(volumes) < lookback_days + 1:
        logger.info(
            "VOL: Insufficient history for spike detection (%d < %d)",
            len(volumes),
            lookback_days + 1,
        )
        return []

    spikes: list[dict[str, Any]] = []
    for i in range(lookback_days, len(volumes)):
        window = volumes[i - lookback_days : i]
        avg = sum(window) / len(window)
        if avg > 0 and volumes[i] / avg >= spike_threshold:
            price_change: float | None = None
            if i > 0 and closes and i < len(closes) and closes[i - 1] > 0:
                price_change = round(
                    (closes[i] - closes[i - 1]) / closes[i - 1] * 100, 2
                )
            spikes.append(
                {
                    "date": dates[i] if i < len(dates) else "unknown",
                    "volume": int(volumes[i]),
                    "avg_volume": int(avg),
                    "volume_multiple": round(volumes[i] / avg, 2),
                    "price_change_pct": price_change,
                }
            )
    logger.info(
        "VOL: Detected %d volume spikes (>%.1fx 20-day avg) in 1-year history",
        len(spikes),
        spike_threshold,
    )
    return spikes


def _extract_column(history: dict[str, Any], col: str) -> list[float]:
    """Extract a column from yfinance dict-of-dicts format as a float list."""
    col_data = history.get(col, {})
    if not isinstance(col_data, dict):
        return []
    # yfinance dict-of-dicts uses string indices
    keys = sorted(col_data.keys(), key=lambda k: int(k) if k.isdigit() else k)
    return [float(col_data.get(k, 0) or 0) for k in keys]


def _extract_dates(history: dict[str, Any]) -> list[str]:
    """Extract date column from yfinance dict-of-dicts."""
    # yfinance may store dates in 'Date' column or as index
    date_data = history.get("Date", {})
    if not isinstance(date_data, dict):
        return []
    keys = sorted(date_data.keys(), key=lambda k: int(k) if k.isdigit() else k)
    return [str(date_data.get(k, "")) for k in keys]
