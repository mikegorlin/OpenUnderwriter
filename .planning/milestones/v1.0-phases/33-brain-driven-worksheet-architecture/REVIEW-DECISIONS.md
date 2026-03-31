# Question Review Decisions

**Started:** 2026-02-20
**Format:** Visual mockup + data sourcing trace per subsection
**Status:** Section 1.1 REVIEWED, continuing through remaining subsections

---

## Overall Strategy Decisions

### Review Pattern (Established Session 1)
For each subsection:
1. Show current state from QUESTION-SPEC
2. Propose restructured visual mockup (with emojis/formatting)
3. Data sourcing trace (layer type, source, acquisition, extraction, working?)
4. Fallback chains for every data point (at least one fallback per item)
5. What simplifies / gets absorbed from other subsections
6. Extraction gaps identified

### Architecture & Refactoring Strategy
- **Decision:** Finish full 45-subsection review FIRST, then one clean refactor pass
- **Rationale:** Current architecture is flexible enough to absorb changes:
  - checks.json v6_subsection_ids are just strings — easy to remap in bulk
  - Renderers are modular (one file per section) — easy to restructure
  - enrichment_data.py mappings can be updated once, not incrementally
  - State model holds all data regardless of display organization
  - Pipeline stages don't care about question organization
- **Exception:** If a fundamental architectural blocker is discovered during review, address immediately
- **Post-review refactor:** Update checks.json mappings, enrichment_data.py, renderers, and extraction modules in one pass

### Fallback Chain Strategy
- **Current state:** CLAUDE.md has high-level fallback chains by DATA SOURCE (SEC, stock, litigation)
- **Gap:** No per-FIELD fallback chains exist — granularity needed per data point
- **Decision:** Capture per-field fallbacks in this doc during review. After full review, consolidate into `config/fallback_chains.json` that acquisition stage can consume as config-driven fallback system
- **Principle:** Every data point must have at least one fallback source

### 5-Layer Framework (Per Data Point)
Every data point in every subsection is traced through all 5 layers:
1. **Source** — Where does the raw data live? (SEC 10-K, yfinance, SCAC, web search, etc.)
2. **Acquisition** — Which acquisition module fetches it? (sec_client, market_client, litigation_client, web_search)
3. **Extraction** — Which extraction module parses/structures it? (company_profile, ten_k_converters, LLM extractors, sca_extractor)
4. **Analysis** — What check/evaluation happens? (EVALUATIVE_CHECK with threshold, MANAGEMENT_DISPLAY, INFERENCE_PATTERN, or none)
5. **Rendering** — How does it appear in the output? (which section, what format, visual treatment)

### Data Complexity Types (Reference)
1. **DISPLAY** — Get data, show it. No evaluation.
2. **EVALUATE** — Compare against threshold. CLEAR or TRIGGERED.
3. **COMPUTE** — Get inputs, apply formula. Deterministic.
4. **INFER** — Pattern recognition across multiple data points. The combination matters.
5. **HUNT** — Broad search, aggregation, deduplication, then analysis.
6. **SYNTHESIZE** — Infer + generate narrative. LLM-dependent. Takes all findings from a subsection/section and writes underwriter-appropriate summary. Every company's story is different — cannot be templated.

### Narrative Synthesis Strategy
- **Per-subsection:** 1-2 sentence synthesis summarizing key findings and D&O relevance (~36 items)
- **Per-section:** Full summary paragraph rolling up all subsection findings (~5 items)
- **Total:** ~41 synthesis items
- **Implementation:** LLM generation at RENDER stage, consuming check results + extracted data
- **Existing code:** `md_narrative_sections.py` has template-driven narratives — needs upgrade to true LLM synthesis

### Tracking Documents
- **REVIEW-DECISIONS.md** (this file) — Design decisions, user direction, structure, fallbacks per subsection
- **DATA-NEEDS.md** — Engineering backlog: all extraction gaps, enhancements, config needs (DN-001+)
- **STATE.md** — GSD state updated after each subsection review
- **QUESTION-SPEC.md** — Original reference (read-only during review, updated after full review)

---

## 1.1 Company Snapshot (REVIEWED)

**Restructured from:** 5 separate questions → 4 display blocks

### User Direction
- 1.1 is "who is this company" — a company card, not analysis
- Snapshot helps underwriter triangulate the TYPE of business and SIZE of business
- No stock valuation, ownership, financial ratios — those belong in analytical sections
- Geographic revenue concentration belongs in its own section (operations/business model analysis)
- Competition/peers belongs in its own section
- D&O litigation flags ARE useful in snapshot — quick red flag check before diving into detail
- Market cap should show relative size (ranking among US public companies), not just the number
- Geographic data should be actual revenue concentration percentages from 10-K, not just country names
- Must include GICS code (not just SIC) — GICS is standard in financial/insurance industry

### Final Structure
1. **🪪 Identity** — Company name, ticker, sector, SIC/GICS, HQ, state of incorporation, exchange, FPI
2. **📊 Size & Stage** — Market cap (with relative ranking), revenue TTM, employees, years public, lifecycle
3. **💼 Description of Operations** — 2-3 sentence summary of business model from 10-K Item 1
4. **⚖️ D&O Litigation History** — Active SCA count, prior SCA count, derivative suit count (flags only with traffic light indicators, detail in Section 5)

### Layer Classification
- 16 Extract & Display, 3 Extract & Compute
- Simplest section in the system — rendering problem, not acquisition problem

### Questions Absorbed From Other Subsections
- Old 1.1.2 (key metrics), 1.1.3 (lifecycle), 1.1.5 (exchange/FPI) → collapsed into Identity and Size blocks
- 1.2.1 business model description (display portion) → absorbed into Operations block
- 5.1/5.2/5.3 summary litigation counts → surfaced as D&O flags

### Extraction Gaps
1. **GICS code** — yfinance has it (`info['industryKey']` etc.) but numeric GICS code not extracted to state model
2. **Market cap ranking** — peer caps acquired but relative position not computed
3. **Business description summarization** — 10-K Item 1 is raw text, may need LLM summarization for clean 2-3 sentence version

### Fallback Chains (Per Field)

