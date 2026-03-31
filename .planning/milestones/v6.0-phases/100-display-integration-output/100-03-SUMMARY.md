---
phase: 100-display-integration-output
plan: 03
subsystem: testing
tags: [ci, contract-tests, brain-portability, template-purity, manifest-coverage]

requires:
  - phase: 100-01
    provides: manifest reordering and v6 signal template mappings
  - phase: 100-02
    provides: v6 subsection renderers and context builders
provides:
  - CI contract tests enforcing brain portability principle
  - Signal portability gate (acquisition implies evaluation + presentation)
  - Manifest-to-template coverage validation
  - Template purity enforcement (zero hardcoded thresholds)
affects: [brain-signals, templates, manifest]

tech-stack:
  added: []
  patterns: [collect-and-assert test pattern, regex-based template scanning, safe-pattern exclusion lists]

key-files:
  created:
    - tests/brain/test_signal_portability.py
    - tests/brain/test_manifest_coverage.py
    - tests/brain/test_template_purity.py
  modified:
    - tests/stages/render/test_section_renderer.py

key-decisions:
  - "BASE.* signals exempt from portability check -- they are data-fetching signals without evaluation/presentation"
  - "Template purity allows presence checks (> 0), length checks, loop counters, and filter args with numbers"
  - "Removed orphaned external_environment.html.j2 (superseded by environment_assessment.html.j2)"

patterns-established:
  - "Portability gate: signals with acquisition blocks must have evaluation + presentation"
  - "Template purity scanning: regex-based detection with safe-pattern exclusion list"

requirements-completed: [RENDER-05, RENDER-06, RENDER-07]

duration: 10min
completed: 2026-03-10
---

# Phase 100 Plan 03: CI Contract Tests Summary

**Three CI contract tests enforcing brain portability: signal completeness gate, manifest-template coverage, and zero-threshold template purity**

## Performance

- **Duration:** 10 min
- **Started:** 2026-03-10T18:26:52Z
- **Completed:** 2026-03-10T18:37:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Created test_signal_portability.py: validates 48 v6 signals with acquisition blocks also have evaluation + presentation
- Created test_manifest_coverage.py: validates all 100+ manifest groups resolve to existing template files
- Created test_template_purity.py: scans 18 company templates for hardcoded thresholds with zero violations
- Removed orphaned external_environment.html.j2 template and updated fragment count assertions
- All 901 render + brain contract tests pass

## Task Commits

1. **Task 1: CI contract tests for portability, coverage, and purity** - `b7c4efa` (test)
2. **Task 2: Verify render audit coverage and fix fragment count assertions** - `113246d` (chore)

## Files Created/Modified
- `tests/brain/test_signal_portability.py` - Signal portability gate: v6 signals must have acquisition + evaluation + presentation
- `tests/brain/test_manifest_coverage.py` - Manifest coverage: every group maps to existing template file
- `tests/brain/test_template_purity.py` - Template purity: zero hardcoded thresholds in company templates
- `tests/stages/render/test_section_renderer.py` - Updated company fragment count 19 -> 18

## Decisions Made
- BASE.* signals (filings, XBRL, market, etc.) exempt from portability check since they are foundational data-fetching signals that acquire raw data for other signals to consume, intentionally without evaluation/presentation blocks
- Template purity regex allows: presence checks (> 0, != 0), collection length checks, loop counters, Jinja2 filter numeric args (truncate, batch, round), CSS class numbers, colspan/rowspan
- Removed orphaned external_environment.html.j2 which was superseded by environment_assessment.html.j2 in Phase 97/100

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Removed orphaned external_environment.html.j2**
- **Found during:** Task 2 (facet audit verification)
- **Issue:** external_environment.html.j2 on disk but not referenced by manifest (superseded by environment_assessment.html.j2)
- **Fix:** Deleted orphan file, updated company fragment count assertion from 19 to 18
- **Files modified:** src/do_uw/templates/html/sections/company/external_environment.html.j2 (deleted), tests/stages/render/test_section_renderer.py
- **Verification:** test_template_facet_audit.py now passes (110 tests)
- **Committed in:** 113246d

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Orphan removal necessary for facet audit test to pass. No scope creep.

## Issues Encountered
- 5 pre-existing test failures in brain/ tests unrelated to this plan: SECT.hazard_tier provenance source not in allowed list, SECT.claim_patterns/regulatory_overlay invalid signal_class, v2 migration count drift. All pre-existing, not caused by plan changes.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All v6.0 CI contract tests in place
- Brain portability principle enforced by automated tests
- Pre-existing test failures (5) in brain/ should be addressed in future maintenance

---
*Phase: 100-display-integration-output*
*Completed: 2026-03-10*
