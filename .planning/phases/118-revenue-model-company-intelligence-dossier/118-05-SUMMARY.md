---
phase: 118-revenue-model-company-intelligence-dossier
plan: 05
subsystem: render
tags: [jinja2, templates, dossier, d-and-o-risk, html]

# Dependency graph
requires:
  - phase: 118-01
    provides: DossierData Pydantic models and context builder output shapes
provides:
  - 9 Jinja2 templates (1 section wrapper + 8 subsections) for Company Intelligence Dossier
  - 19 template rendering tests with fixture data
affects: [118-06, render-pipeline]

# Tech tracking
tech-stack:
  added: []
  patterns: [dossier context variable naming (dossier_what/dossier_flows/dossier_card/etc), do-callout CSS class]

key-files:
  created:
    - src/do_uw/templates/html/sections/dossier.html.j2
    - src/do_uw/templates/html/sections/dossier/what_company_does.html.j2
    - src/do_uw/templates/html/sections/dossier/money_flows.html.j2
    - src/do_uw/templates/html/sections/dossier/revenue_model_card.html.j2
    - src/do_uw/templates/html/sections/dossier/revenue_segments.html.j2
    - src/do_uw/templates/html/sections/dossier/unit_economics.html.j2
    - src/do_uw/templates/html/sections/dossier/revenue_waterfall.html.j2
    - src/do_uw/templates/html/sections/dossier/emerging_risk_radar.html.j2
    - src/do_uw/templates/html/sections/dossier/asc_606.html.j2
    - tests/stages/render/test_dossier_templates.py
  modified: []

key-decisions:
  - "Context variable naming: dossier_what, dossier_flows, dossier_card, dossier_segments, dossier_unit, dossier_waterfall, dossier_risks, dossier_asc"
  - "do-callout class for D&O exposure emphasis with border-l-4 border-risk-red styling"

patterns-established:
  - "Dossier guard pattern: {% set var = context_name | default({}) %} {% if var.get('available_flag', false) %}"
  - "D&O Risk column in every data table -- rendered as-is from context builder, zero template logic"

requirements-completed: [DOSSIER-01, DOSSIER-02, DOSSIER-03, DOSSIER-04, DOSSIER-05, DOSSIER-06, DOSSIER-08, DOSSIER-09]

# Metrics
duration: 4min
completed: 2026-03-20
---

# Phase 118 Plan 05: Dossier Templates Summary

**9 Jinja2 templates for Company Intelligence Dossier with D&O Risk columns in every data table, zero evaluative logic**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-20T13:39:49Z
- **Completed:** 2026-03-20T13:43:49Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- 9 Jinja2 templates created: 1 section wrapper + 8 subsections covering business description, money flows, revenue model card, revenue segments, unit economics, revenue waterfall, emerging risk radar, and ASC 606
- Every data table template includes a D&O Risk column rendering do_risk text as-is
- Revenue flow diagram renders in monospace pre block
- 19 rendering tests validate all templates with realistic fixture data

## Task Commits

Each task was committed atomically:

1. **Task 1: Create 9 dossier Jinja2 templates** - `20a872a9` (feat)
2. **Task 2: Create template rendering tests** - `c2b06884` (test)

## Files Created/Modified
- `src/do_uw/templates/html/sections/dossier.html.j2` - Section wrapper including all 8 subsection templates
- `src/do_uw/templates/html/sections/dossier/what_company_does.html.j2` - Business description + D&O exposure callout
- `src/do_uw/templates/html/sections/dossier/money_flows.html.j2` - Revenue flow diagram in pre block + narrative
- `src/do_uw/templates/html/sections/dossier/revenue_model_card.html.j2` - Attribute/Value/D&O Risk table
- `src/do_uw/templates/html/sections/dossier/revenue_segments.html.j2` - Segment breakdown + concentration assessment
- `src/do_uw/templates/html/sections/dossier/unit_economics.html.j2` - Metrics table with benchmark + D&O Risk
- `src/do_uw/templates/html/sections/dossier/revenue_waterfall.html.j2` - Growth decomposition table
- `src/do_uw/templates/html/sections/dossier/emerging_risk_radar.html.j2` - Risk table with probability/impact/D&O factor
- `src/do_uw/templates/html/sections/dossier/asc_606.html.j2` - ASC 606 elements + billings narrative
- `tests/stages/render/test_dossier_templates.py` - 19 rendering tests with fixture data

## Decisions Made
- Context variable naming convention: `dossier_what`, `dossier_flows`, `dossier_card`, `dossier_segments`, `dossier_unit`, `dossier_waterfall`, `dossier_risks`, `dossier_asc` -- prefixed with `dossier_` for namespace isolation
- Used `do-callout` CSS class with `border-l-4 border-risk-red` for D&O exposure emphasis in what_company_does template

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Templates ready for integration with context builders from 118-04
- Pipeline wiring (118-06) can include dossier section in worksheet output
- CSS class `do-callout` may need addition to project stylesheet if not already present

---
*Phase: 118-revenue-model-company-intelligence-dossier*
*Completed: 2026-03-20*