| Data Point | Primary | Fallback 1 | Fallback 2 |
|-----------|---------|-----------|-----------|
| Company name | SEC EDGAR | yfinance | — |
| Sector | SEC EDGAR (SIC) | yfinance sector/industry | — |
| SIC | SEC EDGAR | yfinance `info['sic']` | — |
| GICS | yfinance | SIC → GICS mapping table (config) | — |
| HQ | yfinance | 10-K cover page | — |
| State of inc. | SEC EDGAR | 10-K cover page | DEF 14A |
| Exchange | yfinance | SEC EDGAR | — |
| FPI | SEC EDGAR | 10-K cover page | — |
| Market cap | yfinance | Price × shares outstanding (XBRL) | — |
| Revenue TTM | XBRL | yfinance `totalRevenue` | 10-K LLM extraction |
| Employees | 10-K LLM | yfinance `fullTimeEmployees` | Web search + cross-validate |
| Years public | yfinance IPO date | SEC earliest filing date | — |
| Lifecycle | Computed (years + growth) | Market cap tier default | — |
| Description | 10-K Item 1 | yfinance `longBusinessSummary` | Web search |
| Active SCAs | SCAC database | 10-K Item 3 | Web search |
| Prior SCAs | SCAC database | 10-K Item 3 | Web search |
| Derivative suits | 10-K Item 3 LLM | CourtListener | Web search |

### Implementation Notes
- SIC → GICS mapping table needed as new config file
- Market cap ranking: compute from peer_group module data (already acquired)
- Employee count has known accuracy issues — Phase 23 added cross-validation logic (1% ratio threshold, 1000x multiplier heuristic)
- No new acquisition modules needed for 1.1 — all data sources already connected

### Design Decisions
- No risk analysis in 1.1 — pure display/factual
- Geographic revenue concentration is business operations analysis, not snapshot — goes in separate section
- Competition/peers is competitive analysis, not snapshot — goes in separate section
- Litigation flags are summary counts only, not evaluative — Section 5 has full detail
- Formatting uses emojis and traffic light indicators (🟢🟡🔴) for visual scanning

---

## 1.2 Business Model & Revenue (REVIEWED)

**Restructured from:** 6 questions (all DISPLAY ONLY) → 7 display blocks with analytical depth

### User Direction
- This is "how the sausage is made" — deep dive into how the company actually makes money
- Revenue breakdown AND earnings breakdown — they tell different stories (Services is 25% of revenue but 42% of gross profit)
- Geographic revenue with actual percentages, not just country names
- Capital allocation matters — buybacks, dividends, R&D investment show management priorities
- Key concentrations with D&O relevance — what parts of the business model create litigation exposure
- Business model trajectory — where is the model heading and what are the transition risks
- This is significantly more depth than the original 1.2 which was all mention counts
- Cost structure and operating leverage moved to Section 3 (financial analysis)
- Innovation/Investment Gap moved to forward-looking risk analysis

### Final Structure
1. **🏗️ How Does This Company Make Money?** — Business model narrative (ecosystem, flywheel, revenue model evolution, pricing power, supply chain)
2. **📊 Revenue by Product/Service** — Segment table with $, %, trend, D&O signals
3. **🌍 Revenue by Geography** — Region table with $, %, risk context
4. **💰 Where Do the Earnings Come From?** — Segment margin analysis showing revenue ≠ profit
5. **💸 Capital Allocation** — Buybacks, dividends, R&D, net cash position
6. **⚠️ Key Concentrations** — Product, geographic, regulatory, customer concentration with traffic lights
7. **🔮 Business Model Trajectory** — Key shifts and their D&O implications

### Layer Classification
- Primarily Extract & Display with some Extract & Compute (margins, concentration %)
- One Extract & Infer item (business model trajectory — YoY comparison)
- Major extraction gap: most data currently returns mention counts, not structured financials

### Questions Absorbed From Other Subsections
- 1.5.1 "Where does the company operate?" → Geographic revenue table in 1.2
- 3.3.5 "Segment-level divergences hiding overall trends?" → Earnings analysis in 1.2
- 1.2.1 display portion already absorbed into 1.1 snapshot

### Questions Moved Out
- 1.2.4 "Cost structure and operating leverage" → Section 3 (Financial Analysis)
- 1.2.6 "Innovation/Investment Gap" → Forward-looking risk analysis section

### Extraction Gaps (See DATA-NEEDS.md for full details)
- DN-001: Revenue by product segment ($ and %) — needs LLM extraction from 10-K Item 7
- DN-002: Revenue by geography ($ and %) — needs LLM extraction from 10-K Item 7
- DN-003: Gross margin by segment — needs LLM extraction from 10-K
- DN-004: Share buyback program — needs LLM extraction from 10-K
- DN-007: Business model trajectory — needs YoY 10-K comparison
- DN-008: Revenue type classification — upgrade from mention count to LLM classification
- DN-009: R&D/CapEx — exists in XBRL, needs surfacing
- DN-011: Dividends — exists in yfinance, needs surfacing
- DN-012: Net cash position — exists, needs computation and display
- DN-013: Customer concentration — needs "absence = positive" interpretation

### Fallback Chains (Per Field)

| Data Point | Primary | Fallback 1 | Fallback 2 |
|-----------|---------|-----------|-----------|
| Business narrative | 10-K Item 1 LLM summary | yfinance `longBusinessSummary` | Web search |
| Revenue segments | 10-K Item 7 LLM extraction | XBRL segment tags | yfinance (limited) |
| Revenue geography | 10-K Item 7 LLM extraction | XBRL geographic tags | — |
| Segment margins | 10-K Item 7 LLM | Compute from XBRL segment data | — |
| R&D spend | XBRL concept | 10-K income statement LLM | — |
| CapEx | XBRL concept | 10-K cash flow LLM | — |
| Buybacks | 10-K / 10-Q LLM | Shares outstanding delta (yfinance) | — |
| Dividends | yfinance `dividendRate` | 10-K / 10-Q LLM | — |
| Net cash | XBRL (cash - debt) | 10-K balance sheet LLM | — |
| Product concentration % | Computed from segment data | — | — |
| Customer concentration | 10-K disclosure | "No >10% customer" = diversified | — |
| Model trajectory | 10-K YoY diff (LLM) | Revenue mix trend (computed) | — |

