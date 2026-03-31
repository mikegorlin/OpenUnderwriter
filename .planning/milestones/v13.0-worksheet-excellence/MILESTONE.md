# v13.0 — Worksheet Excellence

## Vision: The Final Product

An underwriter opens the ORCL worksheet. Here's what they see:

### Page 0: Decision Dashboard (unchanged)
The 5-year stock strip, 6 mini-cards (MCap, Price, Revenue, Profitability, Balance Sheet, Valuation), litigation status bar, combo stock chart, key risk findings with evidence, and underwriter priority metrics. This page tells the story in 30 seconds. **No changes needed — this works.**

### Every Section After Page 0 Follows This Pattern:
1. **Navy header bar** with section title + key badge (Quality Score, Governance Score, etc.)
2. **Summary cards** — 5-8 most important metrics for that domain, color-coded by risk level. The underwriter sees the answer before asking the question.
3. **Key visual** — the chart or visualization that tells THIS section's story at a glance. Stock & Market opens with 1Y+5Y price charts side by side with sector ETF overlay. Financial opens with the 8 metric cards + margin/forensic scores. Governance opens with board cards + ISS risk scores + independence donut.
4. **Narrative opener** — 2-3 sentences connecting this section to the D&O risk story. Written like a human underwriter, not an AI.
5. **Layered detail cards** — organized by analytical theme, each in a colored bordered card:
   - **Navy** = structural/core data (statements, board composition, case lists)
   - **Red** = risk/loss/exposure (distress scores, active cases, claim probability)
   - **Amber** = alerts/flags/warnings (audit alerts, watch items, earnings miss)
   - **Blue** = analytical/investigative (forensics, patterns, peer comparisons)
   - **Green** = actions/recommendations (underwriting posture, tower recommendation)
   - **Purple** = people/governance (board detail, executive risk, compensation)
6. **Checks** — data quality and completeness at the bottom of each section

### The New Section: Underwriting Decision Framework (after Scoring, before Meeting Prep)
A standalone section that reorganizes the ENTIRE analysis as questions an underwriter asks. Not meeting prep (those are questions to ask the COMPANY). These are questions the underwriter asks THEMSELVES to make the decision.

Organized by domain with auto-filled answers:

**Financial Health (10-12 questions)**
- "Is there refinancing risk in the next 24 months?" → Answer pulls debt maturity schedule, interest coverage, cash position. Verdict: ▲ UPGRADE / ▼ DOWNGRADE with evidence.
- "What is the GAAP vs non-GAAP delta?" → Answer pulls actual numbers, not just "Beneish inconclusive."
- "Has the company disclosed any material weakness?" → Answer pulls 10-K Item 9A, auditor opinion, MW signals.

**Governance Quality (8-10 questions)**
- "CFO tenure — how long, any recent changes?" → Answer pulls officer data, 8-K Item 5.02 events.
- "Is the board independent enough?" → Answer pulls independence ratio, dual class, classified board.
- "Are insiders selling before bad news?" → Answer pulls Form 4 timing analysis, scienter level.

**Market Risk (6-8 questions)**
- "Has the stock dropped >15% in the last 12 months?" → Answer pulls actual drop events with dates and catalysts.
- "What is short interest telling us?" → Answer pulls % of float, days to cover, trend.
- "What does the settlement severity curve look like at this market cap?" → Answer pulls scenario benchmarks.

**Litigation Exposure (8-10 questions)**
- "Is this a repeat filer?" → Answer pulls Supabase risk card data with filing count, settlement rate, total exposure.
- "What scenarios match this company?" → Answer pulls matched scenario benchmarks with dismissal rates, settlement distributions.
- "Are there open SOL windows?" → Answer pulls actual window dates and statuses.

**Operational Risk (6-8 questions)**
- "Is revenue recognition complex (ASC 606)?" → Answer pulls industry, revenue model type, segment analysis.
- "What is the disruption risk?" → Answer pulls sector analysis, competitive position.
- "Are there regulatory exposure areas?" → Answer pulls regulatory map, compliance signals.

**D&O Program (4-6 questions)**
- "What tower position makes sense?" → Answer pulls tower recommendation, settlement severity, claim probability.
- "What is the right retention?" → Answer pulls market cap, loss history, peer benchmarks.

Each question shows: **verdict badge** (▲/▼/—/?), **answer with specific numbers** (not vague assessments), **evidence bullets** (data source + confidence), **upgrade/downgrade criteria** (what makes this better/worse). Questions that can't be auto-answered show "Needs Review" with exactly where to find the data.

### What Makes This Different From What We Have Today:
- **One fact, one home** — revenue appears in Financial section and Decision Dashboard. Nowhere else. If the underwriter wants revenue context, they go to Financial.
- **Every number has a source and date** — "$416.2B (FY2025 · XBRL)" not just "$416.2B"
- **Empty sections don't render** — if a sub-template has no data, it's invisible, not an empty card
- **The report works on ANY ticker** — mega-cap, mid-cap, recent IPO, distressed. No crashes, no empty pages, no partial renders.
- **Named correctly** — it's "the worksheet," not "the beta report"

