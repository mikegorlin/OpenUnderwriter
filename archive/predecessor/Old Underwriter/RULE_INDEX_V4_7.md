# D&O UNDERWRITING SYSTEM - MASTER RULE INDEX
## Version 4.7 - Sector Calibration + Enhanced Stock Monitoring + Clean Numbering
## All rules use sequential 3-digit format: [CATEGORY]-[001-999]

---

## v4.7 CHANGES

1. **Clean Sequential Numbering**: Eliminated all letter suffixes (e.g., NEG-001a â†’ NEG-002)
2. **SEC-001 through SEC-009**: Sector calibration rules
3. **STK-001 through STK-010**: Stock performance monitoring module
4. **Consolidated QS-023, QS-029, QS-032**: Replaced by STK module
5. **Updated Cross-References**: All F.2 references point to new STK rule IDs
6. **Total New Rules**: 19

---

## NUMBERING CONVENTION

**Standard Format**: `[CATEGORY]-[3-digit sequential number]`

- No letter suffixes (a, b, c)
- No descriptive IDs (1D, 5D, ATR)
- Related rules grouped by sequential numbers
- Category prefix identifies rule type

---

## TRIAGE RULES (TRI-001 to TRI-005)
File: 00_PROJECT_INSTRUCTIONS_V4_7.md

| Rule ID | Rule Name | Description |
|---------|-----------|-------------|
| TRI-001 | Submission Triage Gate | Ask type, scan litigation, confirm claims |
| TRI-002 | SCAC Litigation Scan | Stanford SCAC search before claims question |
| TRI-003 | Web Litigation Scan | Web search for securities litigation |
| TRI-004 | Route to Full Analysis | New business or renewal with claims pathway |
| TRI-005 | Route to Renewal Module | Clean renewal pathway |

---

## NEGATIVE NEWS SWEEP RULES (NEG-001 to NEG-009)
File: 01_QUICK_SCREEN_V4_7.md

| Rule ID | Rule Name | Description |
|---------|-----------|-------------|
| NEG-001 | Negative Sweep Protocol | Master rule - execute NEG-002 through NEG-009 |
| NEG-002 | Securities Class Action Search | "[Company] securities class action lawsuit sued" |
| NEG-003 | Executive Departure Search | "[Company] CFO CEO resigned departure left fired" |
| NEG-004 | Restatement/Accounting Search | "[Company] restatement accounting problems SEC" |
| NEG-005 | Investigation/Subpoena Search | "[Company] investigation subpoena Wells Notice DOJ" |
| NEG-006 | Stock Drop Search | "[Company] stock drop decline crash plunge" |
| NEG-007 | Guidance Miss Search | "[Company] guidance cut miss warning disappoints" |
| NEG-008 | Short Seller Search | "[Company] short seller Hindenburg Citron fraud" |
| NEG-009 | Layoffs/Restructuring Search | "[Company] layoffs restructuring problems troubles" |

---

## SECTOR CALIBRATION RULES (SEC-001 to SEC-009) - NEW in v4.7
File: 01_QUICK_SCREEN_V4_7.md

| Rule ID | Rule Name | Description |
|---------|-----------|-------------|
| SEC-001 | Sector Identification | Mandatory sector classification before QS execution |
| SEC-002 | EBITDA Calibration | Sector-specific thresholds for negative EBITDA (QS-013) |
| SEC-003 | Leverage Calibration | Sector-specific thresholds for Debt/EBITDA (QS-014) |
| SEC-004 | Cash Runway Calibration | Sector-specific thresholds for cash runway (QS-015) |
| SEC-005 | Margin Calibration | Sector-specific thresholds for margin compression (QS-017) |
| SEC-006 | Current Ratio Calibration | Sector-specific thresholds for working capital (QS-018) |
| SEC-007 | Interest Coverage Calibration | Sector-specific thresholds for coverage (QS-020) |
| SEC-008 | Short Interest Calibration | Sector-specific thresholds for SI (QS-030) |
| SEC-009 | Stock Decline Calibration | Sector-specific thresholds for STK horizons |

---

