# Data Needs Tracker — Question Review

**Purpose:** Running list of all extraction gaps, new data requirements, and engineering work identified during question-by-question review. This becomes the engineering backlog after the design review is complete.

**Updated:** As each subsection is reviewed

---

## Summary Dashboard

| Priority | Count | Description |
|----------|-------|-------------|
| 🔴 New extraction needed | 20 | Data not extracted at all today |
| 🟡 Extraction exists, needs enhancement | 12 | Data partially available, needs enrichment |
| 🟢 Rendering/surfacing only | 3 | Data exists in pipeline, just not displayed |
| 🔵 New config/mapping | 2 | Config files or mapping tables needed |

---

## 🔴 New Extraction Needed

### DN-001: Revenue by Product/Service Segment ($ and %)
- **Needed by:** 1.2 Business Model & Revenue
- **Current state:** BIZ.MODEL.revenue_segment returns 10-K mention count, not actual segment data
- **Required:** Structured table: segment name, revenue $, % of total, YoY trend
- **Source:** 10-K Item 7 (Operating Segments) — Apple reports Products vs Services and 5 product lines
- **Extraction method:** LLM extraction from 10-K segment discussion / XBRL segment reporting tags
- **Fallback:** XBRL `us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax` by segment → yfinance (limited)
- **Complexity:** Extract & Display
- **AAPL example:** iPhone ~$201B (51%), Services ~$96B (25%), Mac ~$30B (8%), iPad ~$27B (7%), Wearables ~$37B (9%)

### DN-002: Revenue by Geography ($ and %)
- **Needed by:** 1.2 Business Model & Revenue
- **Current state:** BIZ.MODEL.revenue_geo returns country names list only (Ireland, Japan, etc.), no percentages
- **Required:** Structured table: region, revenue $, % of total
- **Source:** 10-K Item 7 (Geographic Segments) — Apple reports Americas, Europe, Greater China, Japan, Rest of Asia Pacific
- **Extraction method:** LLM extraction from 10-K geographic segment table / XBRL geographic segment tags
- **Fallback:** XBRL geographic segment tags → estimate from subsidiary locations (Exhibit 21)
- **Complexity:** Extract & Display
- **AAPL example:** Americas ~$170B (42%), Europe ~$102B (25%), Greater China ~$67B (19%), Japan ~$25B (7%), Rest of APAC ~$27B (7%)

### DN-003: Gross Margin by Segment
- **Needed by:** 1.2 Business Model & Revenue (earnings analysis)
- **Current state:** Not extracted at all
- **Required:** Segment-level gross margin % to show where earnings actually come from
- **Source:** 10-K Item 7 — Apple reports Products gross margin vs Services gross margin
- **Extraction method:** LLM extraction from 10-K segment profitability discussion
- **Fallback:** Compute from XBRL segment revenue and COGS if available
- **Complexity:** Extract & Compute
- **AAPL example:** Products ~37% margin, Services ~73% margin → Services is 25% of revenue but ~42% of gross profit

### DN-004: Share Buyback Program
- **Needed by:** 1.2 Business Model & Revenue (capital allocation)
- **Current state:** Not extracted
- **Required:** Annual buyback amount, cumulative program size
- **Source:** 10-K / 10-Q (share repurchase table typically in Item 5 or notes)
- **Extraction method:** LLM extraction from 10-K
- **Fallback:** Compute from shares outstanding delta (yfinance historical)
- **Complexity:** Extract & Display
- **AAPL example:** ~$90B+ annually

### DN-005: GICS Code
- **Needed by:** 1.1 Company Snapshot
- **Current state:** yfinance has sector/industry text but numeric GICS code not extracted
- **Required:** 8-digit GICS code (e.g., 45202030 for Technology Hardware)
- **Source:** yfinance `info` dict
- **Extraction method:** Map yfinance sector + industry to GICS code, OR direct GICS lookup
- **Fallback:** SIC → GICS mapping table (config file DN-010)
- **Complexity:** Extract & Display

