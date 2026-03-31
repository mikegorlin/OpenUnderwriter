---
phase: 38-render-completeness-quarterly-data
verified: 2026-02-21T22:00:00Z
status: gaps_found
score: 6/7 success criteria verified
gaps:
  - truth: "Quarterly data uses YTD comparison: 6-month YTD for Q2, 9-month YTD for Q3, against same YTD period from prior year"
    status: partial
    reason: "The QuarterlyUpdate model has prior_year_revenue / prior_year_net_income / prior_year_eps fields, and renderers handle them gracefully (showing 'N/A' when None). But the extraction layer (quarterly_integration.py line 198-200) hard-codes all three fields to None with a 'Future: parse 10-Q comparison tables' comment. No code ever populates these fields. Renderers display 'N/A' for all prior-year columns — the comparison column is structurally present but always empty."
    artifacts:
      - path: "src/do_uw/stages/extract/quarterly_integration.py"
        issue: "prior_year_revenue=None, prior_year_net_income=None, prior_year_eps=None hardcoded (lines 198-200)"
    missing:
      - "Extract prior-year YTD figures from the 10-Q comparison table (the filing itself includes current YTD and same-period prior year columns in the income statement)"
      - "OR: look up same-quarter filing from prior year in llm_extractions and use its revenue/NI/EPS as the comparison value"
      - "Until one of the above is implemented, SC-3 is structurally partial — the section renders but comparison data is always N/A"
human_verification:
  - test: "Run pipeline on a company with a recent 10-Q filed after the 10-K and confirm 'Recent Quarterly Update' section appears"
    expected: "Section appears with revenue, net income, EPS for the quarter; prior-year row shows N/A (expected until SC-3 extraction is added)"
    why_human: "Requires live pipeline execution with a real filing — test fixture uses mock data, not actual acquired documents"
---

# Phase 38: Render Completeness & Quarterly Data Verification Report

