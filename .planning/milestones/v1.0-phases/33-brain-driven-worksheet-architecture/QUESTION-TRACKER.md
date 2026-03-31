# Question Tracker — Per-Question Categorization

**Purpose:** Every question traced through: complexity layer, current state, new subsection assignment, data source, blocker.
**Generated:** 2026-02-20 during full 45-subsection review

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Working — produces evaluative result (CLEAR or TRIGGERED) |
| 🔴 | TRIGGERED — check fires and flags an issue |
| 🟡 | Partial — data flows but returns INFO (no threshold evaluation) |
| ⚠️ | SKIPPED — check defined but data field not populated |
| ❌ | Not built — no extraction, mapper, or acquisition pipeline |

**Complexity Layers:** DISPLAY, EVALUATE, COMPUTE, INFER, HUNT, SYNTHESIZE

---

# SECTION 1: COMPANY

## 1.1 Company Snapshot → 4 display blocks (REVIEWED)

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 1.1.1 | Company name, ticker, sector | DISPLAY | ✅ | Apple Inc / AAPL / TECH | SEC + yfinance | — |
| 1.1.2 | SIC / GICS code | DISPLAY | 🟡 | SIC=3571 / GICS=⚠️ | SEC + yfinance | DN-005 (GICS), DN-015 (mapping) |
| 1.1.3 | HQ, state of inc, exchange, FPI | DISPLAY | ✅ | Cupertino CA / CA / NASDAQ / No | SEC + yfinance | — |
| 1.1.4 | Market cap + relative ranking | COMPUTE | 🟡 | $3.9T / ranking not computed | yfinance + peer_group | DN-010 |
| 1.1.5 | Revenue TTM | DISPLAY | ✅ | ~$391B | XBRL | — |
| 1.1.6 | Employee count | DISPLAY | ✅ | 150,000 | 10-K + yfinance (cross-validated) | — |
| 1.1.7 | Years public + lifecycle | COMPUTE | ✅ | ~44 years / Mature | yfinance IPO | — |
| 1.1.8 | Business description (2-3 sentences) | DISPLAY | 🟡 | Raw 10-K text (needs summarization) | 10-K Item 1 | DN-006, DN-014 |
| 1.1.9 | Active SCA count | DISPLAY | ✅ | 0 | SCAC | — |
| 1.1.10 | Prior SCA count | DISPLAY | 🔴 | 1 (TRIGGERED) | SCAC | — |
| 1.1.11 | Derivative suit count | DISPLAY | 🔴 | 3 (TRIGGERED) | 10-K Item 3 | — |

## 1.2 Business Model & Revenue → 7 analytical blocks (REVIEWED)

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 1.2.1 | Business model narrative | DISPLAY | 🟡 | Raw 10-K text | 10-K Item 1 | DN-006 |
| 1.2.2 | Revenue by product/service segment | DISPLAY | ❌ | Mention count only | 10-K Item 7 | DN-001 |
| 1.2.3 | Revenue by geography | DISPLAY | 🟡 | Country names, no % | 10-K Item 7 | DN-002 |
| 1.2.4 | Gross margin by segment | COMPUTE | ❌ | Not extracted | 10-K Item 7 | DN-003 |
| 1.2.5 | Revenue type (recurring/one-time) | EVALUATE | 🟡 | Mention count | 10-K Item 1 | DN-008 |
| 1.2.6 | R&D spend + % of revenue | DISPLAY | ⚠️ | In XBRL, not surfaced | XBRL | DN-009 |
| 1.2.7 | CapEx spend + % of revenue | DISPLAY | ⚠️ | In XBRL, not surfaced | XBRL | DN-009 |
| 1.2.8 | Share buyback program | DISPLAY | ❌ | Not extracted | 10-K/10-Q | DN-004 |
| 1.2.9 | Dividends | DISPLAY | ⚠️ | In yfinance, not surfaced | yfinance | DN-011 |
| 1.2.10 | Net cash/debt position | COMPUTE | ⚠️ | Cash + debt extracted, ratio not | XBRL | DN-012 |
| 1.2.11 | Product concentration % | COMPUTE | ❌ | Needs segment data first | Derived | Needs DN-001 |
| 1.2.12 | Customer concentration | EVALUATE | 🟡 | "Not mentioned" = positive | 10-K | DN-013 |
| 1.2.13 | Business model trajectory | INFER | ❌ | Not extracted | 10-K YoY | DN-007 |

## 1.3 Operational Risk & Dependencies → 3 severity blocks (REVIEWED)

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 1.3.1 | Key supplier names + single-source | HUNT | 🟡 | Mention count=1 | 10-K Item 1/1A | DN-017, DN-019 |
| 1.3.2 | Manufacturing geography classification | COMPUTE | 🟡 | Country names, no classification | Exhibit 21 | DN-018 |
| 1.3.3 | Regulatory actions (agency, status) | HUNT | 🟡 | Count=2 | 10-K Item 1A/3 | DN-020 |
| 1.3.4 | Data types + privacy regime mapping | EVALUATE | 🟡 | Mention count=9 | 10-K Item 1/1A | DN-021 |
| 1.3.5 | AI/ML exposure | DISPLAY | ✅ | 9 mentions | 10-K | — |
| 1.3.6 | Labor risk signals | HUNT | 🔴 | 150K FALSE TRIGGER (employee_count) | 10-K | DN-022 |
| 1.3.7 | Key person dependency | EVALUATE | 🟡 | "Not mentioned" | DEF 14A | DN-023 |
| 1.3.8 | ESG/sustainability claims | HUNT | 🟡 | Shared with regulatory_dep | 10-K | DN-024 |
| 1.3.9 | Government contract exposure | EVALUATE | ✅ | Working | 10-K | — |
| 1.3.10 | Supply chain macro sensitivity | DISPLAY | ✅ | Working | 10-K | — |
| 1.3.11 | Trade policy exposure | EVALUATE | 🟡 | 10 mentions | 10-K | — |

## 1.4 Corporate Structure & Complexity → 2 blocks (REVIEWED)

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 1.4.1 | Subsidiary count + jurisdictions | DISPLAY | ❌ | Not extracted | 10-K Exhibit 21 | DN-025 |
| 1.4.2 | VIEs, SPEs, off-balance-sheet structures | EVALUATE | ❌ | Not extracted | 10-K notes | DN-026 |
| ~~1.4.3~~ | ~~Related-party transactions~~ | — | — | — | — | Moved to 4.2 Structural Governance |

