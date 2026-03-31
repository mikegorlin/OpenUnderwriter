# Empty Tiered Threshold Triage

**Date**: 2026-02-20
**Source**: `src/do_uw/brain/checks.json` (v9.0.0, 388 total checks)

## Summary

159 checks have `content_type: "EVALUATIVE_CHECK"` with `threshold.type: "tiered"` but **no red/yellow/clear values**. These are checks that claim to evaluate risk but have no way to actually trigger alerts.

For comparison, 91 EVALUATIVE_CHECK tiered checks DO have populated thresholds.

### Category Counts (Assessment)

| Category | Count | Description |
|---|---|---|
| **TEXT_SIGNAL** | 67 | Detect presence/absence of a specific risk event or text pattern |
| **DISPLAY** | 38 | Actually just displaying information; should be reclassified to MANAGEMENT_DISPLAY or CONTEXT_DISPLAY content_type |
| **NEEDS_THRESHOLD** | 37 | Genuinely evaluative; need numeric or text-based red/yellow/clear values |
| **COUNT_THRESHOLD** | 17 | Return counts of items; need count-based thresholds |

**Total: 159**

---

## STOCK.* (8 checks)

### STOCK.INSIDER (2 checks)

| ID | Name | Assessment | Rationale |
|---|---|---|---|
| `STOCK.INSIDER.notable_activity` | Notable Activity | **NEEDS_THRESHOLD** | field_key=`ceo_cfo_selling_pct`. Needs thresholds like red: ">25% of holdings sold in 90 days", yellow: ">10% of holdings sold in 90 days". Currently the sibling `STOCK.INSIDER.summary` has thresholds but this one doesn't. |
| `STOCK.INSIDER.cluster_timing` | Cluster Timing | **TEXT_SIGNAL** | field_key=`cluster_selling`, expected_type=boolean. Detects whether multiple insiders sold in same window. Threshold should be presence-based: red: "Cluster selling detected pre-announcement", yellow: "Cluster selling detected", clear: "No cluster pattern". |

### STOCK.SHORT (2 checks)

| ID | Name | Assessment | Rationale |
|---|---|---|---|
| `STOCK.SHORT.trend` | Trend | **NEEDS_THRESHOLD** | field_key=`short_interest_ratio`. Needs numeric thresholds: red: "Short ratio >10 days OR increasing >50% QoQ", yellow: "Short ratio >5 days OR increasing >25% QoQ", clear: "Short ratio <5 days and stable/declining". |
| `STOCK.SHORT.report` | Report | **TEXT_SIGNAL** | field_key=`short_interest_pct`. Detects whether activist short reports have been published. Threshold should be: red: "Named short seller report published", yellow: "Elevated short interest without identified report", clear: "No short seller reports". |

### STOCK.VALUATION (4 checks)

| ID | Name | Assessment | Rationale |
|---|---|---|---|
| `STOCK.VALUATION.pe_ratio` | PE Ratio | **NEEDS_THRESHOLD** | field_key=`current_price`, expected_type=numeric. Classic numeric threshold: red: "PE >50x OR negative earnings", yellow: "PE >30x", clear: "PE <30x". Sector-relative would be even better. |
| `STOCK.VALUATION.ev_ebitda` | EV/EBITDA | **NEEDS_THRESHOLD** | field_key=`current_price`. Needs: red: "EV/EBITDA >25x OR negative EBITDA", yellow: "EV/EBITDA >15x", clear: "EV/EBITDA <15x". |
| `STOCK.VALUATION.premium_discount` | Premium/Discount | **NEEDS_THRESHOLD** | field_key=`returns_1y`. Measures premium over peers/sector. Needs: red: ">50% premium to peers", yellow: ">25% premium to peers", clear: "<25% premium". |
| `STOCK.VALUATION.peg_ratio` | PEG Ratio | **NEEDS_THRESHOLD** | field_key=`current_price`. Needs: red: "PEG >3.0 OR negative", yellow: "PEG >2.0", clear: "PEG <2.0". |

---

## FIN.* (12 checks)

### FIN.PROFIT (1 check)

| ID | Name | Assessment | Rationale |
|---|---|---|---|
| `FIN.PROFIT.trend` | Trend | **NEEDS_THRESHOLD** | field_key=`financial_health_narrative`. Evaluates margin trends. Needs: red: "Margins declining >500bps YoY OR loss-making", yellow: "Margins declining >200bps YoY", clear: "Stable or expanding margins". |

### FIN.ACCT (5 checks)

| ID | Name | Assessment | Rationale |
|---|---|---|---|
| `FIN.ACCT.auditor` | Auditor | **TEXT_SIGNAL** | field_key=`auditor_opinion`. Detects audit opinion type. red: "Going concern OR adverse opinion OR disclaimer", yellow: "Qualified opinion OR auditor change", clear: "Unqualified opinion, no change". |
| `FIN.ACCT.internal_controls` | Internal Controls | **TEXT_SIGNAL** | field_key=`material_weaknesses`, expected_type=boolean. red: "Material weakness disclosed", yellow: "Significant deficiency disclosed", clear: "No MW or SD". |
| `FIN.ACCT.sec_correspondence` | SEC Correspondence | **COUNT_THRESHOLD** | field_key=`financial_health_narrative`. Counts SEC comment letters. red: ">3 comment letters in 12 months OR accounting-focused letters", yellow: "1-3 comment letters in 12 months", clear: "No recent comment letters". |
| `FIN.ACCT.quality_indicators` | Quality Indicators | **NEEDS_THRESHOLD** | field_key=`altman_z_score`. Altman Z-Score is a well-known metric. red: "Z-Score <1.81 (distress zone)", yellow: "Z-Score 1.81-2.99 (grey zone)", clear: "Z-Score >2.99 (safe zone)". |
| `FIN.ACCT.earnings_manipulation` | Earnings Manipulation | **NEEDS_THRESHOLD** | field_key=`beneish_m_score`. Beneish M-Score is a well-known metric. red: "M-Score >-1.78 (likely manipulator)", yellow: "M-Score between -2.22 and -1.78 (grey zone)", clear: "M-Score <-2.22 (unlikely manipulator)". |

### FIN.GUIDE (4 checks)

