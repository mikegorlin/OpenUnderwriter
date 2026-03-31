#!/usr/bin/env python3
"""Fix 159 empty-tiered-threshold checks in brain/checks.json.

Three categories of fixes:
1. Reclassify 34 DISPLAY checks to MANAGEMENT_DISPLAY (38 minus 4 deleted stubs)
2. Delete 4 placeholder stubs (FWRD.EVENT.19-BIOT, 20-BIOT, 21-BIOT, 22-HLTH)
3. Add red/yellow/clear threshold values to 121 evaluative checks

Source: EMPTY-THRESHOLD-TRIAGE.md (phase 32 planning)
"""

import json
from pathlib import Path

CHECKS_PATH = Path(__file__).parent.parent / "src" / "do_uw" / "brain" / "checks.json"

# =============================================================================
# Fix 1: DISPLAY reclassification (38 IDs, but 4 overlap with DELETE)
# =============================================================================
DISPLAY_IDS = {
    "FIN.GUIDE.philosophy",
    "FIN.SECTOR.energy",
    "FIN.SECTOR.retail",
    "FWRD.EVENT.proxy_deadline",
    "FWRD.EVENT.19-BIOT",
    "FWRD.EVENT.20-BIOT",
    "FWRD.EVENT.21-BIOT",
    "FWRD.EVENT.22-HLTH",
    "GOV.ACTIVIST.schedule_13g",
    "GOV.BOARD.expertise",
    "GOV.BOARD.refresh_activity",
    "GOV.BOARD.committees",
    "GOV.INSIDER.form4_filings",
    "GOV.INSIDER.10b5_plans",
    "GOV.PAY.ceo_structure",
    "GOV.PAY.incentive_metrics",
    "GOV.PAY.perks",
    "GOV.PAY.401k_match",
    "GOV.PAY.deferred_comp",
    "GOV.PAY.pension",
    "GOV.RIGHTS.voting_rights",
    "GOV.RIGHTS.bylaws",
    "GOV.RIGHTS.forum_select",
    "FWRD.MACRO.sector_performance",
    "FWRD.MACRO.peer_issues",
    "FWRD.MACRO.industry_consolidation",
    "FWRD.MACRO.disruptive_tech",
    "FWRD.MACRO.interest_rate_sensitivity",
    "FWRD.MACRO.inflation_impact",
    "FWRD.MACRO.fx_exposure",
    "FWRD.MACRO.commodity_impact",
    "FWRD.MACRO.labor_market",
    "FWRD.MACRO.regulatory_changes",
    "FWRD.MACRO.legislative_risk",
    "FWRD.MACRO.trade_policy",
    "FWRD.MACRO.geopolitical_exposure",
    "FWRD.MACRO.supply_chain_disruption",
    "FWRD.MACRO.climate_transition_risk",
}

# =============================================================================
# Fix 2: Delete placeholder stubs
# =============================================================================
DELETE_IDS = {
    "FWRD.EVENT.19-BIOT",
    "FWRD.EVENT.20-BIOT",
    "FWRD.EVENT.21-BIOT",
    "FWRD.EVENT.22-HLTH",
}

