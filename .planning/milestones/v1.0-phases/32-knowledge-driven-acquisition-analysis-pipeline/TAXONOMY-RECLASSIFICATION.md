# Taxonomy Reclassification: 388 Checks to 7-Section D&O Underwriting Brain

**Date:** 2026-02-15
**Status:** WORKING DRAFT — for section-by-section user review
**Input:** 388 checks from `brain/checks.json` v9.0.0, OLD-SYSTEM-INSIGHTS.md gap analysis, BRAIN-DESIGN.md risk model
**Output:** Complete mapping of every check to the new 7-section taxonomy

---

## Part 0: Data Source Fallback Chains

Every check references a data source. When the primary method fails, the system falls through this chain before reporting "Not Available."

| Data Source ID | Primary Method | Fallback 1 | Fallback 2 | Final Fallback |
|---|---|---|---|---|
| SEC_10K | EdgarTools MCP | EDGAR REST API | Web search for filing | Not Available |
| SEC_10Q | EdgarTools MCP | EDGAR REST API | Web search | Not Available |
| SEC_DEF14A | EdgarTools MCP | EDGAR REST API | Web search | Not Available |
| SEC_8K | EdgarTools MCP | EDGAR REST API | Web search | Not Available |
| SEC_FORM4 | EDGAR REST API | EdgarTools MCP | Web search | Not Available |
| SEC_ENFORCEMENT | SEC Litigation Releases page | EDGAR REST API | Web search | Not Available |
| SEC_13DG | EDGAR REST API | EdgarTools MCP | Web search | Not Available |
| MARKET_PRICE | yfinance API | Yahoo Finance web | Web search | Not Available |
| MARKET_SHORT | yfinance API | FINRA short interest | Web search | Not Available |
| SCAC_SEARCH | Stanford SCAC (Playwright) | 10-K Item 3 | CourtListener API | Web search |
| COURT_RECORDS | CourtListener API | PACER | Web search | Not Available |
| GLASSDOOR | Glassdoor (Playwright) | Web search for reviews | Not Available | — |
| INDEED | Indeed (Playwright) | Web search | Not Available | — |
| BLIND | Blind app (web search) | Not Available | — | — |
| LINKEDIN | LinkedIn (Playwright) | Web search | Not Available | — |
| APP_STORE | App Store / Google Play (Fetch) | Web search | Not Available | — |
| TRUSTPILOT | Trustpilot (Fetch) | Web search | Not Available | — |
| G2 | G2.com (Fetch) | Web search | Not Available | — |
| NHTSA | NHTSA complaints API | Web search | Not Available | — |
| FDA | FDA FAERS / MedWatch | Web search | Not Available | — |
| CFPB | CFPB complaint database | Web search | Not Available | — |
| NEWS | Brave Search | Web search | Not Available | — |
| ISS_GLASS_LEWIS | ISS/Glass Lewis (if available) | Web search for proxy advisor recommendations | Not Available | — |

---

## Part 1: COMPANY Section

### What This Section Covers

The COMPANY section establishes **what the company is** — its identity, structure, industry context, and operational dependencies. An underwriter reads this section to understand the baseline risk profile: what business the company is in, how it makes money, where its concentration risks lie, and what operational exposures could amplify D&O claims. This section feeds the **Inherent Risk** layer of the risk model.

### Category Definitions

| Category | Description |
|---|---|
| **COMPANY.IDENTITY** | Core identity: risk classification, market cap tier, listing, employee count, public tenure, growth trajectory |
| **COMPANY.STRUCTURE** | Business model: how the company makes money, revenue mix, cost structure, operating leverage, capital intensity |
| **COMPANY.INDUSTRY** | Industry/competitive context: sector, peers, market position, moat, barriers, growth rate, headwinds, consolidation |
| **COMPANY.OPERATIONS** | Operational dependencies and risks: customer/supplier concentration, cyber posture, AI/tech-specific operational risks |

### Check Reclassification Table

| New ID | Old ID | Name | Type | Data Sources | Fallback Chain | Field Key | Factors | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| COMPANY.IDENTITY.primary_classification | BIZ.CLASS.primary | Primary D&O Risk Classification | display | SEC_10K | SEC_10K | risk_classification | — | keep | |
| COMPANY.IDENTITY.secondary_classification | BIZ.CLASS.secondary | Secondary Risk Classification | display | SEC_10K | SEC_10K | risk_classification | — | keep | |
| COMPANY.IDENTITY.litigation_history | BIZ.CLASS.litigation_history | Litigation History Profile | evaluative | SCAC_SEARCH, SEC_10K | SCAC_SEARCH | total_sca_count | F1 | keep | |
| COMPANY.IDENTITY.market_cap | BIZ.SIZE.market_cap | Market Capitalization | display | MARKET_PRICE | MARKET_PRICE | market_cap | — | keep | |
| COMPANY.IDENTITY.revenue_ttm | BIZ.SIZE.revenue_ttm | Revenue TTM | display | SEC_10K | SEC_10K | section_summary | — | needs_work | field_key should be revenue_ttm, not section_summary |
| COMPANY.IDENTITY.employees | BIZ.SIZE.employees | Employee Count | display | SEC_10K | SEC_10K | employee_count | — | keep | |
| COMPANY.IDENTITY.public_tenure | BIZ.SIZE.growth_trajectory | Public Company Tenure | display | SEC_10K | SEC_10K | years_public | — | rename | Old ID says growth_trajectory but it measures public tenure; name said "Public Company Tenure" — ID/name were swapped with BIZ.SIZE.public_tenure |
| COMPANY.IDENTITY.growth_trajectory | BIZ.SIZE.public_tenure | Growth Trajectory | display | SEC_10K | SEC_10K | years_public | — | rename | Old ID says public_tenure but name said "Revenue Growth YoY" — ID/name were swapped; field_key wrong (years_public, should be revenue_growth_yoy) |
| COMPANY.STRUCTURE.description | BIZ.MODEL.description | Business Description | display | SEC_10K | SEC_10K | business_description | — | keep | |
| COMPANY.STRUCTURE.revenue_type | BIZ.MODEL.revenue_type | Revenue Model Type | evaluative | SEC_10K | SEC_10K | revenue_type_analysis | — | keep | |
| COMPANY.STRUCTURE.revenue_segment | BIZ.MODEL.revenue_segment | Revenue Mix by Segment | display | SEC_10K | SEC_10K | revenue_segment_breakdown | — | keep | |
| COMPANY.STRUCTURE.revenue_geo | BIZ.MODEL.revenue_geo | Revenue Mix by Geography | display | SEC_10K | SEC_10K | revenue_geographic_mix | — | keep | |
| COMPANY.STRUCTURE.cost_structure | BIZ.MODEL.cost_structure | Cost Structure | evaluative | SEC_10K | SEC_10K | cost_structure_analysis | — | keep | |
| COMPANY.STRUCTURE.operating_leverage | BIZ.MODEL.leverage_ops | Operating Leverage Assessment | evaluative | SEC_10K | SEC_10K | operating_leverage | — | keep | |
| COMPANY.STRUCTURE.regulatory_dependency | BIZ.MODEL.regulatory_dep | Regulatory Dependency | evaluative | SEC_10K | SEC_10K | model_regulatory_dependency | — | keep | |
| COMPANY.STRUCTURE.capital_intensity | BIZ.MODEL.capital_intensity | Capital Intensity | evaluative | SEC_10K | SEC_10K | capital_intensity_ratio | — | keep | |
| COMPANY.INDUSTRY.sector | BIZ.COMP.market_position | Sector Classification | display | SEC_10K | SEC_10K | sector | — | keep | |
| COMPANY.INDUSTRY.sector_etf | BIZ.COMP.market_share | Sector ETF Benchmark | display | MARKET_PRICE | MARKET_PRICE | sector | — | rename | Name was "Sector ETF Benchmark" not "Market Share" |
| COMPANY.INDUSTRY.peer_group | BIZ.COMP.competitive_advantage | Peer Group | display | SEC_10K | SEC_10K | sector | — | rename | Old ID said competitive_advantage but name was "Peer Group" |
| COMPANY.INDUSTRY.market_position | BIZ.COMP.threat_assessment | Market Position | display | SEC_10K | SEC_10K | sector | — | rename | Old ID said threat_assessment but name was "Market Position" |
| COMPANY.INDUSTRY.market_share | BIZ.COMP.barriers_entry | Market Share | evaluative | SEC_10K | SEC_10K | barriers_to_entry | — | rename | Old ID said barriers_entry but name was "Market Share"; field_key wrong |
| COMPANY.INDUSTRY.competitive_moat | BIZ.COMP.moat | Competitive Moat | evaluative | SEC_10K | SEC_10K | competitive_moat | — | keep | |
| COMPANY.INDUSTRY.barriers_to_entry | BIZ.COMP.barriers | Barriers to Entry | evaluative | SEC_10K | SEC_10K | barriers_to_entry | — | keep | |
| COMPANY.INDUSTRY.industry_growth | BIZ.COMP.industry_growth | Industry Growth Rate | evaluative | SEC_10K | SEC_10K | sector | — | needs_work | field_key should be industry_growth_rate, not sector |
| COMPANY.INDUSTRY.headwinds | BIZ.COMP.headwinds | Industry Headwinds/Tailwinds | evaluative | SEC_10K | SEC_10K | industry_headwinds | — | keep | |
| COMPANY.INDUSTRY.consolidation | BIZ.COMP.consolidation | Consolidation Trend | display | SEC_10K | SEC_10K | sector | — | needs_work | field_key should be consolidation_trend, not sector |
| COMPANY.INDUSTRY.peer_litigation | BIZ.COMP.peer_litigation | Peer Litigation Frequency | evaluative | SCAC_SEARCH | SCAC_SEARCH | active_sca_count | — | keep | |
| COMPANY.OPERATIONS.customer_conc | BIZ.DEPEND.customer_conc | Customer Concentration | evaluative | SEC_10K | SEC_10K | customer_concentration | F9 | keep | |
| COMPANY.OPERATIONS.supplier_conc | BIZ.DEPEND.supplier_conc | Supplier Concentration | evaluative | SEC_10K | SEC_10K | supplier_concentration | F9 | rename | Name was "Top 5 Customers Concentration" but ID is supplier_conc — name should match ID |
| COMPANY.OPERATIONS.tech_dependency | BIZ.DEPEND.tech_dep | Technology Dependency | evaluative | SEC_10K | SEC_10K | technology_dependency | F9 | rename | Name was "Government Contract Percentage" but ID is tech_dep |
| COMPANY.OPERATIONS.key_person | BIZ.DEPEND.key_person | Key Person Risk | evaluative | SEC_10K | SEC_10K | employee_count | F9 | rename | Name was "Customer Concentration Risk Composite"; field_key wrong (employee_count) |
| COMPANY.OPERATIONS.regulatory_dep | BIZ.DEPEND.regulatory_dep | Regulatory Dependency | evaluative | SEC_10K | SEC_10K | regulatory_dependency | F9 | rename | Name was "Single-Source Suppliers" but ID is regulatory_dep |
| COMPANY.OPERATIONS.capital_dep | BIZ.DEPEND.capital_dep | Capital Dependency | evaluative | SEC_10K | SEC_10K | capital_dependency | F9 | rename | Name was "Key Supplier Dependencies" but ID is capital_dep |
| COMPANY.OPERATIONS.macro_sensitivity | BIZ.DEPEND.macro_sensitivity | Macro Sensitivity | evaluative | SEC_10K | SEC_10K | macro_sensitivity | F9 | rename | Name was "Supply Chain Complexity" but ID is macro_sensitivity |
| COMPANY.OPERATIONS.distribution | BIZ.DEPEND.distribution | Distribution Channel Risk | evaluative | SEC_10K | SEC_10K | distribution_channels | F9 | rename | Name was "Product Concentration" but ID is distribution |
| COMPANY.OPERATIONS.contract_terms | BIZ.DEPEND.contract_terms | Contract Terms Risk | evaluative | SEC_10K | SEC_10K | contract_terms | F9 | rename | Name was "Key Partnerships" but ID is contract_terms |
| COMPANY.OPERATIONS.labor | BIZ.DEPEND.labor | Labor Dependency | evaluative | SEC_10K | SEC_10K | employee_count | F9 | rename | Name was "Concentration Risk Composite"; field_key wrong (employee_count, should be labor_dependency) |
| COMPANY.OPERATIONS.cyber_posture | BIZ.UNI.cyber_posture | Cyber Security Posture | evaluative | SEC_10K | SEC_10K | cybersecurity_posture | — | keep | |
| COMPANY.OPERATIONS.cyber_business | BIZ.UNI.cyber_business | Cyber Business Impact | display | SEC_10K | SEC_10K | cyber_business_risk | — | keep | |
| COMPANY.OPERATIONS.hyperscaler_dependency | FWRD.WARN.hyperscaler_dependency | Hyperscaler Dependency | evaluative | SEC_10K | SEC_10K | N/A | F9 | rename | Was FWRD.WARN but is current operational risk; factor corrected F10->F9 |
| COMPANY.OPERATIONS.gpu_allocation | FWRD.WARN.gpu_allocation | GPU Allocation Risk | evaluative | SEC_10K | SEC_10K | N/A | F9 | rename | Was FWRD.WARN but is current operational risk; factor corrected F10->F9 |
| COMPANY.OPERATIONS.data_center_risk | FWRD.WARN.data_center_risk | Data Center Risk | evaluative | SEC_10K | SEC_10K | N/A | F9 | rename | Was FWRD.WARN but is current operational risk; factor corrected F10->F9 |
| COMPANY.OPERATIONS.ai_revenue_concentration | FWRD.WARN.ai_revenue_concentration | AI Revenue Concentration | evaluative | SEC_10K | SEC_10K | N/A | F9 | rename | Was FWRD.WARN but is current operational risk; factor corrected F10->F9 |
| COMPANY.OPERATIONS.partner_stability | FWRD.WARN.partner_stability | Partner Stability | evaluative | SEC_10K | SEC_10K | N/A | F9 | rename | Was FWRD.WARN but is current operational risk; factor corrected F10->F9 |
| COMPANY.OPERATIONS.vendor_payment_delays | FWRD.WARN.vendor_payment_delays | Vendor Payment Delays | evaluative | SEC_10K | SEC_10K | N/A | F9 | rename | Was FWRD.WARN but is current operational risk; factor corrected F10->F9 |
| COMPANY.OPERATIONS.contract_disputes | FWRD.WARN.contract_disputes | Contract Disputes | evaluative | SEC_10K | SEC_10K | N/A | F9 | rename | Was FWRD.WARN but is current operational risk; factor corrected F10->F9 |
| — | BIZ.UNI.ai_claims | AI Claims | — | — | — | — | — | retire | Too vague — needs replacement with specific AI hazard checks (see Gaps) |

### Consolidation Opportunities

1. **BIZ.COMP.barriers_entry / BIZ.COMP.barriers** — Both measure barriers to entry with very similar field_keys. `barriers_entry` (name: "Market Share") is mislabeled; `barriers` is correctly named. Merge `barriers_entry` into either a proper market_share check or retire it.
2. **BIZ.SIZE.growth_trajectory / BIZ.SIZE.public_tenure** — These two checks have their names and IDs completely swapped. Need to fix the ID-name alignment, not merge.
3. **BIZ.DEPEND.key_person / BIZ.DEPEND.labor** — Both use `employee_count` as field_key, which is wrong for both. They measure different things (key person risk vs labor dependency) but share the wrong data mapping.

### Missing Checks (Gaps)

