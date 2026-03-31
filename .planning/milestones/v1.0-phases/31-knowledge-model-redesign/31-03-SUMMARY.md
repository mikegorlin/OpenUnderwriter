---
phase: 31-knowledge-model-redesign
plan: 03
subsystem: analyze
tags: [declarative-routing, field-key, narrow-result, coverage-gaps, content-type, rationale]

# Dependency graph
requires:
  - phase: 31-knowledge-model-redesign
    plan: 02
    provides: "388 checks enriched with content_type, depth, data_strategy.field_key"
  - phase: 26-check-classification
    provides: "FIELD_FOR_CHECK routing dict (247 entries) in check_field_routing.py"
provides:
  - "narrow_result with 3-tier resolution: data_strategy.field_key -> FIELD_FOR_CHECK -> full dict"
  - "All 5 sub-mapper functions thread check_config through to narrow_result"
  - "Coverage gaps section with content type labels and rationale visibility"
  - "5 validation tests for declarative field_key resolution"
affects: [31-04-PLAN]

# Tech tracking
tech-stack:
  added: []
  patterns: ["3-tier field resolution: declarative check_def -> legacy FIELD_FOR_CHECK -> full dict", "Coverage gap enrichment via BackwardCompatLoader metadata cache"]

key-files:
  created:
    - "tests/stages/analyze/test_declarative_mapper.py"
  modified:
    - "src/do_uw/stages/analyze/check_field_routing.py"
    - "src/do_uw/stages/analyze/check_mappers.py"
    - "src/do_uw/stages/analyze/check_mappers_sections.py"
    - "src/do_uw/stages/render/sections/sect7_coverage_gaps.py"

key-decisions:
  - "narrow_result check_def parameter defaults to None for full backward compatibility"
  - "All 5 sub-mapper functions receive check_config as keyword-only with None default"
  - "Coverage gap metadata loaded via BackwardCompatLoader with module-level cache"
  - "Content type labels: MANAGEMENT_DISPLAY->REQUIRED, EVALUATIVE_CHECK->EVALUATIVE, INFERENCE_PATTERN->PATTERN"

patterns-established:
  - "Declarative check metadata flows from check definition through mapper chain to field routing"
  - "Graceful fallback: if metadata unavailable, behavior is identical to pre-enhancement"

# Metrics
duration: 5min
completed: 2026-02-15
---

# Phase 31 Plan 03: Declarative Field Routing & Coverage Gap Enhancement Summary

**narrow_result reads data_strategy.field_key from check definitions with legacy FIELD_FOR_CHECK fallback; coverage gaps show content type labels and rationale for each unavailable check**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-15T21:17:29Z
- **Completed:** 2026-02-15T21:22:51Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- narrow_result now resolves field_key from check definition data_strategy.field_key first, falling back to FIELD_FOR_CHECK (legacy), then returning full dict
- All 5 sub-mapper functions (_map_company_fields, _map_financial_fields, _map_market_fields, map_governance_fields, map_litigation_fields) plus 2 wrapper functions (_gov_fields, _lit_fields) thread check_config through to narrow_result
- Coverage gaps section shows [REQUIRED], [EVALUATIVE], [PATTERN] content type labels and rationale for each gap
- Gap breakdown summary with content type counts added after gap listing
- NOT_APPLICABLE section includes content type prefixes
- 5 new tests validating 3-tier resolution order all passing
- 1788 total tests passing (1 pre-existing ground truth failure unrelated)

## Task Commits

Each task was committed atomically:

1. **Task 1: Declarative field_key resolution in narrow_result with mapper plumbing** - `d884b23` (feat)
2. **Task 2: Enhanced coverage gaps with rationale, content type, and known gap visibility** - `e452eaf` (feat)

## Files Created/Modified
- `src/do_uw/stages/analyze/check_field_routing.py` - narrow_result with 3-tier resolution (check_def -> FIELD_FOR_CHECK -> full dict)
- `src/do_uw/stages/analyze/check_mappers.py` - All sub-mappers and wrapper functions thread check_config to narrow_result
- `src/do_uw/stages/analyze/check_mappers_sections.py` - map_governance_fields and map_litigation_fields accept and forward check_config
- `src/do_uw/stages/render/sections/sect7_coverage_gaps.py` - Enhanced with content type labels, rationale, gap breakdown summary (296 lines)
- `tests/stages/analyze/test_declarative_mapper.py` - 5 tests for declarative field_key resolution

## Decisions Made
- All new parameters use `None` defaults so callers that don't pass them continue to work without modification
- Coverage gap metadata loaded via BackwardCompatLoader with global cache to avoid repeated I/O
- Content type labels map to underwriter-friendly terms: REQUIRED (management displays), EVALUATIVE (analytical checks), PATTERN (inference patterns)
- _GapItem class uses __slots__ for lightweight gap representation

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Declarative field_key resolution is live and backward-compatible
- Coverage gap rendering shows enriched metadata from Phase 31 enrichment
- Ready for Plan 31-04 (final knowledge model integration)
- All existing tests pass without regression

## Self-Check: PASSED

All 5 files verified present. Both task commits (d884b23, e452eaf) verified in git log.

---
*Phase: 31-knowledge-model-redesign*
*Completed: 2026-02-15*
