# Roadmap: v13.0 Worksheet Excellence

## Overview

Transform the worksheet from a data dump into a decision document. Six phases address pipeline resilience, naming cleanup, visual polish, manifest wiring, a new question-driven underwriting section, and cross-ticker validation. Phase 144 establishes the resilient foundation, three independent workstreams follow (rename/dedup, manifest wiring, Q&A section), visual consistency unifies everything after rename, and cross-ticker validation proves it all works.

## Phases

- [x] **Phase 144: Pipeline & Rendering Resilience** - Pipeline always completes; rendering always produces output; no crashes on missing data (completed 2026-03-28)
- [x] **Phase 145: Rename & Deduplication** - One name for the report; each fact appears once with a home section (completed 2026-03-28)
- [x] **Phase 147: Golden Manifest Wiring** - Every manifest template renders meaningful content or is gracefully suppressed (completed 2026-03-28)
- [x] **Phase 148: Question-Driven Underwriting Section** - New standalone section with 50-80 underwriting questions auto-answered from pipeline data (completed 2026-03-28)
- [ ] **Phase 146: Visual Consistency Pass** - Every section looks like it belongs in the same document; print-ready
- [ ] **Phase 149: Cross-Ticker Validation & Baselines** - Worksheet verified across 4 company types with golden baselines

## Phase Details

### Phase 144: Pipeline & Rendering Resilience
**Goal**: Underwriter always gets a worksheet -- pipeline completes all stages or fails clearly, rendering handles missing data gracefully, and partial results still produce useful output
**Depends on**: Nothing (foundation phase)
**Requirements**: RES-01, RES-02, RES-03, RES-04, RES-05, RES-06
**Success Criteria** (what must be TRUE):
  1. Running `underwrite ORCL` produces an HTML worksheet even when individual pipeline stages fail -- failed sections show "Incomplete" banners instead of crashing
  2. Opening a worksheet for a company with no litigation data shows "No data available" placeholders in chart areas and "Data not available" messages in narrative sections -- no AttributeError or empty white space
  3. State.json contains a stage_status block showing each of the 7 stages with status, duration, and error message (if any) -- inspectable after every run
  4. Risk card section renders Supabase SCA data even when EXTRACT stage fails -- the two data paths are independent
**Plans**: 3 plans
Plans:
- [x] 144-01-PLAN.md -- Pipeline catch-and-continue + CLI exit code + audit status
- [x] 144-02-PLAN.md -- Chart null-safety decorator + section failure banners + risk card isolation
- [x] 144-03-PLAN.md -- Gap closure: wire pipeline status table, stage banners, and chart placeholders into rendering

### Phase 145: Rename & Deduplication
**Goal**: The report has one name ("worksheet") and each metric has one home section with full context -- all other appearances are cross-references or the persistent header bar
**Depends on**: Phase 144
**Requirements**: NAME-01, NAME-02, DEDUP-01, DEDUP-02, DEDUP-03, DEDUP-04
**Success Criteria** (what must be TRUE):
  1. `grep -r "beta_report" src/ tests/ templates/` returns zero matches -- the name is gone from the entire codebase
  2. Revenue appears with full provenance (source, period, confidence) in the Financial section and as a compact reference in the header bar -- nowhere else in the worksheet
  3. Market cap, stock price, board size each appear in exactly their home section plus the header bar -- verified by automated dedup check
**Plans**: 3 plans
Plans:
- [x] 145-01-PLAN.md -- Rename beta_report to uw_analysis across all source, templates, tests, scripts
- [x] 145-02-PLAN.md -- Deduplicate headline metrics to home sections + header bar
- [ ] 145-03-PLAN.md -- Gap closure: fix broken stock chart tests + wire revenue provenance into Financial section

### Phase 147: Golden Manifest Wiring
**Goal**: Every one of the 27 recently-added manifest templates either renders meaningful content from pipeline data or is suppressed -- no empty cards, no placeholder text, no unwired templates
**Depends on**: Phase 144
**Requirements**: WIRE-01, WIRE-02, WIRE-03, WIRE-04, WIRE-05
**Success Criteria** (what must be TRUE):
  1. Running the AAPL worksheet shows content in every manifest group that has upstream data -- audit log categorizes all 27 templates as "renders", "wired", or "suppressed"
  2. Adverse events, tariff risk, and ESG indicators appear as manifest groups with data flowing from pipeline state
  3. Automated manifest completeness test passes -- every group either has content or an explicit suppression guard
  4. No empty cards or tables visible in the rendered HTML -- suppressed templates produce zero DOM elements
**Plans**: 2 plans
Plans:
- [x] 147-01-PLAN.md -- Manifest audit classification engine + completeness test suite
- [x] 147-02-PLAN.md -- Wire suppression guards, alt-data context, and audit into render pipeline

