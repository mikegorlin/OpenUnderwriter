"""Calibration ticker configuration for check calibration runs.

Defines the 12 calibration tickers with expected underwriting tiers
and playbook assignments. Used by CalibrationRunner to validate
that pipeline scoring aligns with expert expectations.

Categories:
- clean_mega: Large, well-governed companies expected to score highly
- known_outcome: Companies with known D&O events (should score poorly)
- stable: Established companies with predictable risk profiles
- volatile: Companies with significant risk volatility
- growth: High-growth companies with elevated but manageable risk
- conglomerate: Multi-segment companies testing cross-sector analysis
- turnaround: Companies in transition testing change-related checks
- blue_chip: Iconic consumer brands with strong governance
- high_growth: Exceptional growth trajectories
"""

from __future__ import annotations

from typing import TypedDict


class CalibrationTicker(TypedDict):
    """A calibration ticker with expected tier and playbook assignment."""

    ticker: str
    industry: str
    category: str
    expected_tier: str  # e.g., "WIN/WANT", "WALK/NO_TOUCH"
    playbook: str


CALIBRATION_TICKERS: list[CalibrationTicker] = [
    {
        "ticker": "AAPL",
        "industry": "TECH_SAAS",
        "category": "clean_mega",
        "expected_tier": "WIN/WANT",
        "playbook": "tech_saas",
    },
    {
        "ticker": "SMCI",
        "industry": "TECH_SAAS",
        "category": "known_outcome",
        "expected_tier": "WALK/NO_TOUCH",
        "playbook": "tech_saas",
    },
    {
        "ticker": "XOM",
        "industry": "ENERGY_UTILITIES",
        "category": "stable",
        "expected_tier": "WANT/WRITE",
        "playbook": "energy_utilities",
    },
    {
        "ticker": "MRNA",
        "industry": "BIOTECH_PHARMA",
        "category": "volatile",
        "expected_tier": "WRITE/WATCH",
        "playbook": "biotech_pharma",
    },
    {
        "ticker": "NFLX",
        "industry": "MEDIA_ENTERTAINMENT",
        "category": "growth",
        "expected_tier": "WANT/WRITE",
        "playbook": "media_entertainment",
    },
    {
        "ticker": "JPM",
        "industry": "FINANCIAL_SERVICES",
        "category": "stable",
        "expected_tier": "WANT/WRITE",
        "playbook": "financial_services",
    },
    {
        "ticker": "PLUG",
        "industry": "ENERGY_UTILITIES",
        "category": "known_outcome",
        "expected_tier": "WATCH/WALK",
        "playbook": "energy_utilities",
    },
    {
        "ticker": "HON",
        "industry": "INDUSTRIALS_MFG",
        "category": "conglomerate",
        "expected_tier": "WANT/WRITE",
        "playbook": "industrials_mfg",
    },
    {
        "ticker": "COIN",
        "industry": "TECH_SAAS",
        "category": "known_outcome",
        "expected_tier": "WRITE/WATCH",
        "playbook": "tech_saas",
    },
    {
        "ticker": "DIS",
        "industry": "MEDIA_ENTERTAINMENT",
        "category": "turnaround",
        "expected_tier": "WRITE/WATCH",
        "playbook": "media_entertainment",
    },
    {
        "ticker": "PG",
        "industry": "CPG_CONSUMER",
        "category": "blue_chip",
        "expected_tier": "WIN/WANT",
        "playbook": "cpg_consumer",
    },
    {
        "ticker": "NVDA",
        "industry": "TECH_SAAS",
        "category": "high_growth",
        "expected_tier": "WIN/WANT",
        "playbook": "tech_saas",
    },
]
"""Canonical calibration ticker set: 12 tickers across 7 industries.

Selected for diversity:
- 3 WIN/WANT (clean mega/blue chip/high growth)
- 3 known_outcome (should score poorly)
- 3 WANT/WRITE (stable/growth)
- 3 WRITE/WATCH (volatile/turnaround)
"""


# Deep validation: 2-3 tickers each with claims research and KPI verification
DEEP_VALIDATION_VERTICALS: dict[str, list[str]] = {
    "Tech": ["AAPL", "SMCI", "NVDA"],
    "Biotech": ["MRNA"],
    "Energy": ["XOM", "PLUG"],
    "Financial": ["JPM"],
}

# Light validation: 1 ticker each with differentiation check
LIGHT_VALIDATION_VERTICALS: dict[str, list[str]] = {
    "CPG": ["PG"],
    "Media": ["DIS", "NFLX"],
    "Industrials": ["HON"],
}


def get_calibration_tickers(
    category: str | None = None,
) -> list[CalibrationTicker]:
    """Return calibration tickers, optionally filtered by category.

    Args:
        category: If provided, filter to a specific category
            (e.g., "known_outcome", "clean_mega", "stable").
            If None, return all 12 tickers.

    Returns:
        List of CalibrationTicker dicts.
    """
    if category is None:
        return list(CALIBRATION_TICKERS)
    return [t for t in CALIBRATION_TICKERS if t["category"] == category]
