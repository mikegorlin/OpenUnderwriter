# Requirements: D&O Underwriting System v3.1

**Defined:** 2026-03-06
**Core Value:** Eliminate LLM hallucination from all quantitative data by building a comprehensive XBRL extraction engine with forensic financial analysis, structured filing extraction, SEC Frames API peer benchmarking, and full signal integration. LLM shifts to pure analyst (qualitative/narrative only).

## v3.1 Requirements

75 requirements across 9 phases (67-75), 51 MUST + 24 SHOULD. Four critical problems addressed (original) plus system integrity:
1. **LLM hallucination risk**: ~40 financial concepts currently LLM-extracted with MEDIUM confidence. XBRL provides exact GAAP numbers at HIGH confidence.
2. **Shallow financial coverage**: Only 40 XBRL concepts, annual only (3 periods). Need 120+ concepts, 8 quarters + 3 annual, with QoQ/YoY trends.
3. **No forensic analysis**: Missing Beneish component decomposition, balance sheet forensics, capital allocation quality, revenue recognition red flags, debt/tax analysis.
4. **Fake peer benchmarking**: Current ratio-to-baseline proxy uses fixed baselines. SEC Frames API provides true percentile across all ~8,000 filers.

### XBRL Foundation (XBRL)

- [ ] **XBRL-01** [MUST]: Expand `xbrl_concepts.json` from 50 to 120+ concepts covering income statement (~15 new), balance sheet (~20 new), cash flow (~15 new). Each concept has priority-ordered tag list researched against real filings.
- [ ] **XBRL-02** [MUST]: Add `expected_sign` field to every concept in `xbrl_concepts.json`. Sign normalization layer applies after extraction, before any ratio computation. Log every normalization for audit trail.
- [ ] **XBRL-03** [MUST]: Derived concept computation module (`xbrl_derived.py`): margins (gross, operating, net, EBITDA), ratios (current, quick, D/E, D/EBITDA, interest coverage), per-share metrics (BV/share, FCF/share). All computed from XBRL primitives, zero LLM.
- [ ] **XBRL-04** [MUST]: Concept resolution coverage validator: after extraction, log which tag resolved per concept, track resolution rate per ticker. Alert when coverage drops below 60% for any statement type.
- [ ] **XBRL-05** [SHOULD]: Tag discovery utility: scan Company Facts for a CIK, dump all concepts with values. Used for tag research when adding new concepts.
- [ ] **XBRL-06** [MUST]: Total liabilities derivation hardened for edge cases: minority interest, preferred stock, companies using only `LiabilitiesAndStockholdersEquity`.

### Quarterly Extraction (QTRLY)

- [ ] **QTRLY-01** [MUST]: Extract 8 quarters of XBRL data from Company Facts API by filtering `form_type="10-Q"`. Store in new `QuarterlyStatements` model on `state.extracted.financials.quarterly_xbrl`.
- [ ] **QTRLY-02** [MUST]: YTD-to-quarterly disambiguation for duration concepts (income statement, cash flow). Q1 = as-reported. Q2 = H1 - Q1. Q3 = 9mo - H1. Balance sheet items taken as-is (instant concepts).
- [ ] **QTRLY-03** [MUST]: Fiscal period alignment using `fy` + `fp` fields. Handle non-calendar fiscal years (AAPL Sep, SHW Dec). Store both fiscal period labels AND calendar-aligned period.
- [ ] **QTRLY-04** [MUST]: QoQ and YoY trend computation: sequential change, same-quarter YoY (Q1-to-Q1 eliminates seasonality), acceleration/deceleration detection (growth speeding up or slowing).
- [ ] **QTRLY-05** [MUST]: Sequential pattern detection: 4+ quarters of margin compression, revenue deceleration, cash flow deterioration. Flag these as trend signals.
- [ ] **QTRLY-06** [MUST]: XBRL/LLM reconciler: XBRL always wins for numeric data. Log divergence when both sources have values. LLM retains role for narratives, qualitative assessments, risk factors.
- [ ] **QTRLY-07** [SHOULD]: Validation against yfinance quarterly data: cross-check XBRL quarterly values against existing yfinance_quarterly for the same periods. Log discrepancies.
- [ ] **QTRLY-08** [MUST]: Every quarterly value carries `SourcedValue` with source=`XBRL:10-Q:{end_date}:CIK{cik}:accn:{accn}`, confidence=HIGH.

### Forensic Analysis (FRNSC)

