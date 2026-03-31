# Question-to-Pipeline Audit: Complete Coverage Analysis

**Date:** 2026-02-20
**Test Company:** AAPL (Apple Inc.)
**Source Framework:** v6 Taxonomy (231 questions, 45 subsections)
**Check Registry:** brain/checks.json (384 checks, 377 AUTO-executed)

## Assessment Legend

| Status | Meaning |
|--------|---------|
| **ANSWERED** | Has TRIGGERED or CLEAR checks -- we got data AND evaluated it |
| **PARTIAL** | Has some data (INFO) but can't fully evaluate -- missing thresholds or wrong data type |
| **NO DATA** | All checks SKIPPED -- we didn't get the data at all |
| **NO CHECKS** | No checks mapped to this question/subsection |
| **DISPLAY ONLY** | Only MANAGEMENT_DISPLAY checks -- shows context but doesn't evaluate risk |

---

# 1. COMPANY

## 1.1 Identity
*What is this company?*

**Subsection Assessment: ANSWERED** (8 checks)

**Checks:**
- `BIZ.CLASS.litigation_history`: **TRIGGERED** (red) = `1.0`
  - Evidence: Value 1.0 exceeds red threshold 0.0
- `BIZ.CLASS.primary`: **INFO** [MANAGEMENT_DISPLAY] = `MEGA`
  - Evidence: Management display: MEGA
- `BIZ.CLASS.secondary`: **INFO** [MANAGEMENT_DISPLAY] = `MEGA`
  - Evidence: Management display: MEGA
- `BIZ.SIZE.employees`: **INFO** [MANAGEMENT_DISPLAY] = `150000.0`
  - Evidence: Management display: 150000
- `BIZ.SIZE.growth_trajectory`: **INFO** [MANAGEMENT_DISPLAY] = `45.0`
  - Evidence: Management display: 45
- `BIZ.SIZE.market_cap`: **INFO** [MANAGEMENT_DISPLAY] = `3759435415552.0`
  - Evidence: Management display: 3759435415552.0
- `BIZ.SIZE.public_tenure`: **INFO** [MANAGEMENT_DISPLAY] = `45.0`
  - Evidence: Management display: 45
- `BIZ.SIZE.revenue_ttm`: **INFO** [MANAGEMENT_DISPLAY] = `Apple Inc. operates in the Consumer Electronics industry. Th...`
  - Evidence: Management display: Apple Inc. operates in the Consumer Electronics industry. The company has 150,000 employees and $375...

### 1.1.1: What industry is this company in? (SIC, NAICS, GICS codes and sector/industry classification)
**Status**: ANSWERED
**Data path**: MARKET_PRICE, SCAC_SEARCH, SEC_10K -> employee_count, market_cap, risk_classification, section_summary, total_sca_count, years_public
**Gap**: None -- question is being answered with evaluative checks

### 1.1.2: What are the key company metrics? (Market cap, enterprise value, employee count, revenue, headquarters)
**Status**: ANSWERED
**Data path**: MARKET_PRICE, SCAC_SEARCH, SEC_10K -> employee_count, market_cap, risk_classification, section_summary, total_sca_count, years_public
**Gap**: None -- question is being answered with evaluative checks

### 1.1.3: What lifecycle stage is this company in (IPO, growth, mature, distressed, SPAC)?
**Status**: ANSWERED
**Data path**: MARKET_PRICE, SCAC_SEARCH, SEC_10K -> employee_count, market_cap, risk_classification, section_summary, total_sca_count, years_public
**Gap**: None -- question is being answered with evaluative checks

### 1.1.4: What is the state of incorporation and what legal regime applies?
**Status**: ANSWERED
**Data path**: MARKET_PRICE, SCAC_SEARCH, SEC_10K -> employee_count, market_cap, risk_classification, section_summary, total_sca_count, years_public
**Gap**: None -- question is being answered with evaluative checks

### 1.1.5: What exchange is it listed on and is it a Foreign Private Issuer?
**Status**: ANSWERED
**Data path**: MARKET_PRICE, SCAC_SEARCH, SEC_10K -> employee_count, market_cap, risk_classification, section_summary, total_sca_count, years_public
**Gap**: None -- question is being answered with evaluative checks

## 1.2 Business Model & Revenue
*How does this company make money?*

**Subsection Assessment: DISPLAY ONLY** (8 checks)

**Checks:**
- `BIZ.MODEL.capital_intensity`: **INFO** [MANAGEMENT_DISPLAY] = `Not mentioned in 10-K filing`
  - Evidence: Management display: Not mentioned in 10-K filing
- `BIZ.MODEL.cost_structure`: **INFO** [MANAGEMENT_DISPLAY] = `20 mention(s): l be subject to volatility and downward press...`
  - Evidence: Management display: 20 mention(s): l be subject to volatility and downward pressure. Operating Expenses Operating expens...
- `BIZ.MODEL.description`: **INFO** [MANAGEMENT_DISPLAY] = `Company Background The Company designs, manufactures and mar...`
  - Evidence: Management display: Company Background The Company designs, manufactures and markets smartphones, personal computers, ta...
- `BIZ.MODEL.leverage_ops`: **INFO** [MANAGEMENT_DISPLAY] = `20 mention(s): l be subject to volatility and downward press...`
  - Evidence: Management display: 20 mention(s): l be subject to volatility and downward pressure. Operating Expenses Operating expens...
- `BIZ.MODEL.regulatory_dep`: **INFO** [MANAGEMENT_DISPLAY] = `6 mention(s): enforcement of its intellectual property right...`
  - Evidence: Management display: 6 mention(s): enforcement of its intellectual property rights. Regulatory requirements, government i...
- `BIZ.MODEL.revenue_geo`: **INFO** [MANAGEMENT_DISPLAY] = `Ireland, Japan, Canada, India, Mexico, Singapore, Thailand, ...`
  - Evidence: Management display: Ireland, Japan, Canada, India, Mexico, Singapore, Thailand, Vietnam, Delaware, China
- `BIZ.MODEL.revenue_segment`: **INFO** [MANAGEMENT_DISPLAY] = `11 mention(s): erformance The following table shows net sale...`
  - Evidence: Management display: 11 mention(s): erformance The following table shows net sales by reportable segment for 2025, 2024 a...
- `BIZ.MODEL.revenue_type`: **INFO** [MANAGEMENT_DISPLAY] = `11 mention(s): erformance The following table shows net sale...`
  - Evidence: Management display: 11 mention(s): erformance The following table shows net sales by reportable segment for 2025, 2024 a...

### 1.2.1: What is the company's primary business model and revenue type?
**Status**: DISPLAY ONLY
**Data path**: SEC_10K -> business_description, capital_intensity_ratio, cost_structure_analysis, model_regulatory_dependency, operating_leverage, revenue_geographic_mix, revenue_segment_breakdown, revenue_type_analysis
**Gap**: Only MANAGEMENT_DISPLAY checks present -- shows data but no risk evaluation. Consider adding evaluative thresholds.

### 1.2.2: How is revenue broken down by segment?
**Status**: DISPLAY ONLY
**Data path**: SEC_10K -> business_description, capital_intensity_ratio, cost_structure_analysis, model_regulatory_dependency, operating_leverage, revenue_geographic_mix, revenue_segment_breakdown, revenue_type_analysis
**Gap**: Only MANAGEMENT_DISPLAY checks present -- shows data but no risk evaluation. Consider adding evaluative thresholds.

### 1.2.3: What are the key products/services and how concentrated is the product portfolio?
**Status**: DISPLAY ONLY
**Data path**: SEC_10K -> business_description, capital_intensity_ratio, cost_structure_analysis, model_regulatory_dependency, operating_leverage, revenue_geographic_mix, revenue_segment_breakdown, revenue_type_analysis
**Gap**: Only MANAGEMENT_DISPLAY checks present -- shows data but no risk evaluation. Consider adding evaluative thresholds.

### 1.2.4: What is the cost structure and operating leverage?
**Status**: DISPLAY ONLY
**Data path**: SEC_10K -> business_description, capital_intensity_ratio, cost_structure_analysis, model_regulatory_dependency, operating_leverage, revenue_geographic_mix, revenue_segment_breakdown, revenue_type_analysis
**Gap**: Only MANAGEMENT_DISPLAY checks present -- shows data but no risk evaluation. Consider adding evaluative thresholds.

### 1.2.5: What is the recurring vs non-recurring revenue mix?
**Status**: DISPLAY ONLY
**Data path**: SEC_10K -> business_description, capital_intensity_ratio, cost_structure_analysis, model_regulatory_dependency, operating_leverage, revenue_geographic_mix, revenue_segment_breakdown, revenue_type_analysis
**Gap**: Only MANAGEMENT_DISPLAY checks present -- shows data but no risk evaluation. Consider adding evaluative thresholds.

### 1.2.6: Is there an "Innovation/Investment Gap" -- does the company's public AI/tech narrative diverge from actual R&D/CAPEX spend?
**Status**: DISPLAY ONLY
**Data path**: SEC_10K -> business_description, capital_intensity_ratio, cost_structure_analysis, model_regulatory_dependency, operating_leverage, revenue_geographic_mix, revenue_segment_breakdown, revenue_type_analysis
**Gap**: Only MANAGEMENT_DISPLAY checks present -- shows data but no risk evaluation. Consider adding evaluative thresholds.

## 1.3 Operations & Dependencies
*What does this company depend on to operate?*

**Subsection Assessment: ANSWERED** (13 checks)

**Checks:**
- `BIZ.DEPEND.capital_dep`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds
- `BIZ.DEPEND.contract_terms`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds
- `BIZ.DEPEND.customer_conc`: **INFO** = `Not mentioned in 10-K filing`
  - Evidence: percentage check: value=Not mentioned in 10-K filing
- `BIZ.DEPEND.distribution`: **TRIGGERED** (red) = `4.0`
  - Evidence: Value 4.0 exceeds red threshold 3.0
- `BIZ.DEPEND.key_person`: **INFO** = `150000.0`
  - Evidence: Qualitative check: value=150000
- `BIZ.DEPEND.labor`: **TRIGGERED** (red) = `150000.0`
  - Evidence: Value 150000.0 exceeds red threshold 2.0
- `BIZ.DEPEND.macro_sensitivity`: **TRIGGERED** (red) = `10.0`
  - Evidence: Value 10.0 exceeds red threshold 5.0
- `BIZ.DEPEND.regulatory_dep`: **TRIGGERED** (yellow) = `2.0`
  - Evidence: Value 2.0 exceeds yellow threshold 1.0
- `BIZ.DEPEND.supplier_conc`: **INFO** = `1 mention(s): e Company remains subject to significant risks...`
  - Evidence: percentage check: value=1 mention(s): e Company remains subject to significant risks of supply shortages and price incre...
- `BIZ.DEPEND.tech_dep`: **TRIGGERED** (yellow) = `2.0`
  - Evidence: Value 2.0 exceeds yellow threshold 1.0
- `BIZ.UNI.ai_claims`: **INFO** [MANAGEMENT_DISPLAY] = `9 mention(s): oduction of new and complex technologies, such...`
  - Evidence: Management display: 9 mention(s): oduction of new and complex technologies, such as artificial intelligence features, ca...
- `BIZ.UNI.cyber_business`: **INFO** [MANAGEMENT_DISPLAY] = `Not mentioned in 10-K filing`
  - Evidence: Management display: Not mentioned in 10-K filing
- `BIZ.UNI.cyber_posture`: **INFO** [MANAGEMENT_DISPLAY] = `9 mention(s): acks and other hostile acts, ransomware and ot...`
  - Evidence: Management display: 9 mention(s): acks and other hostile acts, ransomware and other cybersecurity attacks, labor dispute...

### 1.3.1: How concentrated is the customer base?
**Status**: ANSWERED
**Data path**: SEC_10K -> ai_risk_exposure, capital_dependency_count, contract_terms_count, customer_concentration, cyber_business_risk, cybersecurity_posture, distribution_channels_count, employee_count, macro_sensitivity_count, regulatory_dependency_count, supplier_concentration, technology_dependency_count
**Gap**: None -- question is being answered with evaluative checks

### 1.3.2: How dependent is the company on key suppliers or single-source inputs?
**Status**: ANSWERED
**Data path**: SEC_10K -> ai_risk_exposure, capital_dependency_count, contract_terms_count, customer_concentration, cyber_business_risk, cybersecurity_posture, distribution_channels_count, employee_count, macro_sensitivity_count, regulatory_dependency_count, supplier_concentration, technology_dependency_count
**Gap**: None -- question is being answered with evaluative checks

### 1.3.3: How complex and vulnerable is the supply chain?
**Status**: ANSWERED
**Data path**: SEC_10K -> ai_risk_exposure, capital_dependency_count, contract_terms_count, customer_concentration, cyber_business_risk, cybersecurity_posture, distribution_channels_count, employee_count, macro_sensitivity_count, regulatory_dependency_count, supplier_concentration, technology_dependency_count
**Gap**: None -- question is being answered with evaluative checks

### 1.3.4: What is the workforce profile and labor risk?
**Status**: ANSWERED
**Data path**: SEC_10K -> ai_risk_exposure, capital_dependency_count, contract_terms_count, customer_concentration, cyber_business_risk, cybersecurity_posture, distribution_channels_count, employee_count, macro_sensitivity_count, regulatory_dependency_count, supplier_concentration, technology_dependency_count
**Gap**: None -- question is being answered with evaluative checks

### 1.3.5: What technology, IP, or regulatory dependencies exist?
**Status**: ANSWERED
**Data path**: SEC_10K -> ai_risk_exposure, capital_dependency_count, contract_terms_count, customer_concentration, cyber_business_risk, cybersecurity_posture, distribution_channels_count, employee_count, macro_sensitivity_count, regulatory_dependency_count, supplier_concentration, technology_dependency_count
**Gap**: None -- question is being answered with evaluative checks

### 1.3.6: What is the government contract exposure?
**Status**: ANSWERED
**Data path**: SEC_10K -> ai_risk_exposure, capital_dependency_count, contract_terms_count, customer_concentration, cyber_business_risk, cybersecurity_posture, distribution_channels_count, employee_count, macro_sensitivity_count, regulatory_dependency_count, supplier_concentration, technology_dependency_count
**Gap**: None -- question is being answered with evaluative checks

### 1.3.7: What is the data/privacy risk profile? (PII, PHI, financial, children's data; CCPA, GDPR, HIPAA)
**Status**: ANSWERED
**Data path**: SEC_10K -> ai_risk_exposure, capital_dependency_count, contract_terms_count, customer_concentration, cyber_business_risk, cybersecurity_posture, distribution_channels_count, employee_count, macro_sensitivity_count, regulatory_dependency_count, supplier_concentration, technology_dependency_count
**Gap**: None -- question is being answered with evaluative checks

### 1.3.8: Does the company have sector-specific hazard exposure? (Binary flags: Opioid, PFAS, Crypto, Cannabis, China VIE, AI/ML, Nuclear/defense, Social media/content)
**Status**: ANSWERED
**Data path**: SEC_10K -> ai_risk_exposure, capital_dependency_count, contract_terms_count, customer_concentration, cyber_business_risk, cybersecurity_posture, distribution_channels_count, employee_count, macro_sensitivity_count, regulatory_dependency_count, supplier_concentration, technology_dependency_count
**Gap**: None -- question is being answered with evaluative checks

### 1.3.9: Is there ESG/greenwashing risk?
**Status**: ANSWERED
**Data path**: SEC_10K -> ai_risk_exposure, capital_dependency_count, contract_terms_count, customer_concentration, cyber_business_risk, cybersecurity_posture, distribution_channels_count, employee_count, macro_sensitivity_count, regulatory_dependency_count, supplier_concentration, technology_dependency_count
**Gap**: None -- question is being answered with evaluative checks

## 1.4 Corporate Structure & Complexity
*How is this company organized?*

**Subsection Assessment: NO CHECKS** (0 checks)

**Checks:** None mapped

### 1.4.1: How many subsidiaries and legal entities exist?
**Status**: NO CHECKS
**Gap**: No checks mapped to this question -- need to create checks or map existing ones

### 1.4.2: Are there VIEs, SPEs, or off-balance-sheet structures?
**Status**: NO CHECKS
**Gap**: No checks mapped to this question -- need to create checks or map existing ones

### 1.4.3: Are there related-party transactions or intercompany complexity?
**Status**: NO CHECKS
**Gap**: No checks mapped to this question -- need to create checks or map existing ones

## 1.5 Geographic Footprint
*Where does this company operate and what jurisdictional risks exist?*

**Subsection Assessment: DISPLAY ONLY** (1 checks)

**Checks:**
- `BIZ.MODEL.revenue_geo`: **INFO** [MANAGEMENT_DISPLAY] = `Ireland, Japan, Canada, India, Mexico, Singapore, Thailand, ...`
  - Evidence: Management display: Ireland, Japan, Canada, India, Mexico, Singapore, Thailand, Vietnam, Delaware, China

### 1.5.1: Where does the company operate (countries/regions)?
**Status**: DISPLAY ONLY
**Data path**: SEC_10K -> revenue_geographic_mix
**Gap**: Only MANAGEMENT_DISPLAY checks present -- shows data but no risk evaluation. Consider adding evaluative thresholds.

### 1.5.2: What jurisdiction-specific risks apply (FCPA, GDPR, sanctions, export controls)?
**Status**: DISPLAY ONLY
**Data path**: SEC_10K -> revenue_geographic_mix
**Gap**: Only MANAGEMENT_DISPLAY checks present -- shows data but no risk evaluation. Consider adding evaluative thresholds.

## 1.6 M&A & Corporate Transactions
*What deal activity has there been and what's pending?*

**Subsection Assessment: PARTIAL** (2 checks)