### Design Decisions
- 1.2 is analytical depth, not just display — shows HOW money is made and WHERE earnings come from
- Revenue ≠ Earnings is a key insight to surface (Services margin 2x Products for AAPL)
- Capital allocation signals management priorities — buybacks support EPS, R&D shows investment
- Concentrations are flagged with D&O relevance — what could cause stock drops/litigation
- Business model trajectory shows where the company is heading and transition risks
- All data currently sourced from my general knowledge — pipeline needs significant extraction work (see DATA-NEEDS.md)

### 5-Layer Trace (All Data Points)

| # | Data Point | Source | Acquisition | Extraction (Current) | Extraction (Target) | Analysis | Rendering | Gap |
|---|-----------|--------|-------------|---------------------|---------------------|----------|-----------|-----|
| 1 | Business model narrative | 10-K Item 1 | sec_client | ten_k_converters (raw text) | LLM summarization: 2-3 sentence summary for 1.1, expanded for 1.2 | MANAGEMENT_DISPLAY | Narrative block | DN-006 |
| 2 | Revenue by product segment | 10-K Item 7 | sec_client | BIZ.MODEL.revenue_segment returns mention count only | LLM extraction: table with segment name, $, %, trend | MANAGEMENT_DISPLAY | Not rendered as table | DN-001 |
| 3 | Revenue by geography | 10-K Item 7 | sec_client | BIZ.MODEL.revenue_geo returns country names, no % | LLM extraction: table with region, $, % | MANAGEMENT_DISPLAY | Not rendered with % | DN-002 |
| 4 | Gross margin by segment | 10-K Item 7 | sec_client | NOT EXTRACTED | LLM extraction: segment margins (e.g. Products ~37% vs Services ~73%), compute % of gross profit | N/A | N/A | DN-003 |
| 5 | Revenue type (recurring/one-time) | 10-K Item 1 | sec_client | BIZ.MODEL.revenue_type returns mention count | LLM classification: recurring %, one-time %, classification | MANAGEMENT_DISPLAY | Mention count | DN-008 |
| 6 | R&D spend | XBRL | sec_client | Likely in financial_statements but not surfaced | Surface existing data: R&D $, % of revenue | None for 1.2 | Not displayed in 1.2 | DN-009 |
| 7 | CapEx spend | XBRL | sec_client | Likely in financial_statements but not surfaced | Surface existing data: CapEx $, % of revenue | None | Not displayed | DN-009 |
| 8 | Share buybacks | 10-K/10-Q | sec_client | NOT EXTRACTED | LLM extraction: annual buyback $, cumulative program | N/A | N/A | DN-004 |
| 9 | Dividends | yfinance | market_client | Available as dividendRate/dividendYield | Surface existing data: annual dividend $, yield % | None | Not surfaced in 1.2 | DN-011 |
| 10 | Net cash position | XBRL | sec_client | Cash and debt both extracted | Compute and surface: net cash = total cash - total debt | debt_to_ebitda computed | Not displayed as net cash | DN-012 |
| 11 | Product concentration % | Derived from segment data | N/A (computed) | N/A (computed from DN-001) | Compute max segment %, flag >50% single product as red | Could be EVALUATIVE_CHECK (>50% = red) | Concentration table | Needs DN-001 first |
| 12 | Customer concentration | 10-K | sec_client | BIZ.DEPEND.customer_conc returns "Not mentioned" | Interpret absence as positive: "No customer >10%" = green | EVALUATIVE_CHECK but can't evaluate | Shows INFO | DN-013 |
| 13 | Business model trajectory | 10-K YoY | sec_client | NOT EXTRACTED | YoY comparison: key shifts, from→to format with D&O implications | N/A | N/A | DN-007 |

---

## 1.3 Operational Risk & Dependencies (REVIEWED)

**Restructured from:** 9 questions → 3 risk-severity blocks (Critical / Significant / Monitored)

### User Direction
- Frame as "what could trip this company up" — risk scenarios, not categories
- Organize by severity, not by dependency type
- Customer concentration absorbed into 1.2 (already there)
- Each risk should show: dependency, what could go wrong, severity, D&O exposure

### Final Structure
1. **🔴 Critical Dependencies** — Single points of failure (TSMC, Foxconn, China manufacturing)
2. **🟡 Significant Operational Risks** — App Store antitrust, data breach, China tariffs, AI liability, labor
3. **🟢 Monitored but Contained** — Key person, right to repair, ESG, ARM license, component supply

### Complexity Classification
| Question | Layer | Current State |
|----------|-------|--------------|
| Key supplier names + single-source | HUNT | ❌ Mention count only |
| Manufacturing geography | COMPUTE | 🟡 Country names, no classification |
| Regulatory action status | HUNT | ❌ Mention count only |
| Data/privacy risk profile | EVALUATE | 🟡 Mention count only |
| AI/ML exposure | DISPLAY | ✅ Working |
| Labor risk signals | HUNT | ❌ False trigger (reads employee_count) |
| Key person risk | EVALUATE | 🟡 "Not mentioned" |
| ESG/greenwashing | HUNT | ❌ Shared with regulatory_dep |
| Government contract exposure | EVALUATE | ✅ Working |
| Supply chain macro sensitivity | DISPLAY | ✅ Working |
| Trade policy exposure | EVALUATE | ✅ Working (mention count) |

### Questions Absorbed
- 1.3.1 Customer concentration → already in 1.2 concentrations table

### Data Needs: DN-017 through DN-024 (8 items, see DATA-NEEDS.md)
- 4 🔴 New extraction: DN-017 (suppliers), DN-019 (single-source), DN-020 (regulatory actions), DN-022 (labor)
- 4 🟡 Enhancement: DN-018 (geo classification), DN-021 (privacy mapping), DN-023 (key person), DN-024 (ESG)

---

## 1.4 Corporate Structure & Complexity (REVIEWED)

**Restructured from:** 3 questions → 2 questions (related-party moved out)