## 1.5 Geographic Footprint (ABSORBED into 1.2 + 1.3)

| # | Question | Layer | State | Absorbed Into |
|---|----------|-------|-------|---------------|
| 1.5.1 | Where does the company operate? | DISPLAY | 🟡 | 1.2 Revenue by Geography |
| 1.5.2 | Jurisdiction-specific risks (FCPA, GDPR, sanctions) | DISPLAY | 🟡 | 1.3 Operational Risks |

## 1.6 M&A & Corporate Transactions → 6 blocks (REVIEWED)

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 1.6.1 | Pending M&A transactions | EVALUATE | 🟡 | 0 INFO | 8-K + 10-K | — |
| 1.6.2 | 2-3 year acquisition history | HUNT | ❌ | Not extracted | 10-K + 8-K + web | DN-027 |
| 1.6.3 | Goodwill + impairment risk | COMPUTE | 🟡 | debt_to_ebitda=0.63 (wrong field) | XBRL | DN-028 |
| 1.6.4 | Integration track record | INFER | ❌ | Not extracted | 10-K YoY | — |
| 1.6.5 | Deal-related litigation | HUNT | 🟡 | "Not mentioned" INFO | SCAC + 10-K | DN-029 |
| 1.6.6 | Divestitures / spin-offs | HUNT | ❌ | Not extracted | 8-K + 10-K | DN-030 |

## 1.7 Competitive Position (ABSORBED into 1.2 + 1.8)

| # | Question | Layer | State | Absorbed Into |
|---|----------|-------|-------|---------------|
| 1.7.1 | Market position + competitive moat | DISPLAY | 🟡 | 1.2 Business Model narrative |
| 1.7.2 | Direct peers + comparison | DISPLAY | 🟡 | 1.8 Peer Comparison block |
| 1.7.3 | Peer SCA rate (contagion risk) | DISPLAY | 🟡 | 1.8 Peer Comparison block |
| 1.7.4 | Industry headwinds/tailwinds | DISPLAY | 🟡 | 1.8 Industry Dynamics block |

## 1.8 Macro & Industry Environment → 3 blocks (REVIEWED)

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 1.8.1 | Sector performance + peer issues | DISPLAY | ✅ | sector_return=5.03, peers=3 | yfinance | — |
| 1.8.2 | Industry consolidation + disruptive threats | DISPLAY | 🟡 | consolidation=5, disruptive=4 (mentions) | 10-K | — |
| 1.8.3 | Macro factors (rates, FX, commodities, trade) | EVALUATE | 🟡 | trade=10, geopolitical=13, FX=3 (mentions) | 10-K | — |
| 1.8.4 | Regulatory/legislative/geopolitical changes | DISPLAY | 🟡 | regulatory=1 mention | 10-K | — |

## 1.9+1.10 Early Warning Signals (MERGED)

### Former 1.9 Employee & Workforce Signals

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 1.9.1 | Glassdoor / Indeed / Blind sentiment | HUNT | ⚠️ | SKIPPED (no web data) | Web scraping | DN-031 |
| 1.9.2 | Unusual hiring patterns (compliance surge) | HUNT | 🟡 | compliance=1, legal=10 (10-K mentions) | 10-K + web | DN-031 |
| 1.9.3 | LinkedIn headcount / departure trends | HUNT | ⚠️ | SKIPPED (no LinkedIn data) | Web scraping | DN-031 |
| 1.9.4 | WARN Act / mass layoff signals | HUNT | ⚠️ | SKIPPED (no web data) | Web search | DN-031 |
| 1.9.5 | Department-level departures | HUNT | ⚠️ | SKIPPED (no LinkedIn data) | 8-K + web | DN-031 |
| 1.9.6 | CEO approval rating trend | HUNT | ⚠️ | SKIPPED (no Glassdoor data) | Web scraping | DN-031 |

### Former 1.10 Customer & Product Signals

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 1.10.1 | CFPB / app ratings / Trustpilot | HUNT | ⚠️ | SKIPPED | CFPB API + web | DN-031 |
| 1.10.2 | Product quality (FDA/NHTSA) | HUNT | ⚠️ | SKIPPED (sector-conditional, N/A) | FDA/NHTSA APIs | DN-031 |
| 1.10.3 | Customer churn / partner instability | HUNT | 🟡 | "Not mentioned" (10-K) | 10-K + web | DN-031 |
| 1.10.4 | Vendor payment / supply chain stress | HUNT | 🟡 | "Not mentioned" (10-K) | 10-K + web | DN-031 |
| 1.10.5 | Web traffic / app download trends | HUNT | ⚠️ | SKIPPED | Web APIs | DN-031 |
| 1.10.6 | Scientific/academic monitoring | HUNT | ⚠️ | SKIPPED (sector-conditional) | Web search | DN-031 |

## 1.11 Risk Calendar & Upcoming Catalysts (REVIEWED — NO CHANGES)

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 1.11.1 | Next earnings + miss risk | EVALUATE | ✅ | 0 CLEAR | yfinance + 8-K | — |
| 1.11.2 | Pending regulatory decisions | EVALUATE | 🟡 | 10 mentions INFO | 10-K + web | — |
| 1.11.3 | M&A closings / shareholder votes | EVALUATE | 🟡 | 0 INFO | 10-K + 8-K | — |
| 1.11.4 | Debt maturities / covenant tests | EVALUATE | 🟡 | Debt dict INFO | 10-K | — |
| 1.11.5 | Lockup / warrant expiry | EVALUATE | ⚠️ | N/A (mature company, correctly skipped) | SEC filings | — |
| 1.11.6 | Contract renewals | EVALUATE | 🟡 | "Not mentioned" INFO | 10-K | — |
| 1.11.7 | Litigation milestones | EVALUATE | 🟡 | 0 INFO | 10-K + SCAC | — |
| 1.11.8 | Industry-specific catalysts | EVALUATE | 🟡 | 0 INFO | 10-K + web | — |

---

# SECTION 2: MARKET (ALL 8 KEPT AS-IS)

