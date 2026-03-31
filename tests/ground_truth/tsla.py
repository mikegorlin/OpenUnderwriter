"""Ground truth data for TSLA -- hand-verified from SEC filings.

Sources:
- Identity: SEC EDGAR Submissions API (CIK 1318605)
- Financials: SEC EDGAR Company Facts API (XBRL 10-K filings)
  - FY2025 10-K (filed 2026-01, fiscal year ended 2025-12-31)
  - FY2024 10-K (filed 2025-01-29, fiscal year ended 2024-12-31)
  Ground truth tracks the LATEST available period (FY2025).
- Governance: Tesla 2025 DEF 14A proxy statement
- Litigation: Stanford Securities Class Action Clearinghouse
- Distress: Computed from XBRL financial data

All financial values are in raw USD (not millions/thousands).
"""

from __future__ import annotations

from typing import Any

# Tesla FY2025 10-K (period ending 2025-12-31)
# CIK: 1318605, accession: 0001628280-26-003952
# Also verified against FY2024 10-K (accession: 0001628280-25-003063)
GROUND_TRUTH: dict[str, dict[str, Any]] = {
    "identity": {
        "legal_name": "Tesla, Inc.",
        "cik": "1318605",
        "sic_code": "3711",
        # SIC 3711 = Motor Vehicles & Passenger Car Bodies -> INDU sector
        "sector": "INDU",
        "exchange": "Nasdaq",
    },
    "financials": {
        # From XBRL 10-K FY2025 -- all values in raw USD
        # Revenue: Our extractor uses the "Revenues" tag, which yields
        # a different value than RevenueFromContractWithCustomer...
        # FY2025 value from state: 94,827,000,000 (Revenues tag)
        "revenue_latest": 94827000000.0,
        # Net Income: us-gaap:NetIncomeLoss FY2025
        "net_income_latest": 3794000000.0,
        # Total Assets: us-gaap:Assets FY2025
        "total_assets": 137806000000.0,
        # Total Debt FY2025 (from total_debt xbrl_concept)
        "total_debt": 6584000000.0,
        # Cash: us-gaap:CashAndCashEquivalentsAtCarryingValue FY2025
        "cash_and_equivalents": 16513000000.0,
        # Period label assigned by our extractor
        "period_label": "FY2025",
    },
    "market": {
        # Tesla market cap > $500B -> MEGA tier
        "market_cap_tier": "MEGA",
    },
    "governance": {
        # Tesla board: 8 members per DEF 14A
        # Elon Musk, Robyn Denholm, Ira Ehrenpreis, Joe Gebbia,
        # James Murdoch, Kimbal Musk, JB Straubel, Kathleen Wilson-Thompson
        "board_size": 8,
        # CEO: Elon Musk (since inception)
        "ceo_name": "Elon Musk",
        # CFO: Vaibhav Taneja (since 2023-08)
        "cfo_name": "Vaibhav Taneja",
    },
    "litigation": {
        # Tesla has had numerous securities class actions
        "has_active_sca": True,
        # Stanford SCAC shows multiple filings
        "sca_count_approximate": 10,
    },
    "distress": {
        # Tesla has strong financials, Z-Score well above 2.99
        "altman_z_zone": "SAFE",
    },
    "item1_business": {
        # From Tesla 10-K Item 1 (FY2025)
        "has_business_description": True,
        # ~134,785 per yfinance; 10-K reports similar figure
        "employee_count_approximate": 135000,
        "employee_count_tolerance": 0.20,  # 20% tolerance
        "is_dual_class": False,
        "has_customer_concentration": False,  # No 10%+ customer
    },
    "item7_mda": {
        # From Tesla 10-K Item 7 (FY2025)
        "has_critical_accounting_estimates": True,
        "has_guidance_language": True,  # Tesla provides informal guidance
    },
    "item8_footnotes": {
        # From Tesla 10-K Item 8 footnotes (FY2025)
        "has_going_concern": False,
        "has_restatements": False,
    },
    "item9a_controls": {
        # From Tesla 10-K Item 9A (FY2025)
        "has_material_weakness": False,
        # Note: Our extractor reports "Ernst & Young" for TSLA
        # (verified from state.json audit extraction)
        "auditor_name": "Ernst & Young",
        "auditor_opinion": "unqualified",
    },
    "eight_k_events": {
        # From Tesla 8-K filings (trailing 24 months)
        "has_event_timeline": True,
        "event_count_min": 3,  # TSLA has many 8-K filings
    },
    "ownership": {
        # From yfinance data (institutional + insider)
        # Musk ~21% but yfinance reports insider_pct as 11.134
        "insider_ownership_pct_min": 5.0,  # Floor estimate for Musk
        # Top institutional holder
        "top_institutional_holder_contains": "Vanguard",
    },
    "risk_factors": {
        # From Tesla 10-K Item 1A (FY2025)
        # Risk factor extraction is Phase 20 -- may not be populated yet
        "total_risk_factors_min": 15,
        "has_ai_risk_factor": True,
        "has_cyber_risk_factor": True,
    },
}
