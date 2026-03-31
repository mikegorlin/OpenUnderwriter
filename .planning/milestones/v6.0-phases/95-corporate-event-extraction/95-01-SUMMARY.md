---
phase: 95-corporate-event-extraction
plan: 01
subsystem: brain-signals
tags: [brain, signals, corporate-events, M&A, IPO, restatements, capital-markets]

requires:
  - phase: 70-xbrl-forensics
    provides: xbrl_forensics.ma_forensics and balance_sheet data
provides:
  - 5 BIZ.EVENT brain signals for corporate event risk evaluation
  - signal_mappers_events.py routing data from existing state fields
  - corporate_events group in output manifest
affects: [100-display-integration, 99-scoring]

tech-stack:
  added: []
  patterns:
    - "Event signal mapper pattern: dedicated mapper file per signal domain"
    - "BIZ.EVENT prefix routing before generic BIZ.* in signal_mappers.py"

key-files:
  created:
    - src/do_uw/brain/signals/biz/events.yaml
    - src/do_uw/stages/analyze/signal_mappers_events.py
    - tests/test_event_signals.py
  modified:
    - src/do_uw/stages/analyze/signal_mappers.py
    - src/do_uw/stages/analyze/signal_field_routing.py
    - src/do_uw/brain/output_manifest.yaml

key-decisions:
  - "Removed unsupported 'condition' field from ipo_exposure threshold (EvaluationThreshold schema does not support per-threshold conditions)"
  - "M&A risk score is additive 0-4: serial_acquirer(2) + goodwill>40%(1) + goodwill_growth>25%(1)"
  - "Business changes filter uses regex to exclude generic '8-K filed DATE' entries"

patterns-established:
  - "signal_mappers_events.py: dedicated mapper for BIZ.EVENT domain, follows signal_mappers_ext pattern"

requirements-completed: [EVENT-01, EVENT-02, EVENT-03, EVENT-04, EVENT-05]

duration: 7min
completed: 2026-03-10
---

# Phase 95 Plan 01: Corporate Event Extraction Summary

**5 BIZ.EVENT brain signals for M&A risk, IPO exposure, restatements, capital changes, and business pivots with full mapper wiring and 10 tests**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-10T04:45:52Z
- **Completed:** 2026-03-10T04:53:01Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments
- Created 5 BIZ.EVENT brain signals with schema v3 (acquisition, evaluation, presentation blocks)
- Wired signal data mappers to existing state fields (xbrl_forensics, capital_markets, audit, business_changes)
- Added corporate_events group to output manifest under business_profile section
- 10 tests covering YAML structure, all 5 mapper functions (positive + negative cases), and manifest registration

## Task Commits

Each task was committed atomically:

1. **Task 1: Create BIZ.EVENT signal YAML definitions** - `838521d` (feat)
2. **Task 2: Wire signal data mappers and manifest entries** - `17f2072` (feat)
3. **Task 3: Add tests for BIZ.EVENT signal evaluation** - `809cd2b` (test)

## Files Created/Modified
- `src/do_uw/brain/signals/biz/events.yaml` - 5 BIZ.EVENT signal definitions
- `src/do_uw/stages/analyze/signal_mappers_events.py` - map_event_fields() routing for all 5 signals
- `src/do_uw/stages/analyze/signal_mappers.py` - BIZ.EVENT prefix routing before generic BIZ.*
- `src/do_uw/stages/analyze/signal_field_routing.py` - 5 FIELD_FOR_CHECK entries
- `src/do_uw/brain/output_manifest.yaml` - corporate_events group in business_profile
- `tests/test_event_signals.py` - 10 tests for signal structure and mapper logic

## Decisions Made
- Removed `condition` field from ipo_exposure evaluation threshold -- EvaluationThreshold schema does not support per-threshold conditions; documented as YAML comment instead
- M&A risk score uses additive scoring (0-4) from serial acquirer flag + goodwill ratio + growth rate
- Business changes mapper filters generic "8-K filed DATE" entries via regex to count only substantive changes
- IPO exposure maps directly to active_section_11_windows count (already computed by capital_markets extraction)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed ipo_exposure YAML validation error**
- **Found during:** Task 2 verification
- **Issue:** `condition` field in evaluation.thresholds not permitted by BrainSignalEntry Pydantic schema
- **Fix:** Removed `condition` key, added YAML comment documenting the intended logic
- **Files modified:** src/do_uw/brain/signals/biz/events.yaml
- **Verification:** BrainLoader successfully loads all 5 signals
- **Committed in:** 17f2072 (Task 2 commit)

**2. [Rule 3 - Blocking] Fixed BrainLoader API mismatch in plan**
- **Found during:** Task 2 verification
- **Issue:** Plan referenced `BrainLoader().load_all_signals()` which doesn't exist; actual API is `BrainLoader().load_signals()` returning dict with 'signals' key
- **Fix:** Used correct API in verification commands
- **Files modified:** None (verification scripts only)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Both fixes necessary for correctness. No scope creep.

## Issues Encountered
- 2 pre-existing test failures found unrelated to this plan: `test_threshold_provenance_categorized` (Phase 94 BIZ.OPS signal has non-standard provenance source) and `test_brain_help_shows_all_commands` (missing export-docs CLI command)

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- 5 BIZ.EVENT signals ready for evaluation by the check engine
- corporate_events manifest group ready for Phase 100 rendering template creation
- Signal mappers route to existing extracted data (no new acquisition needed)

## Self-Check: PASSED

All 3 created files verified on disk. All 3 task commits verified in git log.

---
*Phase: 95-corporate-event-extraction*
*Completed: 2026-03-10*