## STOCK PERFORMANCE RULES (STK-001 to STK-010) - NEW in v4.7
File: 01_QUICK_SCREEN_V4_7.md + 14_STOCK_MONITORING_REFERENCE.md

| Rule ID | Rule Name | Description |
|---------|-----------|-------------|
| STK-001 | Stock Performance Module | Master module replacing QS-023, QS-029, QS-032 |
| STK-002 | Single-Day Horizon | 1-day decline analysis with sector threshold |
| STK-003 | 5-Day Horizon | 5-day decline analysis with sector threshold |
| STK-004 | 20-Day Horizon | ~1 month decline analysis with sector threshold |
| STK-005 | 60-Day Horizon | ~3 month decline analysis with sector threshold |
| STK-006 | 90-Day Horizon | Quarterly decline analysis with sector threshold |
| STK-007 | 52-Week Horizon | Annual decline from high with sector threshold |
| STK-008 | Attribution Analysis | Company vs Sector vs Market classification |
| STK-009 | Recency Weighting | Time-based severity adjustment for events |
| STK-010 | Pattern Detection | Acceleration, cascade, stabilization, recovery |

---

## STREAMLINED EXECUTION RULES (STR-001 to STR-005)
File: 00_PROJECT_INSTRUCTIONS_V4_7.md

| Rule ID | Rule Name | Description |
|---------|-----------|-------------|
| STR-001 | v1.1 Minimum Deliverable | v1.1 worksheet is minimum output |
| STR-002 | Front-Load Risk Detection | NEG + nuclear triggers run first |
| STR-003 | Industry Before Output | Load sector module before v1.1 |
| STR-004 | Deep-Dive Optional | Full analysis optional based on findings |
| STR-005 | Token Efficiency | Checkpoints in files not chat |

---

## INDUSTRY MODULE RULES (IND-001 to IND-004)
File: 00_PROJECT_INSTRUCTIONS_V4_7.md

| Rule ID | Rule Name | Description |
|---------|-----------|-------------|
| IND-001 | Industry Module Loading | Load sector-specific module per SEC-001 |
| IND-002 | Sector Concerns | Identify sector-specific risks |
| IND-003 | Sector Positives | Identify sector-specific strengths |
| IND-004 | Baseline Comparison | Use sector baselines for scoring |

---

## DEEP-DIVE RECOMMENDATION RULES (DDR-001 to DDR-003)
File: 00_PROJECT_INSTRUCTIONS_V4_7.md

| Rule ID | Rule Name | Description |
|---------|-----------|-------------|
| DDR-001 | Post-v1.1 Recommendations | Output deep-dive recs after v1.1 |
| DDR-002 | Finding-to-Section Mapping | Map findings to sections |
| DDR-003 | User Decision Gate | User decides on deep-dive |

---

## NUCLEAR TRIGGERS (NT-001 to NT-008)
Auto-escalate to minimum tier floor. **Triggers management escalation, not auto-decline.**

| Rule ID | Trigger | Min Tier | Min Score |
|---------|---------|----------|-----------|
| NT-001 | Active securities class action | EXTREME | 70 |
| NT-002 | Wells Notice disclosed | EXTREME | 70 |
| NT-003 | DOJ criminal investigation | EXTREME | 70 |
| NT-004 | Going concern opinion | HIGH | 50 |
| NT-005 | Restatement <12 months | HIGH | 50 |
| NT-006 | SPAC <18mo + stock <$5 | HIGH | 50 |
| NT-007 | Short seller report <6 months | HIGH | 50 |
| NT-008 | Stock decline >60% company-specific | HIGH | 50 |

---

## SCORING RULES - F.1 Prior Litigation (F1-001 to F1-007)
Max: 20 points | File: 10_SCORING.md

| Rule ID | Condition | Points |
|---------|-----------|--------|
| F1-001 | Active securities class action | 20 + NT-001 |
| F1-002 | Securities suit settled <3 years | 18 |
| F1-003 | Securities suit settled 3-5 years | 15 |
| F1-004 | Securities suit settled 5-10 years | 10 |
| F1-005 | SEC enforcement action <5 years | 12 |
| F1-006 | Derivative suit <5 years | 6 |
| F1-007 | No prior litigation | 0 |

