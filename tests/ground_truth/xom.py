"""Ground truth data for XOM -- hand-verified from SEC filings.

Sources:
- Identity: SEC EDGAR Submissions API (CIK 34088)
- Financials: SEC EDGAR Company Facts API (XBRL 10-K filings)
  - FY2024 10-K (filed 2025-02, fiscal year ended 2024-12-31)
  Ground truth tracks the LATEST available period (FY2024).
- Governance: Exxon Mobil 2024 DEF 14A proxy statement
- Litigation: Stanford Securities Class Action Clearinghouse
- Distress: Computed from XBRL financial data

All financial values are in raw USD (not millions/thousands).
"""

from __future__ import annotations

from typing import Any

# Exxon Mobil FY2024 10-K (period ending 2024-12-31)
# CIK: 34088
GROUND_TRUTH: dict[str, dict[str, Any]] = {
    "identity": {
        "legal_name": "EXXON MOBIL CORP",
        "cik": "34088",
        # SEC EDGAR classifies XOM under SIC 2911 (Petroleum Refining)
        # rather than 1311 (Crude Petroleum). Both are valid for an
        # integrated oil company; 2911 reflects downstream operations.
        "sic_code": "2911",
        # SIC 2911 = Petroleum Refining -> ENGY sector (SIC 29xx range)
        "sector": "ENGY",
        "exchange": "NYSE",
    },
    "financials": {
        # From XBRL 10-K FY2024 (period ending 2024-12-31) -- raw USD
        # Revenue: us-gaap:Revenues
        "revenue_latest": 339250000000.0,
        # Net Income: us-gaap:NetIncomeLoss
        "net_income_latest": 33680000000.0,
        # Total Assets: us-gaap:Assets
        "total_assets": 453475000000.0,
        # Total Debt
        "total_debt": 36755000000.0,
        # Cash: us-gaap:CashAndCashEquivalentsAtCarryingValue
        "cash_and_equivalents": 23290000000.0,
        "period_label": "FY2024",
    },
    "market": {
        # Exxon market cap > $500B -> MEGA tier
        "market_cap_tier": "MEGA",
    },
    "governance": {
        # Exxon board: 12 members per DEF 14A
        "board_size": 12,
        # CEO: Darren Woods (since 2017)
        "ceo_name": "Darren Woods",
        # CFO: Kathryn Mikells (since 2021)
        "cfo_name": "Kathryn Mikells",
    },
    "litigation": {
        # Climate change lawsuits + shareholder derivative actions.
        # NOTE: LLM extraction from 10-K text did not capture SCAs for
        # XOM. Climate litigation is disclosed differently than traditional
        # securities class actions. SCAs require SCAC/web data sources.
        "has_active_sca": False,
        "sca_count_approximate": 0,
    },
    "distress": {
        # Exxon has strong financials, Z-Score above 2.99
        "altman_z_zone": "SAFE",
    },
    "item1_business": {
        # From Exxon 10-K Item 1 (FY2024)
        "has_business_description": True,
        # ~61,500 employees per 10-K (post-Pioneer acquisition).
        # NOTE: yfinance may not return employee count for XOM.
        "employee_count_approximate": 61500,
        "employee_count_tolerance": 0.20,
        "is_dual_class": False,
        "has_customer_concentration": False,
    },
    "item7_mda": {
        # From Exxon 10-K Item 7 (FY2024)
        "has_critical_accounting_estimates": True,
        "has_guidance_language": True,
    },
    "item8_footnotes": {
        # From Exxon 10-K Item 8 footnotes (FY2024)
        "has_going_concern": False,
        "has_restatements": False,
    },
    "item9a_controls": {
        # From Exxon 10-K Item 9A (FY2024)
        "has_material_weakness": False,
        "auditor_name": "PricewaterhouseCoopers",
        "auditor_opinion": "unqualified",
    },
    "eight_k_events": {
        # From Exxon 8-K filings (trailing 24 months)
        "has_event_timeline": True,
        "event_count_min": 3,
    },
    "ownership": {
        # From yfinance data -- insiders own <1%
        "insider_ownership_pct_min": 0.01,
        "top_institutional_holder_contains": "Vanguard",
    },
    "risk_factors": {
        # From Exxon 10-K Item 1A (FY2024)
        "total_risk_factors_min": 10,
        "has_ai_risk_factor": False,  # Oil & gas, not AI-focused
        "has_cyber_risk_factor": True,
    },
    "output_facts": {
        # Document-level validation facts (checked against rendered .docx)
        "employee_count_min": 50000,
        "employee_count_max": 80000,
        "sector_display": "Energy",
        "sector_not": ["Industrials", "Technology"],
        "auditor_name_contains": "PricewaterhouseCoopers",
        "shares_no_dollar_prefix": True,  # Shares Outstanding should NOT have $
        "tier_expected_range": ["WANT", "WRITE", "WIN"],
    },
}