### User Direction
- Corporate structure stays as its own subsection
- Related-party transactions → moves to governance section (Section 2)
- Focus: structural complexity that creates D&O exposure (subsidiary sprawl, VIE risk, off-balance-sheet)

### Final Structure
1. **🏢 Subsidiary & Entity Complexity** — Count, key jurisdictions, holding structure type (simple/complex/layered)
2. **⚠️ Off-Balance-Sheet Structures** — VIEs, SPEs, special structures with risk flags

### AAPL Mockup
```
🏢 Corporate Structure & Complexity
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Subsidiaries:      200+  (Exhibit 21)
Key Jurisdictions: Ireland, China, Japan, Singapore, India, UK + 25 others
VIEs/SPEs:         🟢 None disclosed
Off-Balance-Sheet: 🟢 None significant
Holding Structure: Simple (Apple Inc. → wholly-owned subsidiaries)
```

### Complexity Classification
| Question | Layer | Current State |
|----------|-------|--------------|
| Subsidiary count + jurisdictions | DISPLAY | ❌ Not extracted (Exhibit 21 not parsed) |
| VIE/SPE presence | EVALUATE | ❌ Not extracted (10-K notes not parsed) |

### Questions Moved Out
- 1.4.3 Related-party transactions → Section 2 (Governance)

### Data Needs: DN-025, DN-026
- DN-025: 🔴 Exhibit 21 subsidiary parsing (structured list: entity name, jurisdiction, ownership %)
- DN-026: 🔴 VIE/SPE detection from 10-K notes (LLM extraction: presence flag, entity names, risk assessment)

### Fallback Chains
| Data Point | Primary | Fallback 1 | Fallback 2 |
|-----------|---------|-----------|-----------|
| Subsidiary count | 10-K Exhibit 21 | 10-K Item 1 LLM | Web search |
| Jurisdictions | 10-K Exhibit 21 | DEF 14A | — |
| VIEs/SPEs | 10-K notes LLM | 10-Q notes LLM | — |
| Off-balance-sheet | 10-K notes LLM | 10-Q LLM | — |
| Holding structure | Computed from Exhibit 21 | 10-K Item 1 LLM | — |

---

## 1.5 Geographic Footprint (ABSORBED)

**Decision:** Fully absorbed into 1.2 and 1.3. No standalone subsection.
- 1.5.1 "Where does the company operate?" → 1.2 Revenue by Geography table (already has region, $, %, risk context)
- 1.5.2 "Jurisdiction-specific risks (FCPA, GDPR, sanctions)?" → 1.3 Operational Risks (already covers geopolitical, regulatory, trade policy)
- No new data needs — geographic data already tracked in DN-002 (revenue geography) and DN-018/DN-020/DN-021 (jurisdiction risks)

---

## 1.6 M&A & Corporate Transactions (REVIEWED)

**Kept as-is:** 6 questions, all retained

### Final Structure
1. **🤝 Pending M&A** — Active deals, shareholder votes, regulatory approvals pending
2. **📜 Acquisition History** — 2-3 year deal list: target, size, rationale, integration status
3. **💎 Goodwill & Impairment Risk** — Goodwill-to-assets ratio, impairment history, write-down risk
4. **🔄 Divestitures & Spin-offs** — Capital markets transactions, spin-off litigation risk
5. **⚖️ Deal Litigation** — Merger objection suits, appraisal rights, shareholder challenges
6. **📊 Integration Track Record** — Pattern (acqui-hire vs transformative), success rate, D&O exposure

### AAPL Mockup
```
🤝 M&A & Corporate Transactions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pending M&A:         🟢 None
Recent Acquisitions: ~20 in past 3 years (mostly small tuck-ins, AI/ML focus)
Largest Deal:        Beats Electronics ~$3B (2014)
Goodwill:            ~$0 (expenses acquisitions — rare among mega-caps)
Divestitures:        🟢 None significant
Deal Litigation:     🟢 None
Integration Risk:    🟢 Low (small deals absorbed into existing products)
D&O Exposure:        🟢 Low — no large transformative deals = low merger objection risk
```

### Complexity Classification
| Question | Layer | Current State |
|----------|-------|--------------|
| Pending M&A | EVALUATE | 🟡 FWRD.EVENT.ma_closing = 0, INFO only |
| Acquisition history | HUNT | ❌ Not extracted (needs 10-K + 8-K + web) |
| Goodwill/impairment | COMPUTE | 🟡 debt_to_ebitda exists but no goodwill-to-assets |
| Divestitures | HUNT | ❌ Not extracted |
| Deal litigation | HUNT | ❌ Not extracted (needs SCAC + 10-K Item 3) |
| Integration track record | INFER | ❌ Not extracted (pattern across multiple deals) |

### Data Needs: DN-027 through DN-030
- DN-027: 🔴 Acquisition history extraction (10-K notes + 8-K + web search)
- DN-028: 🟡 Goodwill-to-assets ratio computation (XBRL data exists, ratio not computed)
- DN-029: 🔴 Deal litigation extraction (SCAC merger objection filter + 10-K Item 3)
- DN-030: 🔴 Divestiture/spin-off extraction (8-K + 10-K)

### Fallback Chains
| Data Point | Primary | Fallback 1 | Fallback 2 |
|-----------|---------|-----------|-----------|
| Pending M&A | 8-K filings | 10-K Item 7 | Web search |
| Acquisition history | 10-K notes LLM | 8-K filings | Web search |
| Goodwill | XBRL | 10-K balance sheet LLM | — |
| Divestitures | 8-K filings | 10-K Item 7 LLM | Web search |
| Deal litigation | SCAC (merger objection) | 10-K Item 3 | Web search |
| Integration | 10-K Item 7 YoY LLM | Web search | — |

---

## 1.7 Competitive Position & Industry Dynamics (ABSORBED)

**Decision:** Fully absorbed into 1.2 and 1.8. No standalone subsection.
- Competitive moat, market position, barriers to entry → 1.2 Business Model (strengthens "how the sausage is made" narrative)
- Peer SCA rate → already surfaced via BIZ.COMP.peer_litigation check
- Industry headwinds/tailwinds, consolidation, disruptive tech → 1.8 Macro & Industry Environment
- No new data needs — existing checks cross-map naturally

