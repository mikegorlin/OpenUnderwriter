"""Ground truth data for JPM -- hand-verified from SEC filings.

Sources:
- Identity: SEC EDGAR Submissions API (CIK 0000019617)
- Financials: SEC EDGAR Company Facts API (XBRL 10-K filings)
  - FY2024 10-K filed 2025-02-18 (fiscal year ended 2024-12-31)
- Governance: JPMorgan Chase 2024 DEF 14A proxy statement
- Litigation: Stanford Securities Class Action Clearinghouse
- Distress: Altman Z-Score NOT applicable to banks (Z'' variant needed)

All financial values are in raw USD (not millions/thousands).

NOTE: JPMorgan is a bank holding company (SIC 6020). Many standard
financial metrics (Altman Z-Score original formula, standard debt ratios)
are not meaningful for financial institutions. Ground truth for financials
uses bank-appropriate metrics where applicable.
"""

from __future__ import annotations

from typing import Any

# JPMorgan Chase FY2024 10-K (filed 2025-02-18, period ending 2024-12-31)
# CIK: 0000019617
GROUND_TRUTH: dict[str, dict[str, Any]] = {
    "identity": {
        "legal_name": "JPMorgan Chase & Co.",
        "cik": "19617",
        "sic_code": "6020",
        # SIC 6020 = State commercial banks-Federal Reserve members -> FINS
        "sector": "FINS",
        "exchange": "NYSE",
    },
    "financials": {
        # From XBRL 10-K FY2024 -- raw USD
        # Revenue for banks is different: Net Interest Income + Non-interest
        # Revenue: us-gaap:Revenues (or InterestAndNoninterestRevenue)
        "revenue_latest": 180562000000.0,
        # Net Income: us-gaap:NetIncomeLoss
        "net_income_latest": 58471000000.0,
        # Total Assets: us-gaap:Assets
        "total_assets": 4003468000000.0,
        # Total debt for banks: Long-term borrowings
        # us-gaap:LongTermDebt
        "total_debt": 407782000000.0,
        # Cash: us-gaap:CashAndCashEquivalentsAtCarryingValue
        # (includes cash deposited at Federal Reserve)
        "cash_and_equivalents": 24054000000.0,
        "period_label": "FY2024",
        # Note: Bank financial comparisons need wider tolerance (10%)
        # because XBRL tag resolution for banks is less standardized
        # and our extractor may use different revenue/debt concepts.
    },
    "market": {
        # JPM market cap > $500B -> MEGA tier
        "market_cap_tier": "MEGA",
    },
    "governance": {
        # JPM board: 11 members per 2024 DEF 14A
        # Jamie Dimon (Chairman/CEO), plus 10 independent directors
        "board_size": 11,
        # CEO: Jamie Dimon (since Dec 2005)
        "ceo_name": "Jamie Dimon",
        # CFO: Jeremy Barnum (since 2022)
        "cfo_name": "Jeremy Barnum",
    },
    "litigation": {
        # JPM has had securities class actions (financial crisis era +
        # London Whale + others)
        "has_active_sca": True,
        "sca_count_approximate": 5,
    },
    "distress": {
        # Banks: standard Altman Z-Score is not applicable (designed for
        # manufacturing firms). Our system may use Z'' variant or report
        # NOT_APPLICABLE. Either "SAFE" or "not_applicable" is acceptable.
        "altman_z_zone": "SAFE",
    },
}