### Phase 148: Question-Driven Underwriting Section
**Goal**: A new section after Scoring presents 50-80 underwriting questions organized by domain, auto-answered with specific numbers and evidence from pipeline data, so the underwriter can make the decision without leaving the worksheet
**Depends on**: Phase 144
**Requirements**: QFW-01, QFW-02, QFW-03, QFW-04, QFW-05, QFW-06, QFW-07
**Success Criteria** (what must be TRUE):
  1. The ORCL worksheet contains an "Underwriting Decision Framework" section between Scoring and Meeting Prep with questions grouped by 8 domains (company, financial, governance, market, litigation, operational, program, decision)
  2. At least 80% of questions show auto-filled answers with specific dollar amounts, percentages, dates, and verdict badges -- not vague assessments like "Beneish inconclusive"
  3. Questions marked "Needs Review" include specific filing references ("Check 10-K Item 9A, FY2025") telling the underwriter exactly where to find the answer
  4. Supabase scenario-specific questions appear alongside brain domain questions when the company has SCA filing history
  5. Question definitions live in `brain/questions/*.yaml` with full schema (question_id, text, weight, data_sources, answer_template, upgrade/downgrade criteria)
**Plans**: 3 plans
Plans:
- [x] 148-01-PLAN.md -- Answerers subpackage with dedicated answerer for all 55 questions + tests
- [x] 148-02-PLAN.md -- SCA question generator with all 4 scenario types + tests
- [x] 148-03-PLAN.md -- SCA/verdict integration, context ordering fix, print CSS, visual verification
**UI hint**: yes
**Pre-work (built during Phase 145 session, commit 17a81876):**
  - 55 questions across 8 domains in `brain/questions/*.yaml` — loader, YAML schema, domain ordering
  - `uw_questions.py` context builder — auto-answers from pipeline data, verdict badges, evidence, filing refs
  - `uw_questions.html.j2` template — domain groups with completeness bars, verdict dots, evidence
  - Wired into `uw_analysis.py` and `uw_analysis.html.j2` with nav button
  - 8 domain-specific answerers (BIZ-01, BIZ-03, FIN-01, FIN-02, GOV-01, LIT-01, MKT-01, UW-01) + screening_answers fallback
  - **Remaining for 148**: add answerers for remaining 47 questions, Supabase scenario questions (QFW-04), answer quality validation across tickers, tests

### Phase 146: Visual Consistency Pass
**Goal**: Every section in the worksheet follows the same visual language -- consistent typography, spacing, card styles, table formatting, and print-ready layout
**Depends on**: Phase 145
**Requirements**: VIS-01, VIS-02, VIS-03, VIS-04, VIS-05, VIS-06
**Success Criteria** (what must be TRUE):
  1. All tables in the worksheet use identical font sizes (8pt body, 7pt header), padding, and row striping -- verified by CSS audit showing zero inline style overrides on table elements
  2. All summary cards and layer cards have uniform dimensions, padding (10px), border-radius (6px), and color-coding -- no visual mismatch between sections
  3. Printing the worksheet to PDF produces clean output with thin layer borders, page breaks at section boundaries, no nav bar, and no fixed positioning artifacts
  4. Zero empty cards, tables, or sections visible -- every included sub-template has an `{% if %}` guard that suppresses it when data is absent
**Plans**: TBD
**UI hint**: yes

### Phase 149: Cross-Ticker Validation & Baselines
**Goal**: The worksheet is proven to work across 4 company archetypes (mega-cap, repeat filer, small/mid-cap, recent IPO) with golden baselines captured for visual regression
**Depends on**: Phase 144, Phase 145, Phase 146, Phase 147, Phase 148
**Requirements**: VAL-01, VAL-02, VAL-03, VAL-04, VAL-05, VAL-06, VAL-07
**Success Criteria** (what must be TRUE):
  1. AAPL worksheet has all sections populated with real data, zero N/A where pipeline has data, and visual baseline screenshots captured per section
  2. ORCL worksheet renders risk card with SCA scenarios, screening questions auto-answered with real verdicts, and litigation section fully populated
  3. A small/mid-cap ticker worksheet handles sparse governance data (fewer directors, missing backgrounds) and missing financial quarters without crashes or empty sections
  4. A recent IPO or distressed ticker worksheet renders IPO-specific features and handles limited trading history gracefully
  5. Automated QA script runs across all 4 tickers verifying: all sections have content, no rendering errors, no raw Python/debug strings, N/A count within threshold
**Plans**: TBD

## Progress

**Execution Order:** 144 -> 145 -> 147 -> 148 -> 146 -> 149

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 144. Pipeline & Rendering Resilience | 3/3 | Complete    | 2026-03-28 |
| 145. Rename & Deduplication | 3/3 | Complete    | 2026-03-28 |
| 147. Golden Manifest Wiring | 2/2 | Complete    | 2026-03-28 |
| 148. Question-Driven Underwriting | 3/3 | Complete   | 2026-03-28 |
| 146. Visual Consistency Pass | 0/TBD | Not started | - |
| 149. Cross-Ticker Validation | 0/TBD | Not started | - |
