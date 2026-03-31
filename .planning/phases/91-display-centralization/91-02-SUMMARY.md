---
phase: 91-display-centralization
plan: 02
subsystem: render
tags: [yaml, registry, charts, dataclass, importlib, declarative-config]

# Dependency graph
requires:
  - phase: 88-stock-analysis-engine
    provides: "Chart modules (stock, drawdown, volatility, relative, drop)"
  - phase: 90-drop-enhancements
    provides: "Drop analysis and scatter chart modules"
provides:
  - "chart_registry.yaml — declarative catalog of all 15 charts with metadata"
  - "chart_registry.py — loader, validator, and function resolver"
  - "Section/format filtering for registry-driven rendering"
affects: [91-display-centralization, 92-rendering-completeness]

# Tech tracking
tech-stack:
  added: []
  patterns: [declarative-yaml-registry, dynamic-import-resolution, dataclass-catalog]

key-files:
  created:
    - src/do_uw/brain/config/chart_registry.yaml
    - src/do_uw/stages/render/chart_registry.py
    - tests/test_chart_registry.py
  modified: []

key-decisions:
  - "Used dataclass instead of Pydantic for ChartEntry — lightweight metadata, no validation logic needed beyond required field checks"
  - "call_style field distinguishes 5 chart calling conventions (standard, minimal, radar, ownership, timeline)"
  - "Module-level _cache for lazy singleton load — avoids re-parsing YAML on every call"

patterns-established:
  - "Declarative YAML registry: new charts added by YAML entry + rendering function, no template wiring"
  - "Dynamic function resolution via importlib.import_module + getattr with clear error messages"

requirements-completed: [DISP-03]

# Metrics
duration: 3min
completed: 2026-03-09
---

# Phase 91 Plan 02: Chart Registry Summary

**Declarative chart_registry.yaml catalog with Python loader, validator, and dynamic function resolver for all 15 chart types**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-09T16:32:14Z
- **Completed:** 2026-03-09T16:35:30Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Created chart_registry.yaml declaring all 15 charts with id, name, module, function, formats, data_requires, section, position, call_style, signals, and overlays
- Built chart_registry.py with load_chart_registry(), resolve_chart_fn(), get_charts_for_section(), get_charts_for_format()
- All 15 chart rendering functions verified importable via dynamic resolution
- 14 unit tests covering load, resolve, section/format filtering, and validation error handling

## Task Commits

Each task was committed atomically:

1. **Task 1: Create chart_registry.yaml declaring all charts** - `5813551` (feat)
2. **Task 2 RED: Failing tests for chart_registry.py** - `f849f72` (test)
3. **Task 2 GREEN: Implement chart_registry.py loader** - `0d7b0e6` (feat)

_TDD: Task 2 had separate RED and GREEN commits._

## Files Created/Modified
- `src/do_uw/brain/config/chart_registry.yaml` - Declarative catalog of all 15 chart types with metadata, signals, overlays
- `src/do_uw/stages/render/chart_registry.py` - Registry loader, validator, ChartEntry dataclass, function resolver, section/format filtering
- `tests/test_chart_registry.py` - 14 unit tests for YAML structure + Python loader

## Decisions Made
- Used dataclass instead of Pydantic for ChartEntry (lightweight metadata, no complex validation needed)
- 5 call_style values (standard, minimal, radar, ownership, timeline) to capture varying chart function signatures
- Module-level _cache for singleton load pattern — avoids re-parsing YAML on every call
- Overlays declared as top-level section in YAML, referenced by ID from stock chart entries

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Chart registry provides foundation for registry-driven rendering (future wiring)
- Registry serves as CI-checkable completeness catalog
- get_charts_for_section() ready for template-driven chart insertion

## Self-Check: PASSED

All 3 created files verified on disk. All 3 task commits verified in git log.

---
*Phase: 91-display-centralization*
*Completed: 2026-03-09*
