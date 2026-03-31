# v13.0 Requirements — Worksheet Excellence

**Defined:** 2026-03-28
**Core Value:** The single source of truth for underwriters to make the most knowledgeable decisions on a risk.

## Pipeline & Rendering Resilience

- [x] **RES-01**: Pipeline completes all 7 stages or logs clear error with stage name and traceback; state.json includes stage status for each stage
- [x] **RES-02**: Every chart builder guards against None data — no AttributeError crashes; empty chart renders "No data available" placeholder
- [x] **RES-03**: Every section template guards against missing context — if scoring is None, show "Scoring not completed" banner; if extracted.market is None, market section shows acquired data summary
- [ ] **RES-04**: Risk card renders from acquired_data even when extraction is incomplete — Supabase data independent of extraction pipeline
- [x] **RES-05**: CLI always produces HTML output — even on partial pipeline completion, render what exists with "Incomplete" markers on missing sections
- [x] **RES-06**: Pipeline stage status tracked in state.json — each stage records status (pending/running/complete/failed), duration, and error message if failed

## Rename & Deduplication

- [x] **NAME-01**: Rename beta_report → worksheet_report across all Python files (11 files), templates (3 files), context builders, and tests
- [x] **NAME-02**: Context variable `beta_report` → `report` in all templates
- [x] **DEDUP-01**: Define "home section" for each major metric — where it appears with full context and provenance; all other appearances cross-reference
- [x] **DEDUP-02**: Revenue home = Financial section; Market cap home = Decision Dashboard mini-card; Stock price home = Stock & Market section; Board size home = Governance section
- [x] **DEDUP-03**: Header bar keeps MCap/Revenue/Price/Employees as persistent reference — ONLY allowed cross-section duplicates
- [x] **DEDUP-04**: Remove redundant metric displays from sections that aren't the home — replace with layout space for section-specific content

## Visual Consistency

- [ ] **VIS-01**: Define section CSS stylesheet with standard classes for: summary card, layer card, table, metric row, narrative block, check item; all inline styles migrate to classes
- [ ] **VIS-02**: All tables use same font sizes (8pt body, 7pt header), padding (4px 8px), and row striping pattern
- [ ] **VIS-03**: All summary cards use same dimensions, font sizes, and color-coding thresholds
- [ ] **VIS-04**: Layer cards have consistent padding (10px), border-radius (6px), margin-bottom (12px), and header style
- [ ] **VIS-05**: Empty sub-template suppression — every included template wraps content in `{% if data %}...{% endif %}`; zero empty cards, tables, or sections
- [ ] **VIS-06**: Print stylesheet — layer borders print as thin lines, page breaks at section boundaries, no nav bar, no fixed header

## Golden Manifest Wiring

- [x] **WIRE-01**: Audit all 27 recently-added manifest templates — categorize as: has data (renders), no data (needs wiring), structurally empty (suppress)
- [x] **WIRE-02**: For each "needs wiring" template, identify the state path and context builder that should populate it; wire the data
- [x] **WIRE-03**: For each "structurally empty" template, add `{% if %}` guard so it produces zero output when no data
- [x] **WIRE-04**: Add missing manifest groups: adverse_events display, tariff risk assessment, ESG indicators
- [x] **WIRE-05**: Manifest completeness test — automated check that every manifest group either renders content or is explicitly suppressed

## Question-Driven Underwriting Section

- [x] **QFW-01**: Define underwriting question framework in `brain/questions/` as YAML files organized by domain (financial, governance, market, litigation, operational, program)
- [x] **QFW-02**: Each question YAML specifies: question_id, question text, weight (1-10), domain, data_sources (state paths), upgrade/downgrade criteria, why_it_matters, answer_template
- [x] **QFW-03**: Expand auto-answer engine from 11 answerers to full coverage — deep cross-referencing, actual numbers not vague assessments
- [x] **QFW-04**: Supabase scenario-specific questions merge with brain domain questions — company's scenario history determines which SCA questions appear
- [x] **QFW-05**: Section template renders questions grouped by domain, sorted by weight; summary bar shows: N answered, N concerns, N favorable, N needs review
- [x] **QFW-06**: "Needs Review" questions show exactly where to find the data — specific filing references, not just "insufficient data"
- [x] **QFW-07**: Section positioned after Scoring, before Meeting Prep in the report

## Cross-Ticker Validation & Baselines

- [ ] **VAL-01**: AAPL (mega-cap, clean governance) — full pipeline run, all sections populated, zero N/A where data exists, visual baseline captured
- [ ] **VAL-02**: ORCL (repeat filer, active litigation) — risk card flows, SCA scenarios render, screening questions answered with real verdicts
- [ ] **VAL-03**: Small/mid-cap ticker (TBD — governance issues, limited data) — board section handles sparse data, financial section handles missing quarters
- [ ] **VAL-04**: Recent IPO or distressed ticker (TBD) — IPO-specific features render, limited history handled
- [ ] **VAL-05**: Per-section golden baseline screenshots for each ticker — stored as reference images for visual regression
- [ ] **VAL-06**: Automated cross-ticker QA script: verify all sections have content, no rendering errors, no raw Python/debug strings, N/A count within threshold
- [ ] **VAL-07**: Side-by-side comparison tool — render same ticker before/after changes, diff the HTML for regressions

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| RES-01 | Phase 144 | Complete |
| RES-02 | Phase 144 | Complete |
| RES-03 | Phase 144 | Complete |
| RES-04 | Phase 144 | Pending |
| RES-05 | Phase 144 | Complete |
| RES-06 | Phase 144 | Complete |
| NAME-01 | Phase 145 | Complete |
| NAME-02 | Phase 145 | Complete |
| DEDUP-01 | Phase 145 | Complete |
| DEDUP-02 | Phase 145 | Complete |
| DEDUP-03 | Phase 145 | Complete |
| DEDUP-04 | Phase 145 | Complete |
| VIS-01 | Phase 146 | Pending |
| VIS-02 | Phase 146 | Pending |
| VIS-03 | Phase 146 | Pending |
| VIS-04 | Phase 146 | Pending |
| VIS-05 | Phase 146 | Pending |
| VIS-06 | Phase 146 | Pending |
| WIRE-01 | Phase 147 | Complete |
| WIRE-02 | Phase 147 | Complete |
| WIRE-03 | Phase 147 | Complete |
| WIRE-04 | Phase 147 | Complete |
| WIRE-05 | Phase 147 | Complete |
| QFW-01 | Phase 148 | Complete |
| QFW-02 | Phase 148 | Complete |
| QFW-03 | Phase 148 | Complete |
| QFW-04 | Phase 148 | Complete |
| QFW-05 | Phase 148 | Complete |
| QFW-06 | Phase 148 | Complete |
| QFW-07 | Phase 148 | Complete |
| VAL-01 | Phase 149 | Pending |
| VAL-02 | Phase 149 | Pending |
| VAL-03 | Phase 149 | Pending |
| VAL-04 | Phase 149 | Pending |
| VAL-05 | Phase 149 | Pending |
| VAL-06 | Phase 149 | Pending |
| VAL-07 | Phase 149 | Pending |
