"""Pre-defined industry playbook data for all industry verticals.

Defines INDUSTRY_PLAYBOOKS -- a list of playbook definitions for 10
industry verticals: Technology/SaaS, Biotech/Pharma, Financial Services,
Energy/Utilities, Healthcare, CPG/Consumer, Media/Entertainment,
Industrials/Manufacturing, REITs/Real Estate, and Transportation/Rail.
Each playbook contains SIC/NAICS mappings, industry-specific checks,
claim theories, meeting questions, and scoring weight adjustments.

The first 3 playbooks are defined here; the remaining 7 are imported
from playbook_data_extra.py, playbook_data_cpg.py, and
playbook_data_industrials.py to stay under 500 lines per file.
"""

from __future__ import annotations

from typing import Any

from do_uw.knowledge.playbook_data_cpg import (
    CPG_CONSUMER_PLAYBOOK,
    MEDIA_ENTERTAINMENT_PLAYBOOK,
)
from do_uw.knowledge.playbook_data_extra import (
    ENERGY_UTILITIES_PLAYBOOK,
    HEALTHCARE_PLAYBOOK,
)
from do_uw.knowledge.playbook_data_industrials import (
    INDUSTRIALS_MFG_PLAYBOOK,
    REITS_REAL_ESTATE_PLAYBOOK,
    TRANSPORTATION_RAIL_PLAYBOOK,
)


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


TECH_SAAS_PLAYBOOK: dict[str, Any] = {
    "id": "TECH_SAAS",
    "name": "Technology / SaaS",
    "description": (
        "Industry playbook for technology and SaaS companies covering "
        "revenue recognition, customer concentration, stock-based "
        "compensation, growth sustainability, and data privacy risks."
    ),
    "sic_ranges": [
        {"low": 3571, "high": 3579},
        {"low": 3661, "high": 3679},
        {"low": 3812, "high": 3812},
        {"low": 7371, "high": 7379},
    ],
    "naics_prefixes": ["5112", "5182", "5191", "5415"],
    "industry_checks": [
        _check("TECH.REV.asc606_risk", "ASC 606 multi-element revenue recognition risk",
               3, "FINANCIAL_REPORTING", "HIGH", "TECH_SAAS",
               required_data=["sec_filings", "xbrl_data"],
               scoring_factor="F3_financial_health"),
        _check("TECH.REV.customer_concentration", "Top 3 customers >50% revenue concentration",
               2, "BUSINESS_PROFILE", "HIGH", "TECH_SAAS",
               required_data=["sec_filings"],
               scoring_factor="F3_financial_health"),
        _check("TECH.COMP.sbc_ratio", "Stock-based compensation >30% of revenue",
               3, "FINANCIAL_REPORTING", "MEDIUM", "TECH_SAAS",
               required_data=["xbrl_data"],
               scoring_factor="F3_financial_health"),
        _check("TECH.GROWTH.deceleration", "Revenue growth deceleration pattern",
               3, "FINANCIAL_REPORTING", "HIGH", "TECH_SAAS",
               required_data=["sec_filings", "xbrl_data"],
               scoring_factor="F8_emerging_risks"),
        _check("TECH.KEY.person_dependency", "Key person / founder departure risk",
               4, "GOVERNANCE", "MEDIUM", "TECH_SAAS",
               data_locations=["extracted.governance"],
               scoring_factor="F5_governance"),
        _check("TECH.IP.litigation_exposure", "IP/patent troll litigation exposure",
               6, "LITIGATION", "MEDIUM", "TECH_SAAS",
               data_locations=["extracted.litigation"],
               scoring_factor="F1_litigation"),
        _check("TECH.PRIV.data_breach", "Data breach / privacy liability (GDPR, CCPA)",
               6, "LITIGATION", "HIGH", "TECH_SAAS",
               required_data=["sec_filings", "web_search"],
               scoring_factor="F8_emerging_risks"),
        _check("TECH.REG.platform_risk", "Platform/marketplace regulatory risk (antitrust, 230)",
               5, "REGULATORY", "MEDIUM", "TECH_SAAS",
               required_data=["web_search"],
               scoring_factor="F8_emerging_risks"),
        _check("TECH.ACCT.cloud_migration", "Cloud migration capitalized vs expensed dev costs",
               3, "FINANCIAL_REPORTING", "LOW", "TECH_SAAS",
               required_data=["sec_filings"],
               scoring_factor="F3_financial_health"),
        _check(
            "TECH.METRIC.subscription_gaming",
            "Subscription metric manipulation (churn, NRR, ARR)",
            3, "FINANCIAL_REPORTING", "HIGH", "TECH_SAAS",
            required_data=["sec_filings", "web_search"],
               scoring_factor="F3_financial_health"),
    ],
    "risk_patterns": ["revenue_deceleration_selloff", "saas_metric_collapse"],
    "claim_theories": [
        "Revenue recognition fraud in multi-year SaaS contracts",
        "Channel stuffing through reseller agreements",
        "Cookie jar reserves and deferred revenue manipulation",
        "Failure to disclose customer churn acceleration",
    ],
    "meeting_questions": [
        "What percentage of revenue is recognized over time vs. at a point in time?",
        "How has net revenue retention trended over the last 8 quarters?",
        "What is the company's backlog and remaining performance obligation trend?",
        "Has the company changed revenue recognition methodology in the last 3 years?",
        "What is the concentration risk -- top 5 customers as % of revenue?",
    ],
    "scoring_adjustments": {"F3_financial_health": 0.9, "F8_emerging_risks": 1.2},
}

