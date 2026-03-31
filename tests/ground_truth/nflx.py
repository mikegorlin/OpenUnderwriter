"""Ground truth data for NFLX -- hand-verified from SEC filings.

Sources:
- Identity: SEC EDGAR Submissions API (CIK 1065280)
- Financials: SEC EDGAR Company Facts API (XBRL 10-K filings)
  - FY2024 10-K (filed 2025-01, fiscal year ended 2024-12-31)
  Ground truth tracks the LATEST available period (FY2024).
- Governance: Netflix 2024 DEF 14A proxy statement
- Litigation: Stanford Securities Class Action Clearinghouse
- Distress: Computed from XBRL financial data

SECTOR CLASSIFICATION: Netflix SIC code is 7841 (Videotape Rental/Services).
This maps to Communication Services (GICS) / Entertainment.
The previous mapping incorrectly classified it as Industrials because
SIC 78xx fell in the (74,79) range mapped to INDU.

All financial values are in raw USD (not millions/thousands).
"""

from __future__ import annotations

from typing import Any

GROUND_TRUTH: dict[str, dict[str, Any]] = {
    "identity": {
        "legal_name": "NETFLIX INC",
        "cik": "1065280",
        "sic_code": "7841",
        "sector": "COMM",  # SIC 7841 -> Communication Services (fixed)
        "exchange": "Nasdaq",
    },
    "financials": {
        # From XBRL 10-K FY2024 (period ending 2024-12-31) -- raw USD
        # NOTE: Netflix FY2024 filing includes full-year 2024 data.
        # Extracted values reflect latest available XBRL data.
        "revenue_latest": 45183036000.0,  # $45.2B (FY2024 extracted)
        "net_income_latest": 10981201000.0,  # $11.0B
        "total_assets": 55596993000.0,  # $55.6B
        "cash_and_equivalents": 9033681000.0,  # $9.0B
        "period_label": "FY2024",
    },
    "market": {
        "market_cap_tier": "MEGA",  # Netflix >$200B
    },
    "governance": {
        "ceo_name": "Ted Sarandos",  # Co-CEO
        "board_size": 11,
    },
    "litigation": {
        "has_active_sca": False,  # No current active SCAs
        "sca_count_approximate": 0,
    },
    "distress": {
        "altman_z_zone": "SAFE",
    },
    "item1_business": {
        "has_business_description": True,
        "employee_count_approximate": 14000,  # ~14,000
        "employee_count_tolerance": 0.20,
        "is_dual_class": False,
    },
    "item7_mda": {
        "has_critical_accounting_estimates": True,
        "has_guidance_language": True,
    },
    "item8_footnotes": {
        "has_going_concern": False,
        "has_restatements": False,
    },
    "item9a_controls": {
        "has_material_weakness": False,
        "auditor_name": "Ernst & Young",  # EY is Netflix auditor
        "auditor_opinion": "unqualified",
    },
    "eight_k_events": {
        "has_event_timeline": True,
        "event_count_min": 3,
    },
    "ownership": {
        "insider_ownership_pct_min": 0.01,
        "top_institutional_holder_contains": "Vanguard",
    },
    "risk_factors": {
        "total_risk_factors_min": 10,
        "has_ai_risk_factor": True,  # Netflix uses AI for recommendations
        "has_cyber_risk_factor": True,
    },
    "output_facts": {
        "employee_count_min": 10000,
        "employee_count_max": 20000,
        "sector_display": "Communication Services",
        "sector_not": ["Industrials"],
        "industry_display_contains": "Entertainment",
        "auditor_name_contains": "Ernst & Young",
        "shares_no_dollar_prefix": True,
    },
}
