"""Phase 119: Multi-horizon stock performance summary and analyst consensus.

Computes returns across multiple time horizons and structures analyst
consensus data for expanded rendering.
"""

from __future__ import annotations

from typing import Any

from do_uw.stages.render.formatters import safe_float


_HORIZONS: dict[str, int] = {
    "1D": 1,
    "5D": 5,
    "1M": 21,
    "3M": 63,
    "6M": 126,
    "52W": 252,
}


def compute_multi_horizon_returns(
    prices: list[float],
    *,
    trading_days_available: int | None = None,
) -> dict[str, float | None]:
    """Compute returns for standard time horizons from price history.

    Args:
        prices: Chronological close prices (oldest first).
        trading_days_available: If < 252, adds "Since IPO" return.

    Returns:
        Dict mapping horizon label to return percentage, or None if insufficient data.
    """
    if len(prices) < 2:
        return {}

    current = safe_float(prices[-1])
    result: dict[str, float | None] = {}

    for label, days in _HORIZONS.items():
        if len(prices) > days:
            prior = safe_float(prices[-(days + 1)])
            if prior != 0:
                result[label] = round((current - prior) / prior * 100, 2)
            else:
                result[label] = None
        else:
            result[label] = None

    # Since IPO for recent listings
    if trading_days_available is not None and trading_days_available < 252:
        first = safe_float(prices[0])
        if first != 0:
            result["Since IPO"] = round((current - first) / first * 100, 2)

    return result


def build_analyst_consensus(
    analyst_profile: Any,
    market_data: dict[str, Any] | None = None,
    current_price: float | None = None,
) -> dict[str, Any]:
    """Structure analyst consensus data for expanded table rendering.

    Args:
        analyst_profile: AnalystSentimentProfile from state.
        market_data: Raw market data from state.acquired_data for rating distribution.
        current_price: Current stock price for upside calculation.

    Returns:
        Dict with rating_distribution, targets, coverage, consensus, narrative fields.
        Empty dict if no data.
    """
    # Extract fields from profile
    coverage_count = _extract_sourced_value(analyst_profile, "coverage_count")
    consensus_label = _extract_sourced_str(analyst_profile, "consensus")
    rec_mean = _extract_sourced_value(analyst_profile, "recommendation_mean")
    target_mean = _extract_sourced_value(analyst_profile, "target_price_mean")
    target_high = _extract_sourced_value(analyst_profile, "target_price_high")
    target_low = _extract_sourced_value(analyst_profile, "target_price_low")
    upgrades = getattr(analyst_profile, "recent_upgrades", 0) or 0
    downgrades = getattr(analyst_profile, "recent_downgrades", 0) or 0

    # Check if we have any data at all
    if not consensus_label and rec_mean is None and target_mean is None and not coverage_count:
        return {}

    result: dict[str, Any] = {}

    # Rating distribution from recommendations_summary
    rating_dist = _parse_rating_distribution(market_data)
    if rating_dist:
        result["rating_distribution"] = rating_dist

    # Target prices
    if target_mean is not None:
        result["mean_target"] = safe_float(target_mean)
    if target_high is not None:
        result["high_target"] = safe_float(target_high)
    if target_low is not None:
        result["low_target"] = safe_float(target_low)

    # Current price and upside
    upside_pct: float | None = None
    if current_price is not None:
        result["current_price"] = safe_float(current_price)
    if target_mean is not None and current_price is not None:
        cp = safe_float(current_price)
        tm = safe_float(target_mean)
        if cp > 0:
            upside_pct = round((tm - cp) / cp * 100, 1)
            result["upside_pct"] = upside_pct

    # Coverage and consensus
    if coverage_count is not None:
        result["coverage_count"] = int(safe_float(coverage_count))
    if consensus_label:
        result["consensus_label"] = consensus_label

    # Firm-level upgrade/downgrade activity from recommendations
    if market_data:
        firm_upgrades, firm_downgrades = _count_recent_firm_changes(market_data)
        if firm_upgrades > 0 or firm_downgrades > 0:
            result["firm_upgrades"] = firm_upgrades
            result["firm_downgrades"] = firm_downgrades

    # Narrative (STOCK-06)
    narrative = _generate_analyst_narrative(
        consensus_label=consensus_label or "",
        recommendation_mean=safe_float(rec_mean) if rec_mean is not None else None,
        mean_target=safe_float(target_mean) if target_mean is not None else None,
        current_price=safe_float(current_price) if current_price is not None else None,
        upside_pct=upside_pct,
        upgrades=upgrades,
        downgrades=downgrades,
        coverage_count=int(safe_float(coverage_count)) if coverage_count is not None else None,
    )
    result["narrative"] = narrative

    return result