| Proposed ID | Name | Priority | Why Needed | Data Source |
|---|---|---|---|---|
| COMPANY.IDENTITY.spac_status | SPAC/De-SPAC Detection | HIGH | SPAC litigation was #1 source of new SCAs 2022-2024. No detection exists. Old system: QS-43, A.1.3 | SEC_8K, SEC_10K |
| COMPANY.IDENTITY.spac_age | De-SPAC Age Assessment | HIGH | De-SPAC <24mo = high risk. Projections vs actuals critical. | SEC_8K, SEC_10K |
| COMPANY.OPERATIONS.ai_washing | AI Washing Detection | HIGH | Companies marketing traditional software as "AI-powered." Replaces retired BIZ.UNI.ai_claims with specific pattern. 7->15 cases/yr trend. | SEC_10K, NEWS |
| COMPANY.OPERATIONS.ai_cost_concealment | AI Cost Concealment | MEDIUM | GPU/compute costs growing faster than revenue; unsustainable unit economics hidden by non-GAAP. | SEC_10K, SEC_10Q |
| COMPANY.OPERATIONS.ai_limitation_concealment | AI Limitation Concealment | MEDIUM | Known failure rates or bias in AI systems not disclosed. Evolv Technologies precedent. | SEC_10K, NEWS |
| COMPANY.OPERATIONS.ai_revenue_misattribution | Misleading AI Revenue Claims | MEDIUM | Attributing revenue growth to AI when from other sources. Oddity Tech precedent. | SEC_10K, SEC_8K |
| COMPANY.OPERATIONS.ai_risk_disclosure | AI Risk Disclosure Adequacy | MEDIUM | EU AI Act, IP risks from training data, liability risks from AI outputs not disclosed. | SEC_10K |
| COMPANY.OPERATIONS.ai_rd_claims | AI R&D Claims Verification | LOW | Overstating AI research capabilities, claiming patents that don't exist. | SEC_10K, NEWS |
| COMPANY.OPERATIONS.ai_third_party_validation | AI Third-Party Validation Claims | LOW | Misrepresenting analyst reports, fabricating endorsements. | SEC_10K, NEWS |

### Section Data Acquisition Summary

| Data Source | Status | Notes |
|---|---|---|
| SEC_10K | Implemented | Primary source for all COMPANY checks |
| SEC_8K | Implemented | Needed for SPAC detection (new) |
| MARKET_PRICE | Implemented | Market cap, sector ETF |
| SCAC_SEARCH | Implemented | Litigation history, peer litigation |
| NEWS | Implemented | Needed for AI-specific hazard checks (new) |

---

## Part 2: FINANCIAL Section

### What This Section Covers

The FINANCIAL section assesses **whether the company is financially sound and whether its financial reporting is trustworthy**. An underwriter reads this to evaluate bankruptcy risk (the "master hazard" that amplifies all other D&O claims), earnings manipulation risk, and the reliability of management's financial representations. Financial distress is the single strongest predictor of D&O claims — Moody's EDF-X identifies 82% of eventual bankruptcies 3+ months in advance.

### Category Definitions

| Category | Description |
|---|---|
| **FINANCIAL.LIQUIDITY** | Cash position, working capital, cash burn, runway — can the company pay its bills? |
| **FINANCIAL.LEVERAGE** | Debt structure, coverage ratios, maturity profile, covenants, credit ratings — how much debt risk? |
| **FINANCIAL.PROFITABILITY** | Revenue trends, margins, earnings quality, segment performance, guidance track record |
| **FINANCIAL.INTEGRITY** | Auditor quality, internal controls, restatements, forensic accounting scores, earnings manipulation detection |
| **FINANCIAL.DISTRESS** | Explicit distress indicators: zone of insolvency, going concern, goodwill/impairment risk |

### Check Reclassification Table

| New ID | Old ID | Name | Type | Data Sources | Fallback Chain | Field Key | Factors | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| FINANCIAL.LIQUIDITY.position | FIN.LIQ.position | Liquidity Position | evaluative | SEC_10Q | SEC_10Q | current_ratio | F3 | keep | |
| FINANCIAL.LIQUIDITY.working_capital | FIN.LIQ.working_capital | Working Capital Analysis | evaluative | SEC_10Q | SEC_10Q | current_ratio | F3 | keep | |
| FINANCIAL.LIQUIDITY.efficiency | FIN.LIQ.efficiency | Liquidity Efficiency | evaluative | SEC_10Q, SEC_10K | SEC_10Q | cash_ratio | F3 | keep | |
| FINANCIAL.LIQUIDITY.trend | FIN.LIQ.trend | Liquidity Trend | evaluative | SEC_10Q | SEC_10Q | current_ratio | F3 | keep | |
| FINANCIAL.LIQUIDITY.cash_burn | FIN.LIQ.cash_burn | Cash Burn Analysis | evaluative | SEC_10Q, SEC_10K | SEC_10Q | cash_burn_months | F3 | keep | |
| FINANCIAL.LIQUIDITY.working_capital_trends | FWRD.WARN.working_capital_trends | Working Capital Trends | evaluative | SEC_10K | SEC_10K | N/A | F3 | rename | Was FWRD.WARN; factor corrected F10->F3; field_key needs work |
| FINANCIAL.LIQUIDITY.working_capital_deterioration | FIN.TEMPORAL.working_capital_deterioration | Working Capital Deterioration | evaluative | SEC_10K | SEC_10K | N/A | F3 | keep | Temporal check moved to natural category |
| FINANCIAL.LEVERAGE.structure | FIN.DEBT.structure | Debt Structure | evaluative | SEC_10Q | SEC_10Q | debt_to_ebitda | F3 | keep | |
| FINANCIAL.LEVERAGE.coverage | FIN.DEBT.coverage | Debt Service Coverage | evaluative | SEC_10Q | SEC_10Q | interest_coverage | F3 | keep | |
| FINANCIAL.LEVERAGE.maturity | FIN.DEBT.maturity | Debt Maturity Profile | evaluative | SEC_10K | SEC_10K | refinancing_risk | F3 | keep | |
| FINANCIAL.LEVERAGE.credit_rating | FIN.DEBT.credit_rating | Credit Ratings | evaluative | SEC_10K, SEC_8K | SEC_10K | debt_structure | F3 | keep | |
| FINANCIAL.LEVERAGE.covenants | FIN.DEBT.covenants | Covenant Analysis | evaluative | SEC_10Q, SEC_10K, SEC_8K | SEC_10Q | debt_structure | F3 | keep | |
| FINANCIAL.LEVERAGE.debt_ratio_increase | FIN.TEMPORAL.debt_ratio_increase | Leverage Ratio Increase | evaluative | SEC_10K | SEC_10K | N/A | F3 | keep | Temporal check moved to natural category |
| FINANCIAL.PROFITABILITY.revenue | FIN.PROFIT.revenue | Revenue Analysis | evaluative | SEC_10Q, SEC_10K | SEC_10Q | financial_health_narrative | F6 | needs_work | field_key should be revenue_growth or similar |
| FINANCIAL.PROFITABILITY.margins | FIN.PROFIT.margins | Margin Analysis | evaluative | SEC_10Q | SEC_10Q | accruals_ratio | F6 | needs_work | field_key wrong — accruals_ratio is not margins |
| FINANCIAL.PROFITABILITY.earnings | FIN.PROFIT.earnings | Earnings Quality | evaluative | SEC_10Q, SEC_8K | SEC_10Q | ocf_to_ni | F6 | keep | |
| FINANCIAL.PROFITABILITY.segment | FIN.PROFIT.segment | Segment Analysis | evaluative | SEC_10Q, SEC_10K | SEC_10Q | financial_health_narrative | F6 | needs_work | field_key too generic |
| FINANCIAL.PROFITABILITY.trend | FIN.PROFIT.trend | Profitability Trend | evaluative | SEC_10Q | SEC_10Q | financial_health_narrative | F6 | needs_work | field_key too generic |
| FINANCIAL.PROFITABILITY.guidance_current | FIN.GUIDE.current | Current Guidance | evaluative | SEC_8K | SEC_8K | financial_health_narrative | F6 | needs_work | field_key too generic |
| FINANCIAL.PROFITABILITY.guidance_track_record | FIN.GUIDE.track_record | Guidance Track Record | evaluative | SEC_8K | SEC_8K | financial_health_narrative | F6 | needs_work | field_key too generic |
| FINANCIAL.PROFITABILITY.guidance_philosophy | FIN.GUIDE.philosophy | Guidance Philosophy | evaluative | SEC_8K | SEC_8K | financial_health_narrative | F6 | needs_work | field_key too generic |
| FINANCIAL.PROFITABILITY.earnings_reaction | FIN.GUIDE.earnings_reaction | Earnings Reaction | evaluative | SEC_8K | SEC_8K | financial_health_narrative | F6 | needs_work | field_key too generic |
| FINANCIAL.PROFITABILITY.analyst_consensus | FIN.GUIDE.analyst_consensus | Analyst Consensus | evaluative | SEC_8K | SEC_8K | financial_health_narrative | F6 | needs_work | field_key too generic |
| FINANCIAL.PROFITABILITY.energy_metrics | FIN.SECTOR.energy | Energy Sector Metrics | evaluative | SEC_10K, SEC_10Q | SEC_10K | financial_health_narrative | F9 | needs_work | field_key too generic; industry_scope: energy |
| FINANCIAL.PROFITABILITY.retail_metrics | FIN.SECTOR.retail | Retail Sector Metrics | evaluative | SEC_10K, SEC_10Q | SEC_10K | financial_health_narrative | F9 | needs_work | field_key too generic; industry_scope: retail |
| FINANCIAL.PROFITABILITY.revenue_deceleration | FIN.TEMPORAL.revenue_deceleration | Revenue Growth Deceleration | evaluative | SEC_10K | SEC_10K | N/A | F2, F5 | keep | Temporal check moved to natural category |
| FINANCIAL.PROFITABILITY.margin_compression | FIN.TEMPORAL.margin_compression | Gross/Operating Margin Compression | evaluative | SEC_10K | SEC_10K | N/A | F3, F8 | keep | |
| FINANCIAL.PROFITABILITY.operating_margin_compression | FIN.TEMPORAL.operating_margin_compression | Operating Margin Compression | evaluative | SEC_10K | SEC_10K | N/A | F3, F8 | merge_into:FINANCIAL.PROFITABILITY.margin_compression | Duplicates margin_compression |
| FINANCIAL.PROFITABILITY.profitability_trend | FIN.TEMPORAL.profitability_trend | Net Income / Profitability Trend | evaluative | SEC_10K | SEC_10K | N/A | F2, F3 | keep | |
| FINANCIAL.PROFITABILITY.margin_pressure | FWRD.WARN.margin_pressure | Margin Pressure | evaluative | SEC_10K | SEC_10K | N/A | F3 | rename | Was FWRD.WARN; factor corrected F10->F3 |
| FINANCIAL.PROFITABILITY.capex_discipline | FWRD.WARN.capex_discipline | CapEx Discipline | evaluative | SEC_10K | SEC_10K | N/A | F3 | rename | Was FWRD.WARN; factor corrected F10->F3 |
| FINANCIAL.INTEGRITY.auditor | FIN.ACCT.auditor | Auditor | evaluative | SEC_10K | SEC_10K | auditor_opinion | F3 | keep | |
| FINANCIAL.INTEGRITY.internal_controls | FIN.ACCT.internal_controls | Internal Controls | evaluative | SEC_10K | SEC_10K | material_weaknesses | F3 | keep | |
| FINANCIAL.INTEGRITY.restatement | FIN.ACCT.restatement | Restatement History | evaluative | SEC_8K, SEC_10K | SEC_8K | restatements | F3 | keep | |
| FINANCIAL.INTEGRITY.restatement_magnitude | FIN.ACCT.restatement_magnitude | Restatement Revenue Impact | evaluative | SEC_8K, SEC_10K | SEC_8K | restatements | F3 | keep | |
| FINANCIAL.INTEGRITY.restatement_pattern | FIN.ACCT.restatement_pattern | Repeat Restatement Pattern | evaluative | SEC_8K, SEC_10K | SEC_8K | restatements | F3 | keep | |
| FINANCIAL.INTEGRITY.restatement_auditor_link | FIN.ACCT.restatement_auditor_link | Restatement-Auditor Change Correlation | evaluative | SEC_8K, SEC_10K | SEC_8K | restatement_auditor_link | F3 | keep | |
| FINANCIAL.INTEGRITY.material_weakness | FIN.ACCT.material_weakness | Material Weakness in Internal Controls | evaluative | SEC_10K | SEC_10K | material_weaknesses | F3 | keep | |
| FINANCIAL.INTEGRITY.auditor_disagreement | FIN.ACCT.auditor_disagreement | Auditor Disagreement Letter | evaluative | SEC_8K, SEC_10K | SEC_8K | auditor_disagreement | F3 | keep | |
| FINANCIAL.INTEGRITY.auditor_attestation_fail | FIN.ACCT.auditor_attestation_fail | Failed Auditor Attestation on Internal Controls | evaluative | SEC_10K | SEC_10K | auditor_attestation_fail | F3 | keep | |
| FINANCIAL.INTEGRITY.restatement_stock_window | FIN.ACCT.restatement_stock_window | Restatement Within Stock Drop Window | pattern | SEC_8K, SEC_10K, MARKET_PRICE | SEC_8K | restatement_stock_window | F3 | keep | |
| FINANCIAL.INTEGRITY.sec_correspondence | FIN.ACCT.sec_correspondence | SEC Correspondence | evaluative | SEC_10K | SEC_10K | financial_health_narrative | F3 | needs_work | field_key too generic |
| FINANCIAL.INTEGRITY.quality_indicators | FIN.ACCT.quality_indicators | Quality Indicators | computed | SEC_10K | SEC_10K | altman_z_score | F3 | keep | |
| FINANCIAL.INTEGRITY.earnings_manipulation | FIN.ACCT.earnings_manipulation | Earnings Manipulation | computed | SEC_10K | SEC_10K | beneish_m_score | F3 | keep | |
| FINANCIAL.INTEGRITY.fis_composite | FIN.FORENSIC.fis_composite | Financial Integrity Score Composite | composite | SEC_10K, SEC_10Q | SEC_10K | N/A | F3 | keep | |
| FINANCIAL.INTEGRITY.dechow_f_score | FIN.FORENSIC.dechow_f_score | Dechow F-Score Manipulation Indicator | computed | SEC_10K | SEC_10K | N/A | F3 | keep | |
| FINANCIAL.INTEGRITY.montier_c_score | FIN.FORENSIC.montier_c_score | Montier C-Score Manipulation Indicator | computed | SEC_10K | SEC_10K | N/A | F3 | keep | |
| FINANCIAL.INTEGRITY.enhanced_sloan | FIN.FORENSIC.enhanced_sloan | Enhanced Sloan Accrual Ratio | computed | SEC_10K | SEC_10K | N/A | F3 | keep | |
| FINANCIAL.INTEGRITY.accrual_intensity | FIN.FORENSIC.accrual_intensity | Accrual Intensity Ratio | computed | SEC_10K | SEC_10K | N/A | F3 | keep | |
| FINANCIAL.INTEGRITY.beneish_dechow_convergence | FIN.FORENSIC.beneish_dechow_convergence | Beneish-Dechow Convergence Amplifier | composite | SEC_10K | SEC_10K | N/A | F3 | keep | |
| FINANCIAL.INTEGRITY.revenue_quality_score | FIN.QUALITY.revenue_quality_score | Revenue Quality Score Composite | composite | SEC_10K, SEC_10Q | SEC_10K | N/A | F3 | keep | |
| FINANCIAL.INTEGRITY.cash_flow_quality | FIN.QUALITY.cash_flow_quality | Cash Flow Quality Score Composite | composite | SEC_10K, SEC_10Q | SEC_10K | N/A | F8 | keep | |
| FINANCIAL.INTEGRITY.dso_ar_divergence | FIN.QUALITY.dso_ar_divergence | DSO and AR Divergence from Revenue | evaluative | SEC_10K | SEC_10K | N/A | F3 | keep | |
| FINANCIAL.INTEGRITY.q4_revenue_concentration | FIN.QUALITY.q4_revenue_concentration | Q4 Revenue Concentration | evaluative | SEC_10K, SEC_10Q | SEC_10K | N/A | F3, F5 | keep | |
| FINANCIAL.INTEGRITY.deferred_revenue_trend | FIN.QUALITY.deferred_revenue_trend | Deferred Revenue Trend | evaluative | SEC_10K | SEC_10K | N/A | F3 | keep | |
| FINANCIAL.INTEGRITY.quality_of_earnings | FIN.QUALITY.quality_of_earnings | Quality of Earnings (CFO/NI Ratio) | computed | SEC_10K | SEC_10K | N/A | F8 | keep | |
| FINANCIAL.INTEGRITY.non_gaap_divergence | FIN.QUALITY.non_gaap_divergence | Non-GAAP vs GAAP Earnings Divergence | evaluative | SEC_10K | SEC_10K | N/A | F5 | keep | |
| FINANCIAL.INTEGRITY.dso_expansion | FIN.TEMPORAL.dso_expansion | Days Sales Outstanding Expansion | evaluative | SEC_10K | SEC_10K | N/A | F3 | keep | Temporal check moved to integrity |
| FINANCIAL.INTEGRITY.cfo_ni_divergence | FIN.TEMPORAL.cfo_ni_divergence | Cash Flow / Net Income Divergence | evaluative | SEC_10K | SEC_10K | N/A | F3 | keep | Temporal check moved to integrity |
| FINANCIAL.INTEGRITY.cash_flow_deterioration | FIN.TEMPORAL.cash_flow_deterioration | Operating Cash Flow Deterioration | evaluative | SEC_10K | SEC_10K | N/A | F3 | keep | Temporal moved here |
| FINANCIAL.INTEGRITY.earnings_quality_divergence | FIN.TEMPORAL.earnings_quality_divergence | Earnings Quality Divergence Pattern | pattern | SEC_10K | SEC_10K | N/A | F3, F6 | keep | |
| FINANCIAL.INTEGRITY.revenue_quality | FWRD.WARN.revenue_quality | Revenue Quality | evaluative | SEC_10K | SEC_10K | N/A | F3 | rename | Was FWRD.WARN; factor corrected F10->F3 |
| FINANCIAL.INTEGRITY.audit_committee | GOV.EFFECT.audit_committee | Audit Committee | evaluative | SEC_DEF14A, SEC_10K | SEC_DEF14A | governance_score | F3 | rename | Was GOV.EFFECT; moved here — about financial reporting quality; field_key wrong |
| FINANCIAL.INTEGRITY.audit_opinion | GOV.EFFECT.audit_opinion | Audit Opinion | evaluative | SEC_DEF14A, SEC_10K | SEC_10K | governance_score | F3 | rename | Was GOV.EFFECT; moved here; field_key wrong |
| FINANCIAL.INTEGRITY.auditor_change | GOV.EFFECT.auditor_change | Auditor Change | evaluative | SEC_DEF14A, SEC_10K | SEC_10K | governance_score | F3 | rename | Was GOV.EFFECT; moved here; field_key wrong |
| FINANCIAL.INTEGRITY.material_weakness_gov | GOV.EFFECT.material_weakness | Material Weakness (Governance) | evaluative | SEC_DEF14A, SEC_10K | SEC_10K | governance_score | F3 | merge_into:FINANCIAL.INTEGRITY.material_weakness | Duplicate of FIN.ACCT.material_weakness |
| FINANCIAL.INTEGRITY.sox_404 | GOV.EFFECT.sox_404 | SOX 404 Assessment | evaluative | SEC_DEF14A, SEC_10K | SEC_10K | governance_score | F3 | rename | Was GOV.EFFECT; field_key wrong |
| FINANCIAL.INTEGRITY.sig_deficiency | GOV.EFFECT.sig_deficiency | Significant Deficiency | evaluative | SEC_DEF14A, SEC_10K | SEC_10K | governance_score | F3 | rename | Was GOV.EFFECT; field_key wrong |
| FINANCIAL.DISTRESS.insolvency_zone | FWRD.WARN.zone_of_insolvency | Zone of Insolvency | evaluative | SEC_10K | SEC_10K | N/A | F3 | rename | Was FWRD.WARN; factor corrected F10->F3 |
| FINANCIAL.DISTRESS.goodwill_risk | FWRD.WARN.goodwill_risk | Goodwill Impairment Risk | evaluative | SEC_10K | SEC_10K | N/A | F3 | rename | Was FWRD.WARN; factor corrected F10->F3 |
| FINANCIAL.DISTRESS.impairment_risk | FWRD.WARN.impairment_risk | Asset Impairment Risk | evaluative | SEC_10K | SEC_10K | N/A | F3 | rename | Was FWRD.WARN; factor corrected F10->F3 |