**Checks:**
- `FWRD.EVENT.ma_closing`: **INFO** = `0.0`
  - Evidence: Qualitative check: value=0
- `FWRD.WARN.contract_disputes`: **INFO** = `Not mentioned in 10-K filing`
  - Evidence: Qualitative check: value=Not mentioned in 10-K filing

### 1.6.1: Are there pending M&A transactions?
**Status**: PARTIAL
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 1.6.2: What is the 2-3 year acquisition history (deal sizes, rationale, integration)?
**Status**: PARTIAL
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 1.6.3: How much goodwill has accumulated and is there impairment risk?
**Status**: PARTIAL
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 1.6.4: What is the integration track record?
**Status**: PARTIAL
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 1.6.5: Has there been deal-related litigation?
**Status**: PARTIAL
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 1.6.6: Have there been divestitures, spin-offs, or capital markets transactions?
**Status**: PARTIAL
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

## 1.7 Competitive Position & Industry Dynamics
*How is this company positioned within its industry?*

**Subsection Assessment: DISPLAY ONLY** (11 checks)

**Checks:**
- `BIZ.COMP.barriers`: **INFO** [MANAGEMENT_DISPLAY] = `Not mentioned in 10-K filing`
  - Evidence: Management display: Not mentioned in 10-K filing
- `BIZ.COMP.barriers_entry`: **INFO** [MANAGEMENT_DISPLAY] = `Not mentioned in 10-K filing`
  - Evidence: Management display: Not mentioned in 10-K filing
- `BIZ.COMP.competitive_advantage`: **INFO** [MANAGEMENT_DISPLAY] = `TECH`
  - Evidence: Management display: TECH
- `BIZ.COMP.consolidation`: **INFO** [MANAGEMENT_DISPLAY] = `TECH`
  - Evidence: Management display: TECH
- `BIZ.COMP.headwinds`: **INFO** [MANAGEMENT_DISPLAY] = `Not mentioned in 10-K filing`
  - Evidence: Management display: Not mentioned in 10-K filing
- `BIZ.COMP.industry_growth`: **INFO** [MANAGEMENT_DISPLAY] = `TECH`
  - Evidence: Management display: TECH
- `BIZ.COMP.market_position`: **INFO** [MANAGEMENT_DISPLAY] = `TECH`
  - Evidence: Management display: TECH
- `BIZ.COMP.market_share`: **INFO** [MANAGEMENT_DISPLAY] = `TECH`
  - Evidence: Management display: TECH
- `BIZ.COMP.moat`: **INFO** [MANAGEMENT_DISPLAY] = `13 mention(s): ting the Company's products and infringing on...`
  - Evidence: Management display: 13 mention(s): ting the Company's products and infringing on its intellectual property. Apple Inc. |...
- `BIZ.COMP.peer_litigation`: **INFO** [MANAGEMENT_DISPLAY] = `0.0`
  - Evidence: Management display: 0
- `BIZ.COMP.threat_assessment`: **INFO** [MANAGEMENT_DISPLAY] = `TECH`
  - Evidence: Management display: TECH

### 1.7.1: What is the company's market position and competitive moat?
**Status**: DISPLAY ONLY
**Data path**: MARKET_PRICE, SCAC_SEARCH, SEC_10K -> active_sca_count, barriers_to_entry, competitive_moat, industry_headwinds, sector
**Gap**: Only MANAGEMENT_DISPLAY checks present -- shows data but no risk evaluation. Consider adding evaluative thresholds.

### 1.7.2: Who are the direct peers and how do they compare?
**Status**: DISPLAY ONLY
**Data path**: MARKET_PRICE, SCAC_SEARCH, SEC_10K -> active_sca_count, barriers_to_entry, competitive_moat, industry_headwinds, sector
**Gap**: Only MANAGEMENT_DISPLAY checks present -- shows data but no risk evaluation. Consider adding evaluative thresholds.

### 1.7.3: What is the peer litigation frequency (SCA contagion risk)?
**Status**: DISPLAY ONLY
**Data path**: MARKET_PRICE, SCAC_SEARCH, SEC_10K -> active_sca_count, barriers_to_entry, competitive_moat, industry_headwinds, sector
**Gap**: Only MANAGEMENT_DISPLAY checks present -- shows data but no risk evaluation. Consider adding evaluative thresholds.

### 1.7.4: What are the industry headwinds and tailwinds?
**Status**: DISPLAY ONLY
**Data path**: MARKET_PRICE, SCAC_SEARCH, SEC_10K -> active_sca_count, barriers_to_entry, competitive_moat, industry_headwinds, sector
**Gap**: Only MANAGEMENT_DISPLAY checks present -- shows data but no risk evaluation. Consider adding evaluative thresholds.

## 1.8 Macro & Industry Environment
*What external forces are creating risk?*

**Subsection Assessment: DISPLAY ONLY** (18 checks)

**Checks:**
- `BIZ.COMP.consolidation`: **INFO** [MANAGEMENT_DISPLAY] = `TECH`
  - Evidence: Management display: TECH
- `BIZ.COMP.headwinds`: **INFO** [MANAGEMENT_DISPLAY] = `Not mentioned in 10-K filing`
  - Evidence: Management display: Not mentioned in 10-K filing
- `BIZ.COMP.industry_growth`: **INFO** [MANAGEMENT_DISPLAY] = `TECH`
  - Evidence: Management display: TECH
- `FWRD.MACRO.climate_transition_risk`: **INFO** [MANAGEMENT_DISPLAY] = `2 mention(s): o earthquakes and other natural disasters. Glo...`
  - Evidence: Management display: 2 mention(s): o earthquakes and other natural disasters. Global climate change is resulting in certa...
- `FWRD.MACRO.commodity_impact`: **INFO** [MANAGEMENT_DISPLAY] = `Not mentioned in 10-K filing`
  - Evidence: Management display: Not mentioned in 10-K filing
- `FWRD.MACRO.disruptive_tech`: **INFO** [MANAGEMENT_DISPLAY] = `4 mention(s): vices are highly competitive and subject to ra...`
  - Evidence: Management display: 4 mention(s): vices are highly competitive and subject to rapid technological change, and the Compan...
- `FWRD.MACRO.fx_exposure`: **INFO** [MANAGEMENT_DISPLAY] = `3 mention(s): oyment; anticorruption; import, export and tra...`
  - Evidence: Management display: 3 mention(s): oyment; anticorruption; import, export and trade; foreign exchange controls and cash r...
- `FWRD.MACRO.geopolitical_exposure`: **INFO** [MANAGEMENT_DISPLAY] = `13 mention(s): l events, trade and other international dispu...`
  - Evidence: Management display: 13 mention(s): l events, trade and other international disputes, geopolitical tensions, conflict, te...
- `FWRD.MACRO.industry_consolidation`: **INFO** [MANAGEMENT_DISPLAY] = `5 mention(s): gence, which can involve, among other things, ...`
  - Evidence: Management display: 5 mention(s): gence, which can involve, among other things, the acquisition and use of copyrighted m...
- `FWRD.MACRO.inflation_impact`: **INFO** [MANAGEMENT_DISPLAY] = `3 mention(s): ding slow growth or recession, high unemployme...`
  - Evidence: Management display: 3 mention(s): ding slow growth or recession, high unemployment, inflation, tighter credit, higher in...
- `FWRD.MACRO.interest_rate_sensitivity`: **INFO** [MANAGEMENT_DISPLAY] = `Not mentioned in 10-K filing`
  - Evidence: Management display: Not mentioned in 10-K filing
- `FWRD.MACRO.labor_market`: **INFO** [MANAGEMENT_DISPLAY] = `Not mentioned in 10-K filing`
  - Evidence: Management display: Not mentioned in 10-K filing
- `FWRD.MACRO.legislative_risk`: **INFO** [MANAGEMENT_DISPLAY] = `Not mentioned in 10-K filing`
  - Evidence: Management display: Not mentioned in 10-K filing
- `FWRD.MACRO.peer_issues`: **INFO** [MANAGEMENT_DISPLAY] = `3.0`
  - Evidence: Management display: 3
- `FWRD.MACRO.regulatory_changes`: **INFO** [MANAGEMENT_DISPLAY] = `1 mention(s): cal considerations relating to such technologi...`
  - Evidence: Management display: 1 mention(s): cal considerations relating to such technologies. Regulatory changes and other actions...
- `FWRD.MACRO.sector_performance`: **INFO** [MANAGEMENT_DISPLAY] = `5.03`
  - Evidence: Management display: 5.03
- `FWRD.MACRO.supply_chain_disruption`: **INFO** [MANAGEMENT_DISPLAY] = `1 mention(s): e Company remains subject to significant risks...`
  - Evidence: Management display: 1 mention(s): e Company remains subject to significant risks of supply shortages and price increases...
- `FWRD.MACRO.trade_policy`: **INFO** [MANAGEMENT_DISPLAY] = `10 mention(s): U.S. Restrictions on international trade, suc...`
  - Evidence: Management display: 10 mention(s): U.S. Restrictions on international trade, such as tariffs and other controls on impor...

### 1.8.1: How is the sector performing overall and are peers experiencing similar issues?
**Status**: DISPLAY ONLY
**Data path**: SEC_10K -> industry_headwinds, sector
**Gap**: Only MANAGEMENT_DISPLAY checks present -- shows data but no risk evaluation. Consider adding evaluative thresholds.

### 1.8.2: Is the industry consolidating or facing disruptive technology threats?
**Status**: DISPLAY ONLY
**Data path**: SEC_10K -> industry_headwinds, sector
**Gap**: Only MANAGEMENT_DISPLAY checks present -- shows data but no risk evaluation. Consider adding evaluative thresholds.

### 1.8.3: What macro factors materially affect this company (rates, FX, commodities, trade, labor)?
**Status**: DISPLAY ONLY
**Data path**: SEC_10K -> industry_headwinds, sector
**Gap**: Only MANAGEMENT_DISPLAY checks present -- shows data but no risk evaluation. Consider adding evaluative thresholds.

### 1.8.4: Are there regulatory, legislative, or geopolitical changes creating sector risk?
**Status**: DISPLAY ONLY
**Data path**: SEC_10K -> industry_headwinds, sector
**Gap**: Only MANAGEMENT_DISPLAY checks present -- shows data but no risk evaluation. Consider adding evaluative thresholds.

## 1.9 Employee & Workforce Signals
*What are employees telling us about the company's health?*

**Subsection Assessment: PARTIAL** (8 checks)

**Checks:**
- `FWRD.WARN.blind_posts`: **SKIPPED** = `N/A`
- `FWRD.WARN.compliance_hiring`: **INFO** = `1 mention(s): s, financial condition and stock price. Legal ...`
  - Evidence: Qualitative check: value=1 mention(s): s, financial condition and stock price. Legal and Regulatory Compliance Risks The...
- `FWRD.WARN.glassdoor_sentiment`: **SKIPPED** = `N/A`
- `FWRD.WARN.indeed_reviews`: **SKIPPED** = `N/A`
- `FWRD.WARN.job_posting_patterns`: **INFO** = `1 mention(s): s, financial condition and stock price. Legal ...`
  - Evidence: Qualitative check: value=1 mention(s): s, financial condition and stock price. Legal and Regulatory Compliance Risks The...
- `FWRD.WARN.legal_hiring`: **INFO** = `10 mention(s): d be adversely impacted by unfavorable result...`
  - Evidence: Qualitative check: value=10 mention(s): d be adversely impacted by unfavorable results of legal proceedings or governmen...
- `FWRD.WARN.linkedin_departures`: **SKIPPED** = `N/A`
- `FWRD.WARN.linkedin_headcount`: **SKIPPED** = `N/A`

### 1.9.1: What do employee review platforms indicate (Glassdoor, Indeed, Blind)?
**Status**: PARTIAL
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 1.9.2: Are there unusual hiring patterns (compliance/legal hiring surge)?
**Status**: PARTIAL
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 1.9.3: Are there LinkedIn headcount or departure trends?
**Status**: PARTIAL
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 1.9.4: Are there WARN Act or mass layoff signals?
**Status**: PARTIAL
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 1.9.5: What do department-level departures show? (Accounting/legal departures = stronger fraud signal)
**Status**: PARTIAL
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 1.9.6: What is the CEO approval rating trend? (Glassdoor CEO approval drop >20% = red flag)
**Status**: PARTIAL
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

## 1.10 Customer & Product Signals
*What are customers and the market experiencing?*

**Subsection Assessment: PARTIAL** (11 checks)

**Checks:**
- `FWRD.WARN.app_ratings`: **SKIPPED** = `N/A`
- `FWRD.WARN.cfpb_complaints`: **SKIPPED** = `N/A`
- `FWRD.WARN.customer_churn_signals`: **INFO** = `Not mentioned in 10-K filing`
  - Evidence: Qualitative check: value=Not mentioned in 10-K filing
- `FWRD.WARN.fda_medwatch`: **SKIPPED** = `N/A`
- `FWRD.WARN.g2_reviews`: **SKIPPED** = `N/A`
- `FWRD.WARN.journalism_activity`: **SKIPPED** = `N/A`
- `FWRD.WARN.nhtsa_complaints`: **SKIPPED** = `N/A`
- `FWRD.WARN.partner_stability`: **INFO** = `Not mentioned in 10-K filing`
  - Evidence: Qualitative check: value=Not mentioned in 10-K filing
- `FWRD.WARN.social_sentiment`: **SKIPPED** = `N/A`
- `FWRD.WARN.trustpilot_trend`: **SKIPPED** = `N/A`
- `FWRD.WARN.vendor_payment_delays`: **INFO** = `Not mentioned in 10-K filing`
  - Evidence: Qualitative check: value=Not mentioned in 10-K filing

### 1.10.1: Are there customer complaint trends (CFPB, app ratings, Trustpilot)?
**Status**: PARTIAL
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 1.10.2: Are there product quality signals (FDA MedWatch, NHTSA complaints)?
**Status**: PARTIAL
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 1.10.3: Are there customer churn or partner instability signals?
**Status**: PARTIAL
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 1.10.4: Are there vendor payment or supply chain stress signals?
**Status**: PARTIAL
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 1.10.5: What do web traffic and app download trends show?
**Status**: PARTIAL
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 1.10.6: What does scientific/academic community monitoring reveal? (PubPeer, Retraction Watch, KOL sentiment -- biotech/pharma)
**Status**: PARTIAL
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

## 1.11 Risk Calendar & Upcoming Catalysts
*What events are coming in the next policy year?*

**Subsection Assessment: ANSWERED** (17 checks)

**Checks:**
- `FWRD.EVENT.catalyst_dates`: **INFO** [MANAGEMENT_DISPLAY] = `0.0`
  - Evidence: Management display: 0
- `FWRD.EVENT.contract_renewal`: **INFO** = `Not mentioned in 10-K filing`
  - Evidence: Qualitative check: value=Not mentioned in 10-K filing