| ID | Name | Assessment | Rationale |
|---|---|---|---|
| `FIN.GUIDE.current` | Current | **TEXT_SIGNAL** | field_key=`financial_health_narrative`. Detects whether company currently provides guidance. red: "Guidance recently withdrawn or suspended", yellow: "Guidance lowered or narrowed negatively", clear: "Guidance maintained or raised". |
| `FIN.GUIDE.philosophy` | Philosophy | **DISPLAY** | field_key=`financial_health_narrative`. "Philosophy" of guidance provision is informational context (aggressive vs conservative), not really evaluative. Should be MANAGEMENT_DISPLAY. |
| `FIN.GUIDE.earnings_reaction` | Earnings Reaction | **NEEDS_THRESHOLD** | field_key=`financial_health_narrative`. Measures stock reaction to earnings. red: ">10% drop on earnings", yellow: ">5% drop on earnings", clear: "Neutral or positive reaction". |
| `FIN.GUIDE.analyst_consensus` | Analyst Consensus | **NEEDS_THRESHOLD** | field_key=`financial_health_narrative`. Measures consensus direction. red: "Consensus estimates declining >10%", yellow: "Estimates declining 5-10%", clear: "Estimates stable or rising". |

### FIN.SECTOR (2 checks)

| ID | Name | Assessment | Rationale |
|---|---|---|---|
| `FIN.SECTOR.energy` | Energy | **DISPLAY** | category=CONTEXT_DISPLAY. Sector-specific risk factors for energy companies. This is contextual information, not evaluative. Should be MANAGEMENT_DISPLAY. |
| `FIN.SECTOR.retail` | Retail | **DISPLAY** | category=CONTEXT_DISPLAY. Sector-specific risk factors for retail companies. This is contextual information, not evaluative. Should be MANAGEMENT_DISPLAY. |

---

## LIT.* (30 checks)

### LIT.REG (16 checks)

All LIT.REG checks follow the same pattern: they detect specific types of regulatory actions. Most have `field_key: "regulatory_count"` which suggests they're counting occurrences. These are all **TEXT_SIGNAL** -- they detect presence/absence of specific regulatory action types. The signal IS the presence of the action.

| ID | Name | Assessment | Rationale |
|---|---|---|---|
| `LIT.REG.state_ag` | State AG Action | **TEXT_SIGNAL** | Presence of state AG investigation/action. red: "Active state AG enforcement action", yellow: "State AG inquiry disclosed", clear: "No state AG activity". |
| `LIT.REG.subpoena` | Subpoena | **TEXT_SIGNAL** | Presence of government subpoena. red: "DOJ/SEC subpoena disclosed", yellow: "Other government subpoena", clear: "No subpoenas disclosed". |
| `LIT.REG.comment_letters` | Comment Letters | **COUNT_THRESHOLD** | field_key=`comment_letter_count`. red: ">3 comment letters in 12 months OR re-opened correspondence", yellow: "1-3 comment letters in 12 months", clear: "None in 12 months". |
| `LIT.REG.deferred_pros` | Deferred Prosecution | **TEXT_SIGNAL** | Presence of DPA/NPA. red: "Active DPA/NPA in effect", yellow: "DPA/NPA expired within 2 years", clear: "No DPA/NPA history". |
| `LIT.REG.wells_notice` | Wells Notice | **TEXT_SIGNAL** | field_key=`wells_notice`. red: "Wells notice received", yellow: "Prior Wells notice (resolved)", clear: "No Wells notice history". |
| `LIT.REG.consent_order` | Consent Order | **TEXT_SIGNAL** | Presence of consent order. red: "Active consent order in effect", yellow: "Consent order expired within 2 years", clear: "No consent orders". |
| `LIT.REG.cease_desist` | Cease & Desist | **TEXT_SIGNAL** | Presence of cease and desist order. red: "Active C&D order", yellow: "C&D issued within 3 years", clear: "No C&D orders". |
| `LIT.REG.civil_penalty` | Civil Penalty | **TEXT_SIGNAL** | Presence of civil penalty. Dollar amounts refine severity but presence is itself a signal. red: "Civil penalty imposed >$10M OR >1% revenue", yellow: "Civil penalty imposed <$10M", clear: "No civil penalties". |
| `LIT.REG.dol_audit` | DOL Audit | **TEXT_SIGNAL** | Presence of Department of Labor audit. red: "Active DOL investigation with findings", yellow: "DOL audit disclosed", clear: "No DOL activity". |
| `LIT.REG.epa_action` | EPA Action | **TEXT_SIGNAL** | Presence of EPA enforcement action. red: "Active EPA enforcement/Superfund liability", yellow: "EPA inquiry or notice of violation", clear: "No EPA activity". |
| `LIT.REG.osha_citation` | OSHA Citation | **TEXT_SIGNAL** | Presence of OSHA citation. red: "Willful/repeat citation OR fatality investigation", yellow: "Serious citation", clear: "No OSHA citations". |
| `LIT.REG.cfpb_action` | CFPB Action | **TEXT_SIGNAL** | Presence of CFPB enforcement action. red: "Active CFPB enforcement action", yellow: "CFPB inquiry or CID", clear: "No CFPB activity". |
| `LIT.REG.fdic_order` | FDIC Order | **TEXT_SIGNAL** | Presence of FDIC enforcement order. red: "Active FDIC enforcement order", yellow: "FDIC MOU or informal action", clear: "No FDIC activity". |
| `LIT.REG.fda_warning` | FDA Warning | **TEXT_SIGNAL** | Presence of FDA warning letter/action. red: "FDA warning letter OR consent decree", yellow: "FDA 483 observation or untitled letter", clear: "No FDA activity". |
| `LIT.REG.foreign_gov` | Foreign Government | **TEXT_SIGNAL** | Presence of foreign government investigation/action. red: "Foreign government enforcement action", yellow: "Foreign government inquiry disclosed", clear: "No foreign government activity". |
| `LIT.REG.state_action` | State Action | **TEXT_SIGNAL** | Presence of state-level regulatory action. red: "Active state regulatory enforcement", yellow: "State regulatory inquiry", clear: "No state regulatory activity". |

### LIT.OTHER (14 checks)

All LIT.OTHER checks detect specific litigation types. Most have `field_key: "regulatory_count"` which is likely a misnomer -- these should be counting litigation matters by type.

