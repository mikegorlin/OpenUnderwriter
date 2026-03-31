---
phase: 17-system-assessment
plan: 04
subsystem: models
tags: [pydantic, governance, market, deprecation, backward-compat, scoring]

# Dependency graph
requires:
  - phase: 03-corporate-governance-extract
    provides: Phase 3 skeleton fields (ExecutiveProfile, BoardProfile, CompensationFlags)
  - phase: 04-market-governance-analysis
    provides: Phase 4 forensic sub-models (LeadershipForensicProfile, OwnershipAnalysis, etc.)
provides:
  - Clean governance model with deprecated Phase 3 fields marked, all scoring migrated to Phase 4
  - Clean market model with deprecated Phase 3 fields marked
  - Tests verifying backward-compatible deserialization and deprecation markers
affects:
  - 18-filing-extraction: Extraction code should use Phase 4 field paths exclusively
  - 19-governance-enrichment: No confusion about which field path to use

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "json_schema_extra={'deprecated': True} for deprecated Pydantic fields"
    - "Phase 4 leadership.executives (tenure_years) as primary over Phase 3 executives (tenure_start)"

key-files:
  created: []
  modified:
    - src/do_uw/models/governance.py
    - src/do_uw/models/market.py
    - src/do_uw/stages/score/factor_data.py
    - src/do_uw/stages/score/pattern_fields.py
    - src/do_uw/stages/score/allegation_mapping.py
    - src/do_uw/stages/render/sections/meeting_questions_gap.py
    - tests/test_governance_models.py

key-decisions:
  - "Board and compensation Phase 3 fields remain primary -- not duplicated by Phase 4 models"
  - "Deprecated fields retained with json_schema_extra for backward compat deserialization"
  - "Scoring code migrated from tenure_start (date math) to tenure_years * 12 (pre-calculated)"
  - "meeting_questions_gap ownership check migrated to Phase 4 ownership.institutional_pct/insider_pct"

patterns-established:
  - "Deprecation pattern: json_schema_extra={'deprecated': True} + description prefix 'DEPRECATED:'"
  - "Phase 4 is primary data path -- all new code reads Phase 4 forensic sub-models"

# Metrics
duration: 9min
completed: 2026-02-10
---

# Phase 17 Plan 04: Governance Model Consolidation Summary

**Phase 3 skeleton fields deprecated with backward compat, all scoring migrated to Phase 4 forensic field paths**

## Performance

- **Duration:** 9 min
- **Started:** 2026-02-10T16:11:28Z
- **Completed:** 2026-02-10T16:21:09Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Marked 3 deprecated fields on GovernanceData (executives, ownership_structure, sentiment_signals) with deprecation metadata
- Marked 2 deprecated fields on MarketSignals (guidance_record, analyst_sentiment) with deprecation metadata
- Migrated all scoring code (factor_data.py, pattern_fields.py, allegation_mapping.py) from Phase 3 gov.executives to Phase 4 gov.leadership.executives
- Migrated meeting_questions_gap.py ownership check from Phase 3 ownership_structure to Phase 4 ownership
- Added 9 new tests: deprecation markers, backward-compatible deserialization, cross-contamination, schema stability
- All 1991 tests pass, 0 type errors, 0 lint errors

## Task Commits

Each task was committed atomically:

1. **Task 1: Audit and mark deprecated skeleton fields** - `4d1b13e` (refactor)
2. **Task 2: Update tests to verify consolidated model usage** - `51278c7` (test)

## Files Created/Modified
- `src/do_uw/models/governance.py` - Deprecated executives, ownership_structure, sentiment_signals with markers
- `src/do_uw/models/market.py` - Deprecated guidance_record, analyst_sentiment with markers
- `src/do_uw/stages/score/factor_data.py` - F9/F10 scoring uses leadership.executives (tenure_years)
- `src/do_uw/stages/score/pattern_fields.py` - _get_exec_tenure uses leadership.executives
- `src/do_uw/stages/score/allegation_mapping.py` - _check_transformation uses leadership.executives
- `src/do_uw/stages/render/sections/meeting_questions_gap.py` - Ownership gap check uses Phase 4 model
- `tests/test_governance_models.py` - 9 new tests for deprecation, backward compat, cross-contamination

## Decisions Made
- **Board/compensation NOT deprecated:** These Phase 3 aggregate models hold board-level metrics (independence_ratio, ceo_chair_duality, etc.) that are NOT duplicated by Phase 4 models. Phase 4 board_forensics holds individual director profiles, which is complementary, not a replacement.
- **Fields retained for deserialization:** Deprecated fields kept with defaults so existing state.json files deserialize without error. Pydantic simply ignores the deprecated values.
- **tenure_years * 12 replaces date math:** Phase 4 LeadershipForensicProfile pre-calculates tenure_years during extraction, so scoring converts to months via multiplication instead of date arithmetic.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All governance and market models have clear field ownership (Phase 3 aggregate vs Phase 4 forensic)
- Phase 18+ extraction code can confidently use Phase 4 field paths exclusively
- No duplicate field paths exist for any data concept

---
*Phase: 17-system-assessment*
*Completed: 2026-02-10*
