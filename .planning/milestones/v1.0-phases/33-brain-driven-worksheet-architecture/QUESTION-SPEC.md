# Question Specification — D&O Underwriting System

**Generated:** 2026-02-20
**Source Framework:** v6 Taxonomy (231 questions, 45 subsections)
**Check Registry:** brain/checks.json (396 checks, 389 AUTO-executed)
**Backtest Company:** AAPL (Apple Inc.)

## Status Summary

- Total questions: 231
- ANSWERED: 152 (65.8%)
- PARTIAL: 46 (19.9%)
- DISPLAY ONLY: 19 (8.2%)
- NO CHECKS: 14 (6.1%)
- Total checks: 396 (EVALUATIVE_CHECK: 276, MANAGEMENT_DISPLAY: 99, INFERENCE_PATTERN: 21)
- Execution modes: AUTO: 389, FALLBACK_ONLY: 2, MANUAL_ONLY: 3, SECTOR_CONDITIONAL: 2

### Processing Type Legend

| Type | Meaning | Check Content Type |
|------|---------|--------------------|
| DISPLAY | Data shown without evaluation | MANAGEMENT_DISPLAY |
| EVALUATE | Data compared against thresholds | EVALUATIVE_CHECK (numeric/boolean) |
| COMPUTE | Calculation from multiple inputs | EVALUATIVE_CHECK (formula-based) |
| INFER | Pattern recognition across signals | INFERENCE_PATTERN |

### Status Legend

| Status | Meaning |
|--------|---------|
| ANSWERED | Has TRIGGERED or CLEAR checks -- data acquired AND evaluated |
| PARTIAL | Has some data (INFO) but cannot fully evaluate -- missing thresholds or wrong data type |
| DISPLAY ONLY | Only MANAGEMENT_DISPLAY checks -- shows context but does not evaluate risk |
| NO DATA | All checks SKIPPED -- data not acquired |
| NO CHECKS | No checks mapped to this question/subsection |

---

# 1. COMPANY

## 1.1 Identity & Classification (5 questions, 8 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 1.1.1 | What industry is this company in? (SIC, NAICS, GICS codes and sector/industry classification) | EVALUATE | SEC 10-K, yfinance | sec_client, market_client | company_profile | BIZ.CLASS.primary, BIZ.CLASS.secondary | ANSWERED |
| 1.1.2 | What are the key company metrics? (Market cap, enterprise value, employee count, revenue, headquarters) | DISPLAY | SEC 10-K, yfinance | sec_client, market_client | company_profile | BIZ.SIZE.market_cap, BIZ.SIZE.employees, BIZ.SIZE.revenue_ttm | ANSWERED |
| 1.1.3 | What lifecycle stage is this company in (IPO, growth, mature, distressed, SPAC)? | DISPLAY | SEC 10-K, yfinance | sec_client, market_client | company_profile | BIZ.SIZE.growth_trajectory, BIZ.SIZE.public_tenure | ANSWERED |
| 1.1.4 | What is the state of incorporation and what legal regime applies? | EVALUATE | SEC 10-K, SCAC | sec_client, litigation_client | company_profile, sca_extractor | BIZ.CLASS.litigation_history | ANSWERED |
| 1.1.5 | What exchange is it listed on and is it a Foreign Private Issuer? | DISPLAY | SEC 10-K, yfinance | sec_client, market_client | company_profile | BIZ.SIZE.market_cap | ANSWERED |

**Checks Detail:**
- `BIZ.CLASS.primary` [MANAGEMENT_DISPLAY]: Routes to `risk_classification`. AAPL=MEGA (INFO).
- `BIZ.CLASS.secondary` [MANAGEMENT_DISPLAY]: Routes to `risk_classification`. AAPL=MEGA (INFO).
- `BIZ.CLASS.litigation_history` [EVALUATIVE_CHECK]: Routes to `total_sca_count`. AAPL=1.0 (TRIGGERED red, threshold >0).
- `BIZ.SIZE.employees` [MANAGEMENT_DISPLAY]: Routes to `employee_count`. AAPL=150000 (INFO).
- `BIZ.SIZE.growth_trajectory` [MANAGEMENT_DISPLAY]: Routes to `years_public`. AAPL=45 (INFO).
- `BIZ.SIZE.market_cap` [MANAGEMENT_DISPLAY]: Routes to `market_cap`. AAPL=3.76T (INFO).
- `BIZ.SIZE.public_tenure` [MANAGEMENT_DISPLAY]: Routes to `years_public`. AAPL=45 (INFO).
- `BIZ.SIZE.revenue_ttm` [MANAGEMENT_DISPLAY]: Routes to `section_summary`. AAPL=summary text (INFO).

**Gap Analysis:** Subsection is well-covered. Only 1 evaluative check (litigation_history); rest are display. Industry classification codes (SIC/NAICS/GICS) are returned but not individually evaluated.
**Health:** GREEN

---

## 1.2 Business Model & Revenue (6 questions, 8 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 1.2.1 | What is the company's primary business model and revenue type? | DISPLAY | SEC 10-K | sec_client | ten_k_converters, filing_sections | BIZ.MODEL.description, BIZ.MODEL.revenue_type | DISPLAY ONLY |
| 1.2.2 | How is revenue broken down by segment? | DISPLAY | SEC 10-K | sec_client | ten_k_converters | BIZ.MODEL.revenue_segment | DISPLAY ONLY |
| 1.2.3 | What are the key products/services and how concentrated is the product portfolio? | DISPLAY | SEC 10-K | sec_client | ten_k_converters | BIZ.MODEL.revenue_segment | DISPLAY ONLY |
| 1.2.4 | What is the cost structure and operating leverage? | DISPLAY | SEC 10-K | sec_client | ten_k_converters | BIZ.MODEL.cost_structure, BIZ.MODEL.leverage_ops | DISPLAY ONLY |
| 1.2.5 | What is the recurring vs non-recurring revenue mix? | DISPLAY | SEC 10-K | sec_client | ten_k_converters | BIZ.MODEL.revenue_type | DISPLAY ONLY |
| 1.2.6 | Is there an "Innovation/Investment Gap" -- does the company's public AI/tech narrative diverge from actual R&D/CAPEX spend? | DISPLAY | SEC 10-K | sec_client | ten_k_converters | BIZ.MODEL.capital_intensity | DISPLAY ONLY |

**Checks Detail:**
- `BIZ.MODEL.description` [MANAGEMENT_DISPLAY]: Routes to `business_description`. Displays Item 1 text.
- `BIZ.MODEL.revenue_type` [MANAGEMENT_DISPLAY]: Routes to `revenue_type_analysis`. 10-K mention count.
- `BIZ.MODEL.revenue_segment` [MANAGEMENT_DISPLAY]: Routes to `revenue_segment_breakdown`. 10-K mention count.
- `BIZ.MODEL.revenue_geo` [MANAGEMENT_DISPLAY]: Routes to `revenue_geographic_mix`. AAPL=Ireland, Japan, etc.
- `BIZ.MODEL.cost_structure` [MANAGEMENT_DISPLAY]: Routes to `cost_structure_analysis`. 10-K mention count.
- `BIZ.MODEL.leverage_ops` [MANAGEMENT_DISPLAY]: Routes to `operating_leverage`. 10-K mention count.
- `BIZ.MODEL.regulatory_dep` [MANAGEMENT_DISPLAY]: Routes to `model_regulatory_dependency`. 10-K mention count.
- `BIZ.MODEL.capital_intensity` [MANAGEMENT_DISPLAY]: Routes to `capital_intensity_ratio`. Not mentioned for AAPL.

**Gap Analysis:** All 8 checks are MANAGEMENT_DISPLAY -- data is shown but never evaluated against risk thresholds. Revenue concentration, product portfolio concentration, and cost structure should have evaluative thresholds for D&O risk (e.g., single-product dependency > 70% revenue = red flag). The capital_intensity check for innovation gap (1.2.6) returns "Not mentioned" for AAPL.
**Health:** YELLOW -- data flows through, but no risk evaluation occurs.

---

