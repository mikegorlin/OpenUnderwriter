---
phase: 70-signal-integration
plan: 02
subsystem: signals
tags: [xbrl, dual-source, field-routing, shadow-evaluation, signal-migration]

# Dependency graph
requires:
  - phase: 70-01
    provides: "Foundational signals with forensic_ prefix, XBRL field registry"
provides:
  - "45 XBRL-replaceable signals upgraded to xbrl_ field_keys"
  - "20 dual-source signals with xbrl_ + narrative_key pattern"
  - "Shadow evaluation DuckDB table (brain_xbrl_shadow)"
  - "DataStrategy.narrative_key field in signal_definition.py"
affects: [70-03, scoring, rendering]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dual-source signal pattern: xbrl_ field_key + narrative_key"
    - "Shadow evaluation logging for XBRL migration regression detection"

key-files:
  created:
    - src/do_uw/stages/analyze/signal_xbrl_shadow.py
    - tests/test_signal_xbrl_upgrade.py
  modified:
    - src/do_uw/brain/signals/fin/balance.yaml
    - src/do_uw/brain/signals/fin/income.yaml
    - src/do_uw/brain/signals/fin/temporal.yaml
    - src/do_uw/brain/signals/fin/forensic.yaml
    - src/do_uw/brain/signals/fin/accounting.yaml
    - src/do_uw/brain/signals/biz/core.yaml
    - src/do_uw/brain/signals/biz/model.yaml
    - src/do_uw/brain/signals/gov/board.yaml
    - src/do_uw/brain/signals/gov/exec_comp.yaml
    - src/do_uw/brain/signals/gov/effect.yaml
    - src/do_uw/stages/analyze/signal_mappers.py
    - src/do_uw/stages/analyze/signal_mappers_analytical.py
    - src/do_uw/stages/analyze/signal_mappers_sections.py
    - src/do_uw/stages/analyze/signal_field_routing.py
    - src/do_uw/knowledge/signal_definition.py

key-decisions:
  - "Used xbrl_ prefix convention for all XBRL-sourced field_keys to distinguish from legacy LLM-sourced keys"
  - "Dual-source pattern: xbrl_ field_key for threshold evaluation + narrative_key for LLM display context"
  - "Shadow evaluation is fire-and-forget (try/except with logger.warning) to avoid pipeline disruption"

patterns-established:
  - "Dual-source signal: data_strategy has both field_key (xbrl_*) and narrative_key for XBRL+LLM integration"
  - "Mapper alias pattern: return both legacy key and xbrl_ alias for backward compatibility"

requirements-completed: [SIG-02, SIG-03, SIG-04]

# Metrics
duration: 45min
completed: 2026-03-06
---

# Phase 70 Plan 02: XBRL Signal Upgrade Summary

**Upgraded 45 signals to XBRL-sourced field_keys and enhanced 20 signals with dual XBRL+LLM data sources, with shadow evaluation infrastructure for regression detection**

## Performance

- **Duration:** ~45 min (across two sessions due to context continuation)
- **Started:** 2026-03-06
- **Completed:** 2026-03-06
- **Tasks:** 2
- **Files modified:** 15

## Accomplishments
- 45 signals upgraded from LLM-extracted (MEDIUM confidence) to XBRL-sourced (HIGH confidence) field_keys
- 20 dual-source signals with both xbrl_ numeric evaluation and LLM narrative context
- Shadow evaluation infrastructure logging old vs new values to brain_xbrl_shadow DuckDB table
- Total XBRL-sourced signals: 70+ (29 forensic from Plan 01 + 8 from forensic_opportunities + 33 new)
- DataStrategy model extended with narrative_key field

## Task Commits

Each task was committed atomically:

1. **Task 1: Upgrade 45 XBRL-replaceable signals + shadow evaluation infrastructure** - `1de526e` (feat)
2. **Task 2: Enhance 20 dual-source signals** - `d3449ca` (feat)

## Files Created/Modified

### Created
- `src/do_uw/stages/analyze/signal_xbrl_shadow.py` - Shadow evaluation logging: DuckDB table creation, XBRL value extraction, fire-and-forget logging
- `tests/test_signal_xbrl_upgrade.py` - 13 tests: YAML audit, mapper XBRL keys, shadow table, field routing, threshold unchanged