### Consolidation Opportunities

1. **FIN.TEMPORAL.margin_compression / FIN.TEMPORAL.operating_margin_compression** — Both measure margin compression. The first covers gross+operating, the second just operating. Merge into one check with both margin types.
2. **GOV.EFFECT.material_weakness / FIN.ACCT.material_weakness** — Exact duplicate. GOV.EFFECT version uses wrong field_key (governance_score). Retire the GOV.EFFECT version.
3. **FIN.ACCT.auditor / GOV.EFFECT.audit_opinion** — Overlapping but not identical. FIN.ACCT.auditor covers auditor identity; GOV.EFFECT.audit_opinion covers the opinion itself. Keep both but ensure no data overlap.
4. **Multiple FIN.GUIDE.* checks** — 5 guidance checks all use `financial_health_narrative` as field_key. These need specific field_keys or should be consolidated into fewer checks.

### Missing Checks (Gaps)

| Proposed ID | Name | Priority | Why Needed | Data Source |
|---|---|---|---|---|
| FINANCIAL.DISTRESS.going_concern | Going Concern Opinion | HIGH | Direct bankruptcy/claims predictor. Old system: A.6.2. Current system has cash_burn but no explicit going concern flag. | SEC_10K |
| FINANCIAL.DISTRESS.altman_z_score | Altman Z-Score | HIGH | Most widely used bankruptcy prediction model. Formula exists in code but no proper brain check. Z<1.81=distress. | SEC_10K |
| FINANCIAL.INTEGRITY.agr_score | AGR Score | MEDIUM | AGR<50 = 2.5x more likely to face securities litigation. MSCI/RiskMetrics. | SEC_10K, NEWS |
| FINANCIAL.INTEGRITY.bill_and_hold | Bill-and-Hold Revenue Pattern | MEDIUM | Revenue recognized before delivery. Specific fraud pattern from old system taxonomy. | SEC_10K |
| FINANCIAL.INTEGRITY.channel_stuffing | Channel Stuffing Detection | MEDIUM | Forcing excess inventory on distributors. Old system: Module 2 Check 1.1.4. | SEC_10K |
| FINANCIAL.INTEGRITY.side_letters | Side Letter Agreement Risk | MEDIUM | Secret agreements modifying stated terms. Old system: Module 2 Check 1.1.5. | SEC_10K |
| FINANCIAL.INTEGRITY.round_tripping | Round-Tripping Revenue | MEDIUM | Circular transactions creating false revenue. Old system: Module 2 Check 1.1.6. | SEC_10K |
| FINANCIAL.INTEGRITY.cookie_jar_reserves | Cookie Jar Reserves | LOW | Saving earnings for future periods. Old system pattern. | SEC_10K |
| FINANCIAL.INTEGRITY.big_bath_charges | Big Bath Charges | LOW | Taking all bad news at once. Old system pattern. | SEC_10K |
| FINANCIAL.INTEGRITY.non_audit_fee_ratio | Non-Audit Fee Ratio | MEDIUM | Non-audit fees >50% of audit fees = auditor independence red flag. Old system: B.6.1. | SEC_DEF14A |
| FINANCIAL.PROFITABILITY.capex_ocf_ratio | CapEx/OCF Ratio | MEDIUM | Oracle case: capex 571% of OCF. Specific structural check missing. | SEC_10K |
| FINANCIAL.LEVERAGE.off_balance_sheet_leases | Off-Balance Sheet Lease Commitments | MEDIUM | Oracle $248B example. Lease obligations dwarfing revenue. | SEC_10K |
| FINANCIAL.PROFITABILITY.saas_rule_of_40 | SaaS Rule of 40 | LOW | Revenue growth + profit margin >40%. Industry-specific. | SEC_10K |
| FINANCIAL.PROFITABILITY.saas_nrr | SaaS Net Revenue Retention | LOW | NRR <90% = CRITICAL. Industry-specific. | SEC_10K |
| FINANCIAL.PROFITABILITY.biotech_cash_runway | Biotech Cash Runway with Clinical Context | LOW | Cash runway + clinical stage = risk assessment. Industry-specific. | SEC_10K |

### Section Data Acquisition Summary

| Data Source | Status | Notes |
|---|---|---|
| SEC_10K | Implemented | Primary for most financial checks |
| SEC_10Q | Implemented | Quarterly data for liquidity, debt, profitability |
| SEC_8K | Implemented | Restatements, guidance, credit rating changes |
| SEC_DEF14A | Implemented | Audit committee, non-audit fees |
| MARKET_PRICE | Implemented | Restatement-stock window correlation |

---

## Part 3: GOVERNANCE Section

### What This Section Covers

The GOVERNANCE section assesses **whether the people running the company are trustworthy and whether oversight structures work**. An underwriter reads this to evaluate board independence, management stability, compensation alignment, shareholder rights, insider trading patterns, and activist pressure. Governance quality is both a mitigator (strong governance reduces D&O claims) and an amplifier (weak governance enables fraud and mismanagement). Premium credits up to 15% for strong governance.

### Category Definitions

| Category | Description |
|---|---|
| **GOVERNANCE.BOARD** | Board composition, independence, diversity, tenure, meetings, committees, succession |
| **GOVERNANCE.MANAGEMENT** | Executive profiles, stability, turnover, departures, key person risk, prior litigation, risk scores |
| **GOVERNANCE.COMPENSATION** | CEO pay, pay structure, say-on-pay, clawbacks, related party, golden parachutes, hedging, perks |
| **GOVERNANCE.RIGHTS** | Shareholder rights: dual class, voting, bylaws, takeover defenses, proxy access, forum selection |
| **GOVERNANCE.OVERSIGHT** | Governance effectiveness: ISS score, proxy advisory, filing timeliness |
| **GOVERNANCE.INSIDER** | Insider trading activity: Form 4 filings, net selling, 10b5-1 plans, cluster sales, unusual timing |
| **GOVERNANCE.ACTIVIST** | Activist investors: 13D filings, campaigns, proxy contests, short activism, wolf packs |

### Check Reclassification Table

