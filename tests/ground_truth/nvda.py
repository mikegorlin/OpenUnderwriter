"""Ground truth data for NVDA -- hand-verified from SEC filings.

Sources:
- Identity: SEC EDGAR Submissions API (CIK 1045810)
- Financials: SEC EDGAR Company Facts API (XBRL 10-K filings)
  - FY2025 10-K (filed 2025-02, fiscal year ended 2025-01-26)
  NOTE: NVIDIA's fiscal year ends in late January. The "FY2025" label
  maps to the 10-K for the year ending Jan 2025.
  Ground truth tracks the LATEST available period (FY2025).
- Governance: NVIDIA 2024 DEF 14A proxy statement
- Litigation: Stanford Securities Class Action Clearinghouse
- Distress: Computed from XBRL financial data

All financial values are in raw USD (not millions/thousands).
"""

from __future__ import annotations

from typing import Any

# NVIDIA FY2025 10-K (period ending 2025-01-26)
# CIK: 1045810
GROUND_TRUTH: dict[str, dict[str, Any]] = {
    "identity": {
        "legal_name": "NVIDIA CORP",
        "cik": "1045810",
        "sic_code": "3674",
        # SIC 3674 = Semiconductors -> TECH sector (SIC 36xx range)
        "sector": "TECH",
        "exchange": "Nasdaq",
    },
    "financials": {
        # From XBRL 10-K FY2025 (period ending 2025-01-26) -- raw USD
        # Revenue: us-gaap:Revenue
        "revenue_latest": 130497000000.0,
        # Net Income: us-gaap:NetIncomeLoss
        "net_income_latest": 72880000000.0,
        # Total Assets: us-gaap:Assets
        "total_assets": 111601000000.0,
        # Total Debt: from total_debt xbrl_concept
        "total_debt": 8462000000.0,
        # Cash: us-gaap:CashAndCashEquivalentsAtCarryingValue
        "cash_and_equivalents": 8495000000.0,
        "period_label": "FY2025",
    },
    "market": {
        # NVIDIA market cap > $500B -> MEGA tier
        "market_cap_tier": "MEGA",
    },
    "governance": {
        # NVIDIA board: 13 members per DEF 14A
        "board_size": 13,
        # CEO: Jensen Huang (co-founder, since 1993)
        "ceo_name": "Jensen Huang",
        # CFO: Colette Kress (since 2013)
        "cfo_name": "Colette Kress",
    },
    "litigation": {
        # NVIDIA has had securities class actions (gaming demand, crypto)
        "has_active_sca": True,
        "sca_count_approximate": 3,
    },
    "distress": {
        # NVIDIA has very strong financials, Z-Score well above 2.99
        "altman_z_zone": "SAFE",
    },
    "item1_business": {
        # From NVIDIA 10-K Item 1 (FY2025)
        "has_business_description": True,
        # ~36,000 employees per 10-K
        "employee_count_approximate": 36000,
        "employee_count_tolerance": 0.20,
        "is_dual_class": False,
        "has_customer_concentration": False,
    },
    "item7_mda": {
        # From NVIDIA 10-K Item 7 (FY2025)
        "has_critical_accounting_estimates": True,
        "has_guidance_language": True,
    },
    "item8_footnotes": {
        # From NVIDIA 10-K Item 8 footnotes (FY2025)
        "has_going_concern": False,
        "has_restatements": False,
    },
    "item9a_controls": {
        # From NVIDIA 10-K Item 9A (FY2025)
        "has_material_weakness": False,
        "auditor_name": "PricewaterhouseCoopers",
        "auditor_opinion": "unqualified",
    },
    "eight_k_events": {
        # From NVIDIA 8-K filings (trailing 24 months)
        "has_event_timeline": True,
        "event_count_min": 3,
    },
    "ownership": {
        # From yfinance data -- Jensen Huang ~3.5%
        "insider_ownership_pct_min": 1.0,
        "top_institutional_holder_contains": "Vanguard",
    },
    "risk_factors": {
        # From NVIDIA 10-K Item 1A (FY2025)
        "total_risk_factors_min": 15,
        "has_ai_risk_factor": True,
        "has_cyber_risk_factor": True,
    },
}
