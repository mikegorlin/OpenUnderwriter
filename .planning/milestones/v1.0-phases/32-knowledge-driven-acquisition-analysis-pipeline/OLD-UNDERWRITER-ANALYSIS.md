# Old Underwriter System -- Exhaustive Check/Rule Inventory

## Purpose

Complete extraction of every check, question, rule, and data point from the predecessor
D&O underwriting system (15 source files in `Old Underwriter/`). One line per item.
Types: DISPLAY (extract and show), EVALUATIVE (compare against threshold), INFERENCE (pattern/multi-source).

**Total: 594 new-business checks + 67 renewal = 661 checks. 287 indexed rules.**

---

## MODULE 00: PROJECT INSTRUCTIONS (`00_PROJECT_INSTRUCTIONS_V4_7.md`)

### TRI -- Triage Gate (5 rules)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| TRI-001 | Is this new business or a renewal? | User input | EVALUATIVE |
| TRI-002 | Search "[Company] securities class action" | Stanford SCAC | EVALUATIVE |
| TRI-003 | Search "[Company] securities lawsuit shareholders" | Web search | EVALUATIVE |
| TRI-004 | Route to full analysis (new business) | TRI-001 result | EVALUATIVE |
| TRI-005 | Route to renewal module | TRI-001 result | EVALUATIVE |

### STR -- Streamlined Execution (5 rules)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| STR-001 | Phase 0: Triage gate complete? | TRI-001 through TRI-005 | EVALUATIVE |
| STR-002 | Phase 1: Sector ID complete? | SEC-001 | EVALUATIVE |
| STR-003 | Phase 2: Negative sweep complete? | NEG-001 checkpoint | EVALUATIVE |
| STR-004 | Phase 3-4: Quick screen nuclear + calibrated complete? | QS results | EVALUATIVE |
| STR-005 | Phase 5-7: Scoring + industry + output complete? | All factors | EVALUATIVE |

### IND -- Industry Module (4 rules)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| IND-001 | Load sector-specific industry module per SEC-001 | SEC-001 sector code | EVALUATIVE |
| IND-002 | Run key sector-specific checks from industry supplement | Industry module file | EVALUATIVE |
| IND-003 | Identify sector-specific concerns | Industry module checks | INFERENCE |
| IND-004 | Identify sector-specific positives | Industry module checks | INFERENCE |

### DDR -- Deep-Dive Recommendation (3 rules)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| DDR-001 | Map QS/STK findings to deep-dive sections via Trigger Matrix | 02_TRIGGER_MATRIX | EVALUATIVE |
| DDR-002 | Recommend specific sections for further investigation | Trigger matrix output | INFERENCE |
| DDR-003 | User decides whether to proceed with deep-dives | User input | EVALUATIVE |

### EX -- Execution Rules (10 rules)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| EX-001 | Start with TRI-001 Triage | Workflow gate | EVALUATIVE |
| EX-002 | Run SEC-001 Sector ID after Triage | Workflow gate | EVALUATIVE |
| EX-003 | Run NEG-001 before Quick Screen | Workflow gate | EVALUATIVE |
| EX-004 | Check Nuclear Triggers (QS-001 to QS-012) first | QS results | EVALUATIVE |
| EX-005 | Run STK-001 during Quick Screen Phase 4 | Stock data | EVALUATIVE |
| EX-006 | Collect Scoring Data with sources for all 10 factors | Multiple | EVALUATIVE |
| EX-007 | Load Industry Module per SEC-001 before output | SEC-001 | EVALUATIVE |
| EX-008 | Generate v1.2 with pricing/limit/retention guidance | All data | EVALUATIVE |
| EX-009 | Recommend Deep-Dives based on findings | QS/STK results | INFERENCE |
| EX-010 | Save State if conversation is lengthy | Session state | EVALUATIVE |

### ESC -- Escalation Rules (7 rules)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| ESC-001 | Nuclear trigger hit -- ESCALATE to management | QS-001 to QS-012, NT-001 to NT-008 | EVALUATIVE |
| ESC-002 | 3+ red flags in QS -- elevated review required | QS tally | EVALUATIVE |
| ESC-003 | EXTREME tier (70-100) -- senior approval required | Composite score | EVALUATIVE |
| ESC-004 | HIGH tier (50-69) -- document risks | Composite score | EVALUATIVE |
| ESC-005 | Unverified critical checks -- gate before proceeding | VER-001 status | EVALUATIVE |
| ESC-006 | STK-010 BREAKDOWN pattern -- multi-horizon RED | STK-010 | EVALUATIVE |
| ESC-007 | STK-010 CASCADE pattern -- continued selling | STK-010 | EVALUATIVE |

### VER/ZER -- Verification Protocols (2 rules)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| VER-001 | Every claim requires CLAIM + SOURCE + EVIDENCE + VERDICT | All checks | EVALUATIVE |
| ZER-001 | Any factor scored 0 requires documented positive evidence | Scoring factors F.1-F.10 | EVALUATIVE |

---

## MODULE 01: QUICK SCREEN (`01_QUICK_SCREEN_V4_7.md`)

### NEG -- Negative News Sweep (9 rules)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| NEG-001 | Master protocol: execute all 8 searches before QS | Gate rule | EVALUATIVE |
| NEG-002 | "[Company] securities class action lawsuit sued" | Web search | EVALUATIVE |
| NEG-003 | "[Company] CFO CEO resigned departure left fired" | Web search | EVALUATIVE |
| NEG-004 | "[Company] restatement accounting problems SEC" | Web search | EVALUATIVE |
| NEG-005 | "[Company] investigation subpoena Wells Notice DOJ" | Web search | EVALUATIVE |
| NEG-006 | "[Company] stock drop decline crash plunge" | Web search | EVALUATIVE |
| NEG-007 | "[Company] guidance cut miss warning disappoints" | Web search | EVALUATIVE |
| NEG-008 | "[Company] short seller Hindenburg Citron fraud" | Web search | EVALUATIVE |
| NEG-009 | "[Company] layoffs restructuring problems troubles" | Web search | EVALUATIVE |

### SEC -- Sector Calibration (9 rules)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| SEC-001 | Identify company sector from 13 codes (UTIL/STPL/FINS/INDU/TECH/HLTH/BIOT/CDIS/ENGY/REIT/COMM/MATL/SPEC) | 10-K Business section, SIC/NAICS | EVALUATIVE |
| SEC-002 | Sector-calibrated Negative EBITDA thresholds (RED/YELLOW per sector) | Calibration table | EVALUATIVE |
| SEC-003 | Sector-calibrated Debt/EBITDA thresholds (RED/YELLOW per sector) | Calibration table | EVALUATIVE |
| SEC-004 | Sector-calibrated Cash Runway thresholds (applies to TECH pre-profit, BIOT, SPEC only) | Calibration table | EVALUATIVE |
| SEC-005 | Sector-calibrated Margin Compression thresholds (bps by sector) | Calibration table | EVALUATIVE |
| SEC-006 | Sector-calibrated Current Ratio thresholds (per sector) | Calibration table | EVALUATIVE |
| SEC-007 | Sector-calibrated Interest Coverage thresholds (per sector) | Calibration table | EVALUATIVE |
| SEC-008 | Sector-calibrated Short Interest thresholds (per sector) | Calibration table | EVALUATIVE |
| SEC-009 | Sector-calibrated Stock Decline thresholds (per horizon per sector) -- see STK-002 to STK-007 | Calibration table | EVALUATIVE |

### STK -- Stock Performance Module (10 rules)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| STK-001 | Master module: comprehensive multi-horizon stock analysis with sector calibration | Yahoo Finance, sector ETF | INFERENCE |
| STK-002 | Single-day decline vs sector-specific threshold (13 sector thresholds) | Yahoo Finance 1-day return | EVALUATIVE |
| STK-003 | 5-day decline vs sector-specific threshold (13 sector thresholds) | Yahoo Finance 5-day return | EVALUATIVE |
| STK-004 | 20-day (~1 month) decline vs sector-specific threshold | Yahoo Finance 20-day return | EVALUATIVE |
| STK-005 | 60-day (~3 month) decline vs sector-specific threshold | Yahoo Finance 60-day return | EVALUATIVE |
| STK-006 | 90-day (~1 quarter) decline vs sector-specific threshold | Yahoo Finance 90-day return | EVALUATIVE |
| STK-007 | 52-week decline from high vs sector-specific threshold | Yahoo Finance 52-week data | EVALUATIVE |
| STK-008 | Attribution: Company-Specific vs Sector-Wide vs Market-Wide (>10 ppts = company-specific) | Company return vs sector ETF vs S&P 500 | INFERENCE |
| STK-009 | Recency weighting: 30d=1.5x, 31-90d=1.0x, 91-180d=0.75x, 181-365d=0.5x | Event timing | INFERENCE |
| STK-010 | Pattern detection: ACCELERATION, CASCADE, STABILIZATION, RECOVERY, BREAKDOWN | Multi-horizon comparison | INFERENCE |

### QS-A -- Nuclear Triggers (QS-001 to QS-012)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| QS-001 | Active securities class action pending? NUCLEAR if yes | Stanford SCAC, 10-K Item 3 | EVALUATIVE |
| QS-002 | SEC Wells Notice disclosed? NUCLEAR if yes | 10-K/10-Q Risk Factors, 8-K Item 8.01 | EVALUATIVE |
| QS-003 | SPAC status? NUCLEAR if <18mo AND stock <$5 or down >50% | 8-K merger completion, S-4 | EVALUATIVE |
| QS-004 | Recent restatement? NUCLEAR if <12 months | 8-K Item 4.02, 10-K/A | EVALUATIVE |
| QS-005 | Auditor resignation with disagreements? NUCLEAR if <24 months | 8-K Item 4.01 | EVALUATIVE |
| QS-006 | Going concern opinion issued? NUCLEAR | 10-K auditor's report | EVALUATIVE |
| QS-007 | Material weakness (SOX 404) unremediated? NUCLEAR | 10-K Item 9A | EVALUATIVE |
| QS-008 | Active DOJ investigation? NUCLEAR | 10-K/10-Q Risk Factors, news | EVALUATIVE |
| QS-009 | Active SEC investigation (non-Wells)? RED if active | 10-K/10-Q Risk Factors, 8-K | EVALUATIVE |
| QS-010 | Active FTC/antitrust investigation? RED if active | 10-K Risk Factors, news | EVALUATIVE |
| QS-011 | Bankruptcy/default risk? NUCLEAR if debt in default or CCC rating | Credit ratings, 10-K covenants | EVALUATIVE |
| QS-012 | Short seller report <6 months? NUCLEAR | News, Hindenburg/Citron/etc. | EVALUATIVE |

### QS-B -- Financial Distress (QS-013 to QS-022, sector-calibrated)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| QS-013 | Negative EBITDA? (Use SEC-002 sector threshold) | 10-K/10-Q financials | EVALUATIVE |
| QS-014 | Debt/EBITDA elevated? (Use SEC-003 sector threshold) | 10-K balance sheet | EVALUATIVE |
| QS-015 | Cash runway insufficient? (Use SEC-004 -- TECH/BIOT/SPEC only) | 10-K/10-Q cash flow | EVALUATIVE |
| QS-016 | Revenue decline >20% YoY? (Universal: >20% RED, 10-20% YELLOW) | 10-K/10-Q vs prior year | EVALUATIVE |
| QS-017 | Margin compression? (Use SEC-005 sector threshold) | 10-K/10-Q vs prior year | EVALUATIVE |
| QS-018 | Working capital deficit? (Use SEC-006 sector threshold) | 10-K/10-Q balance sheet | EVALUATIVE |
| QS-019 | Debt maturity wall <24 months? (>30% maturing + distress = RED) | 10-K debt footnote | EVALUATIVE |
| QS-020 | Interest coverage low? (Use SEC-007 sector threshold) | EBIT / Interest Expense | EVALUATIVE |
| QS-021 | Goodwill >50% of total assets? (Universal: +recent acq = RED) | 10-K balance sheet | EVALUATIVE |
| QS-022 | Negative operating cash flow TTM? (Universal with sector context) | 10-K/10-Q cash flow | EVALUATIVE |

