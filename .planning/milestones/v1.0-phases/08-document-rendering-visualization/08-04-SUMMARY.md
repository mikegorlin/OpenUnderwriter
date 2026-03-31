---
phase: 08-document-rendering-visualization
plan: 04
subsystem: render
tags: [jinja2, weasyprint, pdf, markdown, meeting-prep, docx, liberty-mutual, templates]

# Dependency graph
requires:
  - phase: 08-02
    provides: Section renderers 1-4 (exec summary, company profile, financial, market)
  - phase: 08-03
    provides: Section renderers 5-7 (governance, litigation, scoring) with charts
provides:
  - Meeting prep companion appendix with 4-category priority-ranked questions
  - Markdown renderer via Jinja2 templates
  - PDF renderer via WeasyPrint (optional, graceful degradation)
  - Three-format output from single AnalysisState (Word + Markdown + PDF)
affects: [08-05, phase-9]

# Tech tracking
tech-stack:
  added: [jinja2 (templates)]
  patterns:
    - "Secondary renderer pattern: try/except wrapper prevents PDF/Markdown failures from crashing pipeline"
    - "Template context reuse: build_template_context() shared between Markdown and PDF renderers"
    - "Lazy import for optional dependency: WeasyPrint imported inside function with try/except ImportError"
    - "500-line split: meeting_questions.py split into meeting_questions.py (278L) + meeting_questions_gap.py (325L)"

key-files:
  created:
    - src/do_uw/stages/render/sections/meeting_prep.py
    - src/do_uw/stages/render/sections/meeting_questions.py
    - src/do_uw/stages/render/sections/meeting_questions_gap.py
    - src/do_uw/stages/render/md_renderer.py
    - src/do_uw/stages/render/pdf_renderer.py
    - src/do_uw/templates/markdown/worksheet.md.j2
    - src/do_uw/templates/pdf/worksheet.html.j2
    - src/do_uw/templates/pdf/styles.css
    - tests/test_render_outputs.py
  modified:
    - src/do_uw/stages/render/__init__.py
    - src/do_uw/stages/render/sections/__init__.py
    - tests/test_render_framework.py

key-decisions:
  - "Split meeting_questions.py (556L) into two files: meeting_questions.py (278L, clarification + forward indicators) and meeting_questions_gap.py (325L, gap fillers + credibility tests)"
  - "Public build_template_context() in md_renderer.py reused by pdf_renderer.py to avoid duplicating state extraction logic"
  - "Non-fatal secondary renderer pattern: _render_secondary() wraps PDF/Markdown with try/except so pipeline completes even if secondary formats fail"
  - "Jinja2 autoescape=False for Markdown renderer (noqa S701) since output is Markdown not HTML"
  - "Liberty Mutual CSS: @page margins, navy headers, no green in risk spectrum, Georgia/Calibri fonts"

patterns-established:
  - "Template context builder: extract AnalysisState into simple dicts for Jinja2 rendering"
  - "Optional dependency lazy import: try/except ImportError inside function body"
  - "FinancialLineItem traversal: _find_line_item_value() searches list by label string"

# Metrics
duration: 31min
completed: 2026-02-09
---

# Phase 8, Plan 4: Meeting Prep Appendix & Multi-Format Output Summary

**Meeting prep appendix with 4-category priority-ranked questions, Markdown renderer via Jinja2, PDF renderer via WeasyPrint (optional), three-format output from single AnalysisState**

## Performance

- **Duration:** 31 min
- **Started:** 2026-02-09T01:15:45Z
- **Completed:** 2026-02-09T01:46:24Z
- **Tasks:** 2
- **Files modified:** 15
- **Tests:** 1090 (was 1071, added 19 new)

## Accomplishments
- Meeting prep companion appendix generates priority-ranked questions by scanning AnalysisState for LOW confidence data, missing fields, trend signals, and narrative coherence mismatches
- Markdown output rendered via Jinja2 templates with all 7 sections plus meeting prep appendix
- PDF output via WeasyPrint with Liberty Mutual themed HTML/CSS (gracefully skipped when WeasyPrint not installed)
- RenderStage now produces Word (always), Markdown (always), and PDF (optional) from same AnalysisState
- Split meeting_questions.py from 556 lines into two files under 500 lines each

## Task Commits

Each task was committed atomically:

1. **Task 1: Meeting prep companion appendix** - `2aa5bc1` (feat)
2. **Task 2: PDF renderer, Markdown renderer, pipeline/CLI test updates** - `55076c8` (feat)

**Plan metadata:** (pending)