| ID | Name | Assessment | Rationale |
|---|---|---|---|
| `LIT.OTHER.product` | Product Liability | **COUNT_THRESHOLD** | Counts product liability matters. red: ">5 active product liability matters OR class action", yellow: "1-5 active matters", clear: "No product liability matters". |
| `LIT.OTHER.employment` | Employment | **COUNT_THRESHOLD** | Counts employment litigation. red: ">5 active employment matters OR class/collective action", yellow: "1-5 active employment matters", clear: "No employment litigation". |
| `LIT.OTHER.ip` | IP Litigation | **COUNT_THRESHOLD** | Counts IP litigation matters. red: ">3 active IP matters OR patent troll targeting", yellow: "1-3 active IP matters", clear: "No IP litigation". |
| `LIT.OTHER.environmental` | Environmental | **COUNT_THRESHOLD** | Counts environmental litigation/liability. red: "Superfund liability OR >$10M environmental reserves", yellow: "Active environmental litigation", clear: "No environmental matters". |
| `LIT.OTHER.contract` | Contract | **COUNT_THRESHOLD** | Counts material contract disputes. red: ">3 material contract disputes OR >10% revenue at risk", yellow: "1-3 active contract disputes", clear: "No material contract disputes". |
| `LIT.OTHER.aggregate` | Aggregate | **COUNT_THRESHOLD** | field_key=`active_matter_count`. Total count across all types. red: ">10 total active matters", yellow: "5-10 active matters", clear: "<5 active matters". |
| `LIT.OTHER.class_action` | Class Action (non-SCA) | **COUNT_THRESHOLD** | Counts non-securities class actions. red: ">2 active class actions", yellow: "1-2 active class actions", clear: "No non-SCA class actions". |
| `LIT.OTHER.antitrust` | Antitrust | **TEXT_SIGNAL** | Presence of antitrust investigation/litigation. red: "Active DOJ/FTC antitrust investigation OR class action", yellow: "Antitrust inquiry disclosed", clear: "No antitrust matters". |
| `LIT.OTHER.trade_secret` | Trade Secret | **COUNT_THRESHOLD** | Counts trade secret litigation. red: ">2 active trade secret cases OR involving key technology", yellow: "1-2 active trade secret cases", clear: "No trade secret litigation". |
| `LIT.OTHER.whistleblower` | Whistleblower | **TEXT_SIGNAL** | field_key=`whistleblower_count`. Presence of whistleblower claims. red: "Qui tam or SEC whistleblower complaint filed", yellow: "Internal whistleblower complaint disclosed", clear: "No whistleblower activity". |
| `LIT.OTHER.cyber_breach` | Cyber Breach | **TEXT_SIGNAL** | Presence of data breach/cyber incident. red: "Material data breach disclosed OR breach litigation", yellow: "Cyber incident disclosed without litigation", clear: "No cyber breaches". |
| `LIT.OTHER.bankruptcy` | Bankruptcy | **TEXT_SIGNAL** | Presence of bankruptcy-related litigation. red: "Bankruptcy/restructuring proceedings", yellow: "Material vendor/customer bankruptcy affecting company", clear: "No bankruptcy matters". |
| `LIT.OTHER.foreign_suit` | Foreign Suit | **COUNT_THRESHOLD** | Counts foreign litigation matters. red: ">3 active foreign suits OR material foreign judgment", yellow: "1-3 active foreign suits", clear: "No foreign litigation". |
| `LIT.OTHER.gov_contract` | Government Contract | **TEXT_SIGNAL** | Presence of government contract disputes. red: "Active False Claims Act suit OR debarment risk", yellow: "Government contract dispute or protest", clear: "No government contract matters". |

---

## GOV.* (54 checks)

### GOV.BOARD (9 checks)

All GOV.BOARD checks have `category: CONTEXT_DISPLAY`, but they are typed as EVALUATIVE_CHECK. Most have `field_key: "governance_score"`. These are a mix: some genuinely evaluate risk (departures, overboarding) while others are more informational (committees, expertise profile).

| ID | Name | Assessment | Rationale |
|---|---|---|---|
| `GOV.BOARD.tenure` | Tenure | **NEEDS_THRESHOLD** | Average board tenure. red: "Average tenure >15 years (entrenchment risk)", yellow: "Average tenure >10 years", clear: "Average tenure <10 years". |
| `GOV.BOARD.overboarding` | Overboarding | **NEEDS_THRESHOLD** | field_key=`overboarded_directors`. red: ">2 directors on 4+ boards OR CEO on 2+ outside boards", yellow: "1-2 directors on 4+ boards", clear: "No overboarded directors". |
| `GOV.BOARD.departures` | Departures | **COUNT_THRESHOLD** | field_key=`departures_18mo`. red: ">3 departures in 18 months OR sudden resignation", yellow: "2-3 departures in 18 months", clear: "0-1 departures (normal refresh)". |
| `GOV.BOARD.attendance` | Attendance | **NEEDS_THRESHOLD** | Board meeting attendance rate. red: "Any director <75% attendance", yellow: "Any director <85% attendance", clear: "All directors >85% attendance". |
| `GOV.BOARD.expertise` | Expertise | **DISPLAY** | Board skills/expertise matrix. This is informational context about what expertise the board has. Not evaluative. Should be MANAGEMENT_DISPLAY. |
| `GOV.BOARD.refresh_activity` | Refresh Activity | **DISPLAY** | Whether the board has added new directors recently. Informational. Should be MANAGEMENT_DISPLAY. |
| `GOV.BOARD.meetings` | Meetings | **NEEDS_THRESHOLD** | Number of board meetings per year. red: "<4 meetings per year", yellow: "4-6 meetings per year", clear: ">6 meetings per year". |
| `GOV.BOARD.committees` | Committees | **DISPLAY** | Committee structure (audit, comp, nom/gov). This is structural information. Should be MANAGEMENT_DISPLAY. |
| `GOV.BOARD.succession` | Succession | **TEXT_SIGNAL** | Whether CEO succession plan exists. red: "No succession plan AND CEO >65 OR tenured >15 years", yellow: "No disclosed succession plan", clear: "Succession plan disclosed". |

### GOV.PAY (14 checks)

Most GOV.PAY checks have `category: CONTEXT_DISPLAY`. They cover executive compensation details. Some are genuinely evaluative (clawback policy, exec loans) while many are informational (401k match, pension, perks details).

