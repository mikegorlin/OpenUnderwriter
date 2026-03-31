---
phase: 97-external-environment-assessment
plan: 01
subsystem: extract
tags: [brain-signals, environment, regulatory, geopolitical, esg, cyber, macro]

requires:
  - phase: 96-structural-complexity-extraction
    provides: signal YAML v3 schema pattern and signal_mappers wiring pattern
provides:
  - 5 ENVR brain signal YAML definitions with v3 schema
  - Environment extraction module computing 5 signal scores from state data
  - ENVR.* prefix routing in signal_mappers.py
  - external_environment group in output manifest with stub template
affects: [98-sector-risk, 100-display, signal-evaluation]

tech-stack:
  added: []
  patterns: [environment-signal-extraction, multi-source-score-computation]

key-files:
  created:
    - src/do_uw/brain/signals/env/environment.yaml
    - src/do_uw/stages/extract/environment_assessment.py
    - src/do_uw/templates/html/sections/company/external_environment.html.j2
    - tests/test_environment_signals.py
  modified:
    - src/do_uw/stages/analyze/signal_mappers.py
    - src/do_uw/brain/output_manifest.yaml

key-decisions:
  - "Score scales use 0-3 for categorical signals (geopolitical, esg_gap, cyber) and 0-N count for intensity signals (regulatory, macro)"
  - "Geopolitical uses OFAC sanctioned countries list for RED threshold, elevated risk list for YELLOW"
  - "LLM extraction data accessed via state.acquired_data.llm_extractions pattern (same as company_profile.py)"
  - "Signal mapper uses lightweight state proxy to bridge mapper arguments to extraction function"

patterns-established:
  - "ENVR prefix routing pattern: lazy import of extraction module inside mapper function"
  - "Environment score computation: each signal has a dedicated _compute_* function returning score + details dict"

requirements-completed: [ENVR-01, ENVR-02, ENVR-03, ENVR-04, ENVR-05]

duration: 27min
completed: 2026-03-10
---

# Phase 97 Plan 01: External Environment Assessment Summary

**5 ENVR brain signals (regulatory intensity, geopolitical, ESG gap, cyber risk, macro sensitivity) with extraction logic computing scores from risk factors, geographic footprint, litigation, and LLM data**

## Performance

- **Duration:** 27 min
- **Started:** 2026-03-10T04:55:30Z
- **Completed:** 2026-03-10T05:22:44Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Created 5 ENVR brain signal YAML definitions with full v3 schema (acquisition, evaluation, presentation blocks)
- Built extraction module that computes numeric scores from existing state data (risk factors, geographic footprint, litigation, LLM extraction)
- Wired ENVR.* prefix routing in signal_mappers.py with state proxy pattern
- 18 unit tests covering all 5 extraction functions + mapper routing

## Task Commits

Each task was committed atomically:

1. **Task 1: Create ENVR brain signal YAML definitions** - `d5303e7` (feat)
2. **Task 2: RED - Failing tests** - `588c224` (test)
3. **Task 2: GREEN - Implementation + mapper wiring** - `fd2d1fd` (feat)

## Files Created/Modified
- `src/do_uw/brain/signals/env/environment.yaml` - 5 ENVR signal definitions with v3 schema
- `src/do_uw/stages/extract/environment_assessment.py` - Extraction logic for 5 environment signals
- `src/do_uw/stages/analyze/signal_mappers.py` - ENVR.* prefix routing + _map_environment_fields
- `src/do_uw/brain/output_manifest.yaml` - Added external_environment group
- `src/do_uw/templates/html/sections/company/external_environment.html.j2` - Stub rendering template
- `tests/test_environment_signals.py` - 18 unit tests for extraction + routing

## Decisions Made
- Score scales: 0-3 for categorical signals (sanctioned=3, high_risk=1-2, clear=0) and 0-N for count signals (regulators, macro dimensions)
- Geopolitical uses OFAC sanctioned countries (Cuba, Iran, North Korea, Syria, Russia, Belarus, Venezuela, Myanmar) for RED; 10 elevated-risk countries for YELLOW
- ESG gap detects commitment-action divergence by cross-referencing ESG risk factors against ESG-related litigation keywords
- Cyber risk checks text_signals for breach indicators (key names and values) in addition to CYBER risk factor severity
- Macro sensitivity counts distinct dimensions from LLM fields (interest_rate_risk, currency_risk) plus FINANCIAL risk factor keyword scanning

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added external_environment group to output manifest**
- **Found during:** Task 2 (test suite verification)
- **Issue:** brain_contract test requires all signal groups to exist in output_manifest.yaml; `external_environment` group was missing
- **Fix:** Added external_environment group entry to manifest + created stub HTML template
- **Files modified:** src/do_uw/brain/output_manifest.yaml, src/do_uw/templates/html/sections/company/external_environment.html.j2
- **Verification:** TestSignalGroupAssignment::test_group_values_exist_in_manifest passes
- **Committed in:** fd2d1fd (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Manifest entry needed for signal group contract compliance. No scope creep.

## Issues Encountered
- Pre-existing test failures (5) in brain contract tests unrelated to this plan: BIZ.OPS threshold_provenance, corporate_events missing template, signal group count stale, v2_migration checks. These are from Phases 94-96 and do not affect this plan.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- 5 ENVR signals ready for evaluation by the check engine (will fire once ENVR prefix is recognized)
- Manifest group + stub template ready for Phase 100 (Display) to flesh out rendering
- Phase 98 (Sector Risk) can use regulatory_intensity and macro_sensitivity as inputs

---
*Phase: 97-external-environment-assessment*
*Completed: 2026-03-10*