| New ID | Old ID | Name | Type | Data Sources | Fallback Chain | Field Key | Factors | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| GOVERNANCE.BOARD.size | GOV.BOARD.size | Board Size | evaluative | SEC_DEF14A | SEC_DEF14A | board_size | F10 | keep | |
| GOVERNANCE.BOARD.independence | GOV.BOARD.independence | Board Independence | evaluative | SEC_DEF14A | SEC_DEF14A | board_independence | F10 | keep | |
| GOVERNANCE.BOARD.ceo_chair | GOV.BOARD.ceo_chair | CEO Chair Separation | evaluative | SEC_DEF14A | SEC_DEF14A | ceo_chair_duality | F10 | keep | |
| GOVERNANCE.BOARD.diversity | GOV.BOARD.diversity | Board Diversity | evaluative | SEC_DEF14A | SEC_DEF14A | board_size | F10 | needs_work | field_key should be board_diversity, not board_size |
| GOVERNANCE.BOARD.tenure | GOV.BOARD.tenure | Board Tenure | evaluative | SEC_DEF14A | SEC_DEF14A | governance_score | F10 | needs_work | field_key should be avg_board_tenure |
| GOVERNANCE.BOARD.overboarding | GOV.BOARD.overboarding | Director Overboarding | evaluative | SEC_DEF14A | SEC_DEF14A | overboarded_directors | F10 | keep | |
| GOVERNANCE.BOARD.departures | GOV.BOARD.departures | Board Departures | evaluative | SEC_DEF14A | SEC_DEF14A | departures_18mo | F10 | keep | |
| GOVERNANCE.BOARD.attendance | GOV.BOARD.attendance | Board Attendance | evaluative | SEC_DEF14A | SEC_DEF14A | governance_score | F10 | needs_work | field_key should be board_attendance |
| GOVERNANCE.BOARD.expertise | GOV.BOARD.expertise | Board Expertise | evaluative | SEC_DEF14A | SEC_DEF14A | governance_score | F10 | needs_work | field_key should be board_expertise |
| GOVERNANCE.BOARD.refresh_activity | GOV.BOARD.refresh_activity | Board Refresh Activity | evaluative | SEC_DEF14A | SEC_DEF14A | governance_score | F10 | needs_work | field_key should be board_refresh |
| GOVERNANCE.BOARD.meetings | GOV.BOARD.meetings | Board Meeting Frequency | evaluative | SEC_DEF14A | SEC_DEF14A | governance_score | F10 | needs_work | field_key should be board_meetings |
| GOVERNANCE.BOARD.committees | GOV.BOARD.committees | Committee Structure | evaluative | SEC_DEF14A | SEC_DEF14A | governance_score | F10 | needs_work | field_key should be committee_structure |
| GOVERNANCE.BOARD.succession | GOV.BOARD.succession | CEO Succession Planning | evaluative | SEC_DEF14A | SEC_DEF14A | governance_score | F10 | needs_work | field_key should be succession_plan |
| GOVERNANCE.MANAGEMENT.ceo_profile | GOV.EXEC.ceo_profile | CEO Profile | evaluative | SEC_DEF14A | SEC_DEF14A | ceo_tenure_years | F7 | keep | |
| GOVERNANCE.MANAGEMENT.cfo_profile | GOV.EXEC.cfo_profile | CFO Profile | evaluative | SEC_DEF14A | SEC_DEF14A | cfo_tenure_years | F7 | keep | |
| GOVERNANCE.MANAGEMENT.other_officers | GOV.EXEC.other_officers | Other Officers Profile | evaluative | SEC_DEF14A, SEC_8K | SEC_DEF14A | leadership_stability_score | F7 | keep | |
| GOVERNANCE.MANAGEMENT.officer_litigation | GOV.EXEC.officer_litigation | Officer Litigation History | evaluative | SCAC_SEARCH | SCAC_SEARCH | leadership_stability_score | F7 | keep | |
| GOVERNANCE.MANAGEMENT.stability | GOV.EXEC.stability | Executive Stability | evaluative | SEC_DEF14A, SEC_8K | SEC_DEF14A | leadership_stability_score | F7 | keep | |
| GOVERNANCE.MANAGEMENT.turnover_analysis | GOV.EXEC.turnover_analysis | Turnover Analysis | evaluative | SEC_8K | SEC_8K | departures_18mo | F7 | keep | |
| GOVERNANCE.MANAGEMENT.departure_context | GOV.EXEC.departure_context | Departure Context | evaluative | SEC_8K | SEC_8K | departures_18mo | F7 | keep | |
| GOVERNANCE.MANAGEMENT.succession_status | GOV.EXEC.succession_status | Succession Status | evaluative | SEC_8K, SEC_DEF14A | SEC_8K | interim_ceo | F7 | keep | |
| GOVERNANCE.MANAGEMENT.founder | GOV.EXEC.founder | Founder Status | evaluative | SEC_DEF14A | SEC_DEF14A | ceo_tenure_years | F7 | needs_work | field_key should be founder_led |
| GOVERNANCE.MANAGEMENT.key_person | GOV.EXEC.key_person | Key Person Risk | evaluative | SEC_10K | SEC_10K | ceo_tenure_years | F7 | needs_work | field_key should be key_person_risk |
| GOVERNANCE.MANAGEMENT.turnover_pattern | GOV.EXEC.turnover_pattern | Turnover Pattern | pattern | SEC_8K, SEC_DEF14A | SEC_8K | departures_18mo | F7 | keep | |
| GOVERNANCE.MANAGEMENT.board_aggregate_risk | EXEC.AGGREGATE.board_risk | Board Aggregate Risk Score | composite | SEC_DEF14A, SEC_FORM4 | SEC_DEF14A | N/A | F9 | keep | |
| GOVERNANCE.MANAGEMENT.highest_risk_individual | EXEC.AGGREGATE.highest_risk_individual | Highest Individual Risk Score | evaluative | SEC_DEF14A, SEC_FORM4 | SEC_DEF14A | N/A | F9 | keep | |
| GOVERNANCE.MANAGEMENT.ceo_risk_score | EXEC.CEO.risk_score | CEO Individual Risk Score | composite | SEC_DEF14A, SEC_FORM4 | SEC_DEF14A | N/A | F9, F10 | keep | |
| GOVERNANCE.MANAGEMENT.cfo_risk_score | EXEC.CFO.risk_score | CFO Individual Risk Score | composite | SEC_DEF14A, SEC_FORM4 | SEC_DEF14A | N/A | F9, F10 | keep | |
| GOVERNANCE.MANAGEMENT.prior_lit_any | EXEC.PRIOR_LIT.any_officer | Any Officer With Prior Litigation | evaluative | SEC_DEF14A, SCAC_SEARCH | SEC_DEF14A | N/A | F9 | keep | |
| GOVERNANCE.MANAGEMENT.prior_lit_ceo_cfo | EXEC.PRIOR_LIT.ceo_cfo | CEO or CFO With Prior Litigation | evaluative | SEC_DEF14A, SCAC_SEARCH | SEC_DEF14A | N/A | F9 | keep | |
| GOVERNANCE.MANAGEMENT.ceo_tenure_new | EXEC.TENURE.ceo_new | CEO Tenure Less Than 2 Years | evaluative | SEC_DEF14A | SEC_DEF14A | N/A | F10 | keep | |
| GOVERNANCE.MANAGEMENT.cfo_tenure_new | EXEC.TENURE.cfo_new | CFO Tenure Less Than 2 Years | evaluative | SEC_DEF14A | SEC_DEF14A | N/A | F10 | keep | |
| GOVERNANCE.MANAGEMENT.c_suite_turnover | EXEC.TENURE.c_suite_turnover | Multiple C-Suite Departures in 12 Months | pattern | SEC_8K, SEC_DEF14A | SEC_8K | N/A | F10 | keep | |
| GOVERNANCE.MANAGEMENT.cfo_departure_timing | EXEC.DEPARTURE.cfo_departure_timing | CFO Departure Coinciding With Stress | evaluative | SEC_8K | SEC_8K | N/A | F10, F3 | keep | |
| GOVERNANCE.MANAGEMENT.cao_departure | EXEC.DEPARTURE.cao_departure | Chief Accounting Officer Departure | evaluative | SEC_8K | SEC_8K | N/A | F10, F3 | keep | |
| GOVERNANCE.MANAGEMENT.avg_tenure | EXEC.PROFILE.avg_tenure | Average Executive Tenure | display | SEC_DEF14A | SEC_DEF14A | N/A | — | keep | Non-duplicate |
| GOVERNANCE.MANAGEMENT.overboarded_directors | EXEC.PROFILE.overboarded_directors | Directors Serving on 4+ Boards | evaluative | SEC_DEF14A | SEC_DEF14A | N/A | F9 | merge_into:GOVERNANCE.BOARD.overboarding | Overlaps with GOV.BOARD.overboarding |
| — | EXEC.PROFILE.board_size | Board Size (Number of Members) | — | — | — | — | — | retire | Duplicate of GOV.BOARD.size |
| — | EXEC.PROFILE.ceo_chair_duality | CEO Also Chairs Board | — | — | — | — | — | retire | Duplicate of GOV.BOARD.ceo_chair |
| — | EXEC.PROFILE.independent_ratio | Board Independence Percentage | — | — | — | — | — | retire | Duplicate of GOV.BOARD.independence |
| GOVERNANCE.COMPENSATION.ceo_total | GOV.PAY.ceo_total | CEO Total Compensation | evaluative | SEC_DEF14A | SEC_DEF14A | ceo_pay_ratio | F10 | keep | |
| GOVERNANCE.COMPENSATION.ceo_structure | GOV.PAY.ceo_structure | CEO Compensation Structure | evaluative | SEC_DEF14A | SEC_DEF14A | ceo_pay_ratio | F10 | keep | |
| GOVERNANCE.COMPENSATION.peer_comparison | GOV.PAY.peer_comparison | Compensation Peer Comparison | evaluative | SEC_DEF14A | SEC_DEF14A | ceo_pay_ratio | F10 | keep | |
| GOVERNANCE.COMPENSATION.say_on_pay | GOV.PAY.say_on_pay | Say-on-Pay Results | evaluative | SEC_DEF14A | SEC_DEF14A | say_on_pay_pct | F10 | keep | |
| GOVERNANCE.COMPENSATION.clawback | GOV.PAY.clawback | Clawback Policy | evaluative | SEC_DEF14A | SEC_DEF14A | governance_score | F10 | needs_work | field_key should be clawback_policy |
| GOVERNANCE.COMPENSATION.related_party | GOV.PAY.related_party | Related Party Transactions | evaluative | SEC_DEF14A | SEC_DEF14A | governance_score | F10 | needs_work | field_key should be related_party_transactions |
| GOVERNANCE.COMPENSATION.golden_parachute | GOV.PAY.golden_para | Golden Parachute | evaluative | SEC_DEF14A | SEC_DEF14A | governance_score | F10 | needs_work | field_key should be golden_parachute |
| GOVERNANCE.COMPENSATION.incentive_metrics | GOV.PAY.incentive_metrics | Incentive Metrics | evaluative | SEC_DEF14A | SEC_DEF14A | governance_score | F10 | needs_work | field_key should be incentive_metrics |
| GOVERNANCE.COMPENSATION.equity_burn | GOV.PAY.equity_burn | Equity Burn Rate | evaluative | SEC_DEF14A | SEC_DEF14A | governance_score | F10 | needs_work | field_key should be equity_burn_rate |
| GOVERNANCE.COMPENSATION.hedging | GOV.PAY.hedging | Anti-Hedging Policy | evaluative | SEC_DEF14A | SEC_DEF14A | governance_score | F10 | needs_work | field_key should be hedging_policy |
| GOVERNANCE.COMPENSATION.perks | GOV.PAY.perks | Executive Perquisites | evaluative | SEC_DEF14A | SEC_DEF14A | governance_score | F10 | needs_work | field_key should be exec_perks |
| GOVERNANCE.COMPENSATION.401k_match | GOV.PAY.401k_match | 401K Match | display | SEC_DEF14A | SEC_DEF14A | governance_score | F10 | needs_work | field_key wrong |
| GOVERNANCE.COMPENSATION.deferred_comp | GOV.PAY.deferred_comp | Deferred Compensation | display | SEC_DEF14A | SEC_DEF14A | governance_score | F10 | needs_work | field_key wrong |
| GOVERNANCE.COMPENSATION.pension | GOV.PAY.pension | Pension | display | SEC_DEF14A | SEC_DEF14A | governance_score | F10 | needs_work | field_key wrong |
| GOVERNANCE.COMPENSATION.exec_loans | GOV.PAY.exec_loans | Executive Loans | evaluative | SEC_DEF14A | SEC_DEF14A | governance_score | F10 | needs_work | field_key wrong |
| GOVERNANCE.RIGHTS.dual_class | GOV.RIGHTS.dual_class | Dual Class Structure | evaluative | SEC_DEF14A | SEC_DEF14A | dual_class | F10 | keep | |
| GOVERNANCE.RIGHTS.voting_rights | GOV.RIGHTS.voting_rights | Voting Rights | evaluative | SEC_DEF14A | SEC_DEF14A | dual_class | F10 | needs_work | field_key should be voting_rights |
| GOVERNANCE.RIGHTS.bylaws | GOV.RIGHTS.bylaws | Bylaws | evaluative | SEC_DEF14A | SEC_DEF14A | governance_score | F10 | needs_work | field_key wrong |
| GOVERNANCE.RIGHTS.takeover | GOV.RIGHTS.takeover | Takeover Defenses | evaluative | SEC_DEF14A | SEC_DEF14A | governance_score | F10 | needs_work | field_key wrong |
| GOVERNANCE.RIGHTS.proxy_access | GOV.RIGHTS.proxy_access | Proxy Access | evaluative | SEC_DEF14A | SEC_DEF14A | governance_score | F10 | needs_work | field_key wrong |
| GOVERNANCE.RIGHTS.forum_select | GOV.RIGHTS.forum_select | Forum Selection | evaluative | SEC_DEF14A | SEC_DEF14A | governance_score | F10 | needs_work | field_key wrong |
| GOVERNANCE.RIGHTS.supermajority | GOV.RIGHTS.supermajority | Supermajority Requirement | evaluative | SEC_DEF14A | SEC_DEF14A | governance_score | F10 | needs_work | field_key wrong |
| GOVERNANCE.RIGHTS.action_consent | GOV.RIGHTS.action_consent | Action by Written Consent | evaluative | SEC_DEF14A | SEC_DEF14A | governance_score | F10 | needs_work | field_key wrong |
| GOVERNANCE.RIGHTS.special_mtg | GOV.RIGHTS.special_mtg | Special Meeting Rights | evaluative | SEC_DEF14A | SEC_DEF14A | governance_score | F10 | needs_work | field_key wrong |
| GOVERNANCE.RIGHTS.classified | GOV.RIGHTS.classified | Classified Board | evaluative | SEC_DEF14A | SEC_DEF14A | classified_board | F10 | keep | |
| GOVERNANCE.OVERSIGHT.iss_score | GOV.EFFECT.iss_score | ISS Governance Score | evaluative | SEC_DEF14A, SEC_10K | ISS_GLASS_LEWIS | governance_score | F10 | needs_work | Data source should be ISS_GLASS_LEWIS, not SEC_10K |
| GOVERNANCE.OVERSIGHT.proxy_advisory | GOV.EFFECT.proxy_advisory | Proxy Advisory Recommendations | evaluative | SEC_DEF14A, SEC_10K | ISS_GLASS_LEWIS | governance_score | F10 | needs_work | Data source should be ISS_GLASS_LEWIS |
| GOVERNANCE.OVERSIGHT.late_filing | GOV.EFFECT.late_filing | Late Filing | evaluative | SEC_DEF14A, SEC_10K | SEC_10K | governance_score | F10 | needs_work | field_key should be late_filing |
| GOVERNANCE.OVERSIGHT.nt_filing | GOV.EFFECT.nt_filing | NT Filing | evaluative | SEC_DEF14A, SEC_10K | SEC_10K | governance_score | F10 | needs_work | field_key should be nt_filing |
| GOVERNANCE.INSIDER.form4_filings | GOV.INSIDER.form4_filings | Form 4 Filing Summary | evaluative | SEC_FORM4 | SEC_FORM4 | insider_pct | F4 | keep | |
| GOVERNANCE.INSIDER.net_selling | GOV.INSIDER.net_selling | Net Insider Selling | evaluative | SEC_FORM4 | SEC_FORM4 | insider_pct | F4 | keep | |
| GOVERNANCE.INSIDER.10b5_plans | GOV.INSIDER.10b5_plans | 10b5-1 Plans | evaluative | SEC_FORM4 | SEC_FORM4 | governance_score | F4 | needs_work | field_key should be 10b5_plan_count |
| GOVERNANCE.INSIDER.plan_adoption | GOV.INSIDER.plan_adoption | Plan Adoption Timing | evaluative | SEC_FORM4 | SEC_FORM4 | governance_score | F4 | needs_work | field_key wrong |
| GOVERNANCE.INSIDER.cluster_sales | GOV.INSIDER.cluster_sales | Cluster Sales | pattern | SEC_FORM4 | SEC_FORM4 | governance_score | F4 | needs_work | field_key wrong |
| GOVERNANCE.INSIDER.unusual_timing | GOV.INSIDER.unusual_timing | Unusual Timing | pattern | SEC_FORM4 | SEC_FORM4 | governance_score | F4 | needs_work | field_key wrong |
| GOVERNANCE.INSIDER.executive_sales | GOV.INSIDER.executive_sales | Executive Sales | evaluative | SEC_FORM4 | SEC_FORM4 | insider_pct | F4 | keep | |
| GOVERNANCE.INSIDER.ownership_pct | GOV.INSIDER.ownership_pct | Insider Ownership Percentage | evaluative | SEC_FORM4 | SEC_FORM4 | insider_pct | F4 | keep | |
| GOVERNANCE.INSIDER.summary | STOCK.INSIDER.summary | Insider Activity Summary | evaluative | SEC_FORM4 | SEC_FORM4 | insider_net_activity | F4 | keep | Moved from STOCK to GOVERNANCE |
| GOVERNANCE.INSIDER.notable_activity | STOCK.INSIDER.notable_activity | Notable Insider Activity | evaluative | SEC_FORM4 | SEC_FORM4 | ceo_cfo_selling_pct | F4 | keep | Moved from STOCK |
| GOVERNANCE.INSIDER.cluster_timing | STOCK.INSIDER.cluster_timing | Cluster Timing | pattern | SEC_FORM4 | SEC_FORM4 | cluster_selling | F4 | keep | Moved from STOCK |
| GOVERNANCE.INSIDER.ceo_net_selling | EXEC.INSIDER.ceo_net_selling | CEO Net Seller of Stock | evaluative | SEC_FORM4 | SEC_FORM4 | N/A | F6, F9 | keep | |
| GOVERNANCE.INSIDER.cfo_net_selling | EXEC.INSIDER.cfo_net_selling | CFO Net Seller of Stock | evaluative | SEC_FORM4 | SEC_FORM4 | N/A | F6, F9 | keep | |
| GOVERNANCE.INSIDER.cluster_selling_exec | EXEC.INSIDER.cluster_selling | Multiple Officers Selling Within 30 Days | pattern | SEC_FORM4 | SEC_FORM4 | N/A | F6, F9 | merge_into:GOVERNANCE.INSIDER.cluster_sales | Overlaps with GOV.INSIDER.cluster_sales |
| GOVERNANCE.INSIDER.non_10b51 | EXEC.INSIDER.non_10b51 | Discretionary Selling (Not 10b5-1) | pattern | SEC_FORM4 | SEC_FORM4 | N/A | F6, F9 | keep | |
| GOVERNANCE.ACTIVIST.13d_filings | GOV.ACTIVIST.13d_filings | 13D Filings | evaluative | SEC_DEF14A, SEC_13DG | SEC_13DG | activist_present | F10 | keep | |
| GOVERNANCE.ACTIVIST.campaigns | GOV.ACTIVIST.campaigns | Activist Campaigns | evaluative | SEC_DEF14A, SEC_13DG | SEC_13DG | activist_present | F10 | keep | |
| GOVERNANCE.ACTIVIST.proxy_contests | GOV.ACTIVIST.proxy_contests | Proxy Contests | evaluative | SEC_DEF14A, SEC_13DG | SEC_13DG | activist_present | F10 | keep | |
| GOVERNANCE.ACTIVIST.settle_agree | GOV.ACTIVIST.settle_agree | Settlement Agreements | evaluative | SEC_DEF14A, SEC_13DG | SEC_13DG | activist_present | F10 | keep | |
| GOVERNANCE.ACTIVIST.short_activism | GOV.ACTIVIST.short_activism | Short Activism | evaluative | SEC_DEF14A, SEC_13DG | SEC_13DG | activist_present | F10 | keep | |
| GOVERNANCE.ACTIVIST.demands | GOV.ACTIVIST.demands | Activist Demands | evaluative | SEC_DEF14A, SEC_13DG | SEC_13DG | activist_present | F10 | keep | |
| GOVERNANCE.ACTIVIST.schedule_13g | GOV.ACTIVIST.schedule_13g | Schedule 13G Analysis | evaluative | SEC_DEF14A, SEC_13DG | SEC_13DG | institutional_pct | F10 | keep | |
| GOVERNANCE.ACTIVIST.wolf_pack | GOV.ACTIVIST.wolf_pack | Wolf Pack Detection | pattern | SEC_DEF14A, SEC_13DG | SEC_13DG | activist_present | F10 | keep | |
| GOVERNANCE.ACTIVIST.board_seat | GOV.ACTIVIST.board_seat | Activist Board Seat | evaluative | SEC_DEF14A, SEC_13DG | SEC_13DG | activist_present | F10 | keep | |
| GOVERNANCE.ACTIVIST.dissident | GOV.ACTIVIST.dissident | Dissident Slate | evaluative | SEC_DEF14A, SEC_13DG | SEC_13DG | activist_present | F10 | keep | |
| GOVERNANCE.ACTIVIST.withhold | GOV.ACTIVIST.withhold | Withhold Campaign | evaluative | SEC_DEF14A, SEC_13DG | SEC_13DG | activist_present | F10 | keep | |
| GOVERNANCE.ACTIVIST.proposal | GOV.ACTIVIST.proposal | Shareholder Proposal | evaluative | SEC_DEF14A, SEC_13DG | SEC_13DG | activist_present | F10 | keep | |
| GOVERNANCE.ACTIVIST.consent | GOV.ACTIVIST.consent | Consent Solicitation | evaluative | SEC_DEF14A, SEC_13DG | SEC_13DG | activist_present | F10 | keep | |
| GOVERNANCE.ACTIVIST.standstill | GOV.ACTIVIST.standstill | Standstill Agreement | evaluative | SEC_DEF14A, SEC_13DG | SEC_13DG | activist_present | F10 | keep | |