---

## 1.8 Macro & Industry Environment (REVIEWED)

**Restructured from:** 4 questions + absorbed 1.7 industry dynamics → 3 display blocks

### Final Structure
1. **📈 Sector & Industry Dynamics** — Sector performance, industry growth/consolidation, disruptive threats, peer comparison (absorbed from 1.7)
2. **🌍 Macro Exposures** — Trade/tariffs, geopolitical, FX, rates, inflation, commodities with traffic lights
3. **📋 Regulatory & Legislative Landscape** — Antitrust, sector-specific regulation, legislative pipeline

### Complexity Classification
| Question | Layer | Current State |
|----------|-------|--------------|
| Sector performance | DISPLAY | ✅ sector_return = 5.03 |
| Industry dynamics | DISPLAY | 🟡 Mention counts only (consolidation=5, disruptive_tech=4) |
| Peer comparison | DISPLAY | 🟡 peer_count=3 but no structured comparison |
| Trade/tariffs | EVALUATE | 🟡 10 mentions, no threshold evaluation |
| Geopolitical | EVALUATE | 🟡 13 mentions, no threshold evaluation |
| FX exposure | DISPLAY | 🟡 3 mentions |
| Interest rates | DISPLAY | 🟡 "Not mentioned" |
| Inflation | DISPLAY | 🟡 3 mentions |
| Regulatory changes | DISPLAY | 🟡 1 mention |

### Data Needs
- No new DN items — existing checks cover the data, but mention counts need threshold interpretation
- Enhancement: Add evaluative thresholds to FWRD.MACRO checks (e.g., geopolitical >10 = elevated)
- Enhancement: Structured peer comparison table (from 1.7 absorption) needs peer_group data surfacing

### Fallback Chains
| Data Point | Primary | Fallback 1 | Fallback 2 |
|-----------|---------|-----------|-----------|
| Sector performance | yfinance sector ETF | Market data API | Web search |
| Industry dynamics | 10-K Item 1/1A LLM | Web search for industry reports | — |
| Trade/tariffs | 10-K Item 1A | Web search | — |
| Geopolitical | 10-K Item 1A | Web search for geopolitical risk | — |
| FX exposure | 10-K Item 7A | XBRL foreign currency data | — |
| Regulatory | 10-K Item 1A | Web search for regulatory actions | — |
| Peer comparison | yfinance peer data | SCAC peer SCA counts | Web search |

---

## 1.9 + 1.10 Early Warning Signals (MERGED)

**Restructured from:** 1.9 Employee & Workforce (6 questions) + 1.10 Customer & Product (6 questions) → 1 combined section

### Rationale
Both subsections are HUNT-type web intelligence with the same data acquisition gap (web scraping not built). Merging creates a single "external intelligence" section that shows all non-SEC signals in one place.

### Final Structure
1. **👥 Employee Signals** — Glassdoor rating + CEO approval, LinkedIn departures, Indeed/Blind sentiment, WARN Act, hiring patterns
2. **🛒 Customer & Product Signals** — CFPB complaints, app ratings, Trustpilot, product quality (FDA/NHTSA where applicable), churn signals
3. **📡 Market Intelligence** — Web traffic trends, social sentiment, journalism activity, academic monitoring (biotech)

### AAPL Mockup
```
🔔 Early Warning Signals
━━━━━━━━━━━━━━━━━━━━━━━━
👥 EMPLOYEE
  Glassdoor:         ⚠️ Not acquired | CEO Approval: ⚠️ Not acquired
  LinkedIn:          ⚠️ Not acquired (departures, headcount trend)
  WARN Act:          ⚠️ Not acquired
  Hiring Patterns:   Legal hiring 10 mentions (10-K) | Compliance 1 mention

🛒 CUSTOMER & PRODUCT
  CFPB Complaints:   ⚠️ Not acquired (N/A for AAPL — not financial services)
  App Ratings:       ⚠️ Not acquired
  Trustpilot:        ⚠️ Not acquired
  FDA/NHTSA:         N/A (sector-conditional)
  Churn Signals:     "Not mentioned" (10-K)

📡 MARKET INTELLIGENCE
  Web Traffic:       ⚠️ Not acquired
  Social Sentiment:  ⚠️ Not acquired
  Journalism:        ⚠️ Not acquired
```

### Complexity Classification
All HUNT — requires web scraping infrastructure:
- Glassdoor API/scrape, LinkedIn profile analysis, Indeed/Blind scraping
- CFPB API, App Store ratings API, Trustpilot scrape
- SimilarWeb/web traffic, social media APIs
- Only 3 of 19 checks currently produce data (from 10-K text search)

### Data Needs: DN-031 (consolidated)
- DN-031: 🔴 Web intelligence acquisition infrastructure — Glassdoor, LinkedIn, CFPB, app stores, social media, web traffic
- This is a platform capability, not individual field extraction
- Sector-conditional checks (FDA, NHTSA, CFPB) should auto-skip for non-applicable sectors

### Design Decisions
- Merged because both share the same infrastructure gap (web scraping)
- Sector-conditional checks preserved (FDA/NHTSA for pharma/auto, CFPB for financial services)
- 10-K text search results retained as weak signals until web data available
- This section will show mostly "Not acquired" until web scraping infrastructure is built

---

## 1.11 Risk Calendar & Upcoming Catalysts (REVIEWED — KEPT AS-IS)

**No changes.** Best-covered subsection: 8 questions, 17 checks, all ANSWERED.

### Final Structure (unchanged)
1. **⏰ Near-Term Events** — Next earnings, guidance risk, shareholder meeting, proxy deadline
2. **📋 Pending Events** — Regulatory decisions, M&A closings, debt maturities, lockup/warrants
3. **⚖️ Litigation Milestones** — Trial dates, settlement deadlines
4. **🏭 Sector-Specific Catalysts** — Contract renewals, industry triggers (PDUFA, patent cliffs)

### Notes
- All 17 checks fire and produce meaningful results
- Sector-conditional checks (lockup/warrants) correctly skip for mature companies
- No new data needs — this is the model for how other subsections should work
- No extraction gaps identified

---