| ID | Name | Assessment | Rationale |
|---|---|---|---|
| `GOV.PAY.ceo_total` | CEO Total Comp | **NEEDS_THRESHOLD** | field_key=`ceo_pay_ratio`. CEO pay ratio to median employee. red: "Pay ratio >500:1 OR total comp >$50M", yellow: "Pay ratio >300:1 OR total comp >$25M", clear: "Pay ratio <300:1". |
| `GOV.PAY.ceo_structure` | CEO Pay Structure | **DISPLAY** | Breakdown of salary/bonus/equity/other. Informational display of compensation composition. Should be MANAGEMENT_DISPLAY. |
| `GOV.PAY.peer_comparison` | Peer Comparison | **NEEDS_THRESHOLD** | CEO pay relative to peers. red: ">75th percentile of peers AND underperformance", yellow: ">75th percentile of peers", clear: "At or below 75th percentile". |
| `GOV.PAY.clawback` | Clawback | **TEXT_SIGNAL** | Presence/strength of clawback policy. red: "No clawback policy beyond SOX minimum", yellow: "SOX-minimum clawback only", clear: "Robust clawback policy beyond SOX requirements". |
| `GOV.PAY.related_party` | Related Party | **TEXT_SIGNAL** | Presence of related party transactions. red: "Material RPTs involving executives", yellow: "RPTs disclosed but immaterial", clear: "No RPTs beyond standard". |
| `GOV.PAY.golden_para` | Golden Parachute | **NEEDS_THRESHOLD** | Magnitude of change-in-control payments. red: "Golden parachute >5x salary OR >$50M", yellow: "Golden parachute >3x salary", clear: "<3x salary or no golden parachute". |
| `GOV.PAY.incentive_metrics` | Incentive Metrics | **DISPLAY** | What metrics drive incentive comp. Informational, not evaluative. Should be MANAGEMENT_DISPLAY. |
| `GOV.PAY.equity_burn` | Equity Burn | **NEEDS_THRESHOLD** | Annual equity dilution from compensation. red: "Equity burn rate >3% annually", yellow: "Equity burn rate >2% annually", clear: "<2% burn rate". |
| `GOV.PAY.hedging` | Hedging | **TEXT_SIGNAL** | Whether executives are allowed to hedge company stock. red: "Hedging permitted with no restrictions", yellow: "Partial hedging restrictions", clear: "Full hedging prohibition". |
| `GOV.PAY.perks` | Perks | **DISPLAY** | Executive perquisite details. Informational display. Should be MANAGEMENT_DISPLAY. |
| `GOV.PAY.401k_match` | 401K Match | **DISPLAY** | 401K match details. Informational display. Should be MANAGEMENT_DISPLAY. |
| `GOV.PAY.deferred_comp` | Deferred Comp | **DISPLAY** | Deferred compensation plan details. Informational display. Should be MANAGEMENT_DISPLAY. |
| `GOV.PAY.pension` | Pension | **DISPLAY** | Pension plan details. Informational display. Should be MANAGEMENT_DISPLAY. |
| `GOV.PAY.exec_loans` | Executive Loans | **TEXT_SIGNAL** | Presence of executive loans (prohibited under SOX). red: "Executive loans disclosed (SOX violation risk)", yellow: "Historic loans grandfathered pre-SOX", clear: "No executive loans". |

### GOV.RIGHTS (10 checks)

All GOV.RIGHTS checks have `category: CONTEXT_DISPLAY` and `signal_type: STRUCTURAL`. These describe governance provisions. Some are evaluative (dual class = bad for shareholders) while others are more structural descriptions.

| ID | Name | Assessment | Rationale |
|---|---|---|---|
| `GOV.RIGHTS.dual_class` | Dual Class | **TEXT_SIGNAL** | field_key=`dual_class`. Presence of dual-class share structure. red: "Dual-class with >50% voting control by insiders", yellow: "Dual-class structure present", clear: "Single class, one-share-one-vote". |
| `GOV.RIGHTS.voting_rights` | Voting Rights | **DISPLAY** | Description of voting rights structure. When dual_class fires, this provides detail. Should be MANAGEMENT_DISPLAY. |
| `GOV.RIGHTS.bylaws` | Bylaws | **DISPLAY** | Description of bylaw provisions. Informational display of key provisions. Should be MANAGEMENT_DISPLAY. |
| `GOV.RIGHTS.takeover` | Takeover | **TEXT_SIGNAL** | Presence of anti-takeover defenses. red: "Poison pill in effect OR multiple anti-takeover provisions", yellow: "Poison pill on shelf OR 1-2 anti-takeover provisions", clear: "Minimal anti-takeover provisions". |
| `GOV.RIGHTS.proxy_access` | Proxy Access | **TEXT_SIGNAL** | Availability of proxy access for shareholders. red: "No proxy access AND no special meeting rights", yellow: "Restrictive proxy access (>5% ownership, >3 year holding)", clear: "Proxy access at 3%/3-year standard or better". |
| `GOV.RIGHTS.forum_select` | Forum Selection | **DISPLAY** | Description of forum selection clause. Informational. Should be MANAGEMENT_DISPLAY. |
| `GOV.RIGHTS.supermajority` | Supermajority | **TEXT_SIGNAL** | Presence of supermajority voting requirements. red: "Supermajority required for bylaw amendments AND board removal", yellow: "Supermajority for some provisions", clear: "Simple majority for all provisions". |
| `GOV.RIGHTS.action_consent` | Action by Consent | **TEXT_SIGNAL** | Whether shareholders can act by written consent. red: "No written consent AND no special meeting right", yellow: "Written consent restricted", clear: "Written consent permitted". |
| `GOV.RIGHTS.special_mtg` | Special Meeting | **TEXT_SIGNAL** | Threshold for calling special meetings. red: "Special meeting rights denied or >25% threshold", yellow: "Special meeting at 15-25% threshold", clear: "Special meeting at <15% threshold". |
| `GOV.RIGHTS.classified` | Classified Board | **TEXT_SIGNAL** | field_key=`classified_board`. Presence of classified/staggered board. red: "Classified board with no declassification proposal", yellow: "Classified board with declassification underway", clear: "Annual election of all directors". |

### GOV.ACTIVIST (14 checks)

All GOV.ACTIVIST checks have `category: DECISION_DRIVING` and `signal_type: EVENT`. These detect specific activist-related events. Most use `field_key: "activist_present"` suggesting boolean detection.

