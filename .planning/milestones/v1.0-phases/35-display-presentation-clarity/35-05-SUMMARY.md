---
phase: 35-display-presentation-clarity
plan: 05
subsystem: render, templates
tags: [html, jinja2, playwright, pdf, bloomberg, density-conditional, section-templates, coverage-appendix]

# Dependency graph
requires:
  - phase: 35-display-presentation-clarity
    provides: "base.html.j2, component macros (Plan 04); DensityLevel/narratives (Plan 01/03); content_type on CheckResult (Plan 02)"
provides:
  - "8 section HTML templates with density-conditional rendering (CLEAN/ELEVATED/CRITICAL)"
  - "2 appendix templates (meeting prep, coverage)"
  - "render_html_pdf Playwright-based PDF renderer with WeasyPrint fallback"
  - "build_html_context with densities, narratives, chart_images, check_results_by_section, coverage_stats"
  - "worksheet.html.j2 master template extending base.html.j2"
  - "RenderStage uses html_renderer as primary PDF engine"
affects: [35-06, 35-07]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Section templates use density-conditional blocks: CLEAN=tables, ELEVATED=warning_box, CRITICAL=deep-dive"
    - "Check-type display dispatch via content_type: MANAGEMENT_DISPLAY=kv, EVALUATIVE_CHECK=traffic_light, INFERENCE_PATTERN=evidence_chain"
    - "Playwright headless Chromium primary with WeasyPrint fallback chain for PDF"
    - "Jinja2 {% extends %} + {% include %} pattern for worksheet assembly"

key-files:
  created:
    - src/do_uw/templates/html/sections/executive.html.j2
    - src/do_uw/templates/html/sections/company.html.j2
    - src/do_uw/templates/html/sections/financial.html.j2
    - src/do_uw/templates/html/sections/market.html.j2
    - src/do_uw/templates/html/sections/governance.html.j2
    - src/do_uw/templates/html/sections/litigation.html.j2
    - src/do_uw/templates/html/sections/scoring.html.j2
    - src/do_uw/templates/html/sections/ai_risk.html.j2
    - src/do_uw/templates/html/appendices/meeting_prep.html.j2
    - src/do_uw/templates/html/appendices/coverage.html.j2
    - src/do_uw/templates/html/worksheet.html.j2
    - src/do_uw/stages/render/html_renderer.py
    - tests/stages/render/test_html_renderer.py
  modified:
    - src/do_uw/stages/render/__init__.py

key-decisions:
  - "Per-subsection density overrides in governance (4.1-4.4) rendered as nested density_indicator calls"
  - "Coverage appendix shows per-section coverage table with color-coded percentage (blue>=80, amber>=50, red<50)"
  - "Jinja2 undefined=Undefined (tolerant) rather than StrictUndefined for graceful handling of missing context"
  - "Blind spot discovery status accessed from state.acquired_data.blind_spot_results (AcquiredData, not AnalysisResults)"
  - "Master worksheet.html.j2 uses extends/include pattern for clean section composition"

patterns-established:
  - "Section template pattern: get density -> density_indicator -> section_narrative -> content tables -> check results -> ELEVATED warnings -> CRITICAL deep dive"
  - "Coverage appendix pattern: overall stats grid -> per-section table -> gap notices -> blind spot status -> data sources"

requirements-completed: [OUT-02, OUT-03, OUT-04, VIS-01, VIS-02, VIS-03, VIS-04, SECT1-01]

# Metrics
duration: 9min
completed: 2026-02-21
---

# Phase 35 Plan 05: HTML Section Templates & Playwright PDF Renderer Summary

**10 Jinja2 section/appendix templates with density-conditional rendering, Playwright headless Chromium PDF generation with WeasyPrint fallback, and RenderStage integration**

## Performance

- **Duration:** 9 min
- **Started:** 2026-02-21T15:09:32Z
- **Completed:** 2026-02-21T15:18:30Z
- **Tasks:** 3
- **Files modified:** 14

## Accomplishments
- Created 8 section templates (executive, company, financial, market, governance, litigation, scoring, ai_risk) each with density-conditional rendering, pre-computed narratives, check-type display dispatch, and CRITICAL deep-dive blocks
- Created 2 appendix templates: meeting prep (LLM questions + section-linked questions) and coverage (per-section check stats, gap notices, blind spot discovery status)
- Built html_renderer.py (373 lines) with Playwright PDF generation, WeasyPrint fallback, check grouping by section prefix, and coverage statistics computation
- Integrated render_html_pdf into RenderStage as primary PDF renderer, replacing direct WeasyPrint call
- 21 new tests covering context building, template rendering, check grouping, coverage stats, and fallback behavior
- All 133 existing render tests pass with no regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Create core section HTML templates (executive, company, financial, market, governance)** - `1ee00b1` (feat)
2. **Task 2: Create remaining section templates, appendices, and verify macro usage** - `168a923` (feat)
3. **Task 3: Build Playwright HTML-to-PDF renderer and integrate into RenderStage** - `d872871` (feat)