- [ ] **FRNSC-01** [MUST]: Balance sheet forensics module: goodwill impairment risk (goodwill/TA trend), intangible concentration, off-balance-sheet exposure (operating leases/TA), cash conversion cycle (8-quarter trend), working capital manipulation (current ratio QoQ volatility).
- [ ] **FRNSC-02** [MUST]: Capital allocation forensics: ROIC trend (3+ year), acquisition effectiveness (goodwill growth vs revenue growth), buyback timing quality (avg buyback price vs avg stock price), dividend sustainability (FCF payout ratio).
- [ ] **FRNSC-03** [MUST]: Debt/tax forensics: interest coverage trajectory (8-quarter), debt maturity concentration (short-term/total ratio), effective tax rate anomalies (deviation from 21% statutory), deferred tax liability growth vs revenue, pension underfunding (pension liability/equity).
- [ ] **FRNSC-04** [MUST]: Revenue quality forensics: deferred revenue growth vs revenue growth, channel stuffing indicator (AR growth 2x+ revenue), margin compression (gross margin declining 4+ quarters), OCF/revenue ratio trend.
- [ ] **FRNSC-05** [MUST]: Beneish M-Score component decomposition: expose all 8 individual indices (DSRI, GMI, AQI, SGI, DEPI, SGAI, TATA, LVGI) in output. Contextualize with growth rate when SGI drives the score.
- [ ] **FRNSC-06** [MUST]: All forensic modules return Pydantic models + ExtractionReport. Composite confidence = min(input confidences).
- [ ] **FRNSC-07** [SHOULD]: Multi-period forensic trajectory: run Beneish/Sloan/accruals across 8 quarters to detect manipulation trend onset, not just latest-period snapshot.
- [ ] **FRNSC-08** [SHOULD]: M&A forensics: acquisition history from XBRL (PaymentsToAcquireBusinessesNetOfCashAcquired trend), serial acquirer detection, goodwill accumulation rate, acquisition-driven revenue vs organic.
- [ ] **FRNSC-09** [SHOULD]: Earnings quality dashboard: Sloan Accruals Ratio (safe/warning/danger zones), cash flow manipulation index, SBC as % of revenue trend, non-GAAP vs GAAP earnings gap indicator.

### Signal Integration (SIG)

- [ ] **SIG-01** [MUST]: 20-30 new forensic brain signals in `fin/forensic_xbrl.yaml` covering all forensic module outputs. Each signal has `field_key` mapping to `analyzed.forensics.*` paths.
- [x] **SIG-02** [MUST]: Upgrade 45 XBRL-replaceable signals: update `data_strategy.field_key` to point to XBRL-sourced paths. Confidence automatically upgrades from MEDIUM to HIGH.
- [x] **SIG-03** [MUST]: Enhance 28 XBRL-enhanceable signals: XBRL for numeric threshold evaluation, LLM narrative retained for context/interpretation.
- [x] **SIG-04** [MUST]: Shadow evaluation for all signal changes: run both old and new field_key mappings for at least one validation cycle. Log per-signal result changes. Zero unexpected flips before cutover.
- [ ] **SIG-05** [MUST]: Reactivate 15+ of the 24 broken/skipped signals by wiring to newly available XBRL or web search data.
- [ ] **SIG-06** [SHOULD]: 12 new signal opportunities from audit: revenue recognition risk, level 3 fair value, pension underfunding, operating lease burden, goodwill deterioration, SBC dilution, related party, insider trading pattern deviation, option exercise-sell, peer valuation gap, estimate revision, M&A integration risk.
- [ ] **SIG-07** [MUST]: Cross-ticker validation: re-run AAPL, RPM, SNA, V, WWD with XBRL-first extraction. Update golden baselines. Document per-signal deltas.
- [ ] **SIG-08** [SHOULD]: Web search tier 2: wire 35 web-search-candidate signals to Brave Search + Exa acquisition. Qualitative/fuzzy data that XBRL can't cover (whistleblower, sentiment, journalism, Glassdoor).

### Form 4 Enhancement (FORM4)

- [ ] **FORM4-01** [MUST]: Parse `sharesOwnedFollowingTransaction` from Form 4 XML. Track post-transaction ownership per insider. Flag when C-suite sells >25% of holdings in 6 months.
- [ ] **FORM4-02** [MUST]: Deduplicate by accession number + transaction date + owner. Prefer Form 4/A (amendments) over original filings.
- [ ] **FORM4-03** [MUST]: Exclude gift transactions (code G) and estate transfers (code W) from buy/sell aggregation. Handle $0 price transactions (grants, RSU vesting) separately.
- [ ] **FORM4-04** [SHOULD]: Exercise-and-sell pattern detection: same owner, same date, code M followed by code S. Report as combined event.
- [ ] **FORM4-05** [SHOULD]: Parse `isDirector`, `isOfficer`, `isTenPercentOwner` relationship flags. Annotate indirect ownership (`directOrIndirectOwnership`).
- [ ] **FORM4-06** [SHOULD]: Filing timing analysis: compare transaction dates against subsequent 8-K filing dates. Detect selling before negative announcements.

### Peer Benchmarking (PEER)