# =============================================================================
# Fix 3: Threshold values for 121 evaluative checks
# Organized by prefix, sourced from EMPTY-THRESHOLD-TRIAGE.md
# =============================================================================
THRESHOLDS: dict[str, dict[str, str]] = {
    # -------------------------------------------------------------------------
    # STOCK.INSIDER (2)
    # -------------------------------------------------------------------------
    "STOCK.INSIDER.notable_activity": {
        "red": ">25% of holdings sold in 90 days",
        "yellow": ">10% of holdings sold in 90 days",
        "clear": "<10% sold or net buying",
    },
    "STOCK.INSIDER.cluster_timing": {
        "red": "Cluster selling detected pre-announcement",
        "yellow": "Cluster selling detected",
        "clear": "No cluster pattern",
    },
    # -------------------------------------------------------------------------
    # STOCK.SHORT (2)
    # -------------------------------------------------------------------------
    "STOCK.SHORT.trend": {
        "red": "Short ratio >10 days OR increasing >50% QoQ",
        "yellow": "Short ratio >5 days OR increasing >25% QoQ",
        "clear": "Short ratio <5 days and stable/declining",
    },
    "STOCK.SHORT.report": {
        "red": "Named short seller report published",
        "yellow": "Elevated short interest without identified report",
        "clear": "No short seller reports",
    },
    # -------------------------------------------------------------------------
    # STOCK.VALUATION (4)
    # -------------------------------------------------------------------------
    "STOCK.VALUATION.pe_ratio": {
        "red": "PE >50x OR negative earnings",
        "yellow": "PE >30x",
        "clear": "PE <30x",
    },
    "STOCK.VALUATION.ev_ebitda": {
        "red": "EV/EBITDA >25x OR negative EBITDA",
        "yellow": "EV/EBITDA >15x",
        "clear": "EV/EBITDA <15x",
    },
    "STOCK.VALUATION.premium_discount": {
        "red": ">50% premium to peers",
        "yellow": ">25% premium to peers",
        "clear": "<25% premium",
    },
    "STOCK.VALUATION.peg_ratio": {
        "red": "PEG >3.0 OR negative",
        "yellow": "PEG >2.0",
        "clear": "PEG <2.0",
    },
    # -------------------------------------------------------------------------
    # FIN.PROFIT (1)
    # -------------------------------------------------------------------------
    "FIN.PROFIT.trend": {
        "red": "Margins declining >500bps YoY OR loss-making",
        "yellow": "Margins declining >200bps YoY",
        "clear": "Stable or expanding margins",
    },
    # -------------------------------------------------------------------------
    # FIN.ACCT (5)
    # -------------------------------------------------------------------------
    "FIN.ACCT.auditor": {
        "red": "Going concern OR adverse opinion OR disclaimer",
        "yellow": "Qualified opinion OR auditor change",
        "clear": "Unqualified opinion, no change",
    },
    "FIN.ACCT.internal_controls": {
        "red": "Material weakness disclosed",
        "yellow": "Significant deficiency disclosed",
        "clear": "No MW or SD",
    },
    "FIN.ACCT.sec_correspondence": {
        "red": ">3 comment letters in 12 months OR accounting-focused letters",
        "yellow": "1-3 comment letters in 12 months",
        "clear": "No recent comment letters",
    },
    "FIN.ACCT.quality_indicators": {
        "red": "Z-Score <1.81 (distress zone)",
        "yellow": "Z-Score 1.81-2.99 (grey zone)",
        "clear": "Z-Score >2.99 (safe zone)",
    },
    "FIN.ACCT.earnings_manipulation": {
        "red": "M-Score >-1.78 (likely manipulator)",
        "yellow": "M-Score between -2.22 and -1.78 (grey zone)",
        "clear": "M-Score <-2.22 (unlikely manipulator)",
    },
    # -------------------------------------------------------------------------
    # FIN.GUIDE (2 evaluative, 1 display already handled)
    # -------------------------------------------------------------------------
    "FIN.GUIDE.current": {
        "red": "Guidance recently withdrawn or suspended",
        "yellow": "Guidance lowered or narrowed negatively",
        "clear": "Guidance maintained or raised",
    },
    "FIN.GUIDE.earnings_reaction": {
        "red": ">10% drop on earnings",
        "yellow": ">5% drop on earnings",
        "clear": "Neutral or positive reaction",
    },
    "FIN.GUIDE.analyst_consensus": {
        "red": "Consensus estimates declining >10%",
        "yellow": "Estimates declining 5-10%",
        "clear": "Estimates stable or rising",
    },
    # -------------------------------------------------------------------------
    # LIT.REG (16)
    # -------------------------------------------------------------------------
    "LIT.REG.state_ag": {
        "red": "Active state AG enforcement action",
        "yellow": "State AG inquiry disclosed",
        "clear": "No state AG activity",
    },
    "LIT.REG.subpoena": {
        "red": "DOJ/SEC subpoena disclosed",
        "yellow": "Other government subpoena",
        "clear": "No subpoenas disclosed",
    },
    "LIT.REG.comment_letters": {
        "red": ">3 comment letters in 12 months OR re-opened correspondence",
        "yellow": "1-3 comment letters in 12 months",
        "clear": "None in 12 months",
    },
    "LIT.REG.deferred_pros": {
        "red": "Active DPA/NPA in effect",
        "yellow": "DPA/NPA expired within 2 years",
        "clear": "No DPA/NPA history",
    },
    "LIT.REG.wells_notice": {
        "red": "Wells notice received",
        "yellow": "Prior Wells notice (resolved)",
        "clear": "No Wells notice history",
    },
    "LIT.REG.consent_order": {
        "red": "Active consent order in effect",
        "yellow": "Consent order expired within 2 years",
        "clear": "No consent orders",
    },
    "LIT.REG.cease_desist": {
        "red": "Active C&D order",
        "yellow": "C&D issued within 3 years",
        "clear": "No C&D orders",
    },
    "LIT.REG.civil_penalty": {
        "red": "Civil penalty imposed >$10M OR >1% revenue",
        "yellow": "Civil penalty imposed <$10M",
        "clear": "No civil penalties",
    },
    "LIT.REG.dol_audit": {
        "red": "Active DOL investigation with findings",
        "yellow": "DOL audit disclosed",
        "clear": "No DOL activity",
    },
    "LIT.REG.epa_action": {
        "red": "Active EPA enforcement/Superfund liability",
        "yellow": "EPA inquiry or notice of violation",
        "clear": "No EPA activity",
    },
    "LIT.REG.osha_citation": {
        "red": "Willful/repeat citation OR fatality investigation",
        "yellow": "Serious citation",
        "clear": "No OSHA citations",
    },
    "LIT.REG.cfpb_action": {
        "red": "Active CFPB enforcement action",
        "yellow": "CFPB inquiry or CID",
        "clear": "No CFPB activity",
    },
    "LIT.REG.fdic_order": {
        "red": "Active FDIC enforcement order",
        "yellow": "FDIC MOU or informal action",
        "clear": "No FDIC activity",
    },
    "LIT.REG.fda_warning": {
        "red": "FDA warning letter OR consent decree",
        "yellow": "FDA 483 observation or untitled letter",
        "clear": "No FDA activity",
    },
    "LIT.REG.foreign_gov": {
        "red": "Foreign government enforcement action",
        "yellow": "Foreign government inquiry disclosed",
        "clear": "No foreign government activity",
    },
    "LIT.REG.state_action": {
        "red": "Active state regulatory enforcement",
        "yellow": "State regulatory inquiry",
        "clear": "No state regulatory activity",
    },
    # -------------------------------------------------------------------------
    # LIT.OTHER (14)
    # -------------------------------------------------------------------------
    "LIT.OTHER.product": {
        "red": ">5 active product liability matters OR class action",
        "yellow": "1-5 active matters",
        "clear": "No product liability matters",
    },
    "LIT.OTHER.employment": {
        "red": ">5 active employment matters OR class/collective action",
        "yellow": "1-5 active employment matters",
        "clear": "No employment litigation",
    },
    "LIT.OTHER.ip": {
        "red": ">3 active IP matters OR patent troll targeting",
        "yellow": "1-3 active IP matters",
        "clear": "No IP litigation",
    },
    "LIT.OTHER.environmental": {
        "red": "Superfund liability OR >$10M environmental reserves",
        "yellow": "Active environmental litigation",
        "clear": "No environmental matters",
    },
    "LIT.OTHER.contract": {
        "red": ">3 material contract disputes OR >10% revenue at risk",
        "yellow": "1-3 active contract disputes",
        "clear": "No material contract disputes",
    },
    "LIT.OTHER.aggregate": {
        "red": ">10 total active matters",
        "yellow": "5-10 active matters",
        "clear": "<5 active matters",
    },
    "LIT.OTHER.class_action": {
        "red": ">2 active class actions",
        "yellow": "1-2 active class actions",
        "clear": "No non-SCA class actions",
    },
    "LIT.OTHER.antitrust": {
        "red": "Active DOJ/FTC antitrust investigation OR class action",
        "yellow": "Antitrust inquiry disclosed",
        "clear": "No antitrust matters",
    },
    "LIT.OTHER.trade_secret": {
        "red": ">2 active trade secret cases OR involving key technology",
        "yellow": "1-2 active trade secret cases",
        "clear": "No trade secret litigation",
    },
    "LIT.OTHER.whistleblower": {
        "red": "Qui tam or SEC whistleblower complaint filed",
        "yellow": "Internal whistleblower complaint disclosed",
        "clear": "No whistleblower activity",
    },
    "LIT.OTHER.cyber_breach": {
        "red": "Material data breach disclosed OR breach litigation",
        "yellow": "Cyber incident disclosed without litigation",
        "clear": "No cyber breaches",
    },
    "LIT.OTHER.bankruptcy": {
        "red": "Bankruptcy/restructuring proceedings",
        "yellow": "Material vendor/customer bankruptcy affecting company",
        "clear": "No bankruptcy matters",
    },
    "LIT.OTHER.foreign_suit": {
        "red": ">3 active foreign suits OR material foreign judgment",
        "yellow": "1-3 active foreign suits",
        "clear": "No foreign litigation",
    },
    "LIT.OTHER.gov_contract": {
        "red": "Active False Claims Act suit OR debarment risk",
        "yellow": "Government contract dispute or protest",
        "clear": "No government contract matters",
    },
    # -------------------------------------------------------------------------
    # GOV.BOARD (5 evaluative, 3 display already handled)
    # -------------------------------------------------------------------------
    "GOV.BOARD.tenure": {
        "red": "Average tenure >15 years (entrenchment risk)",
        "yellow": "Average tenure >10 years",
        "clear": "Average tenure <10 years",
    },
    "GOV.BOARD.overboarding": {
        "red": ">2 directors on 4+ boards OR CEO on 2+ outside boards",
        "yellow": "1-2 directors on 4+ boards",
        "clear": "No overboarded directors",
    },
    "GOV.BOARD.departures": {
        "red": ">3 departures in 18 months OR sudden resignation",
        "yellow": "2-3 departures in 18 months",
        "clear": "0-1 departures (normal refresh)",
    },
    "GOV.BOARD.attendance": {
        "red": "Any director <75% attendance",
        "yellow": "Any director <85% attendance",
        "clear": "All directors >85% attendance",
    },
    "GOV.BOARD.meetings": {
        "red": "<4 meetings per year",
        "yellow": "4-6 meetings per year",
        "clear": ">6 meetings per year",
    },
    "GOV.BOARD.succession": {
        "red": "No succession plan AND CEO >65 OR tenured >15 years",
        "yellow": "No disclosed succession plan",
        "clear": "Succession plan disclosed",
    },
    # -------------------------------------------------------------------------
    # GOV.PAY (7 evaluative, 6 display already handled)
    # -------------------------------------------------------------------------
    "GOV.PAY.ceo_total": {
        "red": "Pay ratio >500:1 OR total comp >$50M",
        "yellow": "Pay ratio >300:1 OR total comp >$25M",
        "clear": "Pay ratio <300:1",
    },
    "GOV.PAY.peer_comparison": {
        "red": ">75th percentile of peers AND underperformance",
        "yellow": ">75th percentile of peers",
        "clear": "At or below 75th percentile",
    },
    "GOV.PAY.clawback": {
        "red": "No clawback policy beyond SOX minimum",
        "yellow": "SOX-minimum clawback only",
        "clear": "Robust clawback policy beyond SOX requirements",
    },
    "GOV.PAY.related_party": {
        "red": "Material RPTs involving executives",
        "yellow": "RPTs disclosed but immaterial",
        "clear": "No RPTs beyond standard",
    },
    "GOV.PAY.golden_para": {
        "red": "Golden parachute >5x salary OR >$50M",
        "yellow": "Golden parachute >3x salary",
        "clear": "<3x salary or no golden parachute",
    },
    "GOV.PAY.equity_burn": {
        "red": "Equity burn rate >3% annually",
        "yellow": "Equity burn rate >2% annually",
        "clear": "<2% burn rate",
    },
    "GOV.PAY.hedging": {
        "red": "Hedging permitted with no restrictions",
        "yellow": "Partial hedging restrictions",
        "clear": "Full hedging prohibition",
    },
    "GOV.PAY.exec_loans": {
        "red": "Executive loans disclosed (SOX violation risk)",
        "yellow": "Historic loans grandfathered pre-SOX",
        "clear": "No executive loans",
    },
    # -------------------------------------------------------------------------
    # GOV.RIGHTS (7 evaluative, 3 display already handled)
    # -------------------------------------------------------------------------
    "GOV.RIGHTS.dual_class": {
        "red": "Dual-class with >50% voting control by insiders",
        "yellow": "Dual-class structure present",
        "clear": "Single class, one-share-one-vote",
    },
    "GOV.RIGHTS.takeover": {
        "red": "Poison pill in effect OR multiple anti-takeover provisions",
        "yellow": "Poison pill on shelf OR 1-2 anti-takeover provisions",
        "clear": "Minimal anti-takeover provisions",
    },
    "GOV.RIGHTS.proxy_access": {
        "red": "No proxy access AND no special meeting rights",
        "yellow": "Restrictive proxy access (>5% ownership, >3 year holding)",
        "clear": "Proxy access at 3%/3-year standard or better",
    },
    "GOV.RIGHTS.supermajority": {
        "red": "Supermajority required for bylaw amendments AND board removal",
        "yellow": "Supermajority for some provisions",
        "clear": "Simple majority for all provisions",
    },
    "GOV.RIGHTS.action_consent": {
        "red": "No written consent AND no special meeting right",
        "yellow": "Written consent restricted",
        "clear": "Written consent permitted",
    },
    "GOV.RIGHTS.special_mtg": {
        "red": "Special meeting rights denied or >25% threshold",
        "yellow": "Special meeting at 15-25% threshold",
        "clear": "Special meeting at <15% threshold",
    },
    "GOV.RIGHTS.classified": {
        "red": "Classified board with no declassification proposal",
        "yellow": "Classified board with declassification underway",
        "clear": "Annual election of all directors",
    },
    # -------------------------------------------------------------------------
    # GOV.ACTIVIST (13 evaluative, 1 display already handled)
    # -------------------------------------------------------------------------
    "GOV.ACTIVIST.13d_filings": {
        "red": "Activist 13D filed with stated objectives",
        "yellow": "13D filed but passive language",
        "clear": "No 13D filings",
    },
    "GOV.ACTIVIST.campaigns": {
        "red": "Active public campaign by known activist",
        "yellow": "Private engagement by activist disclosed",
        "clear": "No activist campaigns",
    },
    "GOV.ACTIVIST.proxy_contests": {
        "red": "Active proxy contest with dissident slate",
        "yellow": "Proxy contest threatened or settled",
        "clear": "No proxy contests",
    },
    "GOV.ACTIVIST.settle_agree": {
        "red": "Settlement with board seats granted + operational demands",
        "yellow": "Settlement with board seats only",
        "clear": "No activist settlements",
    },
    "GOV.ACTIVIST.short_activism": {
        "red": "Named short seller report published + position disclosed",
        "yellow": "Short seller commentary/thesis circulating",
        "clear": "No short activism",
    },
    "GOV.ACTIVIST.demands": {
        "red": "Shareholder demand for investigation or action",
        "yellow": "Informal shareholder pressure",
        "clear": "No shareholder demands",
    },
    "GOV.ACTIVIST.wolf_pack": {
        "red": "Multiple activists accumulating simultaneously",
        "yellow": "Signs of activist coordination",
        "clear": "No wolf pack indicators",
    },
    "GOV.ACTIVIST.board_seat": {
        "red": "Activist holds >2 board seats",
        "yellow": "Activist holds 1-2 board seats",
        "clear": "No activist board representation",
    },
    "GOV.ACTIVIST.dissident": {
        "red": "Dissident proxy solicitation filed",
        "yellow": "Dissident shareholder communication",
        "clear": "No dissident activity",
    },
    "GOV.ACTIVIST.withhold": {
        "red": "Withhold campaign with >30% votes against director(s)",
        "yellow": "Withhold campaign with >20% votes against",
        "clear": "<20% votes against all directors",
    },
    "GOV.ACTIVIST.proposal": {
        "red": ">3 shareholder proposals OR proposal receiving >50% support",
        "yellow": "1-3 shareholder proposals",
        "clear": "No shareholder proposals",
    },
    "GOV.ACTIVIST.consent": {
        "red": "Active consent solicitation",
        "yellow": "Consent solicitation threatened",
        "clear": "No consent solicitation activity",
    },
    "GOV.ACTIVIST.standstill": {
        "red": "Standstill expiring within policy period",
        "yellow": "Active standstill agreement",
        "clear": "No standstill agreements (or none needed)",
    },
    # -------------------------------------------------------------------------
    # GOV.INSIDER (5 evaluative, 2 display already handled)
    # -------------------------------------------------------------------------
    "GOV.INSIDER.plan_adoption": {
        "red": "Plan adopted/modified <30 days before material event",
        "yellow": "Plan adopted/modified <90 days before material event",
        "clear": "Plans adopted with adequate cooling period",
    },
    "GOV.INSIDER.cluster_sales": {
        "red": ">3 insiders selling in same 10-day window",
        "yellow": "2-3 insiders selling in same 30-day window",
        "clear": "No cluster selling pattern",
    },
    "GOV.INSIDER.unusual_timing": {
        "red": "Sales within 30 days before negative disclosure",
        "yellow": "Sales pattern deviates from historical norm",
        "clear": "Consistent with historical pattern",
    },
    "GOV.INSIDER.executive_sales": {
        "red": ">25% of holdings sold in 90 days by C-suite",
        "yellow": ">10% of holdings sold in 90 days by C-suite",
        "clear": "<10% sold or net buying",
    },
    "GOV.INSIDER.ownership_pct": {
        "red": "Insider ownership <1% (no skin in game)",
        "yellow": "Insider ownership declining >50% in 12 months",
        "clear": "Insider ownership stable or increasing",
    },
    # -------------------------------------------------------------------------
    # FWRD.EVENT (3 evaluative, 1 display + 4 deleted already handled)
    # -------------------------------------------------------------------------
    "FWRD.EVENT.customer_retention": {
        "red": "Key customer loss disclosed or at risk",
        "yellow": "Customer concentration risk in transition",
        "clear": "Customer base stable",
    },
    "FWRD.EVENT.employee_retention": {
        "red": "Key employee departures or mass attrition",
        "yellow": "Retention risk disclosed",
        "clear": "Workforce stable",
    },
    "FWRD.EVENT.integration": {
        "red": "Integration problems disclosed OR missed milestones",
        "yellow": "Integration in progress with disclosed challenges",
        "clear": "No pending integration or on track",
    },
    # -------------------------------------------------------------------------
    # FWRD.WARN - Employee/Sentiment (7)
    # -------------------------------------------------------------------------
    "FWRD.WARN.glassdoor_sentiment": {
        "red": "Rating <3.0 OR decline >0.5 in 12 months",
        "yellow": "Rating <3.5 OR decline >0.3 in 12 months",
        "clear": "Rating >3.5 and stable/improving",
    },
    "FWRD.WARN.indeed_reviews": {
        "red": "Rating <3.0 OR significant negative trend",
        "yellow": "Rating declining",
        "clear": "Rating stable/positive",
    },
    "FWRD.WARN.blind_posts": {
        "red": "Viral posts alleging fraud/misconduct",
        "yellow": "Elevated negative anonymous posts",
        "clear": "Normal activity levels",
    },
    "FWRD.WARN.linkedin_headcount": {
        "red": "Headcount declining >10% in 6 months (non-announced)",
        "yellow": "Headcount declining >5%",
        "clear": "Stable or growing headcount",
    },
    "FWRD.WARN.linkedin_departures": {
        "red": ">3 senior departures in 90 days",
        "yellow": "2-3 notable departures in 90 days",
        "clear": "Normal attrition",
    },
    "FWRD.WARN.social_sentiment": {
        "red": "Viral negative campaign or boycott",
        "yellow": "Elevated negative sentiment trending",
        "clear": "Normal sentiment",
    },
    "FWRD.WARN.journalism_activity": {
        "red": "Investigative piece published by major outlet",
        "yellow": "Known investigative journalist inquiring",
        "clear": "Normal media coverage",
    },
    # -------------------------------------------------------------------------
    # FWRD.WARN - Product/Customer (6)
    # -------------------------------------------------------------------------
    "FWRD.WARN.g2_reviews": {
        "red": "Rating declining and below category average",
        "yellow": "Rating declining",
        "clear": "Rating stable or improving",
    },
    "FWRD.WARN.trustpilot_trend": {
        "red": "Rating <2.0 OR declining >1.0 in 6 months",
        "yellow": "Rating declining",
        "clear": "Stable or improving",
    },
    "FWRD.WARN.app_ratings": {
        "red": "Rating <3.0 OR declining >0.5 in 6 months",
        "yellow": "Rating declining",
        "clear": "Stable or improving",
    },
    "FWRD.WARN.customer_churn_signals": {
        "red": "Key customer departure confirmed OR >10% churn rate disclosed",
        "yellow": "Elevated churn indicators",
        "clear": "Normal retention",
    },
    "FWRD.WARN.contract_disputes": {
        "red": ">3 active contract disputes OR material revenue at risk",
        "yellow": "1-3 active disputes",
        "clear": "No contract disputes",
    },
    "FWRD.WARN.partner_stability": {
        "red": "Key partner termination or bankruptcy",
        "yellow": "Partner relationship strain disclosed",
        "clear": "Partnerships stable",
    },
    # -------------------------------------------------------------------------
    # FWRD.WARN - Regulatory Complaints (3)
    # -------------------------------------------------------------------------
    "FWRD.WARN.cfpb_complaints": {
        "red": "Complaint volume >2x industry average",
        "yellow": "Complaint volume rising >25% QoQ",
        "clear": "Complaint volume at or below industry average",
    },
    "FWRD.WARN.fda_medwatch": {
        "red": "Adverse event spike >3x baseline OR safety signal identified",
        "yellow": "Elevated adverse event reporting",
        "clear": "Normal adverse event levels",
    },
    "FWRD.WARN.nhtsa_complaints": {
        "red": "NHTSA investigation opened OR recall pending",
        "yellow": "Elevated complaint volume for specific issue",
        "clear": "Normal complaint levels",
    },
    # -------------------------------------------------------------------------
    # FWRD.WARN - Whistleblower/Legal (3)
    # -------------------------------------------------------------------------
    "FWRD.WARN.whistleblower_exposure": {
        "red": "Active whistleblower complaint with regulatory engagement",
        "yellow": "Whistleblower complaint filed",
        "clear": "No whistleblower activity",
    },
    "FWRD.WARN.compliance_hiring": {
        "red": "Significant compliance hiring surge (>5 positions, senior level)",
        "yellow": "Notable compliance hiring increase",
        "clear": "Normal hiring patterns",
    },
    "FWRD.WARN.legal_hiring": {
        "red": "Significant legal/litigation hiring surge",
        "yellow": "Notable legal hiring increase",
        "clear": "Normal hiring patterns",
    },
    # -------------------------------------------------------------------------
    # FWRD.WARN - Financial Warning (7)
    # -------------------------------------------------------------------------
    "FWRD.WARN.vendor_payment_delays": {
        "red": "DPO increasing >20 days YoY OR vendor complaints in news",
        "yellow": "DPO increasing >10 days YoY",
        "clear": "DPO stable",
    },
    "FWRD.WARN.job_posting_patterns": {
        "red": "Mass job posting removal (>50% in 30 days)",
        "yellow": "Significant hiring slowdown",
        "clear": "Normal posting patterns",
    },
    "FWRD.WARN.zone_of_insolvency": {
        "red": "Current ratio <1.0 AND negative working capital AND declining revenue",
        "yellow": "Current ratio <1.0 OR negative working capital",
        "clear": "Current ratio >1.5 and adequate liquidity",
    },
    "FWRD.WARN.goodwill_risk": {
        "red": "Goodwill >50% of total assets AND market cap < book value",
        "yellow": "Goodwill >30% of total assets OR recent acquisition",
        "clear": "Goodwill <30% of assets",
    },
    "FWRD.WARN.impairment_risk": {
        "red": "Market cap < book value sustained >90 days",
        "yellow": "Market cap approaching book value",
        "clear": "Market cap well above book value",
    },
    "FWRD.WARN.revenue_quality": {
        "red": "Revenue recognition changes OR restatement risk",
        "yellow": "Aggressive revenue recognition noted by auditor",
        "clear": "Standard revenue recognition",
    },
    "FWRD.WARN.margin_pressure": {
        "red": "Gross margin declining >500bps AND operating leverage negative",
        "yellow": "Gross margin declining >300bps",
        "clear": "Margins stable or expanding",
    },
    # -------------------------------------------------------------------------
    # FWRD.WARN - Tech/AI (4)
    # -------------------------------------------------------------------------
    "FWRD.WARN.ai_revenue_concentration": {
        "red": ">50% revenue from AI-related products with regulatory uncertainty",
        "yellow": ">25% AI revenue concentration",
        "clear": "<25% AI revenue",
    },
    "FWRD.WARN.hyperscaler_dependency": {
        "red": ">75% infrastructure on single hyperscaler",
        "yellow": ">50% on single hyperscaler",
        "clear": "Multi-cloud or diversified",
    },
    "FWRD.WARN.gpu_allocation": {
        "red": "GPU allocation constraint impacting production",
        "yellow": "GPU supply risk disclosed in filings",
        "clear": "Adequate compute supply",
    },
    "FWRD.WARN.data_center_risk": {
        "red": "Single data center dependency OR capacity constraints",
        "yellow": "Data center concentration risk",
        "clear": "Diversified data center strategy",
    },
    # -------------------------------------------------------------------------
    # FWRD.WARN - Operational (2)
    # -------------------------------------------------------------------------
    "FWRD.WARN.capex_discipline": {
        "red": "CapEx >2x depreciation AND declining ROIC",
        "yellow": "CapEx >1.5x depreciation",
        "clear": "CapEx aligned with depreciation",
    },
    "FWRD.WARN.working_capital_trends": {
        "red": "Working capital negative AND deteriorating",
        "yellow": "Working capital declining >20% YoY",
        "clear": "Working capital stable or improving",
    },
}