## Files Created/Modified
- `src/do_uw/templates/html/sections/executive.html.j2` - Company Snapshot grid (SECT1-01), tier badge, thesis narrative, key findings, claim probability (136 lines)
- `src/do_uw/templates/html/sections/company.html.j2` - Identity KV table, D&O exposure factors, revenue segments, geographic footprint (122 lines)
- `src/do_uw/templates/html/sections/financial.html.j2` - Conditional-formatted tables (VIS-04), distress model traffic lights, audit profile, peer group (159 lines)
- `src/do_uw/templates/html/sections/market.html.j2` - Stock charts (VIS-01), ownership chart (VIS-02), short interest, earnings guidance, insider analysis (137 lines)
- `src/do_uw/templates/html/sections/governance.html.j2` - Per-subsection density overrides (4.1-4.4), board composition, compensation, activist risk (171 lines)
- `src/do_uw/templates/html/sections/litigation.html.j2` - Active matters, timeline chart (VIS-03), SEC enforcement, settlement history, CRITICAL theory mapping (152 lines)
- `src/do_uw/templates/html/sections/scoring.html.j2` - 10-factor scoring table with risk colors, red flags, severity scenarios, radar chart (155 lines)
- `src/do_uw/templates/html/sections/ai_risk.html.j2` - AI risk score, dimension breakdown, strategic assessment (85 lines)
- `src/do_uw/templates/html/appendices/meeting_prep.html.j2` - LLM questions tied to findings, section-linked questions with category badges (54 lines)
- `src/do_uw/templates/html/appendices/coverage.html.j2` - Per-section coverage table, gap notices, blind spot discovery, data sources (115 lines)
- `src/do_uw/templates/html/worksheet.html.j2` - Master template extending base.html.j2 with all 10 section includes (17 lines)
- `src/do_uw/stages/render/html_renderer.py` - Playwright PDF renderer with fallback, context builder, check grouping, coverage stats (373 lines)
- `tests/stages/render/test_html_renderer.py` - 21 tests across 6 test classes
- `src/do_uw/stages/render/__init__.py` - Updated to use render_html_pdf as primary PDF renderer

## Decisions Made
- Per-subsection density overrides in governance template use nested density_indicator calls for granular risk display within a single section
- Coverage appendix color-codes percentages: blue (>=80% evaluated), amber (50-79%), red (<50%) matching Bloomberg financial convention
- Jinja2 environment uses tolerant Undefined (not StrictUndefined) to gracefully handle missing context variables in section templates
- Blind spot discovery data lives on AcquiredData (not AnalysisResults), accessed via state.acquired_data.blind_spot_results
- Worksheet.html.j2 uses extends/include pattern rather than inlining all sections, keeping each section independently maintainable
- dim_display_name filter registered on HTML Jinja2 environment (same as PDF renderer) for AI risk dimension display

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed SourcedValue construction in test fixture**
- **Found during:** Task 3 (test creation)
- **Issue:** SourcedValue requires `as_of` datetime field; CompanyIdentity requires `ticker` field
- **Fix:** Added `as_of=datetime.now(tz=UTC)` and `ticker="TEST"` to test fixture
- **Files modified:** tests/stages/render/test_html_renderer.py
- **Verification:** All 21 tests pass
- **Committed in:** d872871

**2. [Rule 1 - Bug] Fixed blind_spot_results access path**
- **Found during:** Task 3 (html_renderer.py)
- **Issue:** blind_spot_results is on AcquiredData, not AnalysisState or AnalysisResults
- **Fix:** Changed access to `state.acquired_data.blind_spot_results`
- **Files modified:** src/do_uw/stages/render/html_renderer.py
- **Verification:** All 21 tests pass, no AttributeError
- **Committed in:** d872871

---

**Total deviations:** 2 auto-fixed (2 bugs -- model field access)
**Impact on plan:** Minor test fixture and data access corrections. No scope creep.

## Issues Encountered
- Import sort lint error on lazy Playwright import fixed via `uv run ruff check --fix`
- AnalysisResults model lives in state.py (not a separate analysis.py module) -- corrected import path

## User Setup Required
None -- Playwright is optional. Falls back to WeasyPrint, then to skip. Install Playwright for Bloomberg-quality PDF: `uv add playwright && playwright install chromium`.

## Next Phase Readiness
- All 10 HTML templates ready for Plan 06+ visual refinements
- html_renderer.py ready for end-to-end pipeline PDF generation
- Coverage appendix provides data completeness transparency
- RenderStage produces PDF via Playwright when available
- 133 total render tests pass with no regressions

## Self-Check: PASSED

All 14 created/modified files verified on disk. All 3 task commits (1ee00b1, 168a923, d872871) verified in git log. 21 new tests pass, 133 total render tests pass.

---
*Phase: 35-display-presentation-clarity*
*Completed: 2026-02-21*
