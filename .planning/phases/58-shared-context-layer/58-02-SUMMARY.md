---
phase: 58-shared-context-layer
plan: 02
subsystem: render
tags: [context-builders, extract, governance, litigation, scoring, analysis, calibration]

# Dependency graph
requires:
  - phase: 58-01
    provides: context_builders package with company, financials, financials_balance, market modules
provides:
  - governance context builder (extract_governance)
  - litigation context builder (extract_litigation)
  - scoring context builders (extract_scoring, extract_ai_risk, extract_meeting_questions)
  - analysis context builders (8 extract_* functions for classification, hazard, composites, etc.)
  - calibration context builder (render_calibration_notes)
  - complete __init__.py with 20 public function re-exports from 9 domain modules
affects: [58-03, 60-word-adapter]

# Tech tracking
tech-stack:
  added: []
  patterns: [context-builder-per-domain, path-traversal-depth-fix]

key-files:
  created:
    - src/do_uw/stages/render/context_builders/governance.py
    - src/do_uw/stages/render/context_builders/litigation.py
    - src/do_uw/stages/render/context_builders/scoring.py
    - src/do_uw/stages/render/context_builders/analysis.py
    - src/do_uw/stages/render/context_builders/calibration.py
  modified:
    - src/do_uw/stages/render/context_builders/__init__.py

key-decisions:
  - "Fixed Path(__file__) traversals in scoring.py (4 parents instead of 3 for context_builders/ depth)"
  - "Kept duplicated _sv_str in both governance.py and litigation.py to avoid cross-module imports"
  - "Litigation module does NOT re-export governance (clean separation unlike old _ext.py)"

patterns-established:
  - "Path depth fix: context_builders modules need +1 parent vs original render/ location for brain/ paths"
  - "Domain independence: governance and litigation are separate modules with no cross-imports"

requirements-completed: [CTX-01, CTX-02, CTX-06]

# Metrics
duration: 5min
completed: 2026-03-02
---

# Phase 58 Plan 02: Remaining Context Builders Summary

**5 domain modules (governance, litigation, scoring, analysis, calibration) moved into context_builders/ with zero logic changes, completing all 9 domain modules + __init__.py with 20 public re-exports**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-02T17:50:49Z
- **Completed:** 2026-03-02T17:56:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Created 5 new context_builders modules: governance (375 lines), litigation (495 lines), scoring (415 lines), analysis (480 lines), calibration (221 lines)
- All 9 domain modules + __init__.py = 10 files in context_builders package (3,213 total lines)
- 20 public functions re-exported from __init__.py
- 276 existing render tests pass with no changes

## Task Commits

Each task was committed atomically:

1. **Task 1: Create governance and litigation modules** - `647d7d8` (feat)
2. **Task 2: Create scoring, analysis, calibration modules; finalize __init__.py** - `e96309c` (feat)

## Files Created/Modified
- `src/do_uw/stages/render/context_builders/governance.py` - Board, leadership, ownership, sentiment extraction (375 lines)
- `src/do_uw/stages/render/context_builders/litigation.py` - SCA cases, SOL windows, derivatives, defense extraction (495 lines)
- `src/do_uw/stages/render/context_builders/scoring.py` - Risk scoring, AI risk, meeting questions extraction (415 lines)
- `src/do_uw/stages/render/context_builders/analysis.py` - Classification, hazard, composites, NLP, peril map extraction (480 lines)
- `src/do_uw/stages/render/context_builders/calibration.py` - Brain DuckDB calibration notes rendering (221 lines)
- `src/do_uw/stages/render/context_builders/__init__.py` - Extended with all 20 public function re-exports (76 lines)

## Decisions Made
- Fixed `Path(__file__)` traversals in scoring.py: needs 4 `.parent` calls instead of 3 due to extra context_builders/ directory depth (same fix as company.py in Plan 01)
- Kept duplicated `_sv_str()` helper in both governance.py and litigation.py — avoids circular imports, matches original design
- Litigation module does NOT re-export governance (the old _ext.py did for convenience; in the new structure they are independent)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed Path(__file__) traversals in scoring.py**
- **Found during:** Task 2 (scoring module creation)
- **Issue:** `_load_crf_conditions()` and risk_model.yaml lookup use `Path(__file__).parent.parent.parent` to reach `brain/` directory. Moving to context_builders/ adds one directory level, breaking the path.
- **Fix:** Changed to `Path(__file__).parent.parent.parent.parent` (4 parents instead of 3)
- **Files modified:** src/do_uw/stages/render/context_builders/scoring.py
- **Verification:** Import test confirms red_flags.json and risk_model.yaml are found
- **Committed in:** e96309c (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Essential path fix for correctness. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 9 context_builders domain modules complete
- Plan 03 can now rewire old helpers as shims pointing to context_builders
- Old md_renderer_helpers_*.py files remain untouched (additive only in this plan)

## Self-Check: PASSED

All 7 created/modified files verified present. Both task commits (647d7d8, e96309c) verified in git log.

---
*Phase: 58-shared-context-layer*
*Completed: 2026-03-02*