| ID | Name | Assessment | Rationale |
|---|---|---|---|
| `GOV.ACTIVIST.13d_filings` | 13D Filings | **TEXT_SIGNAL** | Presence of Schedule 13D (activist intent). red: "Activist 13D filed with stated objectives", yellow: "13D filed but passive language", clear: "No 13D filings". |
| `GOV.ACTIVIST.campaigns` | Campaigns | **TEXT_SIGNAL** | Active activist campaigns. red: "Active public campaign by known activist", yellow: "Private engagement by activist disclosed", clear: "No activist campaigns". |
| `GOV.ACTIVIST.proxy_contests` | Proxy Contests | **TEXT_SIGNAL** | Proxy contest activity. red: "Active proxy contest with dissident slate", yellow: "Proxy contest threatened or settled", clear: "No proxy contests". |
| `GOV.ACTIVIST.settle_agree` | Settlement Agreement | **TEXT_SIGNAL** | Activist settlement agreements. red: "Settlement with board seats granted + operational demands", yellow: "Settlement with board seats only", clear: "No activist settlements". |
| `GOV.ACTIVIST.short_activism` | Short Activism | **TEXT_SIGNAL** | Short seller activist campaigns. red: "Named short seller report published + position disclosed", yellow: "Short seller commentary/thesis circulating", clear: "No short activism". |
| `GOV.ACTIVIST.demands` | Demands | **TEXT_SIGNAL** | Shareholder demand letters. red: "Shareholder demand for investigation or action", yellow: "Informal shareholder pressure", clear: "No shareholder demands". |
| `GOV.ACTIVIST.schedule_13g` | Schedule 13G | **DISPLAY** | field_key=`institutional_pct`. 13G filings indicate passive large holders. Informational about ownership concentration. Should be MANAGEMENT_DISPLAY. |
| `GOV.ACTIVIST.wolf_pack` | Wolf Pack | **TEXT_SIGNAL** | Multiple activists coordinating. red: "Multiple activists accumulating simultaneously", yellow: "Signs of activist coordination", clear: "No wolf pack indicators". |
| `GOV.ACTIVIST.board_seat` | Board Seat | **TEXT_SIGNAL** | Activist board representation. red: "Activist holds >2 board seats", yellow: "Activist holds 1-2 board seats", clear: "No activist board representation". |
| `GOV.ACTIVIST.dissident` | Dissident | **TEXT_SIGNAL** | Dissident shareholder activity. red: "Dissident proxy solicitation filed", yellow: "Dissident shareholder communication", clear: "No dissident activity". |
| `GOV.ACTIVIST.withhold` | Withhold | **NEEDS_THRESHOLD** | Withhold vote campaigns. red: "Withhold campaign with >30% votes against director(s)", yellow: "Withhold campaign with >20% votes against", clear: "<20% votes against all directors". |
| `GOV.ACTIVIST.proposal` | Proposal | **COUNT_THRESHOLD** | Shareholder proposals. red: ">3 shareholder proposals OR proposal receiving >50% support", yellow: "1-3 shareholder proposals", clear: "No shareholder proposals". |
| `GOV.ACTIVIST.consent` | Consent | **TEXT_SIGNAL** | Written consent solicitation. red: "Active consent solicitation", yellow: "Consent solicitation threatened", clear: "No consent solicitation activity". |
| `GOV.ACTIVIST.standstill` | Standstill | **TEXT_SIGNAL** | Standstill agreement status. red: "Standstill expiring within policy period", yellow: "Active standstill agreement", clear: "No standstill agreements (or none needed)". |

### GOV.INSIDER (7 checks)

All GOV.INSIDER checks have `category: DECISION_DRIVING` and `signal_type: EVENT`. These evaluate insider trading patterns.

| ID | Name | Assessment | Rationale |
|---|---|---|---|
| `GOV.INSIDER.form4_filings` | Form 4 Filings | **DISPLAY** | field_key=`insider_pct`. Summary of Form 4 filing activity. This is the raw data display; the evaluative sibling checks (cluster_sales, unusual_timing) do the assessment. Should be MANAGEMENT_DISPLAY. |
| `GOV.INSIDER.10b5_plans` | 10b5-1 Plans | **DISPLAY** | Presence of 10b5-1 trading plans. Whether insiders use plans is context, not evaluative. Should be MANAGEMENT_DISPLAY. |
| `GOV.INSIDER.plan_adoption` | Plan Adoption | **TEXT_SIGNAL** | Timing of 10b5-1 plan adoption/modification. red: "Plan adopted/modified <30 days before material event", yellow: "Plan adopted/modified <90 days before material event", clear: "Plans adopted with adequate cooling period". |
| `GOV.INSIDER.cluster_sales` | Cluster Sales | **TEXT_SIGNAL** | Multiple insiders selling simultaneously. red: ">3 insiders selling in same 10-day window", yellow: "2-3 insiders selling in same 30-day window", clear: "No cluster selling pattern". |
| `GOV.INSIDER.unusual_timing` | Unusual Timing | **TEXT_SIGNAL** | Sales timing relative to events. red: "Sales within 30 days before negative disclosure", yellow: "Sales pattern deviates from historical norm", clear: "Consistent with historical pattern". |
| `GOV.INSIDER.executive_sales` | Executive Sales | **NEEDS_THRESHOLD** | field_key=`insider_pct`. Magnitude of executive selling. red: ">25% of holdings sold in 90 days by C-suite", yellow: ">10% of holdings sold in 90 days by C-suite", clear: "<10% sold or net buying". |
| `GOV.INSIDER.ownership_pct` | Ownership Pct | **NEEDS_THRESHOLD** | field_key=`insider_pct`. Insider ownership level. red: "Insider ownership <1% (no skin in game)", yellow: "Insider ownership declining >50% in 12 months", clear: "Insider ownership stable or increasing". |

---

## FWRD.* (55 checks)

### FWRD.EVENT (8 checks)

| ID | Name | Assessment | Rationale |
|---|---|---|---|
| `FWRD.EVENT.customer_retention` | Customer Retention | **TEXT_SIGNAL** | Detects customer retention risks post-event. red: "Key customer loss disclosed or at risk", yellow: "Customer concentration risk in transition", clear: "Customer base stable". |
| `FWRD.EVENT.employee_retention` | Employee Retention | **TEXT_SIGNAL** | Detects employee retention risks. red: "Key employee departures or mass attrition", yellow: "Retention risk disclosed", clear: "Workforce stable". |
| `FWRD.EVENT.integration` | Integration | **TEXT_SIGNAL** | M&A integration risk assessment. red: "Integration problems disclosed OR missed milestones", yellow: "Integration in progress with disclosed challenges", clear: "No pending integration or on track". |
| `FWRD.EVENT.proxy_deadline` | Proxy Deadline | **DISPLAY** | Upcoming proxy filing deadline date. This is a calendar display, not evaluative. Should be MANAGEMENT_DISPLAY. |
| `FWRD.EVENT.19-BIOT` | 19-Biot | **DISPLAY** | Cryptic name -- appears to be a sector-specific biotech check template with no definition. No description, no detection, no extraction hints. Likely placeholder. Should be deleted or fleshed out. |
| `FWRD.EVENT.20-BIOT` | 20-Biot | **DISPLAY** | Same as above -- biotech placeholder with no substance. Should be deleted or fleshed out. |
| `FWRD.EVENT.21-BIOT` | 21-Biot | **DISPLAY** | Same as above -- biotech placeholder with no substance. Should be deleted or fleshed out. |
| `FWRD.EVENT.22-HLTH` | 22-Hlth | **DISPLAY** | Same pattern -- healthcare sector placeholder with no substance. Should be deleted or fleshed out. |

