"""Market positioning analytics engine for D&O pricing intelligence.

Transforms raw pricing data into actionable market positioning insights:
confidence intervals, trend detection, and segment-based comparisons.

Pure computation functions are independently testable. The MarketPositionEngine
class wraps PricingStore for segment queries with dependency injection.

Trend analysis split to pricing_analytics_trends.py for 500-line compliance.
TrendPoint, MarketTrends, and compute_trends re-exported here for backward compat.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import datetime
from math import sqrt
from typing import TYPE_CHECKING

from do_uw.knowledge.pricing_analytics_trends import (
    MarketTrends,
    TrendPoint,
    compute_trends,
)

if TYPE_CHECKING:
    from do_uw.knowledge.pricing_store import PricingStore

__all__ = [
    "MarketPosition",
    "MarketPositionEngine",
    "MarketTrends",
    "TrendPoint",
    "compute_market_position",
    "compute_trends",
]


@dataclass(frozen=True)
class MarketPosition:
    """Statistical market position for a pricing segment."""

    peer_count: int
    confidence_level: str
    median_rate_on_line: float | None
    mean_rate_on_line: float | None
    ci_low: float | None
    ci_high: float | None
    percentile_25: float | None
    percentile_75: float | None
    min_rate: float | None
    max_rate: float | None
    trend_direction: str
    trend_magnitude_pct: float | None
    data_window: str


# T-distribution critical values at 95% CI (two-tailed, alpha=0.05)
_T_TABLE: dict[int, float] = {
    2: 4.303,
    3: 3.182,
    4: 2.776,
    5: 2.571,
    6: 2.447,
    7: 2.365,
    8: 2.306,
    9: 2.262,
    10: 2.228,
    15: 2.145,
    20: 2.086,
    30: 2.042,
    50: 2.009,
    100: 1.984,
}


def _t_value(n: int) -> float:
    """Look up t-distribution critical value for 95% CI.

    Uses exact table values for known sample sizes, interpolates
    for intermediate values, and returns 1.96 (normal approximation)
    for n > 100. Returns 0.0 for n < 2.
    """
    if n < 2:
        return 0.0
    if n > 100:
        return 1.96

    # Exact match
    if n in _T_TABLE:
        return _T_TABLE[n]

    # Interpolation: find surrounding keys
    keys = sorted(_T_TABLE.keys())
    lower_key = keys[0]
    upper_key = keys[-1]
    for k in keys:
        if k <= n:
            lower_key = k
        if k >= n:
            upper_key = k
            break

    if lower_key == upper_key:
        return _T_TABLE[lower_key]

    # Linear interpolation
    lower_val = _T_TABLE[lower_key]
    upper_val = _T_TABLE[upper_key]
    fraction = (n - lower_key) / (upper_key - lower_key)
    return lower_val + fraction * (upper_val - lower_val)


def _classify_confidence(n: int) -> str:
    """Classify confidence level based on sample size.

    HIGH: 50+ data points
    MEDIUM: 10-49 data points
    LOW: 3-9 data points
    INSUFFICIENT: fewer than 3 data points
    """
    if n >= 50:
        return "HIGH"
    if n >= 10:
        return "MEDIUM"
    if n >= 3:
        return "LOW"
    return "INSUFFICIENT"


def compute_market_position(
    rates: list[float],
    dates: list[datetime] | None = None,
) -> MarketPosition:
    """Compute market position statistics from rate-on-line values.

    Args:
        rates: List of rate-on-line float values.
        dates: Optional list of effective dates (same length as rates)
            for trend detection.

    Returns:
        MarketPosition with statistics, confidence level, and trend.
    """
    n = len(rates)

    if n < 3:
        return MarketPosition(
            peer_count=n,
            confidence_level="INSUFFICIENT",
            median_rate_on_line=None,
            mean_rate_on_line=None,
            ci_low=None,
            ci_high=None,
            percentile_25=None,
            percentile_75=None,
            min_rate=None,
            max_rate=None,
            trend_direction="INSUFFICIENT_DATA",
            trend_magnitude_pct=None,
            data_window="",
        )

    median = statistics.median(rates)
    mean = statistics.mean(rates)
    stdev = statistics.stdev(rates)
    quantiles = statistics.quantiles(rates, n=4)
    confidence = _classify_confidence(n)

    # 95% confidence interval
    t = _t_value(n)
    margin = t * stdev / sqrt(n)
    ci_low = mean - margin
    ci_high = mean + margin

    # Trend detection — requires data spanning 2+ distinct half-year periods.
    # Single-timeframe snapshots cannot establish directional trends.
    trend_direction = "INSUFFICIENT_DATA"
    trend_magnitude: float | None = None
    data_window = ""

    if dates is not None and len(dates) == n:
        sorted_pairs = sorted(
            zip(dates, rates, strict=True), key=lambda p: p[0]
        )
        sorted_dates = [p[0] for p in sorted_pairs]
        sorted_rates = [p[1] for p in sorted_pairs]

        min_date = sorted_dates[0]
        max_date = sorted_dates[-1]
        data_window = f"{min_date.strftime('%Y-%m')} to {max_date.strftime('%Y-%m')}"

        # Count distinct half-year periods
        periods: set[str] = set()
        for dt in sorted_dates:
            half = "H1" if dt.month <= 6 else "H2"
            periods.add(f"{dt.year}-{half}")

        if len(periods) >= 2:
            # Split into first/second halves by date ordering
            midpoint = n // 2
            first_half = sorted_rates[:midpoint]
            second_half = sorted_rates[midpoint:]

            if first_half and second_half:
                first_median = statistics.median(first_half)
                second_median = statistics.median(second_half)

                trend_direction = "STABLE"
                if first_median > 0:
                    pct_change = (
                        (second_median - first_median) / first_median * 100.0
                    )
                    trend_magnitude = pct_change
                    if pct_change > 5.0:
                        trend_direction = "HARDENING"
                    elif pct_change < -5.0:
                        trend_direction = "SOFTENING"

    return MarketPosition(
        peer_count=n,
        confidence_level=confidence,
        median_rate_on_line=median,
        mean_rate_on_line=mean,
        ci_low=ci_low,
        ci_high=ci_high,
        percentile_25=quantiles[0],
        percentile_75=quantiles[2],
        min_rate=min(rates),
        max_rate=max(rates),
        trend_direction=trend_direction,
        trend_magnitude_pct=trend_magnitude,
        data_window=data_window,
    )


class MarketPositionEngine:
    """Analytics engine wrapping PricingStore for market intelligence.

    Provides segment-based market position queries with confidence
    intervals and trend detection.

    Args:
        store: PricingStore instance (dependency injection).
    """

    def __init__(self, store: PricingStore) -> None:
        self._store = store

    def get_market_position(
        self,
        market_cap_tier: str | None = None,
        sector: str | None = None,
        layer_position: str | None = None,
        score_range: tuple[float, float] | None = None,
        months_back: int = 24,
    ) -> MarketPosition:
        """Query market position for a segment with optional filters.

        Args:
            market_cap_tier: Filter by market cap tier.
            sector: Filter by sector.
            layer_position: Filter by tower layer position.
            score_range: Optional (min, max) quality score filter.
            months_back: Time window in months from today.

        Returns:
            MarketPosition with statistics and confidence level.
        """
        rates_dates = self._store.get_rates_with_dates(
            market_cap_tier=market_cap_tier,
            sector=sector,
            layer_position=layer_position,
            months_back=months_back,
        )

        if score_range is not None:
            rates_dates = self._filter_by_score(
                rates_dates, score_range, market_cap_tier, sector, months_back
            )

        rates = [r for r, _ in rates_dates]
        dates = [d for _, d in rates_dates]

        return compute_market_position(rates, dates)

    def _filter_by_score(
        self,
        rates_dates: list[tuple[float, datetime]],
        score_range: tuple[float, float],
        market_cap_tier: str | None,
        sector: str | None,
        months_back: int,
    ) -> list[tuple[float, datetime]]:
        """Post-filter rates by quality score range.

        Since get_rates_with_dates returns (rate, date) tuples without
        score info, we query quotes directly for score-based filtering.
        """
        scored_rates = self._store.get_rates_with_dates_and_scores(
            market_cap_tier=market_cap_tier,
            sector=sector,
            months_back=months_back,
        )
        min_score, max_score = score_range
        return [
            (rate, dt)
            for rate, dt, score in scored_rates
            if score is not None and min_score <= score <= max_score
        ]

    def get_trends(
        self,
        market_cap_tier: str | None = None,
        sector: str | None = None,
        layer_position: str | None = None,
        months_back: int = 48,
    ) -> MarketTrends:
        """Compute trend analysis for a market segment.

        Args:
            market_cap_tier: Filter by market cap tier.
            sector: Filter by sector.
            layer_position: Filter by tower layer position.
            months_back: Time window in months from today.

        Returns:
            MarketTrends with per-period data and overall direction.
        """
        rates_dates = self._store.get_rates_with_dates(
            market_cap_tier=market_cap_tier,
            sector=sector,
            layer_position=layer_position,
            months_back=months_back,
        )

        points = compute_trends(rates_dates)
        total_quotes = sum(p.count for p in points)

        # Determine overall direction
        direction = "STABLE"
        magnitude: float | None = None
        if len(points) >= 2:
            first_median = points[0].median_rate
            last_median = points[-1].median_rate
            if first_median > 0:
                pct = (last_median - first_median) / first_median * 100.0
                magnitude = pct
                if pct > 5.0:
                    direction = "HARDENING"
                elif pct < -5.0:
                    direction = "SOFTENING"

        # Build segment label
        parts: list[str] = []
        if market_cap_tier:
            parts.append(market_cap_tier.upper())
        if sector:
            parts.append(sector.upper())
        segment_label = " / ".join(parts) if parts else "ALL SEGMENTS"

        return MarketTrends(
            segment_label=segment_label,
            points=points,
            overall_direction=direction,
            overall_magnitude_pct=magnitude,
            total_quotes=total_quotes,
        )

    def get_position_for_analysis(
        self,
        ticker: str,
        quality_score: float,
        market_cap_tier: str,
        sector: str | None,
    ) -> MarketPosition:
        """Get market position for a company's peer segment.

        Convenience method for pipeline integration: queries by the
        company's market cap tier and sector to find peer pricing.

        Args:
            ticker: Company ticker (for context, not filtered by).
            quality_score: Company quality score (for score-range context).
            market_cap_tier: Company's market cap tier.
            sector: Company's sector.

        Returns:
            MarketPosition for the peer segment.
        """
        return self.get_market_position(
            market_cap_tier=market_cap_tier,
            sector=sector,
        )