BIOTECH_PHARMA_PLAYBOOK: dict[str, Any] = {
    "id": "BIOTECH_PHARMA",
    "name": "Biotech / Pharma",
    "description": (
        "Industry playbook for biotechnology and pharmaceutical companies "
        "covering clinical trial risks, FDA approval uncertainty, drug "
        "pricing exposure, and pipeline dependency."
    ),
    "sic_ranges": [
        {"low": 2830, "high": 2836},
        {"low": 2860, "high": 2869},
        {"low": 3841, "high": 3851},
        {"low": 8731, "high": 8734},
    ],
    "naics_prefixes": ["3254", "3391", "5417"],
    "industry_checks": [
        _check("BIO.TRIAL.disclosure", "Clinical trial adverse result disclosure failures",
               6, "LITIGATION", "HIGH", "BIOTECH_PHARMA",
               required_data=["sec_filings", "web_search"],
               scoring_factor="F1_litigation"),
        _check("BIO.FDA.approval_risk", "FDA approval probability overstatement",
               5, "REGULATORY", "HIGH", "BIOTECH_PHARMA",
               required_data=["sec_filings", "web_search"],
               scoring_factor="F8_emerging_risks"),
        _check("BIO.PIPE.concentration", "Pipeline concentration in single drug/indication",
               3, "FINANCIAL_REPORTING", "HIGH", "BIOTECH_PHARMA",
               scoring_factor="F3_financial_health"),
        _check("BIO.PRICE.drug_pricing", "Drug pricing manipulation or anti-competitive behavior",
               5, "REGULATORY", "MEDIUM", "BIOTECH_PHARMA",
               required_data=["web_search"],
               scoring_factor="F8_emerging_risks"),
        _check("BIO.MFG.quality_control", "Manufacturing quality / cGMP compliance issues",
               5, "REGULATORY", "MEDIUM", "BIOTECH_PHARMA",
               required_data=["sec_filings", "web_search"],
               scoring_factor="F8_emerging_risks"),
        _check("BIO.OFFLABEL.promotion", "Off-label promotion / DOJ enforcement risk",
               6, "LITIGATION", "HIGH", "BIOTECH_PHARMA",
               required_data=["web_search"],
               scoring_factor="F1_litigation"),
        _check("BIO.PATENT.cliff", "Patent cliff revenue exposure (expiry within 3 years)",
               3, "FINANCIAL_REPORTING", "HIGH", "BIOTECH_PHARMA",
               required_data=["sec_filings"],
               scoring_factor="F3_financial_health"),
        _check("BIO.INSIDER.clinical_timing", "Insider trading around clinical trial milestones",
               4, "GOVERNANCE", "HIGH", "BIOTECH_PHARMA",
               data_locations=["extracted.governance"],
               scoring_factor="F5_governance"),
        _check("BIO.REV.rebate_channel", "Rebate and channel inventory manipulation",
               3, "FINANCIAL_REPORTING", "MEDIUM", "BIOTECH_PHARMA",
               required_data=["sec_filings"],
               scoring_factor="F3_financial_health"),
        _check("BIO.ENV.opioid_liability", "Opioid distribution liability exposure",
               6, "LITIGATION", "HIGH", "BIOTECH_PHARMA",
               required_data=["web_search"],
               scoring_factor="F1_litigation"),
    ],
    "risk_patterns": ["clinical_trial_binary_event", "fda_rejection_selloff"],
    "claim_theories": [
        "Failure to disclose adverse clinical trial results",
        "Off-label marketing leading to DOJ/FTC enforcement",
        "Drug pricing manipulation or anti-competitive behavior",
        "Misleading FDA approval likelihood statements",
        "Opioid distribution and dispensing liability",
    ],
    "meeting_questions": [
        "What is the pipeline dependency on a single drug or therapeutic area?",
        "What Phase III trial readouts are expected in the next 12 months?",
        "Has the FDA issued any complete response letters in the last 3 years?",
        "What is the patent expiry schedule for top revenue-generating drugs?",
        "Are there any ongoing DOJ or state AG investigations related to pricing?",
    ],
    "scoring_adjustments": {"F1_litigation": 1.3, "F8_emerging_risks": 1.2},
}