## 2.1 Stock Price Performance

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 2.1.1 | Stock position vs 52-week range | EVALUATE | ✅ | decline_from_high=-11.38% CLEAR | yfinance | — |
| 2.1.2 | Volatility profile vs sector/peers | EVALUATE | ✅ | volatility_90d=21.61% CLEAR | yfinance | — |
| 2.1.3 | Performance vs sector/peers | EVALUATE | ✅ | returns_1y=5.03% CLEAR | yfinance | — |
| 2.1.4 | Delisting risk | EVALUATE | ✅ | current_price=$255.78 CLEAR | yfinance | — |
| 2.1.5 | MD&A abnormal positive tone | EVALUATE | 🟡 | "present" INFO (not quantified) | 10-K | DN-035 |

## 2.2 Stock Drop Events

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 2.2.1 | Single-day drops >=5% (18mo) | EVALUATE | ✅ | 2 drops CLEAR | yfinance | — |
| 2.2.2 | Multi-day decline >=10% | EVALUATE | ✅ | -11.38% CLEAR | yfinance | — |
| 2.2.3 | Drops preceded by corrective disclosures | INFER | 🟡 | 2 drops INFO (multi-signal needed) | yfinance + SEC | — |
| 2.2.4 | Recovery from significant drops | EVALUATE | ✅ | returns_1y=5.03% CLEAR | yfinance | — |

## 2.3 Volatility & Trading Patterns

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 2.3.1 | 90-day volatility vs peers | EVALUATE | 🟡 | Cross-mapped from 2.1 | yfinance | — |
| 2.3.2 | Beta | DISPLAY | ❌ | Not extracted | yfinance | DN-032 |
| 2.3.3 | Trading liquidity | DISPLAY | 🟡 | Routes to current_price (wrong field) | yfinance | DN-032 |
| 2.3.4 | Unusual volume / options patterns | DISPLAY | 🟡 | Routes to adverse_event_count=7 | yfinance | — |

## 2.4 Short Interest & Bearish Signals

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 2.4.1 | Short interest % + trend | EVALUATE | ✅ | 0.8% CLEAR, 2.36 days CLEAR | yfinance | — |
| 2.4.2 | Activist short seller reports | HUNT | 🟡 | Routes to short_interest_pct (not web) | Web search | — |

## 2.5 Ownership Structure

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 2.5.1 | Institutional vs insider vs retail | EVALUATE | 🟡 | institutional_pct=65.48% INFO | yfinance | — |
| 2.5.2 | Largest holders + concentration | DISPLAY | 🟡 | institutional_pct only (no individual holders) | yfinance | — |
| 2.5.3 | Institutional ownership trends (6-12mo) | DISPLAY | 🟡 | No trend computation | yfinance | — |
| 2.5.4 | Capital markets liability windows | EVALUATE | ✅ | active_sca_count=0 CLEAR | SEC + SCAC | — |

## 2.6 Analyst Coverage & Sentiment

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 2.6.1 | Analyst count | DISPLAY | ❌ | Routes to beat_rate (wrong field) | yfinance | DN-033 |
| 2.6.2 | Consensus rating + changes | DISPLAY | ❌ | Routes to beat_rate (wrong field) | yfinance | DN-033 |
| 2.6.3 | Price target vs current price | DISPLAY | ❌ | Routes to beat_rate (wrong field) | yfinance | DN-033 |

## 2.7 Valuation Metrics

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 2.7.1 | P/E, EV/EBITDA, PEG ratios | EVALUATE | ⚠️ | All 3 SKIPPED (fields not populated) | yfinance | DN-034 |
| 2.7.2 | Valuation vs peers | EVALUATE | 🟡 | Routes to returns_1y=5.03% (proxy) | yfinance | DN-034 |

## 2.8 Insider Trading Activity

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 2.8.1 | Net insider trading direction | EVALUATE | ✅ | net_selling=1.71% CLEAR + NET_SELLING | Form 4 | — |
| 2.8.2 | CEO/CFO selling significant holdings | EVALUATE | 🔴 | CEO=100% TRIGGERED, CFO=100% TRIGGERED | Form 4 | — |
| 2.8.3 | 10b5-1 plan percentage | EVALUATE | 🟡 | non_10b51=6.7% INFO | Form 4 | — |
| 2.8.4 | Cluster selling (multiple insiders) | INFER | 🔴 | cluster=True, timing=1 TRIGGERED | Form 4 | — |
| 2.8.5 | Suspicious timing vs material events | INFER | ⚠️ | SKIPPED (unusual_timing not populated) | Form 4 + 8-K | — |
| 2.8.6 | Share pledging as collateral | EVALUATE | 🟡 | Routes to ownership_pct (not pledge data) | DEF 14A | DN-036 |
| 2.8.7 | Form 4 compliance issues | EVALUATE | 🟡 | 1.71% INFO | Form 4 | — |

---

# SECTION 3: FINANCIAL (ALL 8 KEPT AS-IS)

## 3.1 Liquidity & Solvency

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 3.1.1 | Current / quick / cash ratios | EVALUATE | 🔴 | current_ratio=0.89 TRIGGERED (threshold <6.0 miscalibrated) | XBRL | Fix threshold |
| 3.1.2 | Cash runway (months) | EVALUATE | ✅ | "Profitable (OCF positive)" INFO | XBRL | — |
| 3.1.3 | Going concern opinion | EVALUATE | ✅ | auditor_opinion="unqualified" INFO | 10-K | — |
| 3.1.4 | Working capital trend (3yr) | EVALUATE | 🟡 | current_ratio=0.89 INFO (qualitative) | XBRL | — |

## 3.2 Leverage & Debt Structure

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 3.2.1 | D/E, Debt/EBITDA | EVALUATE | ✅ | debt_to_ebitda=0.63 CLEAR | XBRL | — |
| 3.2.2 | Interest coverage | EVALUATE | ✅ | interest_coverage=33.83x CLEAR | XBRL | — |
| 3.2.3 | Debt maturity + refinancing risk | EVALUATE | 🟡 | "10 fixed-rate tranches" INFO | 10-K | — |
| 3.2.4 | Covenant compliance risks | EVALUATE | 🟡 | debt_structure dict INFO | 10-K | — |
| 3.2.5 | Credit rating + trajectory | DISPLAY | ❌ | NOT_RUN (FALLBACK_ONLY) | 10-K + web | — |
| 3.2.6 | Off-balance-sheet obligations | EVALUATE | ✅ | contingent_notes coverage | 10-K | — |

