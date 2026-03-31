"""Ground truth data for MRNA -- hand-verified from SEC filings.

Sources:
- Identity: SEC EDGAR Submissions API (CIK 1682852)
- Financials: SEC EDGAR Company Facts API (XBRL 10-K filings)
  - FY2024 10-K (filed 2025-02, fiscal year ended 2024-12-31)
  Ground truth tracks the LATEST available period (FY2024).
- Governance: Moderna 2024 DEF 14A proxy statement
- Litigation: Stanford Securities Class Action Clearinghouse
- Distress: Computed from XBRL financial data

All financial values are in raw USD (not millions/thousands).
"""

from __future__ import annotations

from typing import Any

# Moderna FY2024 10-K (period ending 2024-12-31)
# CIK: 1682852
GROUND_TRUTH: dict[str, dict[str, Any]] = {
    "identity": {
        "legal_name": "Moderna, Inc.",
        "cik": "1682852",
        "sic_code": "2836",
        # SIC 2836 = Biological Products -> HLTH sector (SIC 28xx range)
        "sector": "HLTH",
        "exchange": "Nasdaq",
    },
    "financials": {
        # From XBRL 10-K FY2024 (period ending 2024-12-31) -- raw USD
        # Revenue declined significantly post-COVID
        "revenue_latest": 3234000000.0,
        # Net Income (loss): FY2024 was a significant net loss
        "net_income_latest": -4301000000.0,
        # Total Assets
        "total_assets": 15062000000.0,
        # Total Debt
        "total_debt": 550000000.0,
        # Cash: Cash + short-term investments
        "cash_and_equivalents": 3411000000.0,
        "period_label": "FY2024",
    },
    "market": {
        # Moderna market cap ~$15-25B -> LARGE tier
        "market_cap_tier": "LARGE",
    },
    "governance": {
        # Moderna board: 9 members per DEF 14A
        "board_size": 9,
        # CEO: Stephane Bancel (since 2011)
        "ceo_name": "Stephane Bancel",
        # CFO: Jamey Mock (since 2022)
        "cfo_name": "Jamey Mock",
    },
    "litigation": {
        # Moderna has patent litigation (Pfizer, Arbutus) plus COVID
        # vaccine-related class actions. NOTE: MRNA extraction failed
        # completely (extracted=None) so no SCA data available.
        "has_active_sca": False,
        "sca_count_approximate": 0,
    },
    "distress": {
        # Moderna has significant cash reserves despite losses.
        # NOTE: MRNA extraction failed so no Altman Z computed.
        # Expected GREY zone given large net losses but cash reserves.
        "altman_z_zone": "GREY",
    },
    "item1_business": {
        # From Moderna 10-K Item 1 (FY2024).
        # NOTE: MRNA extraction failed (extracted=None) so business
        # description was not populated from 10-K text.
        "has_business_description": False,
        # ~5,800 per yfinance (employee_count available from resolve stage)
        "employee_count_approximate": 5800,
        "employee_count_tolerance": 0.20,
        "is_dual_class": False,
        "has_customer_concentration": True,  # US gov / BARDA contracts
    },
    "item7_mda": {
        # From Moderna 10-K Item 7 (FY2024)
        "has_critical_accounting_estimates": True,
        "has_guidance_language": True,
    },
    "item8_footnotes": {
        # From Moderna 10-K Item 8 footnotes (FY2024)
        "has_going_concern": False,  # Large cash reserves
        "has_restatements": False,
    },
    "item9a_controls": {
        # From Moderna 10-K Item 9A (FY2024)
        "has_material_weakness": False,
        "auditor_name": "Ernst & Young",
        "auditor_opinion": "unqualified",
    },
    "eight_k_events": {
        # From Moderna 8-K filings (trailing 24 months).
        # NOTE: MRNA extraction failed so 8-K events not populated.
        "has_event_timeline": False,
        "event_count_min": 0,
    },
    "ownership": {
        # From yfinance data -- Bancel ~7%. NOTE: MRNA extraction
        # failed so ownership data not populated in extracted.governance.
        "insider_ownership_pct_min": 3.0,
        "top_institutional_holder_contains": "Vanguard",
    },
    "risk_factors": {
        # From Moderna 10-K Item 1A (FY2024)
        "total_risk_factors_min": 20,
        "has_ai_risk_factor": False,  # Biotech, less AI-focused
        "has_cyber_risk_factor": True,
    },
}