## 1.3 Operations & Dependencies (9 questions, 13 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 1.3.1 | How concentrated is the customer base? | EVALUATE | SEC 10-K | sec_client | ten_k_converters | BIZ.DEPEND.customer_conc | ANSWERED |
| 1.3.2 | How dependent is the company on key suppliers or single-source inputs? | EVALUATE | SEC 10-K | sec_client | ten_k_converters | BIZ.DEPEND.supplier_conc | ANSWERED |
| 1.3.3 | How complex and vulnerable is the supply chain? | EVALUATE | SEC 10-K | sec_client | ten_k_converters | BIZ.DEPEND.distribution, BIZ.DEPEND.macro_sensitivity | ANSWERED |
| 1.3.4 | What is the workforce profile and labor risk? | EVALUATE | SEC 10-K | sec_client | ten_k_converters | BIZ.DEPEND.labor, BIZ.DEPEND.key_person | ANSWERED |
| 1.3.5 | What technology, IP, or regulatory dependencies exist? | EVALUATE | SEC 10-K | sec_client | ten_k_converters | BIZ.DEPEND.tech_dep, BIZ.DEPEND.regulatory_dep | ANSWERED |
| 1.3.6 | What is the government contract exposure? | EVALUATE | SEC 10-K | sec_client | ten_k_converters | BIZ.DEPEND.contract_terms, BIZ.DEPEND.capital_dep | ANSWERED |
| 1.3.7 | What is the data/privacy risk profile? (PII, PHI, financial, children's data; CCPA, GDPR, HIPAA) | DISPLAY | SEC 10-K | sec_client | ten_k_converters | BIZ.UNI.cyber_posture, BIZ.UNI.cyber_business | ANSWERED |
| 1.3.8 | Does the company have sector-specific hazard exposure? (Binary flags: Opioid, PFAS, Crypto, Cannabis, China VIE, AI/ML, Nuclear/defense, Social media/content) | DISPLAY | SEC 10-K | sec_client | ten_k_converters | BIZ.UNI.ai_claims | ANSWERED |
| 1.3.9 | Is there ESG/greenwashing risk? | EVALUATE | SEC 10-K | sec_client | ten_k_converters | BIZ.DEPEND.regulatory_dep | ANSWERED |

**Checks Detail:**
- `BIZ.DEPEND.customer_conc` [EVALUATIVE_CHECK]: Routes to `customer_concentration`. AAPL="Not mentioned" (INFO -- percentage check could not evaluate).
- `BIZ.DEPEND.supplier_conc` [EVALUATIVE_CHECK]: Routes to `supplier_concentration`. AAPL=1 mention (INFO -- qualitative).
- `BIZ.DEPEND.tech_dep` [EVALUATIVE_CHECK]: Routes to `technology_dependency_count`. AAPL=2 (TRIGGERED yellow, threshold >1).
- `BIZ.DEPEND.key_person` [EVALUATIVE_CHECK]: Routes to `customer_concentration` (re-routed in Phase 33-02 from employee_count). AAPL="Not mentioned" (INFO).
- `BIZ.DEPEND.regulatory_dep` [EVALUATIVE_CHECK]: Routes to `regulatory_dependency_count`. AAPL=2 (TRIGGERED yellow, threshold >1).
- `BIZ.DEPEND.capital_dep` [EVALUATIVE_CHECK]: Routes to `capital_dependency_count`. AAPL=0 (CLEAR).
- `BIZ.DEPEND.macro_sensitivity` [EVALUATIVE_CHECK]: Routes to `macro_sensitivity_count`. AAPL=10 (TRIGGERED red, threshold >5).
- `BIZ.DEPEND.distribution` [EVALUATIVE_CHECK]: Routes to `distribution_channels_count`. AAPL=4 (TRIGGERED red, threshold >3).
- `BIZ.DEPEND.contract_terms` [EVALUATIVE_CHECK]: Routes to `contract_terms_count`. AAPL=0 (CLEAR).
- `BIZ.DEPEND.labor` [EVALUATIVE_CHECK]: Routes to `labor_risk_flag_count` (re-routed in Phase 33-02 from employee_count). AAPL=150000 (TRIGGERED red -- still reading employee_count despite routing fix, needs data extraction update).
- `BIZ.UNI.ai_claims` [MANAGEMENT_DISPLAY]: Routes to `ai_risk_exposure`. AAPL=9 mentions (INFO).
- `BIZ.UNI.cyber_business` [MANAGEMENT_DISPLAY]: Routes to `cyber_business_risk`. AAPL="Not mentioned" (INFO).
- `BIZ.UNI.cyber_posture` [MANAGEMENT_DISPLAY]: Routes to `cybersecurity_posture`. AAPL=9 mentions (INFO).

**Gap Analysis:** Strong evaluative coverage with 10 EVALUATIVE_CHECKs. Known false trigger: BIZ.DEPEND.labor reads employee_count (150,000) instead of labor risk flag count, causing false red. Customer concentration returns "Not mentioned" for AAPL because 10-K does not break out customer percentages (no >10% customer). Supplier concentration is qualitative text, not a numeric value.
**Health:** GREEN (with known false trigger on labor check)

---

## 1.4 Corporate Structure & Complexity (3 questions, 3 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 1.4.1 | How many subsidiaries and legal entities exist? | EVALUATE | SEC 10-K Exhibit 21 | sec_client | ten_k_converters | BIZ.STRUCT.subsidiary_count | NO CHECKS* |
| 1.4.2 | Are there VIEs, SPEs, or off-balance-sheet structures? | EVALUATE | SEC 10-K | sec_client | ten_k_converters | BIZ.STRUCT.vie_spe | NO CHECKS* |
| 1.4.3 | Are there related-party transactions or intercompany complexity? | EVALUATE | SEC 10-K, DEF 14A | sec_client | ten_k_converters | BIZ.STRUCT.related_party | NO CHECKS* |

**Checks Detail (newly added in Plan 33-03):**
- `BIZ.STRUCT.subsidiary_count` [EVALUATIVE_CHECK]: Not yet wired to data mapper. Needs extraction from Exhibit 21.
- `BIZ.STRUCT.vie_spe` [EVALUATIVE_CHECK]: Not yet wired to data mapper. Needs extraction from 10-K notes.
- `BIZ.STRUCT.related_party` [EVALUATIVE_CHECK]: Not yet wired to data mapper. Needs extraction from DEF 14A.

**Gap Analysis:** Checks were defined in checks.json (Plan 33-03) with v6_subsection_ids pointing to 1.4, but the data mapper, field routing, and extraction pipeline are not yet connected. AAPL backtest shows 0 checks executed for this subsection. These checks need: (1) extraction module for Exhibit 21 subsidiary list, (2) 10-K notes parser for VIE/SPE structures, (3) DEF 14A parser for related-party transactions, (4) field routing entries, (5) mapper integration.
**Health:** RED -- checks defined but not yet functional.

---

## 1.5 Geographic Footprint (2 questions, 1 check from audit + 4 in registry)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 1.5.1 | Where does the company operate (countries/regions)? | DISPLAY | SEC 10-K | sec_client | ten_k_converters | BIZ.MODEL.revenue_geo | DISPLAY ONLY |
| 1.5.2 | What jurisdiction-specific risks apply (FCPA, GDPR, sanctions, export controls)? | DISPLAY | SEC 10-K | sec_client | ten_k_converters | FWRD.MACRO.geopolitical_exposure | DISPLAY ONLY |

**Checks Detail:**
- `BIZ.MODEL.revenue_geo` [MANAGEMENT_DISPLAY]: Routes to `revenue_geographic_mix`. AAPL=Ireland, Japan, Canada, India, Mexico, Singapore, Thailand, Vietnam, Delaware, China (INFO). Cross-mapped from 1.2.
- `FWRD.MACRO.geopolitical_exposure` [MANAGEMENT_DISPLAY]: Cross-mapped from 1.8. AAPL=13 mentions (INFO).
- `LIT.REG.foreign_gov` [EVALUATIVE_CHECK]: Cross-mapped from 5.4. Routes to `foreign_gov_count`. AAPL=SKIPPED.
- `LIT.OTHER.foreign_suit` [EVALUATIVE_CHECK]: Cross-mapped from 5.6. Routes to `foreign_suit_count`. AAPL=SKIPPED.

**Gap Analysis:** Geographic presence is displayed but not evaluated for risk. No check evaluates FCPA exposure (presence in high-corruption countries), GDPR applicability (EU operations), or sanctions risk (China, Russia exposure). Revenue_geo returns a country list but does not flag high-risk jurisdictions. The cross-mapped litigation checks (foreign_gov, foreign_suit) SKIPPED because no data was found.
**Health:** YELLOW -- data present for display, no jurisdiction risk evaluation.

---

## 1.6 M&A & Corporate Transactions (6 questions, 2 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 1.6.1 | Are there pending M&A transactions? | EVALUATE | SEC 10-K, 8-K | sec_client | ten_k_converters, eight_k_converter | FWRD.EVENT.ma_closing | PARTIAL |
| 1.6.2 | What is the 2-3 year acquisition history (deal sizes, rationale, integration)? | EVALUATE | SEC 10-K | sec_client | ten_k_converters | FWRD.EVENT.ma_closing | PARTIAL |
| 1.6.3 | How much goodwill has accumulated and is there impairment risk? | EVALUATE | SEC 10-K, 10-Q | sec_client | financial_statements | FWRD.WARN.goodwill_risk | PARTIAL |
| 1.6.4 | What is the integration track record? | EVALUATE | SEC 10-K | sec_client | ten_k_converters | FWRD.EVENT.integration | PARTIAL |
| 1.6.5 | Has there been deal-related litigation? | EVALUATE | SEC 10-K, SCAC | sec_client, litigation_client | deal_litigation, sca_extractor | FWRD.WARN.contract_disputes | PARTIAL |
| 1.6.6 | Have there been divestitures, spin-offs, or capital markets transactions? | EVALUATE | SEC 10-K, 8-K | sec_client | ten_k_converters, capital_markets | FWRD.EVENT.ma_closing | PARTIAL |

**Checks Detail:**
- `FWRD.EVENT.ma_closing` [EVALUATIVE_CHECK]: Routes to forward event data. AAPL=0 (INFO -- qualitative check, no threshold evaluation).
- `FWRD.WARN.contract_disputes` [EVALUATIVE_CHECK]: Routes to 10-K text. AAPL="Not mentioned" (INFO -- qualitative check).

**Gap Analysis:** Only 2 checks for 6 questions. Both return INFO without evaluative thresholds being applied. Goodwill risk (1.6.3) has FWRD.WARN.goodwill_risk mapped to 3.6 (distress) which evaluated CLEAR for AAPL (debt_to_ebitda=0.6265), but no direct goodwill-to-assets ratio check exists. Deal litigation (1.6.5) lacks specific deal_litigation_count extraction. Integration track record (1.6.4) lacks structured extraction.
**Health:** YELLOW -- data flows through but no evaluative thresholds fire.

---

## 1.7 Competitive Position & Industry Dynamics (4 questions, 11 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 1.7.1 | What is the company's market position and competitive moat? | DISPLAY | SEC 10-K, yfinance | sec_client, market_client | company_profile, ten_k_converters | BIZ.COMP.market_position, BIZ.COMP.moat, BIZ.COMP.competitive_advantage | DISPLAY ONLY |
| 1.7.2 | Who are the direct peers and how do they compare? | DISPLAY | yfinance, SCAC | market_client, litigation_client | peer_group, sca_extractor | BIZ.COMP.market_share, BIZ.COMP.barriers_entry | DISPLAY ONLY |
| 1.7.3 | What is the peer litigation frequency (SCA contagion risk)? | DISPLAY | SCAC | litigation_client | sca_extractor | BIZ.COMP.peer_litigation | DISPLAY ONLY |
| 1.7.4 | What are the industry headwinds and tailwinds? | DISPLAY | SEC 10-K | sec_client | ten_k_converters | BIZ.COMP.headwinds, BIZ.COMP.industry_growth | DISPLAY ONLY |

**Checks Detail:**
- `BIZ.COMP.market_position` [MANAGEMENT_DISPLAY]: Routes to `sector`. AAPL=TECH (INFO).
- `BIZ.COMP.market_share` [MANAGEMENT_DISPLAY]: Routes to `sector`. AAPL=TECH (INFO).
- `BIZ.COMP.competitive_advantage` [MANAGEMENT_DISPLAY]: Routes to `sector`. AAPL=TECH (INFO).
- `BIZ.COMP.threat_assessment` [MANAGEMENT_DISPLAY]: Routes to `sector`. AAPL=TECH (INFO).
- `BIZ.COMP.barriers_entry` [MANAGEMENT_DISPLAY]: Routes to `barriers_to_entry`. AAPL="Not mentioned" (INFO).
- `BIZ.COMP.barriers` [MANAGEMENT_DISPLAY]: Routes to `barriers_to_entry`. AAPL="Not mentioned" (INFO).
- `BIZ.COMP.moat` [MANAGEMENT_DISPLAY]: Routes to `competitive_moat`. AAPL=13 IP mentions (INFO).
- `BIZ.COMP.industry_growth` [MANAGEMENT_DISPLAY]: Routes to `sector`. AAPL=TECH (INFO).
- `BIZ.COMP.headwinds` [MANAGEMENT_DISPLAY]: Routes to `industry_headwinds`. AAPL="Not mentioned" (INFO).
- `BIZ.COMP.consolidation` [MANAGEMENT_DISPLAY]: Routes to `sector`. AAPL=TECH (INFO).
- `BIZ.COMP.peer_litigation` [MANAGEMENT_DISPLAY]: Routes to `active_sca_count`. AAPL=0 (INFO).

**Gap Analysis:** All 11 checks are MANAGEMENT_DISPLAY. Multiple checks (market_position, market_share, competitive_advantage, threat_assessment, industry_growth, consolidation) all route to the same field (`sector`) and return "TECH" -- not informative. Peer litigation count is available (from SCAC) but returned as INFO display, not evaluated against a threshold. Barriers_to_entry extraction returns "Not mentioned" for AAPL. Industry headwinds extraction returns "Not mentioned" for AAPL. The competitive analysis extraction produces shallow results -- sector label only instead of structured competitive intelligence.
**Health:** YELLOW -- all display, no risk evaluation. Extraction quality is weak (sector label only).

---

## 1.8 Macro & Industry Environment (4 questions, 18 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 1.8.1 | How is the sector performing overall and are peers experiencing similar issues? | DISPLAY | SEC 10-K, yfinance | sec_client, market_client | company_profile | FWRD.MACRO.sector_performance, FWRD.MACRO.peer_issues | DISPLAY ONLY |
| 1.8.2 | Is the industry consolidating or facing disruptive technology threats? | DISPLAY | SEC 10-K | sec_client | ten_k_converters | FWRD.MACRO.industry_consolidation, FWRD.MACRO.disruptive_tech | DISPLAY ONLY |
| 1.8.3 | What macro factors materially affect this company (rates, FX, commodities, trade, labor)? | DISPLAY | SEC 10-K | sec_client | ten_k_converters | FWRD.MACRO.inflation_impact, FWRD.MACRO.fx_exposure, FWRD.MACRO.commodity_impact, FWRD.MACRO.trade_policy | DISPLAY ONLY |
| 1.8.4 | Are there regulatory, legislative, or geopolitical changes creating sector risk? | DISPLAY | SEC 10-K | sec_client | ten_k_converters | FWRD.MACRO.regulatory_changes, FWRD.MACRO.legislative_risk, FWRD.MACRO.geopolitical_exposure | DISPLAY ONLY |

**Checks Detail (all 18 MANAGEMENT_DISPLAY):**
- `FWRD.MACRO.sector_performance`: AAPL=5.03 (sector return). `FWRD.MACRO.peer_issues`: AAPL=3 (peer count).
- `FWRD.MACRO.industry_consolidation`: AAPL=5 mentions. `FWRD.MACRO.disruptive_tech`: AAPL=4 mentions.
- `FWRD.MACRO.climate_transition_risk`: AAPL=2 mentions. `FWRD.MACRO.supply_chain_disruption`: AAPL=1 mention.
- `FWRD.MACRO.trade_policy`: AAPL=10 mentions. `FWRD.MACRO.geopolitical_exposure`: AAPL=13 mentions.
- `FWRD.MACRO.fx_exposure`: AAPL=3 mentions. `FWRD.MACRO.inflation_impact`: AAPL=3 mentions.
- `FWRD.MACRO.commodity_impact`: "Not mentioned". `FWRD.MACRO.interest_rate_sensitivity`: "Not mentioned".
- `FWRD.MACRO.labor_market`: "Not mentioned". `FWRD.MACRO.legislative_risk`: "Not mentioned".
- `FWRD.MACRO.regulatory_changes`: AAPL=1 mention. Also includes BIZ.COMP checks cross-mapped here.

**Gap Analysis:** All 18 checks are MANAGEMENT_DISPLAY returning 10-K mention counts or "Not mentioned". No evaluative thresholds. Trade policy mention count (10) and geopolitical exposure (13) are high for AAPL but not flagged. This subsection is inherently contextual (macro factors), but some evaluative thresholds would help (e.g., geopolitical mentions > 10 = elevated exposure).
**Health:** YELLOW -- data flows through, but all display-only. Mention counts need threshold interpretation.

---

## 1.9 Employee & Workforce Signals (6 questions, 8 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 1.9.1 | What do employee review platforms indicate (Glassdoor, Indeed, Blind)? | EVALUATE | Web search (Glassdoor, Indeed, Blind) | web_search | N/A (not extracted) | FWRD.WARN.glassdoor_sentiment, FWRD.WARN.indeed_reviews, FWRD.WARN.blind_posts | PARTIAL |
| 1.9.2 | Are there unusual hiring patterns (compliance/legal hiring surge)? | EVALUATE | SEC 10-K, Web search | sec_client, web_search | ten_k_converters | FWRD.WARN.compliance_hiring, FWRD.WARN.job_posting_patterns | PARTIAL |
| 1.9.3 | Are there LinkedIn headcount or departure trends? | EVALUATE | Web search (LinkedIn) | web_search | N/A (not extracted) | FWRD.WARN.linkedin_departures, FWRD.WARN.linkedin_headcount | PARTIAL |
| 1.9.4 | Are there WARN Act or mass layoff signals? | EVALUATE | Web search | web_search | N/A (not extracted) | FWRD.WARN.legal_hiring | PARTIAL |
| 1.9.5 | What do department-level departures show? (Accounting/legal departures = stronger fraud signal) | EVALUATE | SEC 8-K, Web search | sec_client, web_search | eight_k_converter | FWRD.WARN.linkedin_departures | PARTIAL |
| 1.9.6 | What is the CEO approval rating trend? (Glassdoor CEO approval drop >20% = red flag) | EVALUATE | Web search (Glassdoor) | web_search | N/A (not extracted) | FWRD.WARN.glassdoor_sentiment | PARTIAL |

**Checks Detail:**
- `FWRD.WARN.glassdoor_sentiment` [EVALUATIVE_CHECK]: AAPL=SKIPPED (no Glassdoor data acquired).
- `FWRD.WARN.indeed_reviews` [EVALUATIVE_CHECK]: AAPL=SKIPPED (no Indeed data acquired).
- `FWRD.WARN.blind_posts` [EVALUATIVE_CHECK]: AAPL=SKIPPED (no Blind data acquired).
- `FWRD.WARN.compliance_hiring` [EVALUATIVE_CHECK]: AAPL=1 mention (INFO -- qualitative from 10-K).
- `FWRD.WARN.job_posting_patterns` [EVALUATIVE_CHECK]: AAPL=1 mention (INFO -- qualitative from 10-K).
- `FWRD.WARN.legal_hiring` [EVALUATIVE_CHECK]: AAPL=10 mentions (INFO -- qualitative from 10-K).
- `FWRD.WARN.linkedin_departures` [EVALUATIVE_CHECK]: AAPL=SKIPPED (no LinkedIn data acquired).
- `FWRD.WARN.linkedin_headcount` [EVALUATIVE_CHECK]: AAPL=SKIPPED (no LinkedIn data acquired).

**Gap Analysis:** 5 of 8 checks SKIPPED because web data sources (Glassdoor, Indeed, Blind, LinkedIn) are not acquired. The 3 checks that ran pulled from 10-K text search, which is a poor proxy for these questions. The data acquisition pipeline needs web scraping for employee review platforms and LinkedIn. These are "Hunt & Analyze" data type -- requires broad web search, not just filing extraction.
**Health:** RED -- majority of checks SKIPPED due to missing web data acquisition.

---

## 1.10 Customer & Product Signals (6 questions, 11 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 1.10.1 | Are there customer complaint trends (CFPB, app ratings, Trustpilot)? | EVALUATE | Web search, CFPB API | web_search | N/A (not extracted) | FWRD.WARN.cfpb_complaints, FWRD.WARN.app_ratings, FWRD.WARN.trustpilot_trend | PARTIAL |
| 1.10.2 | Are there product quality signals (FDA MedWatch, NHTSA complaints)? | EVALUATE | Web search, FDA/NHTSA APIs | web_search | N/A (not extracted) | FWRD.WARN.fda_medwatch, FWRD.WARN.nhtsa_complaints | PARTIAL |
| 1.10.3 | Are there customer churn or partner instability signals? | EVALUATE | SEC 10-K, Web search | sec_client, web_search | ten_k_converters | FWRD.WARN.customer_churn_signals, FWRD.WARN.partner_stability | PARTIAL |
| 1.10.4 | Are there vendor payment or supply chain stress signals? | EVALUATE | SEC 10-K, Web search | sec_client, web_search | ten_k_converters | FWRD.WARN.vendor_payment_delays | PARTIAL |
| 1.10.5 | What do web traffic and app download trends show? | EVALUATE | Web search | web_search | N/A (not extracted) | FWRD.WARN.g2_reviews | PARTIAL |
| 1.10.6 | What does scientific/academic community monitoring reveal? (PubPeer, Retraction Watch, KOL sentiment -- biotech/pharma) | EVALUATE | Web search | web_search | N/A (not extracted) | FWRD.WARN.social_sentiment | PARTIAL |

**Checks Detail:**
- `FWRD.WARN.cfpb_complaints` [EVALUATIVE_CHECK]: AAPL=SKIPPED (no CFPB data).
- `FWRD.WARN.app_ratings` [EVALUATIVE_CHECK]: AAPL=SKIPPED (no app store data).
- `FWRD.WARN.trustpilot_trend` [EVALUATIVE_CHECK]: AAPL=SKIPPED (no Trustpilot data).
- `FWRD.WARN.fda_medwatch` [EVALUATIVE_CHECK]: AAPL=SKIPPED (sector-conditional, not applicable).
- `FWRD.WARN.nhtsa_complaints` [EVALUATIVE_CHECK]: AAPL=SKIPPED (sector-conditional, not applicable).
- `FWRD.WARN.customer_churn_signals` [EVALUATIVE_CHECK]: AAPL="Not mentioned in 10-K" (INFO).
- `FWRD.WARN.partner_stability` [EVALUATIVE_CHECK]: AAPL="Not mentioned in 10-K" (INFO).
- `FWRD.WARN.vendor_payment_delays` [EVALUATIVE_CHECK]: AAPL="Not mentioned in 10-K" (INFO).
- `FWRD.WARN.g2_reviews` [EVALUATIVE_CHECK]: AAPL=SKIPPED (no G2 data).
- `FWRD.WARN.social_sentiment` [EVALUATIVE_CHECK]: AAPL=SKIPPED (no social data).
- `FWRD.WARN.journalism_activity` [EVALUATIVE_CHECK]: AAPL=SKIPPED (no journalism data).

**Gap Analysis:** 8 of 11 checks SKIPPED because external data sources (CFPB, app stores, Trustpilot, G2, social media, journalism) are not acquired. The 3 checks that ran searched 10-K text and found "Not mentioned" -- expected since these are external signals not in SEC filings. Like 1.9, this is "Hunt & Analyze" data requiring web search acquisition. Sector-conditional checks (FDA, NHTSA) correctly skip for non-applicable sectors.
**Health:** RED -- majority of checks SKIPPED due to missing web data acquisition.

---

## 1.11 Risk Calendar & Upcoming Catalysts (8 questions, 17 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 1.11.1 | When is the next earnings report and what's the miss risk? | EVALUATE | yfinance, SEC 8-K | market_client, sec_client | earnings_guidance | FWRD.EVENT.earnings_calendar, FWRD.EVENT.guidance_risk | ANSWERED |
| 1.11.2 | Are there pending regulatory decisions (FDA, FCC, etc.)? | EVALUATE | SEC 10-K, Web search | sec_client, web_search | ten_k_converters | FWRD.EVENT.regulatory_decision | ANSWERED |
| 1.11.3 | Are there M&A closings or shareholder votes? | EVALUATE | SEC 10-K, 8-K, DEF 14A | sec_client | ten_k_converters, eight_k_converter | FWRD.EVENT.ma_closing, FWRD.EVENT.shareholder_mtg | ANSWERED |
| 1.11.4 | Are there debt maturities or covenant tests in the next 12 months? | EVALUATE | SEC 10-K, 10-Q | sec_client | debt_analysis | FWRD.EVENT.debt_maturity, FWRD.EVENT.covenant_test | ANSWERED |
| 1.11.5 | Are there lockup expirations or warrant expiry? | EVALUATE | SEC filings | sec_client | capital_markets | FWRD.EVENT.lockup_expiry, FWRD.EVENT.warrant_expiry | ANSWERED |
| 1.11.6 | Are there contract renewals or customer retention milestones? | EVALUATE | SEC 10-K | sec_client | ten_k_converters | FWRD.EVENT.contract_renewal, FWRD.EVENT.customer_retention | ANSWERED |
| 1.11.7 | Are there litigation milestones (trial dates, settlement deadlines)? | EVALUATE | SEC 10-K, SCAC, CourtListener | sec_client, litigation_client | sca_extractor | FWRD.EVENT.litigation_milestone | ANSWERED |
| 1.11.8 | Are there industry-specific catalysts (PDUFA dates, patent cliffs)? | EVALUATE | SEC 10-K, Web search | sec_client, web_search | ten_k_converters | FWRD.EVENT.catalyst_dates | ANSWERED |

**Checks Detail:**
- `FWRD.EVENT.earnings_calendar` [EVALUATIVE_CHECK]: AAPL=0 (CLEAR). Evaluates miss risk.
- `FWRD.EVENT.guidance_risk` [EVALUATIVE_CHECK]: AAPL=0 (INFO -- qualitative).
- `FWRD.EVENT.regulatory_decision` [EVALUATIVE_CHECK]: AAPL=10 mentions (INFO -- qualitative).
- `FWRD.EVENT.ma_closing` [EVALUATIVE_CHECK]: AAPL=0 (INFO). Cross-mapped to 1.6.
- `FWRD.EVENT.shareholder_mtg` [MANAGEMENT_DISPLAY]: AAPL=92 days (INFO).
- `FWRD.EVENT.proxy_deadline` [MANAGEMENT_DISPLAY]: AAPL=92 days (INFO).
- `FWRD.EVENT.debt_maturity` [EVALUATIVE_CHECK]: AAPL=debt structure dict (INFO -- qualitative).
- `FWRD.EVENT.covenant_test` [EVALUATIVE_CHECK]: AAPL=debt structure dict (INFO -- qualitative).
- `FWRD.EVENT.lockup_expiry` [MANAGEMENT_DISPLAY]: AAPL=NOT_RUN (SECTOR_CONDITIONAL -- not applicable to mature companies).
- `FWRD.EVENT.warrant_expiry` [MANAGEMENT_DISPLAY]: AAPL=NOT_RUN (SECTOR_CONDITIONAL -- not applicable).
- `FWRD.EVENT.contract_renewal` [EVALUATIVE_CHECK]: AAPL="Not mentioned" (INFO).
- `FWRD.EVENT.customer_retention` [EVALUATIVE_CHECK]: AAPL="Not mentioned" (INFO).
- `FWRD.EVENT.employee_retention` [EVALUATIVE_CHECK]: AAPL=3 mentions (INFO).
- `FWRD.EVENT.litigation_milestone` [EVALUATIVE_CHECK]: AAPL=0 (INFO).
- `FWRD.EVENT.integration` [EVALUATIVE_CHECK]: AAPL=0 (INFO).
- `FWRD.EVENT.synergy` [EVALUATIVE_CHECK]: AAPL=0 (INFO).
- `FWRD.EVENT.catalyst_dates` [MANAGEMENT_DISPLAY]: AAPL=0 (INFO).

**Gap Analysis:** Only 1 check (earnings_calendar) produces evaluative CLEAR/TRIGGERED results. Most checks return INFO with qualitative values. Debt maturity returns a complex dict but does not extract specific near-term maturity amounts. Lockup/warrant correctly skip for mature companies. The risk calendar concept is sound but needs structured date extraction (next earnings, next trial date, debt maturity dates) rather than mention counts.
**Health:** GREEN (subsection functions, but most checks are qualitative INFO rather than evaluative)

---

# 2. MARKET

## 2.1 Stock Price Performance (5 questions, 8 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 2.1.1 | What's the stock's current position relative to its 52-week range? | EVALUATE | yfinance | market_client | extract_market, stock_performance | STOCK.PRICE.position, STOCK.PRICE.chart_comparison | ANSWERED |
| 2.1.2 | What is the stock's volatility profile and how does it compare to sector/peers? | EVALUATE | yfinance | market_client | extract_market, stock_performance | STOCK.PRICE.technical | ANSWERED |
| 2.1.3 | How does performance compare to the sector and peers? | EVALUATE | yfinance | market_client | extract_market, stock_performance | STOCK.PRICE.peer_relative | ANSWERED |
| 2.1.4 | Is there delisting risk? | EVALUATE | yfinance | market_client | extract_market | STOCK.PRICE.delisting_risk | ANSWERED |
| 2.1.5 | Does the MD&A exhibit "Abnormal Positive Tone" relative to quantitative financial reality? | EVALUATE | SEC 10-K | sec_client | ten_k_converters | NLP.MDA.tone_absolute | ANSWERED |

**Checks Detail:**
- `STOCK.PRICE.position` [EVALUATIVE_CHECK]: Routes to `decline_from_high`. AAPL=-11.38% (CLEAR).
- `STOCK.PRICE.chart_comparison` [EVALUATIVE_CHECK]: Routes to `decline_from_high`. AAPL=-11.38% (CLEAR).
- `STOCK.PRICE.peer_relative` [EVALUATIVE_CHECK]: Routes to `returns_1y`. AAPL=5.03% (CLEAR).
- `STOCK.PRICE.delisting_risk` [EVALUATIVE_CHECK]: Routes to `current_price`. AAPL=$255.78 (CLEAR).
- `STOCK.PRICE.technical` [EVALUATIVE_CHECK]: Routes to `volatility_90d`. AAPL=21.61% (CLEAR).
- `STOCK.PRICE.attribution` [EVALUATIVE_CHECK]: Routes to `decline_from_high`. AAPL=-11.38% (CLEAR).
- `STOCK.PRICE.returns_multi_horizon` [EVALUATIVE_CHECK]: Routes to `returns_1y`. AAPL=5.03% (INFO -- multi_period).
- `NLP.MDA.tone_absolute` [MANAGEMENT_DISPLAY]: Routes to tone analysis. AAPL="present" (INFO).

**Gap Analysis:** Strong evaluative coverage. 6 of 8 checks produce CLEAR/TRIGGERED results. Stock data is well-acquired from yfinance. The tone check (2.1.5) is cross-mapped from NLP section and returns "present" without quantitative tone score.
**Health:** GREEN

---

## 2.2 Stock Drop Events (4 questions, 4 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 2.2.1 | Have there been single-day drops >=5% in the past 18 months? | EVALUATE | yfinance | market_client | stock_drops | STOCK.PRICE.single_day_events | ANSWERED |
| 2.2.2 | Have there been multi-day decline events >=10%? | EVALUATE | yfinance | market_client | stock_drops | STOCK.PRICE.recent_drop_alert | ANSWERED |
| 2.2.3 | Were significant drops preceded by "Corrective Disclosures"? | INFER | yfinance, SEC filings | market_client, sec_client | stock_drops | STOCK.PATTERN.event_collapse | ANSWERED |
| 2.2.4 | Has the stock recovered from significant drops? | EVALUATE | yfinance | market_client | stock_performance | STOCK.PRICE.recovery | ANSWERED |

**Checks Detail:**
- `STOCK.PRICE.single_day_events` [EVALUATIVE_CHECK]: Routes to `single_day_drops_count`. AAPL=2 (CLEAR, threshold >5).
- `STOCK.PRICE.recent_drop_alert` [EVALUATIVE_CHECK]: Routes to `decline_from_high`. AAPL=-11.38% (CLEAR).
- `STOCK.PATTERN.event_collapse` [INFERENCE_PATTERN]: Routes to `single_day_drops_count`. AAPL=2 (INFO -- single signal only, insufficient for multi-signal pattern).
- `STOCK.PRICE.recovery` [EVALUATIVE_CHECK]: Routes to `returns_1y`. AAPL=5.03% (CLEAR).

**Gap Analysis:** Good coverage. Event collapse inference pattern correctly requires multiple signals and reports insufficient data for AAPL. The corrective disclosure correlation (2.2.3) needs temporal alignment between stock drops and 8-K filings, which is partially implemented.
**Health:** GREEN

---

## 2.3 Volatility & Trading Patterns (4 questions, 6 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 2.3.1 | What's the 90-day volatility and how does it compare to peers? | EVALUATE | yfinance | market_client | extract_market | STOCK.PRICE.technical (cross-mapped from 2.1) | PARTIAL |
| 2.3.2 | What's the beta? | DISPLAY | yfinance | market_client | extract_market | STOCK.TRADE.liquidity | PARTIAL |
| 2.3.3 | Is there adequate trading liquidity? | DISPLAY | yfinance | market_client | extract_market | STOCK.TRADE.liquidity | PARTIAL |
| 2.3.4 | Are there unusual volume or options patterns? | DISPLAY | yfinance | market_client | extract_market | STOCK.TRADE.volume_patterns, STOCK.TRADE.options | PARTIAL |

**Checks Detail:**
- `STOCK.PATTERN.cascade` [INFERENCE_PATTERN]: Routes to `decline_from_high`. AAPL=-11.38% (INFO -- single signal).
- `STOCK.PATTERN.death_spiral` [INFERENCE_PATTERN]: Routes to `decline_from_high`. AAPL=-11.38% (INFO -- single signal).
- `STOCK.PATTERN.peer_divergence` [INFERENCE_PATTERN]: Routes to `returns_1y`. AAPL=5.03% (INFO -- single signal).
- `STOCK.TRADE.liquidity` [MANAGEMENT_DISPLAY]: Routes to `current_price`. AAPL=$255.78 (INFO).
- `STOCK.TRADE.volume_patterns` [MANAGEMENT_DISPLAY]: Routes to `adverse_event_count`. AAPL=7 (INFO).
- `STOCK.TRADE.options` [MANAGEMENT_DISPLAY]: Routes to `adverse_event_count`. AAPL=7 (INFO).

**Gap Analysis:** 3 INFERENCE_PATTERN checks return INFO because they require multiple corroborating signals. 3 MANAGEMENT_DISPLAY checks show values without evaluation. The trade liquidity check routes to current_price instead of average daily volume. Beta is not explicitly extracted or checked. Volume patterns route to adverse_event_count, not actual volume metrics. Options activity is not acquired.
**Health:** YELLOW -- data present but no evaluative results.

---

## 2.4 Short Interest & Bearish Signals (2 questions, 4 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 2.4.1 | What's the short interest as % of float and what's the trend? | EVALUATE | yfinance | market_client | short_interest | STOCK.SHORT.position, STOCK.SHORT.trend | ANSWERED |
| 2.4.2 | Have there been activist short seller reports? | EVALUATE | Web search | web_search | N/A | STOCK.SHORT.report, STOCK.PATTERN.short_attack | ANSWERED |

**Checks Detail:**
- `STOCK.SHORT.position` [EVALUATIVE_CHECK]: Routes to `short_interest_pct`. AAPL=0.8% (CLEAR).
- `STOCK.SHORT.trend` [EVALUATIVE_CHECK]: Routes to `short_interest_ratio`. AAPL=2.36 days (CLEAR).
- `STOCK.SHORT.report` [EVALUATIVE_CHECK]: Routes to `short_interest_pct`. AAPL=0.8% (INFO -- qualitative).
- `STOCK.PATTERN.short_attack` [INFERENCE_PATTERN]: Routes to `short_interest_pct`. AAPL=0.8% (INFO -- single signal).

**Gap Analysis:** Position and trend checks work well with yfinance data. Short seller report detection (activist reports from Muddy Waters, Hindenburg, etc.) relies on the same short interest % rather than actual web search for published reports.
**Health:** GREEN

---

## 2.5 Ownership Structure (4 questions, 4 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 2.5.1 | What's the institutional vs insider vs retail ownership breakdown? | EVALUATE | yfinance, SEC DEF 14A | market_client, sec_client | ownership_structure | STOCK.OWN.structure | ANSWERED |
| 2.5.2 | Who are the largest holders and what's the concentration? | DISPLAY | yfinance | market_client | ownership_structure | STOCK.OWN.concentration | ANSWERED |
| 2.5.3 | What are the institutional ownership trends over the past 6-12 months? | DISPLAY | yfinance | market_client | ownership_structure | STOCK.OWN.structure | ANSWERED |
| 2.5.4 | Are there capital markets transactions creating liability windows? | EVALUATE | SEC filings, SCAC | sec_client, litigation_client | capital_markets, sca_extractor | STOCK.LIT.existing_action | ANSWERED |

**Checks Detail:**
- `STOCK.OWN.structure` [EVALUATIVE_CHECK]: Routes to `institutional_pct`. AAPL=65.48% (INFO).
- `STOCK.OWN.concentration` [MANAGEMENT_DISPLAY]: Routes to `institutional_pct`. AAPL=65.48% (INFO).
- `STOCK.OWN.activist` [MANAGEMENT_DISPLAY]: Routes to `activist_present`. AAPL=False (INFO).
- `STOCK.LIT.existing_action` [EVALUATIVE_CHECK]: Routes to `active_sca_count`. AAPL=0 (CLEAR).

**Gap Analysis:** Ownership data comes from yfinance. Institutional percentage is displayed but not evaluated against thresholds (e.g., very high institutional = litigation target). Top holders list available but pct_out enrichment missing. Capital markets transaction check (STOCK.LIT.existing_action) evaluates SCA presence, not secondary offerings or ATM programs directly.
**Health:** GREEN

---

## 2.6 Analyst Coverage & Sentiment (3 questions, 2 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 2.6.1 | How many analysts cover this stock? | DISPLAY | yfinance | market_client | extract_market | STOCK.ANALYST.coverage | DISPLAY ONLY |
| 2.6.2 | What's the consensus rating and recent changes? | DISPLAY | yfinance | market_client | extract_market | STOCK.ANALYST.momentum | DISPLAY ONLY |
| 2.6.3 | What's the price target relative to current price? | DISPLAY | yfinance | market_client | extract_market | STOCK.ANALYST.coverage | DISPLAY ONLY |

**Checks Detail:**
- `STOCK.ANALYST.coverage` [MANAGEMENT_DISPLAY]: Routes to `beat_rate`. AAPL=0.9167 (INFO).
- `STOCK.ANALYST.momentum` [MANAGEMENT_DISPLAY]: Routes to `beat_rate`. AAPL=0.9167 (INFO).

**Gap Analysis:** Both checks are MANAGEMENT_DISPLAY routing to `beat_rate` (earnings beat rate), not analyst count or consensus rating. Analyst count, consensus rating, and price target data are available in yfinance but not extracted into separate fields. Both checks return the same value for AAPL.
**Health:** YELLOW -- data source exists but extraction is incomplete and checks are display-only.

---

## 2.7 Valuation Metrics (2 questions, 4 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 2.7.1 | What are the key valuation ratios (P/E, EV/EBITDA, PEG)? | EVALUATE | yfinance | market_client | extract_market | STOCK.VALUATION.pe_ratio, STOCK.VALUATION.ev_ebitda, STOCK.VALUATION.peg_ratio | ANSWERED |
| 2.7.2 | How does valuation compare to peers? | EVALUATE | yfinance | market_client | extract_market, peer_group | STOCK.VALUATION.premium_discount | ANSWERED |

**Checks Detail:**
- `STOCK.VALUATION.pe_ratio` [EVALUATIVE_CHECK]: Routes to `pe_ratio`. AAPL=SKIPPED (field not populated).
- `STOCK.VALUATION.ev_ebitda` [EVALUATIVE_CHECK]: Routes to `ev_ebitda`. AAPL=SKIPPED (field not populated).
- `STOCK.VALUATION.peg_ratio` [EVALUATIVE_CHECK]: Routes to `peg_ratio`. AAPL=SKIPPED (field not populated).
- `STOCK.VALUATION.premium_discount` [EVALUATIVE_CHECK]: Routes to `returns_1y`. AAPL=5.03% (CLEAR).

**Gap Analysis:** 3 of 4 checks SKIPPED because pe_ratio, ev_ebitda, and peg_ratio fields are not populated in the ExtractedData model despite being available from yfinance. The market extraction pipeline acquires these values but does not store them in the correct fields. Only premium_discount evaluates (using returns_1y as proxy). Known extraction gap.
**Health:** YELLOW -- checks defined with thresholds but data extraction not wired.

---

## 2.8 Insider Trading Activity (7 questions, 16 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 2.8.1 | What's the net insider trading direction? | EVALUATE | SEC Form 4 | sec_client | insider_trading | GOV.INSIDER.net_selling, STOCK.INSIDER.summary | ANSWERED |
| 2.8.2 | Are CEO/CFO selling significant holdings? | EVALUATE | SEC Form 4 | sec_client | insider_trading | EXEC.INSIDER.ceo_net_selling, EXEC.INSIDER.cfo_net_selling, STOCK.INSIDER.notable_activity | ANSWERED |
| 2.8.3 | What percentage of transactions use 10b5-1 plans? | EVALUATE | SEC Form 4 | sec_client | insider_trading | GOV.INSIDER.10b5_plans, EXEC.INSIDER.non_10b51 | ANSWERED |
| 2.8.4 | Is there cluster selling (multiple insiders simultaneously)? | INFER | SEC Form 4 | sec_client | insider_trading | GOV.INSIDER.cluster_sales, EXEC.INSIDER.cluster_selling, STOCK.INSIDER.cluster_timing | ANSWERED |
| 2.8.5 | Is insider trading timing suspicious relative to material events? | INFER | SEC Form 4, 8-K | sec_client | insider_trading | GOV.INSIDER.unusual_timing, STOCK.PATTERN.informed_trading | ANSWERED |
| 2.8.6 | Do executives pledge company shares as loan collateral? | EVALUATE | SEC DEF 14A | sec_client | ownership_structure | GOV.INSIDER.ownership_pct | ANSWERED |
| 2.8.7 | Are there Form 4 compliance issues? (Late Section 16 filings, gift transactions timed before declines) | EVALUATE | SEC Form 4 | sec_client | insider_trading | GOV.INSIDER.form4_filings | ANSWERED |

**Checks Detail (16 checks):**
- `EXEC.INSIDER.ceo_net_selling` [EVALUATIVE_CHECK]: AAPL=100% (TRIGGERED red, threshold >80%).
- `EXEC.INSIDER.cfo_net_selling` [EVALUATIVE_CHECK]: AAPL=100% (TRIGGERED red, threshold >80%).
- `EXEC.INSIDER.cluster_selling` [INFERENCE_PATTERN]: AAPL=True (INFO -- single signal).
- `EXEC.INSIDER.non_10b51` [INFERENCE_PATTERN]: AAPL=6.7% (INFO -- single signal).
- `GOV.INSIDER.10b5_plans` [MANAGEMENT_DISPLAY]: AAPL=SKIPPED.
- `GOV.INSIDER.cluster_sales` [EVALUATIVE_CHECK]: AAPL=SKIPPED.
- `GOV.INSIDER.executive_sales` [EVALUATIVE_CHECK]: AAPL=1.71% (CLEAR).
- `GOV.INSIDER.form4_filings` [MANAGEMENT_DISPLAY]: AAPL=1.71% (INFO).
- `GOV.INSIDER.net_selling` [EVALUATIVE_CHECK]: AAPL=1.71% (CLEAR).
- `GOV.INSIDER.ownership_pct` [EVALUATIVE_CHECK]: AAPL=1.71% (CLEAR).
- `GOV.INSIDER.plan_adoption` [EVALUATIVE_CHECK]: AAPL=SKIPPED.
- `GOV.INSIDER.unusual_timing` [EVALUATIVE_CHECK]: AAPL=SKIPPED.
- `STOCK.INSIDER.cluster_timing` [EVALUATIVE_CHECK]: AAPL=1 (TRIGGERED red, threshold >0).
- `STOCK.INSIDER.notable_activity` [EVALUATIVE_CHECK]: AAPL=100% (TRIGGERED red, threshold >25%).
- `STOCK.INSIDER.summary` [EVALUATIVE_CHECK]: AAPL=NET_SELLING (INFO -- qualitative).
- `STOCK.PATTERN.informed_trading` [INFERENCE_PATTERN]: AAPL=NOT_RUN (FALLBACK_ONLY).

**Gap Analysis:** Strong coverage with 4 TRIGGERED checks for AAPL. CEO and CFO both 100% sellers. Cluster timing detected. Some GOV.INSIDER checks SKIPPED because insider_cluster_count, insider_unusual_timing, and plan_adoption_timing fields are not populated in the governance mapper output. The 10b5-1 plan analysis is partially functional.
**Health:** GREEN

---

# 3. FINANCIAL

## 3.1 Liquidity & Solvency (4 questions, 5 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 3.1.1 | Does the company have adequate liquidity (current ratio, quick ratio, cash ratio)? | EVALUATE | SEC 10-Q, XBRL | sec_client | financial_statements, xbrl_mapping | FIN.LIQ.position, FIN.LIQ.efficiency | ANSWERED |
| 3.1.2 | What is the cash runway -- how many months before cash runs out? | EVALUATE | SEC 10-Q, XBRL | sec_client | financial_statements | FIN.LIQ.cash_burn | ANSWERED |
| 3.1.3 | Is there a going concern opinion from the auditor? | EVALUATE | SEC 10-K | sec_client | audit_risk | FIN.ACCT.auditor (cross-mapped) | ANSWERED |
| 3.1.4 | How has working capital trended over the past 3 years? | EVALUATE | SEC 10-Q, XBRL | sec_client | financial_statements | FIN.LIQ.working_capital, FIN.LIQ.trend | ANSWERED |

**Checks Detail:**
- `FIN.LIQ.position` [EVALUATIVE_CHECK]: Routes to `current_ratio`. AAPL=0.8933 (TRIGGERED red, threshold <6.0 -- NOTE: threshold seems too high, likely sector-miscalibrated for tech).
- `FIN.LIQ.working_capital` [EVALUATIVE_CHECK]: Routes to `current_ratio`. AAPL=0.8933 (TRIGGERED red, threshold <1.0).
- `FIN.LIQ.efficiency` [EVALUATIVE_CHECK]: Routes to `cash_ratio`. AAPL=0.217 (TRIGGERED yellow, threshold <0.5).
- `FIN.LIQ.trend` [EVALUATIVE_CHECK]: Routes to `current_ratio`. AAPL=0.8933 (INFO -- qualitative trend check).
- `FIN.LIQ.cash_burn` [EVALUATIVE_CHECK]: Routes to `cash_burn_months`. AAPL="Profitable (OCF positive)" (INFO -- not applicable to profitable companies).

**Gap Analysis:** Strong evaluative coverage. AAPL triggers red on liquidity position because its current ratio is below 1.0 (Apple famously runs lean working capital). The FIN.LIQ.position red threshold of 6.0 appears to be a sector-calibration issue -- 6.0 would be extreme for any non-bank company. Cash burn correctly returns "Profitable" for OCF-positive companies.
**Health:** GREEN (thresholds need sector calibration review)

---

## 3.2 Leverage & Debt Structure (6 questions, 5 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 3.2.1 | How leveraged is the company relative to earnings capacity (D/E, Debt/EBITDA)? | EVALUATE | SEC 10-Q, XBRL | sec_client | financial_statements, debt_analysis | FIN.DEBT.structure | ANSWERED |
| 3.2.2 | Can the company service its debt (interest coverage)? | EVALUATE | SEC 10-Q, XBRL | sec_client | financial_statements | FIN.DEBT.coverage | ANSWERED |
| 3.2.3 | When does significant debt mature and is refinancing at risk? | EVALUATE | SEC 10-K | sec_client | debt_analysis, debt_text_parsing | FIN.DEBT.maturity | ANSWERED |
| 3.2.4 | Are there covenant compliance risks? | EVALUATE | SEC 10-K | sec_client | debt_analysis | FIN.DEBT.covenants | ANSWERED |
| 3.2.5 | What is the credit rating and recent trajectory? | DISPLAY | SEC 10-K, Web search | sec_client, web_search | debt_analysis | FIN.DEBT.credit_rating | ANSWERED |
| 3.2.6 | What off-balance-sheet obligations exist? | EVALUATE | SEC 10-K | sec_client | contingent_notes, contingent_liab | FIN.DEBT.structure | ANSWERED |

**Checks Detail:**
- `FIN.DEBT.structure` [EVALUATIVE_CHECK]: Routes to `debt_to_ebitda`. AAPL=0.6265 (CLEAR).
- `FIN.DEBT.coverage` [EVALUATIVE_CHECK]: Routes to `interest_coverage`. AAPL=33.83x (CLEAR).
- `FIN.DEBT.maturity` [EVALUATIVE_CHECK]: Routes to `refinancing_risk`. AAPL="10 fixed-rate tranches, floating-rate debt present" (INFO -- qualitative).
- `FIN.DEBT.covenants` [EVALUATIVE_CHECK]: Routes to `debt_structure`. AAPL=maturity/rate dict (INFO -- qualitative).
- `FIN.DEBT.credit_rating` [EVALUATIVE_CHECK]: AAPL=NOT_RUN (FALLBACK_ONLY execution mode).

**Gap Analysis:** Core leverage metrics (debt/EBITDA, interest coverage) are well-covered with evaluative thresholds. Debt maturity and covenant checks return qualitative data. Credit rating is not acquired (FALLBACK_ONLY mode). Off-balance-sheet is partially covered through contingent_notes extraction.
**Health:** GREEN

---

## 3.3 Profitability & Growth (6 questions, 10 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 3.3.1 | Is revenue growing or decelerating? | EVALUATE | SEC 10-Q, XBRL | sec_client | financial_statements | FIN.TEMPORAL.revenue_deceleration, FIN.PROFIT.revenue | ANSWERED |
| 3.3.2 | Are margins expanding, stable, or compressing? | EVALUATE | SEC 10-Q, XBRL | sec_client | financial_statements | FIN.TEMPORAL.margin_compression, FIN.PROFIT.margins | ANSWERED |
| 3.3.3 | Is the company profitable? What's the trajectory? | EVALUATE | SEC 10-Q, XBRL | sec_client | financial_statements | FIN.TEMPORAL.profitability_trend, FIN.PROFIT.earnings | ANSWERED |
| 3.3.4 | How does cash flow quality compare to reported earnings? | EVALUATE | SEC 10-Q, XBRL | sec_client | financial_statements | FIN.TEMPORAL.cash_flow_deterioration | ANSWERED |
| 3.3.5 | Are there segment-level divergences hiding overall trends? | DISPLAY | SEC 10-K | sec_client | financial_statements | FIN.PROFIT.segment | ANSWERED |
| 3.3.6 | What is the free cash flow generation and CapEx trend? | EVALUATE | SEC 10-Q, XBRL | sec_client | financial_statements | FIN.PROFIT.trend | ANSWERED |

**Checks Detail:**
- `FIN.PROFIT.revenue` [EVALUATIVE_CHECK]: Routes to `financial_health_narrative`. AAPL="Revenue growing at 6.4% YoY" (INFO).
- `FIN.PROFIT.margins` [EVALUATIVE_CHECK]: Routes to `accruals_ratio`. AAPL=0.0015 (CLEAR).
- `FIN.PROFIT.earnings` [EVALUATIVE_CHECK]: Routes to `ocf_to_ni`. AAPL=0.9953 (INFO).
- `FIN.PROFIT.segment` [EVALUATIVE_CHECK]: Routes to `financial_health_narrative`. AAPL=narrative text (INFO).
- `FIN.PROFIT.trend` [EVALUATIVE_CHECK]: Routes to `financial_health_narrative`. AAPL=narrative text (INFO).
- `FIN.TEMPORAL.revenue_deceleration` [EVALUATIVE_CHECK]: AAPL="revenue_deceleration" (INFO -- temporal check names metric).
- `FIN.TEMPORAL.margin_compression` [EVALUATIVE_CHECK]: AAPL="margin_compression" (INFO -- temporal check names metric).
- `FIN.TEMPORAL.operating_margin_compression` [EVALUATIVE_CHECK]: AAPL="operating_margin_compression" (INFO -- temporal check names metric).
- `FIN.TEMPORAL.profitability_trend` [EVALUATIVE_CHECK]: AAPL="profitability_trend" (INFO -- temporal check names metric).
- `FIN.TEMPORAL.cash_flow_deterioration` [EVALUATIVE_CHECK]: AAPL="cash_flow_deterioration" (INFO -- temporal check names metric).

**Gap Analysis:** FIN.TEMPORAL checks return metric names as values rather than computed trend values. FIN.PROFIT checks mostly route to `financial_health_narrative` (text summary). The accruals_ratio and OCF-to-NI checks produce numeric evaluations. Revenue growth rate extraction works (6.4% for AAPL). Temporal computation pipeline needs completion.
**Health:** GREEN (temporal checks need full computation pipeline)

---

## 3.4 Earnings Quality & Forensic Analysis (7 questions, 17 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 3.4.1 | Is there evidence of earnings manipulation (Beneish M-Score, Dechow F-Score)? | COMPUTE | SEC 10-K, XBRL | sec_client | financial_statements, audit_risk | FIN.ACCT.earnings_manipulation, FIN.FORENSIC.fis_composite | ANSWERED |
| 3.4.2 | Are accruals abnormally high relative to cash flows? | COMPUTE | SEC 10-Q, XBRL | sec_client | financial_statements | FIN.FORENSIC.accrual_intensity, FIN.FORENSIC.enhanced_sloan | ANSWERED |
| 3.4.3 | Is revenue quality deteriorating (DSO expansion, Q4 concentration, deferred revenue)? | EVALUATE | SEC 10-Q, XBRL | sec_client | financial_statements | FIN.QUALITY.dso_ar_divergence, FIN.QUALITY.q4_revenue_concentration | ANSWERED |
| 3.4.4 | Is there a growing gap between GAAP and non-GAAP earnings? | EVALUATE | SEC 10-K | sec_client | financial_statements | FIN.QUALITY.non_gaap_divergence | ANSWERED |
| 3.4.5 | What does the Financial Integrity Score composite indicate? | COMPUTE | SEC 10-K, XBRL | sec_client | financial_statements, audit_risk | FIN.FORENSIC.fis_composite, FIN.FORENSIC.beneish_dechow_convergence | ANSWERED |
| 3.4.6 | Are there specific revenue manipulation patterns? | EVALUATE | SEC 10-K, XBRL | sec_client | financial_statements | FIN.QUALITY.revenue_quality_score | ANSWERED |
| 3.4.7 | Is the Depreciation Index (DEPI) anomalous? | COMPUTE | SEC 10-K, XBRL | sec_client | financial_statements | FIN.ACCT.earnings_manipulation | ANSWERED |

**Checks Detail (key checks):**
- `FIN.ACCT.earnings_manipulation` [EVALUATIVE_CHECK]: Routes to `beneish_m_score`. AAPL=-2.2937 (CLEAR).
- `FIN.FORENSIC.fis_composite` [EVALUATIVE_CHECK]: Routes to `beneish_m_score`. AAPL=-2.2937 (CLEAR).
- `FIN.FORENSIC.accrual_intensity` [EVALUATIVE_CHECK]: Routes to `accruals_ratio`. AAPL=0.0015 (CLEAR).
- `FIN.FORENSIC.enhanced_sloan` [EVALUATIVE_CHECK]: Routes to `accruals_ratio`. AAPL=0.0015 (CLEAR).
- `FIN.FORENSIC.beneish_dechow_convergence` [EVALUATIVE_CHECK]: AAPL=False (CLEAR).
- `FIN.QUALITY.dso_ar_divergence` [EVALUATIVE_CHECK]: AAPL=11.86 (TRIGGERED yellow, threshold >10).
- `FIN.QUALITY.revenue_quality_score` [EVALUATIVE_CHECK]: AAPL=1.0 (CLEAR).
- `FIN.QUALITY.cash_flow_quality` [EVALUATIVE_CHECK]: Routes to `ocf_to_ni`. AAPL=0.9953 (CLEAR).
- `FIN.QUALITY.deferred_revenue_trend` [EVALUATIVE_CHECK]: AAPL=SKIPPED (not populated).
- `FIN.QUALITY.q4_revenue_concentration` [EVALUATIVE_CHECK]: AAPL=SKIPPED (not populated).

**Gap Analysis:** Strong forensic suite. Beneish M-Score computed (-2.2937 CLEAR). Accruals ratio computed. DSO/AR divergence correctly triggers yellow (11.86). Deferred revenue trend and Q4 concentration SKIPPED because quarterly fields not populated. Dechow F-Score and Montier C-Score return "present" qualitatively.
**Health:** GREEN

---

## 3.5 Accounting Integrity & Audit Risk (7 questions, 18 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 3.5.1 | Who is the auditor and what's their tenure and opinion? | EVALUATE | SEC 10-K | sec_client | audit_risk | FIN.ACCT.auditor, GOV.EFFECT.audit_opinion | ANSWERED |
| 3.5.2 | Has there been a restatement, material weakness, or significant deficiency? | EVALUATE | SEC 10-K, 8-K | sec_client | audit_risk | FIN.ACCT.restatement, FIN.ACCT.material_weakness | ANSWERED |
| 3.5.3 | Has there been an auditor change, and why? | EVALUATE | SEC 8-K | sec_client | audit_risk | GOV.EFFECT.auditor_change | ANSWERED |
| 3.5.4 | Are there SEC comment letters raising accounting questions? | EVALUATE | SEC EDGAR | sec_client | audit_risk | FIN.ACCT.sec_correspondence | ANSWERED |
| 3.5.5 | What are the critical audit matters (CAMs)? | DISPLAY | SEC 10-K | sec_client | audit_risk | NLP.CAM.changes | ANSWERED |
| 3.5.6 | What is the non-audit fee ratio? | EVALUATE | SEC DEF 14A | sec_client | audit_risk | GOV.EFFECT.audit_committee | ANSWERED |
| 3.5.7 | Are there PCAOB inspection findings for this auditor? | EVALUATE | Web search | web_search | N/A | FIN.ACCT.auditor | ANSWERED |

**Checks Detail (key checks):**
- `FIN.ACCT.restatement` [EVALUATIVE_CHECK]: Routes to `restatements`. AAPL=0 (CLEAR).
- `FIN.ACCT.material_weakness` [EVALUATIVE_CHECK]: Routes to `material_weaknesses`. AAPL=0 (CLEAR).
- `FIN.ACCT.internal_controls` [EVALUATIVE_CHECK]: Routes to `material_weaknesses`. AAPL=0 (CLEAR).
- `FIN.ACCT.quality_indicators` [EVALUATIVE_CHECK]: Routes to `altman_z_score`. AAPL=10.17 (CLEAR).
- `FIN.ACCT.auditor` [EVALUATIVE_CHECK]: Routes to `auditor_opinion`. AAPL="unqualified" (INFO).
- GOV.EFFECT checks (6 total): All SKIPPED -- DEF 14A governance fields not populated.

**Gap Analysis:** Core accounting checks work. GOV.EFFECT governance overlay checks (audit_committee, auditor_change, material_weakness, sig_deficiency, sox_404) all SKIPPED because DEF 14A extraction does not populate those fields. 10 of 18 checks SKIPPED.
**Health:** GREEN (core checks work; governance overlay needs DEF 14A extraction)

---

## 3.6 Financial Distress Indicators (6 questions, 5 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 3.6.1 | What does the Altman Z-Score indicate? | COMPUTE | SEC 10-K, XBRL | sec_client | financial_statements | FWRD.WARN.zone_of_insolvency | ANSWERED |
| 3.6.2 | What does the Ohlson O-Score show? | COMPUTE | SEC 10-K, XBRL | sec_client | financial_statements | FWRD.WARN.zone_of_insolvency | ANSWERED |
| 3.6.3 | What does the Piotroski F-Score show? | COMPUTE | SEC 10-K, XBRL | sec_client | financial_statements | FWRD.WARN.zone_of_insolvency | ANSWERED |
| 3.6.4 | Is the company in the "Zone of Insolvency"? | COMPUTE | SEC 10-K, XBRL | sec_client | financial_statements | FWRD.WARN.zone_of_insolvency | ANSWERED |
| 3.6.5 | What do credit market signals show? | EVALUATE | Web search | web_search | N/A | FIN.DEBT.credit_rating | ANSWERED |
| 3.6.6 | Is there active restructuring? | EVALUATE | SEC 10-K, 8-K | sec_client | ten_k_converters | FIN.TEMPORAL.debt_ratio_increase | ANSWERED |

**Checks Detail:**
- `FWRD.WARN.zone_of_insolvency` [EVALUATIVE_CHECK]: Routes to `altman_z_score`. AAPL=10.17 (CLEAR).
- `FWRD.WARN.goodwill_risk` [EVALUATIVE_CHECK]: AAPL=0.6265 (CLEAR).
- `FWRD.WARN.impairment_risk` [EVALUATIVE_CHECK]: AAPL="Not mentioned" (INFO).
- `FIN.TEMPORAL.debt_ratio_increase` [EVALUATIVE_CHECK]: AAPL="debt_ratio_increase" (INFO -- temporal).
- `FIN.TEMPORAL.working_capital_deterioration` [EVALUATIVE_CHECK]: AAPL="working_capital_deterioration" (INFO -- temporal).

**Gap Analysis:** Altman Z-Score is the primary distress metric (10.17 = healthy). Ohlson O-Score and Piotroski F-Score are not individually computed -- all 3 questions map to the same zone_of_insolvency check. Credit market signals not acquired.
**Health:** GREEN (primary metric works; secondary scores share one check)

---

## 3.7 Guidance & Market Expectations (5 questions, 5 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 3.7.1 | Does the company provide earnings guidance? | EVALUATE | SEC 8-K | sec_client | earnings_guidance | FIN.GUIDE.current | PARTIAL |
| 3.7.2 | What's the guidance track record? | EVALUATE | yfinance, SEC 8-K | market_client, sec_client | earnings_guidance | FIN.GUIDE.track_record | PARTIAL |
| 3.7.3 | What's the guidance philosophy? | DISPLAY | SEC 8-K | sec_client | earnings_guidance | FIN.GUIDE.philosophy | PARTIAL |
| 3.7.4 | How does analyst consensus align? | EVALUATE | yfinance, SEC 8-K | market_client, sec_client | earnings_guidance | FIN.GUIDE.analyst_consensus | PARTIAL |
| 3.7.5 | How does the market react to earnings? | EVALUATE | yfinance | market_client | stock_performance | FIN.GUIDE.earnings_reaction | PARTIAL |

**Checks Detail:**
All 5 checks route to `financial_health_narrative` and return INFO with narrative text. No evaluative thresholds applied.

**Gap Analysis:** All 5 checks return INFO. Guidance data (beat/miss, estimates) available from yfinance but not extracted into dedicated fields. Earnings_guidance extraction module exists but outputs not connected to check field routing.
**Health:** YELLOW -- all checks return INFO; extraction not connected.

---

## 3.8 Sector-Specific Financial Metrics (1 question, 10 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 3.8.1 | What are the applicable sector-specific KPIs? | EVALUATE | SEC 10-K, 10-Q | sec_client | financial_statements | FIN.SECTOR.energy, FIN.SECTOR.retail, FWRD.WARN.* AI checks | ANSWERED |

**Checks Detail:**
- `FIN.SECTOR.energy` [MANAGEMENT_DISPLAY]: Not applicable to AAPL. Returns narrative (INFO).
- `FIN.SECTOR.retail` [MANAGEMENT_DISPLAY]: Not applicable to AAPL. Returns narrative (INFO).
- `FWRD.WARN.working_capital_trends` [EVALUATIVE_CHECK]: AAPL=0.8933 (CLEAR).
- 7 AI/tech sector FWRD.WARN checks: Return 10-K mention counts (INFO).

**Gap Analysis:** Sector checks are contextual by design. Working_capital_trends is the only evaluative check that fires. AI/tech sector checks detect relevant 10-K mentions but do not evaluate against thresholds. Energy and retail checks should skip for non-applicable sectors.
**Health:** GREEN (functioning as designed)

---

# 4. GOVERNANCE & DISCLOSURE

## 4.1 Board Composition & Quality (8 questions, 18 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 4.1.1 | How independent is the board? | EVALUATE | SEC DEF 14A | sec_client | board_governance, board_parsing | GOV.BOARD.independence, EXEC.PROFILE.independent_ratio | ANSWERED |
| 4.1.2 | Is the CEO also the board chair? | EVALUATE | SEC DEF 14A | sec_client | board_governance | GOV.BOARD.ceo_chair, EXEC.PROFILE.ceo_chair_duality | ANSWERED |
| 4.1.3 | What's the board size and tenure distribution? | EVALUATE | SEC DEF 14A | sec_client | board_governance, board_parsing | GOV.BOARD.size, GOV.BOARD.tenure, EXEC.PROFILE.board_size | ANSWERED |
| 4.1.4 | Do board members have relevant experience? | DISPLAY | SEC DEF 14A | sec_client | board_governance | GOV.BOARD.expertise | ANSWERED |
| 4.1.5 | Is this a classified (staggered) board? | EVALUATE | SEC DEF 14A | sec_client | board_governance | GOV.RIGHTS.classified (cross-mapped) | ANSWERED |
| 4.1.6 | How engaged is the board (meeting frequency, attendance)? | EVALUATE | SEC DEF 14A | sec_client | board_governance | GOV.BOARD.meetings, GOV.BOARD.attendance | ANSWERED |
| 4.1.7 | What is the board committee structure? | DISPLAY | SEC DEF 14A | sec_client | board_governance | GOV.BOARD.committees | ANSWERED |
| 4.1.8 | Is the Board Chair the immediate past CEO ("Successor Chair")? | EVALUATE | SEC DEF 14A | sec_client | board_governance, leadership_profiles | GOV.BOARD.succession | ANSWERED |

**Checks Detail (key checks):**
- `GOV.BOARD.ceo_chair` [EVALUATIVE_CHECK]: Routes to `ceo_chair_duality`. AAPL=1 (TRIGGERED red -- CEO/chair not separated, threshold <50).
- `GOV.BOARD.departures` [EVALUATIVE_CHECK]: Routes to `departures_18mo`. AAPL=0 (CLEAR).
- `EXEC.PROFILE.ceo_chair_duality` [MANAGEMENT_DISPLAY]: AAPL=True (INFO).
- `GOV.BOARD.independence` [EVALUATIVE_CHECK]: AAPL=SKIPPED (board_independence not populated).
- `GOV.BOARD.size` [EVALUATIVE_CHECK]: AAPL=SKIPPED (board_size not populated from DEF 14A).
- `GOV.BOARD.tenure` [EVALUATIVE_CHECK]: AAPL=SKIPPED (avg_board_tenure not populated).
- `GOV.BOARD.diversity` [EVALUATIVE_CHECK]: AAPL=SKIPPED.
- `GOV.BOARD.overboarding` [EVALUATIVE_CHECK]: AAPL=SKIPPED.
- `GOV.BOARD.meetings` [EVALUATIVE_CHECK]: AAPL=SKIPPED.
- `GOV.BOARD.attendance` [EVALUATIVE_CHECK]: AAPL=SKIPPED.
- `GOV.BOARD.expertise` [MANAGEMENT_DISPLAY]: AAPL=SKIPPED.
- `GOV.BOARD.committees` [MANAGEMENT_DISPLAY]: AAPL=SKIPPED.
- `GOV.BOARD.refresh_activity` [MANAGEMENT_DISPLAY]: AAPL=SKIPPED.
- `GOV.BOARD.succession` [EVALUATIVE_CHECK]: AAPL=SKIPPED.
- `EXEC.PROFILE.board_size` [MANAGEMENT_DISPLAY]: AAPL=SKIPPED.
- `EXEC.PROFILE.avg_tenure` [MANAGEMENT_DISPLAY]: AAPL=SKIPPED.
- `EXEC.PROFILE.independent_ratio` [MANAGEMENT_DISPLAY]: AAPL=SKIPPED.
- `EXEC.PROFILE.overboarded_directors` [EVALUATIVE_CHECK]: AAPL=SKIPPED.

**Gap Analysis:** 15 of 18 checks SKIPPED because DEF 14A proxy statement parsing does not extract board composition data (size, independence_ratio, avg_tenure, meeting count, attendance, committee details). Only ceo_chair_duality (True) and departures_18mo (0) are populated. This is a known extraction gap -- the board_governance extraction module exists but DEF 14A parsing is incomplete. CEO-chair duality correctly triggers red for AAPL (Tim Cook is both CEO and de facto board chair in terms of governance concern).
**Health:** YELLOW -- checks defined with thresholds but 15/18 SKIPPED due to DEF 14A extraction gaps.

---

## 4.2 Executive Team & Stability (6 questions, 22 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 4.2.1 | Do the CEO and key executives have relevant experience? | EVALUATE | SEC DEF 14A, SCAC | sec_client, litigation_client | leadership_profiles, leadership_parsing | GOV.EXEC.ceo_profile, GOV.EXEC.cfo_profile | ANSWERED |
| 4.2.2 | Have executives been sued or investigated at prior companies? | EVALUATE | SCAC, Web search | litigation_client, web_search | sca_extractor | EXEC.PRIOR_LIT.any_officer, EXEC.PRIOR_LIT.ceo_cfo | ANSWERED |
| 4.2.3 | Are there negative personal publicity signals? | EVALUATE | Web search | web_search | N/A | GOV.EXEC.officer_litigation | ANSWERED |
| 4.2.4 | What is the C-suite turnover trend? | EVALUATE | SEC 8-K, DEF 14A | sec_client | eight_k_converter, leadership_profiles | GOV.EXEC.turnover_analysis, GOV.EXEC.turnover_pattern, EXEC.TENURE.c_suite_turnover | ANSWERED |
| 4.2.5 | Is there a succession plan for key roles? | EVALUATE | SEC DEF 14A | sec_client | board_governance | GOV.EXEC.succession_status | ANSWERED |
| 4.2.6 | Is there founder/key-person concentration risk? | EVALUATE | SEC DEF 14A | sec_client | leadership_profiles | GOV.EXEC.founder, GOV.EXEC.key_person | ANSWERED |

**Checks Detail (key checks):**
- `EXEC.AGGREGATE.board_risk` [EVALUATIVE_CHECK]: AAPL=29.9 (CLEAR).
- `EXEC.AGGREGATE.highest_risk_individual` [EVALUATIVE_CHECK]: AAPL=0 (CLEAR).
- `EXEC.PRIOR_LIT.any_officer` [EVALUATIVE_CHECK]: AAPL=0 (CLEAR -- no prior lit found).
- `EXEC.PRIOR_LIT.ceo_cfo` [EVALUATIVE_CHECK]: AAPL=0 (CLEAR).
- `EXEC.DEPARTURE.cfo_departure_timing` [EVALUATIVE_CHECK]: AAPL=0 (CLEAR).
- `EXEC.DEPARTURE.cao_departure` [EVALUATIVE_CHECK]: AAPL=0 (CLEAR).
- `GOV.EXEC.turnover_analysis` [EVALUATIVE_CHECK]: AAPL=0 (CLEAR).
- `GOV.EXEC.stability` [EVALUATIVE_CHECK]: Routes to `leadership_stability_score`. AAPL=100 (CLEAR).
- `GOV.EXEC.succession_status` [EVALUATIVE_CHECK]: Routes to `interim_ceo`. AAPL=0 (CLEAR).
- `EXEC.TENURE.ceo_new` [EVALUATIVE_CHECK]: AAPL="CEO identified (Mr. Timothy D. Cook), tenure unavailable" (INFO).
- `EXEC.TENURE.cfo_new` [EVALUATIVE_CHECK]: AAPL="CFO identified (Mr. Kevan Parekh), tenure unavailable" (INFO).
- `GOV.EXEC.ceo_profile` [EVALUATIVE_CHECK]: AAPL="Identified: Mr. Timothy D. Cook (tenure unavailable)" (INFO).
- `EXEC.CEO.risk_score` [EVALUATIVE_CHECK]: AAPL=SKIPPED. `EXEC.CFO.risk_score` [EVALUATIVE_CHECK]: AAPL=SKIPPED.

**Gap Analysis:** Good evaluative coverage with 13 CLEAR results. Executive identification works (CEO and CFO names extracted). Tenure computation is unavailable for both CEO and CFO -- appointment dates are not extracted from DEF 14A to compute tenure. Individual CEO/CFO risk scores SKIPPED (not computed). Prior litigation check works via SCAC cross-reference. Leadership stability score of 100 indicates no recent departures.
**Health:** GREEN (tenure computation unavailable but non-blocking)

---

## 4.3 Compensation & Alignment (10 questions, 15 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 4.3.1 | What's the CEO's total compensation and how does it compare to peers? | EVALUATE | SEC DEF 14A | sec_client | compensation_analysis | GOV.PAY.ceo_total, GOV.PAY.peer_comparison | ANSWERED |
| 4.3.2 | What's the compensation structure? | DISPLAY | SEC DEF 14A | sec_client | compensation_analysis | GOV.PAY.ceo_structure | ANSWERED |
| 4.3.3 | What was the say-on-pay vote result? | EVALUATE | SEC DEF 14A | sec_client | compensation_analysis | GOV.PAY.say_on_pay | ANSWERED |
| 4.3.4 | Are performance metrics in incentive comp appropriate? | DISPLAY | SEC DEF 14A | sec_client | compensation_analysis | GOV.PAY.incentive_metrics | ANSWERED |
| 4.3.5 | Are there clawback policies? | EVALUATE | SEC DEF 14A | sec_client | compensation_analysis | GOV.PAY.clawback | ANSWERED |
| 4.3.6 | Are there related-party transactions or excessive perquisites? | EVALUATE | SEC DEF 14A | sec_client | compensation_analysis | GOV.PAY.related_party, GOV.PAY.perks | ANSWERED |
| 4.3.7 | What's the golden parachute/change-in-control exposure? | EVALUATE | SEC DEF 14A | sec_client | compensation_analysis | GOV.PAY.golden_para | ANSWERED |
| 4.3.8 | What are the executive stock ownership requirements? | EVALUATE | SEC DEF 14A | sec_client | compensation_analysis | GOV.PAY.hedging | ANSWERED |
| 4.3.9 | What is the CEO pay ratio to median employee? | EVALUATE | SEC DEF 14A | sec_client | compensation_analysis | GOV.PAY.ceo_total | ANSWERED |
| 4.3.10 | Are there compensation manipulation indicators? | EVALUATE | SEC DEF 14A | sec_client | compensation_analysis | GOV.PAY.equity_burn, GOV.PAY.exec_loans | ANSWERED |

**Checks Detail (key checks):**
- `GOV.PAY.ceo_total` [EVALUATIVE_CHECK]: Routes to `ceo_pay_ratio`. AAPL=533 (TRIGGERED red, threshold >500).
- `GOV.PAY.peer_comparison` [EVALUATIVE_CHECK]: Routes to `ceo_pay_ratio`. AAPL=533 (TRIGGERED red, threshold >75).
- `GOV.PAY.say_on_pay` [EVALUATIVE_CHECK]: Routes to `say_on_pay_pct`. AAPL=92% (CLEAR).
- `GOV.PAY.ceo_structure` [MANAGEMENT_DISPLAY]: Routes to `ceo_pay_ratio`. AAPL=533 (INFO).
- `GOV.PAY.clawback` [EVALUATIVE_CHECK]: AAPL=SKIPPED (not extracted).
- `GOV.PAY.related_party` [EVALUATIVE_CHECK]: AAPL=SKIPPED (not extracted).
- `GOV.PAY.golden_para` [EVALUATIVE_CHECK]: AAPL=SKIPPED (not extracted).
- `GOV.PAY.hedging` [EVALUATIVE_CHECK]: AAPL=SKIPPED (not extracted).
- `GOV.PAY.equity_burn` [EVALUATIVE_CHECK]: AAPL=SKIPPED (not extracted).
- `GOV.PAY.exec_loans` [EVALUATIVE_CHECK]: AAPL=SKIPPED (not extracted).
- `GOV.PAY.incentive_metrics` [MANAGEMENT_DISPLAY]: AAPL=SKIPPED. `GOV.PAY.perks` [MANAGEMENT_DISPLAY]: AAPL=SKIPPED.
- `GOV.PAY.401k_match` [MANAGEMENT_DISPLAY]: AAPL=SKIPPED. `GOV.PAY.deferred_comp` [MANAGEMENT_DISPLAY]: AAPL=SKIPPED.
- `GOV.PAY.pension` [MANAGEMENT_DISPLAY]: AAPL=SKIPPED.

**Gap Analysis:** CEO pay ratio (533:1) and say-on-pay (92%) are well-extracted and evaluated. 11 of 15 checks SKIPPED because detailed DEF 14A compensation fields (clawback, related_party, golden_parachute, hedging, equity_burn, exec_loans, incentive_metrics, perks, 401k, deferred_comp, pension) are not extracted. The compensation_analysis extraction module exists but only populates ceo_pay_ratio and say_on_pay_pct. The red trigger on ceo_total and peer_comparison both use ceo_pay_ratio=533, which is the pay ratio, not total comp in dollars -- possible field interpretation mismatch.
**Health:** YELLOW -- 2 evaluative checks fire but 11/15 SKIPPED.

---

## 4.4 Shareholder Rights & Protections (5 questions, 10 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 4.4.1 | Does the company have a dual-class voting structure? | EVALUATE | SEC DEF 14A | sec_client | board_governance, ownership_structure | GOV.RIGHTS.dual_class, GOV.RIGHTS.voting_rights | ANSWERED |
| 4.4.2 | Are there anti-takeover provisions? | EVALUATE | SEC DEF 14A | sec_client | board_governance | GOV.RIGHTS.takeover, GOV.RIGHTS.supermajority | ANSWERED |
| 4.4.3 | Is there proxy access for shareholder nominations? | EVALUATE | SEC DEF 14A | sec_client | board_governance | GOV.RIGHTS.proxy_access | ANSWERED |
| 4.4.4 | What forum selection and fee-shifting provisions exist? | EVALUATE | SEC DEF 14A | sec_client | board_governance | GOV.RIGHTS.forum_select | ANSWERED |
| 4.4.5 | Have there been recent bylaw amendments? | EVALUATE | SEC DEF 14A, 8-K | sec_client | board_governance | GOV.RIGHTS.bylaws | ANSWERED |

**Checks Detail:**
- `GOV.RIGHTS.dual_class` [EVALUATIVE_CHECK]: Routes to `dual_class`. AAPL=0 (CLEAR -- no dual-class).
- `GOV.RIGHTS.voting_rights` [MANAGEMENT_DISPLAY]: AAPL=False (INFO).
- `GOV.RIGHTS.bylaws` [MANAGEMENT_DISPLAY]: AAPL=SKIPPED. `GOV.RIGHTS.takeover` [EVALUATIVE_CHECK]: AAPL=SKIPPED.
- `GOV.RIGHTS.proxy_access` [EVALUATIVE_CHECK]: AAPL=SKIPPED. `GOV.RIGHTS.forum_select` [MANAGEMENT_DISPLAY]: AAPL=SKIPPED.
- `GOV.RIGHTS.supermajority` [EVALUATIVE_CHECK]: AAPL=SKIPPED. `GOV.RIGHTS.action_consent` [EVALUATIVE_CHECK]: AAPL=SKIPPED.
- `GOV.RIGHTS.special_mtg` [EVALUATIVE_CHECK]: AAPL=SKIPPED. `GOV.RIGHTS.classified` [EVALUATIVE_CHECK]: AAPL=SKIPPED.

**Gap Analysis:** Only dual_class is populated (from ownership_structure extraction or yfinance). 8 of 10 checks SKIPPED because DEF 14A does not extract takeover defenses, proxy access, forum selection, supermajority requirements, classified board status, bylaws, action by consent, or special meeting thresholds. These are all extractable from the proxy statement but the parser does not cover them.
**Health:** YELLOW -- dual-class works, everything else SKIPPED.

---

## 4.5 Activist Pressure (4 questions, 14 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 4.5.1 | Are there Schedule 13D filings indicating activist intent? | EVALUATE | SEC 13D/G, DEF 14A | sec_client | ownership_structure | GOV.ACTIVIST.13d_filings | ANSWERED |
| 4.5.2 | Have there been proxy contests or board seat demands? | EVALUATE | SEC DEF 14A | sec_client | board_governance | GOV.ACTIVIST.proxy_contests, GOV.ACTIVIST.board_seat | ANSWERED |
| 4.5.3 | Are there shareholder proposals with significant support? | EVALUATE | SEC DEF 14A | sec_client | board_governance | GOV.ACTIVIST.proposal | ANSWERED |
| 4.5.4 | Is there a short activism campaign targeting governance? | EVALUATE | Web search | web_search | N/A | GOV.ACTIVIST.short_activism | ANSWERED |

**Checks Detail:**
All 14 checks route to `activist_present` or `institutional_pct`. For AAPL: 13 checks CLEAR (all activist_present=False), 1 INFO (schedule_13g institutional_pct=65.48%).

**Gap Analysis:** Comprehensive activist detection coverage with 14 checks. All evaluate cleanly for AAPL (no activist activity). The activist_present field is a boolean flag from ownership_structure extraction. Individual activist campaign details (identity, demands, timeline) are not extracted -- just the binary flag.
**Health:** GREEN

---

## 4.6 Disclosure Quality & Filing Mechanics (9 questions, 19 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 4.6.1 | How have risk factors changed year-over-year? | EVALUATE | SEC 10-K | sec_client | ten_k_converters | NLP.RISK.new_risk_factors, NLP.RISK.factor_count_change | ANSWERED |
| 4.6.2 | Have new litigation-specific or regulatory risk factors appeared? | EVALUATE | SEC 10-K | sec_client | ten_k_converters | NLP.RISK.litigation_risk_factor_new, NLP.RISK.regulatory_risk_factor_new | ANSWERED |
| 4.6.3 | Have previously disclosed risks materialized? | EVALUATE | SEC 10-K | sec_client | ten_k_converters | FWRD.DISC.risk_factor_evolution | ANSWERED |
| 4.6.4 | Has the company filed on time? | EVALUATE | SEC EDGAR | sec_client | filing_sections | GOV.EFFECT.late_filing, GOV.EFFECT.nt_filing, NLP.FILING.late_filing | ANSWERED |
| 4.6.5 | Is non-GAAP reconciliation adequate? | DISPLAY | SEC 10-K | sec_client | ten_k_converters | FWRD.DISC.non_gaap_reconciliation | ANSWERED |
| 4.6.6 | Is segment reporting consistent? | DISPLAY | SEC 10-K | sec_client | ten_k_converters | FWRD.DISC.segment_consistency | ANSWERED |
| 4.6.7 | Is related-party disclosure complete? | DISPLAY | SEC 10-K, DEF 14A | sec_client | ten_k_converters | FWRD.DISC.related_party_completeness | ANSWERED |
| 4.6.8 | Is the guidance methodology transparent? | DISPLAY | SEC 10-K | sec_client | ten_k_converters | FWRD.DISC.guidance_methodology | ANSWERED |
| 4.6.9 | Are 8-K event disclosures timely and complete? | EVALUATE | SEC 8-K | sec_client | eight_k_converter | FWRD.DISC.disclosure_quality_composite | ANSWERED |

**Checks Detail (key checks):**
- `NLP.RISK.litigation_risk_factor_new` [EVALUATIVE_CHECK]: AAPL=0 (CLEAR -- no new litigation risk factors).
- `NLP.RISK.regulatory_risk_factor_new` [EVALUATIVE_CHECK]: AAPL=0 (CLEAR).
- `NLP.RISK.factor_count_change` [EVALUATIVE_CHECK]: AAPL=0 (INFO).
- `NLP.RISK.new_risk_factors` [EVALUATIVE_CHECK]: AAPL=0 (INFO).
- `FWRD.DISC.disclosure_quality_composite` [MANAGEMENT_DISPLAY]: AAPL="2/3 disclosure components present" (INFO).
- `FWRD.DISC.guidance_methodology` [MANAGEMENT_DISPLAY]: AAPL="CONSERVATIVE" (INFO).
- `FWRD.DISC.mda_depth` [MANAGEMENT_DISPLAY]: AAPL=7 mentions (INFO).
- GOV.EFFECT checks (late_filing, nt_filing, iss_score, proxy_advisory): All SKIPPED.
- NLP.FILING checks (late_filing, filing_timing_change): SKIPPED.

**Gap Analysis:** Risk factor change detection works well (4 NLP.RISK checks). FWRD.DISC disclosure quality checks provide contextual information. GOV.EFFECT and NLP.FILING checks for late filings are all SKIPPED because the fields are not populated. Filing timing data should be derivable from EDGAR filing dates.
**Health:** GREEN (risk factor analysis works; filing timing checks SKIPPED)

---

## 4.7 Narrative Analysis & Tone (15 questions, 12 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 4.7.1 | Has the MD&A readability changed (Fog Index)? | EVALUATE | SEC 10-K | sec_client | ten_k_converters | NLP.MDA.readability_change | PARTIAL |
| 4.7.2 | Has the negative tone shifted? | EVALUATE | SEC 10-K | sec_client | ten_k_converters | NLP.MDA.tone_shift | PARTIAL |
| 4.7.3 | Is there increased hedging/qualifying language? | DISPLAY | SEC 10-K | sec_client | ten_k_converters | NLP.DISCLOSURE.hedging_language_increase | PARTIAL |
| 4.7.4 | Are forward-looking statements decreasing? | DISPLAY | SEC 10-K | sec_client | ten_k_converters | NLP.DISCLOSURE.forward_looking_decrease | PARTIAL |
| 4.7.5 | Is 10-K narrative consistent with earnings call? | DISPLAY | SEC 10-K, 8-K | sec_client | ten_k_converters | FWRD.NARRATIVE.10k_vs_earnings | PARTIAL |
| 4.7.6 | Is investor narrative consistent with SEC filings? | DISPLAY | SEC 10-K | sec_client | ten_k_converters | FWRD.NARRATIVE.investor_vs_sec | PARTIAL |
| 4.7.7 | Is there analyst skepticism? | DISPLAY | yfinance, Web search | market_client, web_search | N/A | FWRD.NARRATIVE.analyst_skepticism | PARTIAL |
| 4.7.8 | Are there short thesis narratives contradicting management? | DISPLAY | Web search | web_search | N/A | FWRD.NARRATIVE.short_thesis | PARTIAL |
| 4.7.9 | What do auditor CAMs focus on? | EVALUATE | SEC 10-K | sec_client | audit_risk | NLP.CAM.changes, FWRD.NARRATIVE.auditor_cams | PARTIAL |
| 4.7.10 | Are there red-flag phrases appearing for the first time? | EVALUATE | SEC 10-K | sec_client | ten_k_converters | NLP.RISK.new_risk_factors (cross-mapped) | PARTIAL |
| 4.7.11 | Are risk factors boilerplate or company-specific? | DISPLAY | SEC 10-K | sec_client | ten_k_converters | FWRD.DISC.risk_factor_evolution (cross-mapped) | PARTIAL |
| 4.7.12 | What does earnings call Q&A analysis reveal? | EVALUATE | SEC 8-K | sec_client | eight_k_converter | FWRD.NARRATIVE.10k_vs_earnings | PARTIAL |
| 4.7.13 | What does the full 10-K year-over-year diff show? | EVALUATE | SEC 10-K | sec_client | ten_k_converters | NLP.MDA.readability_change | PARTIAL |
| 4.7.14 | How does disclosure compare to peer filings? | EVALUATE | SEC 10-K | sec_client | ten_k_converters, peer_group | FWRD.NARRATIVE.narrative_coherence_composite | PARTIAL |
| 4.7.15 | What is the management credibility score? | COMPUTE | SEC 10-K, yfinance | sec_client, market_client | ten_k_converters | FWRD.NARRATIVE.narrative_coherence_composite | PARTIAL |

**Checks Detail:**
- `NLP.MDA.readability_change` [EVALUATIVE_CHECK]: AAPL="present" (INFO -- detected but not quantified).
- `NLP.MDA.readability_absolute` [MANAGEMENT_DISPLAY]: AAPL="present" (INFO).
- `NLP.MDA.tone_shift` [EVALUATIVE_CHECK]: AAPL="present" (INFO -- detected but not quantified).
- `NLP.DISCLOSURE.forward_looking_decrease` [MANAGEMENT_DISPLAY]: AAPL="present" (INFO).
- `NLP.DISCLOSURE.hedging_language_increase` [MANAGEMENT_DISPLAY]: AAPL="present" (INFO).
- `NLP.CAM.changes` [EVALUATIVE_CHECK]: AAPL=0 (INFO).
- `FWRD.NARRATIVE.narrative_coherence_composite` [MANAGEMENT_DISPLAY]: AAPL="COHERENT" (INFO).
- `FWRD.NARRATIVE.analyst_skepticism` [MANAGEMENT_DISPLAY]: AAPL=0.8 (INFO).
- `FWRD.NARRATIVE.short_thesis` [MANAGEMENT_DISPLAY]: AAPL=0.8 (INFO).
- `FWRD.NARRATIVE.auditor_cams` [MANAGEMENT_DISPLAY]: AAPL=0 (INFO).
- `FWRD.NARRATIVE.10k_vs_earnings` [MANAGEMENT_DISPLAY]: AAPL=SKIPPED. `FWRD.NARRATIVE.investor_vs_sec` [MANAGEMENT_DISPLAY]: AAPL=SKIPPED.

**Gap Analysis:** All 15 questions return PARTIAL. NLP checks detect presence of tone/readability/hedging patterns but do not produce quantified metrics or evaluative thresholds. Tone_shift returns "present" instead of a directional shift score. Readability returns "present" instead of Fog Index delta. Earnings call vs 10-K comparison SKIPPED (no earnings call data). Narrative coherence returns "COHERENT" label. This entire subsection needs quantified NLP metrics with thresholds.
**Health:** RED -- 15 of 15 questions PARTIAL; all checks return INFO/SKIPPED.

---

## 4.8 Whistleblower & Investigation Signals (3 questions, 3 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 4.8.1 | Is there whistleblower/qui tam language in filings? | EVALUATE | SEC 10-K | sec_client | ten_k_converters | NLP.WHISTLE.language_detected | ANSWERED |
| 4.8.2 | Is there internal investigation language? | EVALUATE | SEC 10-K | sec_client | ten_k_converters | NLP.WHISTLE.internal_investigation | ANSWERED |
| 4.8.3 | Are there signals of internal problems from public sources? | EVALUATE | SEC 8-K, Web search | sec_client, web_search | eight_k_converter | FWRD.WARN.whistleblower_exposure | ANSWERED |

**Checks Detail:**
- `NLP.WHISTLE.language_detected` [EVALUATIVE_CHECK]: AAPL=0 (CLEAR -- no whistleblower language).
- `NLP.WHISTLE.internal_investigation` [EVALUATIVE_CHECK]: AAPL=0 (CLEAR -- no investigation language).
- `FWRD.WARN.whistleblower_exposure` [EVALUATIVE_CHECK]: AAPL="Not mentioned" (INFO).

**Gap Analysis:** Well-functioning subsection. Both boolean whistleblower checks evaluate cleanly. The whistleblower_exposure check searches 10-K text and correctly returns "Not mentioned" for AAPL.
**Health:** GREEN

---

## 4.9 Media & External Narrative (2 questions, 0 checks from audit / 2 in registry)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 4.9.1 | What does social media sentiment indicate? | EVALUATE | Web search | web_search | N/A | FWRD.WARN.social_sentiment | NO CHECKS* |
| 4.9.2 | Is there investigative journalism activity? | EVALUATE | Web search | web_search | N/A | FWRD.WARN.journalism_activity | NO CHECKS* |

**Checks Detail (newly mapped in checks.json):**
- `FWRD.WARN.social_sentiment` [EVALUATIVE_CHECK]: Mapped to v6 4.9 in checks.json. AAPL=SKIPPED (no social data acquired).
- `FWRD.WARN.journalism_activity` [EVALUATIVE_CHECK]: Mapped to v6 4.9 in checks.json. AAPL=SKIPPED (no journalism data acquired).

**Gap Analysis:** Checks exist in the registry and are mapped to 4.9 subsection, but both SKIPPED because the data acquisition pipeline does not acquire social media sentiment or journalism activity data. These require web search (Brave Search MCP) during ACQUIRE stage with specific search queries for investigative journalism mentions and social media sentiment.
**Health:** RED -- checks defined but data acquisition not implemented.

---

# 5. LITIGATION & REGULATORY

## 5.1 Securities Class Actions -- Active (4 questions, 9 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 5.1.1 | Are there active securities class actions? | EVALUATE | SCAC (Stanford), SEC 10-K | litigation_client, sec_client | sca_extractor | LIT.SCA.active, LIT.SCA.search | ANSWERED |
| 5.1.2 | What are the class periods, allegations, and case stage? | EVALUATE | SCAC, SEC 10-K | litigation_client, sec_client | sca_extractor, sca_parsing | LIT.SCA.class_period, LIT.SCA.allegations, LIT.SCA.case_status | ANSWERED |
| 5.1.3 | Who is lead counsel and what tier? | EVALUATE | SCAC | litigation_client | sca_extractor | LIT.SCA.lead_plaintiff | ANSWERED |
| 5.1.4 | What is the estimated exposure (DDL and settlement range)? | EVALUATE | SCAC, SEC 10-K | litigation_client, sec_client | sca_extractor, contingent_liab | LIT.SCA.exposure | ANSWERED |

**Checks Detail:**
- `LIT.SCA.search` [EVALUATIVE_CHECK]: Routes to `total_sca_count`. AAPL=1 (TRIGGERED red, threshold >0).
- `LIT.SCA.active` [EVALUATIVE_CHECK]: Routes to `active_sca_count`. AAPL=0 (CLEAR).
- `LIT.SCA.class_period` [EVALUATIVE_CHECK]: Routes to `active_sca_count`. AAPL=0 (CLEAR).
- `LIT.SCA.allegations` [EVALUATIVE_CHECK]: Routes to `active_sca_count`. AAPL=0 (CLEAR).
- `LIT.SCA.exposure` [EVALUATIVE_CHECK]: Routes to `contingent_liabilities_total`. AAPL=0 (CLEAR).
- `LIT.SCA.filing_date` [EVALUATIVE_CHECK]: AAPL="No active SCAs" (INFO).
- `LIT.SCA.policy_status` [EVALUATIVE_CHECK]: AAPL=0 (CLEAR).
- `LIT.SCA.case_status` [EVALUATIVE_CHECK]: AAPL=NOT_RUN (MANUAL_ONLY).
- `LIT.SCA.lead_plaintiff` [EVALUATIVE_CHECK]: AAPL=NOT_RUN (MANUAL_ONLY).

**Gap Analysis:** SCA detection works well. SCAC database search finds 1 historical case (TRIGGERED red on total_sca_count). Active SCA count correctly shows 0 current cases. Case_status and lead_plaintiff are MANUAL_ONLY execution mode (require analyst review). Exposure and policy_status check evaluative.
**Health:** GREEN

---

## 5.2 Securities Class Action History (4 questions, 7 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 5.2.1 | How many prior SCAs has this company had? | EVALUATE | SCAC | litigation_client | sca_extractor | LIT.SCA.historical | ANSWERED |
| 5.2.2 | What were the outcomes (dismissed, settled, amount)? | EVALUATE | SCAC | litigation_client | sca_extractor | LIT.SCA.prior_settle, LIT.SCA.settle_amount, LIT.SCA.prior_dismiss | ANSWERED |
| 5.2.3 | Is there a recidivist pattern (repeat filer)? | EVALUATE | SCAC | litigation_client | sca_extractor | LIT.SCA.historical | ANSWERED |
| 5.2.4 | Are there pre-filing signals? | EVALUATE | Web search, SCAC | web_search, litigation_client | sca_extractor | LIT.SCA.prefiling | ANSWERED |

**Checks Detail:**
- `LIT.SCA.historical` [EVALUATIVE_CHECK]: Routes to `total_sca_count`. AAPL=1 (TRIGGERED yellow, threshold >0).
- `LIT.SCA.prior_settle` [EVALUATIVE_CHECK]: Routes to `settled_sca_count`. AAPL=1 (INFO).
- `LIT.SCA.settle_amount` [EVALUATIVE_CHECK]: Routes to `contingent_liabilities_total`. AAPL=0 (CLEAR).
- `LIT.SCA.prior_dismiss` [EVALUATIVE_CHECK]: Routes to `total_sca_count`. AAPL=1 (CLEAR, threshold allows some).
- `LIT.SCA.prefiling` [EVALUATIVE_CHECK]: Routes to `active_sca_count`. AAPL=0 (CLEAR).
- `LIT.SCA.settle_date` [EVALUATIVE_CHECK]: AAPL=1 (INFO). `LIT.SCA.dismiss_basis` [EVALUATIVE_CHECK]: NOT_RUN (MANUAL_ONLY).

**Gap Analysis:** SCAC data well-utilized. Historical count triggers yellow (1 prior case). Settlement amount CLEAR at 0 (amount not extracted from SCAC). Dismiss_basis requires manual review. Recidivist pattern detection works via historical count threshold.
**Health:** GREEN

---

## 5.3 Derivative & Merger Litigation (6 questions, 4 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 5.3.1 | Are there active derivative suits? | EVALUATE | SEC 10-K | sec_client | derivative_suits | LIT.SCA.derivative | ANSWERED |
| 5.3.2 | Are there merger objection lawsuits? | EVALUATE | SEC 10-K | sec_client | deal_litigation | LIT.SCA.merger_obj | ANSWERED |
| 5.3.3 | Has the company received Section 220 demands? | EVALUATE | SEC 10-K | sec_client | ten_k_converters | LIT.SCA.demand | ANSWERED |
| 5.3.4 | Are there ERISA class actions? | EVALUATE | SEC 10-K | sec_client | ten_k_converters | LIT.SCA.erisa | ANSWERED |
| 5.3.5 | Are there appraisal actions? | EVALUATE | SEC 10-K | sec_client | ten_k_converters | LIT.SCA.merger_obj | ANSWERED |
| 5.3.6 | What derivative suit risk factors are present? | EVALUATE | SEC 10-K | sec_client | derivative_suits | LIT.SCA.derivative | ANSWERED |

**Checks Detail:**
- `LIT.SCA.derivative` [EVALUATIVE_CHECK]: Routes to `derivative_suit_count`. AAPL=3 (TRIGGERED red, threshold >1).
- `LIT.SCA.demand` [EVALUATIVE_CHECK]: Routes to `derivative_suit_count`. AAPL=3 (TRIGGERED red, threshold >0).
- `LIT.SCA.merger_obj` [EVALUATIVE_CHECK]: Routes to `deal_litigation_count`. AAPL=0 (CLEAR).
- `LIT.SCA.erisa` [EVALUATIVE_CHECK]: Routes to `regulatory_count`. AAPL=2 (TRIGGERED red, threshold >0).

**Gap Analysis:** Strong evaluative coverage. AAPL has 3 derivative suits detected (TRIGGERED red). ERISA action detection triggers at 2 regulatory proceedings (may be over-counting -- regulatory_count includes non-ERISA items). Merger objection correctly CLEAR at 0. Section 220 demands route to derivative_suit_count rather than a dedicated field.
**Health:** GREEN

---

## 5.4 SEC Enforcement (4 questions, 9 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 5.4.1 | What stage is any SEC matter at? | EVALUATE | SEC 10-K, SEC Enforcement | sec_client | sec_enforcement | LIT.REG.sec_investigation, LIT.REG.sec_active, LIT.REG.sec_severity | PARTIAL |
| 5.4.2 | Are there SEC comment letters? | EVALUATE | SEC EDGAR | sec_client | sec_enforcement | LIT.REG.comment_letters | PARTIAL |
| 5.4.3 | Has there been a Wells Notice? | EVALUATE | SEC 10-K | sec_client | sec_enforcement | LIT.REG.wells_notice | PARTIAL |
| 5.4.4 | What prior SEC enforcement actions exist? | EVALUATE | SEC Enforcement | sec_client | sec_enforcement | LIT.REG.cease_desist, LIT.REG.civil_penalty, LIT.REG.consent_order, LIT.REG.deferred_pros | PARTIAL |

**Checks Detail:**
- `LIT.REG.sec_investigation` [EVALUATIVE_CHECK]: Routes to `sec_enforcement_stage`. AAPL="NONE" (INFO).
- `LIT.REG.sec_active` [EVALUATIVE_CHECK]: Routes to `sec_enforcement_stage`. AAPL="NONE" (INFO).
- `LIT.REG.sec_severity` [EVALUATIVE_CHECK]: Routes to `sec_enforcement_stage`. AAPL="NONE" (INFO).
- `LIT.REG.wells_notice` [EVALUATIVE_CHECK]: Routes to `wells_notice`. AAPL=False (INFO).
- `LIT.REG.comment_letters` [EVALUATIVE_CHECK]: AAPL=SKIPPED. `LIT.REG.cease_desist`: AAPL=SKIPPED.
- `LIT.REG.civil_penalty`: AAPL=SKIPPED. `LIT.REG.consent_order`: AAPL=SKIPPED. `LIT.REG.deferred_pros`: AAPL=SKIPPED.

**Gap Analysis:** SEC enforcement stage is extracted as "NONE" for AAPL but returned as INFO (qualitative) rather than CLEAR. Wells notice detected as False but also INFO. 5 of 9 checks SKIPPED because comment_letter_count, cease_desist_count, civil_penalty_count, consent_order_count, and deferred_prosecution_count fields are not populated. The sec_enforcement extraction module exists but does not extract historical enforcement action counts.
**Health:** YELLOW -- SEC stage detected but checks return INFO instead of evaluative; count fields not populated.

---

## 5.5 Other Regulatory & Government (6 questions, 13 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 5.5.1 | Which government agencies regulate this company? | EVALUATE | SEC 10-K | sec_client | regulatory_extract | LIT.REG.industry_reg | ANSWERED |
| 5.5.2 | Are there active DOJ investigations? | EVALUATE | SEC 10-K, Web search | sec_client, web_search | ten_k_converters | LIT.REG.doj_investigation | ANSWERED |
| 5.5.3 | Are there state AG investigations? | EVALUATE | SEC 10-K, Web search | sec_client, web_search | ten_k_converters | LIT.REG.state_ag | ANSWERED |
| 5.5.4 | Are there industry-specific enforcement actions? | EVALUATE | SEC 10-K, Web search | sec_client, web_search | regulatory_extract | LIT.REG.ftc_investigation, LIT.REG.fda_warning, etc. | ANSWERED |
| 5.5.5 | Are there foreign government enforcement matters? | EVALUATE | SEC 10-K | sec_client | ten_k_converters | LIT.REG.foreign_gov | ANSWERED |
| 5.5.6 | Are there congressional investigations or subpoenas? | EVALUATE | SEC 10-K, Web search | sec_client, web_search | ten_k_converters | LIT.REG.subpoena | ANSWERED |

**Checks Detail:**
- `LIT.REG.industry_reg` [EVALUATIVE_CHECK]: AAPL=2 (CLEAR, threshold allows some regulatory presence).
- `LIT.REG.doj_investigation` [EVALUATIVE_CHECK]: AAPL=2 (INFO -- qualitative).
- `LIT.REG.ftc_investigation` [EVALUATIVE_CHECK]: AAPL=2 (INFO -- qualitative).
- 10 other LIT.REG checks: All SKIPPED (sector-specific agencies not applicable or data not extracted).

**Gap Analysis:** Industry regulatory presence detected (count=2 for AAPL). DOJ and FTC investigation counts show 2 but return INFO rather than evaluative. 10 of 13 sector-specific checks SKIPPED (cfpb, dol, epa, fda, fdic, osha, foreign_gov, state_ag, state_action, subpoena). These are correctly sector-conditional -- most are not applicable to tech companies.
**Health:** GREEN

---

## 5.6 Non-Securities Litigation (4 questions, 14 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 5.6.1 | What is the aggregate active litigation count? | EVALUATE | SEC 10-K | sec_client | ten_k_converters, contingent_liab | LIT.OTHER.aggregate | ANSWERED |
| 5.6.2 | Are there significant product liability, employment, IP, or antitrust matters? | EVALUATE | SEC 10-K | sec_client | ten_k_converters | LIT.OTHER.product, LIT.OTHER.employment, LIT.OTHER.ip, LIT.OTHER.antitrust | ANSWERED |
| 5.6.3 | Are there whistleblower/qui tam actions? | EVALUATE | SEC 10-K | sec_client | ten_k_converters | LIT.OTHER.whistleblower | ANSWERED |
| 5.6.4 | Are there cyber breach or environmental litigation matters? | EVALUATE | SEC 10-K | sec_client | ten_k_converters | LIT.OTHER.cyber_breach, LIT.OTHER.environmental | ANSWERED |

**Checks Detail:**
- `LIT.OTHER.aggregate` [EVALUATIVE_CHECK]: Routes to `active_matter_count`. AAPL=0 (CLEAR).
- `LIT.OTHER.whistleblower` [EVALUATIVE_CHECK]: Routes to `whistleblower_count`. AAPL=0 (INFO).
- 12 other LIT.OTHER checks: All SKIPPED (specific litigation type counts not populated from 10-K extraction).

**Gap Analysis:** Aggregate active matter count works (CLEAR at 0 for AAPL). Individual litigation type counts (product_liability_count, employment_lit_count, ip_litigation_count, antitrust_count, cyber_breach_count, etc.) are all SKIPPED because the 10-K litigation section extraction does not categorize matters by type. The extraction pipeline extracts total counts but does not classify individual matters into categories.
**Health:** GREEN (aggregate works; individual categorization needs extraction enhancement)

---

## 5.7 Defense Posture & Reserves (3 questions, 3 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 5.7.1 | What defense provisions exist (federal forum, PSLRA safe harbor)? | EVALUATE | SEC DEF 14A, bylaws | sec_client | board_governance | LIT.DEFENSE.forum_selection | NO CHECKS* |
| 5.7.2 | What are the contingent liabilities and litigation reserves (ASC 450)? | EVALUATE | SEC 10-K, 10-Q | sec_client | contingent_liab, contingent_notes | LIT.DEFENSE.contingent_liabilities | NO CHECKS* |
| 5.7.3 | What is the historical defense success rate? | DISPLAY | SCAC | litigation_client | sca_extractor | LIT.DEFENSE.pslra_safe_harbor | NO CHECKS* |

**Checks Detail (newly added in Plan 33-03):**
- `LIT.DEFENSE.forum_selection` [EVALUATIVE_CHECK]: Defined in checks.json with v6 5.7. Not yet wired to data mapper.
- `LIT.DEFENSE.contingent_liabilities` [EVALUATIVE_CHECK]: Defined in checks.json with v6 5.7. Not yet wired to data mapper.
- `LIT.DEFENSE.pslra_safe_harbor` [MANAGEMENT_DISPLAY]: Defined in checks.json with v6 5.7. Not yet wired to data mapper.

**Gap Analysis:** Checks defined in checks.json but data mappers, field routing, and extraction pipeline not connected. Contingent liabilities extraction module (contingent_liab.py, contingent_notes.py) exists and could provide data. Forum selection requires DEF 14A/bylaws extraction. Defense success rate requires SCAC outcome analysis. All 3 checks will SKIP until mapper integration is completed.
**Health:** RED -- checks defined but not functional.

---

## 5.8 Litigation Risk Patterns (4 questions, 5 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 5.8.1 | What are the open statute of limitations windows? | EVALUATE | SEC 10-K, SCAC | sec_client, litigation_client | sol_mapper | LIT.PATTERN.sol_windows | NO CHECKS* |
| 5.8.2 | What industry-specific allegation theories apply? | EVALUATE | SCAC, industry data | litigation_client | sca_extractor | LIT.PATTERN.industry_theories | NO CHECKS* |
| 5.8.3 | What is the contagion risk from peer lawsuits? | INFER | SCAC | litigation_client | sca_extractor | LIT.PATTERN.peer_contagion, BIZ.COMP.peer_litigation | NO CHECKS* |
| 5.8.4 | Do financial events temporally correlate with stock drops to create class period windows? | INFER | yfinance, SEC filings | market_client, sec_client | stock_drops | LIT.PATTERN.temporal_correlation | NO CHECKS* |

**Checks Detail (newly added in Plan 33-03):**
- `LIT.PATTERN.sol_windows` [EVALUATIVE_CHECK]: Defined. Sol_mapper extraction module exists. Not yet wired to check mapper.
- `LIT.PATTERN.industry_theories` [EVALUATIVE_CHECK]: Defined. Requires SCAC allegation pattern analysis.
- `LIT.PATTERN.peer_contagion` [INFERENCE_PATTERN]: Defined. Requires peer SCA data cross-reference.
- `LIT.PATTERN.temporal_correlation` [INFERENCE_PATTERN]: Defined. Requires stock drop / filing event temporal alignment.
- `BIZ.COMP.peer_litigation` [MANAGEMENT_DISPLAY]: Cross-mapped from 1.7. Routes to `active_sca_count`.

**Gap Analysis:** 4 new checks defined in checks.json plus 1 cross-mapped. Sol_mapper extraction module exists in `src/do_uw/stages/extract/sol_mapper.py` and could provide statute of limitations data. Peer contagion and temporal correlation are INFERENCE_PATTERN type requiring multi-signal analysis. None are wired to data mappers yet.
**Health:** RED -- checks and some extraction modules exist but not connected.

---

## 5.9 Sector-Specific Litigation & Regulatory Patterns (2 questions, 2 checks)

| # | Question | Type | Data Source | Acquisition | Extraction | Key Checks | Status |
|---|----------|------|-------------|-------------|------------|------------|--------|
| 5.9.1 | What sector-specific litigation patterns apply to this company? | EVALUATE | SCAC, industry data | litigation_client | sca_extractor | LIT.SECTOR.industry_patterns | NO CHECKS* |
| 5.9.2 | What do sector-specific regulatory databases show? | EVALUATE | Sector APIs (FDA, NHTSA, CFPB, etc.) | web_search | N/A | LIT.SECTOR.regulatory_databases | NO CHECKS* |

**Checks Detail (newly added in Plan 33-03):**
- `LIT.SECTOR.industry_patterns` [EVALUATIVE_CHECK]: Defined in checks.json. Not yet wired.
- `LIT.SECTOR.regulatory_databases` [EVALUATIVE_CHECK]: Defined in checks.json. Not yet wired.

**Gap Analysis:** Checks defined but not connected. Sector-specific litigation patterns require industry-specific allegation databases. Regulatory databases (FDA MedWatch, NHTSA, CFPB, etc.) require dedicated API integrations or web search acquisition.
**Health:** RED -- checks defined but no data acquisition or extraction pipeline.

---

# Cross-Cutting Summary

## Per-Section Health

| Section | GREEN | YELLOW | RED | Total |
|---------|-------|--------|-----|-------|
| 1. COMPANY | 3 (1.1, 1.3, 1.11) | 4 (1.2, 1.5, 1.6, 1.7, 1.8) | 3 (1.4, 1.9, 1.10) | 11 |
| 2. MARKET | 5 (2.1, 2.2, 2.4, 2.5, 2.8) | 3 (2.3, 2.6, 2.7) | 0 | 8 |
| 3. FINANCIAL | 6 (3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.8) | 1 (3.7) | 0 | 8 |
| 4. GOVERNANCE | 4 (4.2, 4.5, 4.6, 4.8) | 3 (4.1, 4.3, 4.4) | 2 (4.7, 4.9) | 9 |
| 5. LITIGATION | 4 (5.1, 5.2, 5.3, 5.5, 5.6) | 1 (5.4) | 3 (5.7, 5.8, 5.9) | 9 |
| **TOTAL** | **22** | **12** | **8** | **45** |

## Data Acquisition Gap Summary

| Data Source | Subsections Blocked | Impact |
|-------------|-------------------|--------|
| DEF 14A detailed parsing | 4.1, 4.3, 4.4 | Board composition, compensation details, shareholder rights all SKIPPED |
| Web search (employee platforms) | 1.9 | Glassdoor, Indeed, Blind, LinkedIn data not acquired |
| Web search (customer platforms) | 1.10 | CFPB, app stores, Trustpilot, G2 data not acquired |
| Web search (social/journalism) | 4.9 | Social media sentiment, investigative journalism not acquired |
| Sector-specific APIs | 5.9 | FDA MedWatch, NHTSA, CFPB APIs not integrated |
| Earnings guidance extraction | 3.7 | Beat/miss history, estimates not connected to checks |
| NLP quantified metrics | 4.7 | Tone shift, readability change detected but not quantified |

## Check Coverage Statistics (from checks.json registry)

| Subsection | Checks in Registry | Checks Fired (AAPL) | TRIGGERED | CLEAR | INFO | SKIPPED/NOT_RUN |
|------------|-------------------|---------------------|-----------|-------|------|-----------------|
| 1.1 | 8 | 8 | 1 | 0 | 7 | 0 |
| 1.2 | 8 | 8 | 0 | 0 | 8 | 0 |
| 1.3 | 17 | 13 | 5 | 2 | 6 | 0 |
| 1.4 | 3 | 0 | 0 | 0 | 0 | 3 |
| 1.5 | 4 | 1 | 0 | 0 | 1 | 0 |
| 1.6 | 2 | 2 | 0 | 0 | 2 | 0 |
| 1.7 | 12 | 11 | 0 | 0 | 11 | 0 |
| 1.8 | 15 | 18 | 0 | 0 | 18 | 0 |
| 1.9 | 6 | 8 | 0 | 0 | 3 | 5 |
| 1.10 | 3 | 11 | 0 | 0 | 3 | 8 |
| 1.11 | 17 | 17 | 0 | 1 | 14 | 2 |
| 2.1 | 9 | 8 | 0 | 6 | 2 | 0 |
| 2.2 | 10 | 4 | 0 | 3 | 1 | 0 |
| 2.3 | 3 | 6 | 0 | 0 | 6 | 0 |
| 2.4 | 4 | 4 | 0 | 2 | 2 | 0 |
| 2.5 | 5 | 4 | 0 | 1 | 3 | 0 |
| 2.6 | 2 | 2 | 0 | 0 | 2 | 0 |
| 2.7 | 4 | 4 | 0 | 1 | 0 | 3 |
| 2.8 | 15 | 16 | 4 | 3 | 4 | 5 |
| 3.1 | 7 | 5 | 3 | 0 | 2 | 0 |
| 3.2 | 7 | 5 | 0 | 2 | 2 | 1 |
| 3.3 | 20 | 10 | 0 | 1 | 9 | 0 |
| 3.4 | 15 | 17 | 1 | 8 | 6 | 2 |
| 3.5 | 16 | 18 | 0 | 6 | 2 | 10 |
| 3.6 | 37 | 5 | 0 | 2 | 3 | 0 |
| 3.7 | 7 | 5 | 0 | 0 | 5 | 0 |
| 3.8 | 2 | 10 | 0 | 1 | 9 | 0 |
| 4.1 | 29 | 18 | 1 | 1 | 1 | 15 |
| 4.2 | 27 | 22 | 0 | 13 | 7 | 2 |
| 4.3 | 15 | 15 | 2 | 1 | 1 | 11 |
| 4.4 | 10 | 10 | 0 | 1 | 1 | 8 |
| 4.5 | 15 | 14 | 0 | 13 | 1 | 0 |
| 4.6 | 21 | 19 | 0 | 2 | 10 | 7 |
| 4.7 | 10 | 12 | 0 | 0 | 10 | 2 |
| 4.8 | 2 | 3 | 0 | 2 | 1 | 0 |
| 4.9 | 2 | 0 | 0 | 0 | 0 | 2 |
| 5.1 | 23 | 9 | 1 | 5 | 1 | 2 |
| 5.2 | 3 | 7 | 1 | 3 | 2 | 1 |
| 5.3 | 3 | 4 | 3 | 1 | 0 | 0 |
| 5.4 | 23 | 9 | 0 | 0 | 4 | 5 |
| 5.5 | 1 | 13 | 0 | 1 | 2 | 10 |
| 5.6 | 14 | 14 | 0 | 1 | 1 | 12 |
| 5.7 | 3 | 0 | 0 | 0 | 0 | 0 |
| 5.8 | 5 | 0 | 0 | 0 | 0 | 0 |
| 5.9 | 2 | 0 | 0 | 0 | 0 | 0 |

**Note:** "Checks in Registry" counts from checks.json v6_subsection_ids. "Checks Fired" counts from AAPL backtest in QUESTION-AUDIT.md. Discrepancies arise because: (1) checks can be cross-mapped to multiple subsections, (2) new checks added in Plan 33-03 were not in the backtest, (3) some subsections share checks across sections.

## Known False Triggers (AAPL Backtest)

| Check | Value | Threshold | Issue |
|-------|-------|-----------|-------|
| BIZ.DEPEND.labor | 150,000 | red >2 | Reads employee_count instead of labor_risk_flag_count (routing fix applied but extraction not updated) |
| FIN.LIQ.position | 0.8933 | red <6.0 | Threshold of 6.0 is unreasonably high for tech sector -- needs sector calibration |
| GOV.PAY.peer_comparison | 533 | red >75 | Uses ceo_pay_ratio (533:1) but threshold expects percentile rank (75th) -- field interpretation mismatch |

## Processing Type Distribution

| Processing Type | Question Count | % |
|----------------|---------------|---|
| EVALUATE | 153 | 66.2% |
| DISPLAY | 45 | 19.5% |
| COMPUTE | 14 | 6.1% |
| INFER | 19 | 8.2% |