# SECTION 2: MARKET (REVIEWED — ALL 8 SUBSECTIONS KEPT AS-IS)

**Decision:** Keep all 8 subsections. Section 2 is the healthiest section — 5/8 GREEN, 3 YELLOW with minor extraction gaps.

## 2.1 Stock Price Performance (GREEN — NO CHANGES)
- 5 questions, 8 checks, all evaluative and working
- No data needs

## 2.2 Stock Drop Events (GREEN — NO CHANGES)
- 4 questions, 4 checks including INFERENCE_PATTERN for corrective disclosure correlation
- No data needs

## 2.3 Volatility & Trading Patterns (YELLOW — MINOR FIXES)
- 4 questions, 6 checks. Trade liquidity routes to current_price instead of avg daily volume. Beta not extracted.
- DN-032: 🟡 Beta and average daily volume extraction from yfinance (fields exist, not wired)

## 2.4 Short Interest & Bearish Signals (GREEN — NO CHANGES)
- 2 questions, 4 checks. Short interest % and days-to-cover both evaluate.
- No data needs

## 2.5 Ownership Structure (GREEN — NO CHANGES)
- 4 questions, 4 checks. Institutional/insider split, activist presence.
- Known minor gap: top holders pct_out enrichment

## 2.6 Analyst Coverage & Sentiment (YELLOW — ROUTING FIX)
- 3 questions, 2 checks. Both route to beat_rate instead of analyst count/consensus.
- DN-033: 🟡 Analyst count, consensus rating, price target extraction from yfinance (data exists, not surfaced)

## 2.7 Valuation Metrics (YELLOW — EXTRACTION FIX)
- 2 questions, 4 checks. P/E, EV/EBITDA, PEG fields not populated despite yfinance availability.
- DN-034: 🟡 Valuation ratio extraction (pe_ratio, ev_ebitda, peg_ratio) — yfinance data acquired but not stored in correct fields

## 2.8 Insider Trading Activity (GREEN — NO CHANGES)
- 7 questions, 16 checks. 4 TRIGGERED for AAPL (CEO/CFO 100% sellers, cluster timing). Strong coverage.
- Some GOV.INSIDER checks SKIPPED (cluster_count, unusual_timing not populated)
- No new data needs — existing extraction partially working

---

# SECTION 3: FINANCIAL (REVIEWED — ALL 8 SUBSECTIONS KEPT AS-IS)

**Decision:** Keep all 8 subsections. 7/8 GREEN, 1 YELLOW. Minor fixes needed, no restructuring.

### Fixes Needed (no new data needs — wiring/calibration issues)
- **3.1:** FIN.LIQ.position threshold <6.0 is wildly miscalibrated — sector-adjust or fix
- **3.3:** FIN.TEMPORAL checks return metric names as values instead of computed trends
- **3.5:** GOV.EFFECT governance overlay checks (10 of 18) SKIPPED due to DEF 14A gap (shared with Section 4)
- **3.6:** Ohlson O-Score and Piotroski F-Score not individually computed — all map to zone_of_insolvency
- **3.7:** All 5 guidance checks return INFO; earnings guidance extraction exists but not connected to field routing

### Absorbed From Other Sections
- Cost structure / operating leverage (from original 1.2) → stays in Section 3

## 3.1 Liquidity & Solvency (GREEN — THRESHOLDS NEED SECTOR CALIBRATION)

- **Questions:** 4 | **Checks:** 5 (all EVALUATIVE_CHECK)
- **Key data fields:** current_ratio (XBRL), cash_ratio (XBRL), cash_burn_months (computed from OCF), working_capital (XBRL)
- **Source:** SEC 10-Q, XBRL via sec_client -> financial_statements, xbrl_mapping
- **Presentation:** Data table with traffic light indicators per metric
- **Status:** GREEN. All checks fire. FIN.LIQ.position red threshold of <6.0 is miscalibrated for non-bank sectors (AAPL triggers red at 0.89 current ratio). Cash burn correctly returns "Profitable" for OCF-positive companies.
- **Fix needed:** Sector-calibrate FIN.LIQ.position threshold (current <6.0 red is bank-appropriate, not tech)

## 3.2 Leverage & Debt Structure (GREEN — NO CHANGES)

- **Questions:** 6 | **Checks:** 5 (4 EVALUATIVE_CHECK, 1 FALLBACK_ONLY)
- **Key data fields:** debt_to_ebitda (computed), interest_coverage (computed), refinancing_risk (text from debt_analysis), debt_structure (dict), credit_rating (not acquired)
- **Source:** SEC 10-Q/10-K, XBRL via sec_client -> financial_statements, debt_analysis, debt_text_parsing
- **Presentation:** Data table for numeric metrics; narrative for qualitative debt maturity/covenant data
- **Status:** GREEN. Core leverage metrics (D/EBITDA=0.63 CLEAR, coverage=33.8x CLEAR) well-covered. Maturity and covenant checks return qualitative INFO. Credit rating FALLBACK_ONLY.

## 3.3 Profitability & Growth (GREEN — TEMPORAL PIPELINE INCOMPLETE)

- **Questions:** 6 | **Checks:** 10 (5 EVALUATIVE_CHECK, 5 FIN.TEMPORAL)
- **Key data fields:** financial_health_narrative (text), accruals_ratio (computed), ocf_to_ni (computed), revenue growth % (computed), margin % (computed)
- **Source:** SEC 10-Q, XBRL via sec_client -> financial_statements
- **Presentation:** Data table for numeric metrics; narrative for growth trajectory
- **Status:** GREEN. Accruals ratio and OCF/NI evaluate numerically. FIN.TEMPORAL checks return metric names as values instead of computed trends (temporal computation pipeline incomplete). Revenue growth rate extraction works (6.4% for AAPL).
- **Fix needed:** FIN.TEMPORAL mapper should use extract_temporal_metrics for computed values (Phase 33-05 partially fixed)

## 3.4 Earnings Quality & Forensic Analysis (GREEN — NO CHANGES)