### DN-006: Business Model Narrative Summary
- **Needed by:** 1.1 (short version), 1.2 (expanded version)
- **Current state:** 10-K Item 1 raw text available; yfinance `longBusinessSummary` available
- **Required:** 2-3 sentence summary for 1.1 snapshot; expanded narrative for 1.2
- **Source:** 10-K Item 1
- **Extraction method:** LLM summarization of Item 1 text
- **Fallback:** yfinance `longBusinessSummary` → web search
- **Complexity:** Extract & Display (with LLM summarization)

### DN-007: Business Model Trajectory / Evolution
- **Needed by:** 1.2 Business Model & Revenue
- **Current state:** Not extracted
- **Required:** Key business model shifts (revenue mix change, geographic shifts, adjacent bets)
- **Source:** 10-K year-over-year comparison (current vs prior year Item 1 / Item 7)
- **Extraction method:** LLM comparison of current vs prior 10-K
- **Fallback:** Revenue mix trend computed from multi-year segment data
- **Complexity:** Extract & Infer

---

## 🟡 Extraction Exists, Needs Enhancement

### DN-008: Revenue Type Classification (Recurring vs One-Time)
- **Needed by:** 1.2 Business Model & Revenue
- **Current state:** BIZ.MODEL.revenue_type returns 10-K mention count
- **Required:** Classification: recurring %, one-time %, mixed — with dollar amounts if possible
- **Source:** 10-K Item 1 / Item 7
- **Enhancement:** Upgrade from mention count to LLM classification with percentage estimate
- **Fallback:** —

### DN-009: R&D and CapEx Spend
- **Needed by:** 1.2 Business Model & Revenue (capital allocation)
- **Current state:** Likely available in XBRL financial statements extraction but not surfaced to business model section
- **Required:** R&D $, CapEx $, both as % of revenue
- **Source:** XBRL `ResearchAndDevelopmentExpense`, `PaymentsToAcquirePropertyPlantAndEquipment`
- **Enhancement:** Surface existing XBRL data to 1.2 display; add % of revenue computation
- **Fallback:** 10-K income statement / cash flow LLM extraction

### DN-010: Market Cap Relative Ranking
- **Needed by:** 1.1 Company Snapshot
- **Current state:** Peer market caps acquired via peer_group module but ranking not computed
- **Required:** "Top N US public company" or "Xth percentile in sector"
- **Enhancement:** Compute ranking from existing peer data
- **Fallback:** —

### DN-011: Dividend Information
- **Needed by:** 1.2 Business Model & Revenue (capital allocation)
- **Current state:** yfinance `dividendRate` / `dividendYield` available but not surfaced
- **Required:** Annual dividend amount, yield
- **Enhancement:** Surface existing yfinance data
- **Fallback:** 10-K / 10-Q LLM extraction

---

## 🟢 Rendering/Surfacing Only

### DN-012: Net Cash/Debt Position
- **Needed by:** 1.2 Business Model & Revenue (capital allocation)
- **Current state:** debt_to_ebitda computed; cash and debt extracted via XBRL
- **Required:** Simple net cash = total cash - total debt display
- **Enhancement:** Compute and surface as display field
- **Fallback:** Already has XBRL data

### DN-013: Customer Concentration Display
- **Needed by:** 1.2 Business Model & Revenue (concentrations)
- **Current state:** BIZ.DEPEND.customer_conc returns "Not mentioned" for AAPL (correct — no >10% customer)
- **Required:** Display "No customer >10% of revenue" as 🟢 when not disclosed (SEC requires disclosure of >10% customers)
- **Enhancement:** Interpret absence of disclosure as positive signal
- **Fallback:** —

### DN-014: Business Description (Short)
- **Needed by:** 1.1 Company Snapshot
- **Current state:** 10-K Item 1 raw text extracted; yfinance longBusinessSummary available
- **Required:** Clean 2-3 sentence version
- **Enhancement:** LLM summarization or use yfinance summary as-is
- **Fallback:** Already has two sources

---

## 🔵 New Config/Mapping Needed