### QS-C -- Stock Performance (QS-023 to QS-032)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| QS-023 | RETIRED -- replaced by STK-001 | -- | -- |
| QS-024 | Delisting notice received? NUCLEAR if yes | 8-K Item 3.01, exchange notices | EVALUATIVE |
| QS-025 | IPO <24 months? RED if <12mo + stock down >30% | S-1, company history | EVALUATIVE |
| QS-026 | Secondary offering <12 months? CAUTION | S-3, 8-K | EVALUATIVE |
| QS-027 | Lock-up expiration <90 days? CAUTION | S-1, calculate from IPO | EVALUATIVE |
| QS-028 | Analyst downgrade cluster? 3+ downgrades in 30 days = RED | News, analyst reports | EVALUATIVE |
| QS-029 | RETIRED -- replaced by STK-001 | -- | -- |
| QS-030 | Short interest elevated? (Use SEC-008 sector threshold) | Yahoo Finance, FINRA | EVALUATIVE |
| QS-031 | ATM (At-the-Market) program active? CAUTION | S-3, prospectus supplements | EVALUATIVE |
| QS-032 | RETIRED -- replaced by STK-001 | -- | -- |

### QS-D -- Governance (QS-033 to QS-038)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| QS-033 | CEO/CFO tenure <6 months? RED if both, YELLOW if either | 8-K Item 5.02, DEF 14A | EVALUATIVE |
| QS-034 | Board independence <50%? RED if <50%, YELLOW if 50-66% | DEF 14A director table | EVALUATIVE |
| QS-035 | Insider selling >$25M net (6mo)? RED if >$25M, YELLOW $10-25M | Form 4 filings | EVALUATIVE |
| QS-036 | Executive background issues? RED if CEO/CFO prior securities fraud defendant | News, SEC database | EVALUATIVE |
| QS-037 | Related party transactions >5% revenue? RED >5%, YELLOW 2-5% | 10-K Related Party, DEF 14A | EVALUATIVE |
| QS-038 | Active proxy contest? RED if active | DEF 14A, 13D filings, news | EVALUATIVE |

### QS-E -- Industry-Specific (QS-039 to QS-043)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| QS-039 | Opioid exposure? (Pharma, Distributors, Retailers w/pharmacy) | 10-K, litigation, news | EVALUATIVE |
| QS-040 | PFAS/environmental contamination exposure? (Chemicals, Mfg, CPG) | 10-K, EPA, news | EVALUATIVE |
| QS-041 | Crypto/digital asset exposure? | 10-K, news | EVALUATIVE |
| QS-042 | Cannabis operations? | 10-K, state licenses | EVALUATIVE |
| QS-043 | China VIE structure? (Companies with China operations) | 10-K, corporate structure | EVALUATIVE |

---

## MODULE 03: LITIGATION & REGULATORY (`03_LITIGATION_REGULATORY.md`) -- Section A, 37 checks

### A.1 Company Event Risk (4 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| A.1.1 | IPO timing risk: time since IPO, IPO price vs current | S-1, 8-K IPO completion | EVALUATIVE |
| A.1.2 | Recent capital raises: secondaries, debt issuances, stock performance since | 8-K, S-3 | EVALUATIVE |
| A.1.3 | SPAC status: de-SPAC date, projections vs actuals, stock vs merger price | 8-K merger completion, S-4 | EVALUATIVE |
| A.1.4 | Secondary offering timing: most recent offering price vs current, insider participation | S-3, 424B prospectus | EVALUATIVE |

### A.2 Securities Litigation History (5 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| A.2.1 | Securities class actions: all cases, class periods, status, settlements | Stanford SCAC, 10-K Item 3 | EVALUATIVE |
| A.2.2 | Derivative litigation: shareholder derivative suits, demand status | 10-K, PACER, Delaware Chancery | EVALUATIVE |
| A.2.3 | Employment/ERISA class actions: class size, alleged damages | 10-K, PACER | EVALUATIVE |
| A.2.4 | Product liability/mass tort: MDL status, bellwether results, settlement reserves | 10-K, news | EVALUATIVE |
| A.2.5 | Patent/IP litigation: active cases, key patent expiration, infringement role | 10-K, USPTO, PACER | EVALUATIVE |

### A.3 Regulatory Enforcement (8 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| A.3.1 | SEC enforcement: active investigation, Wells Notice, settlements | SEC.gov Litigation Releases, 10-K | EVALUATIVE |
| A.3.2 | DOJ/Criminal: investigation status, DPA/NPA, individual indictments | DOJ.gov, 10-K | EVALUATIVE |
| A.3.3 | FCPA/International corruption: high-risk country revenue, compliance program | DOJ FCPA database, SEC releases | EVALUATIVE |
| A.3.4 | FTC enforcement: active action, consent decrees | FTC.gov | EVALUATIVE |
| A.3.5 | FDA enforcement: warning letters, consent decrees, 483 observations (Healthcare) | FDA.gov | EVALUATIVE |
| A.3.6 | EPA enforcement: significant violations | EPA ECHO database | EVALUATIVE |
| A.3.7 | State AG actions: multi-state investigations | News, state AG press releases | EVALUATIVE |
| A.3.8 | Industry-specific regulators: FINRA, OCC, CFPB, FERC, etc. | Varies by industry | EVALUATIVE |

### A.4 Financial Reporting Issues (6 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| A.4.1 | Restatements: date, periods affected, nature, magnitude, fraud vs error | 8-K Item 4.02, 10-K/A | EVALUATIVE |
| A.4.2 | Auditor changes: reason, disagreements, reportable events | 8-K Item 4.01 | EVALUATIVE |
| A.4.3 | Material weaknesses (SOX 404): description, remediation status | 10-K Item 9A | EVALUATIVE |
| A.4.4 | SEC comment letters: open letters, topics, resolution status | SEC EDGAR Correspondence | EVALUATIVE |
| A.4.5 | Late filings: NT 10-K/10-Q filings | SEC EDGAR | EVALUATIVE |
| A.4.6 | Non-GAAP adjustments: Non-GAAP NI / GAAP NI ratio, increasing gap? | Earnings releases, 10-Q MD&A | EVALUATIVE |

### A.5 Whistleblower & Internal (4 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| A.5.1 | Whistleblower complaints: active investigation from whistleblower? | 10-K, news, court filings | EVALUATIVE |
| A.5.2 | Internal investigations: board-level investigations, fraud finding? | 8-K, 10-K, news | EVALUATIVE |
| A.5.3 | Employee hotline activity: material increase disclosed? | 10-K Risk Factors, ESG reports | EVALUATIVE |
| A.5.4 | Books & records demands: Section 220 demands, scope | 10-K, Delaware Chancery | EVALUATIVE |

### A.6 Going Concern & Distress (4 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| A.6.1 | Going concern opinion: auditor opinion, substantial doubt language | 10-K auditor's report | EVALUATIVE |
| A.6.2 | Bankruptcy risk: Altman Z-Score calculation, filing indicators | 10-K MD&A, financial data | EVALUATIVE |
| A.6.3 | Restructuring activity: debt or operational restructuring | 8-K, 10-K | EVALUATIVE |
| A.6.4 | Credit rating downgrades: recent downgrade, negative outlook | Moody's, S&P, Fitch | EVALUATIVE |

---

## MODULE 04: FINANCIAL HEALTH (`04_FINANCIAL_HEALTH.md`) -- Section B, 112 checks

### B.1 Liquidity (8 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| B.1.1 | Cash position & runway: total liquid assets / quarterly cash burn | 10-Q Balance Sheet, Cash Flow | EVALUATIVE |
| B.1.2 | Working capital: current assets - current liabilities, current ratio | 10-Q Balance Sheet | EVALUATIVE |
| B.1.3 | Quick ratio: (current assets - inventory) / current liabilities | 10-Q Balance Sheet | EVALUATIVE |
| B.1.4 | Credit facility availability: commitment, drawn, available amounts | 10-K/Q debt footnotes | DISPLAY |
| B.1.5 | Revolver utilization trend: utilization over 4 quarters | 10-K/Q debt footnotes | EVALUATIVE |
| B.1.6 | Cash concentration risk: % cash offshore with repatriation issues | 10-K geographic footnote | EVALUATIVE |
| B.1.7 | Restricted cash: restricted cash / total cash | Balance sheet, footnotes | EVALUATIVE |
| B.1.8 | ATM/shelf registration status: active shelf, capacity, utilized | S-3 shelf registration | DISPLAY |

### B.2 Leverage & Debt (20 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| B.2.1 | Debt structure summary: all debt by type, rate, maturity | 10-Q/10-K debt footnote | DISPLAY |
| B.2.2 | Debt/EBITDA ratio: total debt / TTM EBITDA | Balance Sheet, Income Statement | EVALUATIVE |
| B.2.3 | Debt/equity ratio: total debt / stockholders' equity | Balance Sheet | EVALUATIVE |
| B.2.4 | Net debt: total debt - cash - marketable securities, Net Debt/EBITDA | Balance Sheet | EVALUATIVE |
| B.2.5 | Interest coverage ratio: EBIT / Interest Expense | Income Statement | EVALUATIVE |
| B.2.6 | Fixed charge coverage (DSCR): (EBITDA-CapEx) / (interest+principal+lease) | Income Statement, Lease footnote | EVALUATIVE |
| B.2.7 | Debt maturity schedule: principal due by year, % of total | Debt footnote maturity table | EVALUATIVE |
| B.2.8 | Floating rate exposure: floating rate debt / total debt, hedges | Debt footnote | EVALUATIVE |
| B.2.9 | Covenant identification: all financial covenants, test levels, current, cushion | 10-K debt footnote, credit agreement | DISPLAY |
| B.2.10 | Covenant cushion analysis: (current - covenant) / covenant, breach proximity | Credit agreement | EVALUATIVE |
| B.2.11 | Covenant trajectory: cushion over 4 quarters, improving/deteriorating | 10-K/Q quarterly data | EVALUATIVE |
| B.2.12 | EBITDA quality check: credit agreement EBITDA / GAAP NI, addback analysis | Credit agreement, 10-Q | EVALUATIVE |
| B.2.13 | Covenant holiday/amendment history: waivers, loosening amendments | 8-K, credit agreement amendments | EVALUATIVE |
| B.2.14 | Liquidity vs maturity: (cash+revolver+OCF) vs maturities <24 months | 10-K debt footnote, cash flow | EVALUATIVE |
| B.2.15 | Secured vs unsecured: secured debt / total debt | Debt footnote | DISPLAY |
| B.2.16 | Subordination structure: first lien, second lien, unsecured, sub debt | Credit agreement | DISPLAY |
| B.2.17 | Cross-default provisions: does breach trigger others? | Credit agreement | EVALUATIVE |
| B.2.18 | Change of control provisions: M&A could trigger acceleration? | Credit agreement, indentures | DISPLAY |
| B.2.19 | Pension/OPEB obligations: funded status, unfunded % of market cap | 10-K pension footnote | EVALUATIVE |
| B.2.20 | Operating lease obligations: lease liability / EBITDA | Lease footnote | EVALUATIVE |

### B.3 Profitability (14 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| B.3.1 | Revenue trend: TTM, prior year, 2 years ago, YoY change | Income Statement | EVALUATIVE |
| B.3.2 | Revenue quality: recurring vs one-time vs services breakdown | Revenue footnote, MD&A | DISPLAY |
| B.3.3 | Gross margin: (revenue-COGS)/revenue, compression >500bps = RED | Income Statement | EVALUATIVE |
| B.3.4 | Operating margin: operating income / revenue | Income Statement | DISPLAY |
| B.3.5 | Net margin: net income / revenue | Income Statement | DISPLAY |
| B.3.6 | EBITDA margin: EBITDA / revenue | Income Statement | DISPLAY |
| B.3.7 | Revenue volatility: std dev of 12 quarterly growth rates | Past 12 quarters | EVALUATIVE |
| B.3.8 | Path to profitability: for unprofitable companies, when profitable? | Management guidance, estimates | EVALUATIVE |
| B.3.9 | Gross margin trend (8 quarters) | Income Statement, 8 quarters | EVALUATIVE |
| B.3.10 | Operating margin trend (8 quarters) | Income Statement, 8 quarters | EVALUATIVE |
| B.3.11 | Net margin trend (8 quarters) | Income Statement, 8 quarters | EVALUATIVE |
| B.3.12 | Margin trend analysis: deterioration patterns | 8-quarter trend data | INFERENCE |
| B.3.13 | Margin trend analysis continued | 8-quarter trend data | INFERENCE |
| B.3.14 | Margin trend analysis continued | 8-quarter trend data | INFERENCE |

