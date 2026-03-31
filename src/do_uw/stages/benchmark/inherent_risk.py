"""Inherent risk baseline computation for SECT1-02.

Computes the actuarial filing probability baseline using a
multiplicative adjustment approach:

    company_rate = sector_base_rate * cap_multiplier * score_multiplier

Inputs:
- Sector base rate from sectors.json claim_base_rates
- Market cap multiplier from sectors.json market_cap_filing_multipliers
- Quality score multiplier derived from tier/score

Severity ranges from scoring.json by_market_cap tiers.
All values marked NEEDS CALIBRATION per SECT7-11.
"""

from __future__ import annotations

import logging
from typing import Any, cast

from do_uw.models.executive_summary import InherentRiskBaseline
from do_uw.models.scoring import Tier

logger = logging.getLogger(__name__)

# Score multiplier ranges by tier.
# Each tier maps to (min_multiplier, max_multiplier).
# The multiplier is interpolated linearly within the quality score
# range for each tier.
_TIER_MULTIPLIER_RANGES: dict[Tier, tuple[float, float]] = {
    Tier.WIN: (0.3, 0.5),
    Tier.WANT: (0.6, 0.9),
    Tier.WRITE: (1.0, 1.2),
    Tier.WATCH: (1.3, 1.8),
    Tier.WALK: (2.0, 3.0),
    Tier.NO_TOUCH: (3.5, 3.5),
}

# Quality score boundaries per tier (high end, low end).
_TIER_SCORE_RANGES: dict[Tier, tuple[int, int]] = {
    Tier.WIN: (100, 86),
    Tier.WANT: (85, 71),
    Tier.WRITE: (70, 51),
    Tier.WATCH: (50, 31),
    Tier.WALK: (30, 11),
    Tier.NO_TOUCH: (10, 0),
}


def _determine_cap_tier(
    market_cap: float | None,
    tiers_config: dict[str, Any],
) -> tuple[str, float]:
    """Determine market cap tier and filing multiplier.

    Iterates tier definitions from largest to smallest (mega -> micro).
    Returns (tier_name, multiplier). Default: ("mid", 1.0).

    Args:
        market_cap: Market capitalization in USD. None = mid tier.
        tiers_config: market_cap_filing_multipliers from sectors.json.

    Returns:
        Tuple of (tier_name, multiplier).
    """
    if market_cap is None:
        return ("mid", 1.0)

    # Order: mega > large > mid > small > micro
    tier_order = ["mega", "large", "mid", "small", "micro"]

    for tier_name in tier_order:
        tier_data = tiers_config.get(tier_name)
        if tier_data is None or not isinstance(tier_data, dict):
            continue
        tier_dict = cast(dict[str, Any], tier_data)
        min_cap = float(tier_dict.get("min_cap", 0))
        if market_cap >= min_cap:
            return (tier_name, float(tier_dict.get("multiplier", 1.0)))

    return ("mid", 1.0)


def _quality_score_multiplier(
    quality_score: float,
    tier: Tier,
) -> float:
    """Compute multiplicative adjustment factor from quality score.

    Uses linear interpolation within the tier's multiplier range.
    Higher quality score within a tier = lower multiplier (less risk).

    Args:
        quality_score: Quality score 0-100.
        tier: Underwriting tier classification.

    Returns:
        Score multiplier for inherent risk calculation.
    """
    mult_range = _TIER_MULTIPLIER_RANGES.get(tier)
    score_range = _TIER_SCORE_RANGES.get(tier)

    if mult_range is None or score_range is None:
        return 1.0

    min_mult, max_mult = mult_range
    high_score, low_score = score_range

    # NO_TOUCH is a fixed multiplier
    if high_score == low_score:
        return min_mult

    score_span = high_score - low_score
    if score_span == 0:
        return min_mult

    # Linear interpolation: higher score within tier = lower multiplier
    # At high_score: multiplier = min_mult (best within tier)
    # At low_score: multiplier = max_mult (worst within tier)
    clamped_score = max(low_score, min(high_score, quality_score))
    fraction_from_top = (high_score - clamped_score) / score_span
    return min_mult + fraction_from_top * (max_mult - min_mult)


