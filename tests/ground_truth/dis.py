"""Ground truth data for DIS -- hand-verified from SEC filings.

Sources:
- Identity: SEC EDGAR Submissions API (CIK 1744489)
- Financials: SEC EDGAR Company Facts API (XBRL 10-K filings)
  - FY2025 10-K (filed 2025-11, fiscal year ended 2025-09-27)
  - FY2024 10-K (filed 2024-11, fiscal year ended 2024-09-28)
  NOTE: Disney's fiscal year ends in late September/early October.
  Ground truth tracks the LATEST available period (FY2025).
- Governance: Walt Disney 2024 DEF 14A proxy statement
- Litigation: Stanford Securities Class Action Clearinghouse
- Distress: Computed from XBRL financial data

All financial values are in raw USD (not millions/thousands).
"""

from __future__ import annotations

from typing import Any

# Walt Disney FY2025 10-K (period ending 2025-09-27)
# CIK: 1744489
GROUND_TRUTH: dict[str, dict[str, Any]] = {
    "identity": {
        "legal_name": "Walt Disney Co",
        "cik": "1744489",
        # SEC EDGAR now classifies Disney as SIC 7990 (Amusement/Recreation)
        # rather than 4841 (Cable TV) after org restructuring
        "sic_code": "7990",
        # SIC 7990 = Services-Amusement & Recreation -> INDU sector
        "sector": "INDU",
        "exchange": "NYSE",
    },
    "financials": {
        # From XBRL 10-K FY2025 (period ending 2025-09-27) -- raw USD
        # Revenue: us-gaap:Revenues
        "revenue_latest": 94425000000.0,
        # Net Income: us-gaap:NetIncomeLoss
        "net_income_latest": 12404000000.0,
        # Total Assets: us-gaap:Assets
        "total_assets": 197514000000.0,
        # Total Debt
        "total_debt": 42026000000.0,
        # Cash: us-gaap:CashAndCashEquivalentsAtCarryingValue
        "cash_and_equivalents": 5695000000.0,
        "period_label": "FY2025",
    },
    "market": {
        # Disney market cap ~$170-210B -> LARGE tier
        "market_cap_tier": "LARGE",
    },
    "governance": {
        # Disney board: 12 members per DEF 14A
        "board_size": 12,
        # CEO: Bob Iger (returned Nov 2022)
        "ceo_name": "Bob Iger",
        # CFO: Hugh Johnston (since Dec 2023)
        "cfo_name": "Hugh Johnston",
    },
    "litigation": {
        # Disney has had some shareholder derivative suits
        "has_active_sca": False,
        "sca_count_approximate": 0,
    },
    "distress": {
        # Disney has massive total assets ($197B) and significant debt ($42B).
        # The original Altman Z model yields a low score (1.73) due to
        # asset-heavy entertainment/media business model. This is a known
        # limitation of the original Z-Score for non-manufacturing firms.
        "altman_z_zone": "DISTRESS",
    },
    "item1_business": {
        # From Disney 10-K Item 1 (FY2024)
        "has_business_description": True,
        # ~175,560 per yfinance (FY2025); 10-K may report higher
        "employee_count_approximate": 175000,
        "employee_count_tolerance": 0.25,
        "is_dual_class": False,
        "has_customer_concentration": False,
    },
    "item7_mda": {
        # From Disney 10-K Item 7 (FY2024)
        "has_critical_accounting_estimates": True,
        "has_guidance_language": True,
    },
    "item8_footnotes": {
        # From Disney 10-K Item 8 footnotes (FY2024)
        "has_going_concern": False,
        "has_restatements": False,
    },
    "item9a_controls": {
        # From Disney 10-K Item 9A (FY2024)
        "has_material_weakness": False,
        "auditor_name": "PricewaterhouseCoopers",
        "auditor_opinion": "unqualified",
    },
    "eight_k_events": {
        # From Disney 8-K filings (trailing 24 months)
        "has_event_timeline": True,
        "event_count_min": 3,
    },
    "ownership": {
        # From yfinance data -- insiders own <1%
        "insider_ownership_pct_min": 0.01,
        "top_institutional_holder_contains": "Vanguard",
    },
    "risk_factors": {
        # From Disney 10-K Item 1A (FY2024)
        "total_risk_factors_min": 10,
        "has_ai_risk_factor": True,
        "has_cyber_risk_factor": True,
    },
}