- `FWRD.EVENT.covenant_test`: **INFO** = `{'maturity_schedule': {}, 'interest_rates': {'fixed_rates': ...`
  - Evidence: Qualitative check: value={'maturity_schedule': {}, 'interest_rates': {'fixed_rates': [0.03, 4.0, 4.07, 4.19, 4.75, 4.83,...
- `FWRD.EVENT.customer_retention`: **INFO** = `Not mentioned in 10-K filing`
  - Evidence: Qualitative check: value=Not mentioned in 10-K filing
- `FWRD.EVENT.debt_maturity`: **INFO** = `{'maturity_schedule': {}, 'interest_rates': {'fixed_rates': ...`
  - Evidence: Qualitative check: value={'maturity_schedule': {}, 'interest_rates': {'fixed_rates': [0.03, 4.0, 4.07, 4.19, 4.75, 4.83,...
- `FWRD.EVENT.earnings_calendar`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds
- `FWRD.EVENT.employee_retention`: **INFO** = `3 mention(s): ailability of highly skilled employees, includ...`
  - Evidence: Qualitative check: value=3 mention(s): ailability of highly skilled employees, including key personnel, and the Company'...
- `FWRD.EVENT.guidance_risk`: **INFO** = `0.0`
  - Evidence: Qualitative check: value=0
- `FWRD.EVENT.integration`: **INFO** = `0.0`
  - Evidence: Qualitative check: value=0
- `FWRD.EVENT.litigation_milestone`: **INFO** = `0.0`
  - Evidence: Qualitative check: value=0
- `FWRD.EVENT.lockup_expiry`: **NOT_RUN** [MANAGEMENT_DISPLAY] = `N/A`
  - Evidence: execution_mode=SECTOR_CONDITIONAL
- `FWRD.EVENT.ma_closing`: **INFO** = `0.0`
  - Evidence: Qualitative check: value=0
- `FWRD.EVENT.proxy_deadline`: **INFO** [MANAGEMENT_DISPLAY] = `92.0`
  - Evidence: Management display: 92.0
- `FWRD.EVENT.regulatory_decision`: **INFO** = `10 mention(s): lectual property rights. Regulatory requireme...`
  - Evidence: Qualitative check: value=10 mention(s): lectual property rights. Regulatory requirements, government investigations and ...
- `FWRD.EVENT.shareholder_mtg`: **INFO** [MANAGEMENT_DISPLAY] = `92.0`
  - Evidence: Management display: 92.0
- `FWRD.EVENT.synergy`: **INFO** = `0.0`
  - Evidence: Qualitative check: value=0
- `FWRD.EVENT.warrant_expiry`: **NOT_RUN** [MANAGEMENT_DISPLAY] = `N/A`
  - Evidence: execution_mode=SECTOR_CONDITIONAL

### 1.11.1: When is the next earnings report and what's the miss risk?
**Status**: ANSWERED
**Gap**: None -- question is being answered with evaluative checks

### 1.11.2: Are there pending regulatory decisions (FDA, FCC, etc.)?
**Status**: ANSWERED
**Gap**: None -- question is being answered with evaluative checks

### 1.11.3: Are there M&A closings or shareholder votes?
**Status**: ANSWERED
**Gap**: None -- question is being answered with evaluative checks

### 1.11.4: Are there debt maturities or covenant tests in the next 12 months?
**Status**: ANSWERED
**Gap**: None -- question is being answered with evaluative checks

### 1.11.5: Are there lockup expirations or warrant expiry?
**Status**: ANSWERED
**Gap**: None -- question is being answered with evaluative checks

### 1.11.6: Are there contract renewals or customer retention milestones?
**Status**: ANSWERED
**Gap**: None -- question is being answered with evaluative checks

### 1.11.7: Are there litigation milestones (trial dates, settlement deadlines)?
**Status**: ANSWERED
**Gap**: None -- question is being answered with evaluative checks

### 1.11.8: Are there industry-specific catalysts (PDUFA dates, patent cliffs)?
**Status**: ANSWERED
**Gap**: None -- question is being answered with evaluative checks

---

# 2. MARKET

## 2.1 Stock Price Performance
*How has the stock performed?*

**Subsection Assessment: ANSWERED** (8 checks)

**Checks:**
- `NLP.MDA.tone_absolute`: **INFO** [MANAGEMENT_DISPLAY] = `present`
  - Evidence: Management display: present
- `STOCK.PRICE.attribution`: **CLEAR** (clear) = `-11.38`
  - Evidence: Value -11.38 within thresholds
- `STOCK.PRICE.chart_comparison`: **CLEAR** (clear) = `-11.38`
  - Evidence: Value -11.38 within thresholds
- `STOCK.PRICE.delisting_risk`: **CLEAR** (clear) = `255.78`
  - Evidence: Value 255.78 within thresholds
- `STOCK.PRICE.peer_relative`: **CLEAR** (clear) = `5.03`
  - Evidence: Value 5.03 within thresholds
- `STOCK.PRICE.position`: **CLEAR** (clear) = `-11.38`
  - Evidence: Value -11.38 within thresholds
- `STOCK.PRICE.returns_multi_horizon`: **INFO** = `5.03`
  - Evidence: multi_period check: 5.03
- `STOCK.PRICE.technical`: **CLEAR** (clear) = `21.6137`
  - Evidence: Value 21.6137 within thresholds

### 2.1.1: What's the stock's current position relative to its 52-week range?
**Status**: ANSWERED
**Data path**: MARKET_PRICE -> current_price, decline_from_high, returns_1y, volatility_90d
**Gap**: None -- question is being answered with evaluative checks

### 2.1.2: What is the stock's volatility profile and how does it compare to sector/peers? (Beta, 90-day vol, calm vs wild characterization)
**Status**: ANSWERED
**Data path**: MARKET_PRICE -> current_price, decline_from_high, returns_1y, volatility_90d
**Gap**: None -- question is being answered with evaluative checks

### 2.1.3: How does performance compare to the sector and peers?
**Status**: ANSWERED
**Data path**: MARKET_PRICE -> current_price, decline_from_high, returns_1y, volatility_90d
**Gap**: None -- question is being answered with evaluative checks

### 2.1.4: Is there delisting risk?
**Status**: ANSWERED
**Data path**: MARKET_PRICE -> current_price, decline_from_high, returns_1y, volatility_90d
**Gap**: None -- question is being answered with evaluative checks

### 2.1.5: Does the MD&A exhibit "Abnormal Positive Tone" relative to quantitative financial reality?
**Status**: ANSWERED
**Data path**: MARKET_PRICE -> current_price, decline_from_high, returns_1y, volatility_90d
**Gap**: None -- question is being answered with evaluative checks

## 2.2 Stock Drop Events
*Have there been significant drops that could trigger litigation?*

**Subsection Assessment: ANSWERED** (4 checks)

**Checks:**
- `STOCK.PATTERN.event_collapse`: **INFO** [INFERENCE_PATTERN] = `2.0`
  - Evidence: Single signal only (single_day_drops_count=2). Insufficient data for multi-signal pattern detection.
- `STOCK.PRICE.recent_drop_alert`: **CLEAR** (clear) = `-11.38`
  - Evidence: Value -11.38 within thresholds
- `STOCK.PRICE.recovery`: **CLEAR** (clear) = `5.03`
  - Evidence: Value 5.03 within thresholds
- `STOCK.PRICE.single_day_events`: **CLEAR** (clear) = `2.0`
  - Evidence: Value 2.0 within thresholds

### 2.2.1: Have there been single-day drops >=5% in the past 18 months?
**Status**: ANSWERED
**Data path**: MARKET_PRICE -> decline_from_high, returns_1y, single_day_drops_count
**Gap**: None -- question is being answered with evaluative checks

### 2.2.2: Have there been multi-day decline events >=10%?
**Status**: ANSWERED
**Data path**: MARKET_PRICE -> decline_from_high, returns_1y, single_day_drops_count
**Gap**: None -- question is being answered with evaluative checks

### 2.2.3: Were significant drops preceded by "Corrective Disclosures" (restatements, guidance withdrawals, auditor changes) that establish loss causation?
**Status**: ANSWERED
**Data path**: MARKET_PRICE -> decline_from_high, returns_1y, single_day_drops_count
**Gap**: None -- question is being answered with evaluative checks

### 2.2.4: Has the stock recovered from significant drops, or is there a sustained unrecovered decline in the past 18 months?
**Status**: ANSWERED
**Data path**: MARKET_PRICE -> decline_from_high, returns_1y, single_day_drops_count
**Gap**: None -- question is being answered with evaluative checks

## 2.3 Volatility & Trading Patterns
*What does trading behavior signal?*

**Subsection Assessment: PARTIAL** (6 checks)

**Checks:**
- `STOCK.PATTERN.cascade`: **INFO** [INFERENCE_PATTERN] = `-11.38`
  - Evidence: Single signal only (decline_from_high=-11.38). Insufficient data for multi-signal pattern detection.
- `STOCK.PATTERN.death_spiral`: **INFO** [INFERENCE_PATTERN] = `-11.38`
  - Evidence: Single signal only (decline_from_high=-11.38). Insufficient data for multi-signal pattern detection.
- `STOCK.PATTERN.peer_divergence`: **INFO** [INFERENCE_PATTERN] = `5.03`
  - Evidence: Single signal only (returns_1y=5.03). Insufficient data for multi-signal pattern detection.
- `STOCK.TRADE.liquidity`: **INFO** [MANAGEMENT_DISPLAY] = `255.78`
  - Evidence: Management display: 255.78
- `STOCK.TRADE.options`: **INFO** [MANAGEMENT_DISPLAY] = `7.0`
  - Evidence: Management display: 7
- `STOCK.TRADE.volume_patterns`: **INFO** [MANAGEMENT_DISPLAY] = `7.0`
  - Evidence: Management display: 7

### 2.3.1: What's the 90-day volatility and how does it compare to peers?
**Status**: PARTIAL
**Data path**: MARKET_PRICE -> adverse_event_count, current_price, decline_from_high, returns_1y
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 2.3.2: What's the beta?
**Status**: PARTIAL
**Data path**: MARKET_PRICE -> adverse_event_count, current_price, decline_from_high, returns_1y
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 2.3.3: Is there adequate trading liquidity?
**Status**: PARTIAL
**Data path**: MARKET_PRICE -> adverse_event_count, current_price, decline_from_high, returns_1y
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 2.3.4: Are there unusual volume or options patterns?
**Status**: PARTIAL
**Data path**: MARKET_PRICE -> adverse_event_count, current_price, decline_from_high, returns_1y
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

## 2.4 Short Interest & Bearish Signals
*Are sophisticated investors betting against this company?*

**Subsection Assessment: ANSWERED** (4 checks)

**Checks:**
- `STOCK.PATTERN.short_attack`: **INFO** [INFERENCE_PATTERN] = `0.8`
  - Evidence: Single signal only (short_interest_pct=0.8). Insufficient data for multi-signal pattern detection.
- `STOCK.SHORT.position`: **CLEAR** (clear) = `0.8`
  - Evidence: Value 0.8 within thresholds
- `STOCK.SHORT.report`: **INFO** = `0.8`
  - Evidence: Qualitative check: value=0.8
- `STOCK.SHORT.trend`: **CLEAR** (clear) = `2.36`
  - Evidence: Value 2.36 within thresholds

### 2.4.1: What's the short interest as % of float and what's the trend over the past 6-12 months?
**Status**: ANSWERED
**Data path**: MARKET_SHORT -> short_interest_pct, short_interest_ratio
**Gap**: None -- question is being answered with evaluative checks

### 2.4.2: Have there been activist short seller reports?
**Status**: ANSWERED
**Data path**: MARKET_SHORT -> short_interest_pct, short_interest_ratio
**Gap**: None -- question is being answered with evaluative checks

## 2.5 Ownership Structure
*Who owns the stock?*

**Subsection Assessment: ANSWERED** (4 checks)

**Checks:**
- `STOCK.LIT.existing_action`: **CLEAR** (clear) = `0.0`
  - Evidence: Boolean check: No SCA history
- `STOCK.OWN.activist`: **INFO** [MANAGEMENT_DISPLAY] = `0.0`
  - Evidence: Management display: False
- `STOCK.OWN.concentration`: **INFO** [MANAGEMENT_DISPLAY] = `65.483004`
  - Evidence: Management display: 65.483004
- `STOCK.OWN.structure`: **INFO** = `65.483004`
  - Evidence: info check: 65.483004

### 2.5.1: What's the institutional vs insider vs retail ownership breakdown?
**Status**: ANSWERED
**Data path**: SCAC_SEARCH, SEC_DEF14A -> active_sca_count, activist_present, institutional_pct
**Gap**: None -- question is being answered with evaluative checks

### 2.5.2: Who are the largest holders and what's the concentration?
**Status**: ANSWERED
**Data path**: SCAC_SEARCH, SEC_DEF14A -> active_sca_count, activist_present, institutional_pct
**Gap**: None -- question is being answered with evaluative checks

### 2.5.3: What are the institutional ownership trends over the past 6-12 months?
**Status**: ANSWERED
**Data path**: SCAC_SEARCH, SEC_DEF14A -> active_sca_count, activist_present, institutional_pct
**Gap**: None -- question is being answered with evaluative checks

### 2.5.4: Are there capital markets transactions creating liability windows? (Secondary offerings, ATM programs, convertible issuance)
**Status**: ANSWERED
**Data path**: SCAC_SEARCH, SEC_DEF14A -> active_sca_count, activist_present, institutional_pct
**Gap**: None -- question is being answered with evaluative checks

## 2.6 Analyst Coverage & Sentiment
*What do professional analysts think?*

**Subsection Assessment: DISPLAY ONLY** (2 checks)

**Checks:**
- `STOCK.ANALYST.coverage`: **INFO** [MANAGEMENT_DISPLAY] = `0.9167`
  - Evidence: Management display: 0.9167
- `STOCK.ANALYST.momentum`: **INFO** [MANAGEMENT_DISPLAY] = `0.9167`
  - Evidence: Management display: 0.9167

### 2.6.1: How many analysts cover this stock?
**Status**: DISPLAY ONLY
**Data path**: MARKET_PRICE -> beat_rate
**Gap**: Only MANAGEMENT_DISPLAY checks present -- shows data but no risk evaluation. Consider adding evaluative thresholds.

### 2.6.2: What's the consensus rating and recent changes?
**Status**: DISPLAY ONLY
**Data path**: MARKET_PRICE -> beat_rate
**Gap**: Only MANAGEMENT_DISPLAY checks present -- shows data but no risk evaluation. Consider adding evaluative thresholds.

### 2.6.3: What's the price target relative to current price?
**Status**: DISPLAY ONLY
**Data path**: MARKET_PRICE -> beat_rate
**Gap**: Only MANAGEMENT_DISPLAY checks present -- shows data but no risk evaluation. Consider adding evaluative thresholds.

## 2.7 Valuation Metrics
*Is the stock priced appropriately?*

**Subsection Assessment: ANSWERED** (4 checks)

**Checks:**
- `STOCK.VALUATION.ev_ebitda`: **SKIPPED** = `N/A`
- `STOCK.VALUATION.pe_ratio`: **SKIPPED** = `N/A`
- `STOCK.VALUATION.peg_ratio`: **SKIPPED** = `N/A`
- `STOCK.VALUATION.premium_discount`: **CLEAR** (clear) = `5.03`
  - Evidence: Value 5.03 within thresholds

### 2.7.1: What are the key valuation ratios (P/E, EV/EBITDA, PEG)?
**Status**: ANSWERED
**Data path**: MARKET_PRICE -> ev_ebitda, pe_ratio, peg_ratio, returns_1y
**Gap**: None -- question is being answered with evaluative checks

### 2.7.2: How does valuation compare to peers?
**Status**: ANSWERED
**Data path**: MARKET_PRICE -> ev_ebitda, pe_ratio, peg_ratio, returns_1y
**Gap**: None -- question is being answered with evaluative checks

## 2.8 Insider Trading Activity
*Are insiders buying or selling, and is the timing suspicious?*

**Subsection Assessment: ANSWERED** (16 checks)

**Checks:**
- `EXEC.INSIDER.ceo_net_selling`: **TRIGGERED** (red) = `100.0`
  - Evidence: Value 100.0 exceeds red threshold 80.0
- `EXEC.INSIDER.cfo_net_selling`: **TRIGGERED** (red) = `100.0`
  - Evidence: Value 100.0 exceeds red threshold 80.0
- `EXEC.INSIDER.cluster_selling`: **INFO** [INFERENCE_PATTERN] = `1.0`
  - Evidence: Single signal only (value=True). Insufficient data for multi-signal pattern detection.
- `EXEC.INSIDER.non_10b51`: **INFO** [INFERENCE_PATTERN] = `6.7`
  - Evidence: Single signal only (value=6.7). Insufficient data for multi-signal pattern detection.
- `GOV.INSIDER.10b5_plans`: **SKIPPED** [MANAGEMENT_DISPLAY] = `N/A`
- `GOV.INSIDER.cluster_sales`: **SKIPPED** = `N/A`
- `GOV.INSIDER.executive_sales`: **CLEAR** (clear) = `1.7070001000000001`
  - Evidence: Value 1.7070001000000001 within thresholds
- `GOV.INSIDER.form4_filings`: **INFO** [MANAGEMENT_DISPLAY] = `1.7070001000000001`
  - Evidence: Management display: 1.7070001000000001
- `GOV.INSIDER.net_selling`: **CLEAR** (clear) = `1.7070001000000001`
  - Evidence: Value 1.7070001000000001 within thresholds
- `GOV.INSIDER.ownership_pct`: **CLEAR** (clear) = `1.7070001000000001`
  - Evidence: Value 1.7070001000000001 within thresholds
- `GOV.INSIDER.plan_adoption`: **SKIPPED** = `N/A`
- `GOV.INSIDER.unusual_timing`: **SKIPPED** = `N/A`
- `STOCK.INSIDER.cluster_timing`: **TRIGGERED** (red) = `1.0`
  - Evidence: Value 1.0 exceeds red threshold 0.0
- `STOCK.INSIDER.notable_activity`: **TRIGGERED** (red) = `100.0`
  - Evidence: Value 100.0 exceeds red threshold 25.0
- `STOCK.INSIDER.summary`: **INFO** = `NET_SELLING`
  - Evidence: Qualitative check: value=NET_SELLING
- `STOCK.PATTERN.informed_trading`: **NOT_RUN** [INFERENCE_PATTERN] = `N/A`
  - Evidence: execution_mode=FALLBACK_ONLY

### 2.8.1: What's the net insider trading direction?
**Status**: ANSWERED
**Data path**: SEC_FORM4 -> ceo_cfo_selling_pct, cluster_selling, insider_cluster_count, insider_net_activity, insider_pct, insider_unusual_timing, plan_adoption_timing, trading_plans_10b51
**Gap**: None -- question is being answered with evaluative checks

### 2.8.2: Are CEO/CFO selling significant holdings?
**Status**: ANSWERED
**Data path**: SEC_FORM4 -> ceo_cfo_selling_pct, cluster_selling, insider_cluster_count, insider_net_activity, insider_pct, insider_unusual_timing, plan_adoption_timing, trading_plans_10b51
**Gap**: None -- question is being answered with evaluative checks

### 2.8.3: What percentage of transactions use 10b5-1 plans?
**Status**: ANSWERED
**Data path**: SEC_FORM4 -> ceo_cfo_selling_pct, cluster_selling, insider_cluster_count, insider_net_activity, insider_pct, insider_unusual_timing, plan_adoption_timing, trading_plans_10b51
**Gap**: None -- question is being answered with evaluative checks

### 2.8.4: Is there cluster selling (multiple insiders simultaneously)?
**Status**: ANSWERED
**Data path**: SEC_FORM4 -> ceo_cfo_selling_pct, cluster_selling, insider_cluster_count, insider_net_activity, insider_pct, insider_unusual_timing, plan_adoption_timing, trading_plans_10b51
**Gap**: None -- question is being answered with evaluative checks

### 2.8.5: Is insider trading timing suspicious relative to material events?
**Status**: ANSWERED
**Data path**: SEC_FORM4 -> ceo_cfo_selling_pct, cluster_selling, insider_cluster_count, insider_net_activity, insider_pct, insider_unusual_timing, plan_adoption_timing, trading_plans_10b51
**Gap**: None -- question is being answered with evaluative checks

### 2.8.6: Do executives pledge company shares as loan collateral?
**Status**: ANSWERED
**Data path**: SEC_FORM4 -> ceo_cfo_selling_pct, cluster_selling, insider_cluster_count, insider_net_activity, insider_pct, insider_unusual_timing, plan_adoption_timing, trading_plans_10b51
**Gap**: None -- question is being answered with evaluative checks

### 2.8.7: Are there Form 4 compliance issues? (Late Section 16 filings, gift transactions timed before declines)
**Status**: ANSWERED
**Data path**: SEC_FORM4 -> ceo_cfo_selling_pct, cluster_selling, insider_cluster_count, insider_net_activity, insider_pct, insider_unusual_timing, plan_adoption_timing, trading_plans_10b51
**Gap**: None -- question is being answered with evaluative checks

---

# 3. FINANCIAL

## 3.1 Liquidity & Solvency
*Can the company meet its near-term obligations? (Sector-calibrated thresholds apply)*

**Subsection Assessment: ANSWERED** (5 checks)

**Checks:**
- `FIN.LIQ.cash_burn`: **INFO** = `Profitable (OCF positive)`
  - Evidence: Qualitative check: value=Profitable (OCF positive)
- `FIN.LIQ.efficiency`: **TRIGGERED** (yellow) = `0.217`
  - Evidence: Value 0.217 below yellow threshold 0.5
- `FIN.LIQ.position`: **TRIGGERED** (red) = `0.8933`
  - Evidence: Value 0.8933 below red threshold 6.0
- `FIN.LIQ.trend`: **INFO** = `0.8933`
  - Evidence: Qualitative check: value=0.8933
- `FIN.LIQ.working_capital`: **TRIGGERED** (red) = `0.8933`
  - Evidence: Value 0.8933 below red threshold 1.0

### 3.1.1: Does the company have adequate liquidity (current ratio, quick ratio, cash ratio)?
**Status**: ANSWERED
**Data path**: SEC_10Q -> cash_burn_months, cash_ratio, current_ratio
**Gap**: None -- question is being answered with evaluative checks

### 3.1.2: What is the cash runway -- how many months before cash runs out?
**Status**: ANSWERED
**Data path**: SEC_10Q -> cash_burn_months, cash_ratio, current_ratio
**Gap**: None -- question is being answered with evaluative checks

### 3.1.3: Is there a going concern opinion from the auditor?
**Status**: ANSWERED
**Data path**: SEC_10Q -> cash_burn_months, cash_ratio, current_ratio
**Gap**: None -- question is being answered with evaluative checks

### 3.1.4: How has working capital trended over the past 3 years?
**Status**: ANSWERED
**Data path**: SEC_10Q -> cash_burn_months, cash_ratio, current_ratio
**Gap**: None -- question is being answered with evaluative checks

## 3.2 Leverage & Debt Structure
*How much debt does the company carry, and can they service it? (Sector-calibrated thresholds apply)*

**Subsection Assessment: ANSWERED** (5 checks)

**Checks:**
- `FIN.DEBT.covenants`: **INFO** = `{'maturity_schedule': {}, 'interest_rates': {'fixed_rates': ...`
  - Evidence: Qualitative check: value={'maturity_schedule': {}, 'interest_rates': {'fixed_rates': [0.03, 4.0, 4.07, 4.19, 4.75, 4.83,...
- `FIN.DEBT.coverage`: **CLEAR** (clear) = `33.8291`
  - Evidence: Value 33.8291 within thresholds
- `FIN.DEBT.credit_rating`: **NOT_RUN** = `N/A`
  - Evidence: execution_mode=FALLBACK_ONLY
- `FIN.DEBT.maturity`: **INFO** = `10 fixed-rate tranches, floating-rate debt present`
  - Evidence: Qualitative check: value=10 fixed-rate tranches, floating-rate debt present
- `FIN.DEBT.structure`: **CLEAR** (clear) = `0.6265`
  - Evidence: Value 0.6265 within thresholds

### 3.2.1: How leveraged is the company relative to earnings capacity (D/E, Debt/EBITDA)?
**Status**: ANSWERED
**Data path**: SEC_10K, SEC_10Q -> debt_structure, debt_to_ebitda, interest_coverage, refinancing_risk
**Gap**: None -- question is being answered with evaluative checks

### 3.2.2: Can the company service its debt (interest coverage)?
**Status**: ANSWERED
**Data path**: SEC_10K, SEC_10Q -> debt_structure, debt_to_ebitda, interest_coverage, refinancing_risk
**Gap**: None -- question is being answered with evaluative checks

### 3.2.3: When does significant debt mature and is refinancing at risk?
**Status**: ANSWERED
**Data path**: SEC_10K, SEC_10Q -> debt_structure, debt_to_ebitda, interest_coverage, refinancing_risk
**Gap**: None -- question is being answered with evaluative checks

### 3.2.4: Are there covenant compliance risks?
**Status**: ANSWERED
**Data path**: SEC_10K, SEC_10Q -> debt_structure, debt_to_ebitda, interest_coverage, refinancing_risk
**Gap**: None -- question is being answered with evaluative checks

### 3.2.5: What is the credit rating and recent trajectory?
**Status**: ANSWERED
**Data path**: SEC_10K, SEC_10Q -> debt_structure, debt_to_ebitda, interest_coverage, refinancing_risk
**Gap**: None -- question is being answered with evaluative checks

### 3.2.6: What off-balance-sheet obligations exist (operating leases, purchase commitments, guarantees)?
**Status**: ANSWERED
**Data path**: SEC_10K, SEC_10Q -> debt_structure, debt_to_ebitda, interest_coverage, refinancing_risk
**Gap**: None -- question is being answered with evaluative checks

## 3.3 Profitability & Growth
*Is the business economically viable and growing?*

**Subsection Assessment: ANSWERED** (10 checks)

**Checks:**
- `FIN.PROFIT.earnings`: **INFO** = `0.9953`
  - Evidence: Qualitative check: value=0.9953
- `FIN.PROFIT.margins`: **CLEAR** (clear) = `0.0015`
  - Evidence: Value 0.0015 within thresholds
- `FIN.PROFIT.revenue`: **INFO** = `Revenue is growing at 6.4% year-over-year. Liquidity is conc...`
  - Evidence: Qualitative check: value=Revenue is growing at 6.4% year-over-year. Liquidity is concerning with a current ratio of 0.89...
- `FIN.PROFIT.segment`: **INFO** = `Revenue is growing at 6.4% year-over-year. Liquidity is conc...`
  - Evidence: info check: Revenue is growing at 6.4% year-over-year. Liquidity is concerning with a current ratio of 0.89, below the 1...
- `FIN.PROFIT.trend`: **INFO** = `Revenue is growing at 6.4% year-over-year. Liquidity is conc...`
  - Evidence: Qualitative check: value=Revenue is growing at 6.4% year-over-year. Liquidity is concerning with a current ratio of 0.89...
- `FIN.TEMPORAL.cash_flow_deterioration`: **INFO** = `cash_flow_deterioration`
  - Evidence: temporal check: metric=operating_cash_flow, direction=lower_is_worse, value=cash_flow_deterioration
- `FIN.TEMPORAL.margin_compression`: **INFO** = `margin_compression`
  - Evidence: temporal check: metric=gross_margin, direction=lower_is_worse, value=margin_compression
- `FIN.TEMPORAL.operating_margin_compression`: **INFO** = `operating_margin_compression`
  - Evidence: temporal check: metric=operating_margin, direction=lower_is_worse, value=operating_margin_compression
- `FIN.TEMPORAL.profitability_trend`: **INFO** = `profitability_trend`
  - Evidence: temporal check: metric=net_income, direction=lower_is_worse, value=profitability_trend
- `FIN.TEMPORAL.revenue_deceleration`: **INFO** = `revenue_deceleration`
  - Evidence: temporal check: metric=revenue_growth, direction=lower_is_worse, value=revenue_deceleration

### 3.3.1: Is revenue growing or decelerating?
**Status**: ANSWERED
**Data path**: SEC_10Q -> accruals_ratio, financial_health_narrative, ocf_to_ni
**Gap**: None -- question is being answered with evaluative checks

### 3.3.2: Are margins expanding, stable, or compressing?
**Status**: ANSWERED
**Data path**: SEC_10Q -> accruals_ratio, financial_health_narrative, ocf_to_ni
**Gap**: None -- question is being answered with evaluative checks

### 3.3.3: Is the company profitable? What's the trajectory?
**Status**: ANSWERED
**Data path**: SEC_10Q -> accruals_ratio, financial_health_narrative, ocf_to_ni
**Gap**: None -- question is being answered with evaluative checks

### 3.3.4: How does cash flow quality compare to reported earnings?
**Status**: ANSWERED
**Data path**: SEC_10Q -> accruals_ratio, financial_health_narrative, ocf_to_ni
**Gap**: None -- question is being answered with evaluative checks

### 3.3.5: Are there segment-level divergences hiding overall trends?
**Status**: ANSWERED
**Data path**: SEC_10Q -> accruals_ratio, financial_health_narrative, ocf_to_ni
**Gap**: None -- question is being answered with evaluative checks

### 3.3.6: What is the free cash flow generation and CapEx trend?
**Status**: ANSWERED
**Data path**: SEC_10Q -> accruals_ratio, financial_health_narrative, ocf_to_ni
**Gap**: None -- question is being answered with evaluative checks

## 3.4 Earnings Quality & Forensic Analysis
*Are the financial statements trustworthy, or is there manipulation?*

**Subsection Assessment: ANSWERED** (17 checks)

**Checks:**
- `FIN.ACCT.earnings_manipulation`: **CLEAR** (clear) = `-2.2937`
  - Evidence: Value -2.2937 within thresholds
- `FIN.FORENSIC.accrual_intensity`: **CLEAR** (clear) = `0.0015`
  - Evidence: Value 0.0015 within thresholds
- `FIN.FORENSIC.beneish_dechow_convergence`: **CLEAR** (clear) = `0.0`
  - Evidence: Boolean check: False condition met
- `FIN.FORENSIC.dechow_f_score`: **INFO** = `present`
  - Evidence: Qualitative check: value=present
- `FIN.FORENSIC.enhanced_sloan`: **CLEAR** (clear) = `0.0015`
  - Evidence: Value 0.0015 within thresholds
- `FIN.FORENSIC.fis_composite`: **CLEAR** (clear) = `-2.2937`
  - Evidence: Value -2.2937 within thresholds
- `FIN.FORENSIC.montier_c_score`: **INFO** = `present`
  - Evidence: Qualitative check: value=present
- `FIN.QUALITY.cash_flow_quality`: **CLEAR** (clear) = `0.9953`
  - Evidence: Value 0.9953 within thresholds
- `FIN.QUALITY.deferred_revenue_trend`: **SKIPPED** = `N/A`
- `FIN.QUALITY.dso_ar_divergence`: **TRIGGERED** (yellow) = `11.86`
  - Evidence: Value 11.86 exceeds yellow threshold 10.0
- `FIN.QUALITY.non_gaap_divergence`: **INFO** = `No non-GAAP measures detected in 10-K`
  - Evidence: Qualitative check: value=No non-GAAP measures detected in 10-K
- `FIN.QUALITY.q4_revenue_concentration`: **SKIPPED** = `N/A`
- `FIN.QUALITY.quality_of_earnings`: **CLEAR** (clear) = `0.9953`
  - Evidence: Value 0.9953 within thresholds
- `FIN.QUALITY.revenue_quality_score`: **CLEAR** (clear) = `1.0`
  - Evidence: Value 1.0 within thresholds
- `FIN.TEMPORAL.cfo_ni_divergence`: **INFO** = `cfo_ni_divergence`
  - Evidence: temporal check: metric=net_income_cfo_divergence, direction=higher_is_worse, value=cfo_ni_divergence
- `FIN.TEMPORAL.dso_expansion`: **INFO** = `dso_expansion`
  - Evidence: temporal check: metric=dso_days, direction=higher_is_worse, value=dso_expansion
- `FIN.TEMPORAL.earnings_quality_divergence`: **INFO** = `earnings_quality_divergence`
  - Evidence: temporal check: metric=net_income_cfo_divergence, direction=higher_is_worse, value=earnings_quality_divergence

### 3.4.1: Is there evidence of earnings manipulation (Beneish M-Score, Dechow F-Score)?
**Status**: ANSWERED
**Data path**: SEC_10K -> beneish_m_score
**Gap**: None -- question is being answered with evaluative checks

### 3.4.2: Are accruals abnormally high relative to cash flows?
**Status**: ANSWERED
**Data path**: SEC_10K -> beneish_m_score
**Gap**: None -- question is being answered with evaluative checks

### 3.4.3: Is revenue quality deteriorating (DSO expansion, Q4 concentration, deferred revenue)?
**Status**: ANSWERED
**Data path**: SEC_10K -> beneish_m_score
**Gap**: None -- question is being answered with evaluative checks

### 3.4.4: Is there a growing gap between GAAP and non-GAAP earnings?
**Status**: ANSWERED
**Data path**: SEC_10K -> beneish_m_score
**Gap**: None -- question is being answered with evaluative checks

### 3.4.5: What does the Financial Integrity Score composite indicate?
**Status**: ANSWERED
**Data path**: SEC_10K -> beneish_m_score
**Gap**: None -- question is being answered with evaluative checks

### 3.4.6: Are there specific revenue manipulation patterns? (Bill-and-hold, channel stuffing, side letters, round-tripping, POC manipulation, cookie jar reserves, big bath, Q4 concentration)
**Status**: ANSWERED
**Data path**: SEC_10K -> beneish_m_score
**Gap**: None -- question is being answered with evaluative checks

### 3.4.7: Is the Depreciation Index (DEPI) anomalous? (Depreciation rate slowing without disclosed asset mix change)
**Status**: ANSWERED
**Data path**: SEC_10K -> beneish_m_score
**Gap**: None -- question is being answered with evaluative checks

## 3.5 Accounting Integrity & Audit Risk
*Is the financial reporting reliable?*

**Subsection Assessment: ANSWERED** (18 checks)

**Checks:**
- `FIN.ACCT.auditor`: **INFO** = `unqualified`
  - Evidence: Qualitative check: value=unqualified
- `FIN.ACCT.auditor_attestation_fail`: **SKIPPED** = `N/A`
- `FIN.ACCT.auditor_disagreement`: **SKIPPED** = `N/A`
- `FIN.ACCT.internal_controls`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds
- `FIN.ACCT.material_weakness`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds
- `FIN.ACCT.quality_indicators`: **CLEAR** (clear) = `10.1665`
  - Evidence: Value 10.1665 within thresholds
- `FIN.ACCT.restatement`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds
- `FIN.ACCT.restatement_auditor_link`: **SKIPPED** = `N/A`
- `FIN.ACCT.restatement_magnitude`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds
- `FIN.ACCT.restatement_pattern`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds
- `FIN.ACCT.restatement_stock_window`: **SKIPPED** = `N/A`
- `FIN.ACCT.sec_correspondence`: **INFO** = `Revenue is growing at 6.4% year-over-year. Liquidity is conc...`
  - Evidence: Qualitative check: value=Revenue is growing at 6.4% year-over-year. Liquidity is concerning with a current ratio of 0.89...
- `GOV.EFFECT.audit_committee`: **SKIPPED** [INFERENCE_PATTERN] = `N/A`
- `GOV.EFFECT.audit_opinion`: **SKIPPED** [INFERENCE_PATTERN] = `N/A`
- `GOV.EFFECT.auditor_change`: **SKIPPED** [INFERENCE_PATTERN] = `N/A`
- `GOV.EFFECT.material_weakness`: **SKIPPED** [INFERENCE_PATTERN] = `N/A`
- `GOV.EFFECT.sig_deficiency`: **SKIPPED** [INFERENCE_PATTERN] = `N/A`
- `GOV.EFFECT.sox_404`: **SKIPPED** [INFERENCE_PATTERN] = `N/A`

### 3.5.1: Who is the auditor and what's their tenure and opinion?
**Status**: ANSWERED
**Data path**: SEC_10K, SEC_8K, SEC_DEF14A -> altman_z_score, audit_committee_quality, audit_opinion_type, auditor_attestation_fail, auditor_change_flag, auditor_disagreement, auditor_opinion, financial_health_narrative, material_weakness_flag, material_weaknesses, restatement_auditor_link, restatement_stock_window, restatements, significant_deficiency_flag, sox_404_assessment
**Gap**: None -- question is being answered with evaluative checks

### 3.5.2: Has there been a restatement, material weakness, or significant deficiency?
**Status**: ANSWERED
**Data path**: SEC_10K, SEC_8K, SEC_DEF14A -> altman_z_score, audit_committee_quality, audit_opinion_type, auditor_attestation_fail, auditor_change_flag, auditor_disagreement, auditor_opinion, financial_health_narrative, material_weakness_flag, material_weaknesses, restatement_auditor_link, restatement_stock_window, restatements, significant_deficiency_flag, sox_404_assessment
**Gap**: None -- question is being answered with evaluative checks

### 3.5.3: Has there been an auditor change, and why?
**Status**: ANSWERED
**Data path**: SEC_10K, SEC_8K, SEC_DEF14A -> altman_z_score, audit_committee_quality, audit_opinion_type, auditor_attestation_fail, auditor_change_flag, auditor_disagreement, auditor_opinion, financial_health_narrative, material_weakness_flag, material_weaknesses, restatement_auditor_link, restatement_stock_window, restatements, significant_deficiency_flag, sox_404_assessment
**Gap**: None -- question is being answered with evaluative checks

### 3.5.4: Are there SEC comment letters raising accounting questions?
**Status**: ANSWERED
**Data path**: SEC_10K, SEC_8K, SEC_DEF14A -> altman_z_score, audit_committee_quality, audit_opinion_type, auditor_attestation_fail, auditor_change_flag, auditor_disagreement, auditor_opinion, financial_health_narrative, material_weakness_flag, material_weaknesses, restatement_auditor_link, restatement_stock_window, restatements, significant_deficiency_flag, sox_404_assessment
**Gap**: None -- question is being answered with evaluative checks

### 3.5.5: What are the critical audit matters (CAMs)?
**Status**: ANSWERED
**Data path**: SEC_10K, SEC_8K, SEC_DEF14A -> altman_z_score, audit_committee_quality, audit_opinion_type, auditor_attestation_fail, auditor_change_flag, auditor_disagreement, auditor_opinion, financial_health_narrative, material_weakness_flag, material_weaknesses, restatement_auditor_link, restatement_stock_window, restatements, significant_deficiency_flag, sox_404_assessment
**Gap**: None -- question is being answered with evaluative checks

### 3.5.6: What is the non-audit fee ratio? (Non-audit > audit = independence compromised)
**Status**: ANSWERED
**Data path**: SEC_10K, SEC_8K, SEC_DEF14A -> altman_z_score, audit_committee_quality, audit_opinion_type, auditor_attestation_fail, auditor_change_flag, auditor_disagreement, auditor_opinion, financial_health_narrative, material_weakness_flag, material_weaknesses, restatement_auditor_link, restatement_stock_window, restatements, significant_deficiency_flag, sox_404_assessment
**Gap**: None -- question is being answered with evaluative checks

### 3.5.7: Are there PCAOB inspection findings for this auditor?
**Status**: ANSWERED
**Data path**: SEC_10K, SEC_8K, SEC_DEF14A -> altman_z_score, audit_committee_quality, audit_opinion_type, auditor_attestation_fail, auditor_change_flag, auditor_disagreement, auditor_opinion, financial_health_narrative, material_weakness_flag, material_weaknesses, restatement_auditor_link, restatement_stock_window, restatements, significant_deficiency_flag, sox_404_assessment
**Gap**: None -- question is being answered with evaluative checks

## 3.6 Financial Distress Indicators
*How close is this company to failure?*

**Subsection Assessment: ANSWERED** (5 checks)

**Checks:**
- `FIN.TEMPORAL.debt_ratio_increase`: **INFO** = `debt_ratio_increase`
  - Evidence: temporal check: metric=debt_ratio, direction=higher_is_worse, value=debt_ratio_increase
- `FIN.TEMPORAL.working_capital_deterioration`: **INFO** = `working_capital_deterioration`
  - Evidence: temporal check: metric=working_capital, direction=lower_is_worse, value=working_capital_deterioration
- `FWRD.WARN.goodwill_risk`: **CLEAR** (clear) = `0.6265`
  - Evidence: Value 0.6265 within thresholds
- `FWRD.WARN.impairment_risk`: **INFO** = `Not mentioned in 10-K filing`
  - Evidence: Qualitative check: value=Not mentioned in 10-K filing
- `FWRD.WARN.zone_of_insolvency`: **CLEAR** (clear) = `10.1665`
  - Evidence: Value 10.1665 within thresholds

### 3.6.1: What does the Altman Z-Score indicate? (Z < 1.8 in high-risk sector = SCORING gate trigger for Side A review)
**Status**: ANSWERED
**Gap**: None -- question is being answered with evaluative checks

### 3.6.2: What does the Ohlson O-Score (bankruptcy probability) show?
**Status**: ANSWERED
**Gap**: None -- question is being answered with evaluative checks

### 3.6.3: What does the Piotroski F-Score (fundamental quality) show?
**Status**: ANSWERED
**Gap**: None -- question is being answered with evaluative checks

### 3.6.4: Is the company in or approaching the "Zone of Insolvency"? (Triggers SCORING gate for Side A structure review)
**Status**: ANSWERED
**Gap**: None -- question is being answered with evaluative checks

### 3.6.5: What do credit market signals show? (CDS spreads, default probability, credit rating downgrades)
**Status**: ANSWERED
**Gap**: None -- question is being answered with evaluative checks

### 3.6.6: Is there active restructuring (debt renegotiation, operational restructuring, workforce reduction)?
**Status**: ANSWERED
**Gap**: None -- question is being answered with evaluative checks

## 3.7 Guidance & Market Expectations
*Is management credible in their forward communications?*

**Subsection Assessment: PARTIAL** (5 checks)

**Checks:**
- `FIN.GUIDE.analyst_consensus`: **INFO** = `Revenue is growing at 6.4% year-over-year. Liquidity is conc...`
  - Evidence: Qualitative check: value=Revenue is growing at 6.4% year-over-year. Liquidity is concerning with a current ratio of 0.89...
- `FIN.GUIDE.current`: **INFO** = `Revenue is growing at 6.4% year-over-year. Liquidity is conc...`
  - Evidence: Qualitative check: value=Revenue is growing at 6.4% year-over-year. Liquidity is concerning with a current ratio of 0.89...
- `FIN.GUIDE.earnings_reaction`: **INFO** = `Revenue is growing at 6.4% year-over-year. Liquidity is conc...`
  - Evidence: Qualitative check: value=Revenue is growing at 6.4% year-over-year. Liquidity is concerning with a current ratio of 0.89...
- `FIN.GUIDE.philosophy`: **INFO** [MANAGEMENT_DISPLAY] = `Revenue is growing at 6.4% year-over-year. Liquidity is conc...`
  - Evidence: Management display: Revenue is growing at 6.4% year-over-year. Liquidity is concerning with a current ratio of 0.89, bel...
- `FIN.GUIDE.track_record`: **INFO** = `Revenue is growing at 6.4% year-over-year. Liquidity is conc...`
  - Evidence: Qualitative check: value=Revenue is growing at 6.4% year-over-year. Liquidity is concerning with a current ratio of 0.89...

### 3.7.1: Does the company provide earnings guidance and what's the current outlook?
**Status**: PARTIAL
**Data path**: SEC_8K -> financial_health_narrative
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 3.7.2: What's the guidance track record (beat/miss pattern)?
**Status**: PARTIAL
**Data path**: SEC_8K -> financial_health_narrative
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 3.7.3: What's the guidance philosophy (conservative vs aggressive)?
**Status**: PARTIAL
**Data path**: SEC_8K -> financial_health_narrative
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 3.7.4: How does analyst consensus align with company guidance?
**Status**: PARTIAL
**Data path**: SEC_8K -> financial_health_narrative
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 3.7.5: How does the market react to earnings?
**Status**: PARTIAL
**Data path**: SEC_8K -> financial_health_narrative
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

## 3.8 Sector-Specific Financial Metrics
*Which industry-specific financial metrics apply? (Sector-conditional -- only applicable metrics evaluate)*

**Subsection Assessment: ANSWERED** (10 checks)

**Checks:**
- `FIN.SECTOR.energy`: **INFO** [MANAGEMENT_DISPLAY] = `Revenue is growing at 6.4% year-over-year. Liquidity is conc...`
  - Evidence: Management display: Revenue is growing at 6.4% year-over-year. Liquidity is concerning with a current ratio of 0.89, bel...
- `FIN.SECTOR.retail`: **INFO** [MANAGEMENT_DISPLAY] = `Revenue is growing at 6.4% year-over-year. Liquidity is conc...`
  - Evidence: Management display: Revenue is growing at 6.4% year-over-year. Liquidity is concerning with a current ratio of 0.89, bel...
- `FWRD.WARN.ai_revenue_concentration`: **INFO** = `Not mentioned in 10-K filing`
  - Evidence: Qualitative check: value=Not mentioned in 10-K filing
- `FWRD.WARN.capex_discipline`: **INFO** = `Not mentioned in 10-K filing`
  - Evidence: Qualitative check: value=Not mentioned in 10-K filing
- `FWRD.WARN.data_center_risk`: **INFO** = `2 mention(s): reputation are impacted by information technol...`
  - Evidence: Qualitative check: value=2 mention(s): reputation are impacted by information technology system failures and network dis...
- `FWRD.WARN.gpu_allocation`: **INFO** = `9 mention(s): oduction of new and complex technologies, such...`
  - Evidence: Qualitative check: value=9 mention(s): oduction of new and complex technologies, such as artificial intelligence feature...
- `FWRD.WARN.hyperscaler_dependency`: **INFO** = `2 mention(s): reputation are impacted by information technol...`
  - Evidence: Qualitative check: value=2 mention(s): reputation are impacted by information technology system failures and network dis...
- `FWRD.WARN.margin_pressure`: **INFO** = `Not mentioned in 10-K filing`
  - Evidence: Qualitative check: value=Not mentioned in 10-K filing
- `FWRD.WARN.revenue_quality`: **INFO** = `Not mentioned in 10-K filing`
  - Evidence: Qualitative check: value=Not mentioned in 10-K filing
- `FWRD.WARN.working_capital_trends`: **CLEAR** (clear) = `0.8933`
  - Evidence: Value 0.8933 within thresholds

### 3.8.1: What are the applicable sector-specific KPIs and how do they compare to benchmarks?
**Status**: ANSWERED
**Data path**: SEC_10K -> financial_health_narrative
**Gap**: None -- question is being answered with evaluative checks

---

# 4. GOVERNANCE & DISCLOSURE

## 4.1 Board Composition & Quality
*Is the board structured to provide effective oversight?*

**Subsection Assessment: ANSWERED** (18 checks)

**Checks:**
- `EXEC.PROFILE.avg_tenure`: **SKIPPED** [MANAGEMENT_DISPLAY] = `N/A`
- `EXEC.PROFILE.board_size`: **SKIPPED** [MANAGEMENT_DISPLAY] = `N/A`
- `EXEC.PROFILE.ceo_chair_duality`: **INFO** [MANAGEMENT_DISPLAY] = `1.0`
  - Evidence: Management display: True
- `EXEC.PROFILE.independent_ratio`: **SKIPPED** [MANAGEMENT_DISPLAY] = `N/A`
- `EXEC.PROFILE.overboarded_directors`: **SKIPPED** = `N/A`
- `GOV.BOARD.attendance`: **SKIPPED** = `N/A`
- `GOV.BOARD.ceo_chair`: **TRIGGERED** (red) = `1.0`
  - Evidence: Value 1.0 below red threshold 50.0
- `GOV.BOARD.committees`: **SKIPPED** [MANAGEMENT_DISPLAY] = `N/A`
- `GOV.BOARD.departures`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds
- `GOV.BOARD.diversity`: **SKIPPED** = `N/A`
- `GOV.BOARD.expertise`: **SKIPPED** [MANAGEMENT_DISPLAY] = `N/A`
- `GOV.BOARD.independence`: **SKIPPED** = `N/A`
- `GOV.BOARD.meetings`: **SKIPPED** = `N/A`
- `GOV.BOARD.overboarding`: **SKIPPED** = `N/A`
- `GOV.BOARD.refresh_activity`: **SKIPPED** [MANAGEMENT_DISPLAY] = `N/A`
- `GOV.BOARD.size`: **SKIPPED** = `N/A`
- `GOV.BOARD.succession`: **SKIPPED** = `N/A`
- `GOV.BOARD.tenure`: **SKIPPED** = `N/A`

### 4.1.1: How independent is the board?
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> avg_board_tenure, board_attendance, board_committees, board_expertise, board_independence, board_meeting_count, board_refresh, board_size, ceo_chair_duality, ceo_succession_plan, departures_18mo, overboarded_directors
**Gap**: None -- question is being answered with evaluative checks

### 4.1.2: Is the CEO also the board chair?
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> avg_board_tenure, board_attendance, board_committees, board_expertise, board_independence, board_meeting_count, board_refresh, board_size, ceo_chair_duality, ceo_succession_plan, departures_18mo, overboarded_directors
**Gap**: None -- question is being answered with evaluative checks

### 4.1.3: What's the board size and tenure distribution?
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> avg_board_tenure, board_attendance, board_committees, board_expertise, board_independence, board_meeting_count, board_refresh, board_size, ceo_chair_duality, ceo_succession_plan, departures_18mo, overboarded_directors
**Gap**: None -- question is being answered with evaluative checks

### 4.1.4: Do board members have relevant, demonstrated experience to oversee THIS company's industry and risks?
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> avg_board_tenure, board_attendance, board_committees, board_expertise, board_independence, board_meeting_count, board_refresh, board_size, ceo_chair_duality, ceo_succession_plan, departures_18mo, overboarded_directors
**Gap**: None -- question is being answered with evaluative checks

### 4.1.5: Is this a classified (staggered) board?
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> avg_board_tenure, board_attendance, board_committees, board_expertise, board_independence, board_meeting_count, board_refresh, board_size, ceo_chair_duality, ceo_succession_plan, departures_18mo, overboarded_directors
**Gap**: None -- question is being answered with evaluative checks

### 4.1.6: How engaged is the board (meeting frequency, attendance)?
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> avg_board_tenure, board_attendance, board_committees, board_expertise, board_independence, board_meeting_count, board_refresh, board_size, ceo_chair_duality, ceo_succession_plan, departures_18mo, overboarded_directors
**Gap**: None -- question is being answered with evaluative checks

### 4.1.7: What is the board committee structure? (Audit committee financial expert, comp committee independence, risk committee existence)
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> avg_board_tenure, board_attendance, board_committees, board_expertise, board_independence, board_meeting_count, board_refresh, board_size, ceo_chair_duality, ceo_succession_plan, departures_18mo, overboarded_directors
**Gap**: None -- question is being answered with evaluative checks

### 4.1.8: Is the Board Chair the immediate past CEO ("Successor Chair")?
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> avg_board_tenure, board_attendance, board_committees, board_expertise, board_independence, board_meeting_count, board_refresh, board_size, ceo_chair_duality, ceo_succession_plan, departures_18mo, overboarded_directors
**Gap**: None -- question is being answered with evaluative checks

## 4.2 Executive Team & Stability
*Are the right leaders in place, and is the team stable?*

**Subsection Assessment: ANSWERED** (22 checks)

**Checks:**
- `EXEC.AGGREGATE.board_risk`: **CLEAR** (clear) = `29.9`
  - Evidence: Value 29.9 within thresholds
- `EXEC.AGGREGATE.highest_risk_individual`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds
- `EXEC.CEO.risk_score`: **SKIPPED** = `N/A`
- `EXEC.CFO.risk_score`: **SKIPPED** = `N/A`
- `EXEC.DEPARTURE.cao_departure`: **CLEAR** (clear) = `0.0`
  - Evidence: Boolean check: False condition met
- `EXEC.DEPARTURE.cfo_departure_timing`: **CLEAR** (clear) = `0.0`
  - Evidence: Boolean check: False condition met
- `EXEC.PRIOR_LIT.any_officer`: **CLEAR** (clear) = `0.0`
  - Evidence: Boolean check: False condition met
- `EXEC.PRIOR_LIT.ceo_cfo`: **CLEAR** (clear) = `0.0`
  - Evidence: Boolean check: False condition met
- `EXEC.TENURE.c_suite_turnover`: **INFO** [INFERENCE_PATTERN] = `0.0`
  - Evidence: Single signal only (value=0). Insufficient data for multi-signal pattern detection.
- `EXEC.TENURE.ceo_new`: **INFO** = `CEO identified (Mr. Timothy D. Cook), tenure unavailable`
  - Evidence: Qualitative check: value=CEO identified (Mr. Timothy D. Cook), tenure unavailable
- `EXEC.TENURE.cfo_new`: **INFO** = `CFO identified (Mr. Kevan  Parekh), tenure unavailable`
  - Evidence: Qualitative check: value=CFO identified (Mr. Kevan  Parekh), tenure unavailable
- `GOV.EXEC.ceo_profile`: **INFO** = `Identified: Mr. Timothy D. Cook (tenure unavailable)`
  - Evidence: Qualitative check: value=Identified: Mr. Timothy D. Cook (tenure unavailable)
- `GOV.EXEC.cfo_profile`: **INFO** = `Identified: Mr. Kevan  Parekh (tenure unavailable)`
  - Evidence: Qualitative check: value=Identified: Mr. Kevan  Parekh (tenure unavailable)
- `GOV.EXEC.departure_context`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds
- `GOV.EXEC.founder`: **INFO** = `Identified: Mr. Timothy D. Cook (tenure unavailable)`
  - Evidence: Qualitative check: value=Identified: Mr. Timothy D. Cook (tenure unavailable)
- `GOV.EXEC.key_person`: **INFO** = `Identified: Mr. Timothy D. Cook (tenure unavailable)`
  - Evidence: Qualitative check: value=Identified: Mr. Timothy D. Cook (tenure unavailable)
- `GOV.EXEC.officer_litigation`: **CLEAR** (clear) = `100.0`
  - Evidence: Value 100.0 within thresholds
- `GOV.EXEC.other_officers`: **CLEAR** (clear) = `100.0`
  - Evidence: Value 100.0 within thresholds
- `GOV.EXEC.stability`: **CLEAR** (clear) = `100.0`
  - Evidence: Value 100.0 within thresholds
- `GOV.EXEC.succession_status`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds
- `GOV.EXEC.turnover_analysis`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds
- `GOV.EXEC.turnover_pattern`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds

### 4.2.1: Do the CEO and key executives have relevant, demonstrated experience to run THIS company?
**Status**: ANSWERED
**Data path**: SCAC_SEARCH, SEC_10K, SEC_8K, SEC_DEF14A -> ceo_tenure_years, cfo_tenure_years, departures_18mo, interim_ceo, leadership_stability_score
**Gap**: None -- question is being answered with evaluative checks

### 4.2.2: Have any executives or directors been sued, investigated, or subject to enforcement actions in prior roles at other companies?
**Status**: ANSWERED
**Data path**: SCAC_SEARCH, SEC_10K, SEC_8K, SEC_DEF14A -> ceo_tenure_years, cfo_tenure_years, departures_18mo, interim_ceo, leadership_stability_score
**Gap**: None -- question is being answered with evaluative checks

### 4.2.3: Are there negative personal publicity signals for executives or directors? (Public scandals, reputational red flags)
**Status**: ANSWERED
**Data path**: SCAC_SEARCH, SEC_10K, SEC_8K, SEC_DEF14A -> ceo_tenure_years, cfo_tenure_years, departures_18mo, interim_ceo, leadership_stability_score
**Gap**: None -- question is being answered with evaluative checks

### 4.2.4: What is the C-suite turnover trend and are there signs of management instability? (Rising departures, unplanned exits, short tenures, interim appointments)
**Status**: ANSWERED
**Data path**: SCAC_SEARCH, SEC_10K, SEC_8K, SEC_DEF14A -> ceo_tenure_years, cfo_tenure_years, departures_18mo, interim_ceo, leadership_stability_score
**Gap**: None -- question is being answered with evaluative checks

### 4.2.5: Is there a succession plan for key roles?
**Status**: ANSWERED
**Data path**: SCAC_SEARCH, SEC_10K, SEC_8K, SEC_DEF14A -> ceo_tenure_years, cfo_tenure_years, departures_18mo, interim_ceo, leadership_stability_score
**Gap**: None -- question is being answered with evaluative checks

### 4.2.6: Is there founder/key-person concentration risk?
**Status**: ANSWERED
**Data path**: SCAC_SEARCH, SEC_10K, SEC_8K, SEC_DEF14A -> ceo_tenure_years, cfo_tenure_years, departures_18mo, interim_ceo, leadership_stability_score
**Gap**: None -- question is being answered with evaluative checks

## 4.3 Compensation & Alignment
*Is management incentivized to act in shareholders' interests?*

**Subsection Assessment: ANSWERED** (15 checks)

**Checks:**
- `GOV.PAY.401k_match`: **SKIPPED** [MANAGEMENT_DISPLAY] = `N/A`
- `GOV.PAY.ceo_structure`: **INFO** [MANAGEMENT_DISPLAY] = `533.0`
  - Evidence: Management display: 533.0
- `GOV.PAY.ceo_total`: **TRIGGERED** (red) = `533.0`
  - Evidence: Value 533.0 exceeds red threshold 500.0
- `GOV.PAY.clawback`: **SKIPPED** = `N/A`
- `GOV.PAY.deferred_comp`: **SKIPPED** [MANAGEMENT_DISPLAY] = `N/A`
- `GOV.PAY.equity_burn`: **SKIPPED** = `N/A`
- `GOV.PAY.exec_loans`: **SKIPPED** = `N/A`
- `GOV.PAY.golden_para`: **SKIPPED** = `N/A`
- `GOV.PAY.hedging`: **SKIPPED** = `N/A`
- `GOV.PAY.incentive_metrics`: **SKIPPED** [MANAGEMENT_DISPLAY] = `N/A`
- `GOV.PAY.peer_comparison`: **TRIGGERED** (red) = `533.0`
  - Evidence: Value 533.0 exceeds red threshold 75.0
- `GOV.PAY.pension`: **SKIPPED** [MANAGEMENT_DISPLAY] = `N/A`
- `GOV.PAY.perks`: **SKIPPED** [MANAGEMENT_DISPLAY] = `N/A`
- `GOV.PAY.related_party`: **SKIPPED** = `N/A`
- `GOV.PAY.say_on_pay`: **CLEAR** (clear) = `92.0`
  - Evidence: Value 92.0 within thresholds

### 4.3.1: What's the CEO's total compensation and how does it compare to peers?
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> ceo_pay_ratio, clawback_policy, deferred_comp_detail, equity_burn_rate, executive_loans, executive_perks, golden_parachute_value, hedging_policy, incentive_metrics_detail, pension_detail, related_party_txns, retirement_benefits, say_on_pay_pct
**Gap**: None -- question is being answered with evaluative checks

### 4.3.2: What's the compensation structure (salary vs bonus vs equity)?
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> ceo_pay_ratio, clawback_policy, deferred_comp_detail, equity_burn_rate, executive_loans, executive_perks, golden_parachute_value, hedging_policy, incentive_metrics_detail, pension_detail, related_party_txns, retirement_benefits, say_on_pay_pct
**Gap**: None -- question is being answered with evaluative checks

### 4.3.3: What was the say-on-pay vote result?
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> ceo_pay_ratio, clawback_policy, deferred_comp_detail, equity_burn_rate, executive_loans, executive_perks, golden_parachute_value, hedging_policy, incentive_metrics_detail, pension_detail, related_party_txns, retirement_benefits, say_on_pay_pct
**Gap**: None -- question is being answered with evaluative checks

### 4.3.4: Are performance metrics in incentive comp appropriate?
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> ceo_pay_ratio, clawback_policy, deferred_comp_detail, equity_burn_rate, executive_loans, executive_perks, golden_parachute_value, hedging_policy, incentive_metrics_detail, pension_detail, related_party_txns, retirement_benefits, say_on_pay_pct
**Gap**: None -- question is being answered with evaluative checks

### 4.3.5: Are there clawback policies and what's their scope?
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> ceo_pay_ratio, clawback_policy, deferred_comp_detail, equity_burn_rate, executive_loans, executive_perks, golden_parachute_value, hedging_policy, incentive_metrics_detail, pension_detail, related_party_txns, retirement_benefits, say_on_pay_pct
**Gap**: None -- question is being answered with evaluative checks

### 4.3.6: Are there related-party transactions or excessive perquisites?
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> ceo_pay_ratio, clawback_policy, deferred_comp_detail, equity_burn_rate, executive_loans, executive_perks, golden_parachute_value, hedging_policy, incentive_metrics_detail, pension_detail, related_party_txns, retirement_benefits, say_on_pay_pct
**Gap**: None -- question is being answered with evaluative checks

### 4.3.7: What's the golden parachute/change-in-control exposure?
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> ceo_pay_ratio, clawback_policy, deferred_comp_detail, equity_burn_rate, executive_loans, executive_perks, golden_parachute_value, hedging_policy, incentive_metrics_detail, pension_detail, related_party_txns, retirement_benefits, say_on_pay_pct
**Gap**: None -- question is being answered with evaluative checks

### 4.3.8: What are the executive stock ownership requirements?
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> ceo_pay_ratio, clawback_policy, deferred_comp_detail, equity_burn_rate, executive_loans, executive_perks, golden_parachute_value, hedging_policy, incentive_metrics_detail, pension_detail, related_party_txns, retirement_benefits, say_on_pay_pct
**Gap**: None -- question is being answered with evaluative checks

### 4.3.9: What is the CEO pay ratio to median employee?
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> ceo_pay_ratio, clawback_policy, deferred_comp_detail, equity_burn_rate, executive_loans, executive_perks, golden_parachute_value, hedging_policy, incentive_metrics_detail, pension_detail, related_party_txns, retirement_benefits, say_on_pay_pct
**Gap**: None -- question is being answered with evaluative checks

### 4.3.10: Are there compensation manipulation indicators? (Option spring-loading, backdating, excise tax gross-ups, single vs double triggers)
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> ceo_pay_ratio, clawback_policy, deferred_comp_detail, equity_burn_rate, executive_loans, executive_perks, golden_parachute_value, hedging_policy, incentive_metrics_detail, pension_detail, related_party_txns, retirement_benefits, say_on_pay_pct
**Gap**: None -- question is being answered with evaluative checks

## 4.4 Shareholder Rights & Protections
*How well are shareholder rights protected?*

**Subsection Assessment: ANSWERED** (10 checks)

**Checks:**
- `GOV.RIGHTS.action_consent`: **SKIPPED** = `N/A`
- `GOV.RIGHTS.bylaws`: **SKIPPED** [MANAGEMENT_DISPLAY] = `N/A`
- `GOV.RIGHTS.classified`: **SKIPPED** = `N/A`
- `GOV.RIGHTS.dual_class`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds
- `GOV.RIGHTS.forum_select`: **SKIPPED** [MANAGEMENT_DISPLAY] = `N/A`
- `GOV.RIGHTS.proxy_access`: **SKIPPED** = `N/A`
- `GOV.RIGHTS.special_mtg`: **SKIPPED** = `N/A`
- `GOV.RIGHTS.supermajority`: **SKIPPED** = `N/A`
- `GOV.RIGHTS.takeover`: **SKIPPED** = `N/A`
- `GOV.RIGHTS.voting_rights`: **INFO** [MANAGEMENT_DISPLAY] = `0.0`
  - Evidence: Management display: False

### 4.4.1: Does the company have a dual-class voting structure?
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> action_by_consent, bylaw_provisions, classified_board, dual_class, forum_selection_clause, proxy_access_threshold, special_meeting_threshold, supermajority_required, takeover_defenses
**Gap**: None -- question is being answered with evaluative checks

### 4.4.2: Are there anti-takeover provisions (poison pill, supermajority requirements)?
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> action_by_consent, bylaw_provisions, classified_board, dual_class, forum_selection_clause, proxy_access_threshold, special_meeting_threshold, supermajority_required, takeover_defenses
**Gap**: None -- question is being answered with evaluative checks

### 4.4.3: Is there proxy access for shareholder nominations?
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> action_by_consent, bylaw_provisions, classified_board, dual_class, forum_selection_clause, proxy_access_threshold, special_meeting_threshold, supermajority_required, takeover_defenses
**Gap**: None -- question is being answered with evaluative checks

### 4.4.4: What forum selection and fee-shifting provisions exist?
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> action_by_consent, bylaw_provisions, classified_board, dual_class, forum_selection_clause, proxy_access_threshold, special_meeting_threshold, supermajority_required, takeover_defenses
**Gap**: None -- question is being answered with evaluative checks

### 4.4.5: Have there been recent bylaw amendments?
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> action_by_consent, bylaw_provisions, classified_board, dual_class, forum_selection_clause, proxy_access_threshold, special_meeting_threshold, supermajority_required, takeover_defenses
**Gap**: None -- question is being answered with evaluative checks

## 4.5 Activist Pressure
*Is there activist investor activity creating governance instability?*

**Subsection Assessment: ANSWERED** (14 checks)

**Checks:**
- `GOV.ACTIVIST.13d_filings`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds
- `GOV.ACTIVIST.board_seat`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds
- `GOV.ACTIVIST.campaigns`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds
- `GOV.ACTIVIST.consent`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds
- `GOV.ACTIVIST.demands`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds
- `GOV.ACTIVIST.dissident`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds
- `GOV.ACTIVIST.proposal`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds
- `GOV.ACTIVIST.proxy_contests`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds
- `GOV.ACTIVIST.schedule_13g`: **INFO** [MANAGEMENT_DISPLAY] = `65.483004`
  - Evidence: Management display: 65.483004
- `GOV.ACTIVIST.settle_agree`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds
- `GOV.ACTIVIST.short_activism`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds
- `GOV.ACTIVIST.standstill`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds
- `GOV.ACTIVIST.withhold`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds
- `GOV.ACTIVIST.wolf_pack`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds

### 4.5.1: Are there Schedule 13D filings indicating activist intent?
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> activist_present, institutional_pct
**Gap**: None -- question is being answered with evaluative checks

### 4.5.2: Have there been proxy contests or board seat demands?
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> activist_present, institutional_pct
**Gap**: None -- question is being answered with evaluative checks

### 4.5.3: Are there shareholder proposals with significant support?
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> activist_present, institutional_pct
**Gap**: None -- question is being answered with evaluative checks

### 4.5.4: Is there a short activism campaign targeting governance?
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> activist_present, institutional_pct
**Gap**: None -- question is being answered with evaluative checks

## 4.6 Disclosure Quality & Filing Mechanics
*Is the company meeting its disclosure obligations?*

**Subsection Assessment: ANSWERED** (19 checks)

**Checks:**
- `FWRD.DISC.disclosure_quality_composite`: **INFO** [MANAGEMENT_DISPLAY] = `2/3 disclosure components present`
  - Evidence: Management display: 2/3 disclosure components present
- `FWRD.DISC.guidance_methodology`: **INFO** [MANAGEMENT_DISPLAY] = `CONSERVATIVE`
  - Evidence: Management display: CONSERVATIVE
- `FWRD.DISC.mda_depth`: **INFO** [MANAGEMENT_DISPLAY] = `7 mention(s): 4 and 2023 are not included, and can be found ...`
  - Evidence: Management display: 7 mention(s): 4 and 2023 are not included, and can be found in "Management's Discussion and Analysis...
- `FWRD.DISC.metric_consistency`: **INFO** [MANAGEMENT_DISPLAY] = `Not mentioned in 10-K filing`
  - Evidence: Management display: Not mentioned in 10-K filing
- `FWRD.DISC.non_gaap_reconciliation`: **INFO** [MANAGEMENT_DISPLAY] = `Not mentioned in 10-K filing`
  - Evidence: Management display: Not mentioned in 10-K filing
- `FWRD.DISC.related_party_completeness`: **INFO** [MANAGEMENT_DISPLAY] = `Not mentioned in 10-K filing`
  - Evidence: Management display: Not mentioned in 10-K filing
- `FWRD.DISC.risk_factor_evolution`: **INFO** [MANAGEMENT_DISPLAY] = `0.0`
  - Evidence: Management display: 0
- `FWRD.DISC.sec_comment_letters`: **SKIPPED** [MANAGEMENT_DISPLAY] = `N/A`
- `FWRD.DISC.segment_consistency`: **INFO** [MANAGEMENT_DISPLAY] = `11 mention(s): erformance The following table shows net sale...`
  - Evidence: Management display: 11 mention(s): erformance The following table shows net sales by reportable segment for 2025, 2024 a...
- `GOV.EFFECT.iss_score`: **SKIPPED** [INFERENCE_PATTERN] = `N/A`
- `GOV.EFFECT.late_filing`: **SKIPPED** [INFERENCE_PATTERN] = `N/A`
- `GOV.EFFECT.nt_filing`: **SKIPPED** [INFERENCE_PATTERN] = `N/A`
- `GOV.EFFECT.proxy_advisory`: **SKIPPED** [INFERENCE_PATTERN] = `N/A`
- `NLP.FILING.filing_timing_change`: **SKIPPED** [MANAGEMENT_DISPLAY] = `N/A`
- `NLP.FILING.late_filing`: **SKIPPED** = `N/A`
- `NLP.RISK.factor_count_change`: **INFO** = `0.0`
  - Evidence: Qualitative check: value=0
- `NLP.RISK.litigation_risk_factor_new`: **CLEAR** (clear) = `0.0`
  - Evidence: Boolean check: False condition met
- `NLP.RISK.new_risk_factors`: **INFO** = `0.0`
  - Evidence: Qualitative check: value=0
- `NLP.RISK.regulatory_risk_factor_new`: **CLEAR** (clear) = `0.0`
  - Evidence: Boolean check: False condition met

### 4.6.1: How have risk factors changed year-over-year?
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> iss_governance_score, late_filing_flag, nt_filing_flag, proxy_advisory_concern
**Gap**: None -- question is being answered with evaluative checks

### 4.6.2: Have new litigation-specific or regulatory risk factors appeared?
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> iss_governance_score, late_filing_flag, nt_filing_flag, proxy_advisory_concern
**Gap**: None -- question is being answered with evaluative checks

### 4.6.3: Have previously disclosed risks materialized?
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> iss_governance_score, late_filing_flag, nt_filing_flag, proxy_advisory_concern
**Gap**: None -- question is being answered with evaluative checks

### 4.6.4: Has the company filed on time (NT filings, date shifts)?
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> iss_governance_score, late_filing_flag, nt_filing_flag, proxy_advisory_concern
**Gap**: None -- question is being answered with evaluative checks

### 4.6.5: Is non-GAAP reconciliation adequate?
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> iss_governance_score, late_filing_flag, nt_filing_flag, proxy_advisory_concern
**Gap**: None -- question is being answered with evaluative checks

### 4.6.6: Is segment reporting consistent?
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> iss_governance_score, late_filing_flag, nt_filing_flag, proxy_advisory_concern
**Gap**: None -- question is being answered with evaluative checks

### 4.6.7: Is related-party disclosure complete?
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> iss_governance_score, late_filing_flag, nt_filing_flag, proxy_advisory_concern
**Gap**: None -- question is being answered with evaluative checks

### 4.6.8: Is the guidance methodology transparent?
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> iss_governance_score, late_filing_flag, nt_filing_flag, proxy_advisory_concern
**Gap**: None -- question is being answered with evaluative checks

### 4.6.9: Are 8-K event disclosures timely and complete? (Item 1.05 cyber, Item 4.01 auditor, Item 5.02 exec departure)
**Status**: ANSWERED
**Data path**: SEC_DEF14A -> iss_governance_score, late_filing_flag, nt_filing_flag, proxy_advisory_concern
**Gap**: None -- question is being answered with evaluative checks

## 4.7 Narrative Analysis & Tone
*What does the language reveal about management's confidence?*

**Subsection Assessment: PARTIAL** (12 checks)

**Checks:**
- `FWRD.NARRATIVE.10k_vs_earnings`: **SKIPPED** [MANAGEMENT_DISPLAY] = `N/A`
- `FWRD.NARRATIVE.analyst_skepticism`: **INFO** [MANAGEMENT_DISPLAY] = `0.8`
  - Evidence: Management display: 0.8
- `FWRD.NARRATIVE.auditor_cams`: **INFO** [MANAGEMENT_DISPLAY] = `0.0`
  - Evidence: Management display: 0
- `FWRD.NARRATIVE.investor_vs_sec`: **SKIPPED** [MANAGEMENT_DISPLAY] = `N/A`
- `FWRD.NARRATIVE.narrative_coherence_composite`: **INFO** [MANAGEMENT_DISPLAY] = `COHERENT`
  - Evidence: Management display: COHERENT
- `FWRD.NARRATIVE.short_thesis`: **INFO** [MANAGEMENT_DISPLAY] = `0.8`
  - Evidence: Management display: 0.8
- `NLP.CAM.changes`: **INFO** = `0.0`
  - Evidence: Qualitative check: value=0
- `NLP.DISCLOSURE.forward_looking_decrease`: **INFO** [MANAGEMENT_DISPLAY] = `present`
  - Evidence: Management display: present
- `NLP.DISCLOSURE.hedging_language_increase`: **INFO** [MANAGEMENT_DISPLAY] = `present`
  - Evidence: Management display: present
- `NLP.MDA.readability_absolute`: **INFO** [MANAGEMENT_DISPLAY] = `present`
  - Evidence: Management display: present
- `NLP.MDA.readability_change`: **INFO** = `present`
  - Evidence: Qualitative check: value=present
- `NLP.MDA.tone_shift`: **INFO** = `present`
  - Evidence: Qualitative check: value=present

### 4.7.1: Has the MD&A readability changed (Fog Index)?
**Status**: PARTIAL
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 4.7.2: Has the negative tone shifted?
**Status**: PARTIAL
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 4.7.3: Is there increased hedging/qualifying language?
**Status**: PARTIAL
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 4.7.4: Are forward-looking statements decreasing?
**Status**: PARTIAL
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 4.7.5: Is the 10-K narrative consistent with earnings call messaging?
**Status**: PARTIAL
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 4.7.6: Is the investor-facing narrative consistent with SEC filings?
**Status**: PARTIAL
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 4.7.7: Is there analyst skepticism about management's story?
**Status**: PARTIAL
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 4.7.8: Are there short thesis narratives contradicting management?
**Status**: PARTIAL
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 4.7.9: What do auditor CAMs focus on, and has focus changed?
**Status**: PARTIAL
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 4.7.10: Are there red-flag phrases appearing for the first time in filings? ("Investigation", "subpoena", "material uncertainty")
**Status**: PARTIAL
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 4.7.11: Are risk factors boilerplate or company-specific?
**Status**: PARTIAL
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 4.7.12: What does earnings call Q&A analysis reveal? (Evasion patterns, deflection, "non-answers")
**Status**: PARTIAL
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 4.7.13: What does the full 10-K year-over-year diff show?
**Status**: PARTIAL
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 4.7.14: How does this company's disclosure compare to peer filings?
**Status**: PARTIAL
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 4.7.15: What is the management credibility score? (Forward statements vs actual outcomes)
**Status**: PARTIAL
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

## 4.8 Whistleblower & Investigation Signals
*Are there signals of internal problems?*

**Subsection Assessment: ANSWERED** (3 checks)

**Checks:**
- `FWRD.WARN.whistleblower_exposure`: **INFO** = `Not mentioned in 10-K filing`
  - Evidence: Qualitative check: value=Not mentioned in 10-K filing
- `NLP.WHISTLE.internal_investigation`: **CLEAR** (clear) = `0.0`
  - Evidence: Boolean check: False condition met
- `NLP.WHISTLE.language_detected`: **CLEAR** (clear) = `0.0`
  - Evidence: Boolean check: False condition met

### 4.8.1: Is there whistleblower/qui tam language in filings?
**Status**: ANSWERED
**Gap**: None -- question is being answered with evaluative checks

### 4.8.2: Is there internal investigation language?
**Status**: ANSWERED
**Gap**: None -- question is being answered with evaluative checks

### 4.8.3: Are there signals of internal problems from public sources? (Special committee formation in 8-K/proxy, board-directed investigations, legal/compliance hiring spikes)
**Status**: ANSWERED
**Gap**: None -- question is being answered with evaluative checks

## 4.9 Media & External Narrative
*What are external observers seeing?*

**Subsection Assessment: NO CHECKS** (0 checks)

**Checks:** None mapped

### 4.9.1: What does social media sentiment indicate?
**Status**: NO CHECKS
**Gap**: No checks mapped to this question -- need to create checks or map existing ones

### 4.9.2: Is there investigative journalism activity?
**Status**: NO CHECKS
**Gap**: No checks mapped to this question -- need to create checks or map existing ones

---

# 5. LITIGATION & REGULATORY

## 5.1 Securities Class Actions (Active)
*Are there current SCAs, and how serious are they?*

**Subsection Assessment: ANSWERED** (9 checks)

**Checks:**
- `LIT.SCA.active`: **CLEAR** (clear) = `0.0`
  - Evidence: Boolean check: No active case
- `LIT.SCA.allegations`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds
- `LIT.SCA.case_status`: **NOT_RUN** = `N/A`
  - Evidence: execution_mode=MANUAL_ONLY
- `LIT.SCA.class_period`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds
- `LIT.SCA.exposure`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds
- `LIT.SCA.filing_date`: **INFO** = `No active SCAs`
  - Evidence: Qualitative check: value=No active SCAs
- `LIT.SCA.lead_plaintiff`: **NOT_RUN** = `N/A`
  - Evidence: execution_mode=MANUAL_ONLY
- `LIT.SCA.policy_status`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds
- `LIT.SCA.search`: **TRIGGERED** (red) = `1.0`
  - Evidence: Value 1.0 exceeds red threshold 0.0

### 5.1.1: Are there active securities class actions against this company?
**Status**: ANSWERED
**Data path**: SCAC_SEARCH, SEC_10K -> active_sca_count, contingent_liabilities_total, sca_filing_date, sca_lead_counsel_tier, total_sca_count
**Gap**: None -- question is being answered with evaluative checks

### 5.1.2: What are the class periods, allegations, and case stage?
**Status**: ANSWERED
**Data path**: SCAC_SEARCH, SEC_10K -> active_sca_count, contingent_liabilities_total, sca_filing_date, sca_lead_counsel_tier, total_sca_count
**Gap**: None -- question is being answered with evaluative checks

### 5.1.3: Who is lead counsel and what tier are they?
**Status**: ANSWERED
**Data path**: SCAC_SEARCH, SEC_10K -> active_sca_count, contingent_liabilities_total, sca_filing_date, sca_lead_counsel_tier, total_sca_count
**Gap**: None -- question is being answered with evaluative checks

### 5.1.4: What is the estimated exposure (DDL and settlement range)?
**Status**: ANSWERED
**Data path**: SCAC_SEARCH, SEC_10K -> active_sca_count, contingent_liabilities_total, sca_filing_date, sca_lead_counsel_tier, total_sca_count
**Gap**: None -- question is being answered with evaluative checks

## 5.2 Securities Class Action History
*What does the litigation track record tell us?*

**Subsection Assessment: ANSWERED** (7 checks)

**Checks:**
- `LIT.SCA.dismiss_basis`: **NOT_RUN** = `N/A`
  - Evidence: execution_mode=MANUAL_ONLY
- `LIT.SCA.historical`: **TRIGGERED** (yellow) = `1.0`
  - Evidence: Value 1.0 exceeds yellow threshold 0.0
- `LIT.SCA.prefiling`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds
- `LIT.SCA.prior_dismiss`: **CLEAR** (clear) = `1.0`
  - Evidence: Value 1.0 within thresholds
- `LIT.SCA.prior_settle`: **INFO** = `1.0`
  - Evidence: Qualitative check: value=1
- `LIT.SCA.settle_amount`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds
- `LIT.SCA.settle_date`: **INFO** = `1.0`
  - Evidence: info check: 1

### 5.2.1: How many prior SCAs has this company had?
**Status**: ANSWERED
**Data path**: SCAC_SEARCH -> active_sca_count, contingent_liabilities_total, settled_sca_count, total_sca_count
**Gap**: None -- question is being answered with evaluative checks

### 5.2.2: What were the outcomes (dismissed, settled, amount)?
**Status**: ANSWERED
**Data path**: SCAC_SEARCH -> active_sca_count, contingent_liabilities_total, settled_sca_count, total_sca_count
**Gap**: None -- question is being answered with evaluative checks

### 5.2.3: Is there a recidivist pattern (repeat filer)?
**Status**: ANSWERED
**Data path**: SCAC_SEARCH -> active_sca_count, contingent_liabilities_total, settled_sca_count, total_sca_count
**Gap**: None -- question is being answered with evaluative checks

### 5.2.4: Are there pre-filing signals (law firm announcements, investigations)?
**Status**: ANSWERED
**Data path**: SCAC_SEARCH -> active_sca_count, contingent_liabilities_total, settled_sca_count, total_sca_count
**Gap**: None -- question is being answered with evaluative checks

## 5.3 Derivative & Merger Litigation
*Are there non-SCA shareholder claims?*

**Subsection Assessment: ANSWERED** (4 checks)

**Checks:**
- `LIT.SCA.demand`: **TRIGGERED** (red) = `3.0`
  - Evidence: Value 3.0 exceeds red threshold 0.0
- `LIT.SCA.derivative`: **TRIGGERED** (red) = `3.0`
  - Evidence: Value 3.0 exceeds red threshold 1.0
- `LIT.SCA.erisa`: **TRIGGERED** (red) = `2.0`
  - Evidence: Value 2.0 exceeds red threshold 0.0
- `LIT.SCA.merger_obj`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds

### 5.3.1: Are there active derivative suits (Caremark, duty of loyalty)?
**Status**: ANSWERED
**Data path**: SEC_10K -> deal_litigation_count, derivative_suit_count, regulatory_count
**Gap**: None -- question is being answered with evaluative checks

### 5.3.2: Are there merger objection lawsuits?
**Status**: ANSWERED
**Data path**: SEC_10K -> deal_litigation_count, derivative_suit_count, regulatory_count
**Gap**: None -- question is being answered with evaluative checks

### 5.3.3: Has the company received any Section 220 (Books & Records) demands in the last 24 months?
**Status**: ANSWERED
**Data path**: SEC_10K -> deal_litigation_count, derivative_suit_count, regulatory_count
**Gap**: None -- question is being answered with evaluative checks

### 5.3.4: Are there ERISA class actions (401k stock drop cases)?
**Status**: ANSWERED
**Data path**: SEC_10K -> deal_litigation_count, derivative_suit_count, regulatory_count
**Gap**: None -- question is being answered with evaluative checks

### 5.3.5: Are there appraisal actions? (Delaware Section 262)
**Status**: ANSWERED
**Data path**: SEC_10K -> deal_litigation_count, derivative_suit_count, regulatory_count
**Gap**: None -- question is being answered with evaluative checks

### 5.3.6: What derivative suit risk factors are present BEFORE a suit is filed?
**Status**: ANSWERED
**Data path**: SEC_10K -> deal_litigation_count, derivative_suit_count, regulatory_count
**Gap**: None -- question is being answered with evaluative checks

## 5.4 SEC Enforcement
*Where is this company in the SEC enforcement pipeline?*

**Subsection Assessment: PARTIAL** (9 checks)

**Checks:**
- `LIT.REG.cease_desist`: **SKIPPED** = `N/A`
- `LIT.REG.civil_penalty`: **SKIPPED** = `N/A`
- `LIT.REG.comment_letters`: **SKIPPED** = `N/A`
- `LIT.REG.consent_order`: **SKIPPED** = `N/A`
- `LIT.REG.deferred_pros`: **SKIPPED** = `N/A`
- `LIT.REG.sec_active`: **INFO** = `NONE`
  - Evidence: Qualitative check: value=NONE
- `LIT.REG.sec_investigation`: **INFO** = `NONE`
  - Evidence: Qualitative check: value=NONE
- `LIT.REG.sec_severity`: **INFO** = `NONE`
  - Evidence: Qualitative check: value=NONE
- `LIT.REG.wells_notice`: **INFO** = `0.0`
  - Evidence: Qualitative check: value=False

### 5.4.1: What stage is any SEC matter at (comment letters > inquiry > investigation > Wells > enforcement)?
**Status**: PARTIAL
**Data path**: SEC_10K, SEC_ENFORCEMENT -> cease_desist_count, civil_penalty_count, comment_letter_count, consent_order_count, deferred_prosecution_count, sec_enforcement_stage, wells_notice
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 5.4.2: Are there SEC comment letters, and what topics?
**Status**: PARTIAL
**Data path**: SEC_10K, SEC_ENFORCEMENT -> cease_desist_count, civil_penalty_count, comment_letter_count, consent_order_count, deferred_prosecution_count, sec_enforcement_stage, wells_notice
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 5.4.3: Has there been a Wells Notice?
**Status**: PARTIAL
**Data path**: SEC_10K, SEC_ENFORCEMENT -> cease_desist_count, civil_penalty_count, comment_letter_count, consent_order_count, deferred_prosecution_count, sec_enforcement_stage, wells_notice
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

### 5.4.4: What prior SEC enforcement actions exist?
**Status**: PARTIAL
**Data path**: SEC_10K, SEC_ENFORCEMENT -> cease_desist_count, civil_penalty_count, comment_letter_count, consent_order_count, deferred_prosecution_count, sec_enforcement_stage, wells_notice
**Gap**: Data present but missing threshold evaluation -- checks return INFO without RED/YELLOW/CLEAR assessment

## 5.5 Other Regulatory & Government
*What non-SEC enforcement exposure exists?*

**Subsection Assessment: ANSWERED** (13 checks)

**Checks:**
- `LIT.REG.cfpb_action`: **SKIPPED** = `N/A`
- `LIT.REG.doj_investigation`: **INFO** = `2.0`
  - Evidence: Qualitative check: value=2
- `LIT.REG.dol_audit`: **SKIPPED** = `N/A`
- `LIT.REG.epa_action`: **SKIPPED** = `N/A`
- `LIT.REG.fda_warning`: **SKIPPED** = `N/A`
- `LIT.REG.fdic_order`: **SKIPPED** = `N/A`
- `LIT.REG.foreign_gov`: **SKIPPED** = `N/A`
- `LIT.REG.ftc_investigation`: **INFO** = `2.0`
  - Evidence: Qualitative check: value=2
- `LIT.REG.industry_reg`: **CLEAR** (clear) = `2.0`
  - Evidence: Value 2.0 within thresholds
- `LIT.REG.osha_citation`: **SKIPPED** = `N/A`
- `LIT.REG.state_action`: **SKIPPED** = `N/A`
- `LIT.REG.state_ag`: **SKIPPED** = `N/A`
- `LIT.REG.subpoena`: **SKIPPED** = `N/A`

### 5.5.1: Which government agencies regulate this company?
**Status**: ANSWERED
**Data path**: SEC_10K, SEC_ENFORCEMENT -> cfpb_action_count, dol_audit_count, epa_action_count, fda_warning_count, fdic_order_count, foreign_gov_count, osha_citation_count, regulatory_count, state_action_count, state_ag_count, subpoena_count
**Gap**: None -- question is being answered with evaluative checks

### 5.5.2: Are there active DOJ investigations?
**Status**: ANSWERED
**Data path**: SEC_10K, SEC_ENFORCEMENT -> cfpb_action_count, dol_audit_count, epa_action_count, fda_warning_count, fdic_order_count, foreign_gov_count, osha_citation_count, regulatory_count, state_action_count, state_ag_count, subpoena_count
**Gap**: None -- question is being answered with evaluative checks

### 5.5.3: Are there state AG investigations or multi-state actions?
**Status**: ANSWERED
**Data path**: SEC_10K, SEC_ENFORCEMENT -> cfpb_action_count, dol_audit_count, epa_action_count, fda_warning_count, fdic_order_count, foreign_gov_count, osha_citation_count, regulatory_count, state_action_count, state_ag_count, subpoena_count
**Gap**: None -- question is being answered with evaluative checks

### 5.5.4: Are there industry-specific enforcement actions (FDA, EPA, OSHA, FTC, CFPB)?
**Status**: ANSWERED
**Data path**: SEC_10K, SEC_ENFORCEMENT -> cfpb_action_count, dol_audit_count, epa_action_count, fda_warning_count, fdic_order_count, foreign_gov_count, osha_citation_count, regulatory_count, state_action_count, state_ag_count, subpoena_count
**Gap**: None -- question is being answered with evaluative checks

### 5.5.5: Are there foreign government enforcement matters (UK SFO, EU Commission)?
**Status**: ANSWERED
**Data path**: SEC_10K, SEC_ENFORCEMENT -> cfpb_action_count, dol_audit_count, epa_action_count, fda_warning_count, fdic_order_count, foreign_gov_count, osha_citation_count, regulatory_count, state_action_count, state_ag_count, subpoena_count
**Gap**: None -- question is being answered with evaluative checks

### 5.5.6: Are there congressional investigations or subpoenas?
**Status**: ANSWERED
**Data path**: SEC_10K, SEC_ENFORCEMENT -> cfpb_action_count, dol_audit_count, epa_action_count, fda_warning_count, fdic_order_count, foreign_gov_count, osha_citation_count, regulatory_count, state_action_count, state_ag_count, subpoena_count
**Gap**: None -- question is being answered with evaluative checks

## 5.6 Non-Securities Litigation
*What is the aggregate non-SCA litigation landscape?*

**Subsection Assessment: ANSWERED** (14 checks)

**Checks:**
- `LIT.OTHER.aggregate`: **CLEAR** (clear) = `0.0`
  - Evidence: Value 0.0 within thresholds
- `LIT.OTHER.antitrust`: **SKIPPED** = `N/A`
- `LIT.OTHER.bankruptcy`: **SKIPPED** = `N/A`
- `LIT.OTHER.class_action`: **SKIPPED** = `N/A`
- `LIT.OTHER.contract`: **SKIPPED** = `N/A`
- `LIT.OTHER.cyber_breach`: **SKIPPED** = `N/A`
- `LIT.OTHER.employment`: **SKIPPED** = `N/A`
- `LIT.OTHER.environmental`: **SKIPPED** = `N/A`
- `LIT.OTHER.foreign_suit`: **SKIPPED** = `N/A`
- `LIT.OTHER.gov_contract`: **SKIPPED** = `N/A`
- `LIT.OTHER.ip`: **SKIPPED** = `N/A`
- `LIT.OTHER.product`: **SKIPPED** = `N/A`
- `LIT.OTHER.trade_secret`: **SKIPPED** = `N/A`
- `LIT.OTHER.whistleblower`: **INFO** = `0.0`
  - Evidence: Qualitative check: value=0

### 5.6.1: What is the aggregate active litigation count?
**Status**: ANSWERED
**Data path**: SEC_10K -> active_matter_count, antitrust_count, bankruptcy_count, contract_dispute_count, cyber_breach_count, employment_lit_count, environmental_lit_count, foreign_suit_count, gov_contract_count, ip_litigation_count, non_sca_class_action_count, product_liability_count, trade_secret_count, whistleblower_count
**Gap**: None -- question is being answered with evaluative checks

### 5.6.2: Are there significant product liability, employment, IP, or antitrust matters?
**Status**: ANSWERED
**Data path**: SEC_10K -> active_matter_count, antitrust_count, bankruptcy_count, contract_dispute_count, cyber_breach_count, employment_lit_count, environmental_lit_count, foreign_suit_count, gov_contract_count, ip_litigation_count, non_sca_class_action_count, product_liability_count, trade_secret_count, whistleblower_count
**Gap**: None -- question is being answered with evaluative checks

### 5.6.3: Are there whistleblower/qui tam actions?
**Status**: ANSWERED
**Data path**: SEC_10K -> active_matter_count, antitrust_count, bankruptcy_count, contract_dispute_count, cyber_breach_count, employment_lit_count, environmental_lit_count, foreign_suit_count, gov_contract_count, ip_litigation_count, non_sca_class_action_count, product_liability_count, trade_secret_count, whistleblower_count
**Gap**: None -- question is being answered with evaluative checks

### 5.6.4: Are there cyber breach or environmental litigation matters?
**Status**: ANSWERED
**Data path**: SEC_10K -> active_matter_count, antitrust_count, bankruptcy_count, contract_dispute_count, cyber_breach_count, employment_lit_count, environmental_lit_count, foreign_suit_count, gov_contract_count, ip_litigation_count, non_sca_class_action_count, product_liability_count, trade_secret_count, whistleblower_count
**Gap**: None -- question is being answered with evaluative checks

## 5.7 Defense Posture & Reserves
*How well positioned is the company to defend against claims?*

**Subsection Assessment: NO CHECKS** (0 checks)

**Checks:** None mapped

### 5.7.1: What defense provisions exist (federal forum, PSLRA safe harbor)?
**Status**: NO CHECKS
**Gap**: No checks mapped to this question -- need to create checks or map existing ones

### 5.7.2: What are the contingent liabilities and litigation reserves (ASC 450)?
**Status**: NO CHECKS
**Gap**: No checks mapped to this question -- need to create checks or map existing ones

### 5.7.3: What is the historical defense success rate?
**Status**: NO CHECKS
**Gap**: No checks mapped to this question -- need to create checks or map existing ones

## 5.8 Litigation Risk Patterns
*What systemic litigation patterns apply?*

**Subsection Assessment: NO CHECKS** (0 checks)

**Checks:** None mapped

### 5.8.1: What are the open statute of limitations windows?
**Status**: NO CHECKS
**Gap**: No checks mapped to this question -- need to create checks or map existing ones

### 5.8.2: What industry-specific allegation theories apply?
**Status**: NO CHECKS
**Gap**: No checks mapped to this question -- need to create checks or map existing ones

### 5.8.3: What is the contagion risk from peer lawsuits?
**Status**: NO CHECKS
**Gap**: No checks mapped to this question -- need to create checks or map existing ones

### 5.8.4: Do financial events temporally correlate with stock drops to create class period windows?
**Status**: NO CHECKS
**Gap**: No checks mapped to this question -- need to create checks or map existing ones

## 5.9 Sector-Specific Litigation & Regulatory Patterns
*What sector-specific patterns and regulatory databases apply? (Sector-conditional)*

**Subsection Assessment: NO CHECKS** (0 checks)

**Checks:** None mapped

### 5.9.1: What sector-specific litigation patterns apply to this company?
**Status**: NO CHECKS
**Gap**: No checks mapped to this question -- need to create checks or map existing ones

### 5.9.2: What do sector-specific regulatory databases show?
**Status**: NO CHECKS
**Gap**: No checks mapped to this question -- need to create checks or map existing ones

---

# Summary

## Overall Assessment

**Total questions: 231**

| Status | Count | % |
|--------|-------|---|
| ANSWERED | 152 | 65.8% |
| PARTIAL | 46 | 19.9% |
| NO DATA | 0 | 0.0% |
| NO CHECKS | 14 | 6.1% |
| DISPLAY ONLY | 19 | 8.2% |

## Per-Section Breakdown

| Section | ANSWERED | PARTIAL | NO DATA | NO CHECKS | DISPLAY ONLY | Total |
|---------|----------|---------|---------|-----------|--------------|-------|
| 1. COMPANY | 22 | 18 | 0 | 3 | 16 | 59 |
| 2. MARKET | 24 | 4 | 0 | 0 | 3 | 31 |
| 3. FINANCIAL | 37 | 5 | 0 | 0 | 0 | 42 |
| 4. GOVERNANCE & DISCLOSURE | 45 | 15 | 0 | 2 | 0 | 62 |
| 5. LITIGATION & REGULATORY | 24 | 4 | 0 | 9 | 0 | 37 |

## Per-Subsection Breakdown

| Subsection | Assessment | Checks | TRIGGERED | CLEAR | INFO | SKIPPED |
|------------|------------|--------|-----------|-------|------|---------|
| 1.1 Identity | ANSWERED | 8 | 1 | 0 | 7 | 0 |
| 1.2 Business Model & Revenue | DISPLAY ONLY | 8 | 0 | 0 | 8 | 0 |
| 1.3 Operations & Dependencies | ANSWERED | 13 | 5 | 2 | 6 | 0 |
| 1.4 Corporate Structure & Complexity | NO CHECKS | 0 | 0 | 0 | 0 | 0 |
| 1.5 Geographic Footprint | DISPLAY ONLY | 1 | 0 | 0 | 1 | 0 |
| 1.6 M&A & Corporate Transactions | PARTIAL | 2 | 0 | 0 | 2 | 0 |
| 1.7 Competitive Position & Industry Dynamics | DISPLAY ONLY | 11 | 0 | 0 | 11 | 0 |
| 1.8 Macro & Industry Environment | DISPLAY ONLY | 18 | 0 | 0 | 18 | 0 |
| 1.9 Employee & Workforce Signals | PARTIAL | 8 | 0 | 0 | 3 | 5 |
| 1.10 Customer & Product Signals | PARTIAL | 11 | 0 | 0 | 3 | 8 |
| 1.11 Risk Calendar & Upcoming Catalysts | ANSWERED | 17 | 0 | 1 | 14 | 2 |
| 2.1 Stock Price Performance | ANSWERED | 8 | 0 | 6 | 2 | 0 |
| 2.2 Stock Drop Events | ANSWERED | 4 | 0 | 3 | 1 | 0 |
| 2.3 Volatility & Trading Patterns | PARTIAL | 6 | 0 | 0 | 6 | 0 |
| 2.4 Short Interest & Bearish Signals | ANSWERED | 4 | 0 | 2 | 2 | 0 |
| 2.5 Ownership Structure | ANSWERED | 4 | 0 | 1 | 3 | 0 |
| 2.6 Analyst Coverage & Sentiment | DISPLAY ONLY | 2 | 0 | 0 | 2 | 0 |
| 2.7 Valuation Metrics | ANSWERED | 4 | 0 | 1 | 0 | 3 |
| 2.8 Insider Trading Activity | ANSWERED | 16 | 4 | 3 | 4 | 5 |
| 3.1 Liquidity & Solvency | ANSWERED | 5 | 3 | 0 | 2 | 0 |
| 3.2 Leverage & Debt Structure | ANSWERED | 5 | 0 | 2 | 2 | 1 |
| 3.3 Profitability & Growth | ANSWERED | 10 | 0 | 1 | 9 | 0 |
| 3.4 Earnings Quality & Forensic Analysis | ANSWERED | 17 | 1 | 8 | 6 | 2 |
| 3.5 Accounting Integrity & Audit Risk | ANSWERED | 18 | 0 | 6 | 2 | 10 |
| 3.6 Financial Distress Indicators | ANSWERED | 5 | 0 | 2 | 3 | 0 |
| 3.7 Guidance & Market Expectations | PARTIAL | 5 | 0 | 0 | 5 | 0 |
| 3.8 Sector-Specific Financial Metrics | ANSWERED | 10 | 0 | 1 | 9 | 0 |
| 4.1 Board Composition & Quality | ANSWERED | 18 | 1 | 1 | 1 | 15 |
| 4.2 Executive Team & Stability | ANSWERED | 22 | 0 | 13 | 7 | 2 |
| 4.3 Compensation & Alignment | ANSWERED | 15 | 2 | 1 | 1 | 11 |
| 4.4 Shareholder Rights & Protections | ANSWERED | 10 | 0 | 1 | 1 | 8 |
| 4.5 Activist Pressure | ANSWERED | 14 | 0 | 13 | 1 | 0 |
| 4.6 Disclosure Quality & Filing Mechanics | ANSWERED | 19 | 0 | 2 | 10 | 7 |
| 4.7 Narrative Analysis & Tone | PARTIAL | 12 | 0 | 0 | 10 | 2 |
| 4.8 Whistleblower & Investigation Signals | ANSWERED | 3 | 0 | 2 | 1 | 0 |
| 4.9 Media & External Narrative | NO CHECKS | 0 | 0 | 0 | 0 | 0 |
| 5.1 Securities Class Actions (Active) | ANSWERED | 9 | 1 | 5 | 1 | 2 |
| 5.2 Securities Class Action History | ANSWERED | 7 | 1 | 3 | 2 | 1 |
| 5.3 Derivative & Merger Litigation | ANSWERED | 4 | 3 | 1 | 0 | 0 |
| 5.4 SEC Enforcement | PARTIAL | 9 | 0 | 0 | 4 | 5 |
| 5.5 Other Regulatory & Government | ANSWERED | 13 | 0 | 1 | 2 | 10 |
| 5.6 Non-Securities Litigation | ANSWERED | 14 | 0 | 1 | 1 | 12 |
| 5.7 Defense Posture & Reserves | NO CHECKS | 0 | 0 | 0 | 0 | 0 |
| 5.8 Litigation Risk Patterns | NO CHECKS | 0 | 0 | 0 | 0 | 0 |
| 5.9 Sector-Specific Litigation & Regulatory Patterns | NO CHECKS | 0 | 0 | 0 | 0 | 0 |

## Top 10 Highest-Impact Gaps

These are questions that SHOULD be answerable from available data sources but currently are not being adequately answered:

**1. 5.7.1: What defense provisions exist (federal forum, PSLRA safe harbor)?**
- Assessment: NO CHECKS
- Checks in subsection: 0 (0 SKIPPED)
- Root cause: No checks mapped
- Impact: High -- this is core D&O underwriting data

**2. 5.7.2: What are the contingent liabilities and litigation reserves (ASC 450)?**
- Assessment: NO CHECKS
- Checks in subsection: 0 (0 SKIPPED)
- Root cause: No checks mapped
- Impact: High -- this is core D&O underwriting data

**3. 5.7.3: What is the historical defense success rate?**
- Assessment: NO CHECKS
- Checks in subsection: 0 (0 SKIPPED)
- Root cause: No checks mapped
- Impact: High -- this is core D&O underwriting data

**4. 5.8.1: What are the open statute of limitations windows?**
- Assessment: NO CHECKS
- Checks in subsection: 0 (0 SKIPPED)
- Root cause: No checks mapped
- Impact: High -- this is core D&O underwriting data

**5. 5.8.2: What industry-specific allegation theories apply?**
- Assessment: NO CHECKS
- Checks in subsection: 0 (0 SKIPPED)
- Root cause: No checks mapped
- Impact: High -- this is core D&O underwriting data

**6. 5.8.3: What is the contagion risk from peer lawsuits?**
- Assessment: NO CHECKS
- Checks in subsection: 0 (0 SKIPPED)
- Root cause: No checks mapped
- Impact: High -- this is core D&O underwriting data

**7. 5.8.4: Do financial events temporally correlate with stock drops to create class period windows?**
- Assessment: NO CHECKS
- Checks in subsection: 0 (0 SKIPPED)
- Root cause: No checks mapped
- Impact: High -- this is core D&O underwriting data

**8. 5.9.1: What sector-specific litigation patterns apply to this company?**
- Assessment: NO CHECKS
- Checks in subsection: 0 (0 SKIPPED)
- Root cause: No checks mapped
- Impact: High -- this is core D&O underwriting data

**9. 5.9.2: What do sector-specific regulatory databases show?**
- Assessment: NO CHECKS
- Checks in subsection: 0 (0 SKIPPED)
- Root cause: No checks mapped
- Impact: High -- this is core D&O underwriting data

**10. 4.9.1: What does social media sentiment indicate?**
- Assessment: NO CHECKS
- Checks in subsection: 0 (0 SKIPPED)
- Root cause: No checks mapped
- Impact: High -- this is core D&O underwriting data

## Subsections With No Check Coverage

- **1.4 Corporate Structure & Complexity** -- no checks mapped
- **4.9 Media & External Narrative** -- no checks mapped
- **5.7 Defense Posture & Reserves** -- no checks mapped
- **5.8 Litigation Risk Patterns** -- no checks mapped
- **5.9 Sector-Specific Litigation & Regulatory Patterns** -- no checks mapped

## Check Coverage Statistics

- Total checks in registry: 384
- AUTO-executed checks: 377 (7 non-AUTO: 2 FALLBACK_ONLY, 3 MANUAL_ONLY, 2 SECTOR_CONDITIONAL)
- Checks mapped to v6 subsections: 384 (this audit)
- TRIGGERED: 22
- CLEAR: 83
- INFO: 168
- SKIPPED: 104

## AAPL-Specific Findings Summary

Key triggered checks for Apple Inc.:

- `BIZ.CLASS.litigation_history` (Litigation History Profile): **red** = 1.0
  - Value 1.0 exceeds red threshold 0.0
- `BIZ.DEPEND.distribution` (Product Concentration): **red** = 4.0
  - Value 4.0 exceeds red threshold 3.0
- `BIZ.DEPEND.labor` (Concentration Risk Composite): **red** = 150000.0
  - Value 150000.0 exceeds red threshold 2.0
- `BIZ.DEPEND.macro_sensitivity` (Supply Chain Complexity): **red** = 10.0
  - Value 10.0 exceeds red threshold 5.0
- `BIZ.DEPEND.regulatory_dep` (Single-Source Suppliers): **yellow** = 2.0
  - Value 2.0 exceeds yellow threshold 1.0
- `BIZ.DEPEND.tech_dep` (Government Contract Percentage): **yellow** = 2.0
  - Value 2.0 exceeds yellow threshold 1.0
- `EXEC.INSIDER.ceo_net_selling` (CEO Net Seller of Stock): **red** = 100.0
  - Value 100.0 exceeds red threshold 80.0
- `EXEC.INSIDER.cfo_net_selling` (CFO Net Seller of Stock): **red** = 100.0
  - Value 100.0 exceeds red threshold 80.0
- `FIN.LIQ.efficiency` (Liquidity Efficiency): **yellow** = 0.217
  - Value 0.217 below yellow threshold 0.5
- `FIN.LIQ.position` (Liquidity Position): **red** = 0.8933
  - Value 0.8933 below red threshold 6.0
- `FIN.LIQ.working_capital` (Working Capital Analysis): **red** = 0.8933
  - Value 0.8933 below red threshold 1.0
- `FIN.QUALITY.dso_ar_divergence` (DSO and AR Divergence from Revenue): **yellow** = 11.86
  - Value 11.86 exceeds yellow threshold 10.0
- `GOV.BOARD.ceo_chair` (CEO Chair Separation): **red** = 1.0
  - Value 1.0 below red threshold 50.0
- `GOV.PAY.ceo_total` (Ceo Total): **red** = 533.0
  - Value 533.0 exceeds red threshold 500.0
- `GOV.PAY.peer_comparison` (Peer Comparison): **red** = 533.0
  - Value 533.0 exceeds red threshold 75.0
- `LIT.SCA.demand` (Derivative Demand): **red** = 3.0
  - Value 3.0 exceeds red threshold 0.0
- `LIT.SCA.derivative` (Derivative Litigation): **red** = 3.0
  - Value 3.0 exceeds red threshold 1.0
- `LIT.SCA.erisa` (ERISA Stock Drop): **red** = 2.0
  - Value 2.0 exceeds red threshold 0.0
- `LIT.SCA.historical` (Historical Suits): **yellow** = 1.0
  - Value 1.0 exceeds yellow threshold 0.0
- `LIT.SCA.search` (SCA Database Search): **red** = 1.0
  - Value 1.0 exceeds red threshold 0.0
- `STOCK.INSIDER.cluster_timing` (Cluster Timing): **red** = 1.0
  - Value 1.0 exceeds red threshold 0.0
- `STOCK.INSIDER.notable_activity` (Notable Activity): **red** = 100.0
  - Value 100.0 exceeds red threshold 25.0
