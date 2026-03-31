"""Industry playbook data for CPG/Consumer and Media/Entertainment.

Split from playbook_data.py for 500-line compliance. Contains the
CPG_CONSUMER and MEDIA_ENTERTAINMENT playbook definitions, mined
from Old Underwriter industry supplement files.
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


# ---------------------------------------------------------------------------
# CPG / Consumer Staples Playbook
# ---------------------------------------------------------------------------

CPG_CONSUMER_PLAYBOOK: dict[str, Any] = {
    "id": "CPG_CONSUMER",
    "name": "CPG / Consumer Staples",
    "description": (
        "Industry playbook for consumer packaged goods and staples companies "
        "covering M&A-driven goodwill impairment, zero-based budgeting damage, "
        "private label competition, brand equity erosion, and product recall risk."
    ),
    "sic_ranges": [
        {"low": 2000, "high": 2099},  # Food and kindred products
        {"low": 2100, "high": 2199},  # Tobacco products
    ],
    "naics_prefixes": ["3111", "3112", "3113", "3114", "3115", "3116", "3121"],
    "industry_checks": [
        _check(
            "CPG.MA.goodwill_impairment",
            "M&A-driven goodwill impairment risk (goodwill >30% of assets)",
            3, "FINANCIAL_REPORTING", "HIGH", "CPG_CONSUMER",
            required_data=["sec_filings", "xbrl_data"],
            scoring_factor="F3_financial_health",
        ),
        _check(
            "CPG.MA.synergy_failure",
            "Acquisition synergy target reductions or integration overruns",
            3, "FINANCIAL_REPORTING", "HIGH", "CPG_CONSUMER",
            required_data=["sec_filings", "web_search"],
            scoring_factor="F3_financial_health",
        ),
        _check(
            "CPG.ZBB.brand_erosion",
            "Zero-based budgeting damage to R&D, brand equity, or quality",
            2, "BUSINESS_PROFILE", "MEDIUM", "CPG_CONSUMER",
            required_data=["sec_filings", "web_search"],
            scoring_factor="F8_emerging_risks",
        ),
        _check(
            "CPG.COMP.private_label",
            "Private label competition eroding brand market share",
            2, "BUSINESS_PROFILE", "MEDIUM", "CPG_CONSUMER",
            required_data=["sec_filings", "web_search"],
            scoring_factor="F3_financial_health",
        ),
        _check(
            "CPG.RECALL.product_safety",
            "FDA recall or warning letter history (Class I/II within 3 years)",
            5, "REGULATORY", "HIGH", "CPG_CONSUMER",
            required_data=["web_search"],
            scoring_factor="F8_emerging_risks",
        ),
        _check(
            "CPG.GUIDANCE.miss_pattern",
            "Earnings guidance miss pattern from input cost or volume declines",
            3, "FINANCIAL_REPORTING", "MEDIUM", "CPG_CONSUMER",
            required_data=["sec_filings"],
            scoring_factor="F3_financial_health",
        ),
        _check(
            "CPG.ANTITRUST.protein_fixing",
            "DOJ antitrust investigation for price-fixing (meat/protein sector)",
            6, "LITIGATION", "HIGH", "CPG_CONSUMER",
            required_data=["web_search"],
            scoring_factor="F1_litigation",
        ),
        _check(
            "CPG.FTC.labeling",
            "FTC investigation for deceptive labeling or advertising claims",
            5, "REGULATORY", "MEDIUM", "CPG_CONSUMER",
            required_data=["web_search"],
            scoring_factor="F8_emerging_risks",
        ),
        _check(
            "CPG.INV.channel_stuffing",
            "Retailer inventory destocking or channel stuffing indicators",
            3, "FINANCIAL_REPORTING", "HIGH", "CPG_CONSUMER",
            required_data=["sec_filings", "xbrl_data"],
            scoring_factor="F3_financial_health",
        ),
        _check(
            "CPG.PE.post_acquisition",
            "PE-backed acquisition in 18-36 month high-risk integration window",
            4, "GOVERNANCE", "HIGH", "CPG_CONSUMER",
            data_locations=["extracted.governance"],
            scoring_factor="F5_governance",
        ),
    ],
    "risk_patterns": ["ma_goodwill_impairment_cascade", "zbb_brand_deterioration"],
    "claim_theories": [
        {
            "id": "CPG_CT1",
            "name": "Concealed acquisition integration failures",
            "description": (
                "Management knew synergies were unrealistic but continued to "
                "affirm targets while integration problems worsened"
            ),
            "factors_affected": ["F3_financial_health", "F5_governance"],
            "historical_examples": [
                "Kraft Heinz $512M (2023)",
                "TreeHouse Foods $27M (2021)",
            ],
        },
        {
            "id": "CPG_CT2",
            "name": "Goodwill impairment delay or concealment",
            "description": (
                "Management delayed goodwill write-down despite internal "
                "knowledge that fair value was below carrying value"
            ),
            "factors_affected": ["F3_financial_health"],
            "historical_examples": [
                "J.M. Smucker/Hostess $619M impairment (2025)",
                "ConAgra/Pinnacle impairment",
            ],
        },
        {
            "id": "CPG_CT3",
            "name": "Product recall concealment with prior FDA warnings",
            "description": (
                "Company knew of contamination or quality issues earlier "
                "than disclosed, with stock drop exceeding 10% on recall news"
            ),
            "factors_affected": ["F1_litigation", "F8_emerging_risks"],
            "historical_examples": [
                "Boar's Head listeria recall",
                "TreeHouse Foods listeria/waffles",
            ],
        },
        {
            "id": "CPG_CT4",
            "name": "Antitrust price-fixing in protein sector",
            "description": (
                "DOJ investigation into industry-wide pricing coordination "
                "followed by securities claims for concealing illegal conduct"
            ),
            "factors_affected": ["F1_litigation"],
            "historical_examples": [
                "Pilgrim's Pride $41.5M (2025)",
                "Tyson Foods (dismissed)",
            ],
        },
    ],
    "meeting_questions": [
        {
            "question": (
                "What acquisitions have been made in the last 5 years "
                "and how is goodwill as % of total assets trending?"
            ),
            "category": "M&A Risk",
            "priority": 1,
        },
        {
            "question": "How are synergy targets tracking vs. projections?",
            "category": "M&A Risk",
            "priority": 1,
        },
        {
            "question": (
                "What is the FDA warning letter and product recall "
                "history for the past 3 years?"
            ),
            "category": "Product Safety",
            "priority": 2,
        },
        {
            "question": "What is the private label threat to core brands?",
            "category": "Business Risk",
            "priority": 2,
        },
        {
            "question": (
                "What percentage of revenue is from your top 5 brands, "
                "and how has brand market share trended?"
            ),
            "category": "Concentration",
            "priority": 3,
        },
    ],
    "scoring_adjustments": {"F3_financial_health": 1.1, "F8_emerging_risks": 1.1},
}

MEDIA_ENTERTAINMENT_PLAYBOOK: dict[str, Any] = {
    "id": "MEDIA_ENTERTAINMENT",
    "name": "Media / Entertainment",
    "description": (
        "Industry playbook for media, entertainment, and communications "
        "companies covering streaming subscriber metric manipulation, "
        "content amortization accounting, goodwill impairment from "
        "cord-cutting, defamation exposure, and M&A controlling "
        "shareholder conflicts."
    ),
    "sic_ranges": [
        {"low": 2700, "high": 2799},  # Printing, publishing, and allied
        {"low": 4800, "high": 4899},  # Communications
        {"low": 7810, "high": 7819},  # Motion picture production/distribution
        {"low": 7900, "high": 7999},  # Amusement and recreation services
    ],
    "naics_prefixes": ["5111", "5121", "5122", "5151", "5152", "5171", "5179"],
    "industry_checks": [
        _check(
            "MEDIA.SUB.metric_manipulation",
            "Streaming subscriber count manipulation or non-standard definitions",
            3, "FINANCIAL_REPORTING", "HIGH", "MEDIA_ENTERTAINMENT",
            required_data=["sec_filings", "web_search"],
            scoring_factor="F3_financial_health",
        ),
        _check(
            "MEDIA.CONTENT.amortization",
            "Content amortization life extension or impairment delay",
            3, "FINANCIAL_REPORTING", "HIGH", "MEDIA_ENTERTAINMENT",
            required_data=["sec_filings", "xbrl_data"],
            scoring_factor="F3_financial_health",
        ),
        _check(
            "MEDIA.GW.impairment_delay",
            "Goodwill impairment delay from cord-cutting or rights loss",
            3, "FINANCIAL_REPORTING", "HIGH", "MEDIA_ENTERTAINMENT",
            required_data=["sec_filings", "xbrl_data"],
            scoring_factor="F3_financial_health",
        ),
        _check(
            "MEDIA.DEFAMATION.exposure",
            "Defamation liability exposure from news or opinion content",
            6, "LITIGATION", "HIGH", "MEDIA_ENTERTAINMENT",
            required_data=["web_search"],
            scoring_factor="F1_litigation",
        ),
        _check(
            "MEDIA.MA.controlling_shareholder",
            "Controlling shareholder conflicts in M&A transactions (dual-class)",
            4, "GOVERNANCE", "HIGH", "MEDIA_ENTERTAINMENT",
            data_locations=["extracted.governance"],
            scoring_factor="F5_governance",
        ),
        _check(
            "MEDIA.SPORTS.rights_loss",
            "Sports rights expiration or loss creating affiliate fee leverage decline",
            2, "BUSINESS_PROFILE", "MEDIUM", "MEDIA_ENTERTAINMENT",
            required_data=["sec_filings", "web_search"],
            scoring_factor="F8_emerging_risks",
        ),
        _check(
            "MEDIA.GAMING.loot_box",
            "Loot box or microtransaction gambling allegations (video gaming)",
            5, "REGULATORY", "MEDIUM", "MEDIA_ENTERTAINMENT",
            required_data=["web_search"],
            scoring_factor="F8_emerging_risks",
        ),
        _check(
            "MEDIA.PRIVACY.vppa",
            "VPPA or viewer data privacy violation exposure",
            6, "LITIGATION", "MEDIUM", "MEDIA_ENTERTAINMENT",
            required_data=["web_search"],
            scoring_factor="F1_litigation",
        ),
        _check(
            "MEDIA.STREAM.profitability",
            "Streaming profitability timeline repeatedly extended or missed",
            3, "FINANCIAL_REPORTING", "MEDIUM", "MEDIA_ENTERTAINMENT",
            required_data=["sec_filings", "web_search"],
            scoring_factor="F3_financial_health",
        ),
        _check(
            "MEDIA.ANTITRUST.ticketing",
            "Antitrust scrutiny for ticketing or content distribution monopoly",
            5, "REGULATORY", "HIGH", "MEDIA_ENTERTAINMENT",
            required_data=["web_search"],
            scoring_factor="F1_litigation",
        ),
    ],
    "risk_patterns": [
        "subscriber_metric_collapse",
        "cord_cutting_impairment_cascade",
    ],
    "claim_theories": [
        {
            "id": "MEDIA_CT1",
            "name": "Subscriber metric manipulation",
            "description": (
                "Overstating subscriber counts through non-standard "
                "definitions, counting trials, or bundled accounts"
            ),
            "factors_affected": ["F3_financial_health"],
            "historical_examples": [
                "Netflix 2022 (dismissed)",
                "Disney streaming lawsuits (pending)",
            ],
        },
        {
            "id": "MEDIA_CT2",
            "name": "Goodwill impairment delay from structural decline",
            "description": (
                "Failing to timely recognize goodwill impairment when "
                "cord-cutting, rights losses, or advertising decline "
                "constitute triggering events"
            ),
            "factors_affected": ["F3_financial_health"],
            "historical_examples": [
                "Warner Bros. Discovery $9.1B impairment (2024)",
            ],
        },
        {
            "id": "MEDIA_CT3",
            "name": "Defamation with actual malice",
            "description": (
                "Publishing known false statements with reckless disregard "
                "for truth, evidenced by internal communications"
            ),
            "factors_affected": ["F1_litigation"],
            "historical_examples": [
                "Fox News/Dominion $787.5M (2023)",
            ],
        },
        {
            "id": "MEDIA_CT4",
            "name": "Controlling shareholder M&A conflicts",
            "description": (
                "Dual-class structures where controlling shareholder "
                "favors own interests in merger transactions"
            ),
            "factors_affected": ["F5_governance", "F1_litigation"],
            "historical_examples": [
                "Paramount CBS-Viacom $290M",
                "Dell Technologies $1.0B",
                "Activision Blizzard $275M",
            ],
        },
    ],
    "meeting_questions": [
        {
            "question": (
                "How do you define and count your key subscriber or "
                "audience metrics, and has the methodology changed?"
            ),
            "category": "Metric Quality",
            "priority": 1,
        },
        {
            "question": (
                "What is your content amortization policy and how "
                "does it compare to actual viewing patterns?"
            ),
            "category": "Accounting",
            "priority": 1,
        },
        {
            "question": (
                "What sports rights are expiring in the next 3 years "
                "and what is the renewal strategy?"
            ),
            "category": "Business Risk",
            "priority": 2,
        },
        {
            "question": (
                "Does the company have dual-class stock or a controlling "
                "shareholder, and what governance safeguards exist?"
            ),
            "category": "Governance",
            "priority": 2,
        },
        {
            "question": (
                "What is your editorial review process for accuracy, "
                "and have there been any defamation claims?"
            ),
            "category": "Content Liability",
            "priority": 3,
        },
    ],
    "scoring_adjustments": {"F1_litigation": 1.2, "F3_financial_health": 1.1},
}
