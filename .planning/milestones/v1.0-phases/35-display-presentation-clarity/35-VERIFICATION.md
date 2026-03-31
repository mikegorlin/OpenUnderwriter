---
phase: 35-display-presentation-clarity
verified: 2026-02-21T16:00:00Z
status: gaps_found
score: 11/13 must-haves verified
gaps:
  - truth: "Financial tables have conditional formatting with YoY coloring in HTML output (VIS-04)"
    status: partial
    reason: "financial_row macro has direction param and yoy coloring CSS, but extract_financials() never passes yoy_change values to the template. YoY column always renders '--'. Distress model uses traffic_light (correct). Infrastructure exists; data not wired."
    artifacts:
      - path: "src/do_uw/templates/html/sections/financial.html.j2"
        issue: "financial_row calls pass direction but no yoy_change — YoY column always shows '--', conditional coloring never fires"
      - path: "src/do_uw/stages/render/html_renderer.py"
        issue: "build_html_context delegates to build_template_context which does not include yoy_change values in financials dict"
    missing:
      - "extract_financials() or build_html_context must compute and expose yoy_change percentages per metric"
      - "financial.html.j2 must pass yoy_change to financial_row() calls once data is available"
  - truth: "No source file over 500 lines (CLAUDE.md anti-pattern constraint)"
    status: failed
    reason: "section_assessments.py is 561 lines, violating the explicit project rule. Plan 01 required it stay under 500; Plan 07 added jurisdiction logic pushing it 61 lines over."
    artifacts:
      - path: "src/do_uw/stages/analyze/section_assessments.py"
        issue: "561 lines, 61 over project limit. Plan 01 specified 'split into section_assessments.py + section_density_helpers.py' if too large."
    missing:
      - "Extract _HIGH_RISK_JURISDICTIONS, _classify_jurisdiction_risk(), _compute_company_density() into section_density_helpers.py (or similar name)"
      - "Import and re-export from section_assessments.py for backward compat"
human_verification:
  - test: "Run full pipeline on AAPL and open generated PDF"
    expected: "Bloomberg-quality PDF with navy/gold palette, Company Snapshot header block, section narratives labeled 'AI Assessment', density indicators on elevated/critical sections, distress model traffic lights in financial section"
    why_human: "Visual quality of Playwright-rendered PDF cannot be verified programmatically"
  - test: "Run full pipeline and check LLM narrative generation"
    expected: "Pre-computed narratives appear in both PDF and Word output with '[AI Assessment]' label. CLEAN sections get 2-3 sentences, CRITICAL sections get 6-8 sentences."
    why_human: "Requires live ANTHROPIC_API_KEY and real pipeline run to verify LLM integration end-to-end"
  - test: "Open generated Word document and verify density indicators"
    expected: "Sections with ELEVATED density show amber 'ELEVATED CONCERN' text before section content. CRITICAL sections show red 'CRITICAL RISK' text."
    why_human: "Word document visual rendering not testable programmatically (tests verify paragraphs exist but not rendering fidelity)"
---

# Phase 35: Display & Presentation Clarity Verification Report

**Phase Goal:** Upgrade rendering pipeline from functional output to Bloomberg/S&P-quality presentation with density-driven content, LLM narratives, and zero analytical logic in render stage.
**Verified:** 2026-02-21T16:00:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | DensityLevel enum has exactly three values: CLEAN, ELEVATED, CRITICAL | VERIFIED | `from do_uw.models.density import DensityLevel; list(DensityLevel)` returns 3 values confirmed by live import |
| 2 | SectionDensity model has level, subsection_overrides, concerns, critical_evidence fields | VERIFIED | density.py lines 41-66, all fields present with typed defaults |
| 3 | AnalysisResults has section_densities dict and pre_computed_narratives field | VERIFIED | state.py lines 210-218; `AnalysisResults().section_densities == {}`, `pre_computed_narratives == None` confirmed |
| 4 | section_assessments.py computes three-tier density per section | VERIFIED | Five density helpers: _compute_governance_density, _compute_litigation_density, _compute_financial_density, _compute_market_density, _compute_company_density — all return SectionDensity |
| 5 | Analytical functions (score_to_risk_level, etc.) live in benchmark/, not render/ | VERIFIED | benchmark/risk_levels.py confirmed; render/sect7_scoring.py imports `from do_uw.stages.benchmark.risk_levels import score_to_risk_level` |
| 6 | check_engine propagates content_type into every check result | VERIFIED | check_engine.py line 121: `result.content_type = content_type` in all code paths |
| 7 | LLM narratives generated in BENCHMARK, stored in pre_computed_narratives | VERIFIED | narrative_generator.py generate_all_narratives() wired in benchmark/__init__.py lines 258-264 |
| 8 | LLM content labeled "AI Assessment" per DATA-14 | VERIFIED | narrative_generator.py line 147: `labeled = f"AI Assessment: {narrative}"` |
| 9 | Bloomberg HTML template foundation with Tailwind CDN and macro components | VERIFIED | base.html.j2 loads tailwindcss CDN; 5 component files confirmed; styles.css has #0B1D3A palette |
| 10 | 8 section templates and 2 appendix templates with density-conditional rendering | VERIFIED | All 10 templates exist; each section uses density_indicator, section_narrative, traffic_light macros |
| 11 | Playwright-based PDF renderer integrated into RenderStage | VERIFIED | html_renderer.py uses sync_playwright with WeasyPrint fallback; RenderStage imports render_html_pdf |
| 12 | Financial tables have conditional formatting with YoY coloring in HTML (VIS-04) | PARTIAL | financial_row macro has conditional coloring logic and direction param; distress model uses traffic_light correctly. But yoy_change never supplied from context — YoY column always renders '--' |
| 13 | Zero analytical logic in render/ (automated audit) | VERIFIED | test_zero_analytical_logic.py passes all 7 tests; _HIGH_RISK_JURISDICTIONS moved to section_assessments.py; no scoring functions in render/ |