- **Questions:** 7 | **Checks:** 17 (all EVALUATIVE_CHECK)
- **Key data fields:** beneish_m_score (computed), accruals_ratio (computed), dso_ar_divergence (computed), ocf_to_ni (computed), revenue_quality_score (computed), deferred_revenue_trend (quarterly), q4_concentration (quarterly)
- **Source:** SEC 10-K/10-Q, XBRL via sec_client -> financial_statements, audit_risk
- **Presentation:** Risk indicator with forensic scores; data table for quality metrics
- **Status:** GREEN. Strong forensic suite. Beneish M-Score computed (-2.29 CLEAR). DSO/AR divergence triggers yellow (11.86). Deferred revenue trend and Q4 concentration SKIPPED (quarterly fields not populated).

## 3.5 Accounting Integrity & Audit Risk (GREEN — GOVERNANCE OVERLAY BLOCKED)

- **Questions:** 7 | **Checks:** 18 (8 core FIN.ACCT + 10 GOV.EFFECT overlay)
- **Key data fields:** restatements (count), material_weaknesses (count), auditor_opinion (text), altman_z_score (computed), sec_correspondence (text)
- **Source:** SEC 10-K, 8-K, DEF 14A via sec_client -> audit_risk, board_governance
- **Presentation:** Risk indicator for restatement/weakness; data table for audit metrics
- **Status:** GREEN (core checks work). 10 of 18 checks SKIPPED because GOV.EFFECT governance overlay requires DEF 14A extraction (audit_committee, auditor_change, sox_404, etc.). Core accounting checks (restatement=0 CLEAR, material_weakness=0 CLEAR, Z-score=10.17 CLEAR) fully functional.
- **Blocker:** Shared with Section 4 — DN-036 DEF 14A comprehensive parsing

## 3.6 Financial Distress Indicators (GREEN — SECONDARY SCORES SHARE ONE CHECK)

- **Questions:** 6 | **Checks:** 5 (all EVALUATIVE_CHECK)
- **Key data fields:** altman_z_score (computed), goodwill_risk (computed from debt_to_ebitda), impairment_risk (text), debt_ratio_increase (temporal), working_capital_deterioration (temporal)
- **Source:** SEC 10-K, XBRL via sec_client -> financial_statements
- **Presentation:** Risk indicator with distress zone classification; data table for component scores
- **Status:** GREEN. Altman Z-Score is the primary distress metric (10.17 = healthy CLEAR). Ohlson O-Score and Piotroski F-Score not individually computed — all 3 questions map to zone_of_insolvency. Temporal checks return INFO.

## 3.7 Guidance & Market Expectations (YELLOW — EXTRACTION NOT CONNECTED)

- **Questions:** 5 | **Checks:** 5 (all EVALUATIVE_CHECK)
- **Key data fields:** guidance_provided (from earnings_guidance), beat_rate (from yfinance), guidance_philosophy (from 8-K), post_earnings_drift (from stock data), consensus_divergence (computed)
- **Source:** SEC 8-K, yfinance via sec_client, market_client -> earnings_guidance, stock_performance
- **Presentation:** Data table for guidance metrics; risk indicator for consensus divergence
- **Status:** YELLOW. All 5 checks return INFO. Field routing fixed in Phase 33-05 (routes to guidance_provided, beat_rate, etc.) but underlying extraction modules do not populate these fields yet. Earnings_guidance extraction module exists but outputs not connected to state model fields.
- **Fix needed:** Connect earnings_guidance extraction outputs to state model fields consumed by check field routing

## 3.8 Sector-Specific Financial Metrics (GREEN — FUNCTIONING AS DESIGNED)

- **Questions:** 1 | **Checks:** 10 (2 MANAGEMENT_DISPLAY, 8 EVALUATIVE_CHECK)
- **Key data fields:** sector-conditional KPIs (energy reserves, retail same-store-sales, etc.), working_capital_trends (computed from current_ratio), AI/tech 10-K mention counts
- **Source:** SEC 10-K, 10-Q via sec_client -> financial_statements
- **Presentation:** Sector-conditional data table (only shows applicable metrics)
- **Status:** GREEN. Sector checks are contextual by design — energy/retail checks INFO for non-applicable sectors. Working_capital_trends evaluates numerically (AAPL=0.89 CLEAR). AI/tech FWRD.WARN checks detect relevant 10-K mentions but report INFO (by design).

---

# SECTION 4: GOVERNANCE & DISCLOSURE (REORGANIZED)

**Decision:** Reorganize from 9 subsections → 4 blocks. Absorb 4.9 into Early Warning Signals.

### User Direction
- Core governance question: "Have these people been in trouble before, and are they qualified?"
- Organize around PEOPLE, STRUCTURE, TRANSPARENCY, ACTIVIST — not by document type
- Prior litigation and personal scandals for board + execs is the #1 governance priority
- Qualifications and relevant experience for the roles they serve

## 4.1 People Risk (REORGANIZED — merges old 4.1 + 4.2)

**Core question:** Have these people been in trouble, and are they qualified?

### Final Structure
1. **👤 Board & Executive Profile** — Who is on the board and C-suite, qualifications, relevant experience
2. **⚖️ Prior Litigation & Investigations** — Prior lawsuits, SEC investigations, personal scandals for each individual
3. **🔄 Stability & Turnover** — C-suite changes, board departures, succession planning
4. **🎯 Key Person & Independence** — Founder risk, CEO-chair duality, board independence, overboarding

### AAPL Mockup
```
👤 People Risk
━━━━━━━━━━━━━
EXECUTIVES
  CEO: Tim Cook (tenure unavailable) | Prior lit: 🟢 None found
  CFO: Kevan Parekh (tenure unavailable) | Prior lit: 🟢 None found
  Aggregate exec risk score: 29.9 (🟢 LOW)

BOARD
  Size: ⚠️ Not extracted | Independence: ⚠️ Not extracted
  CEO-Chair Duality: 🔴 Yes
  Prior lit (any officer): 🟢 0 found
  Departures (18mo): 🟢 0
  Leadership Stability: 🟢 100/100
```

