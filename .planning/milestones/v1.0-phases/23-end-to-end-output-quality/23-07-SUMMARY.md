---
phase: 23-end-to-end-output-quality
plan: 07
subsystem: render
tags: [python-docx, governance, audit, litigation, board-names, fallback-messages]

# Dependency graph
requires:
  - phase: 23-02
    provides: "Improved extraction feeding render-stage data"
provides:
  - "Board name cleaning for LLM extraction artifacts"
  - "Helpful auditor fallback when extraction misses identity"
  - "Web search notice in litigation section"
  - "Filtered defense table removing N/A-only rows"
  - "Improved empty section messages with data source context"
affects: [23-08, render-stage, output-quality]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Regex-based name cleaning for LLM extraction artifacts"
    - "N/A row filtering in defense assessment tables"
    - "Data source notice pattern for blind spot transparency"

key-files:
  created: []
  modified:
    - "src/do_uw/stages/render/sections/sect5_governance.py"
    - "src/do_uw/stages/render/sections/sect3_audit.py"
    - "src/do_uw/stages/render/sections/sect6_litigation.py"
    - "src/do_uw/stages/render/sections/sect6_defense.py"
    - "tests/test_render_sections_5_7.py"

key-decisions:
  - "Board name cleaning via regex rather than NLP -- simple patterns catch Inc/Corp/LLC suffixes and role parentheticals"
  - "Auditor fallback says 'Not identified (review 10-K Item 9A)' instead of raw N/A"
  - "Defense table filters N/A rows rather than showing empty assessment grid"
  - "Blind spot notice added to litigation section rather than executive summary (closer to affected analysis)"

patterns-established:
  - "_clean_board_name: regex pipeline for stripping company names from board member fields"
  - "Data source notice pattern: check acquired_data.blind_spot_results for transparency"

# Metrics
duration: 6m 37s
completed: 2026-02-11
---

# Phase 23 Plan 07: Governance/Audit/Litigation Renderer Completeness Summary

**Board name cleaning, auditor identity fallbacks, litigation data source notice, and defense table N/A filtering across sections 3/5/6**

## Performance

- **Duration:** 6m 37s
- **Started:** 2026-02-11T22:41:21Z
- **Completed:** 2026-02-11T22:47:58Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Board names cleaned of LLM extraction artifacts (company names, role parentheticals, corporate suffixes)
- Auditor identity shows actionable fallback message instead of raw N/A
- Litigation section warns when web-based blind spot detection was not performed
- Defense assessment table filters N/A-only rows to avoid empty grids
- Empty SCA, contingent liability, and whistleblower sections show data source context
- 14 new tests added (9 board name cleaning, 2 auditor display, 3 litigation notice/fallback)

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix board name display and governance completeness** - `5022ef6` (feat)
2. **Task 2: Fix auditor display and litigation section completeness** - `f20b3ea` (feat)

## Files Created/Modified
- `src/do_uw/stages/render/sections/sect5_governance.py` - Added _clean_board_name() regex pipeline, applied to board composition, leadership, D&O context
- `src/do_uw/stages/render/sections/sect3_audit.py` - Added helpful auditor fallback when name not identified
- `src/do_uw/stages/render/sections/sect6_litigation.py` - Added web search notice, improved empty SCA message
- `src/do_uw/stages/render/sections/sect6_defense.py` - N/A row filtering, improved empty section messages
- `tests/test_render_sections_5_7.py` - 14 new tests for all changes

## Decisions Made
- Board name cleaning uses regex rather than NLP: company name patterns (Inc., Corp., LLC, Ltd.) are deterministic and LLM artifacts follow consistent patterns
- Auditor fallback directs user to "review 10-K Item 9A" rather than just "N/A" -- actionable for underwriters
- Web search notice placed in litigation section (closest to affected analysis) rather than executive summary
- Defense table filters N/A rows rather than showing a grid of empty assessments -- more professional output

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Render stage now handles all identified completeness issues
- Board name cleaning pattern available for reuse in other sections
- Data source notice pattern established for blind spot transparency
- All 192 render tests pass with no regressions

---
*Phase: 23-end-to-end-output-quality*
*Completed: 2026-02-11*
