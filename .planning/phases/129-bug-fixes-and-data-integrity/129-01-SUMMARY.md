---
phase: 129-bug-fixes-and-data-integrity
plan: 01
subsystem: render, scoring
tags: [sca-counter, crf-insolvency, data-consistency, centralization]

# Dependency graph
requires:
  - phase: 128-data-integrity-framework
    provides: Assembly registry pattern, scoring context builder
provides:
  - Canonical SCA counter (sca_counter.py) with get_active_genuine_scas and count_active_genuine_scas
  - Canonical insolvency suppression (should_suppress_insolvency in red_flag_gates.py)
  - 22 new consistency tests proving identical results across all render paths
affects: [render, scoring, analyze, executive-summary, litigation-section]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Canonical counter pattern: single function for cross-codebase consistency"
    - "Suppression delegation: wrapper functions delegate to canonical, add domain-specific keyword filtering"

key-files:
  created:
    - src/do_uw/stages/render/sca_counter.py
    - tests/render/test_sca_count_consistency.py
    - tests/render/test_crf_insolvency_suppression.py
    - tests/render/test_crf_ceiling_display.py
  modified:
    - src/do_uw/stages/score/red_flag_gates.py
    - src/do_uw/stages/render/sections/sect1_findings_data.py
    - src/do_uw/stages/render/context_builders/_narrative_generators.py
    - src/do_uw/stages/render/context_builders/monitoring_context.py
    - src/do_uw/stages/render/md_narrative_sections.py
    - src/do_uw/stages/score/factor_data.py
    - src/do_uw/stages/score/pattern_fields.py
    - src/do_uw/stages/analyze/section_assessments.py
    - src/do_uw/stages/render/context_builders/crf_bar_context.py
    - src/do_uw/stages/render/context_builders/assembly_registry.py
    - src/do_uw/stages/render/context_builders/scoring.py
    - src/do_uw/stages/render/sections/sect6_litigation.py

key-decisions:
  - "SCA counter centralizes active count only; sites that count all genuine SCAs (any status) still use _is_regulatory_not_sca directly"
  - "Insolvency suppression threshold: Altman Z > 3.0 AND current ratio > 0.5 AND no going concern"
  - "Kept _get_distress_metrics as deprecated wrapper for backward compatibility"

patterns-established:
  - "Canonical counter pattern: sca_counter.py provides single source of truth for active genuine SCA counting"
  - "Canonical suppression pattern: should_suppress_insolvency in red_flag_gates.py is single source of truth"

requirements-completed: [FIX-04, FIX-05]

# Metrics
duration: 9min
completed: 2026-03-23
---

# Phase 129 Plan 01: SCA Count Centralization + CRF Insolvency Suppression Summary

**Canonical SCA counter (sca_counter.py) and centralized CRF insolvency suppression (should_suppress_insolvency) eliminating 13+ sites of divergent inline filter logic**

## Performance

- **Duration:** 9 min
- **Started:** 2026-03-23T00:01:00Z
- **Completed:** 2026-03-23T00:10:00Z
- **Tasks:** 2
- **Files modified:** 16

## Accomplishments
- Created canonical `sca_counter.py` with `get_active_genuine_scas()` and `count_active_genuine_scas()` -- single source of truth for active genuine SCA counting
- Rewired 5 direct active-count call sites and aligned 3 inline filters with canonical criteria (ACTIVE, PENDING, N/A, None = active)
- Created `should_suppress_insolvency()` in `red_flag_gates.py` -- single source of truth for CRF insolvency suppression
- Rewired all 3 suppression sites (crf_bar_context, assembly_registry, scoring) to delegate to canonical function
- 22 new tests: 12 SCA consistency + 7 insolvency suppression + 3 ceiling display

## Task Commits

Each task was committed atomically:

1. **Task 1: Create canonical SCA counter + rewire call sites** - `3935cb02` (feat)
2. **Task 2: Centralize CRF insolvency suppression + ceiling display** - `37e4fa2a` (feat)

## Files Created/Modified
- `src/do_uw/stages/render/sca_counter.py` - Canonical SCA counter (get_active_genuine_scas, count_active_genuine_scas)
- `src/do_uw/stages/score/red_flag_gates.py` - Added should_suppress_insolvency() public function
- `src/do_uw/stages/render/sections/sect1_findings_data.py` - Rewired to use count_active_genuine_scas
- `src/do_uw/stages/render/context_builders/_narrative_generators.py` - Rewired to use get_active_genuine_scas
- `src/do_uw/stages/render/context_builders/monitoring_context.py` - Rewired to use count_active_genuine_scas
- `src/do_uw/stages/render/md_narrative_sections.py` - Rewired to use get_active_genuine_scas
- `src/do_uw/stages/analyze/section_assessments.py` - Rewired to use get_active_genuine_scas
- `src/do_uw/stages/score/factor_data.py` - Aligned active status criteria with canonical
- `src/do_uw/stages/score/pattern_fields.py` - Aligned active status criteria with canonical
- `src/do_uw/stages/render/sections/sect6_litigation.py` - Aligned active filter to include PENDING/N/A
- `src/do_uw/stages/render/context_builders/crf_bar_context.py` - Delegates to should_suppress_insolvency
- `src/do_uw/stages/render/context_builders/assembly_registry.py` - Delegates to should_suppress_insolvency
- `src/do_uw/stages/render/context_builders/scoring.py` - Delegates to should_suppress_insolvency
- `tests/render/test_sca_count_consistency.py` - 12 tests for canonical SCA counter
- `tests/render/test_crf_insolvency_suppression.py` - 7 tests for insolvency suppression
- `tests/render/test_crf_ceiling_display.py` - 3 tests for ceiling display consistency

## Decisions Made
- SCA counter centralizes only the "active genuine" count; sites that count ALL genuine SCAs regardless of status (e.g., "X on record" display, litigation summary, damage clock exclusions) continue using `_is_regulatory_not_sca` directly since they have legitimately different semantics
- Insolvency suppression threshold chosen as Altman Z > 3.0 AND current ratio > 0.5, matching the existing behavior across all 3 sites
- Going concern opinion is a hard override: never suppress insolvency CRF if going concern exists
- `_get_distress_metrics` kept as deprecated wrapper in scoring.py for backward compatibility

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pre-existing test failures found in `test_crf_calibration.py` (DDL consistency) and `test_peril_scoring_html.py` (SimpleNamespace missing ceiling_details). Both confirmed pre-existing, not caused by these changes.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- SCA count consistency guaranteed across all render paths
- CRF insolvency suppression consolidated into single function
- Ready for remaining Phase 129 plans (129-02, 129-03)

---
*Phase: 129-bug-fixes-and-data-integrity*
*Completed: 2026-03-23*