- [ ] **PEER-01** [MUST]: SEC Frames API client: `acquire_frames(concepts, periods)` fetches cross-filer data for 10-15 key metrics. Cache aggressively (180 days for completed periods, 1 day for current).
- [ ] **PEER-02** [MUST]: True percentile computation: rank company against ALL SEC filers for each concept. Replace ratio-to-baseline proxy.
- [ ] **PEER-03** [MUST]: SIC-code filtering: cross-reference Frames response with SEC `company_tickers.json` for sector-relative percentile. Cache CIK-to-SIC mapping.
- [ ] **PEER-04** [MUST]: Benchmark 10-15 metrics via Frames: revenue, net income, total assets (size); D/E, current ratio, interest coverage (health); operating margin, net margin, ROE (profitability); revenue growth YoY (growth).
- [ ] **PEER-05** [SHOULD]: Percentile signals: brain signals that fire on peer-relative thresholds (e.g., revenue_percentile < 25th, leverage > 90th).
- [ ] **PEER-06** [SHOULD]: Keep existing yfinance peer group for non-XBRL metrics (volatility, short interest, governance score).

### Rendering & Bug Fixes (RENDER)

- [ ] **RENDER-01** [MUST]: 8-quarter trend table template: tabbed view (Income | Balance | Cash Flow), QoQ change with color-coded arrows, sparkline SVG per key metric.
- [ ] **RENDER-02** [MUST]: Forensic dashboard template: grid of hazard cards with color-coded severity (green/yellow/red), key metric value + trend arrow + one-line explanation.
- [ ] **RENDER-03** [MUST]: Peer percentile display: horizontal bar showing company position within all filers, sector-relative overlay. CSS-only, no JavaScript.
- [ ] **RENDER-04** [SHOULD]: Enhanced insider trading table: ownership concentration column, 10b5-1 plan status indicator, cluster event highlighting.
- [ ] **RENDER-05** [SHOULD]: Beneish component breakdown display: 8 individual indices with visual indicators and contextual notes.
- [ ] **RENDER-06** [MUST]: BUG FIX: False SCA classification -- boilerplate "normal course of business" 10-K language misclassified as active SCA.
- [ ] **RENDER-07** [MUST]: BUG FIX: PDF header overlap with content on first page.
- [ ] **RENDER-08** [SHOULD]: Company logo embedding in HTML output header.
- [ ] **RENDER-09** [MUST]: All new templates work in both HTML and PDF (details expanded in PDF, charts render identically).

### System Integrity (SYS)

- [ ] **SYS-01** [MUST]: Explicit Tier 1 data manifest document listing every always-acquired data source, each traced to a foundational signal in `brain/signals/base/`.
- [ ] **SYS-02** [MUST]: Expand foundational signals to cover 100% of actual Tier 1 acquisitions: add 8-K, Form 4, short interest, Frames API, CourtListener as foundational signal declarations.
- [ ] **SYS-03** [SHOULD]: Signal author guide documenting when to add `acquisition:` blocks vs relying on Tier 1, how to populate `gap_bucket`/`gap_keywords`, and the foundational vs evaluative distinction.
- [ ] **SYS-04** [MUST]: Automated template-to-facet validation: CI test that asserts every `.html.j2` template is referenced by a facet YAML entry, and every facet `template:` field points to an existing file.
- [ ] **SYS-05** [SHOULD]: Remove or consolidate orphaned legacy templates identified by the template-facet audit.
- [ ] **SYS-06** [MUST]: Semantic content QA: test framework that validates rendered field values against source data (e.g., revenue in HTML matches XBRL value from state, board size matches DEF 14A extraction).
- [ ] **SYS-07** [SHOULD]: Integrate cross-ticker QA and semantic validation into CI pipeline (not just manual scripts).
- [ ] **SYS-08** [MUST]: Closed-loop feedback auto-adjustment: when N underwriter corrections confirm a signal threshold is miscalibrated, auto-propose (or auto-apply with flag) revised thresholds.
- [ ] **SYS-09** [MUST]: Fire-rate anomaly alerts: detect and log when signals cross thresholds (always-fire >95%, never-fire across 5+ tickers, skip-rate >60%) with recommended action.
- [ ] **SYS-10** [MUST]: Signal lifecycle state machine: ACTIVE -> INCUBATING -> ARCHIVED with automatic transitions based on effectiveness metrics and feedback history.

## Requirement Priority Summary

| Priority | Count | Categories |
|----------|-------|------------|
| MUST | 51 | XBRL foundation, quarterly extraction, forensics, signals, Form 4, peer benchmarking, rendering, bug fixes, system integrity |
| SHOULD | 24 | Tag discovery, validation, M&A forensics, earnings dashboard, web search signals, Form 4 extras, logo, signal author guide, CI integration |
| **Total** | **75** | 9 phases |

## Cross-Cutting Concerns

- **Shadow evaluation** is mandatory when switching any signal from LLM to XBRL data source (SIG-04)
- **SourcedValue provenance** on every value: source, confidence, as_of (QTRLY-08)
- **No new dependencies** -- everything needed is already installed
- **All free SEC data** -- no paid APIs
- **Anti-hallucination guarantee**: XBRL for numbers, LLM for words. Never mix without flagging.