### DN-015: SIC → GICS Mapping Table
- **Needed by:** 1.1 Company Snapshot (GICS fallback)
- **Deliverable:** `config/sic_gics_mapping.json` — maps 4-digit SIC codes to 8-digit GICS codes
- **Source:** Standard industry classification crosswalk (publicly available)
- **Used by:** Fallback when yfinance doesn't provide GICS directly

### DN-016: config/fallback_chains.json
- **Needed by:** Overall system (all subsections)
- **Deliverable:** Per-field fallback chain configuration consumed by acquisition stage
- **Built from:** Fallback tables accumulated during this review
- **Created after:** Full 45-subsection review is complete

---

## From 1.3 Operational Risk & Dependencies

### DN-017: Named Supplier Extraction
- **Needed by:** 1.3 | **Complexity:** HUNT
- **Current:** supplier_conc = 1 mention (qualitative)
- **Target:** Named suppliers + dependency type + single-source flag from 10-K Item 1/1A
- **Source:** 10-K Item 1, Item 1A → LLM extraction
- **Fallback:** Web search for "[company] major suppliers"

### DN-018: Manufacturing vs Sales Geography Classification
- **Needed by:** 1.3 | **Complexity:** COMPUTE
- **Current:** Exhibit 21 country names listed
- **Target:** Classify each subsidiary/location as manufacturing, sales, or legal entity
- **Source:** Exhibit 21 + 10-K Item 1 → LLM classification
- **Fallback:** Infer from subsidiary names and country patterns

### DN-019: Single-Source Supplier Identification
- **Needed by:** 1.3 | **Complexity:** HUNT
- **Current:** Not extracted
- **Target:** Identify "sole source" / "single source" disclosures with supplier name
- **Source:** 10-K Item 1A risk factors → LLM extraction
- **Fallback:** Web search for "[company] single source supplier risk"

### DN-020: Regulatory Actions with Jurisdiction + Status
- **Needed by:** 1.3 | **Complexity:** HUNT
- **Current:** regulatory_dep = 2 mentions (count only)
- **Target:** Specific actions: agency, jurisdiction, status (active/resolved), potential impact
- **Source:** 10-K Item 1A + Item 3 → LLM extraction
- **Fallback:** Web search for "[company] regulatory investigation"

### DN-021: Data Types Held + Privacy Regime Mapping
- **Needed by:** 1.3 | **Complexity:** EVALUATE
- **Current:** cyber_posture = 9 mentions
- **Target:** Data types (PII/PHI/financial/children), applicable regimes (GDPR/CCPA/HIPAA)
- **Source:** 10-K Item 1, Item 1A → LLM extraction
- **Fallback:** Infer from business model + geography

### DN-022: Labor Risk Extraction (Fixes False Trigger)
- **Needed by:** 1.3 | **Complexity:** HUNT
- **Current:** Routes to employee_count (150K) — FALSE TRIGGER
- **Target:** Unionization status, NLRB complaints, labor disputes, WARN Act filings
- **Source:** 10-K Item 1A + 8-K → LLM extraction; web search for NLRB/WARN
- **Fallback:** Web search for "[company] labor dispute union"

### DN-023: Key Person Dependency + Succession Plan
- **Needed by:** 1.3 | **Complexity:** EVALUATE
- **Current:** key_person = "Not mentioned"
- **Target:** CEO/founder dependency disclosure, succession plan existence from DEF 14A
- **Source:** DEF 14A + 10-K Item 1A → LLM extraction
- **Fallback:** Infer from CEO tenure + board succession committee existence

### DN-024: ESG/Sustainability Claims Extraction
- **Needed by:** 1.3 | **Complexity:** HUNT
- **Current:** Routes to regulatory_dep (shared)
- **Target:** Specific environmental/sustainability claims made (e.g., "carbon neutral")
- **Source:** 10-K Item 1 + CSR/ESG report references → LLM extraction
- **Fallback:** Web search for "[company] greenwashing ESG claims"

---

## From 1.4 Corporate Structure & Complexity

