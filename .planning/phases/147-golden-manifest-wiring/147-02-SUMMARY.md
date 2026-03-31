---
phase: 147-golden-manifest-wiring
plan: 02
subsystem: rendering
tags: [manifest, jinja2, suppression-guards, alt-data, template-wiring]

# Dependency graph
requires:
  - phase: 147-golden-manifest-wiring
    provides: ManifestClassification engine, classify_manifest_groups(), build_manifest_audit_context()
provides:
  - Suppression guards on all unguarded display_only templates
  - 3 stub templates converted to zero-output suppressed comments
  - Alt-data context builders individually wrapped for resilience
  - manifest_audit dict available in render context
  - All 163 manifest groups classified (45 renders, 6 wired, 112 suppressed)
affects: [rendering, manifest-audit, template-quality]

# Tech tracking
tech-stack:
  added: []
  patterns: [top-level suppression guards for display_only templates, individual try/except alt-data wiring]

key-files:
  created: []
  modified:
    - src/do_uw/stages/render/context_builders/assembly_dossier.py
    - src/do_uw/templates/html/sections/company/subsidiary_structure.html.j2
    - src/do_uw/templates/html/sections/company/workforce_distribution.html.j2
    - src/do_uw/templates/html/sections/company/operational_resilience.html.j2
    - src/do_uw/templates/html/sections/red_flags/triggered_flags.html.j2
    - src/do_uw/templates/html/sections/market/stock_charts.html.j2
    - src/do_uw/templates/html/sections/market/ownership_chart.html.j2
    - src/do_uw/templates/html/sections/financial/peer_percentiles.html.j2
    - src/do_uw/templates/html/sections/financial/quarterly_updates.html.j2
    - src/do_uw/templates/html/sections/executive_risk/insider_trading.html.j2
    - src/do_uw/templates/html/appendices/meeting_prep.html.j2

key-decisions:
  - "Only 7 templates truly produced DOM before guards (not 70 as estimated) -- most display_only templates already had effective set-then-if guards"
  - "Alt-data builders split into individual try/except blocks for resilience -- single failure no longer kills all 4"
  - "manifest_audit runs after all other builders so classification reflects fully populated context"

patterns-established:
  - "Top-level suppression guard: first non-comment line must be {% if %} for display_only templates"
  - "Individual try/except with has_*_data=False fallback for alt-data context builders"

requirements-completed: [WIRE-02, WIRE-03, WIRE-04]

# Metrics
duration: 12min
completed: 2026-03-28
---

# Phase 147 Plan 02: Template Wiring & Suppression Guards Summary

**Suppression guards on 10 templates (3 stubs + 7 unguarded), individually-wrapped alt-data context builders, and manifest_audit wired into render pipeline -- 163 groups: 45 renders, 6 wired, 112 suppressed**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-28T19:22:56Z
- **Completed:** 2026-03-28T19:34:56Z
- **Tasks:** 3
- **Files modified:** 11

## Accomplishments
- Converted 3 stub templates to zero-output suppression comments (subsidiary_structure, workforce_distribution, operational_resilience)
- Added top-level suppression guards to 7 templates that produced DOM elements before any data check
- Split alt-data context builder wiring from single try/except to 4 individual blocks with has_*_data=False fallbacks
- Wired build_manifest_audit_context() into render pipeline as final builder step
- All 163 manifest groups classified with zero unclassified: 45 renders, 6 wired, 112 suppressed

## Task Commits

1. **Task 1: Add suppression guards + convert stubs** - `ee0ac4c1` (feat)
2. **Task 2: Wire alt-data context + manifest audit** - `cb6a7571` (feat)
3. **Task 3: Final validation** - validation only, no commit needed

## Files Created/Modified
- `src/do_uw/stages/render/context_builders/assembly_dossier.py` - Split alt-data wiring into individual try/except blocks; added manifest_audit context builder call
- `src/do_uw/templates/html/sections/company/subsidiary_structure.html.j2` - Stub converted to suppressed comment
- `src/do_uw/templates/html/sections/company/workforce_distribution.html.j2` - Stub converted to suppressed comment
- `src/do_uw/templates/html/sections/company/operational_resilience.html.j2` - Stub converted to suppressed comment
- `src/do_uw/templates/html/sections/red_flags/triggered_flags.html.j2` - Added outer {% if %} guard wrapping div
- `src/do_uw/templates/html/sections/market/stock_charts.html.j2` - Added chart_files guard
- `src/do_uw/templates/html/sections/market/ownership_chart.html.j2` - Added chart_files.get('ownership') guard
- `src/do_uw/templates/html/sections/financial/peer_percentiles.html.j2` - Moved h3 inside existing if guard
- `src/do_uw/templates/html/sections/financial/quarterly_updates.html.j2` - Added outer {% if qu_list %} guard
- `src/do_uw/templates/html/sections/executive_risk/insider_trading.html.j2` - Added outer {% if exec_signals %} guard
- `src/do_uw/templates/html/appendices/meeting_prep.html.j2` - Added {% if questions %} guard wrapping section

## Decisions Made
- Research found only 7 templates truly produced DOM before any guard (not 70 as estimated). The remaining 59 display_only templates already had effective `{% set x %}{% if x %}` patterns that suppress correctly.
- Split alt-data builders into individual try/except blocks so ESG failure doesn't prevent tariff/AI/peer-SCA from rendering.
- Manifest audit added as the final builder call so it classifies against fully populated context.

## Deviations from Plan

### Scope Adjustment

**1. [Observation] Fewer templates needed guards than estimated**
- **Plan estimated:** ~70 unguarded display_only templates
- **Actual finding:** Only 7 templates produced DOM before any guard. The other 59 already had effective `{% set x %}{% if x %}` patterns.
- **Impact:** Less code changed, same correctness outcome. All display_only templates now produce zero DOM when data is absent.

---

**Total deviations:** 1 scope observation (reduced scope, no quality impact)
**Impact on plan:** Positive -- fewer changes means lower regression risk.

## Issues Encountered
- 2 pre-existing test failures in `test_manifest_rendering.py` (section order mismatch) and `test_119_integration.py` (stale import check) -- not caused by this plan's changes. Both fail identically on clean main branch.

## Known Stubs
None -- all code is fully functional.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 163 manifest groups classified: 45 renders, 6 wired, 112 suppressed
- manifest_audit dict available in render context for audit trail templates
- Alt-data context (ESG, tariff, AI-washing, peer SCA) individually resilient
- Phase 147 golden manifest wiring is complete

---
*Phase: 147-golden-manifest-wiring*
*Completed: 2026-03-28*