**Score:** 11/13 truths fully verified, 1 partial, 1 failed

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/models/density.py` | DensityLevel enum, SectionDensity, PreComputedNarratives | VERIFIED | 92 lines, all three models present with correct fields |
| `src/do_uw/stages/analyze/section_assessments.py` | Three-tier density computation | VERIFIED (with warning) | Computes 5 section densities correctly; FILE IS 561 LINES (61 over project 500-line limit) |
| `src/do_uw/stages/benchmark/risk_levels.py` | score_to_risk_level, score_to_threat_label, dim_score_threat | VERIFIED | All 3 functions present with public names; backward-compat aliases in render/ |
| `src/do_uw/stages/benchmark/narrative_helpers.py` | build_thesis_narrative, build_risk_narrative, build_claim_narrative | VERIFIED | All 3 builders present; BenchmarkStage uses direct imports |
| `src/do_uw/stages/benchmark/narrative_generator.py` | generate_section_narrative, generate_all_narratives, generate_executive_thesis | VERIFIED | 451 lines; all 3 entry points present; AI Assessment labeling; SHA-256 cache; density-tiered max_tokens |
| `src/do_uw/templates/html/base.html.j2` | Tailwind CDN, Bloomberg colors, header/footer, print styles | VERIFIED | Tailwind CDN script tag; #0B1D3A in custom config; macro imports from all 5 components |
| `src/do_uw/templates/html/components/badges.html.j2` | traffic_light, density_indicator, confidence_marker macros | VERIFIED | All 3 macros confirmed at expected line numbers |
| `src/do_uw/templates/html/components/tables.html.j2` | data_table, kv_table, financial_row macros | VERIFIED | All macros present with conditional formatting logic (but yoy_change not wired from context) |
| `src/do_uw/templates/html/styles.css` | Bloomberg palette #0B1D3A, #D4A843, #B91C1C | VERIFIED | All 3 colors as CSS custom properties |
| `src/do_uw/templates/html/sections/executive.html.j2` | Company Snapshot block (SECT1-01) | VERIFIED | Lines 13-26 implement SECT1-01 with kv_table |
| `src/do_uw/templates/html/sections/financial.html.j2` | Conditional formatting tables (VIS-04) | PARTIAL | Distress model uses traffic_light correctly; financial summary uses financial_row with direction but yoy_change never passed |
| `src/do_uw/templates/html/sections/market.html.j2` | embed_chart for stock/ownership (VIS-01, VIS-02) | VERIFIED | embed_chart("stock_1y"), embed_chart("stock_5y"), embed_chart("ownership") confirmed |
| `src/do_uw/templates/html/sections/litigation.html.j2` | embed_chart for timeline (VIS-03) | VERIFIED | embed_chart("timeline") confirmed |
| `src/do_uw/templates/html/appendices/coverage.html.j2` | % checks evaluated, gap notices | VERIFIED | coverage_stats, gap_notice macro, blind spot status all present |
| `src/do_uw/stages/render/html_renderer.py` | Playwright PDF renderer, build_html_context | VERIFIED | 373 lines; sync_playwright with WeasyPrint fallback; full context builder |
| `src/do_uw/stages/render/word_renderer.py` | Density indicators, pre-computed narrative paragraphs | VERIFIED | _add_density_indicator(), _add_section_narrative() implemented; DensityLevel imported and used |
| `tests/stages/render/test_zero_analytical_logic.py` | AST audit for no analytical logic in render/ | VERIFIED | 7 tests all pass; test_no_threshold_comparisons_in_render, test_pipeline_stages_count confirmed |
| `tests/stages/render/test_render_integration.py` | End-to-end render integration | VERIFIED | 7 tests all pass; test_all_formats_render confirmed |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `section_assessments.py` | `models/density.py` | `from do_uw.models.density import DensityLevel, SectionDensity` | VERIFIED | Import confirmed at line 16 |
| `models/state.py` | `models/density.py` | `section_densities: dict[str, SectionDensity]` | VERIFIED | Lines 210-218 in state.py |
| `stages/benchmark/__init__.py` | `narrative_generator.py` | `from do_uw.stages.benchmark.narrative_generator import generate_all_narratives` | VERIFIED | Lines 258-259 in benchmark/__init__.py |
| `stages/render/sections/sect7_scoring.py` | `benchmark/risk_levels.py` | `from do_uw.stages.benchmark.risk_levels import score_to_risk_level` | VERIFIED | Line 27 in sect7_scoring.py |
| `stages/render/sections/sect8_ai_risk.py` | `benchmark/risk_levels.py` | `from do_uw.stages.benchmark.risk_levels import score_to_threat_label, dim_score_threat` | VERIFIED | Lines 34-36 in sect8_ai_risk.py |
| `stages/render/__init__.py` | `html_renderer.py` | `from do_uw.stages.render.html_renderer import render_html_pdf` | VERIFIED | Line 22 in render/__init__.py |
| `narrative_generator.py` | `models/density.py` | DensityLevel drives narrative length and max_tokens | VERIFIED | DensityLevel imported and used in token calculation |
| `financial.html.j2` | context dict (yoy_change values) | financial_row calls need yoy_change argument | NOT WIRED | Template calls financial_row with direction but no yoy_change; context builder does not provide these values |

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|--------------|-------------|--------|----------|
| CORE-04 | 01, 02, 07 | 7-stage pipeline: RESOLVE→ACQUIRE→EXTRACT→ANALYZE→SCORE→BENCHMARK→RENDER | SATISFIED | `PIPELINE_STAGES` has exactly 7 stages confirmed by live import; test_pipeline_stages_count passes |
| DATA-12 | 06 | Missing data shows "Not Available — [reason]" | SATISFIED | HTML gap_notice macro provides field_name + reason format; existing na_if_none for Word is pre-phase behavior |
| DATA-14 | 03, 06 | LLM analysis labeled "AI Assessment" | SATISFIED | narrative_generator.py prefixes all LLM output with "AI Assessment: "; Word renderer adds "[AI Assessment]" italic prefix |
| OUT-01 | 06 | Word document primary output | SATISFIED | word_renderer.py functional; density indicators and pre-computed narratives added |
| OUT-02 | 05, 07 | PDF and Markdown secondary formats from same AnalysisState | SATISFIED | html_renderer.py produces PDF; md_renderer.py produces Markdown; both read same state; render integration tests pass |
| OUT-03 | 03, 05, 06 | Every section begins with summary paragraph | SATISFIED | All 8 HTML section templates call section_narrative(); Word renderer calls _add_section_narrative(); Markdown template has section_narrative() macros |
| OUT-04 | 05 | Every data point includes source citation | SATISFIED | financial.html.j2 line 46 renders `Source: {{ fin.filing_source }}`; gap_notice for missing data |
| VIS-01 | 05 | Stock price charts embedded | SATISFIED | market.html.j2 calls embed_chart("stock_1y") and embed_chart("stock_5y") |
| VIS-02 | 05 | Ownership breakdown chart | SATISFIED | market.html.j2 calls embed_chart("ownership") |
| VIS-03 | 05 | Litigation timeline chart | SATISFIED | litigation.html.j2 calls embed_chart("timeline") |
| VIS-04 | 04, 05 | Conditional formatting on financial tables | PARTIAL | Distress model table uses traffic_light status mapping (correct). Financial summary rows use financial_row with direction param but yoy_change never passed — YoY column always shows '--', coloring never fires |
| VIS-05 | 04 | Comprehensive visual design system | SATISFIED | Bloomberg palette in styles.css; DesignSystem html_* color constants; Tailwind custom config; comprehensive macro component library |
| SECT1-01 | 04, 05 | Company snapshot as structured header block | SATISFIED | executive.html.j2 lines 13-26 implement kv_table Company Snapshot with 2-column grid |

**Orphaned requirements check:** No requirement IDs from REQUIREMENTS.md are mapped to Phase 35 that were not claimed by plans 01-07.

### Anti-Patterns Found

| File | Detail | Severity | Impact |
|------|--------|----------|--------|
| `src/do_uw/stages/analyze/section_assessments.py` | 561 lines — 61 over project 500-line limit. Plan 01 explicitly required this file stay under 500 lines and specified splitting into `section_density_helpers.py` if too large. | Warning | Violates CLAUDE.md "No source file over 500 lines" rule. Not a functional blocker but violates explicit project architecture constraint. |
| `src/do_uw/templates/html/sections/financial.html.j2` | `financial_row` called with `direction` but no `yoy_change` — YoY column renders `--` for all rows | Warning | VIS-04 conditional formatting for YoY changes non-functional in HTML PDF output. Distress model conditional formatting (traffic_light) does work correctly. |

### Human Verification Required

#### 1. Bloomberg PDF Visual Quality

**Test:** Install Playwright (`playwright install chromium`), run pipeline on a real ticker (e.g., AAPL), open generated PDF.
**Expected:** Navy header bar, gold accents on table headers, Company Snapshot structured block in Section 1, density indicators (amber/red text) on elevated/critical sections, distress model traffic lights in financial section, AI Assessment narrative paragraphs at start of each section.
**Why human:** Visual rendering quality of Playwright-generated PDF cannot be verified programmatically. CSS Grid, Tailwind utility classes, and print styles must render correctly in headless Chromium.

#### 2. LLM Narrative Generation End-to-End

**Test:** Set `ANTHROPIC_API_KEY` and run the full pipeline with `uv run do-uw analyze AAPL`. Check output Word and PDF for "[AI Assessment]" paragraphs.
**Expected:** Pre-computed narratives appear in both Word and PDF. CLEAN sections get 2-3 sentences. CRITICAL sections get 6-8 sentences. Narratives are company-specific, cite specific data points, and maintain Bloomberg analyst tone.
**Why human:** Requires live API key and real pipeline run. Tests mock Anthropic — they verify the plumbing, not the LLM output quality.

#### 3. Word Document Density Indicators

**Test:** Run pipeline on a company with known governance issues (e.g., a company with CEO/Chair duality and low board independence). Open generated .docx file.
**Expected:** "ELEVATED CONCERN" in amber text or "CRITICAL RISK" in red text before the governance section content. "[AI Assessment]" italic prefix before narrative paragraph.
**Why human:** Word document visual rendering requires opening the .docx file; programmatic tests verify paragraph existence but not color rendering fidelity.

### Gaps Summary

Two gaps found:

**Gap 1: VIS-04 YoY Conditional Formatting in HTML (PARTIAL)**
The `financial_row` Jinja2 macro is correctly implemented with `direction` and `yoy_change` parameters and full conditional coloring CSS. However, `extract_financials()` in md_renderer_helpers.py does not compute YoY change percentages per metric, and neither `build_template_context()` nor `build_html_context()` populates `yoy_change` values in the financials dict. As a result, every `financial_row` call in financial.html.j2 uses the default `yoy_change=""` and the YoY column always renders `--`. The distress model table correctly uses traffic_light for zone classification (this is working).

Root cause: data extraction gap, not a template or macro gap. The fix is in `extract_financials()` or `build_html_context()`: compute YoY change percentage for each metric and expose it in the context dict under keys like `revenue_yoy`, `net_income_yoy`, etc.

**Gap 2: section_assessments.py Over 500-Line Limit (WARNING)**
The file is 561 lines, 61 lines over the explicit project-wide anti-pattern rule from CLAUDE.md: "No source file over 500 lines — split before it gets there." Plan 01 explicitly anticipated this and specified splitting into `section_assessments.py + section_density_helpers.py`. Plan 07 added jurisdiction classification logic (lines 473-540) without splitting.

This is not a functional gap — all tests pass and the analytical logic is correct. But it violates the project's architecture constraint designed to prevent context rot. The fix: extract `_HIGH_RISK_JURISDICTIONS`, `_classify_jurisdiction_risk()`, and `_compute_company_density()` into `section_density_helpers.py` and import them in `section_assessments.py`.

---

## Test Run Results

All test suites executed during verification:

| Test Suite | Count | Result |
|-----------|-------|--------|
| `tests/stages/analyze/test_section_assessments.py` | 32 | All passed |
| `tests/stages/benchmark/` | 82 | All passed |
| `tests/stages/render/test_html_components.py` | 33 | All passed |
| `tests/stages/render/test_html_renderer.py` | 21 | All passed |
| `tests/stages/render/test_word_density.py` | 19 | All passed |
| `tests/stages/render/test_zero_analytical_logic.py` | 7 | All passed |
| `tests/stages/render/test_render_integration.py` | 7 | All passed |
| Full render test suite | 147 | All passed |

All 15 referenced git commit hashes verified in repository log.

---

_Verified: 2026-02-21T16:00:00Z_
_Verifier: Claude (gsd-verifier)_
