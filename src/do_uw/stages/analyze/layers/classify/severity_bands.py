"""Severity band computation for classification engine.

Maps market cap to expected severity (settlement) ranges based on
the market cap tier definitions in classification.json.

Severity bands represent the expected range of settlement values
in USD millions for D&O claims, based on the company's market cap tier.
"""

from __future__ import annotations

from typing import Any

# Default severity band for MID tier when lookup fails.
_DEFAULT_SEVERITY_LOW_M = 15.0
_DEFAULT_SEVERITY_HIGH_M = 40.0


def compute_severity_band(
    market_cap: float | None,
    tiers_config: list[dict[str, Any]],
) -> tuple[float, float]:
    """Look up severity band [low_m, high_m] from market cap tier.

    Iterates tiers from largest to smallest, matching market cap
    to the first tier whose min_cap is <= market_cap.

    Default: (15.0, 40.0) for MID tier.

    Args:
        market_cap: Market capitalization in USD. None = MID default.
        tiers_config: market_cap_tiers array from classification.json.

    Returns:
        Tuple of (severity_low_m, severity_high_m) in USD millions.
    """
    if market_cap is None:
        return (_DEFAULT_SEVERITY_LOW_M, _DEFAULT_SEVERITY_HIGH_M)

    for tier_data in tiers_config:
        min_cap = float(tier_data.get("min_cap", 0))
        if market_cap >= min_cap:
            raw_band: Any = tier_data.get("severity_band_m", [])
            if isinstance(raw_band, list) and len(raw_band) >= 2:
                return (float(raw_band[0]), float(raw_band[1]))
            return (_DEFAULT_SEVERITY_LOW_M, _DEFAULT_SEVERITY_HIGH_M)

    return (_DEFAULT_SEVERITY_LOW_M, _DEFAULT_SEVERITY_HIGH_M)


__all__ = ["compute_severity_band"]