**Phase Goal:** Every field the brain acquires and populates in state.json appears in the rendered output. No silent data drops. Quarterly results (10-Q) after the most recent annual (10-K) are extracted and shown as a separate "Recent Quarterly Update" section in financials. The Word, Markdown, and PDF outputs are consistent — same data, same structure.
**Verified:** 2026-02-21T22:00:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (from Phase Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Automated render coverage test exceeds 90% | VERIFIED | 95.7% MD / 91.3% Word / 93.5% HTML — all 4 TestMultiFormatCoverage tests pass |
| 2 | "Recent Quarterly Update" subsection renders Q-over-Q revenue, net income, EPS, material changes | VERIFIED | Section renders in MD/Word/HTML when data present; template confirmed at financial.md.j2:93-122 |
| 3 | Quarterly data uses YTD comparison (6-month Q2, 9-month Q3 vs prior year) | PARTIAL | Model has prior_year fields; renderers use them; but extraction always sets them to None — no actual prior-year data is ever populated |
| 4 | All litigation matters rendered with full detail | VERIFIED | Derivative suits (allegations, court, status, settlement), contingent liabilities, WPE, whistleblower all render in MD/Word/HTML |
| 5 | Board forensic profiles complete (interlocks, tenure, committees) | VERIFIED | Per-member profiles with committees, interlocks, relationship_flags, independence_concerns, overboarded status confirmed in governance.md.j2 and md_renderer_helpers_governance.py |
| 6 | Financial statements complete (all three with all line items) | VERIFIED | Full income/balance sheet/cash flow tables with _build_statement_rows() iterating all line items in MD and HTML |
| 7 | Cross-format consistency test verifies Word, Markdown, PDF same structure | VERIFIED | 4/4 cross-format tests pass; PDF coverage via HTML uses same build_template_context() as MD |

**Score:** 6/7 truths verified (SC-3 partial)

---

## Required Artifacts

### Plan 01 — Template Split + Data Flow Fix

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/templates/markdown/sections/executive.md.j2` | Executive summary section template | VERIFIED | Exists, 71 lines, referenced in worksheet.md.j2 |
| `src/do_uw/templates/markdown/sections/company.md.j2` | Company profile section template | VERIFIED | Exists, 128 lines (after 38-06 additions) |
| `src/do_uw/templates/markdown/sections/financial.md.j2` | Financial section template | VERIFIED | Exists, 172 lines (after 38-04 additions) |
| `src/do_uw/templates/markdown/sections/governance.md.j2` | Governance section template | VERIFIED | Exists, 98 lines (after 38-05 additions) |
| `src/do_uw/templates/markdown/sections/litigation.md.j2` | Litigation section template | VERIFIED | Exists, 113 lines (after 38-05 additions) |
| `src/do_uw/templates/markdown/sections/scoring.md.j2` | Scoring section template | VERIFIED | Exists, 145 lines (after 38-06 additions) |
| `src/do_uw/templates/markdown/sections/market.md.j2` | Market section template | VERIFIED | Exists, 61 lines |
| `src/do_uw/templates/markdown/sections/appendix.md.j2` | Appendix section template | VERIFIED | Exists, 76 lines |
| `src/do_uw/templates/markdown/worksheet.md.j2` | Root template with include directives | VERIFIED | Exists, 64 lines; 8 `{% include 'sections/*.md.j2' %}` directives confirmed |

### Plan 02 — Render Coverage Test Framework

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/stages/render/coverage.py` | State field walker and format-aware matcher | VERIFIED | Exists, 389 lines; walk_state_values, check_value_rendered, compute_coverage all implemented |
| `tests/test_render_coverage.py` | Parametrized render coverage test | VERIFIED | Exists, 757 lines; 39 tests (35 unit + 4 multi-format coverage) — all pass |

### Plan 03 — Quarterly Data Model + Extraction

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/models/financials.py` | QuarterlyUpdate model | VERIFIED | Class QuarterlyUpdate exists at line 296; quarterly_updates field on ExtractedFinancials confirmed |
| `src/do_uw/stages/extract/quarterly_integration.py` | aggregate_quarterly_updates() function | VERIFIED | Exists, wired into extract/__init__.py as Phase 8b; 15 integration tests all pass |
| `tests/test_quarterly_integration.py` | Tests for quarterly data aggregation | VERIFIED | Exists; 15 tests across 7 classes — all pass |

### Plan 04 — Financial Statement Tables + Quarterly Rendering

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/stages/render/sections/sect3_quarterly.py` | Quarterly update Word renderer | VERIFIED | Exists, 122 lines; imported and called in sect3_financial.py |
| `src/do_uw/templates/html/sections/financial.html.j2` | Full statements + quarterly in HTML | VERIFIED | Exists, 327 lines (from summary) |
| `src/do_uw/stages/render/md_renderer_helpers_financial.py` | _build_statement_rows + _build_quarterly_context | VERIFIED | Both functions confirmed at lines 242 and 322; wired in extract_financials() |

### Plan 05 — Governance Forensics + Complete Litigation

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/stages/render/md_renderer_helpers_governance.py` | extract_governance() split out | VERIFIED | Exists, 258 lines; committees, interlocks, relationship_flags, independence_concerns all extracted |
| `src/do_uw/stages/render/md_renderer_helpers_ext.py` | Updated with derivative/contingent/WPE/whistleblower | VERIFIED | 420 lines; _extract_derivative_suits, _extract_contingent_liabilities, _extract_workforce_product_env, _extract_whistleblower_indicators all present |
| `src/do_uw/templates/markdown/sections/governance.md.j2` | Full board forensic profiles | VERIFIED | Committees, interlocks, relationship_flags, independence_concerns confirmed at lines 39-54 |
| `src/do_uw/templates/markdown/sections/litigation.md.j2` | All litigation matter types | VERIFIED | Derivative suits (with allegations), contingent liabilities, WPE, whistleblower confirmed at lines 21-80 |
| `src/do_uw/stages/render/sections/sect6_defense.py` | WPE + contingent + whistleblower in Word | VERIFIED | _render_contingent_liabilities, _render_whistleblower_indicators, _render_workforce_product_env confirmed |
| `src/do_uw/stages/render/sections/sect6_timeline.py` | Derivative suits in Word | VERIFIED | _render_derivative_suits confirmed at lines 37-85; iterates all suits with case_name, filing_date, status, court, settlement |

### Plan 06 — Missing Data Domains

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/stages/render/md_renderer_helpers_analysis.py` | 8 extraction helpers | VERIFIED | Exists, 412 lines; all 8 helpers confirmed via import check in md_renderer.py |
| `src/do_uw/stages/render/sections/sect2_company_hazard.py` | Hazard/classification/risk factors in Word | VERIFIED | Exists, 281 lines; called from sect2_company.py lines 363-369 |
| `src/do_uw/stages/render/sections/sect7_scoring_analysis.py` | Forensic composites/executive risk/temporal/NLP in Word | VERIFIED | Exists, 189 lines; called from sect7_scoring.py lines 469-477 |
| `src/do_uw/templates/markdown/sections/company.md.j2` | Classification + hazard (all 55 dims) + risk factors | VERIFIED | classification, hazard_profile (IES, 55 dimensions, categories), risk_factors confirmed at lines 24-100 |
| `src/do_uw/templates/markdown/sections/scoring.md.j2` | Forensic composites, executive risk, temporal, NLP, peril map | VERIFIED | All 5 domains confirmed at lines 69-139 |

### Plan 07 — Cross-Format Consistency + Final Coverage

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tests/test_cross_format_consistency.py` | Cross-format section and data verification | VERIFIED | Exists, 414 lines; SECTION_REGISTRY with 8 canonical sections; 4/4 tests pass |
| `tests/test_render_coverage.py` | Updated with >90% threshold | VERIFIED | 4 multi-format coverage tests added; assert coverage_pct > 90 at lines 679, 706, 728; all pass |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `worksheet.md.j2` | `sections/*.md.j2` | `{% include 'sections/...' %}` | WIRED | 8 include directives confirmed |
| `md_renderer.py` | `md_renderer_helpers_analysis.py` | `extract_classification, extract_hazard_profile, extract_risk_factors` + 5 more | WIRED | All 8 imports + assignments to context at lines 142-149 |
| `financial.md.j2` | `md_renderer_helpers_financial.py` | `financials.quarterly_updates`, `income_statement_rows`, `balance_sheet_rows`, `cash_flow_rows` | WIRED | Template keys confirmed match context dict keys |
| `tests/test_render_coverage.py` | `coverage.py` | `from do_uw.stages.render.coverage import compute_coverage` | WIRED | Import confirmed; all 4 threshold assertions call compute_coverage |
| `tests/test_cross_format_consistency.py` | `md_renderer.py` + `word_renderer.py` | `render_markdown`, `render_word_document` | WIRED | Confirmed in test fixture fixtures and test methods |
| `sect3_financial.py` | `sect3_quarterly.py` | `render_quarterly_update` | WIRED | Import at line 35; call at line 63 |
| `extract/__init__.py` | `quarterly_integration.py` | `aggregate_quarterly_updates` | WIRED | Phase 8b insertion confirmed at lines 195-201 |
| `sect2_company.py` | `sect2_company_hazard.py` | `render_classification, render_hazard_profile, render_risk_factors` | WIRED | Confirmed at lines 363-369 |
| `sect7_scoring.py` | `sect7_scoring_analysis.py` | `render_forensic_composites, render_executive_risk, render_temporal_signals, render_nlp_signals` | WIRED | Confirmed at lines 469-477 |
| `html_renderer.py` | `md_renderer.build_template_context` | `from do_uw.stages.render.md_renderer import build_template_context` | WIRED | HTML/PDF uses identical context as MD — architectural parity confirmed |
| `quarterly_integration.py` | `prior_year_revenue/net_income/eps` | NEVER POPULATED | NOT_WIRED | All three set to `None` hardcoded; no extraction path exists |

---

## Requirements Coverage

SC-1 through SC-7 are Phase 38 Success Criteria IDs (not global REQUIREMENTS.md IDs). They map 1:1 to the 7 success criteria in ROADMAP.md Phase 38 entry.

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| SC-1 | 38-01, 38-02, 38-06, 38-07 | Automated render coverage test >90% | SATISFIED | 95.7% MD, 91.3% Word, 93.5% HTML — all 4 multi-format tests pass |
| SC-2 | 38-03, 38-04 | "Recent Quarterly Update" subsection renders Q-over-Q revenue, NI, EPS, material changes | SATISFIED | Section renders in all 3 formats; template confirmed; Word via sect3_quarterly.py |
| SC-3 | 38-03, 38-04 | Quarterly data uses YTD comparison (6-month Q2, 9-month Q3 vs prior year) | BLOCKED | prior_year_revenue/net_income/eps fields always None — hardcoded in quarterly_integration.py:198-200; prior-year comparison never populated |
| SC-4 | 38-05 | All litigation matters with full detail (derivative suits, not just count) | SATISFIED | Derivative suits render with case_name, filing_date, court, status, allegations, settlement in MD and Word |
| SC-5 | 38-05 | Board forensics: individual profiles with interlocks, tenure, committees | SATISFIED | Per-member forensic cards with committees, interlocks, relationship_flags, independence_concerns confirmed in template and helper |
| SC-6 | 38-04 | All three financial statements with all available line items | SATISFIED | _build_statement_rows() iterates all line_items; full tables in MD and HTML |
| SC-7 | 38-01, 38-07 | Test verifies Word, Markdown, PDF share section headings and key data | SATISFIED | 4/4 cross-format tests pass; SECTION_REGISTRY covers 8 canonical sections; PDF=HTML by architecture (same build_template_context) |

Note: SC-1 through SC-7 do not appear in `.planning/REQUIREMENTS.md` (which uses REQ-ID format like CORE-01, DATA-01). They are phase-internal success criteria defined in ROADMAP.md Phase 38 entry. No orphaned requirements found.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/do_uw/stages/extract/quarterly_integration.py` | 198-200 | `prior_year_revenue=None, # Future: parse 10-Q comparison tables` | Blocker | SC-3 prior-year YTD comparison never populated; "Prior Year" column in quarterly update always shows "N/A" |

### Pre-Existing Test Failures (not introduced by Phase 38)

Three test failures exist in the render test suite but are confirmed pre-existing (not caused by Phase 38):

1. `tests/test_render_outputs.py::TestPdfRenderer::test_render_pdf_returns_none_without_weasyprint` — WeasyPrint library (`libgobject-2.0-0`) not installed on this machine. Pre-existing since Phase 8 (last commit touching this test: `55076c8`).
2. `tests/test_render_outputs.py::TestRenderStageIntegration::test_render_stage_calls_all_renderers` — Expects `render_pdf` to be called; fails because WeasyPrint is unavailable. Same root cause.
3. `tests/stages/render/test_stock_charts.py::TestTemplateChartEmbedding::test_md_template_embeds_chart_images` — Chart image embedding test; pre-existing from Phase 37 chart work.

None of these were introduced by Phase 38. All Phase 38 tests (43/43) pass.

---

## Human Verification Required

### 1. Live Pipeline Quarterly Update

**Test:** Run `do-uw analyze <TICKER>` on a company that filed a 10-Q after its most recent 10-K. Confirm the "Recent Quarterly Update" section appears in the rendered output.
**Expected:** Section header `### Recent Quarterly Update (Q1 FY2026, filed 2026-01-30)` with revenue, net income, EPS for the quarter. Prior Year column shows "N/A" (expected — SC-3 extraction gap).
**Why human:** Requires live pipeline with real SEC filings; test fixtures use mock data that bypasses the acquisition layer.

---

## Gaps Summary

**One gap blocks goal achievement:**

**SC-3: Prior-year YTD comparison data is not extracted.** The QuarterlyUpdate model has `prior_year_revenue`, `prior_year_net_income`, and `prior_year_eps` fields. Renderers check for them and display "N/A" when None. But the extraction function (`aggregate_quarterly_updates()`) hardcodes all three to `None` with a comment `# Future: parse 10-Q comparison tables`. No extraction path exists that would ever populate them.

The SC-3 success criterion states: "6-month YTD for Q2, 9-month YTD for Q3, against same YTD period from prior year." The rendered quarterly section has a "Prior Year | Change" table structure, but that column is always "N/A" in production runs.

**Root cause options for a fix plan:**
1. Parse the 10-Q income statement comparison table (10-Qs always include the same period from prior year as a comparison column)
2. Look up the same-quarter filing from the prior year in `llm_extractions` and use its revenue/NI/EPS values
3. Extend the TenQExtraction LLM schema to capture `prior_year_revenue`, `prior_year_net_income`, `prior_year_eps` directly from the 10-Q document (the filing contains these numbers explicitly)

The remainder of the quarterly rendering is complete: the subsection renders, is correctly omitted when no post-annual 10-Q exists, shows material changes, new legal proceedings, going concern, material weaknesses, and subsequent events. Only the YTD comparison data is missing.

---

_Verified: 2026-02-21T22:00:00Z_
_Verifier: Claude (gsd-verifier)_