FINANCIAL_SERVICES_PLAYBOOK: dict[str, Any] = {
    "id": "FINANCIAL_SERVICES",
    "name": "Financial Services / Banking / Insurance",
    "description": (
        "Industry playbook for banks, insurance companies, and financial "
        "services firms covering credit reserves, regulatory compliance, "
        "trading risk, consumer protection, and systemic risk indicators."
    ),
    "sic_ranges": [
        {"low": 6000, "high": 6199},
        {"low": 6200, "high": 6299},
        {"low": 6300, "high": 6399},
        {"low": 6400, "high": 6499},
        {"low": 6500, "high": 6509},
        {"low": 6554, "high": 6599},
    ],
    "naics_prefixes": ["5221", "5222", "5223", "5231", "5241", "5242"],
    "industry_checks": [
        _check("FIN.CREDIT.reserve_adequacy", "Loan loss reserve adequacy under CECL/ASC 326",
               3, "FINANCIAL_REPORTING", "HIGH", "FINANCIAL_SERVICES",
               required_data=["sec_filings", "xbrl_data"],
               scoring_factor="F3_financial_health"),
        _check("FIN.REG.bsa_aml", "BSA/AML compliance program deficiency indicators",
               5, "REGULATORY", "HIGH", "FINANCIAL_SERVICES",
               required_data=["sec_filings", "web_search"],
               scoring_factor="F8_emerging_risks"),
        _check("FIN.TRADE.risk_exposure", "Trading desk risk concentration and VaR breaches",
               3, "FINANCIAL_REPORTING", "HIGH", "FINANCIAL_SERVICES",
               required_data=["sec_filings"],
               scoring_factor="F3_financial_health"),
        _check("FIN.CONSUMER.lending_practices", "Predatory or discriminatory lending indicators",
               6, "LITIGATION", "HIGH", "FINANCIAL_SERVICES",
               required_data=["web_search"],
               scoring_factor="F1_litigation"),
        _check("FIN.CYBER.breach_exposure", "Cybersecurity breach and data exposure risk",
               6, "LITIGATION", "HIGH", "FINANCIAL_SERVICES",
               required_data=["sec_filings", "web_search"],
               scoring_factor="F8_emerging_risks"),
        _check("FIN.CAP.stress_test", "Capital adequacy and stress test performance",
               3, "FINANCIAL_REPORTING", "MEDIUM", "FINANCIAL_SERVICES",
               required_data=["sec_filings"],
               scoring_factor="F3_financial_health"),
        _check("FIN.RATE.interest_sensitivity", "Interest rate sensitivity and NIM compression",
               3, "FINANCIAL_REPORTING", "MEDIUM", "FINANCIAL_SERVICES",
               required_data=["sec_filings", "xbrl_data"],
               scoring_factor="F3_financial_health"),
        _check("FIN.SANCTIONS.compliance", "OFAC sanctions screening compliance gaps",
               5, "REGULATORY", "HIGH", "FINANCIAL_SERVICES",
               required_data=["web_search"],
               scoring_factor="F8_emerging_risks"),
        _check("FIN.FIDUCIARY.breach", "Fiduciary duty breach or self-dealing indicators",
               4, "GOVERNANCE", "HIGH", "FINANCIAL_SERVICES",
               data_locations=["extracted.governance"],
               scoring_factor="F5_governance"),
        _check("FIN.DERIV.accounting", "Derivative instrument valuation and hedge accounting risk",
               3, "FINANCIAL_REPORTING", "MEDIUM", "FINANCIAL_SERVICES",
               required_data=["sec_filings"],
               scoring_factor="F3_financial_health"),
    ],
    "risk_patterns": ["credit_cycle_deterioration", "regulatory_enforcement_cascade"],
    "claim_theories": [
        "Understating loan loss reserves during credit deterioration",
        "BSA/AML compliance failures and consent orders",
        "Predatory or discriminatory lending practices",
        "LIBOR/benchmark rate manipulation",
        "Fiduciary breach in fund management",
    ],
    "meeting_questions": [
        "What is the current CECL reserve coverage ratio vs. peer median?",
        "Have any regulatory consent orders or MRAs been issued in the last 3 years?",
        "What is the trading desk VaR utilization trend?",
        "Are there pending CFPB or state AG consumer protection actions?",
        "What percentage of assets are Level 3 fair value measurements?",
    ],
    "scoring_adjustments": {"F3_financial_health": 1.2, "F8_emerging_risks": 1.1},
}

INDUSTRY_PLAYBOOKS: list[dict[str, Any]] = [
    TECH_SAAS_PLAYBOOK,
    BIOTECH_PHARMA_PLAYBOOK,
    FINANCIAL_SERVICES_PLAYBOOK,
    ENERGY_UTILITIES_PLAYBOOK,
    HEALTHCARE_PLAYBOOK,
    CPG_CONSUMER_PLAYBOOK,
    MEDIA_ENTERTAINMENT_PLAYBOOK,
    INDUSTRIALS_MFG_PLAYBOOK,
    REITS_REAL_ESTATE_PLAYBOOK,
    TRANSPORTATION_RAIL_PLAYBOOK,
]
"""All 10 industry playbook definitions for loading into the knowledge store."""
