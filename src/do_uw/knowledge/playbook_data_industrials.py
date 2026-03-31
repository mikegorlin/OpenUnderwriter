"""Industry playbook data for Industrials, REITs, and Transportation.

Split from playbook_data.py for 500-line compliance. Contains the
INDUSTRIALS_MFG, REITS_REAL_ESTATE, and TRANSPORTATION_RAIL playbook
definitions, mined from Old Underwriter industry supplement files.
"""

from __future__ import annotations

from typing import Any


def _check(
    signal_id: str,
    name: str,
    section: int,
    pillar: str,
    severity: str,
    playbook_id: str,
    *,
    execution_mode: str = "AUTO",
    threshold_type: str = "qualitative",
    required_data: list[str] | None = None,
    data_locations: list[str] | None = None,
    scoring_factor: str | None = None,
    output_section: str = "SECT3",
) -> dict[str, Any]:
    """Build a compact check dict for playbook inclusion."""
    return {
        "id": signal_id,
        "name": name,
        "section": section,
        "pillar": pillar,
        "severity": severity,
        "execution_mode": execution_mode,
        "threshold_type": threshold_type,
        "required_data": required_data or ["sec_filings"],
        "data_locations": data_locations or ["extracted.financials"],
        "scoring_factor": scoring_factor,
        "output_section": output_section,
        "metadata_json": f'{{"playbook_id": "{playbook_id}"}}',
    }


INDUSTRIALS_MFG_PLAYBOOK: dict[str, Any] = {
    "id": "INDUSTRIALS_MFG",
    "name": "Industrials / Manufacturing",
    "description": (
        "Industry playbook for industrial conglomerates, machinery, "
        "aerospace, and electrical equipment companies covering product "
        "safety, cyclical revenue manipulation, supply chain/tariff "
        "disclosure, and asbestos/environmental legacy liabilities."
    ),
    "sic_ranges": [
        {"low": 3400, "high": 3499},
        {"low": 3500, "high": 3570},
        {"low": 3580, "high": 3599},
        {"low": 3700, "high": 3799},
    ],
    "naics_prefixes": ["3321", "3327", "3331", "3332", "3333", "3336", "3364"],
    "industry_checks": [
        _check("MFG.SAFETY.product_defect",
               "Product defect concealment cascading to securities liability",
               6, "LITIGATION", "HIGH", "INDUSTRIALS_MFG",
               required_data=["sec_filings", "web_search"],
               scoring_factor="F1_litigation"),
        _check("MFG.CYCLE.revenue_manipulation",
               "Cyclical revenue manipulation (channel stuffing, bill-and-hold)",
               3, "FINANCIAL_REPORTING", "HIGH", "INDUSTRIALS_MFG",
               required_data=["sec_filings", "xbrl_data"],
               scoring_factor="F3_financial_health"),
        _check("MFG.SUPPLY.tariff_disclosure",
               "Supply chain disruption or tariff impact disclosure failure",
               3, "FINANCIAL_REPORTING", "HIGH", "INDUSTRIALS_MFG",
               required_data=["sec_filings", "web_search"],
               scoring_factor="F8_emerging_risks"),
        _check("MFG.LEGACY.asbestos_env",
               "Asbestos or environmental remediation legacy liability exposure",
               6, "LITIGATION", "HIGH", "INDUSTRIALS_MFG",
               required_data=["sec_filings", "web_search"],
               scoring_factor="F1_litigation"),
        _check("MFG.ACCT.expense_capitalization",
               "Operating expense capitalization (CapEx/depreciation >2.0x)",
               3, "FINANCIAL_REPORTING", "MEDIUM", "INDUSTRIALS_MFG",
               required_data=["sec_filings", "xbrl_data"],
               scoring_factor="F3_financial_health"),
        _check("MFG.SEGMENT.accounting",
               "Conglomerate segment accounting manipulation or intercompany schemes",
               3, "FINANCIAL_REPORTING", "HIGH", "INDUSTRIALS_MFG",
               scoring_factor="F3_financial_health"),
        _check("MFG.WARRANTY.reserve_decline",
               "Warranty reserve declining while sales or claims grow",
               3, "FINANCIAL_REPORTING", "MEDIUM", "INDUSTRIALS_MFG",
               required_data=["sec_filings", "xbrl_data"],
               scoring_factor="F3_financial_health"),
        _check("MFG.RECALL.cpsc_nhtsa",
               "Active CPSC or NHTSA product recall or investigation",
               5, "REGULATORY", "HIGH", "INDUSTRIALS_MFG",
               required_data=["web_search"],
               scoring_factor="F8_emerging_risks"),
        _check("MFG.CYCLE.backlog_decline",
               "Backlog declining while maintaining aggressive guidance",
               3, "FINANCIAL_REPORTING", "MEDIUM", "INDUSTRIALS_MFG",
               scoring_factor="F3_financial_health"),
        _check("MFG.QUALITY.exec_turnover",
               "Quality or safety executive turnover indicating systemic issues",
               4, "GOVERNANCE", "MEDIUM", "INDUSTRIALS_MFG",
               data_locations=["extracted.governance"],
               scoring_factor="F5_governance"),
    ],
    "risk_patterns": ["product_safety_securities_cascade", "cyclical_earnings_manipulation"],
    "claim_theories": [
        {"id": "MFG_CT1", "name": "Product defect concealment",
         "description": (
             "Engineering knew of defects but management concealed "
             "from regulators and investors"),
         "factors_affected": ["F1_litigation", "F8_emerging_risks"],
         "historical_examples": [
             "Boeing 737 MAX $237.5M+", "3M $6B", "GM $900M"]},
        {"id": "MFG_CT2", "name": "Cyclical revenue recognition fraud",
         "description": (
             "Channel stuffing or percentage-of-completion "
             "manipulation during downcycles"),
         "factors_affected": ["F3_financial_health"],
         "historical_examples": [
             "GE $362.5M (2025)", "Tyco $3.2B (2007)"]},
        {"id": "MFG_CT3", "name": "Supply chain/tariff failure",
         "description": (
             "Material tariff impacts not disclosed while "
             "guidance maintained"),
         "factors_affected": ["F3_financial_health", "F8_emerging_risks"],
         "historical_examples": ["Mobileye (2024)"]},
        {"id": "MFG_CT4", "name": "Legacy liability understatement",
         "description": (
             "Asbestos, PFAS, or environmental costs "
             "systematically understated"),
         "factors_affected": ["F1_litigation"],
         "historical_examples": [
             "3M PFAS $12.5B (2024)", "Honeywell asbestos"]},
    ],
    "meeting_questions": [
        {"question": (
             "What product recalls or CPSC/NHTSA investigations "
             "have occurred in the past 5 years?"),
         "category": "Product Safety", "priority": 1},
        {"question": (
             "What is your tariff exposure and supply chain "
             "concentration risk?"),
         "category": "Supply Chain", "priority": 1},
        {"question": (
             "What legacy liabilities (asbestos, environmental) "
             "exist and how are reserves trending?"),
         "category": "Legacy Risk", "priority": 2},
        {"question": (
             "What is your CapEx/depreciation ratio and "
             "maintenance spending trend?"),
         "category": "Financial Quality", "priority": 2},
        {"question": (
             "Where are we in the equipment/order cycle and "
             "how does backlog compare?"),
         "category": "Cyclical Risk", "priority": 3},
    ],
    "scoring_adjustments": {"F1_litigation": 1.2, "F3_financial_health": 1.1},
}

