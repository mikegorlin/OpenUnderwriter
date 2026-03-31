"""Classification engine: deterministic filing rate from 3 objective variables.

classify_company() is a pure function with no side effects. It takes
market cap, sector code, and years public, reads all domain values from
the classification.json config, and returns a ClassificationResult.

Formula: filing_rate = sector_base_rate * cap_multiplier * ipo_multiplier
Capped at 25% as a sanity ceiling.

Internal helpers:
- _determine_cap_tier: Market cap -> tier + multiplier
- _get_sector_rate: Sector code -> base filing rate
- _ipo_age_multiplier: Years public -> IPO age multiplier (3-year cliff model)
- _compute_ddl_base: Market cap * assumed drop -> DDL exposure
"""

from __future__ import annotations

import logging
from typing import Any, cast

from do_uw.brain.brain_unified_loader import load_config
from do_uw.models.classification import ClassificationResult, MarketCapTier
from do_uw.stages.analyze.layers.classify.severity_bands import compute_severity_band

logger = logging.getLogger(__name__)

# Absolute maximum filing rate to prevent unreasonable results.
_MAX_FILING_RATE_PCT = 25.0


def load_classification_config() -> dict[str, Any]:
    """Load classification.json from the config directory.

    Returns:
        Parsed classification config dict.
    """
    return load_config("classification")


def _determine_cap_tier(
    market_cap: float | None,
    tiers_config: list[dict[str, Any]],
) -> tuple[MarketCapTier, float]:
    """Determine market cap tier and filing multiplier.

    Iterates tiers from largest to smallest (MEGA -> MICRO).
    Returns (MarketCapTier, filing_multiplier).
    Default for None market_cap: (MID, 1.0).

    Args:
        market_cap: Market capitalization in USD. None = unknown.
        tiers_config: market_cap_tiers array from classification.json.

    Returns:
        Tuple of (MarketCapTier, filing_multiplier).
    """
    if market_cap is None:
        return (MarketCapTier.MID, 1.0)

    for tier_data in tiers_config:
        tier_name = str(tier_data.get("tier", "MID"))
        min_cap = float(tier_data.get("min_cap", 0))
        multiplier = float(tier_data.get("filing_multiplier", 1.0))

        if market_cap >= min_cap:
            try:
                cap_tier = MarketCapTier(tier_name)
            except ValueError:
                cap_tier = MarketCapTier.MID
            return (cap_tier, multiplier)

    # Fallback: if nothing matched (should not happen with min_cap=0 MICRO)
    return (MarketCapTier.MID, 1.0)


def _get_sector_rate(
    sector_code: str,
    sector_rates: dict[str, Any],
) -> tuple[float, str]:
    """Look up base filing rate by sector code.

    Falls back to DEFAULT if sector code not found.

    Args:
        sector_code: Sector code (e.g., "TECH", "BIOT").
        sector_rates: sector_rates dict from classification.json.

    Returns:
        Tuple of (base_rate_pct, sector_code_used).
    """
    if sector_code in sector_rates:
        return (float(sector_rates[sector_code]), sector_code)

    default_rate = float(sector_rates.get("DEFAULT", 3.5))
    return (default_rate, "DEFAULT")


def _ipo_age_multiplier(
    years_public: int | None,
    ipo_config: dict[str, Any],
) -> float:
    """Compute IPO age multiplier using the 3-year cliff model.

    The cliff model:
    - Years 0 to cliff_years (inclusive): cliff_multiplier (2.8x)
    - Years cliff_years+1 to transition_years (inclusive): transition_multiplier (1.5x)
    - Years > transition_years: seasoned_multiplier (1.0x)
    - None years_public: assume seasoned (1.0x)

    Args:
        years_public: Years since IPO. None = unknown.
        ipo_config: ipo_age_decay dict from classification.json.

    Returns:
        IPO age multiplier.
    """
    if years_public is None:
        return float(ipo_config.get("seasoned_multiplier", 1.0))

    cliff_years = int(ipo_config.get("cliff_years", 3))
    cliff_mult = float(ipo_config.get("cliff_multiplier", 2.8))
    transition_years = int(ipo_config.get("transition_years", 5))
    transition_mult = float(ipo_config.get("transition_multiplier", 1.5))
    seasoned_mult = float(ipo_config.get("seasoned_multiplier", 1.0))

    if years_public <= cliff_years:
        return cliff_mult
    if years_public <= transition_years:
        return transition_mult
    return seasoned_mult


