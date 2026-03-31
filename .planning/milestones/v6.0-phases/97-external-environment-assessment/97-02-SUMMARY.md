---
phase: 97-external-environment-assessment
plan: 02
subsystem: render
tags: [environment-signals, manifest, context-builder, html-template, kv-table]

requires:
  - phase: 97-external-environment-assessment
    provides: 5 ENVR signal YAML definitions + extraction module + signal_mappers routing
provides:
  - Manifest wiring for external_environment group with environment_assessment template
  - Extraction pipeline integration storing ENVR results in text_signals
  - Context builder formatting 5 signals with score/level/details structure
  - HTML template rendering environment signals with badge-pill indicators
affects: [100-display, render-pipeline]

tech-stack:
  added: []
  patterns: [text-signals-transport, env-signal-context-builder]

key-files:
  created:
    - src/do_uw/templates/html/sections/company/environment_assessment.html.j2
  modified:
    - src/do_uw/brain/output_manifest.yaml
    - src/do_uw/stages/extract/company_profile.py
    - src/do_uw/stages/render/context_builders/company.py
    - src/do_uw/stages/extract/environment_assessment.py

key-decisions:
  - "Environment data transported via text_signals dict to avoid new model fields"
  - "Score-to-level mapping: >= 3 HIGH, >= 1 MODERATE, else LOW"
  - "Badge styling uses existing badge-pill CSS classes (bg-red-700, bg-amber-500, bg-emerald-600)"

patterns-established:
  - "text_signals as transport for cross-cutting signal data: extraction stores dict, context builder reads and formats"
  - "_format_env_signal helper for uniform signal-to-template data transformation"

requirements-completed: [ENVR-01, ENVR-02, ENVR-03, ENVR-04, ENVR-05]

duration: 4min
completed: 2026-03-10
---

# Phase 97 Plan 02: External Environment Assessment Wiring Summary

**Environment signals wired end-to-end: manifest group, extraction pipeline integration, context builder formatting, and HTML template with red/amber/green badge indicators**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-10T05:24:58Z
- **Completed:** 2026-03-10T05:29:39Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Updated manifest external_environment group to reference new environment_assessment.html.j2 template
- Wired extract_environment_signals() call into company_profile.py extraction pipeline, storing results in text_signals
- Built context builder with _format_env_signal() and _build_environment_assessment() helpers that map numeric scores to HIGH/MODERATE/LOW levels with detail strings
- Created HTML template using existing badge-pill CSS patterns for consistent visual treatment

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire manifest, extraction pipeline, and context builder** - `a6c4bb9` (feat)
2. **Task 2: Create HTML template + defensive extraction fixes** - `fde59b8` (feat)

## Files Created/Modified
- `src/do_uw/brain/output_manifest.yaml` - Updated external_environment group template reference
- `src/do_uw/stages/extract/company_profile.py` - Added extract_environment_signals() call after LLM enrichment
- `src/do_uw/stages/render/context_builders/company.py` - Added _format_env_signal(), _build_environment_assessment(), environment_assessment + has_environment_data in output dict
- `src/do_uw/templates/html/sections/company/environment_assessment.html.j2` - New template with 5 signal rows and badge-pill indicators
- `src/do_uw/stages/extract/environment_assessment.py` - Made risk_factors access defensive with getattr

## Decisions Made
- Transport environment data via state.extracted.text_signals["environment_assessment"] dict to avoid adding new fields to ExtractedData model
- Score-to-level mapping thresholds: score >= 3 -> HIGH, score >= 1 -> MODERATE, else LOW (consistent across all 5 signals)
- Used existing badge-pill CSS classes from badges.html.j2 (bg-red-700, bg-amber-500, bg-emerald-600) for visual consistency

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed AttributeError when state.extracted is None**
- **Found during:** Task 2 (test verification)
- **Issue:** extract_environment_signals accessed state.extracted.risk_factors directly, which crashes when state.extracted is None (as in some integration tests)
- **Fix:** Used getattr(state.extracted, "risk_factors", None) or [] pattern for all 4 risk_factors accesses; added try/except guard in company_profile.py caller
- **Files modified:** src/do_uw/stages/extract/environment_assessment.py, src/do_uw/stages/extract/company_profile.py
- **Verification:** 11 previously-failing integration tests now pass; 18 environment signal tests still pass
- **Committed in:** fde59b8 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Defensive access pattern needed for correctness when extraction runs early. No scope creep.

## Issues Encountered
None beyond the auto-fixed deviation above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 5 ENVR signals now wired end-to-end: YAML -> extraction -> text_signals -> context builder -> HTML template
- Phase 100 (Display) can enhance the template layout further
- Phase 98 (Sector Risk) can read environment scores from text_signals for sector-specific assessment

---
*Phase: 97-external-environment-assessment*
*Completed: 2026-03-10*