### B.4 Cash Flow (8 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| B.4.1 | Operating cash flow: TTM OCF, OCF/NI quality ratio | Cash Flow Statement | EVALUATIVE |
| B.4.2 | Free cash flow: OCF - CapEx, persistent negative? | Cash Flow Statement | EVALUATIVE |
| B.4.3 | Cash vs earnings quality: compare NI to OCF over 8 quarters for divergence | Cash Flow, Income Statement | EVALUATIVE |
| B.4.4 | CapEx intensity: CapEx / revenue | Cash Flow Statement | DISPLAY |
| B.4.5 | Working capital changes: cash trapped in working capital | Cash Flow Statement WC section | DISPLAY |
| B.4.6 | Dividend/buyback sustainability: (dividends+buybacks) / FCF | Cash Flow Statement | EVALUATIVE |
| B.4.7 | Cash conversion cycle (DSO component) | Balance Sheet, Income Statement | DISPLAY |
| B.4.8 | Cash conversion cycle (DIO, DPO components) | Balance Sheet, Income Statement | DISPLAY |

### B.5 Stock Performance (12 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| B.5.1 | Stock price analysis: current, 52-week high/low, decline from high, market cap | Yahoo Finance | EVALUATIVE |
| B.5.2 | Attribution analysis: company decline vs sector ETF decline by period (if >10%) | Yahoo Finance | INFERENCE |
| B.5.3 | Peer comparison: performance vs 3+ direct competitors | Yahoo Finance | INFERENCE |
| B.5.4 | 90-day volatility: std dev of 90 daily returns | Yahoo Finance historical | EVALUATIVE |
| B.5.5 | Beta: market sensitivity (5-year monthly) | Yahoo Finance | EVALUATIVE |
| B.5.6 | Single-day drop analysis: drops >5% and >10% in past 12 months | Yahoo Finance historical | EVALUATIVE |
| B.5.7 | Detailed attribution for drop #1 (trigger, sector, peers, disclosure, litigation) | Yahoo Finance, 8-K, news | INFERENCE |
| B.5.8 | Detailed attribution for drop #2 | Yahoo Finance, 8-K, news | INFERENCE |
| B.5.9 | Detailed attribution for drop #3 | Yahoo Finance, 8-K, news | INFERENCE |
| B.5.10 | Detailed attribution for drop #4 | Yahoo Finance, 8-K, news | INFERENCE |
| B.5.11 | Detailed attribution for drop #5 | Yahoo Finance, 8-K, news | INFERENCE |
| B.5.12 | Detailed attribution for drop #6 | Yahoo Finance, 8-K, news | INFERENCE |

### B.6 Accounting Quality (12 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| B.6.1 | Revenue recognition: complexity, changes, multiple-element, ASC 606 issues | 10-K Note 2 | EVALUATIVE |
| B.6.2 | Receivables quality (DSO): A/R/Revenue x 365, 4-quarter trend, increasing >20% = RED | Balance Sheet | EVALUATIVE |
| B.6.3 | Allowance for doubtful accounts: allowance/gross A/R, decreasing + DSO increasing = RED | A/R footnote | EVALUATIVE |
| B.6.4 | Inventory quality: DIO trend, growing faster than sales + write-downs = RED | Balance Sheet, Inventory footnote | EVALUATIVE |
| B.6.5 | Goodwill impairment risk: goodwill/total equity, stock below deal value? | 10-K goodwill footnote | EVALUATIVE |
| B.6.6 | Deferred revenue changes: declining while recognized revenue grows = RED flag | Balance Sheet | EVALUATIVE |
| B.6.7 | Accrual vs cash accounting: accruals = NI - OCF, >10% of assets = RED | Income Statement, Cash Flow | EVALUATIVE |
| B.6.8 | Related party transactions: material without business purpose = RED | 10-K Related Party, DEF 14A | EVALUATIVE |
| B.6.9 | Auditor assessment: Big 4?, tenure, opinion type | 10-K auditor's report | DISPLAY |
| B.6.10 | Off-balance sheet arrangements | 10-K OBS disclosures | EVALUATIVE |
| B.6.11 | Special purpose entities | 10-K | EVALUATIVE |
| B.6.12 | Segment reporting changes | 10-K segment disclosures | EVALUATIVE |

### B.7 Industry-Specific KPIs (24 checks)

#### SaaS/Software (6 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| B.7.1.1 | Annual Recurring Revenue (ARR): MRR x 12, growth rate | Earnings releases, MD&A | DISPLAY |
| B.7.1.2 | Net Revenue Retention (NRR): expansion - churn, target >120% | Earnings releases | EVALUATIVE |
| B.7.1.3 | Gross Revenue Retention: before expansion, target >90% | Earnings releases | EVALUATIVE |
| B.7.1.4 | Customer Churn Rate: churned / starting customers | Company disclosures | EVALUATIVE |
| B.7.1.5 | CAC Payback Period: S&M / new ARR, target <18 months | Financial statements | EVALUATIVE |
| B.7.1.6 | Rule of 40: revenue growth % + EBITDA margin %, target >40% | Financial statements | EVALUATIVE |

#### Life Sciences (6 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| B.7.2.1 | Pipeline stage analysis: drug, phase, indication, FDA date, probability | ClinicalTrials.gov, 10-K | DISPLAY |
| B.7.2.2 | Cash runway to data: can company fund to next catalyst? | Cash flow, pipeline dates | EVALUATIVE |
| B.7.2.3 | FDA status: pending decisions, CRLs, inspection status | FDA.gov, company disclosures | EVALUATIVE |
| B.7.2.4 | Patent cliff: key patents expiring, revenue at risk | 10-K, patent filings | EVALUATIVE |
| B.7.2.5 | Partner milestones: upcoming collaboration milestones | 10-K, investor presentations | DISPLAY |
| B.7.2.6 | Clinical trial risk: enrollment status, site issues | ClinicalTrials.gov | EVALUATIVE |

#### Financial Services (6 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| B.7.3.1 | Capital ratios: CET1, Total Capital, Leverage vs minimums | Regulatory filings | EVALUATIVE |
| B.7.3.2 | Non-performing loans: NPLs / total loans, trend | 10-Q | EVALUATIVE |
| B.7.3.3 | Net interest margin: NIM trend over 8 quarters | 10-Q | EVALUATIVE |
| B.7.3.4 | Loan loss reserves: reserves / NPLs | 10-Q | EVALUATIVE |
| B.7.3.5 | Regulatory exam status: last exam, MRAs/MRIAs | Regulatory filings | EVALUATIVE |
| B.7.3.6 | Credit quality trends: 30-day delinquencies, charge-off rate | 10-Q | EVALUATIVE |

#### Retail (6 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| B.7.4.1 | Comparable store sales: comp sales, traffic, ticket by quarter | Earnings releases | EVALUATIVE |
| B.7.4.2 | Inventory turn: COGS / average inventory | Financial statements | EVALUATIVE |
| B.7.4.3 | E-commerce mix: online % of sales, digital growth | Earnings releases | DISPLAY |
| B.7.4.4 | Store count trends: opens, closes, net | 10-K, earnings releases | EVALUATIVE |
| B.7.4.5 | Customer metrics: traffic trends, loyalty program stats | Company disclosures | DISPLAY |
| B.7.4.6 | Gross margin by channel | Financial statements | DISPLAY |

### B.8 Guidance Track Record (6 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| B.8.1 | Guidance miss count: misses in past 8 quarters (4+ = RED) | 8-K earnings releases vs guidance | EVALUATIVE |
| B.8.2 | Average miss magnitude: any miss >15% = F.5 +2 bonus | 8-K earnings releases | EVALUATIVE |
| B.8.3 | Stock impact of misses: 5-day stock return after each miss | Yahoo Finance, 8-K dates | EVALUATIVE |
| B.8.4 | Guidance credibility pattern: systematic over-promising? | 8-quarter analysis | INFERENCE |
| B.8.5 | Guidance changes: withdrawn or lowered guidance | Earnings releases | EVALUATIVE |
| B.8.6 | Guidance vs street: sandbagging vs aggressive guidance | Analyst consensus vs guidance | INFERENCE |

---

## MODULE 05: BUSINESS MODEL (`05_BUSINESS_MODEL.md`) -- Section C, 74 checks

### C.1 Business Model Fundamentals (8 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| C.1.1 | Business model sustainability: moat, pricing power, disruption risk | 10-K Business, MD&A | INFERENCE |
| C.1.2 | Revenue model: revenue streams breakdown by product/service | 10-K Business, Revenue footnote | DISPLAY |
| C.1.3 | Recurring vs one-time revenue: recurring/total ratio, <30% = RED | 10-K, MD&A | EVALUATIVE |
| C.1.4 | Unit economics: LTV, CAC, LTV/CAC ratio, gross margin per unit | Varies by business | EVALUATIVE |
| C.1.5 | Scalability: operating leverage = % change EBIT / % change Revenue | Financial statements | EVALUATIVE |
| C.1.6 | Capital intensity: CapEx / Revenue, >20% + negative FCF = RED | Cash Flow Statement | EVALUATIVE |
| C.1.7 | Asset light vs asset heavy: total assets / revenue | Balance Sheet | DISPLAY |
| C.1.8 | Platform vs linear model: network effects, marketplace dynamics | 10-K Business | INFERENCE |

### C.2 Concentration Risk (12 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| C.2.1 | Customer concentration: single customer >40% = CRITICAL, top 5 >60% = MODERATE | 10-K Business (>10% disclosure) | EVALUATIVE |
| C.2.2 | Customer concentration trend: increasing or decreasing over 3 years | 10-K 3-year comparison | EVALUATIVE |
| C.2.3 | Customer quality: financial health of major customers | Customer public filings | EVALUATIVE |
| C.2.4 | Contract terms with major customers: length, renewal risk, exclusivity | 10-K Business | DISPLAY |
| C.2.5 | Supplier concentration: single-source critical, no alternatives = RED | 10-K Risk Factors | EVALUATIVE |
| C.2.6 | Supplier financial health: risk of supplier failure | Supplier filings, news | EVALUATIVE |
| C.2.7 | Geographic concentration: >50% from unstable region = RED | 10-K Geographic segment | EVALUATIVE |
| C.2.8 | Production concentration: single facility, high-risk location | 10-K Properties | EVALUATIVE |
| C.2.9 | Product concentration: single product >60% + declining = RED | 10-K Segment disclosure | EVALUATIVE |
| C.2.10 | Channel concentration: Amazon/Walmart dependence, platform risk | 10-K | EVALUATIVE |
| C.2.11 | Technology platform dependence: single cloud, critical APIs | 10-K Risk Factors | EVALUATIVE |
| C.2.12 | IP concentration: key patent expirations, trade secret, licensing | 10-K, patent analysis | EVALUATIVE |

