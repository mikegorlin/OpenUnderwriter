---
phase: 28-presentation-layer-context-through-comparison
plan: 04
subsystem: render
tags: [peer-context, density-gating, governance, litigation, scoring, percentile, docx]

# Dependency graph
requires:
  - phase: 28-02
    provides: "peer_context.py with format_metric_with_context, get_peer_context_line, get_benchmark_for_metric"
provides:
  - "Governance score peer percentile in Section 5"
  - "Issue-driven density gating for Section 5 (governance) and Section 6 (litigation)"
  - "Quality score peer percentile and peer comparison table in Section 7"
  - "Factor-to-benchmark inline context in scoring detail (F.6-F.9)"
  - "render_enforcement_pipeline() moved to sect6_defense.py (public API)"
  - "is_valid_person_name(), filter_valid_executives(), count_shade_factors() in sect5_governance_board.py"
affects: [28-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Issue-driven density gating: _is_X_clean() predicate controls concise vs forensic rendering"
    - "Factor-to-benchmark mapping: _FACTOR_BENCHMARK_MAP constant maps factor IDs to benchmark metric keys"
    - "Peer quality score comparison table in tier classification box"

key-files:
  created: []
  modified:
    - src/do_uw/stages/render/sections/sect5_governance.py
    - src/do_uw/stages/render/sections/sect5_governance_board.py
    - src/do_uw/stages/render/sections/sect6_litigation.py
    - src/do_uw/stages/render/sections/sect6_defense.py
    - src/do_uw/stages/render/sections/sect6_timeline.py
    - src/do_uw/stages/render/sections/sect7_scoring.py
    - src/do_uw/stages/render/sections/sect7_scoring_detail.py
    - tests/test_render_sections_5_7.py

key-decisions:
  - "Moved enforcement pipeline rendering from sect6_litigation.py to sect6_defense.py for 500-line compliance"
  - "Moved name validation helpers from sect5_governance.py to sect5_governance_board.py (public API: is_valid_person_name, filter_valid_executives, count_shade_factors)"
  - "Factor-to-benchmark mapping covers F.6 (short_interest_pct), F.7 (volatility_90d), F.8 (leverage_debt_ebitda), F.9 (governance_score)"
  - "Used state.benchmark (confirmed correct path from 28-02 summary) not state.benchmarked"

patterns-established:
  - "_is_governance_clean() checks: independence >= 75%, no overboarding, no duality, no activists, no forensic flags, gov score >= 50th pctl"
  - "_is_litigation_clean() checks: no active SCA, no SEC enforcement beyond comment letters, no derivative suits, no regulatory proceedings, no deal litigation"
  - "render_board_quality_metrics() backward-compatible signature: accepts (doc, gov, state, ds) or (doc, gov, ds)"

# Metrics
duration: 14min
completed: 2026-02-13
---

# Phase 28 Plan 04: Sections 5/6/7 Peer Context and Issue-Driven Density Gating Summary

**Governance/litigation density gating with concise rendering for clean companies, plus quality score and factor-level peer percentile context in Section 7**

## Performance

- **Duration:** 14 min
- **Started:** 2026-02-13T13:27:54Z
- **Completed:** 2026-02-13T13:42:06Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Section 5: governance score rendered with peer percentile; clean governance (high independence, no overboarding, no duality, no activists) renders concise one-sentence summaries instead of full board roster/ownership tables
- Section 6: clean litigation (no active SCA, no SEC enforcement, no derivative suits) renders concise summary instead of full forensic tables; SOL map and defense assessment still always render
- Section 7: quality score in tier box shows peer percentile context; peer quality score comparison table with sector average; factor detail has inline benchmark context for F.6-F.9 (short interest, volatility, leverage, governance)
- All files under 500-line anti-context-rot limit via targeted refactoring (enforcement pipeline to defense module, name validation to board module)

## Task Commits

Each task was committed atomically:

1. **Task 1: Peer context + density gating for Sections 5 and 6** - `d2a0eae` (feat)
2. **Task 2: Peer context in Section 7 scoring synthesis** - `8cc56c5` (feat)

## Files Created/Modified
- `src/do_uw/stages/render/sections/sect5_governance.py` - Orchestrator with _is_governance_clean(), governance score peer context, clean summary renderers (412 lines)
- `src/do_uw/stages/render/sections/sect5_governance_board.py` - Board renderers plus name validation helpers moved here (492 lines)
- `src/do_uw/stages/render/sections/sect6_litigation.py` - Orchestrator with _is_litigation_clean(), clean litigation summary, density gating (467 lines)
- `src/do_uw/stages/render/sections/sect6_defense.py` - Defense assessment plus enforcement pipeline rendering moved here (443 lines)
- `src/do_uw/stages/render/sections/sect6_timeline.py` - Added concise parameter for clean litigation SOL-only rendering (269 lines)
- `src/do_uw/stages/render/sections/sect7_scoring.py` - Quality score peer context in tier box, peer comparison table (474 lines)
- `src/do_uw/stages/render/sections/sect7_scoring_detail.py` - Factor-to-benchmark inline context via _FACTOR_BENCHMARK_MAP (369 lines)
- `tests/test_render_sections_5_7.py` - Updated tests for density gating behavior

## Decisions Made
- Moved enforcement pipeline rendering to sect6_defense.py rather than creating a new file, since defense module already handles SEC enforcement-related content and had room (325 -> 443 lines)
- Made name validation functions public (is_valid_person_name, filter_valid_executives, count_shade_factors) instead of private, since they're now imported cross-module
- render_board_quality_metrics() uses backward-compatible signature with isinstance check: old callers pass (doc, gov, ds), new callers pass (doc, gov, state, ds)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] 500-line compliance for sect5_governance.py and sect6_litigation.py**
- **Found during:** Task 1 (verifying line counts)
- **Issue:** After adding density gating code, sect5_governance.py was 528 lines and sect6_litigation.py was 598 lines, both exceeding the 500-line anti-context-rot limit
- **Fix:** Moved name validation helpers (~100 lines) from sect5_governance.py to sect5_governance_board.py; moved enforcement pipeline rendering (~130 lines) from sect6_litigation.py to sect6_defense.py
- **Files modified:** All 4 affected files
- **Verification:** Final line counts: 412, 492, 467, 443 -- all under 500
- **Committed in:** d2a0eae (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary for 500-line compliance. No scope creep -- just reorganizing existing code into appropriate modules.

## Issues Encountered
- Pre-existing uncommitted changes from partial plan 28-03 and 28-04 execution were found in the working tree. Plan 28-03 changes were committed by a pre-commit hook during Task 1 staging. The 28-04 governance/litigation changes were already correct and were included in Task 1 commit.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- SC1 (context-through-comparison) complete: all sections with benchmark-able metrics now show peer percentile context
- SC2 (issue-driven density) complete: Sections 3 (via 28-03), 4 (via 28-03), 5, and 6 have clean/problematic branching
- Ready for Plan 28-05 (final integration/testing)
- All 2928 tests pass with 0 regressions

## Self-Check: PASSED

- All 8 modified files exist on disk
- Both commit hashes (d2a0eae, 8cc56c5) found in git log
- All files under 500 lines (max: 492 in sect5_governance_board.py)
- 2928 tests pass

---
*Phase: 28-presentation-layer-context-through-comparison*
*Completed: 2026-02-13*