### Complexity Classification
| Question | Layer | Source |
|----------|-------|--------|
| Exec qualifications | DISPLAY | DEF 14A ⚠️ mostly SKIPPED |
| Prior litigation | HUNT | SCAC + web search ✅ working |
| Personal scandals | HUNT | Web search 🟡 partial |
| Board composition | DISPLAY | DEF 14A ⚠️ SKIPPED (DN-036) |
| C-suite turnover | EVALUATE | 8-K + DEF 14A ✅ working |
| Succession plan | EVALUATE | DEF 14A ⚠️ SKIPPED |
| CEO-chair duality | EVALUATE | DEF 14A ✅ TRIGGERED |

### Checks Absorbed (from old 4.1 + 4.2)
- 18 checks from 4.1 Board Composition (15 SKIPPED)
- 22 checks from 4.2 Executive Team (13 CLEAR, 2 SKIPPED)
- Total: 40 checks, many blocked by DN-036

## 4.2 Structural Governance (REORGANIZED — merges old 4.3 + 4.4 + 1.4.3)

### Final Structure
1. **💰 Compensation & Alignment** — CEO pay, structure, say-on-pay, clawback, golden parachute
2. **🛡️ Shareholder Rights** — Dual-class, anti-takeover, proxy access, forum selection
3. **🤝 Related-Party Transactions** — Intercompany complexity, RPT disclosure (absorbed from 1.4.3)

### AAPL Mockup
```
🏛️ Structural Governance
━━━━━━━━━━━━━━━━━━━━━━━━
COMPENSATION
  CEO Pay Ratio: 🔴 533:1 (threshold >500)
  Say-on-Pay: 🟢 92% approval
  Clawback: ⚠️ Not extracted
  Golden Parachute: ⚠️ Not extracted

SHAREHOLDER RIGHTS
  Dual-Class: 🟢 No
  Anti-Takeover: ⚠️ Not extracted
  Proxy Access: ⚠️ Not extracted
  Forum Selection: ⚠️ Not extracted

RELATED-PARTY
  RPT Disclosure: ⚠️ Not extracted
```

### Checks Absorbed
- 15 checks from 4.3 Compensation (11 SKIPPED)
- 10 checks from 4.4 Shareholder Rights (8 SKIPPED)
- Total: 25 checks, heavily blocked by DN-036

## 4.3 Transparency & Disclosure (REORGANIZED — merges old 4.6 + 4.7 + 4.8)

### Final Structure
1. **📋 Disclosure Quality** — Risk factor changes, filing timeliness, non-GAAP reconciliation, 8-K completeness
2. **📝 Narrative Analysis** — Tone shift, readability change, red-flag phrases, narrative coherence, management credibility (slimmed from 15 to 5 questions)
3. **🚨 Whistleblower & Investigation** — Whistleblower language, internal investigation signals

### Notes
- 4.7 slimmed from 15 → 5 core NLP analyses (see below)
- DN-035: Quantified NLP metrics needed (currently all return "present" or INFO)
- 4.8 whistleblower checks are GREEN and working

### 4.7 Slim (5 questions from original 15)
1. Tone shift (absorbs 4.7.2, 4.7.3, 4.7.4)
2. Readability change (absorbs 4.7.1, 4.7.13)
3. Red-flag phrases (absorbs 4.7.10, 4.7.11)
4. Narrative coherence (absorbs 4.7.5, 4.7.6, 4.7.7, 4.7.8, 4.7.14)
5. Management credibility score (absorbs 4.7.9, 4.7.12, 4.7.15)

## 4.4 Activist Pressure (KEPT STANDALONE from old 4.5)

- 4 questions, 14 checks. All CLEAR for AAPL (no activist activity).
- 13D filings, proxy contests, shareholder proposals, short activism.
- GREEN — no changes needed.

## 4.9 Media & External Narrative (ABSORBED)
**Decision:** Absorbed into Early Warning Signals (merged 1.9+1.10)
- No new data needs (already tracked under DN-031)

### Shared Blocker: DEF 14A Extraction
- DN-036: 🔴 DEF 14A comprehensive parsing — affects People Risk (4.1) + Structural Governance (4.2)
- Needs: board size, independence ratio, tenure, meeting count, attendance, committee details, compensation structure, clawback, golden parachute, hedging policy, proxy access, forum selection, classified board, supermajority, action by consent, special meeting threshold
- This is the single highest-impact extraction investment — unblocks 34 SKIPPED checks

---

# SECTION 5: LITIGATION & REGULATORY (REVIEWED)

**Decision:** Keep 7 subsections (was 9). Merge 5.7+5.8+5.9 into one "Litigation Risk Analysis" subsection.

## 5.1 Active SCAs (GREEN — NO CHANGES)
- 4 questions, 9 checks. SCAC data well-utilized. 1 historical case detected.

## 5.2 SCA History (GREEN — NO CHANGES)
- 4 questions, 7 checks. Historical count, outcomes, recidivist pattern detection.

## 5.3 Derivative & Merger Litigation (GREEN — NO CHANGES)
- 6 questions, 4 checks. 3 derivative suits TRIGGERED red. Merger objection CLEAR.

## 5.4 SEC Enforcement (YELLOW — MINOR FIXES)
- 4 questions, 9 checks. Stage detected as "NONE" but INFO not CLEAR. Count fields not populated.
- Enhancement: Convert sec_enforcement_stage="NONE" to evaluative CLEAR result

## 5.5 Other Regulatory & Government (GREEN — NO CHANGES)
- 6 questions, 13 checks. Sector-conditional checks correctly skip.

## 5.6 Non-Securities Litigation (GREEN — NO CHANGES)
- 4 questions, 14 checks. Aggregate count works. Individual categorization needs enhancement.

## 5.7+5.8+5.9 Litigation Risk Analysis (MERGED)
**Restructured from:** 3 RED subsections → 1 consolidated section
1. **🛡️ Defense Posture** — Forum selection, contingent liabilities (ASC 450), PSLRA safe harbor
2. **📊 Litigation Patterns** — Statute of limitations windows, temporal correlations, peer contagion
3. **🏭 Sector-Specific Patterns** — Industry allegation theories, sector regulatory databases
- All checks defined in checks.json but not wired to data mappers
- DN-037: 🔴 Litigation risk analysis pipeline (SOL mapper wiring, peer contagion, temporal correlation, sector patterns)
