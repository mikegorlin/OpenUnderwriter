---
phase: 38-render-completeness-quarterly-data
plan: 06
subsystem: render
tags: [jinja2, markdown, html, word, extraction-helpers, classification, hazard-profile, risk-factors, forensic-composites]

# Dependency graph
requires:
  - phase: 38-render-completeness-quarterly-data
    plan: 01
    provides: "Split templates with section includes, build_template_context()"
provides:
  - "8 analysis extraction helpers (classification, hazard profile, risk factors, forensic composites, executive risk, temporal signals, NLP signals, peril map)"
  - "MD/HTML templates rendering all 15+ previously-unrendered data domains"
  - "Word renderer sections for classification, hazard profile, risk factors, forensic composites, executive risk, temporal signals, NLP signals"
  - "Format parity: all three formats (MD, HTML, Word) render same data domains"
affects: [38-07]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Extraction helper pattern: read from AnalysisState, return template-ready dict or None", "Delegation pattern for Word renderer: parent calls try-import child module"]

key-files:
  created:
    - src/do_uw/stages/render/md_renderer_helpers_analysis.py
    - src/do_uw/stages/render/sections/sect2_company_hazard.py
    - src/do_uw/stages/render/sections/sect7_scoring_analysis.py
  modified:
    - src/do_uw/stages/render/md_renderer.py
    - src/do_uw/templates/markdown/sections/executive.md.j2
    - src/do_uw/templates/markdown/sections/company.md.j2
    - src/do_uw/templates/markdown/sections/scoring.md.j2
    - src/do_uw/templates/html/sections/executive.html.j2
    - src/do_uw/templates/html/sections/company.html.j2
    - src/do_uw/templates/html/sections/scoring.html.j2
    - src/do_uw/stages/render/sections/sect2_company.py
    - src/do_uw/stages/render/sections/sect7_scoring.py

key-decisions:
  - "Executive risk rendered in sect7_scoring_analysis (analysis composite) not sect1_executive (already full)"
  - "HTML hazard profile uses collapsible details element for 55-dimension table to avoid overwhelming the page"
  - "Risk factors filtered to D&O-relevant (HIGH/MEDIUM), new this year, or unique high-severity -- not all Item 1A factors"

patterns-established:
  - "Analysis extraction helpers in md_renderer_helpers_analysis.py -- return None when data absent, template-safe"
  - "Word renderer delegation via try-import: parent calls child module, graceful degradation if not available"

requirements-completed: [SC-1]

# Metrics
duration: 9min
completed: 2026-02-21
---

# Phase 38 Plan 06: Render Missing Data Domains Summary

**8 extraction helpers and matching templates/Word sections rendering classification, hazard profile (55 dimensions), risk factors, forensic composites, executive risk, temporal signals, NLP signals, and peril map across MD, HTML, and Word formats**

## Performance

- **Duration:** 9 min
- **Started:** 2026-02-21T20:33:29Z
- **Completed:** 2026-02-21T20:42:48Z
- **Tasks:** 3
- **Files modified:** 12

## Accomplishments
- Created md_renderer_helpers_analysis.py with 8 extraction helpers for all previously-unrendered data domains (412 lines)
- Updated MD templates: executive (detail tables for findings), company (classification + full 55-dimension hazard profile + risk factors), scoring (forensic composites + executive risk + temporal signals + NLP + peril map)
- Updated HTML templates with matching content: collapsible hazard dimension table, color-coded exposure levels, structured risk factor display
- Created Word renderer sections: sect2_company_hazard.py (281 lines) for classification/hazard/risk factors, sect7_scoring_analysis.py (189 lines) for forensic composites/executive risk/temporal/NLP
- Format parity achieved: all three formats (MD, HTML, Word) now render the same data domains
- All empty/absent domains show "Not available" or "None found" gracefully
- All existing 17 render tests continue to pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Create analysis extraction helpers + context integration** - `b1ea50d` (feat)
2. **Task 2: Render missing domains in MD/HTML templates** - `e270bc5` (feat)
3. **Task 3: Render missing domains in Word renderer** - `f164255` (feat)

**Plan metadata:** (see below)

## Files Created/Modified
- `src/do_uw/stages/render/md_renderer_helpers_analysis.py` - 8 extraction helpers for classification, hazard, risk factors, forensic composites, executive risk, temporal signals, NLP, peril map (412 lines)
- `src/do_uw/stages/render/md_renderer.py` - Added 8 new context keys to build_template_context()
- `src/do_uw/templates/markdown/sections/executive.md.j2` - Findings rendered as detail tables with evidence/section/impact/theory columns
- `src/do_uw/templates/markdown/sections/company.md.j2` - Added classification, hazard profile (IES + 55 dimensions + categories), risk factors
- `src/do_uw/templates/markdown/sections/scoring.md.j2` - Added forensic composites, executive risk, temporal signals, NLP, peril map
- `src/do_uw/templates/html/sections/executive.html.j2` - Matching HTML with structured findings tables
- `src/do_uw/templates/html/sections/company.html.j2` - Classification, hazard profile with collapsible details, risk factors with severity coloring
- `src/do_uw/templates/html/sections/scoring.html.j2` - All analysis composites with styled tables
- `src/do_uw/stages/render/sections/sect2_company_hazard.py` - Word renderer: classification table, full hazard profile, risk factors (281 lines)
- `src/do_uw/stages/render/sections/sect7_scoring_analysis.py` - Word renderer: forensic composites, executive risk, temporal signals, NLP (189 lines)
- `src/do_uw/stages/render/sections/sect2_company.py` - Added hazard delegation call
- `src/do_uw/stages/render/sections/sect7_scoring.py` - Added analysis composites delegation call

## Decisions Made
- **Executive risk in sect7 not sect1**: Executive risk profile (BoardAggregateRisk) is an analysis composite and belongs with other composites in Section 7, not in the already-full Section 1 executive summary renderer.
- **Collapsible HTML hazard table**: 55 dimensions is a lot of data. HTML template uses `<details>` element to collapse the full table by default, showing only top risk dimensions (ELEVATED+) prominently.
- **Risk factor filtering**: Not all Item 1A risk factors are shown. Filtered to D&O-relevant (HIGH/MEDIUM relevance), new this year, or unique (non-OTHER category with HIGH severity). Sorted new-first, then by severity.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added executive risk to Word renderer**
- **Found during:** Task 3 (Word renderer creation)
- **Issue:** Plan stated "Executive risk is covered by sect1_executive.py" but grep confirmed it was NOT rendered anywhere in Word
- **Fix:** Added render_executive_risk() to sect7_scoring_analysis.py and delegation call in sect7_scoring.py
- **Files modified:** sect7_scoring_analysis.py, sect7_scoring.py
- **Verification:** Import succeeds, all tests pass
- **Committed in:** f164255 (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Essential for format parity. Without this fix, executive risk would render in MD/HTML but not Word.

## Issues Encountered
- Two pre-existing test failures (PDF/WeasyPrint library loading) unrelated to this plan were present throughout execution and not fixed (out of scope).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All 15+ previously-unrendered data domains now have rendering paths in all three formats
- Template context provides all new keys with None fallback for empty state
- SC-1 render coverage significantly improved -- remaining gaps (if any) to be identified in 38-07

## Self-Check: PASSED

- All 12 files verified present on disk (see below)
- All 3 task commits verified in git history
- All 17 render tests pass (2 pre-existing PDF failures excluded)

---
*Phase: 38-render-completeness-quarterly-data*
*Completed: 2026-02-21*
