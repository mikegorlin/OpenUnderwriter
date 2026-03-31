---
phase: 148-question-driven-underwriting-section
plan: 01
subsystem: render
tags: [answerers, underwriting-questions, registry-pattern, d&o-analysis]

requires:
  - phase: 145
    provides: "brain/questions YAML framework, initial 8 answerers, uw_questions.py context builder"
provides:
  - "ANSWERER_REGISTRY with 55 dedicated answerer functions"
  - "answerers/ subpackage with 8 domain files + registry + helpers"
  - "Refactored uw_questions.py using registry pattern (145 -> 55 answerers)"
affects: [148-02, 148-03, render-pipeline]

tech-stack:
  added: []
  patterns: ["decorator-based registry for answerer functions", "separate _registry.py to avoid circular imports"]

key-files:
  created:
    - src/do_uw/stages/render/context_builders/answerers/_registry.py
    - src/do_uw/stages/render/context_builders/answerers/_helpers.py
    - src/do_uw/stages/render/context_builders/answerers/company.py
    - src/do_uw/stages/render/context_builders/answerers/financial.py
    - src/do_uw/stages/render/context_builders/answerers/governance.py
    - src/do_uw/stages/render/context_builders/answerers/market.py
    - src/do_uw/stages/render/context_builders/answerers/litigation.py
    - src/do_uw/stages/render/context_builders/answerers/operational.py
    - src/do_uw/stages/render/context_builders/answerers/program.py
    - src/do_uw/stages/render/context_builders/answerers/decision.py
    - tests/render/test_uw_questions.py
  modified:
    - src/do_uw/stages/render/context_builders/answerers/__init__.py
    - src/do_uw/stages/render/context_builders/uw_questions.py

key-decisions:
  - "Split registry into _registry.py to avoid circular imports between __init__.py and domain modules"
  - "Used decorator @register pattern for self-registration instead of manual dict"
  - "Helpers extracted to _helpers.py with safe_float_extract wrapping formatters.safe_float"

patterns-established:
  - "Answerer pattern: @register('XXX-NN') decorator on function taking (q, state, ctx) -> dict"
  - "Partial answer pattern: partial_answer() returns answer with inline Needs Review flag per D-01"
  - "No-data-as-upgrade: clean signal results (no flags) return UPGRADE verdict, not NO_DATA"

requirements-completed: [QFW-01, QFW-02, QFW-03, QFW-06]

duration: 12min
completed: 2026-03-28
---

# Phase 148 Plan 01: Answerers Subpackage Summary

**55 dedicated answerer functions across 8 domain files with @register decorator pattern, replacing 8 inline answerers and screening_answers fallback in uw_questions.py**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-28T20:38:03Z
- **Completed:** 2026-03-28T20:49:39Z
- **Tasks:** 2
- **Files modified:** 13

## Accomplishments
- Created answerers/ subpackage with 55 answerer functions covering all brain questions
- Refactored uw_questions.py from 542 lines to 145 lines using ANSWERER_REGISTRY
- 7 tests validating schema (QFW-01/02), registry completeness, answer quality, and section position (QFW-07)
- BIZ-05, BIZ-06, OPS-01, OPS-04 include LLM extraction fallback paths per D-02
- All answerers use safe_float_extract -- zero bare float() calls

## Task Commits

1. **Task 1: Create answerers subpackage with registry, helpers, and all 55 answerers** - `ddde5707` (feat)
2. **Task 2: Wire answerers into uw_questions.py and add tests** - `64085a2b` (feat)

## Files Created/Modified
- `answerers/_registry.py` - Central ANSWERER_REGISTRY dict + @register decorator
- `answerers/_helpers.py` - sv, fmt_currency, fmt_pct, safe_float_extract, suggest_filing_reference, partial_answer
- `answerers/company.py` - BIZ-01 through BIZ-06 (6 answerers)
- `answerers/financial.py` - FIN-01 through FIN-08 (8 answerers)
- `answerers/governance.py` - GOV-01 through GOV-08 (8 answerers)
- `answerers/market.py` - MKT-01 through MKT-07 (7 answerers)
- `answerers/litigation.py` - LIT-01 through LIT-07 (7 answerers)
- `answerers/operational.py` - OPS-01 through OPS-07 (7 answerers)
- `answerers/program.py` - PRG-01 through PRG-05 (5 answerers)
- `answerers/decision.py` - UW-01 through UW-07 (7 answerers)
- `uw_questions.py` - Refactored to use ANSWERER_REGISTRY (542 -> 145 lines)
- `tests/render/test_uw_questions.py` - 7 tests for schema, registry, answer quality, section position

## Decisions Made
- Split registry into `_registry.py` instead of keeping in `__init__.py` to avoid circular imports when domain modules import `register`
- Domain modules import `register` from `_registry`, `__init__.py` re-exports `ANSWERER_REGISTRY` after importing all domain modules
- Clean signal results (no flags triggered) return UPGRADE verdict with "no issues detected" message rather than NO_DATA -- provides underwriter confirmation of what was checked

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Circular import in __init__.py**
- **Found during:** Task 1 (creating answerers subpackage)
- **Issue:** Domain modules importing `register` from `__init__.py` caused circular import since `__init__.py` also imports domain modules
- **Fix:** Created separate `_registry.py` module holding `ANSWERER_REGISTRY` and `register`. Domain modules import from `_registry.py`, `__init__.py` re-exports after importing domains.
- **Files modified:** answerers/_registry.py (new), answerers/__init__.py
- **Committed in:** ddde5707

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Architecture improvement. No scope creep.

## Issues Encountered
- Linter/file-watcher repeatedly reverted `__init__.py` to stub content during writes. Resolved by creating all domain files first, then writing `__init__.py` last.

## Known Stubs
None. All 55 answerers are fully implemented with data access paths.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- ANSWERER_REGISTRY is ready for import by plan 02 (SCA question integration) and plan 03 (template/CSS/verdict rollups)
- `suggest_filing_reference` in _helpers.py expanded with scoring/benchmark/analysis data_source patterns
- screening_answers.py is still available for legacy risk card screening (not removed)

## Self-Check: PASSED

All 12 created/modified files exist. Both task commits (ddde5707, 64085a2b) found in git log.

---
*Phase: 148-question-driven-underwriting-section*
*Completed: 2026-03-28*