---

## SCORING RULES - F.2 Stock Decline (F2-001 to F2-008)
Max: 15 points | File: 10_SCORING.md
**Updated v4.7**: Integrates with STK module output

| Rule ID | Condition | Points |
|---------|-----------|--------|
| F2-001 | Decline >60% (per STK-007) | 15 |
| F2-002 | Decline 50-60% | 12 |
| F2-003 | Decline 40-50% | 9 |
| F2-004 | Decline 30-40% | 6 |
| F2-005 | Decline 20-30% | 3 |
| F2-006 | Decline <20% | 0 |
| F2-007 | Company-specific >20% vs sector (per STK-008) | +3 bonus |
| F2-008 | CASCADE or ACCELERATION pattern (per STK-010) | +2 bonus |

---

## SCORING RULES - F.3 through F.10
(Unchanged from v4.6)

| Factor | Max Pts | Rule IDs |
|--------|---------|----------|
| F.3 Restatement/Audit | 12 | F3-001 to F3-007 |
| F.4 IPO/SPAC/M&A | 10 | F4-001 to F4-006 |
| F.5 Guidance Misses | 8 | F5-001 to F5-006 |
| F.6 Short Interest | 8 | F6-R01 to F6-X02 (contextual) |
| F.7 Insider Trading | 8 | F7-H01 to F7-B02 (contextual) |
| F.8 Volatility | 7 | F8-xxx (contextual) |
| F.9 Financial Distress | 6 | F9-xxx (contextual) |
| F.10 Governance | 3 | F10-001 to F10-005 |

---

## QUICK SCREEN RULES - NUCLEAR TRIGGERS (QS-001 to QS-012)
File: 01_QUICK_SCREEN_V4_7.md
**Not sector-calibrated - universal thresholds**

| Rule ID | Check | Nuclear? |
|---------|-------|----------|
| QS-001 | Active Securities Class Action | â­ YES |
| QS-002 | SEC Wells Notice | â­ YES |
| QS-003 | SPAC Status | â­ YES (conditional) |
| QS-004 | Recent Restatement | â­ YES |
| QS-005 | Auditor Resignation | â­ YES |
| QS-006 | Going Concern | â­ YES |
| QS-007 | Material Weakness | â­ YES (if unremediated) |
| QS-008 | DOJ Investigation | â­ YES |
| QS-009 | SEC Investigation | No |
| QS-010 | FTC/Antitrust | No |
| QS-011 | Bankruptcy/Default | â­ YES |
| QS-012 | Short Seller Report | â­ YES |

---

## QUICK SCREEN RULES - FINANCIAL DISTRESS (QS-013 to QS-022)
File: 01_QUICK_SCREEN_V4_7.md
**Sector-calibrated via SEC-002 through SEC-007**

| Rule ID | Check | Calibration Rule |
|---------|-------|------------------|
| QS-013 | Negative EBITDA | SEC-002 |
| QS-014 | Debt/EBITDA | SEC-003 |
| QS-015 | Cash Runway | SEC-004 |
| QS-016 | Revenue Decline | Universal |
| QS-017 | Margin Compression | SEC-005 |
| QS-018 | Working Capital | SEC-006 |
| QS-019 | Debt Maturity Wall | Universal |
| QS-020 | Interest Coverage | SEC-007 |
| QS-021 | Goodwill >50% | Universal |
| QS-022 | Negative OCF | Universal + context |

---

## QUICK SCREEN RULES - STOCK PERFORMANCE (QS-023 to QS-032)
File: 01_QUICK_SCREEN_V4_7.md

| Rule ID | Check | v4.7 Status |
|---------|-------|-------------|
| QS-023 | Stock Decline | **RETIRED â†’ STK-001** |
| QS-024 | Delisting Notice | Active (Nuclear) |
| QS-025 | IPO <24 Months | Active |
| QS-026 | Secondary Offering | Active |
| QS-027 | Lock-Up Expiration | Active |
| QS-028 | Analyst Downgrades | Active |
| QS-029 | Multiple Stock Drops | **RETIRED â†’ STK-001** |
| QS-030 | Short Interest | SEC-008 calibrated |
| QS-031 | ATM Program | Active |
| QS-032 | Stock <$5 | **RETIRED â†’ STK-001** |