## 3.3 Profitability & Growth

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 3.3.1 | Revenue growth / deceleration | EVALUATE | ✅ | "Revenue growing at 6.4%" INFO | XBRL | — |
| 3.3.2 | Margin trajectory | EVALUATE | ✅ | accruals_ratio=0.0015 CLEAR | XBRL | — |
| 3.3.3 | Profitability trajectory | EVALUATE | ✅ | ocf_to_ni=0.9953 INFO | XBRL | — |
| 3.3.4 | Cash flow quality vs earnings | EVALUATE | 🟡 | FIN.TEMPORAL returns metric names | XBRL | Fix temporal |
| 3.3.5 | Segment-level divergences | DISPLAY | 🟡 | narrative text INFO | 10-K | — |
| 3.3.6 | FCF generation + CapEx trend | EVALUATE | 🟡 | narrative text INFO | XBRL | — |

## 3.4 Earnings Quality & Forensic Analysis

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 3.4.1 | Beneish M-Score / Dechow F-Score | COMPUTE | ✅ | M-Score=-2.29 CLEAR | XBRL | — |
| 3.4.2 | Abnormal accruals | COMPUTE | ✅ | accruals_ratio=0.0015 CLEAR | XBRL | — |
| 3.4.3 | Revenue quality (DSO, Q4, deferred) | EVALUATE | 🔴 | DSO=11.86 TRIGGERED yellow; Q4/deferred ⚠️ SKIPPED | XBRL | — |
| 3.4.4 | GAAP vs non-GAAP gap | EVALUATE | ✅ | revenue_quality_score=1.0 CLEAR | 10-K | — |
| 3.4.5 | Financial Integrity Score composite | COMPUTE | ✅ | FIS CLEAR | XBRL | — |
| 3.4.6 | Revenue manipulation patterns | EVALUATE | ✅ | revenue_quality_score=1.0 CLEAR | XBRL | — |
| 3.4.7 | Depreciation Index (DEPI) anomaly | COMPUTE | ✅ | Part of M-Score CLEAR | XBRL | — |

## 3.5 Accounting Integrity & Audit Risk

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 3.5.1 | Auditor + tenure + opinion | EVALUATE | ✅ | "unqualified" INFO | 10-K | — |
| 3.5.2 | Restatement / material weakness | EVALUATE | ✅ | 0 CLEAR | 10-K + 8-K | — |
| 3.5.3 | Auditor change + reason | EVALUATE | ⚠️ | SKIPPED (GOV.EFFECT not populated) | 8-K | DN-036 |
| 3.5.4 | SEC comment letters | EVALUATE | ⚠️ | SKIPPED (not populated) | EDGAR | — |
| 3.5.5 | Critical audit matters (CAMs) | DISPLAY | ✅ | 0 INFO | 10-K | — |
| 3.5.6 | Non-audit fee ratio | EVALUATE | ⚠️ | SKIPPED (DEF 14A gap) | DEF 14A | DN-036 |
| 3.5.7 | PCAOB inspection findings | EVALUATE | ⚠️ | SKIPPED (no web data) | Web search | — |

## 3.6 Financial Distress Indicators

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 3.6.1 | Altman Z-Score | COMPUTE | ✅ | 10.17 CLEAR | XBRL | — |
| 3.6.2 | Ohlson O-Score | COMPUTE | 🟡 | Maps to same zone_of_insolvency | XBRL | Separate computation |
| 3.6.3 | Piotroski F-Score | COMPUTE | 🟡 | Maps to same zone_of_insolvency | XBRL | Separate computation |
| 3.6.4 | Zone of Insolvency | COMPUTE | ✅ | 10.17 CLEAR | XBRL | — |
| 3.6.5 | Credit market signals | EVALUATE | ❌ | NOT_RUN (FALLBACK_ONLY) | Web search | — |
| 3.6.6 | Active restructuring | EVALUATE | 🟡 | FIN.TEMPORAL INFO | 10-K + 8-K | — |

## 3.7 Guidance & Market Expectations

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 3.7.1 | Provides earnings guidance? | EVALUATE | 🟡 | narrative INFO | 8-K | Wiring fix |
| 3.7.2 | Guidance track record | EVALUATE | 🟡 | narrative INFO | yfinance + 8-K | Wiring fix |
| 3.7.3 | Guidance philosophy | DISPLAY | 🟡 | narrative INFO | 8-K | — |
| 3.7.4 | Analyst consensus alignment | EVALUATE | 🟡 | narrative INFO | yfinance + 8-K | Wiring fix |
| 3.7.5 | Market reaction to earnings | EVALUATE | 🟡 | narrative INFO | yfinance | Wiring fix |

## 3.8 Sector-Specific Financial Metrics

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 3.8.1 | Sector-specific KPIs | EVALUATE | ✅ | working_capital_trends=0.89 CLEAR; AI checks INFO | 10-K + XBRL | — |

---

# SECTION 4: GOVERNANCE & DISCLOSURE (REORGANIZED TO 4 BLOCKS)

## NEW 4.1 People Risk (from old 4.1 Board + 4.2 Executive)

### From old 4.1 Board Composition & Quality

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 4.1.1 | Board independence | EVALUATE | ⚠️ | SKIPPED (not populated) | DEF 14A | DN-036 |
| 4.1.2 | CEO-chair duality | EVALUATE | 🔴 | duality=1 TRIGGERED | DEF 14A | — |
| 4.1.3 | Board size + tenure distribution | EVALUATE | ⚠️ | SKIPPED (not populated) | DEF 14A | DN-036 |
| 4.1.4 | Board member relevant experience | DISPLAY | ⚠️ | SKIPPED | DEF 14A | DN-036 |
| 4.1.5 | Classified (staggered) board | EVALUATE | ⚠️ | SKIPPED | DEF 14A | DN-036 |
| 4.1.6 | Board engagement (meetings, attendance) | EVALUATE | ⚠️ | SKIPPED | DEF 14A | DN-036 |
| 4.1.7 | Board committee structure | DISPLAY | ⚠️ | SKIPPED | DEF 14A | DN-036 |
| 4.1.8 | Successor Chair (past CEO as chair) | EVALUATE | ⚠️ | SKIPPED | DEF 14A | DN-036 |