def _lookup_severity_ranges(
    market_cap: float | None,
    scoring_config: dict[str, Any],
) -> tuple[float, float, float, float, str]:
    """Look up severity ranges from scoring.json by_market_cap.

    Returns (25th, 50th, 75th, 95th percentile, tier_label) in millions.
    Uses the tier_multipliers to compute weighted severity at each percentile.

    Args:
        market_cap: Market cap in USD. None = MID tier defaults.
        scoring_config: Full scoring.json config.

    Returns:
        Tuple of (p25, p50, p75, p95, tier_label) in USD millions.
    """
    severity = scoring_config.get("severity_ranges", {})
    by_cap = severity.get("by_market_cap", [])

    # Find matching market cap tier
    if not isinstance(by_cap, list):
        return (0.0, 0.0, 0.0, 0.0, "UNKNOWN")

    matched_tier: dict[str, Any] = {}
    tier_label = "MID"

    cap_b = (market_cap or 0) / 1_000_000_000  # Convert to billions

    cap_list = cast(list[Any], by_cap)
    for raw_entry in cap_list:
        if not isinstance(raw_entry, dict):
            continue
        entry_dict = cast(dict[str, Any], raw_entry)
        min_b = float(entry_dict.get("min_cap_b", 0))
        max_b = float(entry_dict.get("max_cap_b", float("inf")))
        if min_b <= cap_b and (cap_b < max_b or max_b == float("inf")):
            matched_tier = entry_dict
            tier_label = str(entry_dict.get("tier", "MID"))
            break

    if not matched_tier:
        return (0.0, 0.0, 0.0, 0.0, "UNKNOWN")

    raw_range: Any = matched_tier.get("base_range_m", [0, 0])
    base_range = cast(list[Any], raw_range)
    if not isinstance(raw_range, list) or len(base_range) < 2:
        return (0.0, 0.0, 0.0, 0.0, tier_label)

    low_m = float(cast(float, base_range[0]))
    high_m = float(cast(float, base_range[1]))
    spread = high_m - low_m

    # Distribute across percentiles within the range
    p25 = low_m
    p50 = low_m + spread * 0.4
    p75 = low_m + spread * 0.7
    p95 = high_m

    return (p25, p50, p75, p95, tier_label)


def compute_inherent_risk_baseline(
    sector_code: str,
    market_cap: float | None,
    quality_score: float,
    tier: Tier,
    sectors_config: dict[str, Any],
    scoring_config: dict[str, Any],
) -> InherentRiskBaseline:
    """Compute actuarial filing probability baseline with company adjustments.

    Steps:
    1. Look up base rate from sectors_config["claim_base_rates"][sector_code]
    2. Look up cap multiplier from sectors_config["market_cap_filing_multipliers"]
    3. Compute score multiplier from quality_score/tier
    4. adjusted_rate = base_rate * cap_multiplier * score_multiplier
    5. Look up severity ranges from scoring_config

    Args:
        sector_code: Sector code (e.g., "TECH", "FINS").
        market_cap: Market capitalization in USD.
        quality_score: Quality score 0-100.
        tier: Underwriting tier classification.
        sectors_config: Full sectors.json config.
        scoring_config: Full scoring.json config.

    Returns:
        Populated InherentRiskBaseline model.
    """
    # Step 1: Base rate
    raw_rates: Any = sectors_config.get("claim_base_rates", {})
    claim_rates = cast(dict[str, Any], raw_rates) if isinstance(raw_rates, dict) else {}
    raw_base: Any = claim_rates.get(sector_code, claim_rates.get("DEFAULT", 3.9))
    base_rate = float(cast(float, raw_base))

    # Step 2: Market cap multiplier
    raw_tiers: Any = sectors_config.get("market_cap_filing_multipliers", {})
    cap_tiers = cast(dict[str, Any], raw_tiers) if isinstance(raw_tiers, dict) else {}
    cap_tier_name, cap_multiplier = _determine_cap_tier(market_cap, cap_tiers)

    # Step 3: Score multiplier
    score_mult = _quality_score_multiplier(quality_score, tier)

    # Step 4: Adjusted rate
    cap_adjusted = base_rate * cap_multiplier
    company_adjusted = cap_adjusted * score_mult

    # Step 5: Severity ranges
    p25, p50, p75, p95, _sev_tier = _lookup_severity_ranges(
        market_cap, scoring_config,
    )

    # Sector name lookup
    raw_codes: Any = sectors_config.get("sector_codes", {})
    sector_codes_dict = cast(dict[str, Any], raw_codes) if isinstance(raw_codes, dict) else {}
    raw_mappings: Any = sector_codes_dict.get("mappings", {})
    mappings_dict = cast(dict[str, Any], raw_mappings) if isinstance(raw_mappings, dict) else {}
    sector_name = str(mappings_dict.get(sector_code, sector_code))

    logger.info(
        "Inherent risk: sector=%s base=%.1f%% cap_mult=%.2f "
        "score_mult=%.2f adjusted=%.2f%%",
        sector_code, base_rate, cap_multiplier, score_mult, company_adjusted,
    )

    return InherentRiskBaseline(
        sector_base_rate_pct=base_rate,
        market_cap_multiplier=cap_multiplier,
        market_cap_adjusted_rate_pct=round(cap_adjusted, 4),
        score_multiplier=round(score_mult, 4),
        company_adjusted_rate_pct=round(company_adjusted, 4),
        severity_range_25th=round(p25, 2),
        severity_range_50th=round(p50, 2),
        severity_range_75th=round(p75, 2),
        severity_range_95th=round(p95, 2),
        sector_name=sector_name,
        market_cap_tier=cap_tier_name.upper(),
        methodology_note="NEEDS CALIBRATION",
    )


__all__ = ["compute_inherent_risk_baseline"]