### Consolidation Opportunities

1. **GOV.INSIDER.cluster_sales / EXEC.INSIDER.cluster_selling / STOCK.INSIDER.cluster_timing** — Three checks measuring cluster insider selling from three different prefixes. Consolidate into one GOVERNANCE.INSIDER.cluster_sales with proper thresholds.
2. **GOV.BOARD.overboarding / EXEC.PROFILE.overboarded_directors** — Same check, different locations. Keep the GOV.BOARD version.
3. **GOV.INSIDER.net_selling / STOCK.INSIDER.summary** — Both track net insider selling. Summary is more comprehensive; keep both but ensure distinct purposes (summary = overview, net_selling = specific metric).
4. **Many GOV.PAY.* checks use `governance_score` as field_key** — 15 compensation checks all use the same wrong field_key. Each needs its own specific key.
5. **Many GOV.BOARD.* checks use `governance_score` as field_key** — 8 board checks use this catch-all. Each needs a specific key.
6. **Many GOV.RIGHTS.* checks use `governance_score` as field_key** — 8 rights checks use this catch-all. Each needs a specific key.

### Missing Checks (Gaps)

| Proposed ID | Name | Priority | Why Needed | Data Source |
|---|---|---|---|---|
| GOVERNANCE.COMPENSATION.spring_loading | Options Spring-Loading | MEDIUM | Granting options before positive news. Old system: Module 4 Check 5.1. | SEC_DEF14A, SEC_FORM4 |
| GOVERNANCE.COMPENSATION.backdating | Options Backdating | MEDIUM | Retroactively dating options to lower strike. Old system: Module 4 Check 5.2. | SEC_DEF14A, SEC_FORM4 |
| GOVERNANCE.COMPENSATION.share_pledging | Share Pledging by Insiders | MEDIUM | Using company stock as loan collateral = forced selling risk. Old system: Module 4 Check 5.3. | SEC_DEF14A |
| GOVERNANCE.COMPENSATION.anti_pledging_policy | Anti-Hedging/Pledging Policy | MEDIUM | Existence and enforcement of anti-hedging/pledging policy. | SEC_DEF14A |
| GOVERNANCE.COMPENSATION.change_control_triggers | Change-in-Control Triggers | LOW | Single vs double trigger analysis for change-in-control payments. | SEC_DEF14A |
| GOVERNANCE.INSIDER.10b5_adoption_timing | 10b5-1 Adoption Timing Analysis | MEDIUM | Plan adopted right before bad news = suspect. Old system: Module 4 Check 5.4. | SEC_FORM4, SEC_8K |
| GOVERNANCE.RIGHTS.dual_class_sunset | Dual-Class Sunset Provisions | LOW | Do dual-class provisions expire? When? Old system: Module 4 Check 6.1. | SEC_DEF14A |
| GOVERNANCE.RIGHTS.fee_shifting_bylaws | Fee-Shifting Bylaws | LOW | Loser pays in litigation = chilling effect on derivative suits. | SEC_DEF14A |

### Section Data Acquisition Summary

| Data Source | Status | Notes |
|---|---|---|
| SEC_DEF14A | Implemented | Primary for board, comp, rights |
| SEC_FORM4 | Implemented | Insider trading data |
| SEC_8K | Implemented | Departures, changes |
| SEC_13DG | Implemented | Activist/ownership data |
| SCAC_SEARCH | Implemented | Prior litigation for officers |
| ISS_GLASS_LEWIS | NOT implemented | ISS QualityScore, proxy advisor recs. Currently N/A. |

---

## Part 4: LITIGATION Section

### What This Section Covers

The LITIGATION section catalogs **what legal and regulatory actions exist or are imminent**. An underwriter reads this to evaluate current claims exposure, regulatory risk, and the litigation environment. Active securities class actions are the single most important D&O underwriting factor — a company with a pending SCA is essentially a known loss. The section also tracks regulatory enforcement, employment litigation, and commercial disputes that could escalate to D&O claims.

### Category Definitions

| Category | Description |
|---|---|
| **LITIGATION.SECURITIES** | Securities class actions: active, historical, settlements, dismissals, derivative suits, merger objections, ERISA |
| **LITIGATION.REGULATORY** | Regulatory enforcement: SEC, DOJ, FTC, state AG, industry regulators (EPA, OSHA, CFPB, FDA, FDIC) |
| **LITIGATION.EMPLOYMENT** | Employment-related: employment suits, whistleblower actions |
| **LITIGATION.COMMERCIAL** | Commercial litigation: antitrust, contract, IP, trade secret, product liability, cyber breach, foreign suits, gov contracts, environmental |
| **LITIGATION.AGGREGATE** | Aggregate litigation metrics: total active matters, class actions, bankruptcy-related claims |

### Check Reclassification Table

| New ID | Old ID | Name | Type | Data Sources | Fallback Chain | Field Key | Factors | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| LITIGATION.SECURITIES.search | LIT.SCA.search | SCA Database Search | evaluative | SCAC_SEARCH | SCAC_SEARCH | total_sca_count | F1 | keep | |
| LITIGATION.SECURITIES.active | LIT.SCA.active | Active SCA Status | evaluative | SCAC_SEARCH | SCAC_SEARCH | active_sca_count | F1 | keep | |
| LITIGATION.SECURITIES.filing_date | LIT.SCA.filing_date | SCA Filing Date | display | SCAC_SEARCH | SCAC_SEARCH | sca_filing_date | F1 | keep | |
| LITIGATION.SECURITIES.class_period | LIT.SCA.class_period | Class Period | evaluative | SCAC_SEARCH | SCAC_SEARCH | active_sca_count | F1 | needs_work | field_key should be class_period |
| LITIGATION.SECURITIES.allegations | LIT.SCA.allegations | Allegation Summary | evaluative | SCAC_SEARCH | SCAC_SEARCH | active_sca_count | F1 | needs_work | field_key should be allegation_types |
| LITIGATION.SECURITIES.lead_plaintiff | LIT.SCA.lead_plaintiff | Lead Plaintiff | evaluative | SCAC_SEARCH | SCAC_SEARCH | sca_lead_counsel_tier | F1 | keep | |
| LITIGATION.SECURITIES.case_status | LIT.SCA.case_status | Case Status | evaluative | SCAC_SEARCH | SCAC_SEARCH | active_sca_count | F1 | needs_work | field_key should be case_status |
| LITIGATION.SECURITIES.exposure | LIT.SCA.exposure | Exposure Estimate | computed | SCAC_SEARCH, MARKET_PRICE | SCAC_SEARCH | contingent_liabilities_total | F1 | keep | |
| LITIGATION.SECURITIES.policy_status | LIT.SCA.policy_status | D&O Policy Status | evaluative | SEC_10K | SEC_10K | active_sca_count | F1 | needs_work | field_key should be policy_status |
| LITIGATION.SECURITIES.prior_settle | LIT.SCA.prior_settle | Prior Settlements | evaluative | SCAC_SEARCH | SCAC_SEARCH | settled_sca_count | F1 | keep | |
| LITIGATION.SECURITIES.settle_amount | LIT.SCA.settle_amount | Settlement Amount | evaluative | SCAC_SEARCH | SCAC_SEARCH | contingent_liabilities_total | F1 | keep | |
| LITIGATION.SECURITIES.settle_date | LIT.SCA.settle_date | Settlement Date | display | SCAC_SEARCH | SCAC_SEARCH | settled_sca_count | F1 | keep | |
| LITIGATION.SECURITIES.prior_dismiss | LIT.SCA.prior_dismiss | Prior Dismissals | evaluative | SCAC_SEARCH | SCAC_SEARCH | total_sca_count | F1 | keep | |
| LITIGATION.SECURITIES.dismiss_basis | LIT.SCA.dismiss_basis | Dismissal Basis | evaluative | SCAC_SEARCH | SCAC_SEARCH | total_sca_count | F1 | keep | |
| LITIGATION.SECURITIES.historical | LIT.SCA.historical | Historical Suits | evaluative | SCAC_SEARCH | SCAC_SEARCH | total_sca_count | F1 | keep | |
| LITIGATION.SECURITIES.derivative | LIT.SCA.derivative | Derivative Litigation | evaluative | SEC_10K, SCAC_SEARCH | SCAC_SEARCH | derivative_suit_count | F1 | keep | |
| LITIGATION.SECURITIES.demand | LIT.SCA.demand | Derivative Demand | evaluative | SEC_10K, SEC_8K | SEC_10K | derivative_suit_count | F1 | keep | |
| LITIGATION.SECURITIES.merger_objection | LIT.SCA.merger_obj | Merger Objection | evaluative | SEC_10K, SEC_8K | SEC_10K | deal_litigation_count | F1 | keep | |
| LITIGATION.SECURITIES.erisa | LIT.SCA.erisa | ERISA Stock Drop | evaluative | SEC_10K | SEC_10K | regulatory_count | F1 | keep | |
| LITIGATION.SECURITIES.prefiling | LIT.SCA.prefiling | Pre-Filing Activity | evaluative | SCAC_SEARCH | SCAC_SEARCH | active_sca_count | F1 | keep | |
| LITIGATION.SECURITIES.existing_action | STOCK.LIT.existing_action | Existing Securities Action | evaluative | SCAC_SEARCH, SEC_10K | SCAC_SEARCH | active_sca_count | F1, F2 | keep | Moved from STOCK |
| LITIGATION.REGULATORY.sec_investigation | LIT.REG.sec_investigation | SEC Investigation | evaluative | SEC_ENFORCEMENT, SEC_10K | SEC_ENFORCEMENT | sec_enforcement_stage | F1, F5 | keep | |
| LITIGATION.REGULATORY.sec_wells_notice | LIT.REG.sec_active | SEC Wells Notice | evaluative | SEC_10K, SEC_10Q, SEC_8K | SEC_10K | sec_enforcement_stage | F1, F5 | keep | |
| LITIGATION.REGULATORY.sec_current_action | LIT.REG.sec_severity | SEC Current Action | evaluative | SEC_ENFORCEMENT | SEC_ENFORCEMENT | sec_enforcement_stage | F1, F5 | keep | |
| LITIGATION.REGULATORY.doj_investigation | LIT.REG.doj_investigation | DOJ Investigation | evaluative | SEC_ENFORCEMENT | SEC_ENFORCEMENT | regulatory_count | F1, F5 | rename | Name was "SEC Prior Actions" — corrected |
| LITIGATION.REGULATORY.industry_reg | LIT.REG.industry_reg | Industry Regulatory Action | evaluative | SEC_ENFORCEMENT | SEC_ENFORCEMENT | regulatory_count | F1, F5 | rename | Name was "SEC Penalties" — corrected |
| LITIGATION.REGULATORY.ftc_investigation | LIT.REG.ftc_investigation | FTC Investigation | evaluative | SEC_ENFORCEMENT | SEC_ENFORCEMENT | regulatory_count | F1, F5 | rename | Name was "SEC Consent Decrees" — corrected |
| LITIGATION.REGULATORY.state_ag | LIT.REG.state_ag | State Attorney General Action | evaluative | SEC_10K, SEC_ENFORCEMENT | SEC_10K | regulatory_count | F5, F7 | keep | |
| LITIGATION.REGULATORY.subpoena | LIT.REG.subpoena | Subpoena | evaluative | SEC_10K, SEC_ENFORCEMENT | SEC_10K | regulatory_count | F5, F7 | keep | |
| LITIGATION.REGULATORY.comment_letters | LIT.REG.comment_letters | SEC Comment Letters | evaluative | SEC_10K, SEC_ENFORCEMENT | SEC_10K | comment_letter_count | F5, F7 | keep | |
| LITIGATION.REGULATORY.deferred_pros | LIT.REG.deferred_pros | Deferred Prosecution Agreement | evaluative | SEC_10K, SEC_ENFORCEMENT | SEC_10K | regulatory_count | F5, F7 | keep | |
| LITIGATION.REGULATORY.wells_notice | LIT.REG.wells_notice | Wells Notice | evaluative | SEC_10K, SEC_ENFORCEMENT | SEC_10K | wells_notice | F5, F7 | keep | |
| LITIGATION.REGULATORY.consent_order | LIT.REG.consent_order | Consent Order | evaluative | SEC_10K, SEC_ENFORCEMENT | SEC_10K | regulatory_count | F5, F7 | keep | |
| LITIGATION.REGULATORY.cease_desist | LIT.REG.cease_desist | Cease and Desist | evaluative | SEC_10K, SEC_ENFORCEMENT | SEC_10K | regulatory_count | F5, F7 | keep | |
| LITIGATION.REGULATORY.civil_penalty | LIT.REG.civil_penalty | Civil Penalty | evaluative | SEC_10K, SEC_ENFORCEMENT | SEC_10K | regulatory_count | F5, F7 | keep | |
| LITIGATION.REGULATORY.dol_audit | LIT.REG.dol_audit | DOL Audit | evaluative | SEC_10K, SEC_ENFORCEMENT | SEC_10K | regulatory_count | F5, F7 | keep | |
| LITIGATION.REGULATORY.epa_action | LIT.REG.epa_action | EPA Action | evaluative | SEC_10K, SEC_ENFORCEMENT | SEC_10K | regulatory_count | F5, F7 | keep | |
| LITIGATION.REGULATORY.osha_citation | LIT.REG.osha_citation | OSHA Citation | evaluative | SEC_10K, SEC_ENFORCEMENT | SEC_10K | regulatory_count | F5, F7 | keep | |
| LITIGATION.REGULATORY.cfpb_action | LIT.REG.cfpb_action | CFPB Action | evaluative | SEC_10K, SEC_ENFORCEMENT | SEC_10K | regulatory_count | F5, F7 | keep | |
| LITIGATION.REGULATORY.fdic_order | LIT.REG.fdic_order | FDIC Order | evaluative | SEC_10K, SEC_ENFORCEMENT | SEC_10K | regulatory_count | F5, F7 | keep | |
| LITIGATION.REGULATORY.fda_warning | LIT.REG.fda_warning | FDA Warning Letter | evaluative | SEC_10K, SEC_ENFORCEMENT | SEC_10K | regulatory_count | F5, F7 | keep | |
| LITIGATION.REGULATORY.foreign_gov | LIT.REG.foreign_gov | Foreign Government Action | evaluative | SEC_10K, SEC_ENFORCEMENT | SEC_10K | regulatory_count | F5, F7 | keep | |
| LITIGATION.REGULATORY.state_action | LIT.REG.state_action | State Regulatory Action | evaluative | SEC_10K, SEC_ENFORCEMENT | SEC_10K | regulatory_count | F5, F7 | keep | |
| LITIGATION.EMPLOYMENT.employment | LIT.OTHER.employment | Employment Litigation | evaluative | SEC_10K | SEC_10K | regulatory_count | F1 | needs_work | field_key should be employment_litigation_count |
| LITIGATION.EMPLOYMENT.whistleblower | LIT.OTHER.whistleblower | Whistleblower Actions | evaluative | SEC_10K | SEC_10K | whistleblower_count | F1 | keep | |
| LITIGATION.COMMERCIAL.antitrust | LIT.OTHER.antitrust | Antitrust Litigation | evaluative | SEC_10K | SEC_10K | regulatory_count | F1 | needs_work | field_key should be antitrust_count |
| LITIGATION.COMMERCIAL.contract | LIT.OTHER.contract | Contract Disputes | evaluative | SEC_10K | SEC_10K | regulatory_count | F1 | needs_work | field_key should be contract_litigation_count |
| LITIGATION.COMMERCIAL.ip | LIT.OTHER.ip | Intellectual Property | evaluative | SEC_10K | SEC_10K | regulatory_count | F1 | needs_work | field_key should be ip_litigation_count |
| LITIGATION.COMMERCIAL.trade_secret | LIT.OTHER.trade_secret | Trade Secret | evaluative | SEC_10K | SEC_10K | regulatory_count | F1 | needs_work | field_key should be trade_secret_count |
| LITIGATION.COMMERCIAL.product | LIT.OTHER.product | Product Liability | evaluative | SEC_10K | SEC_10K | regulatory_count | F1 | needs_work | field_key should be product_liability_count |
| LITIGATION.COMMERCIAL.cyber_breach | LIT.OTHER.cyber_breach | Cyber Breach Litigation | evaluative | SEC_10K | SEC_10K | regulatory_count | F1 | needs_work | field_key should be cyber_breach_count |
| LITIGATION.COMMERCIAL.foreign_suit | LIT.OTHER.foreign_suit | Foreign Suit | evaluative | SEC_10K | SEC_10K | regulatory_count | F1 | keep | |
| LITIGATION.COMMERCIAL.gov_contract | LIT.OTHER.gov_contract | Government Contract Dispute | evaluative | SEC_10K | SEC_10K | regulatory_count | F1 | keep | |
| LITIGATION.COMMERCIAL.environmental | LIT.OTHER.environmental | Environmental Litigation | evaluative | SEC_10K | SEC_10K | regulatory_count | F1 | keep | |
| LITIGATION.AGGREGATE.aggregate | LIT.OTHER.aggregate | Aggregate Litigation Load | evaluative | SEC_10K | SEC_10K | active_matter_count | F1 | keep | |
| LITIGATION.AGGREGATE.class_action | LIT.OTHER.class_action | Non-Securities Class Actions | evaluative | SEC_10K | SEC_10K | regulatory_count | F1 | needs_work | field_key should be class_action_count |
| LITIGATION.AGGREGATE.bankruptcy | LIT.OTHER.bankruptcy | Bankruptcy-Related Claims | evaluative | SEC_10K | SEC_10K | regulatory_count | F1 | keep | |