### DN-025: Exhibit 21 Subsidiary Parsing
- **Needed by:** 1.4 | **Complexity:** DISPLAY
- **Current:** Not extracted
- **Target:** Structured list: entity name, jurisdiction, ownership % from Exhibit 21
- **Source:** 10-K Exhibit 21 → parsing/LLM extraction
- **Fallback:** 10-K Item 1 description → web search

### DN-026: VIE/SPE Detection
- **Needed by:** 1.4 | **Complexity:** EVALUATE
- **Current:** Not extracted
- **Target:** Presence flag, entity names, consolidation status, risk assessment
- **Source:** 10-K notes to financial statements → LLM extraction
- **Fallback:** 10-Q notes → web search for "[company] variable interest entity"

## From 1.6 M&A & Corporate Transactions

### DN-027: Acquisition History Extraction
- **Needed by:** 1.6 | **Complexity:** HUNT
- **Current:** Not extracted
- **Target:** Structured list: target name, date, deal size, rationale, integration status
- **Source:** 10-K notes to financial statements + 8-K filings → LLM extraction
- **Fallback:** Web search for "[company] acquisitions [year]"

### DN-028: Goodwill-to-Assets Ratio
- **Needed by:** 1.6 | **Complexity:** COMPUTE
- **Current:** Goodwill likely in XBRL but ratio not computed
- **Target:** Goodwill/total assets %, impairment history, write-down flag
- **Source:** XBRL `Goodwill`, `Assets`
- **Fallback:** 10-K balance sheet LLM extraction

### DN-029: Deal Litigation Extraction
- **Needed by:** 1.6 | **Complexity:** HUNT
- **Current:** Not extracted separately from general SCA data
- **Target:** Merger objection suits, appraisal actions filtered from SCA data
- **Source:** SCAC database (filter by merger objection category) + 10-K Item 3
- **Fallback:** Web search for "[company] merger lawsuit"

### DN-030: Divestiture/Spin-off Extraction
- **Needed by:** 1.6 | **Complexity:** HUNT
- **Current:** Not extracted
- **Target:** Divestitures, spin-offs, major asset sales with dates and amounts
- **Source:** 8-K filings (Item 2.01) + 10-K Item 7
- **Fallback:** Web search for "[company] divestiture spinoff"

---

## From Section 4: Governance & Disclosure

### DN-035: Quantified NLP Metrics
- **Needed by:** 4.7 | **Complexity:** COMPUTE
- **Current:** NLP checks detect presence ("present") but don't quantify
- **Target:** Fog Index delta (YoY), negative tone score change, hedging language frequency, forward-looking statement count change, coherence score
- **Source:** 10-K text analysis (already acquired, needs NLP computation)
- **Fallback:** Simpler word-count-based proxies

### DN-036: DEF 14A Comprehensive Parsing (HIGHEST IMPACT)
- **Needed by:** 4.1, 4.3, 4.4 | **Complexity:** HUNT
- **Current:** DEF 14A acquired but only ceo_pay_ratio, say_on_pay_pct, ceo_chair_duality, dual_class extracted
- **Target:** Full proxy statement parsing: board composition (size, independence, tenure, meetings, attendance, committees), compensation details (structure, clawback, golden parachute, hedging, perks), shareholder rights (proxy access, forum selection, classified board, supermajority, action by consent, special meeting threshold)
- **Source:** DEF 14A → LLM structured extraction
- **Fallback:** ISS/Glass Lewis governance scores (web search)
- **Impact:** Unblocks 34 SKIPPED checks across 3 subsections

---

## From Section 5: Litigation

### DN-037: Litigation Risk Analysis Pipeline
- **Needed by:** 5.7+5.8+5.9 merged | **Complexity:** INFER
- **Current:** Checks defined in checks.json, sol_mapper module exists, nothing wired
- **Target:** SOL window computation, peer contagion scoring, stock drop → filing event temporal correlation, sector-specific allegation pattern matching
- **Source:** SCAC data + stock drops + 10-K filings (all already acquired)
- **Fallback:** Manual analyst review flags

