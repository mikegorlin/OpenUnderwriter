# D&O SECTION TRIGGER MATRIX
## Version 4.7 - Updated for Sector Calibration + STK Module
## Maps Quick Screen Findings to Required Deep-Dive Sections

**Purpose**: After Quick Screen, use this matrix to determine which section files to load.
**Principle**: Don't load what you don't need. Load sections dynamically based on findings.

---

## v4.7 CHANGES

1. **Fixed QS Reference Errors** - All QS numbers now match actual checks
2. **Added STK-001 Routing** - Stock module findings map to sections
3. **Added SEC-001 Routing** - Sector identification drives industry module loading
4. **Consolidated Stock Checks** - QS-023, QS-029, QS-032 replaced by STK module

---

## HOW TO USE THIS MATRIX

1. Complete SEC-001 (Sector ID) and NEG-001 through NEG-009 (Negative Sweep)
2. Complete STK-001 through STK-010 (Stock Performance Module)
3. Complete QS-001 through QS-043 (Quick Screen)
4. For each ðŸ”´ RED or ðŸŸ¡ YELLOW finding, look up the trigger in the table below
5. Mark which sections are required based on triggers
6. Load ONLY the sections marked "Required"

---

## TRIGGER MAPPING TABLE

### From Litigation & Enforcement Findings (QS-001 to QS-012)

| QS Finding | Sections to Load | Specific Checks to Prioritize |
|------------|------------------|-------------------------------|
| QS-001: Active SCA | **03_LITIGATION_REGULATORY** (full) + **09_PRIOR_ACTS_PROSPECTIVE** | A.2.1, G.1-G.85 (entire Prior Acts framework) |
| QS-002: Wells Notice | **03_LITIGATION_REGULATORY** (full) | A.3.1 SEC Enforcement, A.3.4 Industry Regulators |
| QS-003: SPAC Status | **03_LITIGATION_REGULATORY** + **04_FINANCIAL_HEALTH** | A.1.3 SPAC, B.5.1 Stock Attribution |
| QS-004: Restatement | **03_LITIGATION_REGULATORY** + **04_FINANCIAL_HEALTH** | A.4.1-A.4.4, B.6 Accounting Quality |
| QS-005: Auditor Issues | **03_LITIGATION_REGULATORY** + **04_FINANCIAL_HEALTH** | A.4.2, B.6 Accounting Quality |
| QS-006: Going Concern | **04_FINANCIAL_HEALTH** (full) | B.1 Liquidity, B.2 Leverage, B.3 Profitability |
| QS-007: Material Weakness | **03_LITIGATION_REGULATORY** + **04_FINANCIAL_HEALTH** | A.4.3, B.6 Accounting Quality |
| QS-008: DOJ Investigation | **03_LITIGATION_REGULATORY** (full) | A.3.2 DOJ/Criminal, A.5 Whistleblower |
| QS-009: SEC Investigation | **03_LITIGATION_REGULATORY** | A.3.1 SEC Enforcement |
| QS-010: FTC/Antitrust | **03_LITIGATION_REGULATORY** | A.3.3 Antitrust |
| QS-011: Bankruptcy/Default | **04_FINANCIAL_HEALTH** (full) | B.1-B.4 all financial metrics |
| QS-012: Short Seller Report | **03_LITIGATION_REGULATORY** + **07_MARKET_DYNAMICS** + **08_ALTERNATIVE_DATA** | A.2.1, E.2 Short Interest, F.5 Media |

### From Financial Distress Findings (QS-013 to QS-022)

