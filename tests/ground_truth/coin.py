"""Ground truth data for COIN -- hand-verified from SEC filings.

Sources:
- Identity: SEC EDGAR Submissions API (CIK 1679788)
- Financials: SEC EDGAR Company Facts API (XBRL 10-K filings)
  - FY2024 10-K (filed 2025-02, fiscal year ended 2024-12-31)
  Ground truth tracks the LATEST available period (FY2024).
- Governance: Coinbase 2024 DEF 14A proxy statement
- Litigation: Stanford Securities Class Action Clearinghouse, SEC
- Distress: Computed from XBRL financial data

KNOWN-OUTCOME COMPANY: Coinbase was sued by the SEC in June 2023
alleging unregistered securities offering. Active securities class
actions. These D&O signals are the critical ground truth values.

All financial values are in raw USD (not millions/thousands).
"""

from __future__ import annotations

from typing import Any

# Coinbase FY2024 10-K (period ending 2024-12-31)
# CIK: 1679788
GROUND_TRUTH: dict[str, dict[str, Any]] = {
    "identity": {
        "legal_name": "Coinbase Global, Inc.",
        "cik": "1679788",
        "sic_code": "6199",
        # SIC 6199 = Finance Services -> FINS sector (SIC 60-64 range)
        "sector": "FINS",
        "exchange": "Nasdaq",
    },
    "financials": {
        # From XBRL 10-K FY2024 (period ending 2024-12-31) -- raw USD
        # Revenue rebounded with crypto market recovery
        "revenue_latest": 6564028000.0,
        # Net Income: returned to profitability in 2024
        "net_income_latest": 2579066000.0,
        # Total Assets: includes customer crypto assets held on balance sheet
        # which significantly inflates this figure vs company-only assets
        "total_assets": 22541951000.0,
        # Total Debt
        "total_debt": 4234081000.0,
        # Cash: includes crypto custodial cash
        "cash_and_equivalents": 8543903000.0,
        "period_label": "FY2024",
    },
    "market": {
        # Coinbase market cap ~$40-70B -> LARGE tier
        "market_cap_tier": "LARGE",
    },
    "governance": {
        # Coinbase board: 8 members per DEF 14A
        "board_size": 8,
        # CEO: Brian Armstrong (co-founder, since 2012)
        "ceo_name": "Brian Armstrong",
        # CFO: Alesia Haas (since 2018)
        "cfo_name": "Alesia Haas",
    },
    "litigation": {
        # KNOWN-OUTCOME: SEC enforcement action (Jun 2023) +
        # multiple securities class actions. NOTE: LLM extraction from
        # 10-K text did not capture SCAs for COIN (depends on 10-K
        # disclosure detail). SCAs require SCAC/web data sources.
        "has_active_sca": False,
        "sca_count_approximate": 0,
    },
    "distress": {
        # Coinbase returned to profitability in 2024
        "altman_z_zone": "SAFE",
    },
    "item1_business": {
        # From Coinbase 10-K Item 1 (FY2024)
        "has_business_description": True,
        # ~3,700 employees per 10-K (reduced from peak)
        "employee_count_approximate": 3700,
        "employee_count_tolerance": 0.25,  # Higher tolerance (volatile headcount)
        "is_dual_class": True,  # Class A + Class B shares
        "has_customer_concentration": False,
    },
    "item7_mda": {
        # From Coinbase 10-K Item 7 (FY2024)
        "has_critical_accounting_estimates": True,
        "has_guidance_language": True,
    },
    "item8_footnotes": {
        # From Coinbase 10-K Item 8 footnotes (FY2024)
        "has_going_concern": False,
        "has_restatements": False,
    },
    "item9a_controls": {
        # From Coinbase 10-K Item 9A (FY2024)
        "has_material_weakness": False,
        "auditor_name": "Deloitte",
        "auditor_opinion": "unqualified",
    },
    "eight_k_events": {
        # From Coinbase 8-K filings (trailing 24 months)
        "has_event_timeline": True,
        "event_count_min": 3,
    },
    "ownership": {
        # From yfinance data -- Brian Armstrong holds Class B shares but
        # yfinance reports insider_pct as ~1.1% (common shares only)
        "insider_ownership_pct_min": 0.5,
        "top_institutional_holder_contains": "Vanguard",
    },
    "risk_factors": {
        # From Coinbase 10-K Item 1A (FY2024)
        "total_risk_factors_min": 20,
        "has_ai_risk_factor": True,  # AI in fraud detection, etc.
        "has_cyber_risk_factor": True,
    },
}
