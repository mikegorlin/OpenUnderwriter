---
phase: 42-brain-risk-framework
plan: 03
subsystem: render
tags: [jinja2, html, markdown, peril-scoring, brain-framework]

# Dependency graph
requires:
  - phase: 42-01
    provides: scoring_peril_data.py with extract_peril_scoring() function, BrainDBLoader peril/chain loading
provides:
  - Peril-organized scoring data wired into HTML and Markdown template contexts
  - Peril summary table and per-peril deep dive cards in HTML scoring template
  - Peril summary table in Markdown scoring template
affects: [42-04, render, html-templates, markdown-templates]

# Tech tracking
tech-stack:
  added: []
  patterns: [lazy-import peril data into existing extract_scoring, graceful empty-data fallback in templates]

key-files:
  created: []
  modified:
    - src/do_uw/stages/render/md_renderer_helpers_scoring.py
    - src/do_uw/templates/html/sections/scoring.html.j2
    - src/do_uw/templates/markdown/sections/scoring.md.j2

key-decisions:
  - "Dynamic peril count (ps.all_perils|length) instead of hardcoded '8' for future peril additions"
  - "Explanatory footer bullets added to HTML peril section matching existing scoring template pattern"

patterns-established:
  - "Peril template graceful fallback: if peril_scoring empty or missing, no visible change to output"

requirements-completed: []

# Metrics
duration: 2min
completed: 2026-02-24
---

# Phase 42 Plan 03: HTML + Markdown Template -- Peril Sections Summary

**Peril-organized scoring wired into HTML/Markdown templates with summary table, per-peril deep dives, and graceful empty-data fallback**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-24T06:12:10Z
- **Completed:** 2026-02-24T06:14:21Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- extract_scoring() now populates peril_scoring key from brain framework via lazy import
- HTML template renders peril summary table with traffic_light risk levels and per-peril chain deep dive cards
- Markdown template renders peril summary table with bold risk levels and chain counts
- All 158 scoring-related tests pass with no regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Add peril data to extract_scoring() context** - `4905d67` (feat)
2. **Task 2: Add peril sections to HTML template** - `9716c53` (feat)
3. **Task 3: Add peril summary to Markdown template** - `91239dd` (feat)

## Files Created/Modified
- `src/do_uw/stages/render/md_renderer_helpers_scoring.py` - Added lazy import of extract_peril_scoring, populates peril_scoring key in result dict (366 lines, under 500)
- `src/do_uw/templates/html/sections/scoring.html.j2` - Added peril summary table and per-peril deep dive cards after Tier Classification (733 lines)
- `src/do_uw/templates/markdown/sections/scoring.md.j2` - Added peril summary table after Tier Classification (156 lines)

## Decisions Made
- Used dynamic `ps.all_perils|length` instead of plan's hardcoded "8" for peril count -- more robust if perils are added/removed
- Added explanatory footer bullets to HTML peril section matching the existing pattern used by other scoring subsections

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- HTML and Markdown renderers now display peril-organized scoring matching Plan 02's Word renderer structure
- Plan 04 (test suite and verification) can proceed with all three renderers having peril sections

## Self-Check: PASSED

All 3 modified files verified present. All 3 task commits verified in git log.

---
*Phase: 42-brain-risk-framework*
*Completed: 2026-02-24*