### FWRD.WARN (32 checks)

All FWRD.WARN checks have `category: DECISION_DRIVING` and `signal_type: EVENT`. These are forward-looking warning signals. None have data_strategy or extraction_hints. They are the most "aspirational" checks -- they name important risk signals but have no implementation backing.

**Employee/Sentiment Signals (7 checks)**

| ID | Name | Assessment | Rationale |
|---|---|---|---|
| `FWRD.WARN.glassdoor_sentiment` | Glassdoor Sentiment | **NEEDS_THRESHOLD** | Employee satisfaction rating trends. red: "Rating <3.0 OR decline >0.5 in 12 months", yellow: "Rating <3.5 OR decline >0.3 in 12 months", clear: "Rating >3.5 and stable/improving". |
| `FWRD.WARN.indeed_reviews` | Indeed Reviews | **NEEDS_THRESHOLD** | Similar to Glassdoor. red: "Rating <3.0 OR significant negative trend", yellow: "Rating declining", clear: "Rating stable/positive". |
| `FWRD.WARN.blind_posts` | Blind Posts | **TEXT_SIGNAL** | Anonymous employee posts flagging issues. red: "Viral posts alleging fraud/misconduct", yellow: "Elevated negative anonymous posts", clear: "Normal activity levels". |
| `FWRD.WARN.linkedin_headcount` | LinkedIn Headcount | **NEEDS_THRESHOLD** | Headcount trajectory from LinkedIn. red: "Headcount declining >10% in 6 months (non-announced)", yellow: "Headcount declining >5%", clear: "Stable or growing headcount". |
| `FWRD.WARN.linkedin_departures` | LinkedIn Departures | **NEEDS_THRESHOLD** | Executive/key employee departures visible on LinkedIn. red: ">3 senior departures in 90 days", yellow: "2-3 notable departures in 90 days", clear: "Normal attrition". |
| `FWRD.WARN.social_sentiment` | Social Sentiment | **TEXT_SIGNAL** | Social media sentiment trends. red: "Viral negative campaign or boycott", yellow: "Elevated negative sentiment trending", clear: "Normal sentiment". |
| `FWRD.WARN.journalism_activity` | Journalism Activity | **TEXT_SIGNAL** | Investigative journalism targeting company. red: "Investigative piece published by major outlet", yellow: "Known investigative journalist inquiring", clear: "Normal media coverage". |

**Product/Customer Signals (6 checks)**

| ID | Name | Assessment | Rationale |
|---|---|---|---|
| `FWRD.WARN.g2_reviews` | G2 Reviews | **NEEDS_THRESHOLD** | B2B software review trends. red: "Rating declining and below category average", yellow: "Rating declining", clear: "Rating stable or improving". |
| `FWRD.WARN.trustpilot_trend` | Trustpilot Trend | **NEEDS_THRESHOLD** | Consumer review trends. red: "Rating <2.0 OR declining >1.0 in 6 months", yellow: "Rating declining", clear: "Stable or improving". |
| `FWRD.WARN.app_ratings` | App Ratings | **NEEDS_THRESHOLD** | Mobile app rating trends. red: "Rating <3.0 OR declining >0.5 in 6 months", yellow: "Rating declining", clear: "Stable or improving". |
| `FWRD.WARN.customer_churn_signals` | Customer Churn Signals | **TEXT_SIGNAL** | Evidence of customer departure. red: "Key customer departure confirmed OR >10% churn rate disclosed", yellow: "Elevated churn indicators", clear: "Normal retention". |
| `FWRD.WARN.contract_disputes` | Contract Disputes | **COUNT_THRESHOLD** | Active contract dispute activity. red: ">3 active contract disputes OR material revenue at risk", yellow: "1-3 active disputes", clear: "No contract disputes". |
| `FWRD.WARN.partner_stability` | Partner Stability | **TEXT_SIGNAL** | Key partner/channel stability. red: "Key partner termination or bankruptcy", yellow: "Partner relationship strain disclosed", clear: "Partnerships stable". |

**Regulatory Complaint Signals (3 checks)**

| ID | Name | Assessment | Rationale |
|---|---|---|---|
| `FWRD.WARN.cfpb_complaints` | CFPB Complaints | **COUNT_THRESHOLD** | Consumer Financial Protection Bureau complaint volume. red: "Complaint volume >2x industry average", yellow: "Complaint volume rising >25% QoQ", clear: "Complaint volume at or below industry average". |
| `FWRD.WARN.fda_medwatch` | FDA MedWatch | **COUNT_THRESHOLD** | FDA adverse event reports. red: "Adverse event spike >3x baseline OR safety signal identified", yellow: "Elevated adverse event reporting", clear: "Normal adverse event levels". |
| `FWRD.WARN.nhtsa_complaints` | NHTSA Complaints | **COUNT_THRESHOLD** | Vehicle safety complaints. red: "NHTSA investigation opened OR recall pending", yellow: "Elevated complaint volume for specific issue", clear: "Normal complaint levels". |

**Whistleblower/Legal (3 checks)**

| ID | Name | Assessment | Rationale |
|---|---|---|---|
| `FWRD.WARN.whistleblower_exposure` | Whistleblower Exposure | **TEXT_SIGNAL** | Forward-looking whistleblower risk. red: "Active whistleblower complaint with regulatory engagement", yellow: "Whistleblower complaint filed", clear: "No whistleblower activity". |
| `FWRD.WARN.compliance_hiring` | Compliance Hiring | **TEXT_SIGNAL** | Surge in compliance hiring as leading indicator. red: "Significant compliance hiring surge (>5 positions, senior level)", yellow: "Notable compliance hiring increase", clear: "Normal hiring patterns". |
| `FWRD.WARN.legal_hiring` | Legal Hiring | **TEXT_SIGNAL** | Surge in legal hiring as leading indicator. red: "Significant legal/litigation hiring surge", yellow: "Notable legal hiring increase", clear: "Normal hiring patterns". |

**Financial Warning Signals (7 checks)**