def main() -> None:
    with open(CHECKS_PATH) as f:
        data = json.load(f)

    original_count = len(data["checks"])
    print(f"Original check count: {original_count}")

    # Counters for reporting
    deleted = 0
    reclassified = 0
    thresholds_added = 0
    unknown_threshold_ids = set()

    new_checks = []
    for check in data["checks"]:
        cid = check["id"]

        # Fix 2: Delete placeholder stubs
        if cid in DELETE_IDS:
            deleted += 1
            print(f"  DELETED: {cid}")
            continue

        # Fix 1: Reclassify DISPLAY to MANAGEMENT_DISPLAY
        if cid in DISPLAY_IDS:
            check["content_type"] = "MANAGEMENT_DISPLAY"
            check["threshold"] = {"type": "display"}
            reclassified += 1
            print(f"  RECLASSIFIED: {cid} -> MANAGEMENT_DISPLAY")

        # Fix 3: Add threshold values
        if cid in THRESHOLDS:
            t = check.get("threshold", {})
            t.update(THRESHOLDS[cid])
            check["threshold"] = t
            thresholds_added += 1
            print(f"  THRESHOLD: {cid} -> red/yellow/clear added")
        elif (
            check.get("threshold", {}).get("type") == "tiered"
            and not check.get("threshold", {}).get("red")
            and cid not in DISPLAY_IDS
        ):
            # Track evaluative checks we didn't fix (outside triage scope)
            unknown_threshold_ids.add(cid)

        new_checks.append(check)

    data["checks"] = new_checks
    data["total_checks"] = len(new_checks)

    # Write back
    with open(CHECKS_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")  # trailing newline

    print(f"\n--- Summary ---")
    print(f"Original checks: {original_count}")
    print(f"Deleted: {deleted}")
    print(f"Reclassified to MANAGEMENT_DISPLAY: {reclassified}")
    print(f"Thresholds added: {thresholds_added}")
    print(f"New check count: {len(new_checks)}")

    if unknown_threshold_ids:
        print(f"\nStill empty tiered (outside triage scope): {len(unknown_threshold_ids)}")
        for cid in sorted(unknown_threshold_ids):
            print(f"  {cid}")

    # Validate
    # 1. No empty tiered among triage-targeted checks
    triage_targeted = (DISPLAY_IDS | set(THRESHOLDS.keys())) - DELETE_IDS
    empty_targeted = [
        c
        for c in new_checks
        if c["id"] in triage_targeted
        and c.get("threshold", {}).get("type") == "tiered"
        and not c.get("threshold", {}).get("red")
    ]
    assert len(empty_targeted) == 0, f"Still {len(empty_targeted)} empty among targeted checks: {[c['id'] for c in empty_targeted]}"

    # 2. Check count
    assert len(new_checks) == original_count - deleted, f"Expected {original_count - deleted} checks, got {len(new_checks)}"

    print("\nAll validations passed.")


if __name__ == "__main__":
    main()
