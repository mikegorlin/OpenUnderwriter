---
phase: 83-dependency-graph-visualization
plan: 01
subsystem: brain
tags: [graphlib, dag, topological-sort, dependency-graph, signal-ordering]

# Dependency graph
requires:
  - phase: 82-v3-schema-migration
    provides: "signal_class field on all 476 signals (foundational/evaluative/inference)"
provides:
  - "dependency_graph.py module with DAG construction, cycle detection, tier+topo ordering"
  - "Cycle detection at signal load time (warning level)"
  - "Tier-based topological signal execution ordering in signal_engine"
affects: [83-02, 83-03, 83-04, 84-section-elimination]

# Tech tracking
tech-stack:
  added: [graphlib.TopologicalSorter]
  patterns: [tier-based-ordering, within-tier-topological-sort, cross-tier-edge-exclusion]

key-files:
  created:
    - src/do_uw/brain/dependency_graph.py
    - tests/brain/test_dependency_graph.py
    - tests/stages/analyze/test_signal_execution_order.py
  modified:
    - src/do_uw/brain/brain_unified_loader.py
    - src/do_uw/stages/analyze/signal_engine.py

key-decisions:
  - "Cycle detection is WARNING level (not error) since only 55/476 signals have depends_on"
  - "Cross-tier dependencies excluded from per-tier TopologicalSorter to avoid missing-node errors"
  - "Ordering applied before chunk loop in execute_signals, preserving all existing evaluation logic"

patterns-established:
  - "Tier ordering pattern: foundational(0) -> evaluative(1) -> inference(2) with within-tier topo sort"
  - "Cross-tier edge exclusion: per-tier sub-graphs only include edges where both nodes are in same tier"

requirements-completed: [GRAPH-01, GRAPH-02, GRAPH-03]

# Metrics
duration: 4min
completed: 2026-03-08
---

# Phase 83 Plan 01: Dependency Graph Infrastructure Summary

**Signal dependency DAG using graphlib.TopologicalSorter with tier-based execution ordering and load-time cycle detection**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-08T06:51:22Z
- **Completed:** 2026-03-08T06:55:52Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Created dependency_graph.py with 4 exported functions: build_dependency_graph, detect_cycles, topological_order, order_signals_for_execution
- Integrated cycle detection into BrainLoader.load_signals() as a warning-level check
- Integrated tier+topological execution ordering into signal_engine.execute_signals() before chunk loop
- 14 tests (10 unit + 4 integration), 1041 existing tests pass with no regression

## Task Commits

Each task was committed atomically:

1. **Task 1: Create dependency_graph.py module with DAG, cycle detection, and ordering** - `88ca5d4` (feat)
2. **Task 2: Integrate cycle detection into BrainLoader and execution ordering into signal_engine** - `09af853` (feat)

## Files Created/Modified
- `src/do_uw/brain/dependency_graph.py` - DAG construction, cycle detection, tier+topo ordering (163 lines)
- `tests/brain/test_dependency_graph.py` - 10 unit tests for all graph functions
- `tests/stages/analyze/test_signal_execution_order.py` - 4 integration tests for execution ordering
- `src/do_uw/brain/brain_unified_loader.py` - Added cycle detection call after _warn_v3_fields()
- `src/do_uw/stages/analyze/signal_engine.py` - Added order_signals_for_execution() before chunk loop

## Decisions Made
- Cycle detection is WARNING level (not error) since only 55/476 signals currently have depends_on fields; will become ERROR when all signals populated
- Cross-tier dependencies excluded from per-tier TopologicalSorter to avoid missing-node errors (e.g., evaluative depending on foundational would fail if foundational ID not in evaluative sub-graph)
- Ordering applied to auto_signals list before existing chunk loop, preserving all evaluation logic unchanged

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test mock patch path for local import**
- **Found during:** Task 2 (integration test)
- **Issue:** `order_signals_for_execution` imported inside function body, not at module level, so `patch("do_uw.stages.analyze.signal_engine.order_signals_for_execution")` failed with AttributeError
- **Fix:** Changed patch target to `do_uw.brain.dependency_graph.order_signals_for_execution` (the source module)
- **Files modified:** tests/stages/analyze/test_signal_execution_order.py
- **Verification:** All 14 tests pass
- **Committed in:** 09af853 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor test fix, no scope change.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Dependency graph infrastructure complete, ready for visualization (83-02)
- order_signals_for_execution available for any module needing signal ordering
- Cycle detection runs automatically on every load_signals() call

---
*Phase: 83-dependency-graph-visualization*
*Completed: 2026-03-08*
