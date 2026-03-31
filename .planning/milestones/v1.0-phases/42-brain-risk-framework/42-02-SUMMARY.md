---
phase: 42-brain-risk-framework
plan: 02
subsystem: render
tags: [docx, python-docx, peril-scoring, causal-chains, word-renderer]

# Dependency graph
requires:
  - phase: 42-01
    provides: scoring_peril_data.py extraction, BrainDBLoader peril/chain loading
provides:
  - sect7_scoring_perils.py Word renderer for peril summary table and deep dives
  - sect7_scoring.py orchestration wiring for peril-organized scoring
affects: [42-03, 42-04, render]

# Tech tracking
tech-stack:
  added: []
  patterns: [color-coded risk table with cell-level shading, lazy import for graceful fallback, trigger/amplifier/mitigator chain narrative]

key-files:
  created:
    - src/do_uw/stages/render/sections/sect7_scoring_perils.py
    - tests/stages/render/test_sect7_scoring_perils.py
  modified:
    - src/do_uw/stages/render/sections/sect7_scoring.py

key-decisions:
  - "Color-coded summary table uses cell-level shading (like peril_map heat map) rather than add_styled_table, for per-risk-level visual differentiation"
  - "Section divider comments compacted from 5-line blocks to 2-line blocks to stay under 500-line limit after adding peril wiring"
  - "Peril scoring inserted after tier box, before composite breakdown per plan ordering"

patterns-established:
  - "Lazy import pattern for brain framework rendering: try/except ImportError for graceful fallback when DuckDB unavailable"
  - "Chain narrative format: Triggers (bold label + bullet list with evidence) -> Amplifiers -> Mitigators -> Historical context"

requirements-completed: []

# Metrics
duration: 5min
completed: 2026-02-24
---

# Phase 42 Plan 02: Word Renderer -- Peril-Organized Scoring Summary

**Color-coded D&O peril summary table and per-peril causal chain deep dives in Word renderer with trigger/amplifier/mitigator narrative format**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-24T06:12:04Z
- **Completed:** 2026-02-24T06:16:35Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- New sect7_scoring_perils.py (313 lines) with render_peril_summary() and render_peril_deep_dives()
- Peril summary table: color-coded risk levels with cell shading, active chain counts, key evidence
- Per-peril deep dives: causal chain narratives with trigger/amplifier/mitigator structure and historical context
- sect7_scoring.py orchestration wiring with lazy import for graceful fallback
- 27 comprehensive tests covering table structure, content rendering, edge cases, and graceful fallbacks

## Task Commits

Each task was committed atomically:

1. **Task 1: Create sect7_scoring_perils.py** - `6e3cfd0` (feat)
2. **Task 2: Modify sect7_scoring.py orchestration** - `e4adc91` (feat)

## Files Created/Modified
- `src/do_uw/stages/render/sections/sect7_scoring_perils.py` - New peril summary table and deep dive renderers (313 lines)
- `tests/stages/render/test_sect7_scoring_perils.py` - 27 tests for peril scoring renderers
- `src/do_uw/stages/render/sections/sect7_scoring.py` - Added _render_peril_scoring() call and compacted section dividers (473 lines)

## Decisions Made
- Color-coded summary table uses direct cell-level shading (set_cell_shading) instead of add_styled_table for the risk level column, matching the peril_map heat map pattern
- Section divider comments in sect7_scoring.py compacted from verbose 5-line blocks to compact 2-line blocks to stay under 500 lines after adding the new function
- Peril scoring renders after tier box but before composite breakdown, placing the new peril-organized view prominently in the scoring section

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Compacted section dividers to stay under 500-line limit**
- **Found during:** Task 2 (sect7_scoring.py orchestration)
- **Issue:** Adding _render_peril_scoring() function (17 lines) pushed sect7_scoring.py to 506 lines, exceeding 500-line limit
- **Fix:** Compacted 11 section divider comment blocks from 5-line format (blank + dashes + heading + dashes + blank) to 2-line format (compact comment + blank), saving 33 lines
- **Files modified:** src/do_uw/stages/render/sections/sect7_scoring.py
- **Verification:** File now 473 lines, all 46 sect7 tests pass
- **Committed in:** e4adc91 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Comment compaction necessary to respect 500-line limit. No functionality or readability impact.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Peril summary table and deep dives render in Word output when brain framework data is available
- Graceful fallback: if brain.duckdb is missing or has no perils, section silently omits
- Ready for Plan 03 (HTML template equivalent) and Plan 04 (integration/calibration)

---
*Phase: 42-brain-risk-framework*
*Completed: 2026-02-24*