### From old 4.2 Executive Team & Stability

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 4.2.1 | CEO/exec relevant experience | EVALUATE | 🟡 | CEO/CFO identified, tenure unavail | DEF 14A + SCAC | — |
| 4.2.2 | Executives sued at prior companies | HUNT | ✅ | 0 CLEAR | SCAC + web | — |
| 4.2.3 | Negative personal publicity | HUNT | 🟡 | Partial (web search limited) | Web search | — |
| 4.2.4 | C-suite turnover trend | EVALUATE | ✅ | turnover=0 CLEAR, stability=100 | 8-K + DEF 14A | — |
| 4.2.5 | Succession plan for key roles | EVALUATE | ✅ | interim_ceo=0 CLEAR | DEF 14A | — |
| 4.2.6 | Founder/key-person concentration risk | EVALUATE | ✅ | CLEAR | DEF 14A | — |

## NEW 4.2 Structural Governance (from old 4.3 Comp + 4.4 Rights + 1.4.3 RPT)

### From old 4.3 Compensation & Alignment

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 4.3.1 | CEO total comp vs peers | EVALUATE | 🔴 | pay_ratio=533 TRIGGERED (>500) | DEF 14A | — |
| 4.3.2 | Compensation structure | DISPLAY | 🟡 | pay_ratio=533 INFO | DEF 14A | DN-036 |
| 4.3.3 | Say-on-pay vote result | EVALUATE | ✅ | 92% CLEAR | DEF 14A | — |
| 4.3.4 | Performance metrics in incentive comp | DISPLAY | ⚠️ | SKIPPED | DEF 14A | DN-036 |
| 4.3.5 | Clawback policies | EVALUATE | ⚠️ | SKIPPED | DEF 14A | DN-036 |
| 4.3.6 | Related-party + excessive perquisites | EVALUATE | ⚠️ | SKIPPED | DEF 14A | DN-036 |
| 4.3.7 | Golden parachute / change-in-control | EVALUATE | ⚠️ | SKIPPED | DEF 14A | DN-036 |
| 4.3.8 | Stock ownership requirements | EVALUATE | ⚠️ | SKIPPED | DEF 14A | DN-036 |
| 4.3.9 | CEO pay ratio to median employee | EVALUATE | 🔴 | 533:1 TRIGGERED (same as 4.3.1) | DEF 14A | — |
| 4.3.10 | Compensation manipulation indicators | EVALUATE | ⚠️ | SKIPPED | DEF 14A | DN-036 |

### From old 4.4 Shareholder Rights & Protections

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 4.4.1 | Dual-class voting structure | EVALUATE | ✅ | 0 CLEAR (no dual-class) | DEF 14A | — |
| 4.4.2 | Anti-takeover provisions | EVALUATE | ⚠️ | SKIPPED | DEF 14A | DN-036 |
| 4.4.3 | Proxy access for nominations | EVALUATE | ⚠️ | SKIPPED | DEF 14A | DN-036 |
| 4.4.4 | Forum selection + fee-shifting | EVALUATE | ⚠️ | SKIPPED | DEF 14A | DN-036 |
| 4.4.5 | Recent bylaw amendments | EVALUATE | ⚠️ | SKIPPED | DEF 14A + 8-K | DN-036 |

### From old 1.4.3 (moved to governance)

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 1.4.3 | Related-party transactions | EVALUATE | ⚠️ | Not extracted | DEF 14A + 10-K | DN-036 |

## NEW 4.3 Transparency & Disclosure (from old 4.6 + 4.7 slimmed + 4.8)

### From old 4.6 Disclosure Quality & Filing Mechanics

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 4.6.1 | Risk factor YoY changes | EVALUATE | ✅ | 0 CLEAR/INFO | 10-K | — |
| 4.6.2 | New litigation/regulatory risk factors | EVALUATE | ✅ | 0 CLEAR | 10-K | — |
| 4.6.3 | Previously disclosed risks materialized | EVALUATE | 🟡 | INFO | 10-K | — |
| 4.6.4 | Filed on time | EVALUATE | ⚠️ | SKIPPED (timing not populated) | EDGAR | — |
| 4.6.5 | Non-GAAP reconciliation adequate | DISPLAY | 🟡 | INFO | 10-K | — |
| 4.6.6 | Segment reporting consistency | DISPLAY | 🟡 | INFO | 10-K | — |
| 4.6.7 | Related-party disclosure complete | DISPLAY | 🟡 | INFO | 10-K + DEF 14A | — |
| 4.6.8 | Guidance methodology transparent | DISPLAY | ✅ | "CONSERVATIVE" INFO | 10-K | — |
| 4.6.9 | 8-K event disclosures timely/complete | EVALUATE | 🟡 | "2/3 components" INFO | 8-K | — |

### From old 4.7 Narrative Analysis (SLIMMED 15 → 5)

| # | Slimmed Question | Layer | State | Absorbs Original | Blocker |
|---|-----------------|-------|-------|-----------------|---------|
| 4.7-S1 | Tone shift (MD&A negative tone YoY) | COMPUTE | 🟡 | 4.7.2, 4.7.3, 4.7.4 → "present" INFO | DN-035 |
| 4.7-S2 | Readability change (Fog Index delta) | COMPUTE | 🟡 | 4.7.1, 4.7.13 → "present" INFO | DN-035 |
| 4.7-S3 | Red-flag phrases (new risk factors) | EVALUATE | ✅ | 4.7.10, 4.7.11 → 0 CLEAR | — |
| 4.7-S4 | Narrative coherence (internal consistency) | INFER | 🟡 | 4.7.5, 4.7.6, 4.7.7, 4.7.8, 4.7.14 → "COHERENT" | DN-035 |
| 4.7-S5 | Management credibility score | COMPUTE | 🟡 | 4.7.9, 4.7.12, 4.7.15 → composite | DN-035 |

### From old 4.8 Whistleblower & Investigation Signals

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 4.8.1 | Whistleblower/qui tam language | EVALUATE | ✅ | 0 CLEAR | 10-K | — |
| 4.8.2 | Internal investigation language | EVALUATE | ✅ | 0 CLEAR | 10-K | — |
| 4.8.3 | Public source signals | EVALUATE | 🟡 | "Not mentioned" INFO | 8-K + web | — |

## NEW 4.4 Activist Pressure (from old 4.5 — unchanged)

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 4.5.1 | Schedule 13D filings | EVALUATE | ✅ | activist_present=False CLEAR | SEC 13D/G | — |
| 4.5.2 | Proxy contests / board demands | EVALUATE | ✅ | CLEAR | DEF 14A | — |
| 4.5.3 | Shareholder proposals (significant support) | EVALUATE | ✅ | CLEAR | DEF 14A | — |
| 4.5.4 | Short activism governance campaign | EVALUATE | ✅ | CLEAR | Web search | — |

