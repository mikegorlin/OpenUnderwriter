"""Trend analysis and year-over-year tracking for D&O pricing.

Split from pricing_analytics.py for 500-line compliance. Provides:
- TrendPoint/MarketTrends dataclasses for trend time series
- compute_trends() for half-year bucketing of rate data
- compute_yoy_changes() for year-over-year program evolution
- detect_carrier_rotations() for carrier movement tracking
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class TrendPoint:
    """A single period in a market trend time series."""

    period: str
    median_rate: float
    count: int
    mean_rate: float


@dataclass(frozen=True)
class MarketTrends:
    """Trend analysis results for a market segment."""

    segment_label: str
    points: list[TrendPoint]
    overall_direction: str
    overall_magnitude_pct: float | None
    total_quotes: int


def _date_to_half_year(dt: datetime) -> str:
    """Convert a datetime to half-year period string (e.g., '2025-H1')."""
    half = "H1" if dt.month <= 6 else "H2"
    return f"{dt.year}-{half}"


def compute_trends(
    rates_with_dates: list[tuple[float, datetime]],
    period_type: str = "half",
) -> list[TrendPoint]:
    """Group rates by half-year period and compute per-period statistics.

    Args:
        rates_with_dates: List of (rate_on_line, effective_date) tuples.
        period_type: Period grouping type. Currently only "half" supported.

    Returns:
        Sorted list of TrendPoint objects, one per period with data.
    """
    if not rates_with_dates:
        return []

    _ = period_type  # Reserved for future period types

    # Group by period
    period_buckets: dict[str, list[float]] = {}
    for rate, dt in rates_with_dates:
        period = _date_to_half_year(dt)
        if period not in period_buckets:
            period_buckets[period] = []
        period_buckets[period].append(rate)

    # Build TrendPoints sorted by period
    points: list[TrendPoint] = []
    for period in sorted(period_buckets.keys()):
        bucket = period_buckets[period]
        points.append(
            TrendPoint(
                period=period,
                median_rate=statistics.median(bucket),
                count=len(bucket),
                mean_rate=statistics.mean(bucket),
            )
        )

    return points


def _pct_change(old: float, new: float) -> float | None:
    """Compute percentage change from old to new value.

    Returns None if old is zero (division undefined).
    """
    if old == 0.0:
        return None
    return (new - old) / old * 100.0


def _extract_carrier_names(
    layers: list[dict[str, Any]],
) -> set[str]:
    """Extract carrier names from a list of layer dicts."""
    names: set[str] = set()
    for layer in layers:
        name = layer.get("carrier_name")
        if name and isinstance(name, str) and name != "TBD":
            names.add(name)
    return names


def compute_yoy_changes(
    policy_years: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Compute year-over-year changes for a D&O program.

    Compares consecutive policy years on premium, limit, retention,
    and rate-on-line, identifying carrier rotations between years.

    Args:
        policy_years: List of policy year dicts, each with keys:
            - policy_year (int): The year
            - total_premium (float | None): Total program premium
            - total_limit (float | None): Total program limit
            - retention (float | None): SIR/deductible
            - program_rate_on_line (float | None): ROL
            - layers (list[dict]): Layer dicts with carrier_name

    Returns:
        List of change dicts for each consecutive pair, with:
            - from_year, to_year
            - premium_change_pct, limit_change_pct, retention_change_pct,
              rol_change_pct (all float | None)
            - carriers_added, carriers_removed (list[str])
    """
    if len(policy_years) < 2:
        return []

    # Sort by policy_year ascending
    sorted_years = sorted(
        policy_years, key=lambda py: py.get("policy_year", 0)
    )

    changes: list[dict[str, Any]] = []
    for i in range(len(sorted_years) - 1):
        prev = sorted_years[i]
        curr = sorted_years[i + 1]

        prev_premium = prev.get("total_premium")
        curr_premium = curr.get("total_premium")
        prev_limit = prev.get("total_limit")
        curr_limit = curr.get("total_limit")
        prev_retention = prev.get("retention")
        curr_retention = curr.get("retention")
        prev_rol = prev.get("program_rate_on_line")
        curr_rol = curr.get("program_rate_on_line")

        premium_pct: float | None = None
        if prev_premium is not None and curr_premium is not None:
            premium_pct = _pct_change(prev_premium, curr_premium)

        limit_pct: float | None = None
        if prev_limit is not None and curr_limit is not None:
            limit_pct = _pct_change(prev_limit, curr_limit)

        retention_pct: float | None = None
        if prev_retention is not None and curr_retention is not None:
            retention_pct = _pct_change(prev_retention, curr_retention)

        rol_pct: float | None = None
        if prev_rol is not None and curr_rol is not None:
            rol_pct = _pct_change(prev_rol, curr_rol)

        # Carrier rotation
        prev_carriers = _extract_carrier_names(
            prev.get("layers", [])
        )
        curr_carriers = _extract_carrier_names(
            curr.get("layers", [])
        )
        carriers_added = sorted(curr_carriers - prev_carriers)
        carriers_removed = sorted(prev_carriers - curr_carriers)

        changes.append(
            {
                "from_year": prev.get("policy_year"),
                "to_year": curr.get("policy_year"),
                "premium_change_pct": premium_pct,
                "limit_change_pct": limit_pct,
                "retention_change_pct": retention_pct,
                "rol_change_pct": rol_pct,
                "carriers_added": carriers_added,
                "carriers_removed": carriers_removed,
            }
        )

    return changes


def detect_carrier_rotations(
    policy_years: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Detect carrier rotations across consecutive policy years.

    Focused carrier movement tracking: for each year transition,
    identifies which carriers entered and exited the tower.

    Args:
        policy_years: List of policy year dicts with keys:
            - policy_year (int): The year
            - layers (list[dict]): Layer dicts with carrier_name

    Returns:
        List of rotation event dicts with:
            - year (int): The new policy year
            - carriers_in (list[str]): Carriers that joined
            - carriers_out (list[str]): Carriers that left
        Only includes years where there was actual rotation.
    """
    if len(policy_years) < 2:
        return []

    sorted_years = sorted(
        policy_years, key=lambda py: py.get("policy_year", 0)
    )

    rotations: list[dict[str, Any]] = []
    for i in range(len(sorted_years) - 1):
        prev = sorted_years[i]
        curr = sorted_years[i + 1]

        prev_carriers = _extract_carrier_names(
            prev.get("layers", [])
        )
        curr_carriers = _extract_carrier_names(
            curr.get("layers", [])
        )

        carriers_in = sorted(curr_carriers - prev_carriers)
        carriers_out = sorted(prev_carriers - curr_carriers)

        if carriers_in or carriers_out:
            rotations.append(
                {
                    "year": curr.get("policy_year"),
                    "carriers_in": carriers_in,
                    "carriers_out": carriers_out,
                }
            )

    return rotations