### Consolidation Opportunities

1. **LIT.SCA.active / STOCK.LIT.existing_action** — Both check for active securities class actions. The STOCK version adds F2 factor. Merge into one LITIGATION.SECURITIES check with both F1 and F2 factors.
2. **LIT.REG.wells_notice / LIT.REG.sec_active** — Both relate to Wells Notices. `sec_active` name says "SEC Wells Notice," `wells_notice` is also Wells Notice. These may be duplicates or one is SEC-specific and the other is generic. Review for merge.
3. **Many LIT.OTHER.* checks share `regulatory_count` field_key** — 11 different litigation types all map to the same field_key, which means the data mapping is broken. Each needs its own field_key or the field_key needs to be a dict with type-specific counts.

### Missing Checks (Gaps)

| Proposed ID | Name | Priority | Why Needed | Data Source |
|---|---|---|---|---|
| LITIGATION.SECURITIES.derivative_risk_factors | Derivative Suit Risk Factor Assessment | HIGH | 5-category pre-filing risk model (board conflicts, M&A failures, egregtic behavior, Caremark, fraud). 2/3 of SCAs have derivative suits. Old system has detailed model. | SEC_10K, SCAC_SEARCH |
| LITIGATION.COMMERCIAL.litigation_funding | Litigation Funding Detection | LOW | Third-party litigation funders increase probability and severity. Old system: Module 6 Check 10.6. | NEWS, COURT_RECORDS |
| LITIGATION.REGULATORY.fda_form_483 | FDA Form 483 Observations | MEDIUM | Inspection findings, not just warning letters. Earlier signal. Old system: Module 6. | FDA, NEWS |
| LITIGATION.REGULATORY.congressional_inquiry | Congressional Inquiry | LOW | Letters from Congress = escalation signal. Old system: Module 6. | NEWS |
| LITIGATION.COMMERCIAL.npe_litigation | Non-Practicing Entity Exposure | LOW | Patent troll litigation exposure. Old system: Module 6 Section 7. | NEWS, COURT_RECORDS |
| LITIGATION.COMMERCIAL.ptab_challenges | PTAB Patent Challenges | LOW | Patent Trial and Appeal Board inter partes review. | NEWS |

### Section Data Acquisition Summary

| Data Source | Status | Notes |
|---|---|---|
| SCAC_SEARCH | Implemented | Primary for securities class action data |
| SEC_10K | Implemented | Item 3 legal proceedings, contingencies |
| SEC_8K | Implemented | Material events, Wells notices |
| SEC_ENFORCEMENT | Implemented | SEC litigation releases |
| COURT_RECORDS | NOT implemented | CourtListener/PACER for non-SCA litigation detail |
| FDA | NOT implemented | Form 483, MedWatch — needed for regulatory gaps |

---

## Part 5: MARKET Section

### What This Section Covers

The MARKET section analyzes **what the stock market is telling us about the company**. An underwriter reads this to evaluate stock price behavior, short selling signals, ownership structure, valuation metrics, and trading patterns. A >20% stock drop is the primary trigger for securities class actions. Short interest >20% signals that sophisticated investors are betting against the company. This section feeds heavily into the HAZ-SCA (securities class action) hazard assessment.

### Category Definitions

| Category | Description |
|---|---|
| **MARKET.PRICE** | Stock price levels, returns, drops, attribution, recovery, technical indicators, delisting risk |
| **MARKET.SHORT** | Short interest position, trend, short seller reports |
| **MARKET.OWNERSHIP** | Ownership structure, concentration, activist presence |
| **MARKET.SENTIMENT** | Analyst coverage, momentum, consensus |
| **MARKET.VALUATION** | P/E ratio, EV/EBITDA, premium/discount, PEG ratio |
| **MARKET.TRADING** | Trading liquidity, volume patterns, options activity |

Note: STOCK.INSIDER.* and STOCK.LIT.* checks have been moved to GOVERNANCE.INSIDER and LITIGATION.SECURITIES respectively. STOCK.PATTERN.* checks stay here as they are price-derived market patterns.

### Check Reclassification Table

| New ID | Old ID | Name | Type | Data Sources | Fallback Chain | Field Key | Factors | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| MARKET.PRICE.recent_drop_alert | STOCK.PRICE.recent_drop_alert | Recent Drop Alert | evaluative | MARKET_PRICE | MARKET_PRICE | decline_from_high | F2 | keep | |
| MARKET.PRICE.chart_comparison | STOCK.PRICE.chart_comparison | Chart Comparison | evaluative | MARKET_PRICE | MARKET_PRICE | decline_from_high | F2 | keep | |
| MARKET.PRICE.position | STOCK.PRICE.position | Stock Price Position | evaluative | MARKET_PRICE | MARKET_PRICE | decline_from_high | F2 | keep | |
| MARKET.PRICE.returns_multi_horizon | STOCK.PRICE.returns_multi_horizon | Returns Multi Horizon | evaluative | MARKET_PRICE | MARKET_PRICE | returns_1y | F2 | keep | |
| MARKET.PRICE.attribution | STOCK.PRICE.attribution | Price Attribution | evaluative | MARKET_PRICE | MARKET_PRICE | decline_from_high | F2 | keep | |
| MARKET.PRICE.peer_relative | STOCK.PRICE.peer_relative | Peer Relative Performance | evaluative | MARKET_PRICE | MARKET_PRICE | returns_1y | F2 | keep | |
| MARKET.PRICE.single_day_events | STOCK.PRICE.single_day_events | Single Day Events | evaluative | MARKET_PRICE, SEC_8K | MARKET_PRICE | single_day_drops_count | F2 | keep | |
| MARKET.PRICE.recovery | STOCK.PRICE.recovery | Recovery Analysis | evaluative | MARKET_PRICE | MARKET_PRICE | returns_1y | F2 | keep | |
| MARKET.PRICE.technical | STOCK.PRICE.technical | Technical Indicators | evaluative | MARKET_PRICE | MARKET_PRICE | volatility_90d | F2 | keep | |
| MARKET.PRICE.delisting_risk | STOCK.PRICE.delisting_risk | Delisting Risk | evaluative | MARKET_PRICE, SEC_8K | MARKET_PRICE | current_price | F2 | keep | |
| MARKET.PRICE.event_collapse | STOCK.PATTERN.event_collapse | Event Collapse Pattern | pattern | MARKET_PRICE | MARKET_PRICE | single_day_drops_count | F2 | keep | |
| MARKET.PRICE.informed_trading | STOCK.PATTERN.informed_trading | Informed Trading Pattern | pattern | SEC_FORM4, MARKET_PRICE | SEC_FORM4 | insider_net_activity | F4 | keep | |
| MARKET.PRICE.cascade | STOCK.PATTERN.cascade | Price Cascade Pattern | pattern | MARKET_PRICE, MARKET_SHORT | MARKET_PRICE | decline_from_high | F2 | keep | |
| MARKET.PRICE.peer_divergence | STOCK.PATTERN.peer_divergence | Peer Divergence Pattern | pattern | MARKET_PRICE | MARKET_PRICE | returns_1y | F2 | keep | |
| MARKET.PRICE.death_spiral | STOCK.PATTERN.death_spiral | Death Spiral Pattern | pattern | MARKET_PRICE, MARKET_SHORT, SEC_10K | MARKET_PRICE | decline_from_high | F2 | keep | |
| MARKET.PRICE.short_attack | STOCK.PATTERN.short_attack | Short Attack Pattern | pattern | MARKET_SHORT, SEC_8K | MARKET_SHORT | short_interest_pct | F2 | keep | |
| MARKET.SHORT.position | STOCK.SHORT.position | Short Interest Position | evaluative | MARKET_SHORT | MARKET_SHORT | short_interest_pct | F2 | keep | |
| MARKET.SHORT.trend | STOCK.SHORT.trend | Short Interest Trend | evaluative | MARKET_SHORT | MARKET_SHORT | short_interest_ratio | F2 | keep | |
| MARKET.SHORT.report | STOCK.SHORT.report | Short Seller Report | evaluative | MARKET_SHORT | MARKET_SHORT | short_interest_pct | F2 | keep | |
| MARKET.OWNERSHIP.structure | STOCK.OWN.structure | Ownership Structure | evaluative | SEC_DEF14A, SEC_13DG | SEC_DEF14A | institutional_pct | F4 | keep | |
| MARKET.OWNERSHIP.concentration | STOCK.OWN.concentration | Ownership Concentration | display | SEC_DEF14A | SEC_DEF14A | institutional_pct | — | keep | |
| MARKET.OWNERSHIP.activist | STOCK.OWN.activist | Activist Presence | display | SEC_DEF14A | SEC_DEF14A | activist_present | — | keep | |
| MARKET.SENTIMENT.coverage | STOCK.ANALYST.coverage | Analyst Coverage | display | MARKET_PRICE | MARKET_PRICE | beat_rate | — | needs_work | field_key should be analyst_count |
| MARKET.SENTIMENT.momentum | STOCK.ANALYST.momentum | Price Momentum | display | MARKET_PRICE | MARKET_PRICE | beat_rate | — | needs_work | field_key should be price_momentum |
| MARKET.VALUATION.pe_ratio | STOCK.VALUATION.pe_ratio | P/E Ratio | evaluative | MARKET_PRICE, SEC_10K | MARKET_PRICE | current_price | F2 | needs_work | field_key should be pe_ratio |
| MARKET.VALUATION.ev_ebitda | STOCK.VALUATION.ev_ebitda | EV/EBITDA | evaluative | MARKET_PRICE, SEC_10K | MARKET_PRICE | current_price | F2 | needs_work | field_key should be ev_ebitda |
| MARKET.VALUATION.premium_discount | STOCK.VALUATION.premium_discount | Valuation Premium/Discount | evaluative | MARKET_PRICE, SEC_10K | MARKET_PRICE | returns_1y | F2 | needs_work | field_key should be valuation_premium |
| MARKET.VALUATION.peg_ratio | STOCK.VALUATION.peg_ratio | PEG Ratio | evaluative | MARKET_PRICE, SEC_10K | MARKET_PRICE | current_price | F2 | needs_work | field_key should be peg_ratio |
| MARKET.TRADING.liquidity | STOCK.TRADE.liquidity | Trading Liquidity | display | MARKET_PRICE | MARKET_PRICE | current_price | — | needs_work | field_key should be avg_daily_volume |
| MARKET.TRADING.volume_patterns | STOCK.TRADE.volume_patterns | Volume Patterns | display | MARKET_PRICE | MARKET_PRICE | adverse_event_count | — | needs_work | field_key wrong |
| MARKET.TRADING.options | STOCK.TRADE.options | Options Activity | display | MARKET_PRICE | MARKET_PRICE | adverse_event_count | — | needs_work | field_key wrong; data source needs options data |

### Consolidation Opportunities

1. **STOCK.PRICE.chart_comparison / STOCK.PRICE.peer_relative / STOCK.PATTERN.peer_divergence** — All three compare the company's stock to peers/sector. chart_comparison is sector-relative, peer_relative is peer-relative, peer_divergence is a pattern. Keep all three but ensure distinct purposes.
2. **STOCK.PRICE.position / STOCK.PRICE.returns_multi_horizon** — Some overlap in measuring how far the stock has fallen. Position uses 52-week high/low; returns uses multi-period returns. Distinct enough to keep both.
3. **STOCK.VALUATION.* checks** — All 4 use wrong field_keys (current_price, returns_1y). Each needs its own valuation-specific field_key.
4. **STOCK.TRADE.volume_patterns / STOCK.TRADE.options** — Both use `adverse_event_count` as field_key, which is completely wrong for both.

### Missing Checks (Gaps)

| Proposed ID | Name | Priority | Why Needed | Data Source |
|---|---|---|---|---|
| MARKET.PRICE.death_cross | Death Cross Detection | MEDIUM | 50-day MA crosses below 200-day MA. Classic bearish technical signal. Old system: Module 2. | MARKET_PRICE |
| MARKET.PRICE.gap_down | Gap-Down Analysis | MEDIUM | Single-day gaps >5%. Key litigation trigger event. Old system: B.5.1. | MARKET_PRICE |
| MARKET.SHORT.days_to_cover | Days to Cover | MEDIUM | Short interest / average daily volume. Measures short squeeze risk. Old system: Module 2. | MARKET_SHORT, MARKET_PRICE |
| MARKET.TRADING.block_trades | Block Trade Analysis | LOW | Institutional selling patterns (large blocks). Old system: Module 2. | MARKET_PRICE |
| MARKET.TRADING.options_activity | Unusual Options Activity | LOW | Unusual put buying as predictor of future drops. Old system: Module 2. | MARKET_PRICE |
| MARKET.SHORT.short_squeeze_risk | Short Squeeze Risk | LOW | Assessment of squeeze potential from short interest + catalysts. | MARKET_SHORT, MARKET_PRICE |

