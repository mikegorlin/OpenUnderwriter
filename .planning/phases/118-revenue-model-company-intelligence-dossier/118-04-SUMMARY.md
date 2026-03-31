---
phase: 118-revenue-model-company-intelligence-dossier
plan: 04
subsystem: render
tags: [context-builders, dossier, jinja2, formatting, css-classes]

# Dependency graph
requires:
  - phase: 118-01
    provides: DossierData Pydantic models (8 model classes)
  - phase: 118-03
    provides: Enriched dossier data with D&O commentary and risk levels
provides:
  - 8 context builders transforming DossierData into template-ready dicts
  - CSS class mapping for risk/probability/complexity levels
  - Availability flags for graceful template degradation
affects: [118-05, 118-06]

# Tech tracking
tech-stack:
  added: []
  patterns: [dossier-context-builder-pattern, availability-flag-pattern, css-risk-class-mapping]

key-files:
  created:
    - src/do_uw/stages/render/context_builders/dossier_what_company_does.py
    - src/do_uw/stages/render/context_builders/dossier_money_flows.py
    - src/do_uw/stages/render/context_builders/dossier_revenue_card.py
    - src/do_uw/stages/render/context_builders/dossier_segments.py
    - src/do_uw/stages/render/context_builders/dossier_unit_economics.py
    - src/do_uw/stages/render/context_builders/dossier_waterfall.py
    - src/do_uw/stages/render/context_builders/dossier_emerging_risks.py
    - src/do_uw/stages/render/context_builders/dossier_asc606.py
    - tests/stages/render/test_dossier_context_builders.py
  modified: []

key-decisions:
  - "Followed forward_risk_map.py pattern exactly: keyword-only signal_results, availability flags, CSS class dicts"
  - "Zero evaluative logic in all builders -- D&O commentary passed through from enrichment stage"

patterns-established:
  - "Dossier context builder: extract_{section}(state, *, signal_results=None) -> dict with {section}_available flag"
  - "CSS risk class mapping: _RISK_CSS dict maps HIGH/MEDIUM/LOW to risk-high/risk-medium/risk-low"

requirements-completed: [DOSSIER-01, DOSSIER-02, DOSSIER-03, DOSSIER-04, DOSSIER-05, DOSSIER-06, DOSSIER-08, DOSSIER-09]

# Metrics
duration: 3min
completed: 2026-03-20
---

# Phase 118 Plan 04: Dossier Context Builders Summary

**8 pure-formatter context builders bridging DossierData to Jinja2 templates with CSS risk classes and availability flags**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-20T13:39:48Z
- **Completed:** 2026-03-20T13:43:16Z
- **Tasks:** 2
- **Files created:** 9

## Accomplishments
- 8 context builders following the established forward_risk_map.py pattern
- CSS class mapping for risk levels (HIGH/MEDIUM/LOW) across revenue card, segments, concentration, emerging risks, and ASC 606
- 33 tests covering output shape, CSS mapping, availability flags, and graceful empty-data handling
- Zero evaluative logic -- all D&O commentary passes through from enrichment

## Task Commits

Each task was committed atomically:

1. **Task 1: Create 8 dossier context builders** - `f2cd0995` (feat)
2. **Task 2: Create context builder tests** - `cc0e04e1` (test)

## Files Created/Modified
- `src/do_uw/stages/render/context_builders/dossier_what_company_does.py` - Business description + core D&O exposure formatter
- `src/do_uw/stages/render/context_builders/dossier_money_flows.py` - Revenue flow diagram + narrative formatter
- `src/do_uw/stages/render/context_builders/dossier_revenue_card.py` - Revenue model card rows with CSS risk classes
- `src/do_uw/stages/render/context_builders/dossier_segments.py` - Segment dossiers + concentration dimensions formatter
- `src/do_uw/stages/render/context_builders/dossier_unit_economics.py` - Unit economics metrics + narrative formatter
- `src/do_uw/stages/render/context_builders/dossier_waterfall.py` - YoY revenue waterfall rows + narrative formatter
- `src/do_uw/stages/render/context_builders/dossier_emerging_risks.py` - Emerging risks with probability CSS classes
- `src/do_uw/stages/render/context_builders/dossier_asc606.py` - ASC 606 elements with complexity CSS classes
- `tests/stages/render/test_dossier_context_builders.py` - 20 test functions (33 test cases with parametrize)

## Decisions Made
- Followed forward_risk_map.py pattern exactly with keyword-only signal_results parameter
- Used na_if_none() consistently for all potentially-None values (per project safe_float/na_if_none rules)
- CSS class mapping via module-level dicts rather than inline conditionals

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- AnalysisState requires `ticker` field -- fixed test fixture to include `ticker="TEST"` (trivial fix)

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All 8 context builders ready for Jinja2 template consumption (118-05)
- Availability flags enable graceful degradation when dossier data is partial
- CSS classes ready for template styling

## Self-Check: PASSED

All 9 created files verified on disk. Both task commits (f2cd0995, cc0e04e1) verified in git log.

---
*Phase: 118-revenue-model-company-intelligence-dossier*
*Completed: 2026-03-20*