| QS Finding | Sections to Load | Specific Checks to Prioritize |
|------------|------------------|-------------------------------|
| QS-013: Negative EBITDA | **04_FINANCIAL_HEALTH** | B.3 Profitability, B.4 Cash Flow |
| QS-014: Debt/EBITDA | **04_FINANCIAL_HEALTH** | B.2.1-B.2.20, especially B.2.9-B.2.14 (Debt Sustainability) |
| QS-015: Cash Runway | **04_FINANCIAL_HEALTH** (full) | B.1.1 Cash, B.4 Cash Flow |
| QS-016: Revenue Decline | **04_FINANCIAL_HEALTH** + **05_BUSINESS_MODEL** | B.3 Profitability, C.1 Business Model |
| QS-017: Margin Compression | **04_FINANCIAL_HEALTH** | B.3 Profitability |
| QS-018: Working Capital | **04_FINANCIAL_HEALTH** | B.1 Liquidity |
| QS-019: Debt Maturity Wall | **04_FINANCIAL_HEALTH** | B.2.9-B.2.14 Debt Sustainability |
| QS-020: Interest Coverage | **04_FINANCIAL_HEALTH** | B.2 Leverage |
| QS-021: Goodwill >50% | **04_FINANCIAL_HEALTH** + **05_BUSINESS_MODEL** | B.6.4 Goodwill, C.4 M&A |
| QS-022: Negative OCF | **04_FINANCIAL_HEALTH** | B.4.1-B.4.3 Cash Flow |

### From Stock Performance Module (STK-001 to STK-010) - NEW in v4.7

| STK Finding | Sections to Load | Specific Checks to Prioritize |
|-------------|------------------|-------------------------------|
| STK-002 RED (1-Day) | **04_FINANCIAL_HEALTH** + **07_MARKET_DYNAMICS** | B.5.1 Attribution, E.1 Recent Events |
| STK-003 RED (5-Day) | **04_FINANCIAL_HEALTH** + **07_MARKET_DYNAMICS** | B.5.1 Attribution, E.1-E.2 |
| STK-004 RED (20-Day) | **04_FINANCIAL_HEALTH** + **07_MARKET_DYNAMICS** | B.5 Full Attribution |
| STK-005/006 RED (60/90-Day) | **04_FINANCIAL_HEALTH** + **05_BUSINESS_MODEL** | B.5, C.1-C.2 Business Fundamentals |
| STK-007 RED (52-Week) | **04_FINANCIAL_HEALTH** + **07_MARKET_DYNAMICS** | B.5 Full Attribution Analysis |
| STK-008: Company-Specific | **07_MARKET_DYNAMICS** (full) | E.1-E.4 all market checks |
| STK-010: ACCELERATION | **07_MARKET_DYNAMICS** | E.1 Momentum Analysis |
| STK-010: CASCADE | **07_MARKET_DYNAMICS** + **08_ALTERNATIVE_DATA** | E.1-E.2, F.5 Media |
| STK-010: BREAKDOWN | ALL SECTIONS | Full deep-dive recommended |

### From Stock & Market Findings (QS-024 to QS-031)

| QS Finding | Sections to Load | Specific Checks to Prioritize |
|------------|------------------|-------------------------------|
| QS-024: Delisting Notice | **04_FINANCIAL_HEALTH** + **07_MARKET_DYNAMICS** | B.5, E.2 Liquidity |
| QS-025: IPO <24mo | **03_LITIGATION_REGULATORY** + **04_FINANCIAL_HEALTH** | A.1.1 IPO Risk, B.5 Stock Performance |
| QS-026: Secondary Offering | **04_FINANCIAL_HEALTH** | B.1 Liquidity |
| QS-027: Lock-Up Expiration | **07_MARKET_DYNAMICS** | E.1 Ownership |
| QS-028: Analyst Downgrades | **07_MARKET_DYNAMICS** | E.4 Analyst Sentiment |
| QS-030: Short Interest | **07_MARKET_DYNAMICS** + **08_ALTERNATIVE_DATA** | E.2 Short Interest, F.5 Media |
| QS-031: ATM Program | **04_FINANCIAL_HEALTH** | B.1 Liquidity |

**Note**: QS-023, QS-029, QS-032 are RETIRED - replaced by STK-001 through STK-010

### From Governance Findings (QS-033 to QS-038)