---

## QUICK SCREEN RULES - GOVERNANCE (QS-033 to QS-038)
File: 01_QUICK_SCREEN_V4_7.md
**Not sector-calibrated - universal standards**

| Rule ID | Check |
|---------|-------|
| QS-033 | CEO/CFO Tenure <6 Months |
| QS-034 | Board Independence <50% |
| QS-035 | Insider Selling >$25M |
| QS-036 | Executive Background Issues |
| QS-037 | Related Party >5% Revenue |
| QS-038 | Active Proxy Contest |

---

## QUICK SCREEN RULES - INDUSTRY-SPECIFIC (QS-039 to QS-043)
File: 01_QUICK_SCREEN_V4_7.md

| Rule ID | Check | Applies To |
|---------|-------|------------|
| QS-039 | Opioid Exposure | Pharma, Distributors |
| QS-040 | PFAS Contamination | Chemicals, Manufacturing |
| QS-041 | Crypto Exposure | Any |
| QS-042 | Cannabis Operations | Any |
| QS-043 | China VIE Structure | China operations |

---

## EXECUTION RULES (EX-001 to EX-010)
File: 00_PROJECT_INSTRUCTIONS_V4_7.md

| Rule ID | Rule | Description |
|---------|------|-------------|
| EX-001 | Start with Triage | Every analysis begins with TRI-001 |
| EX-002 | Sector ID After Triage | SEC-001 runs after TRI, before NEG |
| EX-003 | NEG Before QS | Run NEG-001 before Quick Screen |
| EX-004 | Nuclear Triggers First | QS-001 to QS-012 must pass |
| EX-005 | STK During QS | Run STK-001 as part of QS-C |
| EX-006 | Scoring Data with Sources | All 10 factors need data + source |
| EX-007 | Industry Module Before Output | Load per SEC-001 |
| EX-008 | Generate v1.1 with Guidance | Include pricing/limit/retention |
| EX-009 | Recommend Deep-Dives | Map findings to sections |
| EX-010 | Save State if Lengthy | Use continuity protocol |

---

## ESCALATION RULES (ESC-001 to ESC-007)
File: 00_PROJECT_INSTRUCTIONS_V4_7.md

| Rule ID | Condition | Action |
|---------|-----------|--------|
| ESC-001 | Nuclear trigger hit | ESCALATE - Management approval |
| ESC-002 | 3+ red flags in QS | ESCALATE - Elevated review |
| ESC-003 | EXTREME tier (70-100) | ESCALATE - Senior approval |
| ESC-004 | HIGH tier (50-69) | FLAG - Document risks |
| ESC-005 | Unverified critical checks | GATE - Resolve first |
| ESC-006 | STK-010 BREAKDOWN pattern | ESCALATE - Multi-horizon RED |
| ESC-007 | STK-010 CASCADE pattern | ESCALATE - Continued selling |

---

## VERIFICATION & ZERO SCORE RULES
File: 00_PROJECT_INSTRUCTIONS_V4_7.md

| Rule ID | Rule Name | Description |
|---------|-----------|-------------|
| VER-001 | Affirmative Verification | Every claim requires CLAIM/SOURCE/EVIDENCE/VERDICT |
| ZER-001 | Zero Score Justification | Factors = 0 require positive evidence |

---

## TIER RULES (TR-001 to TR-006)
File: 10_SCORING.md

| Rule ID | Score | Tier | 18-Mo Probability |
|---------|-------|------|-------------------|
| TR-001 | 70-100 | EXTREME | >20% |
| TR-002 | 50-69 | HIGH | 10-20% |
| TR-003 | 30-49 | AVERAGE | 5-10% |
| TR-004 | 15-29 | BELOW AVG | 2-5% |
| TR-005 | 0-14 | MINIMAL | <2% |
| TR-006 | N/A | Cap | Never claim >25% |