## 4.9 Media & External (ABSORBED into Early Warning Signals)

| # | Question | Layer | State | Absorbed Into | Blocker |
|---|----------|-------|-------|---------------|---------|
| 4.9.1 | Social media sentiment | HUNT | ⚠️ | Early Warning Signals | DN-031 |
| 4.9.2 | Investigative journalism activity | HUNT | ⚠️ | Early Warning Signals | DN-031 |

---

# SECTION 5: LITIGATION & REGULATORY (7 SUBSECTIONS AFTER MERGE)

## 5.1 Securities Class Actions — Active

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 5.1.1 | Active securities class actions | EVALUATE | ✅ | active_sca_count=0 CLEAR | SCAC + 10-K | — |
| 5.1.2 | Class periods, allegations, case stage | EVALUATE | ✅ | 0 CLEAR | SCAC + 10-K | — |
| 5.1.3 | Lead counsel + tier | EVALUATE | ⚠️ | NOT_RUN (MANUAL_ONLY) | SCAC | — |
| 5.1.4 | Estimated exposure (DDL + settlement) | EVALUATE | ✅ | contingent_liab=0 CLEAR | SCAC + 10-K | — |

## 5.2 Securities Class Action History

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 5.2.1 | Prior SCA count | EVALUATE | 🔴 | total_sca_count=1 TRIGGERED yellow | SCAC | — |
| 5.2.2 | Outcomes (dismissed, settled, amount) | EVALUATE | ✅ | settled=1 INFO, amount=0 CLEAR | SCAC | — |
| 5.2.3 | Recidivist pattern (repeat filer) | EVALUATE | 🔴 | total_sca_count=1 TRIGGERED yellow | SCAC | — |
| 5.2.4 | Pre-filing signals | EVALUATE | ✅ | active=0 CLEAR | Web + SCAC | — |

## 5.3 Derivative & Merger Litigation

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 5.3.1 | Active derivative suits | EVALUATE | 🔴 | derivative_suit_count=3 TRIGGERED red | 10-K | — |
| 5.3.2 | Merger objection lawsuits | EVALUATE | ✅ | deal_litigation_count=0 CLEAR | 10-K | — |
| 5.3.3 | Section 220 demands received | EVALUATE | 🔴 | derivative_suit_count=3 TRIGGERED red | 10-K | — |
| 5.3.4 | ERISA class actions | EVALUATE | 🔴 | regulatory_count=2 TRIGGERED red (possible overcounting) | 10-K | — |
| 5.3.5 | Appraisal actions | EVALUATE | ✅ | deal_litigation_count=0 CLEAR | 10-K | — |
| 5.3.6 | Derivative suit risk factors | EVALUATE | 🔴 | derivative_suit_count=3 TRIGGERED red | 10-K | — |

## 5.4 SEC Enforcement

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 5.4.1 | SEC matter stage | EVALUATE | 🟡 | "NONE" INFO (should be CLEAR) | 10-K + SEC | Fix routing |
| 5.4.2 | SEC comment letters | EVALUATE | ⚠️ | SKIPPED (not populated) | EDGAR | — |
| 5.4.3 | Wells Notice | EVALUATE | 🟡 | False INFO | 10-K | Fix routing |
| 5.4.4 | Prior SEC enforcement actions | EVALUATE | ⚠️ | 5 checks SKIPPED (counts not populated) | SEC | — |

## 5.5 Other Regulatory & Government

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 5.5.1 | Regulating agencies | EVALUATE | ✅ | industry_reg=2 CLEAR | 10-K | — |
| 5.5.2 | DOJ investigations | EVALUATE | 🟡 | doj_investigation=2 INFO | 10-K + web | — |
| 5.5.3 | State AG investigations | EVALUATE | ⚠️ | SKIPPED (sector-conditional) | 10-K + web | — |
| 5.5.4 | Industry enforcement actions | EVALUATE | 🟡 | ftc_investigation=2 INFO | 10-K + web | — |
| 5.5.5 | Foreign government enforcement | EVALUATE | ⚠️ | SKIPPED | 10-K | — |
| 5.5.6 | Congressional investigations / subpoenas | EVALUATE | ⚠️ | SKIPPED | 10-K + web | — |

## 5.6 Non-Securities Litigation

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 5.6.1 | Aggregate active litigation count | EVALUATE | ✅ | active_matter_count=0 CLEAR | 10-K | — |
| 5.6.2 | Product liability, employment, IP, antitrust | EVALUATE | ⚠️ | 12 checks SKIPPED (no categorization) | 10-K | — |
| 5.6.3 | Whistleblower/qui tam actions | EVALUATE | 🟡 | whistleblower_count=0 INFO | 10-K | — |
| 5.6.4 | Cyber breach / environmental litigation | EVALUATE | ⚠️ | SKIPPED | 10-K | — |

## 5.7+5.8+5.9 Litigation Risk Analysis (MERGED)

### From old 5.7 Defense Posture & Reserves

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 5.7.1 | Defense provisions (forum, PSLRA) | EVALUATE | ❌ | Not wired | DEF 14A + bylaws | DN-037 |
| 5.7.2 | Contingent liabilities (ASC 450) | EVALUATE | ❌ | Not wired (data exists) | 10-K + 10-Q | DN-037 |
| 5.7.3 | Historical defense success rate | DISPLAY | ❌ | Not wired | SCAC | DN-037 |

### From old 5.8 Litigation Risk Patterns

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 5.8.1 | Statute of limitations windows | EVALUATE | ❌ | Not wired (sol_mapper exists) | 10-K + SCAC | DN-037 |
| 5.8.2 | Industry allegation theories | EVALUATE | ❌ | Not wired | SCAC | DN-037 |
| 5.8.3 | Peer contagion risk | INFER | ❌ | Not wired | SCAC | DN-037 |
| 5.8.4 | Financial event / stock drop temporal correlation | INFER | ❌ | Not wired | yfinance + SEC | DN-037 |

### From old 5.9 Sector-Specific Litigation

| # | Question | Layer | State | AAPL Value | Source | Blocker |
|---|----------|-------|-------|------------|--------|---------|
| 5.9.1 | Sector litigation patterns | EVALUATE | ❌ | Not wired | SCAC | DN-037 |
| 5.9.2 | Sector regulatory databases | EVALUATE | ❌ | No acquisition | Sector APIs | DN-037 |

