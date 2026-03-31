---
phase: 41-peril-organized-scoring-golden-html-output
plan: 01
subsystem: render
tags: [peril-scoring, html, jinja2, brain-framework, frequency-severity, duckdb]

# Dependency graph
requires:
  - phase: 42-brain-risk-framework
    provides: "brain_perils (8), brain_causal_chains (16), scoring_peril_data.py, brain build CLI"
provides:
  - "F/S role dimension annotations on 10 scoring factors from risk_model.yaml"
  - "Color-coded F/S/F+S badges in HTML 10-factor scoring table"
  - "Verified peril scoring data flow from brain.duckdb through extract_scoring to HTML template"
  - "10 integration tests covering peril scoring and role badges"
affects: [41-02-PLAN, 41-03-PLAN]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "YAML-driven factor annotation at render time (read-once, try/except graceful degradation)"
    - "Jinja2 inline conditional class badges for role display"

key-files:
  created:
    - tests/render/test_peril_scoring_html.py
  modified:
    - src/do_uw/stages/render/md_renderer_helpers_scoring.py
    - src/do_uw/templates/html/sections/scoring.html.j2

key-decisions:
  - "Factor roles loaded from risk_model.yaml at render time (not from DuckDB) -- lightweight, follows existing try/except graceful degradation pattern"
  - "Badge design: single-letter F/S/F+S with color-coded backgrounds (blue/orange/purple) matching Bloomberg annotation style"
  - "Template autoescape=False means D&O renders literally, not as D&amp;O"

patterns-established:
  - "YAML annotation enrichment at render: load YAML config file once, annotate existing data structures"

requirements-completed: []

# Metrics
duration: 17min
completed: 2026-02-24
---

# Phase 41 Plan 01: Wire Peril Scoring Data and F/S Role Badges Summary

**Peril scoring data flow verified end-to-end from brain.duckdb to HTML template, with F/S role dimension badges on all 10 scoring factors**

## Performance

- **Duration:** 17 min
- **Started:** 2026-02-24T16:31:41Z
- **Completed:** 2026-02-24T16:48:16Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Verified `brain build` produces 8 perils and 16 causal chains in brain.duckdb
- Confirmed extract_peril_scoring() returns structured data with all_perils and perils keys when brain tables populated
- Added F/S role annotations (FREQUENCY/SEVERITY/BOTH) to all 10 scoring factors from risk_model.yaml
- Added color-coded role badges to HTML 10-factor scoring table with explanatory footnote
- Created 10 integration tests covering peril scoring data flow, role annotations, template rendering, and graceful degradation

## Task Commits

Each task was committed atomically:

1. **Task 1: Verify brain build and peril scoring data flow** - `070f837` (feat)
2. **Task 2: Add F/S role badges to scoring template and write integration tests** - `ec359f4` (feat)

## Files Created/Modified
- `src/do_uw/stages/render/md_renderer_helpers_scoring.py` - Added F/S role annotation block after factor list construction
- `src/do_uw/templates/html/sections/scoring.html.j2` - Added role badge HTML in factor name cell + footnote explaining badges
- `tests/render/test_peril_scoring_html.py` - 10 integration tests for peril scoring and role badges in HTML context

## Decisions Made
- Factor roles loaded from risk_model.yaml at render time (not from DuckDB) -- lightweight, follows existing try/except graceful degradation pattern in the codebase
- Badge design uses single-letter (F/S/F+S) with color-coded backgrounds (blue/orange/purple) -- compact and professional, matches Bloomberg annotation style from plan
- Template uses autoescape=False, so D&O renders as literal text not HTML entity

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pre-existing DuckDB file lock contention causes test failures in test_compat_loader.py and test_backtest.py when brain.duckdb is held by another process (PID 51645). This is a known pre-existing issue, NOT caused by this plan's changes. 529 render/brain tests pass with zero regressions.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Peril scoring data flows end-to-end; Plan 02 can build on this for enhanced peril deep-dive rendering
- Plan 03 can use the F/S role data for scoring presentation refinement
- brain.duckdb has up-to-date framework tables (8 perils, 16 chains, 19 framework entries)

## Self-Check: PASSED

All files verified present, all commit hashes confirmed in git log.

---
*Phase: 41-peril-organized-scoring-golden-html-output*
*Completed: 2026-02-24*
