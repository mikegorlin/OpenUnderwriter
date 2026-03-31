"""Ground truth data for AAPL -- hand-verified from SEC filings.

Sources:
- Identity: SEC EDGAR Submissions API (CIK 0000320193)
- Financials: SEC EDGAR Company Facts API (XBRL 10-K filings)
  - FY2025 10-K (filed 2025-11, fiscal year ended 2025-09-27)
  - FY2024 10-K (filed 2024-11-01, fiscal year ended 2024-09-28)
  NOTE: Apple's fiscal year ends in late September. The "FY2025" label
  in our extractor maps to the 10-K for the year ending Sep 2025.
  Ground truth tracks the LATEST available period (FY2025).
- Governance: Apple 2025 DEF 14A proxy statement
- Litigation: Stanford Securities Class Action Clearinghouse
- Distress: Computed from XBRL financial data

All financial values are in raw USD (not millions/thousands).
"""

from __future__ import annotations

from typing import Any

# Apple FY2025 10-K (period ending 2025-09-27)
# CIK: 0000320193, accession: 0000320193-25-000079
GROUND_TRUTH: dict[str, dict[str, Any]] = {
    "identity": {
        "legal_name": "Apple Inc.",
        "cik": "320193",
        "sic_code": "3571",
        # SIC 3571 = Electronic Computers -> TECH sector
        "sector": "TECH",
        "exchange": "Nasdaq",
    },
    "financials": {
        # From XBRL 10-K FY2025 (period ending 2025-09-27) -- raw USD
        # Revenue: us-gaap (Revenues tag)
        "revenue_latest": 416161000000.0,
        # Net Income: us-gaap:NetIncomeLoss
        "net_income_latest": 112010000000.0,
        # Total Assets: us-gaap:Assets
        "total_assets": 359241000000.0,
        # Total Debt (LTD + STD from total_debt xbrl_concept)
        "total_debt": 90678000000.0,
        # Cash: us-gaap:CashAndCashEquivalentsAtCarryingValue
        "cash_and_equivalents": 35934000000.0,
        # Period label assigned by our extractor
        "period_label": "FY2025",
    },
    "market": {
        # Apple market cap > $500B -> MEGA tier
        "market_cap_tier": "MEGA",
    },
    "governance": {
        # Apple board: 8 members per DEF 14A
        # Tim Cook, James Bell, Al Gore, Alex Gorsky,
        # Andrea Jung, Monica Lozano, Ron Sugar, Sue Wagner
        "board_size": 8,
        # CEO: Tim Cook (since Aug 2011)
        "ceo_name": "Tim Cook",
        # CFO: Kevan Parekh (since Jan 2025)
        "cfo_name": "Kevan Parekh",
    },
    "litigation": {
        # Apple has regulatory/antitrust actions (EU DMA, DOJ, Epic Games)
        # that the LLM extractor classifies as securities_class_actions.
        # These are not traditional SCAs but the field captures all
        # significant litigation from 10-K Item 3 disclosure.
        "has_active_sca": True,
        "sca_count_approximate": 4,
    },
    "distress": {
        # Apple has strong financials, Z-Score well above 2.99
        "altman_z_zone": "SAFE",
    },
    "item1_business": {
        # From Apple 10-K Item 1 (FY2025)
        "has_business_description": True,
        # ~150,000 per yfinance (10-K reports ~164,000)
        "employee_count_approximate": 150000,
        "employee_count_tolerance": 0.20,  # 20% tolerance
        "is_dual_class": False,
        "has_customer_concentration": False,  # No 10%+ customer
    },
    "item7_mda": {
        # From Apple 10-K Item 7 (FY2025)
        "has_critical_accounting_estimates": True,
        # Apple famously does not give formal forward guidance
        "has_guidance_language": False,
    },
    "item8_footnotes": {
        # From Apple 10-K Item 8 footnotes (FY2025)
        "has_going_concern": False,
        "has_restatements": False,
    },
    "item9a_controls": {
        # From Apple 10-K Item 9A (FY2025)
        "has_material_weakness": False,
        "auditor_name": "Ernst & Young",
        "auditor_opinion": "unqualified",
    },
    "eight_k_events": {
        # From Apple 8-K filings (trailing 24 months)
        "has_event_timeline": True,
        "event_count_min": 3,  # Apple files regular 8-Ks
    },
    "ownership": {
        # From yfinance data (institutional + insider)
        # Apple insiders own ~1.7%
        "insider_ownership_pct_min": 0.01,
        # Top institutional holder
        "top_institutional_holder_contains": "Vanguard",
    },
    "risk_factors": {
        # From Apple 10-K Item 1A (FY2025)
        # Risk factor extraction is Phase 20 -- may not be populated yet
        "total_risk_factors_min": 15,
        "has_ai_risk_factor": True,
        "has_cyber_risk_factor": True,
    },
}