---

# NARRATIVE SYNTHESIS (SYNTHESIZE Layer)

**Purpose:** LLM-generated summaries that roll up findings into underwriter-appropriate narratives. Every company's story is different — cannot be templated.

## Per-Subsection Synthesis (~35 items)

Each active subsection gets a 1-2 sentence synthesis summarizing key findings and D&O relevance.

| # | Subsection | Synthesis Question | Layer | State | Inputs |
|---|-----------|-------------------|-------|-------|--------|
| SYN-1.1 | Company Snapshot | What is the essential identity and risk profile of this company for D&O purposes? | SYNTHESIZE | ❌ | 1.1 identity + size + litigation flags |
| SYN-1.2 | Business Model & Revenue | What aspects of the business model create D&O litigation exposure? | SYNTHESIZE | ❌ | 1.2 segments + concentrations + trajectory |
| SYN-1.3 | Operational Risk | What operational dependencies could trigger securities claims? | SYNTHESIZE | ❌ | 1.3 critical/significant/monitored risks |
| SYN-1.4 | Corporate Structure | Does structural complexity create disclosure or oversight risk? | SYNTHESIZE | ❌ | 1.4 subsidiaries + VIE/SPE |
| SYN-1.6 | M&A & Transactions | Do past or pending deals create D&O exposure? | SYNTHESIZE | ❌ | 1.6 pending + history + goodwill + deal litigation |
| SYN-1.8 | Macro & Industry | What macro/industry forces elevate D&O risk for this company? | SYNTHESIZE | ❌ | 1.8 sector dynamics + macro exposures + regulatory |
| SYN-1.9 | Early Warning | Are there non-SEC signals suggesting emerging D&O risk? | SYNTHESIZE | ❌ | 1.9+1.10 employee + customer + market intelligence |
| SYN-1.11 | Risk Calendar | What upcoming catalysts could trigger securities litigation? | SYNTHESIZE | ❌ | 1.11 all calendar events |
| SYN-2.1 | Stock Performance | Does stock price behavior suggest elevated SCA risk? | SYNTHESIZE | ❌ | 2.1 range + volatility + performance |
| SYN-2.2 | Stock Drop Events | Do recent drops have characteristics of corrective disclosure events? | SYNTHESIZE | ❌ | 2.2 drops + disclosure correlation |
| SYN-2.3 | Volatility & Trading | Do trading patterns suggest informed trading or market stress? | SYNTHESIZE | ❌ | 2.3 volatility + beta + volume |
| SYN-2.4 | Short Interest | Is bearish sentiment signaling potential SCA activity? | SYNTHESIZE | ❌ | 2.4 short % + activist reports |
| SYN-2.5 | Ownership Structure | Does ownership structure create governance or litigation risk? | SYNTHESIZE | ❌ | 2.5 institutional + insider + concentration |
| SYN-2.6 | Analyst Coverage | Does analyst activity suggest earnings surprise or guidance risk? | SYNTHESIZE | ❌ | 2.6 count + consensus + target |
| SYN-2.7 | Valuation Metrics | Does the valuation create downside risk or short interest motivation? | SYNTHESIZE | ❌ | 2.7 P/E + EV/EBITDA + PEG vs peers |
| SYN-2.8 | Insider Trading | Does insider trading activity suggest information asymmetry? | SYNTHESIZE | ❌ | 2.8 net selling + CEO/CFO + cluster + timing |
| SYN-3.1 | Liquidity & Solvency | Is there going concern or liquidity risk that could trigger claims? | SYNTHESIZE | ❌ | 3.1 ratios + cash runway + going concern |
| SYN-3.2 | Leverage & Debt | Does the debt structure create financial distress exposure? | SYNTHESIZE | ❌ | 3.2 D/E + coverage + maturity + covenants |
| SYN-3.3 | Profitability & Growth | Are earnings trends creating disclosure or guidance risk? | SYNTHESIZE | ❌ | 3.3 growth + margins + cash flow quality |
| SYN-3.4 | Earnings Quality | Do forensic indicators suggest potential accounting issues? | SYNTHESIZE | ❌ | 3.4 M-Score + accruals + DSO + FIS |
| SYN-3.5 | Accounting Integrity | Does the audit environment suggest disclosure risk? | SYNTHESIZE | ❌ | 3.5 auditor + restatements + material weakness |
| SYN-3.6 | Financial Distress | Is the company approaching or in the zone of insolvency? | SYNTHESIZE | ❌ | 3.6 Z-Score + O-Score + F-Score |
| SYN-3.7 | Guidance & Expectations | Does guidance behavior create earnings surprise risk? | SYNTHESIZE | ❌ | 3.7 guidance + track record + analyst alignment |
| SYN-3.8 | Sector-Specific Financial | Do sector KPIs diverge from peer expectations? | SYNTHESIZE | ❌ | 3.8 sector metrics |
| SYN-4.1 | People Risk | Do board/exec backgrounds create D&O liability exposure? | SYNTHESIZE | ❌ | 4.1 prior lit + qualifications + turnover |
| SYN-4.2 | Structural Governance | Do governance structures create shareholder action risk? | SYNTHESIZE | ❌ | 4.2 compensation + rights + RPT |
| SYN-4.3 | Transparency & Disclosure | Does disclosure quality suggest potential misrepresentation? | SYNTHESIZE | ❌ | 4.3 risk factors + narrative + whistleblower |
| SYN-4.4 | Activist Pressure | Is there current or emerging activist/proxy risk? | SYNTHESIZE | ❌ | 4.4 13D + proxy + proposals |
| SYN-5.1 | Active SCAs | What is the current securities litigation posture? | SYNTHESIZE | ❌ | 5.1 active cases + allegations + exposure |
| SYN-5.2 | SCA History | Does litigation history suggest recidivist risk? | SYNTHESIZE | ❌ | 5.2 prior cases + outcomes + pattern |
| SYN-5.3 | Derivative & Merger | Does derivative/merger litigation indicate governance failure? | SYNTHESIZE | ❌ | 5.3 derivative + merger + ERISA |
| SYN-5.4 | SEC Enforcement | Is there SEC enforcement activity or risk? | SYNTHESIZE | ❌ | 5.4 stage + comment letters + Wells |
| SYN-5.5 | Other Regulatory | Does regulatory activity create D&O exposure? | SYNTHESIZE | ❌ | 5.5 DOJ + AG + foreign + congressional |
| SYN-5.6 | Non-Securities Litigation | Does non-SCA litigation create coverage or reputational risk? | SYNTHESIZE | ❌ | 5.6 product + employment + IP + antitrust |
| SYN-5.7 | Litigation Risk Analysis | What is the overall litigation risk trajectory? | SYNTHESIZE | ❌ | 5.7-5.9 defense + patterns + sector |