---

## Issues Catalog (from this session)

### Fixed This Session
- [x] Stock & Market summary cards showed insider trading → now Price/Beta/Short/Range/Drawdown/Analyst
- [x] Charts buried after 300 lines of content → now first visual element after summary cards
- [x] Monolithic 2,500-line template → decomposed into 12 per-section files
- [x] 27 manifest templates existed but weren't included → all added to sections
- [x] Scoring section was flat list → organized into 5 analytical layers
- [x] All sections now have colored layer grouping
- [x] Financial/Governance sections had verdict before metric cards → reordered
- [x] HTML entities (&#9650;) showing as text → replaced with Unicode ▲▼
- [x] Adverse events collected but not displayed → added to market context
- [x] SUPABASE_KEY not configured → added to .zshrc + settings.local.json
- [x] Supabase risk card wired end-to-end with auto-answer engine
- [x] 142-02 quality gates (real-state tests + template validation)

### Not Fixed — Must Fix in v13.0
1. **Pipeline resilience** — ORCL ran but didn't complete SCORE/ANALYZE/RENDER. CLI silently produced partial state. No HTML output on first run. Pipeline MUST complete all stages or fail clearly.
2. **Rendering resilience** — if scoring is None, section should show "Not completed" not render empty. Risk card should render even when extraction is incomplete.
3. **Combo chart crash** — `stock_drops` can be None, crashes chart_1_combo with AttributeError. Every chart builder needs None guards.
4. **Duplicate data** — Revenue, market cap, stock price, board size appear 3-4 times across sections.
5. **"Beta report" naming** — 11 Python files, 3 templates still use the name.
6. **Shallow auto-answerers** — ACCT-03 says "Beneish inconclusive" instead of pulling actual GAAP vs non-GAAP numbers. ACCT-04 can't find CFO because officer data isn't in a clean field.
7. **Sub-template styling inconsistent** — different font sizes, spacing, table styles within the same layer card.
8. **No visual regression testing** — no golden baselines, no automated comparison.
9. **Many of 27 newly-added templates may render empty** — context data not wired for all of them.
10. **Question framework is Python-only** — should be YAML-driven per brain portability principle.
11. **Print/PDF not optimized** — page breaks, margins, layer borders in print need work.
12. **No cross-ticker validation** — only AAPL tested thoroughly. ORCL exposed pipeline failures.

---

## Phases

### Phase 144: Pipeline & Rendering Resilience
**Goal:** Pipeline always completes. Rendering always produces output. No crashes on missing data.

Requirements:
- RES-01: Pipeline completes all 7 stages or logs clear error with stage name and traceback. State.json includes stage status for each stage.
- RES-02: Every chart builder guards against None data — no AttributeError crashes. Empty chart renders "No data available" placeholder.
- RES-03: Every section template guards against missing context — if scoring is None, show "Scoring not completed" banner. If extracted.market is None, market section shows acquired data summary.
- RES-04: Risk card renders from acquired_data even when extraction is incomplete — Supabase data is independent of the extraction pipeline.
- RES-05: CLI always produces HTML output — even on partial pipeline completion, render what exists with "Incomplete" markers on missing sections.
- RES-06: Pipeline stage status tracked in state.json — each stage records status (pending/running/complete/failed), duration, and error message if failed.

### Phase 145: Rename & Deduplication
**Goal:** One name for the report. Each fact appears once.

Requirements:
- NAME-01: Rename beta_report → worksheet_report across all Python files (11 files), templates (3 files), context builders, and tests. Single PR, mechanical rename.
- NAME-02: Context variable `beta_report` → `report` in all templates.
- DEDUP-01: Define "home section" for each major metric — where it appears with full context and provenance. All other appearances cross-reference.
- DEDUP-02: Revenue home = Financial section. Market cap home = Decision Dashboard mini-card. Stock price home = Stock & Market section. Board size home = Governance section.
- DEDUP-03: Header bar keeps MCap/Revenue/Price/Employees as persistent reference — these are the ONLY allowed cross-section duplicates.
- DEDUP-04: Remove redundant metric displays from sections that aren't the home — replace with layout space for section-specific content.

### Phase 146: Visual Consistency Pass
**Goal:** Every section looks like it belongs in the same document.

Requirements:
- VIS-01: Define a section CSS stylesheet with standard classes for: summary card, layer card, table, metric row, narrative block, check item. All inline styles migrate to classes.
- VIS-02: All tables use the same font sizes (8pt body, 7pt header), padding (4px 8px), and row striping pattern.
- VIS-03: All summary cards use the same dimensions, font sizes, and color-coding thresholds.
- VIS-04: Layer cards have consistent padding (10px), border-radius (6px), margin-bottom (12px), and header style.
- VIS-05: Empty sub-template suppression — every included template wraps content in `{% if data %}...{% endif %}`. Zero empty cards, tables, or sections.
- VIS-06: Print stylesheet — layer borders print as thin lines, page breaks at section boundaries, no nav bar, no fixed header.

### Phase 147: Golden Manifest Wiring
**Goal:** Every manifest-defined template renders meaningful content or is gracefully suppressed.

Requirements:
- WIRE-01: Audit all 27 recently-added manifest templates — categorize as: has data (renders), no data (needs wiring), structurally empty (suppress).
- WIRE-02: For each "needs wiring" template, identify the state path and context builder that should populate it. Wire the data.
- WIRE-03: For each "structurally empty" template, add `{% if %}` guard so it produces zero output when no data.
- WIRE-04: Add missing manifest groups: adverse_events display, tariff risk assessment, ESG indicators.
- WIRE-05: Manifest completeness test — automated check that every manifest group either renders content or is explicitly suppressed.

### Phase 148: Question-Driven Underwriting Section
**Goal:** New standalone section with 50-80 underwriting questions auto-answered from pipeline data.

Requirements:
- QFW-01: Define underwriting question framework in `brain/questions/` as YAML files, organized by domain (financial.yaml, governance.yaml, market.yaml, litigation.yaml, operational.yaml, program.yaml).
- QFW-02: Each question YAML specifies: question_id, question text, weight (1-10), domain, data_sources (state paths to check), upgrade_criteria, downgrade_criteria, why_it_matters, answer_template (how to format the answer from data).
- QFW-03: Expand auto-answer engine from 11 answerers to full coverage — deep cross-referencing, actual numbers not vague assessments. ACCT-03 pulls real GAAP/non-GAAP numbers. ACCT-04 extracts CFO name and tenure from governance data.
- QFW-04: Supabase scenario-specific questions merge with brain domain questions — company's scenario history determines which SCA questions appear alongside universal underwriting questions.
- QFW-05: Section template renders questions grouped by domain, sorted by weight within domain. Summary bar shows: N answered, N concerns, N favorable, N needs review.
- QFW-06: "Needs Review" questions show exactly where to find the data — "Check 10-K Item 9A, proxy statement audit committee report" not just "insufficient data."
- QFW-07: Section positioned after Scoring, before Meeting Prep in the report.

### Phase 149: Cross-Ticker Validation & Baselines
**Goal:** Worksheet verified across 4 company types. Golden baselines established.

Requirements:
- VAL-01: AAPL (mega-cap, clean governance, no active litigation) — full pipeline run, all sections populated, zero N/A where data exists, visual baseline captured.
- VAL-02: ORCL (repeat filer, active litigation, accounting fraud scenario) — risk card flows, SCA scenarios render, screening questions answered with real verdicts.
- VAL-03: Small/mid-cap ticker (TBD — governance issues, limited data) — board section handles sparse data, officer backgrounds show what's available, financial section handles missing quarters.
- VAL-04: Recent IPO or distressed ticker (TBD) — IPO-specific features render, limited history handled, binary event classification works.
- VAL-05: Per-section golden baseline screenshots for each ticker — stored as reference images for visual regression.
- VAL-06: Automated cross-ticker QA script: for each ticker, verify all sections have content, no rendering errors, no raw Python/debug strings, N/A count within threshold.
- VAL-07: Side-by-side comparison tool — render same ticker before/after changes, diff the HTML for regressions.

---

## Phase Dependencies

```
Phase 144 (Resilience) ──→ Phase 149 (Validation)
                      ╲
Phase 145 (Rename/Dedup) ─→ Phase 146 (Visual) ──→ Phase 149
                      ╱
Phase 147 (Manifest) ────→ Phase 149

Phase 148 (Q&A Section) ──→ Phase 149
```

144 is foundation — must be first. 145/147/148 are independent. 146 depends on 145 (new class names after rename). 149 is the capstone — validates everything.

## Execution Order
1. **Phase 144** — Resilience (fix crashes, guards, stage tracking)
2. **Phase 145** — Rename + Dedup (clean naming, eliminate redundancy)
3. **Phase 147** — Manifest Wiring (surface hidden data)
4. **Phase 148** — Q&A Section (new underwriting decision framework)
5. **Phase 146** — Visual Consistency (polish everything)
6. **Phase 149** — Cross-Ticker Validation (prove it works)

## Success Criteria

1. `underwrite ORCL` produces a complete worksheet with zero crashes, all sections populated, risk card data flowing, screening questions auto-answered
2. A 30-year underwriter opens the worksheet and can make a decision without referring to any other source
3. Zero N/A values where pipeline has data
4. Zero duplicate facts without progressive disclosure purpose
5. Question-driven section auto-answers 80%+ questions with specific numbers and cross-referenced evidence
6. Every golden manifest group renders meaningful content or is gracefully suppressed
7. Visual regression baselines established for 4+ tickers
8. No file in the codebase contains "beta_report" in any context