## Files Created/Modified
- `src/do_uw/stages/render/sections/meeting_prep.py` (171L) - Word document appendix renderer with priority-ranked questions
- `src/do_uw/stages/render/sections/meeting_questions.py` (278L) - MeetingQuestion dataclass, clarification and forward indicator generators
- `src/do_uw/stages/render/sections/meeting_questions_gap.py` (325L) - Gap filler and credibility test question generators
- `src/do_uw/stages/render/md_renderer.py` (377L) - Markdown renderer with Jinja2 templates and shared context builder
- `src/do_uw/stages/render/pdf_renderer.py` (143L) - PDF renderer with WeasyPrint (optional dependency)
- `src/do_uw/templates/markdown/worksheet.md.j2` (234L) - Jinja2 Markdown template for full worksheet
- `src/do_uw/templates/pdf/worksheet.html.j2` (175L) - HTML template for WeasyPrint PDF rendering
- `src/do_uw/templates/pdf/styles.css` (197L) - Liberty Mutual themed CSS with navy/gold/risk spectrum
- `tests/test_render_outputs.py` (369L) - 19 tests for Markdown, PDF, meeting questions, integration
- `src/do_uw/stages/render/__init__.py` (122L) - RenderStage updated to call all three renderers
- `src/do_uw/stages/render/sections/__init__.py` - Added meeting_prep export
- `tests/test_render_framework.py` - Updated assertion for completed meeting prep section

## Decisions Made
- Split meeting_questions.py (556 lines) into meeting_questions.py (278L) + meeting_questions_gap.py (325L) for 500-line compliance
- Public `build_template_context()` in md_renderer.py reused by pdf_renderer.py (DRY state extraction)
- Non-fatal `_render_secondary()` wrapper prevents PDF/Markdown failures from crashing the pipeline
- Jinja2 `autoescape=False` for Markdown renderer (S701 noqa -- Markdown output, not HTML)
- Liberty Mutual CSS: `@page` margins, navy header backgrounds, no green in risk spectrum, Georgia/Calibri fonts
- `_find_line_item_value()` helper for FinancialLineItem list traversal (list[FinancialLineItem], not dict)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed 70+ pyright strict errors in md_renderer.py**
- **Found during:** Task 2 (Markdown renderer)
- **Issue:** Initial implementation used wrong field names from AnalysisState models (ExecutiveSummary has no tier_label, FinancialStatement.line_items is list not dict, FactorScore has points_deducted not raw_score, etc.)
- **Fix:** Verified all model field names via Python introspection, rewrote all extractors with correct field paths
- **Files modified:** src/do_uw/stages/render/md_renderer.py
- **Verification:** pyright strict 0 errors
- **Committed in:** 55076c8

**2. [Rule 3 - Blocking] Split meeting_questions.py over 500-line limit**
- **Found during:** Task 1 (Meeting prep)
- **Issue:** meeting_questions.py reached 556 lines, exceeding the 500-line anti-context-rot rule
- **Fix:** Split into meeting_questions.py (278L, clarification + forward generators) and meeting_questions_gap.py (325L, gap + credibility generators)
- **Files modified:** meeting_questions.py, meeting_questions_gap.py (new), meeting_prep.py (updated imports)
- **Verification:** Both files under 500 lines, all imports resolve, tests pass
- **Committed in:** 2aa5bc1

**3. [Rule 1 - Bug] Fixed test assertion for completed meeting prep section**
- **Found during:** Task 2 (test updates)
- **Issue:** test_render_framework.py asserted "To be implemented" but all sections now render actual content
- **Fix:** Changed assertion to check for "Meeting Prep Companion" section presence
- **Files modified:** tests/test_render_framework.py
- **Verification:** Test passes
- **Committed in:** 55076c8

---

**Total deviations:** 3 auto-fixed (2 bugs, 1 blocking)
**Impact on plan:** All auto-fixes necessary for correctness and compliance. No scope creep.

## Issues Encountered
- Ruff F541 f-string without placeholders in meeting_questions_gap.py: embedded f-string inside another f-string had no actual interpolation. Fixed by restructuring the string concatenation.
- Gap filler test expected 0 questions for empty state, but `_check_litigation_gaps` fires when extracted is None (missing litigation data IS a gap). Updated test to expect 1 question.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- RENDER stage functionally complete: Word (always), Markdown (always), PDF (optional)
- One plan remains (08-05): final integration, end-to-end testing, pipeline wiring
- All 7 worksheet sections render with charts
- Meeting prep appendix generates data-driven questions
- 1090 tests passing, pyright strict clean, all files under 500 lines

---
*Phase: 08-document-rendering-visualization*
*Completed: 2026-02-09*
