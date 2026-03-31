---
phase: 35-display-presentation-clarity
plan: 02
subsystem: benchmark, analyze, render
tags: [refactor, stage-boundaries, content-type, narrative-helpers, risk-levels]

# Dependency graph
requires:
  - phase: 32-knowledge-driven-acquisition-analysis-pipeline
    provides: content_type field on check definitions in checks.json
provides:
  - score_to_risk_level, score_to_threat_label, dim_score_threat in benchmark/risk_levels.py
  - build_thesis_narrative, build_risk_narrative, build_claim_narrative in benchmark/narrative_helpers.py
  - content_type field on every CheckResult for RENDER display dispatch
affects: [35-03, 35-04, 35-05, 35-06, 35-07]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Analytical functions in benchmark/, not render/ -- proper stage boundaries"
    - "Backward-compat re-export aliases when relocating functions"
    - "content_type propagation through check engine for display dispatch"

key-files:
  created:
    - src/do_uw/stages/benchmark/risk_levels.py
    - src/do_uw/stages/benchmark/narrative_helpers.py
    - tests/stages/benchmark/test_narrative_helpers.py
  modified:
    - src/do_uw/stages/benchmark/__init__.py
    - src/do_uw/stages/render/sections/sect7_scoring.py
    - src/do_uw/stages/render/sections/sect8_ai_risk.py
    - src/do_uw/stages/render/sections/sect1_helpers.py
    - src/do_uw/stages/analyze/check_engine.py
    - src/do_uw/stages/analyze/check_results.py

key-decisions:
  - "Public API for relocated functions (no underscore prefix) with backward-compat aliases in render/"
  - "content_type field added to CheckResult model with default EVALUATIVE_CHECK for backward compat"
  - "Narrative helper safe_* functions co-located with narrative builders (used by narratives, not just render)"

patterns-established:
  - "Relocated analytical functions: canonical source in benchmark/, re-export from render/ for backward compat"
  - "content_type on CheckResult enables downstream display dispatch without re-reading check definitions"

requirements-completed: [CORE-04, DATA-14]

# Metrics
duration: 5min
completed: 2026-02-21
---

# Phase 35 Plan 02: Analytical Logic Relocation Summary

**Relocated score-to-risk-level, threat-label, and narrative builders from render/ to benchmark/; propagated content_type through check engine results for display dispatch**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-21T14:47:58Z
- **Completed:** 2026-02-21T14:53:25Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Created benchmark/risk_levels.py with 3 public scoring functions (score_to_risk_level, score_to_threat_label, dim_score_threat)
- Created benchmark/narrative_helpers.py with 3 narrative builders and supporting helpers (build_thesis_narrative, build_risk_narrative, build_claim_narrative)
- Added content_type field to CheckResult and propagated it through all 4 check engine code paths
- 28 new tests covering all relocated functions, boundary conditions, and backward compatibility
- All 33 existing render tests pass via backward-compat re-exports

## Task Commits

Each task was committed atomically:

1. **Task 1: Relocate analytical functions from render/ to benchmark/** - `de49a59` (refactor)
2. **Task 2: Propagate content_type through check engine results** - `8f11819` (feat)

## Files Created/Modified
- `src/do_uw/stages/benchmark/risk_levels.py` - Score-to-risk-level and threat label functions (public API)
- `src/do_uw/stages/benchmark/narrative_helpers.py` - Thesis, risk, and claim narrative builders relocated from sect1_helpers.py
- `tests/stages/benchmark/test_narrative_helpers.py` - 28 tests for relocated functions and backward compat
- `src/do_uw/stages/benchmark/__init__.py` - Updated _precompute_narratives() to use direct imports from benchmark/
- `src/do_uw/stages/render/sections/sect7_scoring.py` - Imports score_to_risk_level from benchmark/risk_levels.py
- `src/do_uw/stages/render/sections/sect8_ai_risk.py` - Imports score_to_threat_label and dim_score_threat from benchmark/risk_levels.py
- `src/do_uw/stages/render/sections/sect1_helpers.py` - Re-exports from benchmark/narrative_helpers.py, retains presentation-only helpers
- `src/do_uw/stages/analyze/check_engine.py` - Propagates content_type onto every CheckResult
- `src/do_uw/stages/analyze/check_results.py` - Added content_type field to CheckResult model

## Decisions Made
- Made relocated functions public (dropped underscore prefix) since they are now a proper API in benchmark/; backward-compat aliases preserve old private names in render/
- Added content_type as a string field (not enum) on CheckResult for backward compatibility with existing serialization
- Co-located safe_distress and safe_leverage_ratio with narrative builders in narrative_helpers.py since they are analytical helpers used by the narratives

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- InherentRiskBaseline requires market_cap_adjusted_rate_pct field (not in plan's test fixture) -- fixed test fixture with correct field

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- benchmark/risk_levels.py and benchmark/narrative_helpers.py ready for import by later plans (35-03 through 35-07)
- content_type on CheckResult enables knowledge-driven display dispatch in plan 35-03+
- All backward-compat re-exports verified -- no breaking changes

## Self-Check: PASSED

All 4 created files verified on disk. Both commit hashes (de49a59, 8f11819) found in git log. 55 benchmark tests pass, 33 render backward-compat tests pass, 29 check engine content type tests pass.

---
*Phase: 35-display-presentation-clarity*
*Completed: 2026-02-21*