### C.3 Competitive Position (10 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| C.3.1 | Market position: share, rank, trend (gaining/losing/stable) | 10-K Business, industry reports | EVALUATIVE |
| C.3.2 | Market size & growth: TAM, market growth rate, company vs market | Industry reports | DISPLAY |
| C.3.3 | Competitive moat assessment: cost, network, switching, brand, regulatory, IP | 10-K Business | INFERENCE |
| C.3.4 | Competitive threats: new entrants, disruption, convergence | 10-K Risk Factors, news | EVALUATIVE |
| C.3.5 | Pricing power: price erosion, commoditization | MD&A, gross margin trends | EVALUATIVE |
| C.3.6 | Customer switching costs: integration depth, data lock-in | 10-K Business | INFERENCE |
| C.3.7 | Industry dynamics: consolidation, regulatory changes, tech shifts | Industry reports | INFERENCE |
| C.3.8 | Barriers to entry: capital requirements, regulations, IP, scale | 10-K Business | INFERENCE |
| C.3.9 | Substitute threats: alternative solutions | 10-K Risk Factors | EVALUATIVE |
| C.3.10 | Supplier/buyer power: bargaining dynamics (Porter's) | Porter's analysis | INFERENCE |

### C.4 M&A & Integration (10 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| C.4.1 | Recent M&A activity: acquisitions in past 3 years, price, % of market cap | 8-K, 10-K | DISPLAY |
| C.4.2 | Integration risk: missed synergies, personnel departures, system issues | 8-K, MD&A | EVALUATIVE |
| C.4.3 | Goodwill impairment risk: stock below deal value, impairment headroom | Goodwill footnote | EVALUATIVE |
| C.4.4 | Earnout obligations: contingent consideration amounts, triggers | Acquisition footnotes | DISPLAY |
| C.4.5 | M&A strategy assessment: aggressive/debt-funded vs selective/disciplined | Track record | EVALUATIVE |
| C.4.6 | Roll-up risk: multiple acquisitions/year, complex accounting, goodwill accumulation | 10-K, 8-K | EVALUATIVE |
| C.4.7 | Divestiture activity: selling core or non-core assets? | 8-K | EVALUATIVE |
| C.4.8 | Merger agreement issues (runoff): R&W survival, indemnification, MAE | Merger Agreement (8-K exhibit) | DISPLAY |
| C.4.9 | Deal completion risk: regulatory hurdles, financing conditions, competing bids | Proxy statement | EVALUATIVE |
| C.4.10 | Post-close exposure: hidden liabilities, disclosure gaps | Due diligence analysis | INFERENCE |

### C.5 Commodity Exposure (6 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| C.5.1 | Output pricing exposure: revenue tied to commodity prices, % hedged | 10-K Business, MD&A | EVALUATIVE |
| C.5.2 | Input cost exposure: COGS dependence on commodities, % hedged | 10-K, MD&A | EVALUATIVE |
| C.5.3 | Dual squeeze analysis: both input and output at commodity risk | 10-K, scenario analysis | EVALUATIVE |
| C.5.4 | Break-even analysis: break-even price vs current price, margin of safety | 10-K, investor presentations | EVALUATIVE |
| C.5.5 | Hedging program assessment: hedge ratio, duration, effectiveness | 10-K derivatives footnote | DISPLAY |
| C.5.6 | Commodity cycle position: trough, recovery, peak, decline | Industry analysis | INFERENCE |

### C.6 Operational Execution (10 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| C.6.1 | Product launch track record: success rate, revenue impact | 10-K, earnings calls | EVALUATIVE |
| C.6.2 | Project execution: major initiative delivery, delays, overruns | MD&A, 8-K | EVALUATIVE |
| C.6.3 | Operational incidents: manufacturing issues, cyber, safety (<12mo = RED) | 8-K, 10-K | EVALUATIVE |
| C.6.4 | Quality issues: recalls, complaints, warranty claims increasing | 10-K, FDA, recalls | EVALUATIVE |
| C.6.5 | Capacity utilization: <50% + high fixed costs = RED | MD&A, earnings calls | EVALUATIVE |
| C.6.6 | Supply chain resilience: geographic diversification, inventory buffers | 10-K Risk Factors | INFERENCE |
| C.6.7 | Labor relations: union %, contract expirations, strike history | 10-K, news | EVALUATIVE |
| C.6.8 | Regulatory compliance: operational regulatory status by industry | 10-K, regulatory databases | EVALUATIVE |
| C.6.9 | Environmental compliance: permits, compliance status | EPA, state agencies | EVALUATIVE |
| C.6.10 | Business continuity: disaster recovery capability | 10-K Risk Factors | INFERENCE |

### C.7 Growth Strategy (8 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| C.7.1 | Organic growth drivers: new products, market expansion, price, customer expansion | Investor presentations, MD&A | DISPLAY |
| C.7.2 | R&D investment: R&D / Revenue ratio | Income Statement | DISPLAY |
| C.7.3 | Geographic expansion: international growth plans, high-risk market entry | 10-K, earnings calls | EVALUATIVE |
| C.7.4 | Product pipeline: future releases, launch dates, expected revenue | Investor presentations | DISPLAY |
| C.7.5 | Capital allocation strategy: growth CapEx, M&A, dividends, buybacks, debt paydown | MD&A, earnings calls | DISPLAY |
| C.7.6 | Management execution history: delivered on prior plans? | Compare prior guidance to actuals | EVALUATIVE |
| C.7.7 | Strategic risks: risks to strategy execution | 10-K Risk Factors | INFERENCE |
| C.7.8 | Industry tailwinds/headwinds: macro factors affecting growth | Industry analysis | INFERENCE |

---

## MODULE 06: GOVERNANCE (`06_GOVERNANCE.md`) -- Section D, 78 checks

### D.1 Executive Team (16 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| D.1.1 | CEO assessment: name, age, tenure, prior company, industry experience, controversies | DEF 14A, LinkedIn, news | EVALUATIVE |
| D.1.2 | CFO assessment: name, tenure, CPA, Big 4 experience, restatement history | DEF 14A, LinkedIn | EVALUATIVE |
| D.1.3 | Executive team stability: C-suite turnover rate in past 12 months | 8-K Item 5.02 | EVALUATIVE |
| D.1.4 | Executive background issues: prior securities fraud, SEC bars, failed companies | News, SEC database, PACER | EVALUATIVE |
| D.1.5 | GC/CLO assessment: tenure, securities law experience | DEF 14A, LinkedIn | DISPLAY |
| D.1.6 | COO assessment (if applicable) | DEF 14A | DISPLAY |
| D.1.7 | CTO/CIO assessment (if applicable) | DEF 14A | DISPLAY |
| D.1.8 | Division/segment leaders: key business unit leadership | 10-K, investor presentations | DISPLAY |
| D.1.9 | Bench strength: succession planning for key roles | DEF 14A | INFERENCE |
| D.1.10 | Executive employment agreements: severance, COC multiples, non-competes | DEF 14A, 8-K employment agreements | DISPLAY |
| D.1.11 | Executive hedging/pledging: shares pledged or hedged (pledging = RED flag) | DEF 14A | EVALUATIVE |
| D.1.12 | Executive health/age: key person risk, founder >70 no succession = RED | DEF 14A, news | EVALUATIVE |
| D.1.13 | Non-compete enforceability: can key employees leave easily? | State law, employment agreements | DISPLAY |
| D.1.14 | Recent promotions: internal advancement (positive indicator) | 8-K Item 5.02 | DISPLAY |
| D.1.15 | Compensation competitiveness: pay vs peers to retain talent | DEF 14A peer comparison | DISPLAY |
| D.1.16 | Leadership transitions in progress: planned retirements, transitions | 8-K, news | DISPLAY |

### D.2 Board Structure (18 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| D.2.1 | Board independence: independent / total directors, <50% = RED | DEF 14A director table | EVALUATIVE |
| D.2.2 | CEO/Chairman separation: combined = RED if <50% independent | DEF 14A | EVALUATIVE |
| D.2.3 | Financial expertise: audit committee qualification, no expert = RED | DEF 14A | EVALUATIVE |
| D.2.4 | Board tenure: average years, >15 + no refresh = RED | DEF 14A | EVALUATIVE |
| D.2.5 | Overboarding: directors on 4+ boards = RED | DEF 14A bios | EVALUATIVE |
| D.2.6 | Board diversity: gender, ethnic, skill mix | DEF 14A skills matrix | DISPLAY |
| D.2.7 | Audit committee independence: must be 100% | DEF 14A | EVALUATIVE |
| D.2.8 | Compensation committee independence: must be 100% | DEF 14A | EVALUATIVE |
| D.2.9 | Nominating committee independence | DEF 14A | EVALUATIVE |
| D.2.10 | Board meeting attendance: <75% for any director = RED flag | DEF 14A | EVALUATIVE |
| D.2.11 | Executive sessions: regular sessions without management? | DEF 14A | DISPLAY |
| D.2.12 | Board evaluation process: self-assessment practice | DEF 14A governance | DISPLAY |
| D.2.13 | Risk oversight: board risk committee or process | DEF 14A | DISPLAY |
| D.2.14 | Cyber expertise: directors with technology/cyber experience | DEF 14A bios | DISPLAY |
| D.2.15 | Recent board changes: additions, departures, reasons | 8-K | DISPLAY |
| D.2.16 | Classified board: staggered terms (anti-takeover) | DEF 14A | DISPLAY |
| D.2.17 | Majority voting: director election standard | DEF 14A | DISPLAY |
| D.2.18 | Proxy access: shareholder ability to nominate | DEF 14A | DISPLAY |

### D.3 Ownership & Insider Activity (14 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| D.3.1 | Ownership structure: voting vs economic ownership, insiders, institutions | DEF 14A beneficial ownership | DISPLAY |
| D.3.2 | Dual-class structure: class A/B votes, founder voting control % | DEF 14A | EVALUATIVE |
| D.3.3 | Insider trading activity: net buying/selling past 6 months (>$50M selling = CRITICAL) | Form 4 filings | EVALUATIVE |
| D.3.4 | 10b5-1 plan usage: % of $ sold via pre-arranged plans | Form 4 footnotes | EVALUATIVE |
| D.3.5 | Selling pattern assessment: timing vs material events | Form 4 dates vs 8-K dates | INFERENCE |
| D.3.6 | Founder/CEO ownership level: alignment through ownership | DEF 14A | DISPLAY |
| D.3.7 | Director stock ownership requirements: guidelines | DEF 14A | DISPLAY |
| D.3.8 | Executive stock ownership requirements: CEO 5-6x salary typical | DEF 14A | DISPLAY |
| D.3.9 | Large shareholder activity: 5%+ holder actions, changes | 13F, 13D/G | EVALUATIVE |
| D.3.10 | Related party transactions: self-dealing conflicts | 10-K Related Party, DEF 14A | EVALUATIVE |
| D.3.11 | Loan programs for executives: prohibited post-SOX | DEF 14A | EVALUATIVE |
| D.3.12 | Tax gross-ups: company pays executive taxes | DEF 14A | DISPLAY |
| D.3.13 | Perquisites analysis: personal aircraft, security, housing | DEF 14A Summary Compensation | DISPLAY |
| D.3.14 | Institutional ownership changes: >10% reduction QoQ = RED | 13F quarterly | EVALUATIVE |

### D.4 Compensation (12 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| D.4.1 | Say-on-pay results: approval %, <70% = RED | 8-K annual meeting results | EVALUATIVE |
| D.4.2 | Compensation structure: pay mix (base/bonus/LTI), metric alignment | DEF 14A CD&A | DISPLAY |
| D.4.3 | Short-term incentives: annual bonus design, RED if tied solely to stock price | DEF 14A | EVALUATIVE |
| D.4.4 | Long-term incentives: equity design, best practice 3+ year vesting | DEF 14A | EVALUATIVE |
| D.4.5 | CEO pay vs peers: relative positioning | DEF 14A peer comparison | DISPLAY |
| D.4.6 | CEO pay vs TSR: pay aligned with shareholder returns? | DEF 14A pay-for-performance | EVALUATIVE |
| D.4.7 | Pay ratio: CEO to median employee | DEF 14A | DISPLAY |
| D.4.8 | Clawback policy: recovery of incentive pay | DEF 14A | DISPLAY |
| D.4.9 | Severance arrangements: total potential severance | DEF 14A, employment agreements | DISPLAY |
| D.4.10 | Change in control payments: golden parachute totals | DEF 14A | DISPLAY |
| D.4.11 | Pension/SERP benefits: executive retirement | DEF 14A | DISPLAY |
| D.4.12 | Peer group appropriateness: benchmarks include much larger companies? RED | DEF 14A | EVALUATIVE |

### D.5 Shareholder Rights & Activism (18 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| D.5.1 | Anti-takeover provisions: poison pill, classified board, supermajority, golden parachutes | DEF 14A, Charter, Bylaws | DISPLAY |
| D.5.2 | Activist history: past activist involvement, 13D filings | 13D, news | DISPLAY |
| D.5.3 | Active proxy contest: current proxy battle, board seats sought | DEF 14A, PREC14A | EVALUATIVE |
| D.5.4 | Proxy contest root cause: underperformance, governance, capital allocation | 13D, activist presentations | INFERENCE |
| D.5.5 | Activist demands: board seats, strategic changes, M&A, capital return | 13D, activist presentations | DISPLAY |
| D.5.6 | Proxy contest resolution: settlement, victory, ongoing | 8-K settlement agreements | DISPLAY |
| D.5.7 | Shareholder proposal history: prior proposals and support levels | DEF 14A | DISPLAY |
| D.5.8 | Activism vulnerability assessment: underperformance, weak governance, excess cash | Multiple factors | INFERENCE |
| D.5.9 | Universal proxy rules: impact of SEC 2022 rules | SEC rules | DISPLAY |
| D.5.10 | Supermajority voting requirements | Charter | DISPLAY |
| D.5.11 | Written consent rights: shareholder action without meeting | Charter, Bylaws | DISPLAY |
| D.5.12 | Special meeting rights: threshold %, notice period | Charter, Bylaws | DISPLAY |
| D.5.13 | Cumulative voting: director election method | Charter | DISPLAY |
| D.5.14 | Exclusive forum provisions: litigation forum selection | Charter, Bylaws | DISPLAY |
| D.5.15 | Fee-shifting provisions: loser pays in shareholder suits | Charter, Bylaws | DISPLAY |
| D.5.16 | NOL poison pill: tax asset protection | 8-K, rights plan | DISPLAY |
| D.5.17 | ESG activism: environmental/social proposals | DEF 14A shareholder proposals | DISPLAY |
| D.5.18 | Labor activism: union organizing, labor disputes | News, NLRB | EVALUATIVE |

---

## MODULE 07: MARKET DYNAMICS (`07_MARKET_DYNAMICS.md`) -- Section E, 68 checks

### E.1 Recent Events & Momentum (18 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| E.1.1 | Significant stock drop events (past 24mo): all >10% single-day or >20% multi-day | Yahoo Finance historical | EVALUATIVE |
| E.1.2 | Event window attribution: company-specific vs sector for each drop | Company vs sector ETF same dates | INFERENCE |
| E.1.3 | Momentum direction: price vs 50-day MA, 200-day MA, golden/death cross | Yahoo Finance, TradingView | EVALUATIVE |
| E.1.4 | Lock-up expiration status: expired, upcoming, recent | S-1, calculate from IPO | EVALUATIVE |
| E.1.5 | Secondary offering impact: stock performance vs offering price, dilution | S-3, 424B | EVALUATIVE |
| E.1.6 | Earnings reaction pattern: beat/miss + next-day stock move per quarter | 8-K, earnings, Yahoo Finance | INFERENCE |
| E.1.7 | Guidance changes (8 quarters): 2+ cuts = RED | Earnings releases | EVALUATIVE |
| E.1.8 | Pre-announcement frequency: any pre-announcement = YELLOW | 8-K | EVALUATIVE |
| E.1.9 | Analyst day/investor day events: date + stock reaction | IR calendar | DISPLAY |
| E.1.10 | Conference presentation impact: large drop after = RED | Conference schedule | EVALUATIVE |
| E.1.11 | CEO media appearances: statements vs outcomes | News search | EVALUATIVE |
| E.1.12 | Product launch events: announce vs reality | 8-K, PR | EVALUATIVE |
| E.1.13 | Contract win/loss announcements: material contract loss = RED | 8-K | EVALUATIVE |
| E.1.14 | FDA/regulatory decision events: adverse + drop = RED | Agency decisions, 8-K | EVALUATIVE |
| E.1.15 | M&A announcement reaction: >10% drop on M&A = RED | 8-K | EVALUATIVE |
| E.1.16 | Dividend change events: cut/suspension = RED | 8-K | EVALUATIVE |
| E.1.17 | Share repurchase announcements: actual buybacks vs announced | 8-K, 10-Q | EVALUATIVE |
| E.1.18 | Index inclusion/exclusion: exclusion + drop = YELLOW | S&P, Russell index changes | EVALUATIVE |

### E.2 Short Interest & Trading (20 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| E.2.1 | Short interest level: % of float, vs sector average (SEC-008) | FINRA, Yahoo Finance | EVALUATIVE |
| E.2.2 | Short interest trend: direction over 90 days, increasing >50% = CRITICAL | Historical short data | EVALUATIVE |
| E.2.3 | Days to cover: shares short / avg daily volume | Yahoo Finance | EVALUATIVE |
| E.2.4 | Named short seller reports: Hindenburg, Citron, etc. <6mo = NUCLEAR | News, activist short sites | EVALUATIVE |
| E.2.5 | Borrow fee / cost to borrow: >20% = CRITICAL | Interactive Brokers, S3 Partners | EVALUATIVE |
| E.2.6 | Fail-to-deliver volume: elevated FTDs | SEC FTD data | EVALUATIVE |
| E.2.7 | Dark pool activity: unusual % via ATS | FINRA ATS data | EVALUATIVE |
| E.2.8 | Options put/call ratio: high puts = YELLOW | Options chain | EVALUATIVE |
| E.2.9 | Options volume vs open interest: unusual spikes | Options chain | EVALUATIVE |
| E.2.10 | Implied volatility skew: high put skew = RED | Options chain | EVALUATIVE |
| E.2.11 | Trading volume anomalies: 3x avg = YELLOW | Yahoo Finance | EVALUATIVE |
| E.2.12 | Bid-ask spread: wide spread = liquidity concern | Level 2 data | EVALUATIVE |
| E.2.13 | Block trade activity: large blocks | Bloomberg | EVALUATIVE |
| E.2.14 | Average daily volume trend: declining = YELLOW | Historical volume | EVALUATIVE |
| E.2.15 | Relative volume: >2x sustained = YELLOW | Current vs avg volume | EVALUATIVE |
| E.2.16 | Pre-market/after-hours activity: unusual = YELLOW | Extended hours data | EVALUATIVE |
| E.2.17 | Exchange short sale volume: % of total volume | Exchange data | DISPLAY |
| E.2.18 | Securities lending utilization: high = RED | S3 Partners | EVALUATIVE |
| E.2.19 | Short squeeze probability: high = YELLOW | S3 Partners | EVALUATIVE |
| E.2.20 | Synthetic short position: large synthetic = RED | Options analysis | EVALUATIVE |

### E.3 Ownership Structure (15 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| E.3.1 | Institutional ownership level: % held by institutions, # institutions | 13F, Yahoo Finance | DISPLAY |
| E.3.2 | Institutional ownership trend: net buying/selling quarterly, >15% reduction = RED | 13F comparisons | EVALUATIVE |
| E.3.3 | Top holder concentration: top 5 >50%, hedge fund >15% = activist risk | 13F filings | EVALUATIVE |
| E.3.4 | Insider ownership level: % held by officers/directors | DEF 14A, Form 4 | DISPLAY |
| E.3.5 | Dual-class structure: governance concern | DEF 14A | EVALUATIVE |
| E.3.6 | Controlling shareholder: >50% control | 13D | EVALUATIVE |
| E.3.7 | Founder control | DEF 14A | EVALUATIVE |
| E.3.8 | PE/VC ownership: >30% = exit risk | S-1, 13D | EVALUATIVE |
| E.3.9 | Activist presence: activist = volatility | 13D | EVALUATIVE |
| E.3.10 | Poison pill status: active pill | DEF 14A | DISPLAY |
| E.3.11 | Staggered board: entrenchment concern | DEF 14A | DISPLAY |
| E.3.12 | Supermajority requirements | Charter | DISPLAY |
| E.3.13 | Shareholder rights plan: recent adoption | DEF 14A, 8-K | EVALUATIVE |
| E.3.14 | Share pledge by insiders: pledged shares = RED | DEF 14A | EVALUATIVE |
| E.3.15 | Margin loan risk: insider margin = RED forced selling risk | Proxy | EVALUATIVE |

### E.4 Analyst Sentiment (15 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| E.4.1 | Analyst coverage level: 0-1 analysts = RED (information asymmetry) | Yahoo Finance, Bloomberg | EVALUATIVE |
| E.4.2 | Consensus rating: Strong Buy to Strong Sell scale | Yahoo Finance, TipRanks | DISPLAY |
| E.4.3 | Rating changes (90 days): net upgrades/downgrades, 3+ downgrades in 30d = CRITICAL | News, analyst reports | EVALUATIVE |
| E.4.4 | Price target analysis: current vs avg/high/low target, implied upside/downside | TipRanks, Yahoo Finance | EVALUATIVE |
| E.4.5 | Estimate revisions (90 days): EPS and revenue direction, unanimous down = CRITICAL | Yahoo Finance, Bloomberg | EVALUATIVE |
| E.4.6 | Earnings surprise history: pattern of misses = RED | Earnings data | EVALUATIVE |
| E.4.7 | Revenue surprise history: pattern of misses = RED | Earnings data | EVALUATIVE |
| E.4.8 | Guidance vs consensus: below consensus = RED | Earnings releases | EVALUATIVE |
| E.4.9 | Management credibility: broken promises = RED | Track record | INFERENCE |
| E.4.10 | Conference call tone: negative tone shift = YELLOW | Earnings call transcripts | INFERENCE |
| E.4.11 | Q&A evasiveness: dodging questions = YELLOW | Earnings call transcripts | INFERENCE |
| E.4.12 | Peer comparison: underperforming peers = YELLOW | Peer analysis | EVALUATIVE |
| E.4.13 | Sector analyst views: sector headwinds = YELLOW | Sector reports | EVALUATIVE |
| E.4.14 | Initiation/termination: coverage dropped = RED | Coverage changes | EVALUATIVE |
| E.4.15 | Target price changes: cuts >20% = RED | Analyst reports | EVALUATIVE |

---

## MODULE 08: ALTERNATIVE DATA (`08_ALTERNATIVE_DATA.md`) -- Section F (alt-data), 97 checks

### F.1 Employee Signals (15 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| F.1.1 | Glassdoor overall rating: <3.0 = RED (>50 reviews) | Glassdoor.com | EVALUATIVE |
| F.1.2 | Glassdoor rating trend: declined >0.5 in 12 months = RED | Glassdoor historical | EVALUATIVE |
| F.1.3 | CEO approval rating: <50% = RED | Glassdoor | EVALUATIVE |
| F.1.4 | "Recommend to friend": <50% = RED | Glassdoor | EVALUATIVE |
| F.1.5 | Business outlook: <30% positive = RED | Glassdoor | EVALUATIVE |
| F.1.6 | Glassdoor review themes: fraud/ethics mentions, "sinking ship" = RED | Glassdoor review content | INFERENCE |
| F.1.7 | LinkedIn employee count: >15% decline in 6mo = RED (unreported layoffs) | LinkedIn company page | EVALUATIVE |
| F.1.8 | LinkedIn executive departures: multiple C-suite/VP not in 8-K = RED | LinkedIn profiles | EVALUATIVE |
| F.1.9 | LinkedIn department analysis: sales/revenue teams shrinking = RED | LinkedIn employees | EVALUATIVE |
| F.1.10 | Job posting analysis: hiring freeze + layoffs = RED | LinkedIn Jobs, Indeed | EVALUATIVE |
| F.1.11 | Critical role vacancies: CFO/Controller/GC open >3mo = RED | Job postings | EVALUATIVE |
| F.1.12 | Indeed rating: <3.0 corroborating Glassdoor = RED | Indeed.com | EVALUATIVE |
| F.1.13 | Blind app activity: fraud/layoff discussions = RED | Blind app (tech) | EVALUATIVE |
| F.1.14 | H-1B data: dramatic decline in sponsorships = RED | H1bdata.info | EVALUATIVE |
| F.1.15 | Layoff tracker data: multiple rounds not fully disclosed = RED | Layoffs.fyi, WARN notices | EVALUATIVE |

### F.2 Customer Signals (12 checks) -- alt-data F.2, not scoring F.2

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| F.2.1 | App store rating: <3.0 stars = RED | Apple App Store, Google Play | EVALUATIVE |
| F.2.2 | App store rating trend: declined >0.5 in 6mo = RED | Historical app ratings | EVALUATIVE |
| F.2.3 | App store review themes: billing fraud, data breaches = RED | Recent reviews | INFERENCE |
| F.2.4 | BBB rating: F or D = RED | BBB.org | EVALUATIVE |
| F.2.5 | BBB complaint volume: >100% increase YoY = RED | BBB complaint history | EVALUATIVE |
| F.2.6 | Trustpilot rating: <3.0 = RED | Trustpilot.com | EVALUATIVE |
| F.2.7 | G2/Capterra reviews (B2B): <3.5 + declining = RED | G2.com, Capterra | EVALUATIVE |
| F.2.8 | NPS/customer satisfaction: <0 NPS = RED | Company disclosures | EVALUATIVE |
| F.2.9 | CFPB complaints (financial services): significant spike = RED | CFPB complaint database | EVALUATIVE |
| F.2.10 | Social media complaints: viral negative content = RED | Twitter/X | EVALUATIVE |
| F.2.11 | Reddit discussion: coordinated negative campaigns = RED | Relevant subreddits | EVALUATIVE |
| F.2.12 | Churn indicators: mass cancellation reports = RED | Reviews, social media | EVALUATIVE |

### F.3 Regulatory Databases (20 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| F.3.1 | FDA warning letters: <12mo = CRITICAL | FDA.gov Warning Letters | EVALUATIVE |
| F.3.2 | FDA 483 observations: OAI findings = RED | FDA 483 database | EVALUATIVE |
| F.3.3 | FDA import alerts: active = RED | FDA Import Alert database | EVALUATIVE |
| F.3.4 | FDA recalls: Class I = CRITICAL, Class II <12mo = RED | FDA Recalls, 8-K | EVALUATIVE |
| F.3.5 | FDA clinical trial database: failed/terminated = RED | ClinicalTrials.gov | EVALUATIVE |
| F.3.6 | FDA MAUDE database: death/injury reports trending up = RED | FDA MAUDE | EVALUATIVE |
| F.3.7 | OSHA violations: willful <3yr = CRITICAL | OSHA.gov | EVALUATIVE |
| F.3.8 | OSHA fatalities: any fatality under investigation = CRITICAL | OSHA fatality data | EVALUATIVE |
| F.3.9 | EPA ECHO database: SNC = CRITICAL, HPV = RED | EPA ECHO | EVALUATIVE |
| F.3.10 | EPA Superfund: named PRP = CRITICAL | EPA Superfund list | EVALUATIVE |
| F.3.11 | EPA air quality: NOV <2yr = RED | EPA ECHO Air | EVALUATIVE |
| F.3.12 | EPA water quality: SNC for effluents = RED | EPA ECHO Water | EVALUATIVE |
| F.3.13 | MSHA (mining): pattern of violations = CRITICAL | MSHA.gov | EVALUATIVE |
| F.3.14 | NHTSA (auto): open defect investigation = CRITICAL | NHTSA.gov | EVALUATIVE |
| F.3.15 | CPSC (consumer products): active recall = CRITICAL | CPSC.gov | EVALUATIVE |
| F.3.16 | FTC enforcement: active investigation <2yr = RED | FTC.gov cases | EVALUATIVE |
| F.3.17 | State AG actions: multi-state investigation = RED | State AG press releases | EVALUATIVE |
| F.3.18 | EEOC charges: pattern or practice lawsuit = RED | EEOC.gov, news | EVALUATIVE |
| F.3.19 | DOL/Wage & Hour: significant back wages = RED | DOL.gov enforcement | EVALUATIVE |
| F.3.20 | OCC/Banking regulators: consent order = CRITICAL | OCC enforcement | EVALUATIVE |

### F.4 Research & Academic Signals (10 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| F.4.1 | PubPeer activity (life sciences): management publications flagged = CRITICAL | PubPeer.com | EVALUATIVE |
| F.4.2 | Retraction Watch: company-authored retractions = CRITICAL | RetractionWatch.com | EVALUATIVE |
| F.4.3 | Clinical trial data integrity: FDA data integrity letter = RED | FDA reviews | EVALUATIVE |
| F.4.4 | Patent challenges: key claims invalidated = RED | USPTO PTAB | EVALUATIVE |
| F.4.5 | Academic litigation: active dispute over foundational IP = RED | Court records, news | EVALUATIVE |
| F.4.6 | KOL sentiment (life sciences): KOLs publicly critical = RED | Conferences, social media | INFERENCE |
| F.4.7 | Conference presentation issues: withdrawn presentation = RED | Conference records | EVALUATIVE |
| F.4.8 | Peer review concerns: expression of concern issued = RED | Journal notices | EVALUATIVE |
| F.4.9 | Research fraud database: ORI finding = CRITICAL | ORI.hhs.gov | EVALUATIVE |
| F.4.10 | Technology assessment: validity questioned = RED | Academic reviews | EVALUATIVE |

### F.5 Media Monitoring (12 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| F.5.1 | Investigative journalism: fraud/misconduct investigation published = CRITICAL | WSJ, NYT, Bloomberg | EVALUATIVE |
| F.5.2 | Whistleblower reports: detailed fraud allegations = CRITICAL | News, SEC tips | EVALUATIVE |
| F.5.3 | Documentary/podcast coverage: documentary about fraud = RED | Streaming, podcasts | EVALUATIVE |
| F.5.4 | Industry publication coverage: industry critics = RED | Trade press | EVALUATIVE |
| F.5.5 | Local news coverage: environmental/community conflict = RED | Local news | EVALUATIVE |
| F.5.6 | International media: negative coverage in key markets = RED | International news | EVALUATIVE |
| F.5.7 | Financial media sentiment: repeated negative segments = RED | CNBC, Bloomberg TV | EVALUATIVE |
| F.5.8 | Blog/newsletter coverage: fraud allegations from credible source = RED | Seeking Alpha, Substack | EVALUATIVE |
| F.5.9 | News volume spike: spike + negative sentiment = RED | Google News | EVALUATIVE |
| F.5.10 | Executive interviews: evasive, defensive behavior = RED | TV, podcasts | INFERENCE |
| F.5.11 | Conference call sentiment: contentious, defensive management = RED | Earnings transcripts | INFERENCE |
| F.5.12 | PR crisis history: poorly managed past crisis = RED | News archives | EVALUATIVE |

### F.6 Competitive Intelligence (10 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| F.6.1 | Market share trend: losing share significantly = RED | Industry reports | EVALUATIVE |
| F.6.2 | Competitor announcements: direct competitive product launch = RED | Competitor press | EVALUATIVE |
| F.6.3 | Pricing pressure: significant price wars = RED | Industry reports | EVALUATIVE |
| F.6.4 | Technology disruption: disruptive tech gaining traction = RED | Tech news | EVALUATIVE |
| F.6.5 | New entrant threat: major new entrant (big tech, funded startup) = RED | Funding news | EVALUATIVE |
| F.6.6 | Customer win/loss: lost major customers to competitors = RED | Press releases | EVALUATIVE |
| F.6.7 | Talent competition: key executives joined competitor = RED | LinkedIn, news | EVALUATIVE |
| F.6.8 | Patent activity: competitor patent blocks key products = RED | USPTO | EVALUATIVE |
| F.6.9 | Partnership losses: critical partnership terminated = RED | 8-K, press releases | EVALUATIVE |
| F.6.10 | Industry consolidation: competitors merging = RED | Deal announcements | EVALUATIVE |

### F.7 Supply Chain Signals (8 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| F.7.1 | Supplier news: key supplier bankruptcy/disruption = RED | Supplier filings, news | EVALUATIVE |
| F.7.2 | Port/logistics data: significant volume decline = RED | Trade databases | EVALUATIVE |
| F.7.3 | Commodity price impact: key input up >30% unhedged = RED | Commodity pricing | EVALUATIVE |
| F.7.4 | Contract manufacturing issues: contract mfg cited by FDA/EPA = RED | Supplier news, regulatory | EVALUATIVE |
| F.7.5 | Shipping/freight rates: major cost increase exposure = RED | Freight indices | EVALUATIVE |
| F.7.6 | Inventory channel: channel stuffing indicators = RED | Channel checks | EVALUATIVE |
| F.7.7 | Vendor payment practices: stretched payables, slow pay = RED | D&B, supplier forums | EVALUATIVE |
| F.7.8 | Supplier concentration: single-source for critical inputs = RED | 10-K Risk Factors | EVALUATIVE |

### F.8 Digital Signals (10 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| F.8.1 | Website traffic trend: >30% decline YoY = RED | SimilarWeb, Semrush | EVALUATIVE |
| F.8.2 | App download trend: >30% decline = RED | Sensor Tower, App Annie | EVALUATIVE |
| F.8.3 | SEO/SEM position: lost key rankings = RED | Search rankings | EVALUATIVE |
| F.8.4 | Social media following: declining + negative sentiment = RED | Social platforms | EVALUATIVE |
| F.8.5 | Domain authority: low/declining = RED | Moz, Ahrefs | EVALUATIVE |
| F.8.6 | Email marketing indicators: list degradation = RED | Industry data | EVALUATIVE |
| F.8.7 | Conversion rate indicators: below industry benchmarks = RED | Industry benchmarks | EVALUATIVE |
| F.8.8 | Server/infrastructure status: frequent outages = RED | Down Detector | EVALUATIVE |
| F.8.9 | Cybersecurity posture: low security rating = RED | SecurityScorecard, BitSight | EVALUATIVE |
| F.8.10 | Data breach history: major breach <2yr = RED | HaveIBeenPwned | EVALUATIVE |

---

## MODULE 09: PRIOR ACTS & PROSPECTIVE (`09_PRIOR_ACTS_PROSPECTIVE.md`) -- Section G, 85 checks

### G.1 Stock Drop Analysis -- Detailed (19 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| G.1.1 | 52-week decline from high: >70% = NUCLEAR, feeds F.2 | Yahoo Finance | EVALUATIVE |
| G.1.2 | Attribution -- sector comparison: company vs sector ETF return | Sector ETF | INFERENCE |
| G.1.3 | Attribution -- peer comparison: company vs 3-5 direct peers | Competitor tickers | INFERENCE |
| G.1.4 | Single-day drops >10% count: 3+ in 12mo = CRITICAL | Yahoo Finance historical | EVALUATIVE |
| G.1.4a | Event-window analysis: 0/1/5/10-day sector-adjusted returns for each material event | Yahoo Finance, sector ETF, peers | INFERENCE |
| G.1.4b | Cumulative loss calculation: total market cap loss across all event windows | Market cap x decline % | EVALUATIVE |
| G.1.4c | Recovery analysis: current price vs post-event low, no recovery = RED | Yahoo Finance | EVALUATIVE |
| G.1.5 | Drop #1 detailed analysis: date, magnitude, trigger, attribution, disclosure quality, litigation | Yahoo Finance, 8-K, news | INFERENCE |
| G.1.6 | Drop #2 detailed analysis (same format) | Yahoo Finance, 8-K, news | INFERENCE |
| G.1.7 | Drop #3 detailed analysis (same format) | Yahoo Finance, 8-K, news | INFERENCE |
| G.1.8 | Drop #4 detailed analysis (if applicable) | Yahoo Finance, 8-K, news | INFERENCE |
| G.1.9 | Total actionable drops: drops >10% with open statutes not covered by existing litigation | Court records, filing dates | EVALUATIVE |
| G.1.10 | 90-day volatility: >8% = RED, feeds F.8 | Yahoo Finance 90-day historical | EVALUATIVE |
| G.1.11 | Volatility vs sector: >2x sector = RED | Company vol / sector ETF vol | EVALUATIVE |
| G.1.12 | Beta analysis: >2.5 = RED (+2 to F.8) | Yahoo Finance 5-year monthly | EVALUATIVE |
| G.1.13 | Max drawdown (12 months): >60% = CRITICAL | Yahoo Finance historical | EVALUATIVE |
| G.1.14 | Recovery analysis: still near lows = RED | Yahoo Finance | EVALUATIVE |
| G.1.15 | Volume during drops: >5x average = RED (panic selling) | Yahoo Finance volume | EVALUATIVE |
| G.1.16 | Drop timing vs disclosures: drop before 8-K = CRITICAL (insider knowledge) | 8-K dates vs drops | INFERENCE |

### G.2 Existing Litigation Analysis (12 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| G.2.1 | Active securities class actions: all cases, class periods, status, MTD outcome | Stanford SCAC, PACER | EVALUATIVE |
| G.2.2 | Prior securities settlements: settlement amount, time since (<3yr = CRITICAL) | Stanford SCAC | EVALUATIVE |
| G.2.3 | Derivative litigation: all cases, demand status | PACER, Delaware Chancery | EVALUATIVE |
| G.2.4 | SEC enforcement history: active investigation = CRITICAL | SEC.gov Litigation Releases | EVALUATIVE |
| G.2.5 | DOJ/Criminal history: active = NUCLEAR | DOJ.gov, news | EVALUATIVE |
| G.2.6 | State AG actions: state, allegations, status | State AG press releases | EVALUATIVE |
| G.2.7 | Industry-specific regulatory history: agency, matter, status, penalty | Respective agency databases | EVALUATIVE |
| G.2.8 | Class period coverage analysis: existing class periods vs policy periods | Litigation timeline vs policy | EVALUATIVE |
| G.2.9 | Settlement adequacy analysis: settlement vs claimed damages | Settlement records | EVALUATIVE |
| G.2.10 | Related party litigation: suits involving insiders | Court records, 10-K | EVALUATIVE |
| G.2.11 | Books & records demands: Section 220 demands, broad scope = RED | 10-K, court records | EVALUATIVE |
| G.2.12 | Appraisal litigation: M&A appraisal proceedings | Delaware Chancery | EVALUATIVE |

### G.3 Prospective Triggers (18 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| G.3.1 | Upcoming earnings: date, consensus EPS/revenue, miss risk, stock impact estimate | Earnings calendar, estimates | INFERENCE |
| G.3.2 | Guidance changes expected: cut likely, uncertain, or maintained | Prior guidance, analyst commentary | INFERENCE |
| G.3.3 | Pending FDA decisions (life sciences): PDUFA dates, approval probability | ClinicalTrials.gov | EVALUATIVE |
| G.3.4 | Clinical trial readouts: phase, indication, binary vs continuous, impact if failed | ClinicalTrials.gov | EVALUATIVE |
| G.3.5 | Patent expirations: key cliff dates, revenue at risk, generic competition | Patent filings, 10-K | EVALUATIVE |
| G.3.6 | Contract renewals: major customer/supplier expiring, revenue/cost, renewal risk | 10-K, 8-K | EVALUATIVE |
| G.3.7 | Debt maturities: amount, date, refinancing plan, risk if unable | 10-K debt footnotes | EVALUATIVE |
| G.3.8 | Regulatory deadlines: compliance deadlines, penalties for non-compliance | Regulatory filings | EVALUATIVE |
| G.3.9 | Legal proceedings timeline: upcoming court dates, potential outcomes | Court dockets | EVALUATIVE |
| G.3.10 | Activist campaign milestones: proxy season, board elections | Proxy filings | EVALUATIVE |
| G.3.11 | Product launch dates: expected revenue, delay risk | Company announcements | EVALUATIVE |
| G.3.12 | Restructuring milestones: expected completion, savings target, miss risk | 8-K, earnings calls | EVALUATIVE |
| G.3.13 | Acquisition closing dates: regulatory approvals, break fee | 8-K, merger agreements | EVALUATIVE |
| G.3.14 | Divestiture dates: expected proceeds, failed sale risk | 8-K, announcements | EVALUATIVE |
| G.3.15 | Credit rating reviews: agency, date, expected direction | Rating agency announcements | EVALUATIVE |
| G.3.16 | Index inclusion/exclusion: likely exclusion = forced selling = RED | Index methodology | EVALUATIVE |
| G.3.17 | Lock-up expirations: shares released, % of float, selling pressure | S-1, prospectus | EVALUATIVE |
| G.3.18 | Warrant/convert exercises: exercise price, dilution %, in-the-money? | 10-K, warrant terms | EVALUATIVE |

### G.4 Disclosure Gap Analysis (12 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| G.4.1 | Earnings quality vs disclosure: material issues not discussed = RED | Financials vs MD&A | EVALUATIVE |
| G.4.2 | Risk factor currency: known issues not in risk factors = RED | 10-K vs actual events | EVALUATIVE |
| G.4.3 | Forward-looking statement support: aggressive guidance without caveats = RED | Safe harbor language | EVALUATIVE |
| G.4.4 | Material contract disclosure: key contracts not filed = RED | Exhibit list | EVALUATIVE |
| G.4.5 | Related party transparency: undisclosed material relationships = RED | 10-K footnotes, proxy | EVALUATIVE |
| G.4.6 | Segment reporting quality: aggregation obscures performance = RED | 10-K segments | EVALUATIVE |
| G.4.7 | Goodwill impairment testing disclosure: no cushion disclosure = RED | 10-K goodwill footnote | EVALUATIVE |
| G.4.8 | Off-balance sheet disclosure: material OBS not quantified = RED | 10-K contractual obligations | EVALUATIVE |
| G.4.9 | Litigation disclosure completeness: material litigation not disclosed = RED | 10-K vs court records | EVALUATIVE |
| G.4.10 | Revenue recognition policy clarity: complex/unclear = RED | 10-K Note 2 | EVALUATIVE |
| G.4.11 | Cybersecurity incident disclosure: known incident not disclosed = RED | 8-K Item 1.05, 10-K | EVALUATIVE |
| G.4.12 | Management discussion quality: boilerplate, no real analysis = RED | 10-K MD&A | INFERENCE |

### G.5 Insider Trading Deep Dive (12 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| G.5.1 | Net insider position (6mo): >$50M net selling = CRITICAL, feeds F.7 | Form 4 filings | EVALUATIVE |
| G.5.2 | CEO trading activity: sold >50% holdings = CRITICAL (+3 to F.7) | Form 4 filings | EVALUATIVE |
| G.5.3 | CFO trading activity: same thresholds as CEO | Form 4 filings | EVALUATIVE |
| G.5.4 | 10b5-1 plan analysis: <50% via plans = RED (+2 to F.7) | Form 4 footnotes | EVALUATIVE |
| G.5.5 | Timing analysis: heavy sales before negative news = CRITICAL | Form 4 vs 8-K dates | INFERENCE |
| G.5.6 | Director trading: material transactions by directors | Form 4 filings | DISPLAY |
| G.5.7 | Section 16 late filings: pattern of late filings = RED | SEC EDGAR filing dates | EVALUATIVE |
| G.5.8 | Derivative transactions: material options/RSU exercises | Form 4 Table II | DISPLAY |
| G.5.9 | Gift transactions: large gifts before decline = RED (tax strategy) | Form 4 gift codes | EVALUATIVE |
| G.5.10 | Rule 144 sales: material unregistered share sales | Form 144 filings | DISPLAY |
| G.5.11 | Insider pledging: material shares pledged = RED | DEF 14A beneficial ownership | EVALUATIVE |
| G.5.12 | Insider hedging: hedging permitted and used = RED | DEF 14A hedging policy | EVALUATIVE |

### G.6 Runoff-Specific Analysis (12 checks)

| ID | Question / Purpose | Data Source | Type |
|----|-------------------|-------------|------|
| G.6.1 | Transaction structure: buyer, deal value, structure, premium, close date | Merger agreement (8-K exhibit) | DISPLAY |
| G.6.2 | Rep & warranty survival: general, fundamental, financial, tax rep periods | Merger agreement | DISPLAY |
| G.6.3 | Indemnification cap: general cap, fundamental cap, per-claim deductible | Merger agreement | DISPLAY |
| G.6.4 | Escrow/holdback: amount, release schedule, claim process | Merger agreement | DISPLAY |
| G.6.5 | R&W insurance: obtained?, limit, retention, exclusions | Deal announcements | DISPLAY |
| G.6.6 | Known issues analysis: issues requiring coverage exclusion | Disclosure schedules, 10-K | EVALUATIVE |
| G.6.7 | Material adverse change definition: MAC carve-outs, buyer's out | Merger agreement | DISPLAY |
| G.6.8 | Management transition: key executives leaving/staying | 8-K, deal announcements | DISPLAY |
| G.6.9 | Post-close discovery risk: financial, contract, compliance, customer, employee issues | Due diligence analysis | INFERENCE |
| G.6.10 | Appraisal rights: available?, exercise threshold | State law, merger agreement | DISPLAY |
| G.6.11 | Shareholder litigation risk: premium challenge, process challenge, disclosure challenge | Deal premium, process analysis | INFERENCE |
| G.6.12 | Tail policy needs: required period, who purchases, limit requirements | D&O program analysis | DISPLAY |

---

## MODULE 10: SCORING (`10_SCORING.md` + `10_SCORING_F2_UPDATE.md`)

### NT -- Nuclear Triggers (8 rules)

| ID | Question / Purpose | Data Source | Min Score |
|----|-------------------|-------------|-----------|
| NT-001 | Active securities class action | Stanford SCAC | 70 (EXTREME) |
| NT-002 | Wells Notice disclosed | 10-K, 8-K | 70 (EXTREME) |
| NT-003 | DOJ criminal investigation | DOJ.gov, 10-K | 70 (EXTREME) |
| NT-004 | Going concern opinion | 10-K auditor report | 50 (HIGH) |
| NT-005 | Restatement <12 months | 8-K Item 4.02 | 50 (HIGH) |
| NT-006 | SPAC <18mo + stock <$5 | Filing dates, price | 50 (HIGH) |
| NT-007 | Short seller report <6 months | Activist short websites | 50 (HIGH) |
| NT-008 | Stock decline >60% company-specific | Yahoo Finance + attribution | 50 (HIGH) |

### F.1 Prior Litigation (7 rules, 0-20 pts)

| ID | Question / Purpose | Data Source | Points |
|----|-------------------|-------------|--------|
| F1-001 | Active securities class action | Stanford SCAC | 20 + NT-001 |
| F1-002 | Securities suit settled <3 years | Stanford SCAC | 18 |
| F1-003 | Securities suit settled 3-5 years | Stanford SCAC | 15 |
| F1-004 | Securities suit settled 5-10 years | Stanford SCAC | 10 |
| F1-005 | SEC enforcement action <5 years | SEC.gov Lit Releases | 12 |
| F1-006 | Derivative suit <5 years | PACER, Delaware | 6 |
| F1-007 | No prior litigation | Stanford SCAC verified | 0 |

### F.2 Stock Decline (8 rules, 0-15 pts)

| ID | Question / Purpose | Data Source | Points |
|----|-------------------|-------------|--------|
| F2-001 | Decline from 52-week high >60% | Yahoo Finance, STK-007 | 15 |
| F2-002 | Decline 50-60% | Yahoo Finance, STK-007 | 12 |
| F2-003 | Decline 40-50% | Yahoo Finance, STK-007 | 9 |
| F2-004 | Decline 30-40% | Yahoo Finance, STK-007 | 6 |
| F2-005 | Decline 20-30% | Yahoo Finance, STK-007 | 3 |
| F2-006 | Decline <20% | Yahoo Finance, STK-007 | 0 |
| F2-007 | Company underperformed sector by >20 ppts | STK-008 attribution | +3 bonus (cap 15) |
| F2-008 | CASCADE or ACCELERATION pattern detected (v4.7: via STK-010) | STK-010 patterns | +2, flag |

### F.3 Restatement & Audit (7 rules, 0-12 pts)

| ID | Question / Purpose | Data Source | Points |
|----|-------------------|-------------|--------|
| F3-001 | Restatement <12 months | 8-K Item 4.02 | 12 + NT-005 |
| F3-002 | Restatement 12-24 months | 8-K Item 4.02 | 10 |
| F3-003 | Restatement 2-5 years | 8-K history | 6 |
| F3-004 | Auditor fired/resigned with disagreement | 8-K Item 4.01 | 10 |
| F3-005 | Material weakness (SOX 404) | 10-K Item 9A | 5 |
| F3-006 | Auditor change (routine rotation) | 8-K Item 4.01 | 2 |
| F3-007 | Clean | 8-K search, 10-K | 0 |

### F.4 IPO/SPAC/M&A (6 rules, 0-10 pts)

| ID | Question / Purpose | Data Source | Points |
|----|-------------------|-------------|--------|
| F4-001 | SPAC merger <18 months | 8-K merger date | 10 |
| F4-002 | SPAC merger 18-36 months | 8-K merger date | 7 |
| F4-003 | IPO <18 months | S-1 date | 8 |
| F4-004 | IPO 18-36 months | S-1 date | 5 |
| F4-005 | Major M&A (>25% market cap) <2 years | 8-K | 6 |
| F4-006 | IPO/SPAC >36 months or N/A | Filing history | 0 |

### F.5 Guidance Misses (6 rules, 0-8 pts)

| ID | Question / Purpose | Data Source | Points |
|----|-------------------|-------------|--------|
| F5-001 | 4+ misses in past 8 quarters | 8-K earnings vs guidance | 8 |
| F5-002 | 3 misses | 8-K earnings vs guidance | 6 |
| F5-003 | 2 misses | 8-K earnings vs guidance | 4 |
| F5-004 | 1 miss | 8-K earnings vs guidance | 2 |
| F5-005 | 0 misses | 8-K earnings vs guidance | 0 |
| F5-006 | Any single miss >15% vs guidance | 8-K earnings vs guidance | +2 bonus (cap 8) |

### F.6 Short Interest -- Contextual (12 rules, 0-8 pts)

| ID | Question / Purpose | Data Source | Points |
|----|-------------------|-------------|--------|
| F6-R01 | Short interest >3x sector average | Yahoo Finance, FINRA | 4 |
| F6-R02 | Short interest 2-3x sector average | Yahoo Finance, FINRA | 3 |
| F6-R03 | Short interest 1.5-2x sector average | Yahoo Finance, FINRA | 2 |
| F6-R04 | Short interest 1-1.5x sector average | Yahoo Finance, FINRA | 1 |
| F6-R05 | Short interest <1x sector average | Yahoo Finance, FINRA | 0 |
| F6-M01 | Market cap <$1B modifier | Market cap | +2 |
| F6-M02 | Market cap $1-5B modifier | Market cap | +1 |
| F6-M03 | Market cap >$5B modifier | Market cap | +0 |
| F6-D01 | SI increased >50% (3 months) | FINRA trend | +2 |
| F6-D02 | SI increased 25-50% | FINRA trend | +1 |
| F6-D03 | SI stable (+-25%) | FINRA trend | +0 |
| F6-D04 | SI decreased >25% | FINRA trend | -1 |

| ID | Question / Purpose | Data Source | Points |
|----|-------------------|-------------|--------|
| F6-X01 | Named short report <6 months | Activist short sites | Min 6 + NT-007 |
| F6-X02 | Named short report 6-12 months | Activist short sites | Min 4 |

### F.7 Insider Trading -- Contextual (14 rules, 0-8 pts)

| ID | Question / Purpose | Data Source | Points |
|----|-------------------|-------------|--------|
| F7-H01 | CEO/CFO sold >50% of holdings (6mo) | Form 4 | 5 |
| F7-H02 | CEO/CFO sold 25-50% of holdings | Form 4 | 3 |
| F7-H03 | CEO/CFO sold 10-25% of holdings | Form 4 | 1 |
| F7-H04 | CEO/CFO sold <10% of holdings | Form 4 | 0 |
| F7-C01 | Total selling >1% of market cap | Form 4, market cap | 3 |
| F7-C02 | Total selling 0.5-1% of market cap | Form 4, market cap | 2 |
| F7-C03 | Total selling 0.1-0.5% of market cap | Form 4, market cap | 1 |
| F7-C04 | Total selling <0.1% of market cap | Form 4, market cap | 0 |
| F7-P01 | >50% of $ sold outside 10b5-1 plans | Form 4 footnotes | +2 |
| F7-P02 | New 10b5-1 adopted <90 days before sale | Form 4 footnotes | +1 |
| F7-P03 | All sales via 10b5-1 established >6mo prior | Form 4 footnotes | -1 |
| F7-T01 | Heavy selling within 90 days before >15% drop | Form 4 dates vs price | +2 (scienter) |
| F7-T02 | Sales volume >2x vs prior 12mo pattern | Form 4 history | +1 |
| F7-T03 | Consistent quarterly 10b5-1 pattern | Form 4 history | -1 |

| ID | Question / Purpose | Data Source | Points |
|----|-------------------|-------------|--------|
| F7-B01 | Net buying by CEO or CFO (6mo) | Form 4 | Cap at 2 max |
| F7-B02 | Significant open market buys by multiple insiders | Form 4 | Cap at 1 max |

### F.8 Volatility -- Contextual (10 rules, 0-7 pts)

| ID | Question / Purpose | Data Source | Points |
|----|-------------------|-------------|--------|
| F8-R01 | Volatility >3x sector ETF | Yahoo Finance 90-day calc | 4 |
| F8-R02 | Volatility 2-3x sector ETF | Yahoo Finance 90-day calc | 3 |
| F8-R03 | Volatility 1.5-2x sector ETF | Yahoo Finance 90-day calc | 2 |
| F8-R04 | Volatility 1-1.5x sector ETF | Yahoo Finance 90-day calc | 1 |
| F8-R05 | Volatility <1x sector ETF | Yahoo Finance 90-day calc | 0 |
| F8-D01 | Volatility increased >100% (6mo) | Historical comparison | +2 |
| F8-D02 | Volatility increased 50-100% | Historical comparison | +1 |
| F8-D03 | Volatility stable (+-50%) | Historical comparison | +0 |
| F8-D04 | Volatility decreased >50% | Historical comparison | -1 |
| F8-E01 | 5+ days with >5% move (past 90 days) | Yahoo Finance | +2 |
| F8-E02 | 3-4 days with >5% move | Yahoo Finance | +1 |
| F8-E03 | 0-2 days with >5% move | Yahoo Finance | +0 |

### F.9 Financial Distress -- Contextual (12 rules, 0-6 pts)

| ID | Question / Purpose | Data Source | Points |
|----|-------------------|-------------|--------|
| F9-L01 | Leverage >sector critical threshold | 10-K, sector baselines | 3 |
| F9-L02 | Leverage elevated to critical | 10-K, sector baselines | 2 |
| F9-L03 | Leverage normal to elevated | 10-K, sector baselines | 1 |
| F9-L04 | Leverage below normal | 10-K, sector baselines | 0 |
| F9-C01 | Cash runway <6 months | 10-K/Q cash flow | 4 |
| F9-C02 | Cash runway 6-12 months | 10-K/Q cash flow | 2 |
| F9-C03 | Cash runway 12-18 months | 10-K/Q cash flow | 1 |
| F9-C04 | Cash runway >18 months or OCF positive | 10-K/Q cash flow | 0 |
| F9-T01 | Leverage increased >50% YoY | 10-K/Q | +1 |
| F9-T02 | Cash declined >40% QoQ (non-seasonal) | 10-K/Q | +1 |
| F9-T03 | EBITDA margin declined >500bps YoY | 10-K/Q | +1 |
| F9-T04 | Metrics improving (leverage down, cash up) | 10-K/Q | -1 |

| ID | Question / Purpose | Data Source | Points |
|----|-------------------|-------------|--------|
| F9-X01 | Going concern opinion | 10-K auditor report | 6 + NT-004 |
| F9-X02 | Covenant breach or waiver | 8-K, credit agreement | Min 4 |
| F9-X03 | Missed debt payment | 8-K | 6 |
| F9-X04 | Credit rating downgrade to junk (<BBB-) in past 12mo | Rating agencies | +2 |

### F.10 Governance Weakness (5 rules, 0-3 pts, cumulative)

| ID | Question / Purpose | Data Source | Points |
|----|-------------------|-------------|--------|
| F10-001 | CEO = Chairman + Board independence <50% | DEF 14A | 3 |
| F10-002 | CEO = Chairman alone OR Board independence <66% alone | DEF 14A | 2 |
| F10-003 | CEO tenure <6 months | 8-K Item 5.02, DEF 14A | 1 |
| F10-004 | CFO tenure <6 months | 8-K Item 5.02, DEF 14A | 1 |
| F10-005 | Strong governance (none of above) | DEF 14A | 0 |

### TR -- Tier Rules (6 rules)

| ID | Score Range | Tier | 18-Mo Probability | Posture |
|----|------------|------|-------------------|---------|
| TR-001 | 70-100 | EXTREME | >20% (1 in 5) | Decline or 2-3x rate |
| TR-002 | 50-69 | HIGH | 10-20% (1 in 5-10) | 1.5-2x rate, higher retention |
| TR-003 | 30-49 | AVERAGE | 5-10% (1 in 10-20) | Market rate |
| TR-004 | 15-29 | BELOW AVG | 2-5% (1 in 20-50) | Discount available |
| TR-005 | 0-14 | MINIMAL | <2% (1 in 50+) | Best rates |
| TR-006 | -- | CEILING | Never claim >25% probability | Probability cap |

---

## MODULE 13: SECTOR BASELINES (`13_SECTOR_BASELINES.md`)

Reference tables only (no numbered checks). Provides sector-specific baselines for:

| Area | Sectors Covered | Used By |
|------|----------------|---------|
| Market Cap Tiers | MEGA >$50B, LARGE $10-50B, MID $2-10B, SMALL $500M-2B, MICRO <$500M | F.6, F.7 |
| F.6 Short Interest Baselines | 10 sectors with typical range + elevated threshold | F.6 scoring |
| F.8 Volatility Baselines (90-day) | 11 sectors with typical, elevated, high thresholds | F.8 scoring |
| F.9 Leverage Baselines (Debt/EBITDA) | 10 sectors with normal, elevated, critical ranges | F.9 scoring |
| Sector ETF Reference | 11 sectors with primary + alternative ETFs | All attribution checks |
| Peer Group Guidance | Tech, Healthcare, Financials sub-sectors | B.5.3, E.1.2, G.1.3 |

---

## MODULE 14: STOCK MONITORING REFERENCE (`14_STOCK_MONITORING_REFERENCE.md`)

Reference methodology only (no numbered checks beyond STK-001 to STK-010 documented above). Provides:

| Topic | Purpose | Used By |
|-------|---------|---------|
| Decline % calculation formula | (Reference - Current) / Reference x 100 | STK-002 to STK-007 |
| Attribution calculation steps | Company, Sector, Market component decomposition | STK-008 |
| Recency weight schedule | 30d=1.5x, 31-90d=1.0x, 91-180d=0.75x, 181-365d=0.5x | STK-009 |
| ACCELERATION detection | STK-004 > STK-005 and both negative | STK-010 |
| CASCADE detection | STK-003 > STK-002 after >5% single day | STK-010 |
| STABILIZATION detection | STK-003 flat and prior decline exists | STK-010 |
| RECOVERY detection | Current >10% above 20-day low | STK-010 |
| BREAKDOWN detection | 3+ horizons simultaneously RED | STK-010 |
| Sector volatility hierarchy | 13 sectors ranked lowest to highest volatility | SEC-009 threshold rationale |
| F.2 integration mapping | STK-007 -> F.2 base, STK-008 -> F2-007, STK-010 -> F2-008 | F.2 scoring |

---

## MODULE 02: TRIGGER MATRIX (`02_TRIGGER_MATRIX_V4_7.md`)

Mapping rules (no numbered checks). Routes QS/STK findings to deep-dive sections:

| Finding | Loads Sections |
|---------|---------------|
| QS-001 (active SCA) | Section A (03), Section G (09) |
| QS-002 (Wells Notice) | Section A (03) |
| QS-003 (SPAC) | Section A (03), Section B (04) |
| QS-004 (restatement) | Section A (03), Section B (04) |
| QS-005 (auditor change) | Section A (03), Section B (04) |
| QS-006 (going concern) | Section A (03), Section B (04) |
| QS-007 (material weakness) | Section A (03), Section B (04) |
| QS-008 (DOJ) | Section A (03) |
| QS-009 (SEC investigation) | Section A (03) |
| QS-011 (bankruptcy risk) | Section A (03), Section B (04) |
| QS-012 (short seller report) | Section E (07), Section F (08) |
| QS-013 to QS-022 (financial) | Section B (04) |
| STK RED + company-specific | Section E (07), Section G (09) |
| STK-010 BREAKDOWN/CASCADE | Section E (07) |
| QS-024 (delisting) | Section E (07) |
| QS-025 (IPO <24mo) | Section A (03) |
| QS-028 (analyst downgrades) | Section E (07) |
| QS-030 (short interest) | Section E (07) |
| QS-033 (CEO/CFO tenure) | Section D (06) |
| QS-034 (board independence) | Section D (06) |
| QS-035 (insider selling) | Section D (06), Section G (09) |
| QS-038 (proxy contest) | Section D (06) |
| SEC-001 = BIOT | Section B.7.2 (life sciences KPIs) |
| SEC-001 = TECH (SaaS) | Section B.7.1 (SaaS KPIs) |
| SEC-001 = FINS | Section B.7.3 (financial KPIs) |
| SEC-001 = CDIS (retail) | Section B.7.4 (retail KPIs) |
| SEC-001 = ENGY | Section C.5 (commodity exposure) |
| Existing claims / runoff | Section G (09) mandatory |

---

## SUMMARY COUNTS

| Module | File | Check Count | Rule Count |
|--------|------|-------------|------------|
| 00 Project Instructions | 00_PROJECT_INSTRUCTIONS_V4_7.md | -- | 36 (TRI-5, STR-5, IND-4, DDR-3, EX-10, ESC-7, VER/ZER-2) |
| 01 Quick Screen | 01_QUICK_SCREEN_V4_7.md | 40 QS active | 68 (NEG-9, SEC-9, STK-10, QS-40) |
| 02 Trigger Matrix | 02_TRIGGER_MATRIX_V4_7.md | -- | Routing rules (no count) |
| 03 Litigation/Regulatory | 03_LITIGATION_REGULATORY.md | 37 | 37 |
| 04 Financial Health | 04_FINANCIAL_HEALTH.md | 112 | 112 |
| 05 Business Model | 05_BUSINESS_MODEL.md | 74 | 74 |
| 06 Governance | 06_GOVERNANCE.md | 78 | 78 |
| 07 Market Dynamics | 07_MARKET_DYNAMICS.md | 68 | 68 |
| 08 Alternative Data | 08_ALTERNATIVE_DATA.md | 97 | 97 |
| 09 Prior Acts/Prospective | 09_PRIOR_ACTS_PROSPECTIVE.md | 85 | 85 |
| 10 Scoring | 10_SCORING.md + F2 patch | -- | ~100 (NT-8, F1-7, F2-8, F3-7, F4-6, F5-6, F6-14, F7-16, F8-11, F9-16, F10-5, TR-6) |
| 13 Sector Baselines | 13_SECTOR_BASELINES.md | -- | Reference tables |
| 14 Stock Monitoring Ref | 14_STOCK_MONITORING_REFERENCE.md | -- | Reference methodology |
| **TOTAL** | | **594 new business** | **287 indexed** |

---

**END OF EXHAUSTIVE OLD UNDERWRITER ANALYSIS**