---

## From Section 2: Market

### DN-032: Beta and Average Daily Volume
- **Needed by:** 2.3 | **Complexity:** DISPLAY
- **Current:** Trade liquidity routes to current_price; beta not extracted
- **Target:** Beta value, avg daily volume, volume trend
- **Source:** yfinance `info['beta']`, `info['averageDailyVolume10Day']`
- **Fallback:** Computed from price returns vs market returns

### DN-033: Analyst Count, Consensus Rating, Price Target
- **Needed by:** 2.6 | **Complexity:** DISPLAY
- **Current:** Both checks route to beat_rate instead of analyst metrics
- **Target:** Number of analysts, consensus recommendation, mean/median price target, target vs current price
- **Source:** yfinance `info['numberOfAnalystOpinions']`, `info['recommendationMean']`, `info['targetMeanPrice']`
- **Fallback:** Web search for "[ticker] analyst ratings"

### DN-034: Valuation Ratio Extraction
- **Needed by:** 2.7 | **Complexity:** DISPLAY
- **Current:** pe_ratio, ev_ebitda, peg_ratio fields not populated despite yfinance data
- **Target:** Forward P/E, trailing P/E, EV/EBITDA, PEG ratio stored in correct ExtractedData fields
- **Source:** yfinance `info['forwardPE']`, `info['trailingPE']`, `info['enterpriseToEbitda']`, `info['pegRatio']`
- **Fallback:** Computed from market cap, earnings, EBITDA

---

## From 1.9+1.10 Early Warning Signals

### DN-031: Web Intelligence Acquisition Infrastructure
- **Needed by:** 1.9+1.10 | **Complexity:** HUNT (platform)
- **Current:** No web scraping for employee/customer signals
- **Target:** Acquisition modules for Glassdoor, LinkedIn, CFPB, app stores, Trustpilot, social media, web traffic
- **Source:** Multiple web APIs and scraping targets
- **Fallback:** Brave Search as catch-all for "[company] glassdoor reviews", "[company] layoffs", etc.
- **Note:** This is infrastructure, not a single field — enables 16+ individual checks

---

## Tracking by Subsection

| Subsection | Data Needs Created | IDs |
|-----------|-------------------|-----|
| 1.1 Company Snapshot | 5 | DN-005, DN-006, DN-010, DN-014, DN-015 |
| 1.2 Business Model & Revenue | 9 | DN-001, DN-002, DN-003, DN-004, DN-007, DN-008, DN-009, DN-011, DN-012, DN-013 |
| 1.3 Operational Risk & Dependencies | 8 | DN-017, DN-018, DN-019, DN-020, DN-021, DN-022, DN-023, DN-024 |
| 1.4 Corporate Structure & Complexity | 2 | DN-025, DN-026 |
| 1.5 Geographic Footprint | 0 | (absorbed into 1.2 + 1.3) |
| 1.6 M&A & Corporate Transactions | 4 | DN-027, DN-028, DN-029, DN-030 |
| 1.7 Competitive Position | 0 | (absorbed into 1.2 + 1.8) |
| 1.8 Macro & Industry Environment | 0 | No new DN items (existing checks need threshold enhancement) |
| 1.9+1.10 Early Warning Signals | 1 | DN-031 (web intelligence platform) |
| 1.11 Risk Calendar | 0 | No gaps — model subsection |
| 2.1-2.8 Market (all) | 3 | DN-032 (beta/volume), DN-033 (analyst), DN-034 (valuation ratios) |
| 3.1-3.8 Financial (all) | 0 | No new DN items (calibration/wiring fixes only) |
| 4.1-4.8 Governance (kept) | 2 | DN-035 (NLP metrics), DN-036 (DEF 14A parsing) |
| 4.9 Media & External | 0 | (absorbed into Early Warning Signals, DN-031) |
| 5.1-5.6 Litigation (kept) | 0 | No new DN items (minor wiring fixes) |
| 5.7+5.8+5.9 Lit Risk Analysis | 1 | DN-037 (litigation risk pipeline) |