---

## RENEWAL MODULE RULES
File: renewal_analysis_module_v1.md

| Category | Rule IDs | Count |
|----------|----------|-------|
| Renewal Quick Screen | RQS-001 to RQS-020 | 20 |
| Renewal Module | REN-001 to REN-011 | 11 |
| Corridor | COR-001 to COR-007 | 7 |

---

## TOTAL RULE COUNT

| Category | Count | Notes |
|----------|-------|-------|
| Triage (TRI) | 5 | Renumbered |
| Negative Sweep (NEG) | 9 | Renumbered |
| Sector Calibration (SEC) | 9 | NEW in v4.7 |
| Stock Performance (STK) | 10 | NEW in v4.7 |
| Streamlined Execution (STR) | 5 | |
| Industry Module (IND) | 4 | |
| Deep-Dive Recommendation (DDR) | 3 | |
| Nuclear Triggers (NT) | 8 | |
| F.1 Prior Litigation | 7 | |
| F.2 Stock Decline | 8 | Updated refs |
| F.3-F.10 | 70 | Unchanged |
| Tier Rules (TR) | 6 | |
| Quick Screen (QS) | 40 | -3 retired |
| Renewal (RQS, REN, COR) | 38 | |
| Validation/Citation (VR, CR) | 16 | |
| Execution (EX) | 10 | Renumbered |
| Escalation (ESC) | 7 | +2 for STK |
| Other (SV, EW, DF) | 30 | |
| Verification (VER, ZER) | 2 | |
| **TOTAL INDEXED RULES** | **287** | |

---

## FILE MANIFEST (v4.7)

| File | Version | Status |
|------|---------|--------|
| 00_PROJECT_INSTRUCTIONS_V4_7.md | 4.7 | Update needed |
| 01_QUICK_SCREEN_V4_7.md | 4.7 | **CURRENT** |
| 02_TRIGGER_MATRIX_V4_7.md | 4.7 | **CURRENT** |
| 03_LITIGATION_REGULATORY.md | - | Current |
| 04_FINANCIAL_HEALTH.md | - | Current |
| 05_BUSINESS_MODEL.md | - | Current |
| 06_GOVERNANCE.md | - | Current |
| 07_MARKET_DYNAMICS.md | - | Current |
| 08_ALTERNATIVE_DATA.md | - | Current |
| 09_PRIOR_ACTS_PROSPECTIVE.md | - | Current |
| 10_SCORING.md | - | Update F2 refs |
| 11_OUTPUT_TEMPLATE_V1_1.md | 1.1 | Update STK section |
| 12_OUTPUT_TEMPLATE_V3_0.md | 3.0 | Current |
| 13_SECTOR_BASELINES.md | - | Expanded in SEC-xxx |
| 14_STOCK_MONITORING_REFERENCE.md | 1.0 | **NEW** |
| RULE_INDEX_V4_7.md | 4.7 | **CURRENT** |
| RULE_RENUMBERING_MAP.md | 1.0 | **NEW** |
| renewal_analysis_module_v1.md | 1.0 | Current |

**Industry Modules**: All current (10 modules)

---

## CHANGE LOG

| Date | Change | Reason |
|------|--------|--------|
| 2025-12-17 | v4.1 Initial numbering | Framework release |
| 2025-12-17 | v4.2 Contextual scoring | Sector-relative F.6-F.9 |
| 2025-12-26 | v4.4 Red flag framework | No auto-declines |
| 2026-01-06 | v4.5 Renewal integration | Delta-based renewal analysis |
| 2026-01-07 | v4.6 Streamlined execution | Efficient v1.1 generation |
| 2026-01-07 | v4.7 Sector calibration | SEC-001 to SEC-009 |
| 2026-01-07 | v4.7 Stock monitoring | STK-001 to STK-010 |
| 2026-01-07 | v4.7 Clean numbering | Eliminated letter suffixes |
| 2026-01-07 | v4.7 Fixed trigger matrix | Corrected QS references |

---

**END OF RULE INDEX v4.7**