## Per-Section Synthesis (5 items)

Each section gets a full paragraph rolling up all subsection findings into a cohesive narrative.

| # | Section | Synthesis Question | Layer | State | Inputs |
|---|---------|-------------------|-------|-------|--------|
| SYN-S1 | Company | What is the overall company risk profile for D&O underwriting? | SYNTHESIZE | ❌ | All Section 1 subsection syntheses |
| SYN-S2 | Market | What do market signals indicate about securities litigation probability? | SYNTHESIZE | ❌ | All Section 2 subsection syntheses |
| SYN-S3 | Financial | What do financial indicators suggest about disclosure/fraud risk? | SYNTHESIZE | ❌ | All Section 3 subsection syntheses |
| SYN-S4 | Governance | What is the governance quality and what exposure does it create? | SYNTHESIZE | ❌ | All Section 4 subsection syntheses |
| SYN-S5 | Litigation | What is the litigation landscape and risk trajectory? | SYNTHESIZE | ❌ | All Section 5 subsection syntheses |

---

# CROSS-CUTTING STATISTICS

## By Complexity Layer

| Layer | Count | Description |
|-------|-------|-------------|
| DISPLAY | 42 | Get data, show it |
| EVALUATE | 117 | Compare against threshold |
| COMPUTE | 22 | Apply formula to inputs |
| INFER | 12 | Pattern across multiple signals |
| HUNT | 26 | Broad search + aggregate + analyze |
| SYNTHESIZE | 40 | Infer + generate narrative (35 subsection + 5 section) |
| **TOTAL** | **~259** | (219 data + 40 synthesis) |

## By Current State

| State | Count | Description |
|-------|-------|-------------|
| ✅ Working | 68 | Produces CLEAR or meaningful evaluative result |
| 🔴 TRIGGERED | 18 | Check fires and flags issue |
| 🟡 Partial | 60 | Data flows but INFO only (no threshold) |
| ⚠️ SKIPPED | 48 | Check defined, data not populated |
| ❌ Not built | 65 | No extraction/mapper/acquisition (25 data + 40 synthesis) |
| **TOTAL** | **~259** | (219 data + 40 synthesis) |

## By Blocker

| Blocker | Questions Blocked | Impact |
|---------|-------------------|--------|
| DN-036 (DEF 14A parsing) | 34 | Board, comp, shareholder rights |
| DN-031 (Web intelligence) | 14 | Employee + customer + media signals |
| DN-035 (NLP quantification) | 5 | Narrative analysis metrics |
| DN-001/002/003 (10-K segments) | 4 | Revenue/margin analysis |
| DN-037 (Litigation risk pipeline) | 9 | Defense posture, patterns, sector |
| Other DN items | ~20 | Various individual gaps |
| Wiring/routing fixes | ~15 | Data exists, just not connected |

## New Subsection Map (36 subsections)

| # | Subsection | Questions | Status |
|---|-----------|-----------|--------|
| 1.1 | Company Snapshot | 11 | Mixed ✅🟡 |
| 1.2 | Business Model & Revenue | 13 | Mostly ❌🟡 (extraction gaps) |
| 1.3 | Operational Risk & Dependencies | 11 | Mixed ✅🟡❌ |
| 1.4 | Corporate Structure & Complexity | 2 | ❌ (Exhibit 21 not parsed) |
| ~~1.5~~ | ~~Geographic Footprint~~ | — | ABSORBED → 1.2 + 1.3 |
| 1.6 | M&A & Corporate Transactions | 6 | Mostly ❌ (HUNT) |
| ~~1.7~~ | ~~Competitive Position~~ | — | ABSORBED → 1.2 + 1.8 |
| 1.8 | Macro & Industry Environment | 4 | 🟡 (mention counts) |
| 1.9+1.10 | Early Warning Signals | 12 | Mostly ⚠️ (DN-031) |
| 1.11 | Risk Calendar | 8 | ✅ (model subsection) |
| 2.1 | Stock Price Performance | 5 | ✅ |
| 2.2 | Stock Drop Events | 4 | ✅ |
| 2.3 | Volatility & Trading | 4 | 🟡 (DN-032) |
| 2.4 | Short Interest | 2 | ✅ |
| 2.5 | Ownership Structure | 4 | 🟡 |
| 2.6 | Analyst Coverage | 3 | ❌ (DN-033) |
| 2.7 | Valuation Metrics | 2 | ⚠️ (DN-034) |
| 2.8 | Insider Trading | 7 | ✅🔴 |
| 3.1 | Liquidity & Solvency | 4 | ✅🔴 (threshold fix) |
| 3.2 | Leverage & Debt | 6 | ✅ |
| 3.3 | Profitability & Growth | 6 | ✅🟡 |
| 3.4 | Earnings Quality & Forensic | 7 | ✅ |
| 3.5 | Accounting Integrity & Audit | 7 | ✅⚠️ (DN-036) |
| 3.6 | Financial Distress | 6 | ✅🟡 |
| 3.7 | Guidance & Expectations | 5 | 🟡 (wiring fix) |
| 3.8 | Sector-Specific Financial | 1 | ✅ |
| 4.1 | People Risk | 14 | ⚠️✅ (DN-036) |
| 4.2 | Structural Governance | 16 | ⚠️ (DN-036) |
| 4.3 | Transparency & Disclosure | 17 | ✅🟡 (DN-035) |
| 4.4 | Activist Pressure | 4 | ✅ |
| 5.1 | Active SCAs | 4 | ✅ |
| 5.2 | SCA History | 4 | ✅🔴 |
| 5.3 | Derivative & Merger | 6 | ✅🔴 |
| 5.4 | SEC Enforcement | 4 | 🟡⚠️ |
| 5.5 | Other Regulatory | 6 | ✅⚠️ |
| 5.6 | Non-Securities Litigation | 4 | ✅⚠️ |
| 5.7-5.9 | Litigation Risk Analysis | 9 | ❌ (DN-037) |