def _compute_ddl_base(
    market_cap: float | None,
    drop_pct: float,
) -> float:
    """Compute base DDL exposure from market cap and assumed stock drop.

    DDL (Direct D&O Liability) exposure is a rough estimate of
    potential claim damages based on market cap decline.

    Args:
        market_cap: Market capitalization in USD. None = 0.
        drop_pct: Assumed stock drop percentage.

    Returns:
        DDL exposure in USD millions.
    """
    if market_cap is None:
        return 0.0
    ddl_usd = market_cap * drop_pct / 100.0
    return round(ddl_usd / 1_000_000, 1)


def classify_company(
    market_cap: float | None,
    sector_code: str,
    years_public: int | None,
    config: dict[str, Any],
) -> ClassificationResult:
    """Classify company into base filing rate and severity band.

    Uses ONLY 3 objective variables:
    1. Market cap -> tier (Mega/Large/Mid/Small/Micro)
    2. Industry sector (SIC/NAICS -> sector code) -> base rate
    3. IPO age (years since listing) -> age multiplier

    Formula: filing_rate = sector_base_rate * cap_multiplier * ipo_multiplier
    Capped at 25% as a sanity ceiling.

    This is a pure function -- fully deterministic, no side effects.
    All domain values loaded from config.

    Args:
        market_cap: Market capitalization in USD. None = unknown.
        sector_code: Sector code (e.g., "TECH", "BIOT", "FINS").
        years_public: Years since IPO. None = unknown (treated as seasoned).
        config: Parsed classification.json config dict.

    Returns:
        Populated ClassificationResult with filing rate, severity band, etc.
    """
    raw_tiers: Any = config.get("market_cap_tiers", [])
    tiers_config = cast(list[dict[str, Any]], raw_tiers)

    raw_rates: Any = config.get("sector_rates", {})
    sector_rates = cast(dict[str, Any], raw_rates)

    raw_ipo: Any = config.get("ipo_age_decay", {})
    ipo_config = cast(dict[str, Any], raw_ipo)

    # Step 1: Determine market cap tier and multiplier
    cap_tier, cap_multiplier = _determine_cap_tier(market_cap, tiers_config)

    # Step 2: Get sector base rate
    base_rate, sector_used = _get_sector_rate(sector_code, sector_rates)

    # Step 3: Compute IPO age multiplier
    ipo_mult = _ipo_age_multiplier(years_public, ipo_config)

    # Step 4: Compute filing rate (capped at maximum)
    filing_rate = base_rate * cap_multiplier * ipo_mult
    filing_rate = min(filing_rate, _MAX_FILING_RATE_PCT)

    # Step 5: Compute severity band
    severity_low, severity_high = compute_severity_band(
        market_cap, tiers_config,
    )

    # Step 6: Compute DDL base exposure
    drop_pct = float(config.get("ddl_base_drop_pct", 15))
    ddl_base = _compute_ddl_base(market_cap, drop_pct)

    # Build sector name from code
    sector_name = sector_code if sector_used == sector_code else f"{sector_code} (DEFAULT)"

    logger.info(
        "Classification: tier=%s sector=%s rate=%.2f%% "
        "cap_mult=%.2f ipo_mult=%.2f severity=[%.0f-%.0fM]",
        cap_tier.value,
        sector_code,
        filing_rate,
        cap_multiplier,
        ipo_mult,
        severity_low,
        severity_high,
    )

    return ClassificationResult(
        market_cap_tier=cap_tier,
        sector_code=sector_code,
        sector_name=sector_name,
        years_public=years_public,
        base_filing_rate_pct=round(filing_rate, 2),
        severity_band_low_m=severity_low,
        severity_band_high_m=severity_high,
        ddl_exposure_base_m=ddl_base,
        ipo_multiplier=ipo_mult,
        cap_filing_multiplier=cap_multiplier,
        methodology="classification_v1",
    )


__all__ = [
    "classify_company",
    "load_classification_config",
]