| ID | Name | Assessment | Rationale |
|---|---|---|---|
| `FWRD.WARN.vendor_payment_delays` | Vendor Payment Delays | **TEXT_SIGNAL** | Evidence of stretching payables. red: "DPO increasing >20 days YoY OR vendor complaints in news", yellow: "DPO increasing >10 days YoY", clear: "DPO stable". |
| `FWRD.WARN.job_posting_patterns` | Job Posting Patterns | **TEXT_SIGNAL** | Hiring freeze or mass role removal as leading indicator. red: "Mass job posting removal (>50% in 30 days)", yellow: "Significant hiring slowdown", clear: "Normal posting patterns". |
| `FWRD.WARN.zone_of_insolvency` | Zone of Insolvency | **NEEDS_THRESHOLD** | Near-insolvency risk assessment. red: "Current ratio <1.0 AND negative working capital AND declining revenue", yellow: "Current ratio <1.0 OR negative working capital", clear: "Current ratio >1.5 and adequate liquidity". |
| `FWRD.WARN.goodwill_risk` | Goodwill Risk | **NEEDS_THRESHOLD** | Goodwill impairment risk. red: "Goodwill >50% of total assets AND market cap < book value", yellow: "Goodwill >30% of total assets OR recent acquisition", clear: "Goodwill <30% of assets". |
| `FWRD.WARN.impairment_risk` | Impairment Risk | **NEEDS_THRESHOLD** | Asset impairment risk beyond goodwill. red: "Market cap < book value sustained >90 days", yellow: "Market cap approaching book value", clear: "Market cap well above book value". |
| `FWRD.WARN.revenue_quality` | Revenue Quality | **TEXT_SIGNAL** | Revenue recognition quality signals. red: "Revenue recognition changes OR restatement risk", yellow: "Aggressive revenue recognition noted by auditor", clear: "Standard revenue recognition". |
| `FWRD.WARN.margin_pressure` | Margin Pressure | **NEEDS_THRESHOLD** | Forward margin pressure. red: "Gross margin declining >500bps AND operating leverage negative", yellow: "Gross margin declining >300bps", clear: "Margins stable or expanding". |

**Tech/AI-Specific Signals (4 checks)**

| ID | Name | Assessment | Rationale |
|---|---|---|---|
| `FWRD.WARN.ai_revenue_concentration` | AI Revenue Concentration | **NEEDS_THRESHOLD** | Revenue dependency on AI/ML. red: ">50% revenue from AI-related products with regulatory uncertainty", yellow: ">25% AI revenue concentration", clear: "<25% AI revenue". |
| `FWRD.WARN.hyperscaler_dependency` | Hyperscaler Dependency | **NEEDS_THRESHOLD** | Cloud provider concentration risk. red: ">75% infrastructure on single hyperscaler", yellow: ">50% on single hyperscaler", clear: "Multi-cloud or diversified". |
| `FWRD.WARN.gpu_allocation` | GPU Allocation | **TEXT_SIGNAL** | GPU supply chain risk. red: "GPU allocation constraint impacting production", yellow: "GPU supply risk disclosed in filings", clear: "Adequate compute supply". |
| `FWRD.WARN.data_center_risk` | Data Center Risk | **TEXT_SIGNAL** | Data center concentration/capacity risk. red: "Single data center dependency OR capacity constraints", yellow: "Data center concentration risk", clear: "Diversified data center strategy". |

**Operational Signals (2 checks)**

| ID | Name | Assessment | Rationale |
|---|---|---|---|
| `FWRD.WARN.capex_discipline` | CapEx Discipline | **NEEDS_THRESHOLD** | Capital expenditure discipline. red: "CapEx >2x depreciation AND declining ROIC", yellow: "CapEx >1.5x depreciation", clear: "CapEx aligned with depreciation". |
| `FWRD.WARN.working_capital_trends` | Working Capital Trends | **NEEDS_THRESHOLD** | Working capital trajectory. red: "Working capital negative AND deteriorating", yellow: "Working capital declining >20% YoY", clear: "Working capital stable or improving". |

### FWRD.MACRO (15 checks)

All FWRD.MACRO checks have `category: CONTEXT_DISPLAY` and `signal_type: STRUCTURAL`. These describe macro/industry risk factors. They are context for the underwriter, not evaluative triggers.

| ID | Name | Assessment | Rationale |
|---|---|---|---|
| `FWRD.MACRO.sector_performance` | Sector Performance | **DISPLAY** | How the company's sector is performing. Context, not evaluative. Should be MANAGEMENT_DISPLAY. |
| `FWRD.MACRO.peer_issues` | Peer Issues | **DISPLAY** | Whether peers face similar D&O issues. Context. Should be MANAGEMENT_DISPLAY. |
| `FWRD.MACRO.industry_consolidation` | Industry Consolidation | **DISPLAY** | M&A activity in the sector. Context. Should be MANAGEMENT_DISPLAY. |
| `FWRD.MACRO.disruptive_tech` | Disruptive Tech | **DISPLAY** | Technology disruption threats. Context. Should be MANAGEMENT_DISPLAY. |
| `FWRD.MACRO.interest_rate_sensitivity` | Interest Rate Sensitivity | **DISPLAY** | Company's sensitivity to rate changes. Context. Should be MANAGEMENT_DISPLAY. |
| `FWRD.MACRO.inflation_impact` | Inflation Impact | **DISPLAY** | Inflation exposure. Context. Should be MANAGEMENT_DISPLAY. |
| `FWRD.MACRO.fx_exposure` | FX Exposure | **DISPLAY** | Foreign exchange risk exposure. Context. Should be MANAGEMENT_DISPLAY. |
| `FWRD.MACRO.commodity_impact` | Commodity Impact | **DISPLAY** | Commodity price exposure. Context. Should be MANAGEMENT_DISPLAY. |
| `FWRD.MACRO.labor_market` | Labor Market | **DISPLAY** | Labor market conditions relevant to company. Context. Should be MANAGEMENT_DISPLAY. |
| `FWRD.MACRO.regulatory_changes` | Regulatory Changes | **DISPLAY** | Upcoming regulatory changes affecting sector. Context. Should be MANAGEMENT_DISPLAY. |
| `FWRD.MACRO.legislative_risk` | Legislative Risk | **DISPLAY** | Pending legislation affecting company. Context. Should be MANAGEMENT_DISPLAY. |
| `FWRD.MACRO.trade_policy` | Trade Policy | **DISPLAY** | Trade policy/tariff exposure. Context. Should be MANAGEMENT_DISPLAY. |
| `FWRD.MACRO.geopolitical_exposure` | Geopolitical Exposure | **DISPLAY** | Geopolitical risk exposure. Context. Should be MANAGEMENT_DISPLAY. |
| `FWRD.MACRO.supply_chain_disruption` | Supply Chain Disruption | **DISPLAY** | Supply chain vulnerability. Context. Should be MANAGEMENT_DISPLAY. |
| `FWRD.MACRO.climate_transition_risk` | Climate Transition Risk | **DISPLAY** | Climate transition risk exposure. Context. Should be MANAGEMENT_DISPLAY. |