REITS_REAL_ESTATE_PLAYBOOK: dict[str, Any] = {
    "id": "REITS_REAL_ESTATE",
    "name": "REITs / Real Estate",
    "description": (
        "Industry playbook for real estate investment trusts covering "
        "AFFO methodology divergence, external management conflicts, "
        "dividend payout sustainability, office sector distress, and "
        "mREIT interest rate sensitivity."
    ),
    "sic_ranges": [
        {"low": 6510, "high": 6553},
    ],
    "naics_prefixes": ["5311", "5312", "5313"],
    "industry_checks": [
        _check("REIT.AFFO.methodology",
               "AFFO methodology divergence from NAREIT guidelines or peers",
               3, "FINANCIAL_REPORTING", "HIGH", "REITS_REAL_ESTATE",
               scoring_factor="F3_financial_health"),
        _check("REIT.DIV.payout_sustainability",
               "AFFO payout ratio >100% indicating unsustainable dividends",
               3, "FINANCIAL_REPORTING", "HIGH", "REITS_REAL_ESTATE",
               required_data=["sec_filings", "xbrl_data"],
               scoring_factor="F3_financial_health"),
        _check("REIT.MGMT.external_conflicts",
               "External management with AUM-based fees and related party transactions",
               4, "GOVERNANCE", "HIGH", "REITS_REAL_ESTATE",
               data_locations=["extracted.governance"],
               scoring_factor="F5_governance"),
        _check("REIT.OFFICE.concentration",
               "Office sector concentration >50% (Class B/C especially distressed)",
               2, "BUSINESS_PROFILE", "HIGH", "REITS_REAL_ESTATE",
               scoring_factor="F8_emerging_risks"),
        _check("REIT.DEBT.maturity_wall",
               "Debt maturing within 24 months >30% of total (refinancing risk)",
               3, "FINANCIAL_REPORTING", "HIGH", "REITS_REAL_ESTATE",
               required_data=["sec_filings", "xbrl_data"],
               scoring_factor="F3_financial_health"),
        _check("REIT.MREIT.book_value_decline",
               "mREIT book value decline >15% in 1 year (capital destruction)",
               3, "FINANCIAL_REPORTING", "HIGH", "REITS_REAL_ESTATE",
               scoring_factor="F3_financial_health"),
        _check("REIT.TENANT.concentration",
               "Single tenant >10% or pre-revenue biotech concentration",
               2, "BUSINESS_PROFILE", "MEDIUM", "REITS_REAL_ESTATE",
               scoring_factor="F8_emerging_risks"),
        _check("REIT.NOI.same_store_decline",
               "Same-store NOI negative for 2+ consecutive quarters",
               3, "FINANCIAL_REPORTING", "MEDIUM", "REITS_REAL_ESTATE",
               scoring_factor="F3_financial_health"),
        _check("REIT.NAV.nontrade_risk",
               "Non-traded REIT structure with illiquidity and NAV manipulation risk",
               3, "FINANCIAL_REPORTING", "HIGH", "REITS_REAL_ESTATE",
               scoring_factor="F3_financial_health"),
        _check("REIT.DIV.recent_cut",
               "Dividend cut or suspension within past 24 months",
               3, "FINANCIAL_REPORTING", "MEDIUM", "REITS_REAL_ESTATE",
               required_data=["sec_filings", "web_search"],
               scoring_factor="F3_financial_health"),
    ],
    "risk_patterns": ["affo_manipulation_cascade", "office_sector_structural_decline"],
    "claim_theories": [
        {"id": "REIT_CT1", "name": "AFFO manipulation",
         "description": (
             "Inflating AFFO through non-standard adjustments "
             "to appear sustainable"),
         "factors_affected": ["F3_financial_health"],
         "historical_examples": [
             "ARCP $1.025B (2020)", "CTO Realty (2025)"]},
        {"id": "REIT_CT2", "name": "External mgmt self-dealing",
         "description": (
             "External manager acquiring properties from "
             "controlled entities at inflated prices"),
         "factors_affected": ["F5_governance"],
         "historical_examples": [
             "ARCP/Schorsch", "Cole Credit $120M (2015)"]},
        {"id": "REIT_CT3", "name": "Occupancy/impairment concealment",
         "description": (
             "Failing to disclose occupancy deterioration or "
             "delaying impairment recognition"),
         "factors_affected": ["F3_financial_health", "F8_emerging_risks"],
         "historical_examples": [
             "Alexandria RE (2025)", "OPI bankruptcy (2025)"]},
    ],
    "meeting_questions": [
        {"question": (
             "How do you calculate AFFO and what adjustments "
             "differ from NAREIT guidelines?"),
         "category": "Accounting", "priority": 1},
        {"question": (
             "What is your debt maturity schedule and refinancing "
             "plan for the next 24 months?"),
         "category": "Financial Risk", "priority": 1},
        {"question": (
             "Under what circumstances would you consider "
             "cutting the dividend?"),
         "category": "Dividend Risk", "priority": 2},
        {"question": (
             "If externally managed, does the manager manage "
             "competing vehicles?"),
         "category": "Governance", "priority": 2},
        {"question": (
             "What is your office/retail concentration and "
             "view on structural demand?"),
         "category": "Subsector Risk", "priority": 3},
    ],
    "scoring_adjustments": {"F3_financial_health": 1.2, "F5_governance": 1.1},
}

