---
phase: 99-operational-scoring-signals
plan: 01
subsystem: analyze
tags: [brain-signals, operational-complexity, composite-score, context-builder, jinja2]

# Dependency graph
requires:
  - phase: 94-operational-data-extraction
    provides: "OPS extraction functions (subsidiary, workforce, resilience)"
  - phase: 93-business-model-extraction
    provides: "Revenue segments, company profile fields"
provides:
  - "BIZ.OPS.complexity_score composite signal (0-20 scale)"
  - "_map_ops_fields signal mapper routing for BIZ.OPS.*"
  - "_build_operational_complexity context builder"
  - "operational_complexity.html.j2 dashboard template"
affects: [100-company-profile-display]

# Tech tracking
tech-stack:
  added: []
  patterns: [state-proxy-mapper, composite-signal-formula, score-to-level-in-builder]

key-files:
  created:
    - tests/test_ops_signals.py
  modified:
    - src/do_uw/brain/signals/biz/operations.yaml
    - src/do_uw/stages/analyze/signal_mappers.py
    - src/do_uw/stages/analyze/signal_field_routing.py
    - src/do_uw/brain/field_registry.yaml
    - src/do_uw/brain/field_registry_functions.py
    - src/do_uw/stages/render/context_builders/company.py
    - src/do_uw/templates/html/sections/company/operational_complexity.html.j2
    - tests/brain/test_signal_group_resolution.py

key-decisions:
  - "Composite score uses additive weighted formula (0-20 scale) with 7 dimensions"
  - "Score-to-level mapping in context builder: >=15 HIGH, >=8 MODERATE, else LOW"
  - "State proxy pattern reused from ENVR/SECT phases for BIZ.OPS mapper"
  - "Fixed pre-existing group count assertion from 55 to 60 (phases 96-98 added 5 groups)"

patterns-established:
  - "BIZ.OPS.* signal mapper: _map_ops_fields with state proxy bridging to extraction functions"
  - "Composite score formula: jurisdiction(max 5) + high_reg(max 3) + segments(max 3) + intl_pct(max 3) + VIE(2) + dual_class(2) + union(2)"

requirements-completed: [OPS-01, OPS-05]

# Metrics
duration: 6min
completed: 2026-03-10
---

# Phase 99 Plan 01: Operational Scoring Signals Summary

**BIZ.OPS composite complexity score (0-20 scale) aggregating jurisdictions, workforce, segments, VIE, and dual-class via signal mapper + context builder + dashboard template**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-10T16:50:57Z
- **Completed:** 2026-03-10T16:56:46Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- Added BIZ.OPS.complexity_score composite signal with full v3 schema to operations.yaml
- Created _map_ops_fields mapper with state proxy pattern routing BIZ.OPS.* before generic BIZ.*
- Built _build_operational_complexity context builder with composite score, level/color mapping, and structural indicators
- Replaced stub template with full operational complexity dashboard (score badge, KV table, indicator badges)
- Added 16 tests covering YAML validation, composite formula, context builder, and field routing

## Task Commits

Each task was committed atomically:

1. **Task 1: Add composite signal YAML + signal mapper routing + field routing** - `e8188f8` (feat)
2. **Task 2: Context builder + HTML template + manifest + tests** - `0ad63c8` (feat)

## Files Created/Modified
- `src/do_uw/brain/signals/biz/operations.yaml` - Added BIZ.OPS.complexity_score composite signal
- `src/do_uw/stages/analyze/signal_mappers.py` - Added _map_ops_fields + BIZ.OPS routing
- `src/do_uw/stages/analyze/signal_field_routing.py` - Added 4 BIZ.OPS field routing entries
- `src/do_uw/brain/field_registry.yaml` - Added ops_complexity_score COMPUTED entry
- `src/do_uw/brain/field_registry_functions.py` - Added compute_ops_complexity_score function
- `src/do_uw/stages/render/context_builders/company.py` - Added _build_operational_complexity, wired into extract_company
- `src/do_uw/templates/html/sections/company/operational_complexity.html.j2` - Full dashboard template
- `tests/test_ops_signals.py` - 16 tests for OPS signal pipeline
- `tests/brain/test_signal_group_resolution.py` - Fixed group count assertion (55 -> 60)

## Decisions Made
- Composite score uses additive weighted formula with 7 dimensions (0-20 max): jurisdictions (max 5), high-reg (max 3), segments (max 3), international workforce (max 3), VIE (2), dual-class (2), unionization (2)
- Score-to-level mapping: >=15 HIGH/red, >=8 MODERATE/amber, <8 LOW/green -- all logic in context builder, not template
- State proxy pattern reused from Phase 97 (ENVR) and Phase 98 (SECT) for consistent mapper architecture
- Fixed pre-existing group count test assertion (55 -> 60) to match actual state after phases 96-98

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed pre-existing group count test assertion**
- **Found during:** Task 2 (test verification)
- **Issue:** test_signal_group_count_is_55 was already failing (actual count 60 from phases 96-98)
- **Fix:** Updated assertion to 60 with explanation of count progression
- **Files modified:** tests/brain/test_signal_group_resolution.py
- **Verification:** Test passes with corrected assertion
- **Committed in:** 0ad63c8 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Pre-existing test assertion updated to match current reality. No scope creep.

## Issues Encountered
- Pre-existing test_threshold_provenance_categorized failure in brain_contract (SECT signals with invalid signal_class) -- out of scope, not caused by our changes

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- BIZ.OPS.* signals fully wired through evaluation pipeline
- Composite score ready for consumption by Phase 100 (display)
- Context builder and template ready for integration into company profile section

---
*Phase: 99-operational-scoring-signals*
*Completed: 2026-03-10*