| QS Finding | Sections to Load | Specific Checks to Prioritize |
|------------|------------------|-------------------------------|
| QS-033: CEO+CFO Turnover | **06_GOVERNANCE** (full) | D.1.1-D.1.4 Executive Team |
| QS-034: Board <50% | **06_GOVERNANCE** | D.2 Board Structure |
| QS-035: Heavy Insider Selling | **06_GOVERNANCE** | D.3.2 Insider Trading |
| QS-036: Executive Background | **06_GOVERNANCE** | D.1.4 Background Issues |
| QS-037: Related Party | **06_GOVERNANCE** | D.3.3 Related Party |
| QS-038: Proxy Contest | **06_GOVERNANCE** | D.5.3-D.5.6 Proxy Battle checks |

### From Industry-Specific Findings (QS-039 to QS-043)

| QS Finding | Sections to Load | Specific Checks to Prioritize |
|------------|------------------|-------------------------------|
| QS-039: Opioid | **03_LITIGATION_REGULATORY** + **08_ALTERNATIVE_DATA** | A.2-A.3, F.4 Regulatory |
| QS-040: PFAS | **03_LITIGATION_REGULATORY** + **08_ALTERNATIVE_DATA** | A.3, F.4.3 EPA |
| QS-041: Crypto | **03_LITIGATION_REGULATORY** + **07_MARKET_DYNAMICS** | A.3, E.4 |
| QS-042: Cannabis | **03_LITIGATION_REGULATORY** | A.3 |
| QS-043: China VIE | **05_BUSINESS_MODEL** + **07_MARKET_DYNAMICS** | C.3 Geographic, E.4 |

---

## SECTOR-BASED TRIGGERS (SEC-001) - NEW in v4.7

Load these industry modules based on SEC-001 sector identification:

| Sector Code | Industry Module | Always Load |
|-------------|-----------------|-------------|
| BIOT | biotech_industry_module_supplement.md | 04_FINANCIAL_HEALTH (B.7.2 Life Sciences) |
| TECH | technology_industry_module_supplement.md | 05_BUSINESS_MODEL |
| FINS | financials_industry_module_supplement_v3.md | 04_FINANCIAL_HEALTH (B.7.3) |
| HLTH | healthcare_industry_module_supplement.md | 04_FINANCIAL_HEALTH (B.7.2) |
| ENGY | energy_oil_gas_industry_module_supplement.md | 05_BUSINESS_MODEL (C.5) |
| INDU | industrials_manufacturing_industry_module_supplement.md | 05_BUSINESS_MODEL |
| REIT | reits_real_estate_industry_module_supplement_v2.md | 04_FINANCIAL_HEALTH |
| STPL | cpg_industry_module_supplement.md | 05_BUSINESS_MODEL |
| COMM | media_entertainment_industry_module_supplement.md | 05_BUSINESS_MODEL |
| CDIS (Retail) | Load retail checks from 04_FINANCIAL_HEALTH | B.7.4 Retail KPIs |

---

## COMPANY TYPE TRIGGERS

Load these sections based on company type regardless of Quick Screen findings:

### SaaS/Software Company (TECH)
- **Always Load**: 04_FINANCIAL_HEALTH (B.7.1 SaaS KPIs), 05_BUSINESS_MODEL
- **Key Checks**: ARR, NRR, Churn, CAC Payback, Rule of 40

### Biotech/Pharma (BIOT/HLTH)
- **Always Load**: 04_FINANCIAL_HEALTH (B.7.2 Life Sciences), 08_ALTERNATIVE_DATA (F.4.1 FDA)
- **Key Checks**: Pipeline stage, Cash runway, FDA status, Patent cliff

### Retail/Consumer (CDIS)
- **Always Load**: 05_BUSINESS_MODEL, 04_FINANCIAL_HEALTH (B.7.4 Retail)
- **Key Checks**: Comp sales, Inventory turn, E-commerce mix, Customer trends

### Financial Services/Banks (FINS)
- **Always Load**: 04_FINANCIAL_HEALTH (B.7.3 Financial Services), 03_LITIGATION_REGULATORY
- **Key Checks**: Capital ratios, NPLs, NIM trends, Regulatory status