TRANSPORTATION_RAIL_PLAYBOOK: dict[str, Any] = {
    "id": "TRANSPORTATION_RAIL",
    "name": "Transportation / Freight Rail",
    "description": (
        "Industry playbook for railroads, trucking, air transport, and "
        "logistics companies covering PSR safety trade-off disclosure, "
        "deferred maintenance concealment, operating ratio manipulation, "
        "derailment/incident liability, and regulatory intensification."
    ),
    "sic_ranges": [
        {"low": 4000, "high": 4099},
        {"low": 4100, "high": 4199},
        {"low": 4200, "high": 4299},
        {"low": 4400, "high": 4499},
        {"low": 4500, "high": 4599},
    ],
    "naics_prefixes": ["4811", "4821", "4831", "4841", "4842", "4851", "4852"],
    "industry_checks": [
        _check("RAIL.PSR.safety_tradeoff",
               "PSR implementation contradicting public safety-first messaging",
               6, "LITIGATION", "HIGH", "TRANSPORTATION_RAIL",
               required_data=["sec_filings", "web_search"],
               scoring_factor="F1_litigation"),
        _check("RAIL.MAINT.deferred",
               "Deferred maintenance concealment (CapEx/depreciation <1.0x)",
               3, "FINANCIAL_REPORTING", "HIGH", "TRANSPORTATION_RAIL",
               required_data=["sec_filings", "xbrl_data"],
               scoring_factor="F3_financial_health"),
        _check("RAIL.OR.manipulation",
               "Operating ratio improvement through maintenance deferral",
               3, "FINANCIAL_REPORTING", "MEDIUM", "TRANSPORTATION_RAIL",
               scoring_factor="F3_financial_health"),
        _check("RAIL.INCIDENT.derailment",
               "Major derailment or hazmat incident within 24 months",
               6, "LITIGATION", "HIGH", "TRANSPORTATION_RAIL",
               required_data=["web_search"],
               scoring_factor="F1_litigation"),
        _check("RAIL.REG.fra_violations",
               "FRA safety violations above industry average or pending enforcement",
               5, "REGULATORY", "HIGH", "TRANSPORTATION_RAIL",
               required_data=["web_search"],
               scoring_factor="F8_emerging_risks"),
        _check("RAIL.SERVICE.degradation",
               "Service metric deterioration (velocity <22mph, dwell >28hrs)",
               2, "BUSINESS_PROFILE", "MEDIUM", "TRANSPORTATION_RAIL",
               required_data=["sec_filings", "web_search"],
               scoring_factor="F8_emerging_risks"),
        _check("RAIL.LABOR.workforce_cuts",
               "Workforce reductions >15% in safety-sensitive positions",
               4, "GOVERNANCE", "MEDIUM", "TRANSPORTATION_RAIL",
               data_locations=["extracted.governance"],
               scoring_factor="F5_governance"),
        _check("RAIL.HAZMAT.concentration",
               "Hazmat carload concentration >25% without enhanced safety disclosure",
               5, "REGULATORY", "MEDIUM", "TRANSPORTATION_RAIL",
               scoring_factor="F8_emerging_risks"),
        _check("RAIL.MERGER.regulatory",
               "Pending merger application with extended STB review uncertainty",
               4, "GOVERNANCE", "MEDIUM", "TRANSPORTATION_RAIL",
               required_data=["sec_filings", "web_search"],
               scoring_factor="F5_governance"),
        _check("RAIL.SAFETY.detector_spacing",
               "Hot bearing detector spacing exceeding industry recommendations",
               5, "REGULATORY", "HIGH", "TRANSPORTATION_RAIL",
               required_data=["sec_filings", "web_search"],
               scoring_factor="F8_emerging_risks"),
    ],
    "risk_patterns": ["psr_safety_incident_cascade", "deferred_maintenance_failure"],
    "claim_theories": [
        {"id": "RAIL_CT1", "name": "PSR safety misrepresentation",
         "description": "Safety-first claims contradicted by PSR workforce/inspection cuts",
         "factors_affected": ["F1_litigation", "F5_governance"],
         "historical_examples": ["Norfolk Southern East Palestine $1.7B+ (ongoing)"]},
        {"id": "RAIL_CT2", "name": "Deferred maintenance concealment",
         "description": "Reducing maintenance CapEx to boost OR while claiming adequacy",
         "factors_affected": ["F3_financial_health"],
         "historical_examples": []},
        {"id": "RAIL_CT3", "name": "Catastrophic event-driven liability",
         "description": "Single incident generating exposure far exceeding historical assumptions",
         "factors_affected": ["F1_litigation", "F8_emerging_risks"],
         "historical_examples": ["Norfolk Southern East Palestine $1.7B+ total costs"]},
    ],
    "meeting_questions": [
        {"question": (
             "How has PSR affected safety investment and "
             "workforce in safety-sensitive positions?"),
         "category": "Safety", "priority": 1},
        {"question": ("What is your derailment rate trend and "
                       "hot bearing detector spacing?"),
         "category": "Safety", "priority": 1},
        {"question": "What is your CapEx/depreciation ratio and maintenance spending trend?",
         "category": "Financial Quality", "priority": 2},
        {"question": "Are there any pending FRA enforcement actions or NTSB investigations?",
         "category": "Regulatory", "priority": 2},
        {"question": "What is your OR target and how do you balance efficiency with safety?",
         "category": "Strategy", "priority": 3},
    ],
    "scoring_adjustments": {"F1_litigation": 1.3, "F8_emerging_risks": 1.2},
}