### Section Data Acquisition Summary

| Data Source | Status | Notes |
|---|---|---|
| MARKET_PRICE | Implemented | yfinance provides price, returns, volume, beta, volatility |
| MARKET_SHORT | Implemented | Short interest from yfinance |
| SEC_DEF14A | Implemented | Ownership tables |
| SEC_13DG | Implemented | 13D/13G filings for activist/ownership |
| SEC_FORM4 | Implemented | For informed trading pattern |
| SEC_8K | Implemented | For single-day event attribution |

---

## Part 6: DISCLOSURE Section

### What This Section Covers

The DISCLOSURE section analyzes **what the company's own filings reveal through language, tone, and changes over time**. An underwriter reads this to detect disclosure quality issues, narrative inconsistencies, risk factor evolution, and audit-related red flags. NLP-driven checks detect what management is trying to hide or obfuscate — increasing readability difficulty (Fog Index), shifting tone, adding new risk factors, or changing language to qualify/hedge earlier statements. These are leading indicators of future misrepresentation claims.

### Category Definitions

| Category | Description |
|---|---|
| **DISCLOSURE.RISK_FACTOR** | Risk factor analysis: count changes, new additions, litigation-specific new factors, regulatory new factors |
| **DISCLOSURE.NARRATIVE** | MD&A and narrative analysis: readability, tone shifts, hedging language, forward-looking statement changes, narrative coherence |
| **DISCLOSURE.FILING** | Filing mechanics: late filings, timing shifts, whistleblower language |
| **DISCLOSURE.AUDIT** | Critical Audit Matters (CAM) changes |
| **DISCLOSURE.QUALITY** | Disclosure quality assessments: risk factor evolution, MDA depth, non-GAAP reconciliation, segment consistency, related party completeness |

### Check Reclassification Table

| New ID | Old ID | Name | Type | Data Sources | Fallback Chain | Field Key | Factors | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| DISCLOSURE.RISK_FACTOR.count_change | NLP.RISK.factor_count_change | Risk Factor Count Change YoY | evaluative | SEC_10K | SEC_10K | N/A | F3 | keep | |
| DISCLOSURE.RISK_FACTOR.new_factors | NLP.RISK.new_risk_factors | New Risk Factors Added This Year | evaluative | SEC_10K | SEC_10K | N/A | F3 | keep | |
| DISCLOSURE.RISK_FACTOR.litigation_new | NLP.RISK.litigation_risk_factor_new | New Litigation-Specific Risk Factor | evaluative | SEC_10K | SEC_10K | N/A | F1, F3 | keep | |
| DISCLOSURE.RISK_FACTOR.regulatory_new | NLP.RISK.regulatory_risk_factor_new | New Regulatory Risk Factor | evaluative | SEC_10K | SEC_10K | N/A | F3 | keep | |
| DISCLOSURE.NARRATIVE.mda_readability_change | NLP.MDA.readability_change | MD&A Readability Change (Fog Index YoY) | evaluative | SEC_10K | SEC_10K | N/A | F3 | keep | |
| DISCLOSURE.NARRATIVE.mda_tone_shift | NLP.MDA.tone_shift | MD&A Negative Tone Shift | evaluative | SEC_10K | SEC_10K | N/A | F3, F5 | keep | |
| DISCLOSURE.NARRATIVE.mda_readability_absolute | NLP.MDA.readability_absolute | Current MD&A Fog Index Level | display | SEC_10K | SEC_10K | N/A | — | keep | |
| DISCLOSURE.NARRATIVE.mda_tone_absolute | NLP.MDA.tone_absolute | Current MD&A Negative Tone Ratio | display | SEC_10K | SEC_10K | N/A | — | keep | |
| DISCLOSURE.NARRATIVE.hedging_language | NLP.DISCLOSURE.hedging_language_increase | Increase in Hedging/Qualifying Language | evaluative | SEC_10K | SEC_10K | N/A | — | keep | |
| DISCLOSURE.NARRATIVE.forward_looking_decrease | NLP.DISCLOSURE.forward_looking_decrease | Decrease in Forward-Looking Statements | evaluative | SEC_10K | SEC_10K | N/A | — | keep | |
| DISCLOSURE.NARRATIVE.10k_vs_earnings | FWRD.NARRATIVE.10k_vs_earnings | 10-K vs Earnings Call Narrative | evaluative | SEC_10K, SEC_8K | SEC_10K | N/A | — | keep | |
| DISCLOSURE.NARRATIVE.investor_vs_sec | FWRD.NARRATIVE.investor_vs_sec | Investor vs SEC Filing Narrative | evaluative | SEC_10K, SEC_8K | SEC_10K | N/A | — | keep | |
| DISCLOSURE.NARRATIVE.analyst_skepticism | FWRD.NARRATIVE.analyst_skepticism | Analyst Skepticism | evaluative | SEC_10K, SEC_8K | SEC_10K | N/A | — | keep | |
| DISCLOSURE.NARRATIVE.short_thesis | FWRD.NARRATIVE.short_thesis | Short Thesis Narrative | evaluative | SEC_10K, SEC_8K | SEC_10K | N/A | — | keep | |
| DISCLOSURE.NARRATIVE.auditor_cams | FWRD.NARRATIVE.auditor_cams | Auditor CAMs Narrative | evaluative | SEC_10K, SEC_8K | SEC_10K | N/A | — | keep | |
| DISCLOSURE.NARRATIVE.narrative_coherence | FWRD.NARRATIVE.narrative_coherence_composite | Narrative Coherence Composite | composite | SEC_10K, SEC_8K | SEC_10K | N/A | — | keep | |
| DISCLOSURE.FILING.late_filing | NLP.FILING.late_filing | Filing Deadline Missed (NT Filing) | evaluative | SEC_10K | SEC_10K | N/A | F3 | keep | |
| DISCLOSURE.FILING.timing_change | NLP.FILING.filing_timing_change | Filing Date Shifted vs Prior Year | display | SEC_10K | SEC_10K | N/A | — | keep | |
| DISCLOSURE.FILING.whistleblower_language | NLP.WHISTLE.language_detected | Whistleblower/Qui Tam Language in Filings | evaluative | SEC_10K | SEC_10K | N/A | F1, F3 | keep | |
| DISCLOSURE.FILING.internal_investigation | NLP.WHISTLE.internal_investigation | Internal Investigation Language Detected | evaluative | SEC_10K | SEC_10K | N/A | F3 | keep | |
| DISCLOSURE.AUDIT.cam_changes | NLP.CAM.changes | Critical Audit Matters Changed From Prior Year | evaluative | SEC_10K | SEC_10K | N/A | F3 | keep | |
| DISCLOSURE.QUALITY.risk_factor_evolution | FWRD.DISC.risk_factor_evolution | Risk Factor Evolution | evaluative | SEC_10K | SEC_10K | N/A | — | keep | |
| DISCLOSURE.QUALITY.mda_depth | FWRD.DISC.mda_depth | MD&A Depth Assessment | evaluative | SEC_10K | SEC_10K | N/A | — | keep | |
| DISCLOSURE.QUALITY.non_gaap_reconciliation | FWRD.DISC.non_gaap_reconciliation | Non-GAAP Reconciliation Quality | evaluative | SEC_10K | SEC_10K | N/A | — | keep | |
| DISCLOSURE.QUALITY.segment_consistency | FWRD.DISC.segment_consistency | Segment Reporting Consistency | evaluative | SEC_10K | SEC_10K | N/A | — | keep | |
| DISCLOSURE.QUALITY.related_party_completeness | FWRD.DISC.related_party_completeness | Related Party Completeness | evaluative | SEC_10K | SEC_10K | N/A | — | keep | |
| DISCLOSURE.QUALITY.metric_consistency | FWRD.DISC.metric_consistency | Metric Consistency | evaluative | SEC_10K | SEC_10K | N/A | — | keep | |
| DISCLOSURE.QUALITY.guidance_methodology | FWRD.DISC.guidance_methodology | Guidance Methodology Quality | evaluative | SEC_10K | SEC_10K | N/A | — | keep | |
| DISCLOSURE.QUALITY.sec_comment_letters | FWRD.DISC.sec_comment_letters | SEC Comment Letter Response Quality | evaluative | SEC_10K | SEC_10K | N/A | — | keep | |
| DISCLOSURE.QUALITY.composite | FWRD.DISC.disclosure_quality_composite | Disclosure Quality Composite | composite | SEC_10K | SEC_10K | N/A | — | keep | |

### Consolidation Opportunities

1. **NLP.FILING.late_filing / GOV.EFFECT.late_filing** — Both check for late filings. The NLP version is text-detection based; the GOV.EFFECT version is governance-effectiveness. GOV.EFFECT.late_filing moved to GOVERNANCE.OVERSIGHT. Keep both if they serve different analytical purposes (detection vs governance impact).
2. **FWRD.DISC.sec_comment_letters / FIN.ACCT.sec_correspondence** — Both relate to SEC comment letters. One focuses on disclosure quality (response adequacy); the other on financial integrity. Review for potential merge.
3. **NLP.MDA.readability_change / NLP.MDA.readability_absolute** — Change vs level. Both needed — change is the signal, absolute is context.
4. **NLP.MDA.tone_shift / NLP.MDA.tone_absolute** — Same pattern: change vs level. Both needed.

### Missing Checks (Gaps)

| Proposed ID | Name | Priority | Why Needed | Data Source |
|---|---|---|---|---|
| DISCLOSURE.QUALITY.undisclosed_related_party | Undisclosed Related Party Discovery | LOW | Proactive discovery of undisclosed related parties through web research. Old system: Module 6 Check 10.9. | NEWS, SEC_10K |

The DISCLOSURE section is relatively well-covered in the current system. The NLP checks and FWRD.DISC/FWRD.NARRATIVE checks provide good coverage of disclosure quality and narrative analysis.

### Section Data Acquisition Summary

| Data Source | Status | Notes |
|---|---|---|
| SEC_10K | Implemented | Primary source — all disclosure checks parse 10-K text |
| SEC_8K | Implemented | Earnings call transcripts, press releases for narrative comparison |

---

## Part 7: FORWARD Section

### What This Section Covers

The FORWARD section identifies **what could go wrong during the policy period**. An underwriter reads this to evaluate upcoming catalysts (earnings dates, debt maturities, regulatory decisions), early warning signals from alternative data sources (employee reviews, customer complaints, social sentiment), and macroeconomic/industry headwinds. This is the "crystal ball" section — it doesn't measure what has happened, but what is likely to happen. Alternative data signals (Glassdoor, LinkedIn, CFPB complaints) appear months to years before formal litigation or regulatory action.

### Category Definitions

| Category | Description |
|---|---|
| **FORWARD.CATALYST** | Known upcoming events: earnings, debt maturities, regulatory decisions, M&A closings, shareholder meetings |
| **FORWARD.SIGNAL** | Alternative data early warning signals: employee reviews, customer complaints, social sentiment, hiring patterns |
| **FORWARD.ENVIRONMENT** | Macro/industry headwinds: sector performance, peer issues, interest rates, FX, trade policy, geopolitical |

### Check Reclassification Table

