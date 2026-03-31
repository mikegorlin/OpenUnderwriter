---
phase: 137-canonical-metrics-registry
plan: 02
subsystem: render
tags: [canonical-metrics, context-builders, backward-compat, cross-section-consistency]

requires:
  - phase: 137-canonical-metrics-registry
    plan: 01
    provides: MetricValue, CanonicalMetrics, build_canonical_metrics

provides:
  - Canonical metrics wired into build_html_context (computed once, shared across builders)
  - 5 highest-duplication builders migrated to consume from canonical registry
  - Backward-compatible canonical=None defaults for md_renderer path

affects: [key-stats, beta-report, company-profile, scorecard, exec-summary, assembly-registry]

tech-stack:
  added: []
  patterns: [canonical-kwarg-injection, fallback-to-legacy-extraction]

key-files:
  created: []
  modified:
    - src/do_uw/stages/render/context_builders/assembly_registry.py
    - src/do_uw/stages/render/context_builders/key_stats_context.py
    - src/do_uw/stages/render/context_builders/beta_report.py
    - src/do_uw/stages/render/context_builders/company_profile.py
    - src/do_uw/stages/render/context_builders/scorecard_context.py
    - src/do_uw/stages/render/context_builders/company_exec_summary.py
    - src/do_uw/stages/render/context_builders/assembly_dossier.py
    - src/do_uw/stages/render/context_builders/assembly_beta_report.py
    - tests/test_canonical_metrics.py

key-decisions:
  - "Canonical passed as keyword-only param (canonical=None) rather than modifying BuilderFn signature"
  - "Assembly wrappers extract _canonical_obj from context and pass to inner builders"
  - "All old extraction functions preserved as fallback for md_renderer and non-assembly callers"

patterns-established:
  - "canonical=None kwarg pattern: builder accepts optional canonical, falls back to legacy extraction"
  - "Assembly wrapper pattern: context.get('_canonical_obj') passed through to inner builder calls"

requirements-completed: [METR-02, METR-04]

duration: 7min
completed: 2026-03-27
---

# Phase 137 Plan 02: Wire Canonical Registry into Context Builders Summary

**Canonical metrics computed once in build_html_context and consumed by 5 highest-duplication builders (key_stats, beta_report, company_profile, scorecard, exec_summary) with full backward compatibility**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-27T20:55:52Z
- **Completed:** 2026-03-27T21:02:45Z
- **Tasks:** 2/2
- **Files modified:** 9

## Accomplishments

- assembly_registry.py computes canonical metrics once at top of build_html_context via try/except
- Stores both serialized dict (context["_canonical"]) and CanonicalMetrics object (context["_canonical_obj"])
- 5 builders migrated with canonical=None keyword-only parameter for backward compatibility
- key_stats_context: revenue, market_cap, employees, exchange from canonical
- beta_report: revenue, market_cap, stock_price, employees, 52w high/low from canonical
- company_profile: exchange, employee_count_fmt from canonical
- scorecard_context: metrics_strip market_cap, revenue, employees from canonical
- company_exec_summary: snapshot exchange, market_cap, revenue, employees from canonical
- Assembly wrappers (assembly_dossier, assembly_beta_report) pass _canonical_obj from context
- 10 new integration tests covering backward compat, canonical consumption, and end-to-end flow
- All 24 tests pass (14 from Plan 01 + 10 new)

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire canonical into assembly_registry** - `b2d42ce5` (feat)
2. **Task 2: Migrate 5 builders + integration tests** - `cb2ddbd3` (feat)

## Files Created/Modified

- `src/do_uw/stages/render/context_builders/assembly_registry.py` - Canonical metrics computation in build_html_context
- `src/do_uw/stages/render/context_builders/key_stats_context.py` - canonical kwarg for revenue, market_cap, employees, exchange
- `src/do_uw/stages/render/context_builders/beta_report.py` - canonical kwarg for revenue, market_cap, price, employees, 52w
- `src/do_uw/stages/render/context_builders/company_profile.py` - canonical kwarg for exchange, employees
- `src/do_uw/stages/render/context_builders/scorecard_context.py` - canonical kwarg for metrics_strip
- `src/do_uw/stages/render/context_builders/company_exec_summary.py` - canonical kwarg for snapshot
- `src/do_uw/stages/render/context_builders/assembly_dossier.py` - Pass _canonical_obj to key_stats and scorecard
- `src/do_uw/stages/render/context_builders/assembly_beta_report.py` - Pass _canonical_obj to beta_report
- `tests/test_canonical_metrics.py` - 10 new integration tests (now 24 total)

## Decisions Made

- **Canonical passed via keyword param, not BuilderFn signature change**: Avoids changing the registered builder type alias. Assembly wrappers extract canonical from context dict and pass it explicitly to inner builder functions.
- **All old extraction functions preserved**: _extract_revenue(), extract_xbrl_revenue(), inline XBRL loops in scorecard_context all remain as fallback paths. This ensures md_renderer (which doesn't compute canonical) continues to work unchanged.
- **company_profile and company_exec_summary get canonical via param, not context**: These are called from md_renderer.py which doesn't have the context dict. The canonical=None default means they use legacy extraction in the md_renderer path.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed NameError in _extract_litigation_legacy**
- **Found during:** Task 2
- **Issue:** `_extract_litigation_legacy(ext)` referenced `state` variable that was not in scope (neither a parameter nor a closure variable). Pre-existing bug that would crash when key_stats_context was called.
- **Fix:** Added `state` as optional parameter to `_extract_litigation_legacy()` and passed it from the calling site.
- **Files modified:** key_stats_context.py
- **Committed in:** cb2ddbd3

---

**Total deviations:** 1 auto-fixed (Rule 1 - pre-existing bug)
**Impact on plan:** Minimal. Bug fix was necessary for tests to pass.

## Issues Encountered

None.

## Known Stubs

None -- all canonical reads are wired to real resolver data and fall back to legacy extraction.

## User Setup Required

None.

## Next Phase Readiness

- Canonical registry fully wired: computed once, consumed by 5 builders
- Remaining builders (governance, litigation, financial health, etc.) can be migrated in future plans using same pattern
- Template output unchanged -- canonical values match legacy extraction for same data
- md_renderer path continues to work unchanged (canonical=None fallback)

## Self-Check: PASSED