### Modified (YAML signals)
- `brain/signals/fin/balance.yaml` - 8 FIN.LIQ + 3 FIN.DEBT signals upgraded to xbrl_ field_keys
- `brain/signals/fin/income.yaml` - 4 FIN.PROFIT signals upgraded
- `brain/signals/fin/temporal.yaml` - 10 FIN.TEMPORAL signals added data_strategy blocks with xbrl_ keys
- `brain/signals/fin/forensic.yaml` - 8 FIN.FORENSIC/QUALITY signals updated
- `brain/signals/fin/accounting.yaml` - 13 FIN.ACCT signals with dual xbrl_ + narrative_key
- `brain/signals/biz/core.yaml` - BIZ.SIZE.market_cap upgraded
- `brain/signals/biz/model.yaml` - 2 BIZ.MODEL signals upgraded
- `brain/signals/gov/board.yaml` - GOV.BOARD.independence dual-source
- `brain/signals/gov/exec_comp.yaml` - GOV.EXEC.ceo_profile + cfo_profile dual-source
- `brain/signals/gov/effect.yaml` - GOV.EFFECT.audit_committee + sox_404 dual-source

### Modified (mappers/routing)
- `signal_mappers.py` - Added xbrl_ aliases for all FIN.ACCT and FIN.DEBT dual-source signals
- `signal_mappers_analytical.py` - Extended temporal/quality mappers with xbrl_ key population
- `signal_mappers_sections.py` - Added xbrl_ aliases for governance signals
- `signal_field_routing.py` - Updated FIELD_FOR_CHECK with xbrl_ targets for all enhanced signals
- `knowledge/signal_definition.py` - Added narrative_key field to DataStrategy model

## Decisions Made
- Used `xbrl_` prefix convention for all XBRL-sourced field_keys to distinguish from legacy LLM keys
- Dual-source pattern uses `narrative_key` in YAML data_strategy (not a second field_key)
- Shadow evaluation is fire-and-forget to avoid pipeline disruption
- Plan specified 28 dual-source but several signal IDs don't exist (going_concern, convertible_exposure, expertise_gaps) -- achieved 20, exceeding the 20+ verification threshold

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added narrative_key to DataStrategy Pydantic model**
- **Found during:** Task 2 (dual-source signal enhancement)
- **Issue:** SignalDefinition.DataStrategy model uses `extra="forbid"` -- adding `narrative_key` to YAML signals caused validation failures
- **Fix:** Added `narrative_key: str | None = None` to DataStrategy class
- **Files modified:** `src/do_uw/knowledge/signal_definition.py`
- **Verification:** `test_enriched_check_validates_against_definition` narrative_key errors eliminated
- **Committed in:** d3449ca (Task 2 commit)

**2. [Rule 1 - Bug] Fixed test assertions for XBRL-migrated field_keys**
- **Found during:** Task 1 (XBRL signal upgrade)
- **Issue:** Pre-existing tests expected old field_keys (`current_ratio`, `board_independence`) -- now `xbrl_current_ratio`
- **Fix:** Updated test_brain_loader_roundtrip, test_no_field_key_value_changed, test_field_for_check_has_xbrl_fin_liq_entries
- **Files modified:** `tests/knowledge/test_enriched_roundtrip.py`, `tests/brain/test_v2_migration.py`
- **Verification:** All 3 tests pass
- **Committed in:** 1de526e (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both fixes necessary for correctness. No scope creep.

## Issues Encountered
- Plan specified 28 dual-source signals but several signal IDs (FIN.ACCT.going_concern, FIN.DEBT.convertible_exposure, GOV.BOARD.expertise_gaps) don't exist in the YAML. Achieved 20 dual-source (meeting the >=20 verification threshold).
- Pre-existing test failures (5 in knowledge tests, 2 in render coverage) confirmed as pre-existing on clean main -- not introduced by this plan.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Plan 03 (validation + threshold calibration) can proceed with shadow evaluation data
- All 70+ XBRL-sourced signals are wired through mappers and field routing
- Dual-source pattern established for future signal enhancement

## Self-Check: PASSED

All files verified present. All commits verified in git log.

---
*Phase: 70-signal-integration*
*Completed: 2026-03-06*