| New ID | Old ID | Name | Type | Data Sources | Fallback Chain | Field Key | Factors | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| FORWARD.CATALYST.earnings_calendar | FWRD.EVENT.earnings_calendar | Upcoming Earnings Date | evaluative | MARKET_PRICE, SEC_8K | MARKET_PRICE | N/A | F6 | keep | |
| FORWARD.CATALYST.guidance_risk | FWRD.EVENT.guidance_risk | Guidance Risk | evaluative | SEC_8K | SEC_8K | N/A | F6 | keep | |
| FORWARD.CATALYST.catalyst_dates | FWRD.EVENT.catalyst_dates | Catalyst Dates | display | SEC_10K | SEC_10K | N/A | — | keep | |
| FORWARD.CATALYST.debt_maturity | FWRD.EVENT.debt_maturity | Debt Maturity 12mo | evaluative | SEC_10K | SEC_10K | N/A | F3 | keep | |
| FORWARD.CATALYST.covenant_test | FWRD.EVENT.covenant_test | Covenant Test Dates | evaluative | SEC_10K | SEC_10K | N/A | F3 | keep | |
| FORWARD.CATALYST.lockup_expiry | FWRD.EVENT.lockup_expiry | Lock-up Expiration | display | SEC_10K | SEC_10K | N/A | — | keep | |
| FORWARD.CATALYST.warrant_expiry | FWRD.EVENT.warrant_expiry | Warrant Expiration | display | SEC_10K | SEC_10K | N/A | — | keep | |
| FORWARD.CATALYST.contract_renewal | FWRD.EVENT.contract_renewal | Contract Renewal Dates | evaluative | SEC_10K | SEC_10K | N/A | F9 | keep | |
| FORWARD.CATALYST.regulatory_decision | FWRD.EVENT.regulatory_decision | Regulatory Decision Dates | evaluative | SEC_10K | SEC_10K | N/A | F5 | keep | |
| FORWARD.CATALYST.litigation_milestone | FWRD.EVENT.litigation_milestone | Litigation Milestones | evaluative | SCAC_SEARCH, SEC_10K | SCAC_SEARCH | N/A | F1 | keep | |
| FORWARD.CATALYST.shareholder_mtg | FWRD.EVENT.shareholder_mtg | Shareholder Meeting Date | display | SEC_DEF14A | SEC_DEF14A | N/A | — | keep | |
| FORWARD.CATALYST.ma_closing | FWRD.EVENT.ma_closing | M&A Closing Date | evaluative | SEC_8K | SEC_8K | N/A | F8 | keep | |
| FORWARD.CATALYST.synergy | FWRD.EVENT.synergy | Synergy Realization | evaluative | SEC_8K | SEC_8K | N/A | F8 | keep | |
| FORWARD.CATALYST.customer_retention | FWRD.EVENT.customer_retention | Customer Retention Risk | evaluative | SEC_10K, SEC_8K | SEC_10K | N/A | F10 | keep | |
| FORWARD.CATALYST.employee_retention | FWRD.EVENT.employee_retention | Employee Retention Risk | evaluative | SEC_10K, SEC_8K | SEC_10K | N/A | F10 | keep | |
| FORWARD.CATALYST.integration | FWRD.EVENT.integration | Integration Risk | evaluative | SEC_10K, SEC_8K | SEC_10K | N/A | F10 | keep | |
| FORWARD.CATALYST.proxy_deadline | FWRD.EVENT.proxy_deadline | Proxy Deadline | evaluative | SEC_10K, SEC_8K | SEC_10K | N/A | F10 | keep | |
| FORWARD.CATALYST.biotech_19 | FWRD.EVENT.19-BIOT | Biotech Catalyst 19 | evaluative | SEC_10K, SEC_8K | SEC_10K | N/A | F10 | needs_work | Name is generic "19-Biot" — needs meaningful name |
| FORWARD.CATALYST.biotech_20 | FWRD.EVENT.20-BIOT | Biotech Catalyst 20 | evaluative | SEC_10K, SEC_8K | SEC_10K | N/A | F10 | needs_work | Name is generic "20-Biot" — needs meaningful name |
| FORWARD.CATALYST.biotech_21 | FWRD.EVENT.21-BIOT | Biotech Catalyst 21 | evaluative | SEC_10K, SEC_8K | SEC_10K | N/A | F10 | needs_work | Name is generic "21-Biot" — needs meaningful name |
| FORWARD.CATALYST.healthcare_22 | FWRD.EVENT.22-HLTH | Healthcare Catalyst 22 | evaluative | SEC_10K, SEC_8K | SEC_10K | N/A | F10 | needs_work | Name is generic "22-Hlth" — needs meaningful name |
| FORWARD.SIGNAL.glassdoor_sentiment | FWRD.WARN.glassdoor_sentiment | Glassdoor Sentiment | evaluative | GLASSDOOR | GLASSDOOR | N/A | F7 | rename | Data source corrected SEC_10K->GLASSDOOR; factor corrected F10->F7 |
| FORWARD.SIGNAL.indeed_reviews | FWRD.WARN.indeed_reviews | Indeed Reviews | evaluative | INDEED | INDEED | N/A | F7 | rename | Data source corrected; factor corrected F10->F7 |
| FORWARD.SIGNAL.blind_posts | FWRD.WARN.blind_posts | Blind Posts | evaluative | BLIND | BLIND | N/A | F7 | rename | Data source corrected; factor corrected F10->F7 |
| FORWARD.SIGNAL.linkedin_headcount | FWRD.WARN.linkedin_headcount | LinkedIn Headcount Trends | evaluative | LINKEDIN | LINKEDIN | N/A | F7 | rename | Data source corrected; factor corrected F10->F7 |
| FORWARD.SIGNAL.linkedin_departures | FWRD.WARN.linkedin_departures | LinkedIn Departures | evaluative | LINKEDIN | LINKEDIN | N/A | F7 | rename | Data source corrected; factor corrected F10->F7 |
| FORWARD.SIGNAL.g2_reviews | FWRD.WARN.g2_reviews | G2 Reviews | evaluative | G2 | G2 | N/A | F9 | rename | Data source corrected; factor corrected F10->F9 |
| FORWARD.SIGNAL.trustpilot_trend | FWRD.WARN.trustpilot_trend | Trustpilot Trend | evaluative | TRUSTPILOT | TRUSTPILOT | N/A | F9 | rename | Data source corrected; factor corrected F10->F9 |
| FORWARD.SIGNAL.app_ratings | FWRD.WARN.app_ratings | App Store Ratings | evaluative | APP_STORE | APP_STORE | N/A | F9 | rename | Data source corrected; factor corrected F10->F9 |
| FORWARD.SIGNAL.cfpb_complaints | FWRD.WARN.cfpb_complaints | CFPB Complaints | evaluative | CFPB | CFPB | N/A | F9 | rename | Data source corrected; factor corrected F10->F9 |
| FORWARD.SIGNAL.fda_medwatch | FWRD.WARN.fda_medwatch | FDA MedWatch Adverse Events | evaluative | FDA | FDA | N/A | F9 | rename | Data source corrected; factor corrected F10->F9 |
| FORWARD.SIGNAL.nhtsa_complaints | FWRD.WARN.nhtsa_complaints | NHTSA Complaints | evaluative | NHTSA | NHTSA | N/A | F9 | rename | Data source corrected; factor corrected F10->F9 |
| FORWARD.SIGNAL.social_sentiment | FWRD.WARN.social_sentiment | Social Sentiment | evaluative | NEWS | NEWS | N/A | F2 | rename | Data source corrected; factor corrected F10->F2 |
| FORWARD.SIGNAL.journalism_activity | FWRD.WARN.journalism_activity | Journalism Activity | evaluative | NEWS | NEWS | N/A | F2 | rename | Data source corrected; factor corrected F10->F2 |
| FORWARD.SIGNAL.whistleblower_exposure | FWRD.WARN.whistleblower_exposure | Whistleblower Exposure | evaluative | NEWS, SEC_10K | NEWS | N/A | F1 | rename | Data source corrected; factor corrected F10->F1 |
| FORWARD.SIGNAL.job_posting_patterns | FWRD.WARN.job_posting_patterns | Job Posting Patterns | evaluative | LINKEDIN, NEWS | LINKEDIN | N/A | F7 | rename | Data source corrected; factor corrected F10->F7 |
| FORWARD.SIGNAL.compliance_hiring | FWRD.WARN.compliance_hiring | Compliance Hiring Surge | evaluative | LINKEDIN, NEWS | LINKEDIN | N/A | F7 | rename | Data source corrected; factor corrected F10->F7 |
| FORWARD.SIGNAL.legal_hiring | FWRD.WARN.legal_hiring | Legal Hiring Surge | evaluative | LINKEDIN, NEWS | LINKEDIN | N/A | F7 | rename | Data source corrected; factor corrected F10->F7 |
| FORWARD.SIGNAL.customer_churn_signals | FWRD.WARN.customer_churn_signals | Customer Churn Signals | evaluative | NEWS | NEWS | N/A | F9 | rename | Was FWRD.WARN; factor corrected F10->F9 |
| FORWARD.ENVIRONMENT.sector_performance | FWRD.MACRO.sector_performance | Sector Performance | evaluative | SEC_10K | SEC_10K | N/A | F9 | keep | |
| FORWARD.ENVIRONMENT.peer_issues | FWRD.MACRO.peer_issues | Peer Issues | evaluative | SEC_10K | SEC_10K | N/A | F9 | keep | |
| FORWARD.ENVIRONMENT.industry_consolidation | FWRD.MACRO.industry_consolidation | Industry Consolidation | evaluative | SEC_10K | SEC_10K | N/A | F9 | keep | |
| FORWARD.ENVIRONMENT.disruptive_tech | FWRD.MACRO.disruptive_tech | Disruptive Technology | evaluative | SEC_10K | SEC_10K | N/A | F9 | keep | |
| FORWARD.ENVIRONMENT.interest_rate | FWRD.MACRO.interest_rate_sensitivity | Interest Rate Sensitivity | evaluative | SEC_10K | SEC_10K | N/A | F9 | keep | |
| FORWARD.ENVIRONMENT.inflation | FWRD.MACRO.inflation_impact | Inflation Impact | evaluative | SEC_10K | SEC_10K | N/A | F9 | keep | |
| FORWARD.ENVIRONMENT.fx_exposure | FWRD.MACRO.fx_exposure | FX Exposure | evaluative | SEC_10K | SEC_10K | N/A | F9 | keep | |
| FORWARD.ENVIRONMENT.commodity | FWRD.MACRO.commodity_impact | Commodity Impact | evaluative | SEC_10K | SEC_10K | N/A | F9 | keep | |
| FORWARD.ENVIRONMENT.labor_market | FWRD.MACRO.labor_market | Labor Market | evaluative | SEC_10K | SEC_10K | N/A | F9 | keep | |
| FORWARD.ENVIRONMENT.regulatory_changes | FWRD.MACRO.regulatory_changes | Regulatory Changes | evaluative | SEC_10K | SEC_10K | N/A | F9 | keep | |
| FORWARD.ENVIRONMENT.legislative_risk | FWRD.MACRO.legislative_risk | Legislative Risk | evaluative | SEC_10K | SEC_10K | N/A | F9 | keep | |
| FORWARD.ENVIRONMENT.trade_policy | FWRD.MACRO.trade_policy | Trade Policy | evaluative | SEC_10K | SEC_10K | N/A | F9 | keep | |
| FORWARD.ENVIRONMENT.geopolitical | FWRD.MACRO.geopolitical_exposure | Geopolitical Exposure | evaluative | SEC_10K | SEC_10K | N/A | F9 | keep | |
| FORWARD.ENVIRONMENT.supply_chain | FWRD.MACRO.supply_chain_disruption | Supply Chain Disruption | evaluative | SEC_10K | SEC_10K | N/A | F9 | keep | |
| — | FWRD.MACRO.climate_transition_risk | Climate Transition Risk | — | — | — | — | — | retire | ESG not relevant per user directive |

### Consolidation Opportunities

1. **FWRD.WARN.glassdoor_sentiment / FWRD.WARN.indeed_reviews / FWRD.WARN.blind_posts** — All three are employee review signals from different platforms. Could be consolidated into a single "Employee Sentiment Composite" check, but keeping separate allows platform-specific thresholds.
2. **FWRD.WARN.linkedin_headcount / FWRD.WARN.linkedin_departures** — Both use LinkedIn data but measure different things (headcount trend vs departures). Keep separate.
3. **FWRD.WARN.job_posting_patterns / FWRD.WARN.compliance_hiring / FWRD.WARN.legal_hiring** — All three analyze job postings. Could merge into one "Hiring Pattern Analysis" with sub-categories, but keeping separate allows distinct thresholds (compliance hiring = different signal than legal hiring).
4. **FWRD.EVENT.19-BIOT / 20-BIOT / 21-BIOT / 22-HLTH** — Four industry-specific catalyst checks with cryptic names. Need meaningful names or merge into a single industry-catalyst framework.

### Missing Checks (Gaps)

| Proposed ID | Name | Priority | Why Needed | Data Source |
|---|---|---|---|---|
| FORWARD.SIGNAL.pubpeer_comments | PubPeer Scientific Integrity | HIGH | PubPeer comments on company-sponsored research. SAVA case showed 3+ year lead time. Old system: Module 6 Section 6. | NEWS |
| FORWARD.SIGNAL.retraction_watch | Retraction Watch Monitoring | HIGH | Paper retractions for life sciences companies. Old system: Module 6 Section 6. | NEWS |
| FORWARD.SIGNAL.kol_sentiment | Key Opinion Leader Sentiment | MEDIUM | KOL sentiment at conferences for life sciences. Old system: Module 6 Section 6. | NEWS |
| FORWARD.SIGNAL.clinical_trial_status | Clinical Trial Status Monitoring | MEDIUM | ClinicalTrials.gov status changes. Old system: Module 6 Section 6. | NEWS |
| FORWARD.SIGNAL.citizen_petition | FDA Citizen Petition | MEDIUM | Citizen petitions to FDA questioning data. SAVA precedent. Old system: Module 6. | NEWS, FDA |
| FORWARD.SIGNAL.glassdoor_fraud_keywords | Glassdoor Fraud Keyword Search | MEDIUM | Specific fraud-related keywords in reviews: "cooking books", "pressure to meet numbers". Old system: Module 6 Section 3. | GLASSDOOR |
| FORWARD.SIGNAL.review_surge_detection | Employee Review Surge Detection | MEDIUM | Sudden increase in negative reviews across platforms. Old system: Module 6. | GLASSDOOR, INDEED |
| FORWARD.SIGNAL.ceo_approval_trend | CEO Approval Rating Trend | LOW | Drop >20% = red flag. Old system: Module 6 Section 3. | GLASSDOOR |
| FORWARD.SIGNAL.linkedin_department_departures | LinkedIn Department-Level Departures | MEDIUM | Accounting/legal departures = red flag vs sales departures = less concerning. Old system: Module 6. | LINKEDIN |
| FORWARD.SIGNAL.web_traffic_trend | Web Traffic / App Download Trends | LOW | SimilarWeb/Sensor Tower data. Old system: Module 6 Section 4. | NEWS |
| FORWARD.SIGNAL.union_organizing | Union Organizing / NLRB Filings | LOW | Labor risk signal. Old system: Module 6 Check 10.5. | NEWS |

### Section Data Acquisition Summary

| Data Source | Status | Notes |
|---|---|---|
| SEC_10K | Implemented | For ENVIRONMENT checks, catalyst dates |
| SEC_8K | Implemented | Earnings, M&A events |
| SEC_DEF14A | Implemented | Shareholder meeting dates |
| SCAC_SEARCH | Implemented | Litigation milestones |
| MARKET_PRICE | Implemented | Earnings calendar |
| GLASSDOOR | NOT implemented | Playwright-based scraping needed. Critical for employee signals. |
| INDEED | NOT implemented | Playwright-based scraping needed. |
| BLIND | NOT implemented | Web search proxy only. |
| LINKEDIN | NOT implemented | Playwright-based scraping needed. Critical for departure/hiring signals. |
| APP_STORE | NOT implemented | Fetch-based. Needed for consumer-facing companies. |
| TRUSTPILOT | NOT implemented | Fetch-based. |
| G2 | NOT implemented | Fetch-based. Needed for SaaS companies. |
| NHTSA | NOT implemented | API available. Needed for auto companies. |
| FDA | NOT implemented | FAERS database. Needed for pharma/medical device. |
| CFPB | NOT implemented | Database available. Needed for financial services. |
| NEWS | Implemented | Brave Search covers social sentiment, journalism. |

---

## Summary Statistics

### Check Disposition by Section

| Section | Keep | Rename | Retire | Merge | Needs Work | Total |
|---|---|---|---|---|---|---|
| COMPANY | 23 | 16 | 1 | 0 | 4 | 44 |
| FINANCIAL | 38 | 9 | 0 | 2 | 16 | 65 |
| GOVERNANCE | 48 | 0 | 3 | 2 | 30 | 83 |
| LITIGATION | 30 | 3 | 0 | 0 | 10 | 43 |
| MARKET | 17 | 0 | 0 | 0 | 14 | 31 |
| DISCLOSURE | 30 | 0 | 0 | 0 | 0 | 30 |
| FORWARD | 36 | 18 | 1 | 0 | 4 | 59 |
| **TOTAL** | **222** | **46** | **5** | **4** | **78** | **355** |

Note: 388 original checks - 355 mapped = 33 checks mapped to new homes from other prefixes (STOCK.INSIDER->GOVERNANCE, STOCK.LIT->LITIGATION, FWRD.WARN financial->FINANCIAL, GOV.EFFECT audit->FINANCIAL, etc.). The 5 retirements (3 EXEC.PROFILE duplicates + 1 ESG + 1 AI Claims) bring the effective check count to 383.

### Major Issues Found

1. **78 checks marked `needs_work`** — Mostly wrong field_keys. The `governance_score` catch-all is used by 30+ checks that should each have specific field keys. Similarly `financial_health_narrative` is overloaded.

2. **46 checks renamed** — Primarily ID-name mismatches in BIZ.DEPEND.* (10 checks where names don't match IDs) and data source corrections in FWRD.WARN.* (18 checks with wrong SEC_10K data source).

3. **5 retirements** — 3 EXEC.PROFILE duplicates of GOV.BOARD checks, 1 ESG check (user directive), 1 too-vague AI claims check (replaced with 7 specific AI hazard gap checks).

4. **4 merges** — 2 duplicate insider cluster checks, 1 duplicate material weakness check, 1 duplicate margin compression check.

### Missing Check Summary (Gaps by Priority)

| Priority | Count | Key Gaps |
|---|---|---|
| HIGH | 7 | SPAC detection, Going concern, Altman Z-Score, Derivative risk factors, PubPeer, Retraction Watch, AI washing |
| MEDIUM | 18 | Revenue fraud patterns (5), compensation manipulation (3), 10b5-1 timing, CapEx/OCF, non-audit fees, off-balance sheet leases, clinical trials, department departures, review surge, fraud keywords, FDA 483 |
| LOW | 14 | Industry-specific metrics (SaaS, biotech), dual-class sunset, fee-shifting bylaws, web traffic, union organizing, block trades, litigation funding, congressional inquiry, patent challenges, NPE exposure |
| **TOTAL** | **39** | |

### Data Source Implementation Status

| Status | Sources | Notes |
|---|---|---|
| Implemented | SEC_10K, SEC_10Q, SEC_DEF14A, SEC_8K, SEC_FORM4, SEC_ENFORCEMENT, SEC_13DG, MARKET_PRICE, MARKET_SHORT, SCAC_SEARCH, NEWS | Core pipeline working |
| NOT Implemented | GLASSDOOR, INDEED, BLIND, LINKEDIN, APP_STORE, TRUSTPILOT, G2, NHTSA, FDA, CFPB, COURT_RECORDS, ISS_GLASS_LEWIS | 12 alternative data sources needed for FORWARD.SIGNAL and GOVERNANCE.OVERSIGHT |

---

*End of Taxonomy Reclassification Document*
