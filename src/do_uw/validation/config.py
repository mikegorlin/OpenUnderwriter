"""Ticker configuration for multi-ticker validation runs.

Defines the canonical set of validation tickers across 9 industry
verticals, known-outcome companies with historical D&O events,
and edge-case filers (e.g., Foreign Private Issuers).
"""

from __future__ import annotations

from typing import TypedDict


class TickerEntry(TypedDict):
    """A validation ticker with its industry and category metadata."""

    ticker: str
    industry: str
    category: str  # "standard", "known_outcome", "edge_case"


VALIDATION_TICKERS: list[TickerEntry] = [
    # --- Standard tickers: 2 per industry vertical (18 total) ---
    # Technology / SaaS
    {"ticker": "NVDA", "industry": "TECH_SAAS", "category": "standard"},
    {"ticker": "CRM", "industry": "TECH_SAAS", "category": "standard"},
    # Biotech / Pharma
    {"ticker": "MRNA", "industry": "BIOTECH_PHARMA", "category": "standard"},
    {"ticker": "AMGN", "industry": "BIOTECH_PHARMA", "category": "standard"},
    # Energy / Utilities
    {"ticker": "XOM", "industry": "ENERGY_UTILITIES", "category": "standard"},
    {"ticker": "NEE", "industry": "ENERGY_UTILITIES", "category": "standard"},
    # Healthcare
    {"ticker": "UNH", "industry": "HEALTHCARE", "category": "standard"},
    {"ticker": "HCA", "industry": "HEALTHCARE", "category": "standard"},
    # CPG / Consumer
    {"ticker": "PG", "industry": "CPG_CONSUMER", "category": "standard"},
    {"ticker": "KO", "industry": "CPG_CONSUMER", "category": "standard"},
    # Media / Entertainment
    {"ticker": "DIS", "industry": "MEDIA_ENTERTAINMENT", "category": "standard"},
    {"ticker": "NFLX", "industry": "MEDIA_ENTERTAINMENT", "category": "standard"},
    # Industrials
    {"ticker": "CAT", "industry": "INDUSTRIALS", "category": "standard"},
    {"ticker": "HON", "industry": "INDUSTRIALS", "category": "standard"},
    # REITs
    {"ticker": "PLD", "industry": "REITS", "category": "standard"},
    {"ticker": "AMT", "industry": "REITS", "category": "standard"},
    # Transportation
    {"ticker": "UNP", "industry": "TRANSPORTATION", "category": "standard"},
    {"ticker": "FDX", "industry": "TRANSPORTATION", "category": "standard"},
    # --- Known-outcome companies with historical D&O events (5 total) ---
    {"ticker": "SMCI", "industry": "TECH_SAAS", "category": "known_outcome"},
    {"ticker": "RIDE", "industry": "INDUSTRIALS", "category": "known_outcome"},
    {"ticker": "COIN", "industry": "TECH_SAAS", "category": "known_outcome"},
    {"ticker": "LCID", "industry": "INDUSTRIALS", "category": "known_outcome"},
    {"ticker": "PLUG", "industry": "ENERGY_UTILITIES", "category": "known_outcome"},
    # --- Edge-case filers (1 total) ---
    # TSM: Foreign Private Issuer, files 20-F instead of 10-K,
    # CIK 1046179, SIC 3674
    {"ticker": "TSM", "industry": "TECH_SAAS", "category": "edge_case"},
]
"""Canonical validation ticker list.

- 18 standard tickers across 9 industry playbooks (2 per vertical)
- 5 known-outcome companies with historical D&O events
- 1 edge-case Foreign Private Issuer (TSM: files 20-F, not 10-K)

Total: 24 tickers.
"""


def get_tickers(category: str | None = None) -> list[str]:
    """Return ticker symbols, optionally filtered by category.

    Args:
        category: If provided, filter to "standard", "known_outcome",
            or "edge_case". If None, return all tickers.

    Returns:
        List of ticker symbol strings.
    """
    if category is None:
        return [t["ticker"] for t in VALIDATION_TICKERS]
    return [t["ticker"] for t in VALIDATION_TICKERS if t["category"] == category]
