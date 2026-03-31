"""Extra industry playbook data for Energy/Utilities and Healthcare.

Split from playbook_data.py for 500-line compliance. Contains the
ENERGY_UTILITIES and HEALTHCARE playbook definitions.
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


ENERGY_UTILITIES_PLAYBOOK: dict[str, Any] = {
    "id": "ENERGY_UTILITIES",
    "name": "Energy / Utilities",
    "description": (
        "Industry playbook for energy producers, refiners, and utility "
        "companies covering reserve valuation, environmental liability, "
        "climate disclosure, pipeline safety, and transition risk."
    ),
    "sic_ranges": [
        {"low": 1200, "high": 1299},
        {"low": 1300, "high": 1389},
        {"low": 2900, "high": 2999},
        {"low": 4900, "high": 4991},
    ],
    "naics_prefixes": ["2111", "2121", "2211", "2212", "3241", "4861"],
    "industry_checks": [
        _check("ENGY.RESERVE.overstatement", "Proved reserve overstatement or reclassification",
               3, "FINANCIAL_REPORTING", "HIGH", "ENERGY_UTILITIES",
               required_data=["sec_filings"],
               scoring_factor="F3_financial_health"),
        _check(
            "ENGY.ENV.remediation_understatement",
            "Environmental remediation cost understatement",
            6, "LITIGATION", "HIGH", "ENERGY_UTILITIES",
            required_data=["sec_filings", "web_search"],
            scoring_factor="F1_litigation",
        ),
        _check(
            "ENGY.CLIMATE.disclosure_risk",
            "Inadequate climate risk disclosure (SEC climate rule)",
            5, "REGULATORY", "HIGH", "ENERGY_UTILITIES",
            required_data=["sec_filings", "web_search"],
            scoring_factor="F8_emerging_risks",
        ),
        _check(
            "ENGY.SAFETY.pipeline_incidents",
            "Pipeline/refinery safety incidents and OSHA violations",
            6, "LITIGATION", "HIGH", "ENERGY_UTILITIES",
            required_data=["web_search"],
            scoring_factor="F1_litigation",
        ),
        _check(
            "ENGY.TRANSITION.stranded_assets",
            "Stranded asset and energy transition impairment risk",
            3, "FINANCIAL_REPORTING", "MEDIUM", "ENERGY_UTILITIES",
            required_data=["sec_filings"],
            scoring_factor="F3_financial_health",
        ),
        _check(
            "ENGY.COMMODITY.hedging_risk",
            "Commodity hedging program and mark-to-market exposure",
            3, "FINANCIAL_REPORTING", "MEDIUM", "ENERGY_UTILITIES",
            required_data=["sec_filings", "xbrl_data"],
            scoring_factor="F3_financial_health",
        ),
        _check("ENGY.REG.rate_case_exposure", "Utility rate case and regulatory disallowance risk",
               5, "REGULATORY", "MEDIUM", "ENERGY_UTILITIES",
               required_data=["sec_filings", "web_search"],
               scoring_factor="F8_emerging_risks"),
        _check("ENGY.WILDFIRE.liability", "Wildfire / natural disaster liability exposure",
               6, "LITIGATION", "HIGH", "ENERGY_UTILITIES",
               required_data=["web_search"],
               scoring_factor="F1_litigation"),
        _check("ENGY.DECOM.obligation", "Asset retirement and decommissioning obligation adequacy",
               3, "FINANCIAL_REPORTING", "MEDIUM", "ENERGY_UTILITIES",
               required_data=["sec_filings"],
               scoring_factor="F3_financial_health"),
        _check("ENGY.GOV.board_independence", "Board independence and fossil fuel industry ties",
               4, "GOVERNANCE", "LOW", "ENERGY_UTILITIES",
               data_locations=["extracted.governance"],
               scoring_factor="F5_governance"),
    ],
    "risk_patterns": ["environmental_enforcement_cascade", "commodity_price_collapse"],
    "claim_theories": [
        "Overstating proved reserves to inflate asset valuation",
        "Understating environmental remediation costs and ARO obligations",
        "Inadequate climate risk disclosure under SEC rules",
        "Workplace safety and OSHA violations at production sites",
        "Wildfire liability from utility infrastructure negligence",
    ],
    "meeting_questions": [
        "What is the trend in proved reserve revisions over the last 3 years?",
        "What are total environmental remediation liabilities and adequacy confidence?",
        "Has the company adopted TCFD or SEC climate disclosure framework?",
        "What is the asset retirement obligation trend and key assumptions?",
        "Are there any pending EPA, OSHA, or state environmental enforcement actions?",
    ],
    "scoring_adjustments": {"F1_litigation": 1.2, "F8_emerging_risks": 1.3},
}

HEALTHCARE_PLAYBOOK: dict[str, Any] = {
    "id": "HEALTHCARE",
    "name": "Healthcare Services / Providers",
    "description": (
        "Industry playbook for healthcare service providers, hospitals, "
        "managed care organizations, and pharmacy chains covering billing "
        "fraud, quality of care, HIPAA compliance, and regulatory risk."
    ),
    "sic_ranges": [
        {"low": 8000, "high": 8099},
        {"low": 5912, "high": 5912},
        {"low": 5047, "high": 5047},
    ],
    "naics_prefixes": [
        "6211", "6214", "6215", "6216", "6219", "6221", "6223",
    ],
    "industry_checks": [
        _check("HC.BILLING.fca_risk", "False Claims Act / Medicare billing fraud indicators",
               6, "LITIGATION", "HIGH", "HEALTHCARE",
               required_data=["sec_filings", "web_search"],
               scoring_factor="F1_litigation"),
        _check(
            "HC.QUALITY.patient_outcomes",
            "Patient outcome quality metrics and CMS star ratings",
            5, "REGULATORY", "MEDIUM", "HEALTHCARE",
            required_data=["web_search"],
            scoring_factor="F8_emerging_risks",
        ),
        _check("HC.HIPAA.compliance", "HIPAA breach incidents and OCR investigations",
               6, "LITIGATION", "HIGH", "HEALTHCARE",
               required_data=["web_search"],
               scoring_factor="F1_litigation"),
        _check("HC.STARK.anti_kickback", "Stark Law / Anti-Kickback Statute violation indicators",
               5, "REGULATORY", "HIGH", "HEALTHCARE",
               required_data=["sec_filings", "web_search"],
               scoring_factor="F8_emerging_risks"),
        _check("HC.STAFFING.labor_risk", "Healthcare worker staffing shortages and labor disputes",
               5, "REGULATORY", "MEDIUM", "HEALTHCARE",
               required_data=["web_search"],
               scoring_factor="F8_emerging_risks"),
        _check("HC.REIMBURSE.rate_changes", "Reimbursement rate changes (Medicare/Medicaid cuts)",
               3, "FINANCIAL_REPORTING", "HIGH", "HEALTHCARE",
               required_data=["sec_filings"],
               scoring_factor="F3_financial_health"),
        _check("HC.PBM.pricing", "PBM spread pricing and pharmacy benefit manipulation",
               5, "REGULATORY", "MEDIUM", "HEALTHCARE",
               required_data=["web_search"],
               scoring_factor="F8_emerging_risks"),
        _check("HC.OPIOID.distribution", "Opioid distribution and dispensing liability",
               6, "LITIGATION", "HIGH", "HEALTHCARE",
               required_data=["web_search"],
               scoring_factor="F1_litigation"),
        _check("HC.MERGER.antitrust", "Healthcare merger antitrust scrutiny and FTC challenges",
               5, "REGULATORY", "MEDIUM", "HEALTHCARE",
               required_data=["web_search"],
               scoring_factor="F8_emerging_risks"),
        _check("HC.CHARITY.care", "Charity care and 340B program compliance issues",
               5, "REGULATORY", "LOW", "HEALTHCARE",
               required_data=["sec_filings"],
               scoring_factor="F8_emerging_risks"),
    ],
    "risk_patterns": ["fca_whistleblower_cascade", "reimbursement_rate_compression"],
    "claim_theories": [
        "False Claims Act violations in Medicare/Medicaid billing",
        "HIPAA data breach affecting patient records",
        "Anti-Kickback Statute violations in physician referral arrangements",
        "Opioid distribution and dispensing liability",
        "Quality of care failures leading to wrongful death litigation",
    ],
    "meeting_questions": [
        "What percentage of revenue comes from Medicare/Medicaid vs. commercial payers?",
        "Have there been any qui tam (whistleblower) actions in the last 5 years?",
        "What is the HIPAA breach notification history?",
        "Are there any OIG Corporate Integrity Agreements currently in effect?",
        "How does the company handle Stark Law compliance in physician relationships?",
    ],
    "scoring_adjustments": {"F1_litigation": 1.3, "F8_emerging_risks": 1.1},
}