def _generate_analyst_narrative(
    consensus_label: str,
    recommendation_mean: float | None,
    mean_target: float | None,
    current_price: float | None,
    upside_pct: float | None,
    upgrades: int,
    downgrades: int,
    coverage_count: int | None,
) -> str:
    """Generate interpretive narrative for analyst consensus (STOCK-06).

    Returns a 1-2 sentence summary like:
    "Analyst consensus is Overweight (mean 2.1/5.0) with $185 mean target
    (+14.2% upside). 3 upgrades vs 1 downgrade in last 90 days.
    15 analysts provide coverage."

    Returns empty string if insufficient data for meaningful narrative.
    """
    parts: list[str] = []
    if not consensus_label and recommendation_mean is None:
        return ""

    # Consensus + mean rating
    if consensus_label:
        mean_str = f" (mean {recommendation_mean:.1f}/5.0)" if recommendation_mean else ""
        parts.append(f"Analyst consensus is {consensus_label}{mean_str}")

    # Target price + upside
    if mean_target is not None and current_price is not None and upside_pct is not None:
        direction = "upside" if upside_pct >= 0 else "downside"
        parts.append(f"with ${mean_target:.0f} mean target ({upside_pct:+.1f}% {direction})")

    # Upgrade/downgrade momentum
    if upgrades > 0 or downgrades > 0:
        parts.append(f"{upgrades} upgrade(s) vs {downgrades} downgrade(s) in last 90 days")

    # Coverage
    if coverage_count and coverage_count > 0:
        parts.append(f"{coverage_count} analysts provide coverage")

    # Join with periods
    if not parts:
        return ""
    narrative = ". ".join(parts) + "."
    return narrative


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_sourced_value(obj: Any, attr: str) -> Any:
    """Extract .value from SourcedValue attribute, or None."""
    sv = getattr(obj, attr, None)
    if sv is None:
        return None
    if hasattr(sv, "value"):
        return sv.value
    return sv


def _extract_sourced_str(obj: Any, attr: str) -> str:
    """Extract string from SourcedValue attribute, or empty string."""
    val = _extract_sourced_value(obj, attr)
    if val is None:
        return ""
    return str(val)


def _parse_rating_distribution(
    market_data: dict[str, Any] | None,
) -> dict[str, int] | None:
    """Parse rating distribution from recommendations_summary.

    IMPORTANT: Uses recommendations_summary (aggregate counts per period),
    NOT recommendations (per-firm history).
    """
    if not market_data:
        return None

    rec_summary = market_data.get("recommendations_summary")
    if not rec_summary or not isinstance(rec_summary, dict):
        return None

    # recommendations_summary has columns: period, strongBuy, buy, hold, sell, strongSell
    # Each is a list. Use the most recent period (index 0).
    result: dict[str, int] = {}
    for key in ("strongBuy", "buy", "hold", "sell", "strongSell"):
        values = rec_summary.get(key, [])
        if isinstance(values, list) and len(values) > 0:
            result[key] = int(safe_float(values[0]))
        else:
            result[key] = 0

    # Only return if we have any non-zero counts
    if sum(result.values()) == 0:
        return None

    return result


def _count_recent_firm_changes(
    market_data: dict[str, Any],
) -> tuple[int, int]:
    """Count recent upgrade/downgrade firm-level changes from recommendations.

    Uses market_data["recommendations"] which has columns:
    firm, toGrade, fromGrade, action.
    """
    recs = market_data.get("recommendations")
    if not recs or not isinstance(recs, dict):
        return 0, 0

    actions = recs.get("action", [])
    if not isinstance(actions, list):
        return 0, 0

    upgrades = 0
    downgrades = 0
    for action in actions:
        action_str = str(action).lower()
        if action_str in ("up", "upgrade", "reiterate"):
            upgrades += 1
        elif action_str in ("down", "downgrade"):
            downgrades += 1

    return upgrades, downgrades