### BDC (Business Development Company)
- **Always Load**: 04_FINANCIAL_HEALTH (full), 03_LITIGATION_REGULATORY
- **Key Checks**: NAV discount, Non-accruals, Portfolio quality, Leverage

### Commodity/Mining (MATL/ENGY)
- **Always Load**: 05_BUSINESS_MODEL (C.5.1-C.5.4 Commodity checks)
- **Key Checks**: Break-even price, Cycle position, Dual squeeze risk

### REIT (REIT)
- **Always Load**: 04_FINANCIAL_HEALTH, 05_BUSINESS_MODEL
- **Key Checks**: FFO/AFFO, Occupancy, Lease expiration, Debt maturities

---

## EXISTING CLAIMS TRIGGER

**If company has active D&O claim or litigation disclosed:**

âš ï¸ **MANDATORY: Load 09_PRIOR_ACTS_PROSPECTIVE**

This section contains 85 checks specifically for:
- Assessing prospective risk (will there be NEW claims?)
- Evaluating whether prior acts exclusion adequately protects
- Determining class period overlap risk
- Analyzing statute of limitations exposure

**Note**: Prior claim will be excluded via Prior Acts exclusion. Your analysis should focus on NEW claim probability during policy period.

---

## RUNOFF TRANSACTION TRIGGER

**If transaction type = RUNOFF (company being acquired):**

Different analysis focus is required:
- Replace Sections 4-5 of output with Merger Agreement Analysis
- Key question: What can buyer claim back from former management?
- Load 09_PRIOR_ACTS_PROSPECTIVE for historical acts assessment

**Key Checks for Runoff**:
1. Reps & warranties survival periods
2. Indemnification structure (escrow, caps, baskets)
3. R&W insurance presence
4. Post-close discovery scenarios
5. Known vs. unknown issues

---

## SECTION LOADING DECISION CHECKLIST

After reviewing Quick Screen and STK module, complete this checklist:

```
## SECTION LOADING DECISION - [COMPANY NAME]

### Sector Identification (SEC-001)
- Sector: [CODE] - [Name]
- Industry Module: [filename.md] â†’ LOAD

### STK-001 Stock Performance Triggers
- Highest Severity: [STK-00X] at [ðŸ”´/ðŸŸ¡/ðŸŸ¢]
- Patterns: [List]
- Triggered Sections: [List]

### Required Sections:
â–¡ 03_LITIGATION_REGULATORY - Triggered by: [QS-XXX, STK-XXX]
â–¡ 04_FINANCIAL_HEALTH - Triggered by: [QS-XXX, company type: X]
â–¡ 05_BUSINESS_MODEL - Triggered by: [QS-XXX]
â–¡ 06_GOVERNANCE - Triggered by: [QS-XXX]
â–¡ 07_MARKET_DYNAMICS - Triggered by: [QS-XXX, STK-XXX]
â–¡ 08_ALTERNATIVE_DATA - Triggered by: [QS-XXX]
â–¡ 09_PRIOR_ACTS_PROSPECTIVE - Triggered by: [Existing claims: Yes/No]

### NOT Loading (Reason):
- [Section]: No triggers identified
- [Section]: Not applicable to company type

### Estimated Deep-Dive Time: X minutes
```

---

## CROSS-REFERENCE: NEG FINDINGS TO QS CHECKS

When NEG-002 through NEG-009 surface issues, verify in specific QS checks:

| NEG Finding | Verify In |
|-------------|-----------|
| NEG-002 (Litigation) | QS-001, QS-009, QS-010 |
| NEG-003 (Exec Turnover) | QS-033 |
| NEG-004 (Restatement) | QS-004, QS-005, QS-007 |
| NEG-005 (Investigation) | QS-002, QS-008, QS-009, QS-010 |
| NEG-006 (Stock Drop) | STK-001 through STK-010 |
| NEG-007 (Guidance Miss) | F.5 Scoring |
| NEG-008 (Short Seller) | QS-012 |
| NEG-009 (Restructuring) | QS-013, QS-022, Section B and C |

---

**END OF TRIGGER MATRIX v4.7**