---

## Summary by Assessment Category

### DISPLAY (38 checks) -- Should be reclassified

These checks are not evaluating risk; they are displaying contextual information. They should have their `content_type` changed from `EVALUATIVE_CHECK` to `MANAGEMENT_DISPLAY` (or just remove the tiered threshold and set to `"type": "display"`).

| Prefix | Count | Checks |
|---|---|---|
| FIN.GUIDE | 1 | philosophy |
| FIN.SECTOR | 2 | energy, retail |
| FWRD.EVENT | 5 | proxy_deadline, 19-BIOT, 20-BIOT, 21-BIOT, 22-HLTH |
| FWRD.MACRO | 15 | ALL (sector_performance through climate_transition_risk) |
| GOV.ACTIVIST | 1 | schedule_13g |
| GOV.BOARD | 3 | expertise, refresh_activity, committees |
| GOV.INSIDER | 2 | form4_filings, 10b5_plans |
| GOV.PAY | 6 | ceo_structure, incentive_metrics, perks, 401k_match, deferred_comp, pension |
| GOV.RIGHTS | 3 | voting_rights, bylaws, forum_select |

### NEEDS_THRESHOLD (37 checks) -- Need numeric red/yellow/clear values

These are genuinely evaluative checks that compare values against thresholds. They need specific numeric or descriptive red/yellow/clear values.

| Prefix | Count | Checks |
|---|---|---|
| FIN.ACCT | 2 | quality_indicators (Z-Score), earnings_manipulation (M-Score) |
| FIN.GUIDE | 2 | earnings_reaction, analyst_consensus |
| FIN.PROFIT | 1 | trend |
| FWRD.WARN | 15 | glassdoor_sentiment, indeed_reviews, linkedin_headcount, linkedin_departures, g2_reviews, trustpilot_trend, app_ratings, zone_of_insolvency, goodwill_risk, impairment_risk, ai_revenue_concentration, hyperscaler_dependency, margin_pressure, capex_discipline, working_capital_trends |
| GOV.ACTIVIST | 1 | withhold |
| GOV.BOARD | 4 | tenure, overboarding, attendance, meetings |
| GOV.INSIDER | 2 | executive_sales, ownership_pct |
| GOV.PAY | 4 | ceo_total, peer_comparison, golden_para, equity_burn |
| STOCK.INSIDER | 1 | notable_activity |
| STOCK.SHORT | 1 | trend |
| STOCK.VALUATION | 4 | pe_ratio, ev_ebitda, premium_discount, peg_ratio |

### COUNT_THRESHOLD (17 checks) -- Need count-based thresholds

These checks count occurrences of specific items (lawsuits, proposals, departures, complaints). Thresholds should be count-based (e.g., red: >5, yellow: 2-5, clear: 0-1).

| Prefix | Count | Checks |
|---|---|---|
| FIN.ACCT | 1 | sec_correspondence |
| FWRD.WARN | 4 | cfpb_complaints, fda_medwatch, nhtsa_complaints, contract_disputes |
| GOV.ACTIVIST | 1 | proposal |
| GOV.BOARD | 1 | departures |
| LIT.OTHER | 9 | product, employment, ip, environmental, contract, aggregate, class_action, trade_secret, foreign_suit |
| LIT.REG | 1 | comment_letters |

### TEXT_SIGNAL (67 checks) -- Need presence-based evaluation

These checks detect the presence or absence of specific risk events or text patterns. Thresholds should be presence-based (e.g., red: "Active enforcement action", yellow: "Inquiry disclosed", clear: "No activity").

| Prefix | Count | Checks |
|---|---|---|
| FIN.ACCT | 2 | auditor, internal_controls |
| FIN.GUIDE | 1 | current |
| FWRD.EVENT | 3 | customer_retention, employee_retention, integration |
| FWRD.WARN | 13 | blind_posts, social_sentiment, journalism_activity, customer_churn_signals, partner_stability, whistleblower_exposure, compliance_hiring, legal_hiring, vendor_payment_delays, job_posting_patterns, revenue_quality, gpu_allocation, data_center_risk |
| GOV.ACTIVIST | 11 | 13d_filings, campaigns, proxy_contests, settle_agree, short_activism, demands, wolf_pack, board_seat, dissident, consent, standstill |
| GOV.BOARD | 1 | succession |
| GOV.INSIDER | 3 | plan_adoption, cluster_sales, unusual_timing |
| GOV.PAY | 4 | clawback, related_party, hedging, exec_loans |
| GOV.RIGHTS | 7 | dual_class, takeover, proxy_access, supermajority, action_consent, special_mtg, classified |
| LIT.OTHER | 5 | antitrust, whistleblower, cyber_breach, bankruptcy, gov_contract |
| LIT.REG | 15 | state_ag, subpoena, deferred_pros, wells_notice, consent_order, cease_desist, civil_penalty, dol_audit, epa_action, osha_citation, cfpb_action, fdic_order, fda_warning, foreign_gov, state_action |
| STOCK.INSIDER | 1 | cluster_timing |
| STOCK.SHORT | 1 | report |

---

## Recommended Actions

### Priority 1: Reclassify DISPLAY checks (38 checks)
These are the easiest wins. Change `content_type` from `EVALUATIVE_CHECK` to `MANAGEMENT_DISPLAY` and change `threshold.type` from `tiered` to `display`. This reduces the "broken evaluative check" count from 159 to 121 and correctly represents their intent.

### Priority 2: Populate TEXT_SIGNAL thresholds (67 checks)
These are relatively straightforward -- the presence/absence of a specific event IS the signal. Suggested thresholds are provided in the detail tables above. Most follow the pattern: red = active enforcement/action, yellow = inquiry/disclosed, clear = no activity.

### Priority 3: Populate NEEDS_THRESHOLD values (37 checks)
These need specific numeric thresholds sourced from D&O underwriting expertise. Some have well-known values (Z-Score distress zones, M-Score cutoffs). Others need industry-specific calibration.

### Priority 4: Populate COUNT_THRESHOLD values (17 checks)
These need count-based thresholds. Some can use standard D&O benchmarks (e.g., >5 active lawsuits = elevated). Others need calibration by sector and company size.

### Priority 5: Delete or flesh out placeholder checks (4 checks)
FWRD.EVENT.19-BIOT, 20-BIOT, 21-BIOT, and 22-HLTH appear to be placeholder stubs for sector-specific checks. They have no descriptions, no extraction hints, and cryptic names. They should either be deleted or properly defined with descriptions, data strategies, and thresholds.
