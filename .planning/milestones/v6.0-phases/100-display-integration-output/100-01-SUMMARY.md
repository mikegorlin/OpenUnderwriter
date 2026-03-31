---
phase: 100-display-integration-output
plan: 01
subsystem: render
tags: [jinja2, templates, context-builders, manifest, business-model, corporate-events, structural-complexity]

# Dependency graph
requires:
  - phase: 93-business-model-extraction
    provides: BMOD signal data and extract_business_model() builder
  - phase: 95-corporate-event-extraction
    provides: BIZ.EVENT signal data in text_signals and xbrl_forensics
  - phase: 96-structural-complexity-extraction
    provides: BIZ.STRUC signal data in text_signals
  - phase: 97-environment-assessment
    provides: ENVR signal context builder pattern
  - phase: 99-operational-scoring-signals
    provides: BIZ.OPS composite score context builder pattern
provides:
  - Reordered manifest business_profile groups matching underwriting-standard layout
  - _build_corporate_events() context builder for M&A, IPO, restatements, capital/business changes
  - _build_structural_complexity() context builder for 5 text signal opacity dimensions
  - Full professional templates for business_model, corporate_events, structural_complexity
  - Updated company.html.j2 legacy fallback with correct ordering
affects: [render, html-output, worksheet-quality]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Context builder (dict, bool) tuple pattern for new dimension groups"
    - "Badge-pill CSS pattern (bg-red-700/bg-amber-500/bg-emerald-600) for level indicators"
    - "Zero-threshold templates consuming pre-computed levels from context builders"

key-files:
  created: []
  modified:
    - src/do_uw/brain/output_manifest.yaml
    - src/do_uw/stages/render/context_builders/company.py
    - src/do_uw/templates/html/sections/company/business_model.html.j2
    - src/do_uw/templates/html/sections/company/corporate_events.html.j2
    - src/do_uw/templates/html/sections/company/structural_complexity.html.j2
    - src/do_uw/templates/html/sections/company.html.j2

key-decisions:
  - "Corporate events reads M&A data from analysis.xbrl_forensics (dict or Pydantic) with dual-path handling"
  - "Structural complexity uses text_signals mention_count for all 5 dimensions with >=3/>=1 thresholds"
  - "Disclosure complexity composite score = risk_factor_count + critical_accounting_count + fls_density"
  - "Corporate events render_as changed from check_summary to kv_table to match actual template pattern"

patterns-established:
  - "All new dimension context builders return (dict, bool) tuple consistent with environment/sector patterns"
  - "Template badge pattern: level -> color mapping in context builder, template uses pre-computed color class"

requirements-completed: [RENDER-01, RENDER-02]

# Metrics
duration: 4min
completed: 2026-03-10
---

# Phase 100 Plan 01: Display Integration & Output Summary

**Reordered Business Profile manifest to underwriting-standard layout and upgraded 3 placeholder templates to full professional rendering with badge indicators and KV tables**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-10T18:12:25Z
- **Completed:** 2026-03-10T18:16:55Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Manifest business_profile groups reordered: Identity > Business Model > Operations > Events > Environment > Sector > Structure > Summary > Alerts
- Business model template upgraded with all 6 BMOD dimensions (revenue model, concentration, key person, lifecycle, disruption, margins)
- Corporate events template with M&A risk scoring, IPO exposure window, restatement history, capital/business changes
- Structural complexity template with 5 opacity dimensions (disclosure, non-GAAP, related parties, OBS, holding structure)
- Two new context builders (_build_corporate_events, _build_structural_complexity) wired into extract_company()

## Task Commits

Each task was committed atomically:

1. **Task 1: Reorder manifest groups + add context builders** - `c0bb497` (feat)
2. **Task 2: Upgrade placeholder templates to full rendering** - `381eb7a` (feat)

## Files Created/Modified
- `src/do_uw/brain/output_manifest.yaml` - Reordered business_profile groups with section comments
- `src/do_uw/stages/render/context_builders/company.py` - Added _build_corporate_events() and _build_structural_complexity(), wired into extract_company()
- `src/do_uw/templates/html/sections/company/business_model.html.j2` - Full 6-dimension template with badge indicators and data tables
- `src/do_uw/templates/html/sections/company/corporate_events.html.j2` - Full M&A/IPO/restatement/capital/business changes template
- `src/do_uw/templates/html/sections/company/structural_complexity.html.j2` - Full 5-dimension opacity template with level badges
- `src/do_uw/templates/html/sections/company.html.j2` - Updated legacy fallback ordering to match manifest

## Decisions Made
- Corporate events reads M&A data from analysis.xbrl_forensics with dual-path handling (dict or Pydantic model) since the field can be either depending on serialization state
- Structural complexity disclosure score is a composite of risk_factor_count + critical_accounting_count + fls_density from the disclosure_complexity text signal
- Changed corporate_events render_as from check_summary to kv_table to match actual template pattern (badge-pill KV rows)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pre-existing test failure: `test_no_orphaned_group_templates` fails due to `external_environment.html.j2` orphan file (superseded by `environment_assessment.html.j2` in manifest). Not caused by this plan's changes -- logged as out-of-scope.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All 6 v6.0 dimension groups now have full professional templates
- Business Profile section ready for visual review with real pipeline data
- Pre-existing orphan template (external_environment.html.j2) should be cleaned up in a future maintenance pass

---
*Phase: 100-display-integration-output*
*Completed: 2026-03-10*
