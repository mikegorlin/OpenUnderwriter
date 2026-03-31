---
phase: 135-governance-intelligence
plan: 01
subsystem: models, extraction
tags: [pydantic, governance, serial-defendant, insider-trading, supabase, officer-background]

requires:
  - phase: 134-company-intelligence
    provides: "Supabase batch query pattern (query_peer_sca_filings)"
provides:
  - "OfficerBackground, OfficerSCAExposure, PriorCompany models for officer investigation"
  - "ShareholderRightsProvision, ShareholderRightsInventory models for 8-provision checklist"
  - "PerInsiderActivity model for per-insider sell aggregation"
  - "BoardProfile.cumulative_voting field (closes data gap for 8-provision inventory)"
  - "extract_prior_companies_from_bio: regex extraction from DEF 14A bios"
  - "detect_serial_defendants: Supabase SCA cross-reference with date overlap"
  - "aggregate_per_insider: per-insider sell totals with 10b5-1 and %O/S"
affects: [135-02-governance-intelligence, governance-context-builders, governance-templates]

tech-stack:
  added: []
  patterns:
    - "Officer prior company regex extraction with deduplication"
    - "Year-to-date-range conversion for fuzzy date overlap (start_year-01-01 to end_year-12-31)"
    - "Fuzzy company name matching with stop-word removal for SCA cross-reference"
    - "Per-insider sell aggregation excluding compensation codes (A, F) and gifts (G, W)"

key-files:
  created:
    - src/do_uw/models/governance_intelligence.py
    - src/do_uw/stages/extract/officer_background.py
    - tests/models/test_governance_intelligence.py
    - tests/extract/test_officer_background.py
  modified:
    - src/do_uw/models/governance.py

key-decisions:
  - "Regex-first approach for prior company extraction (LLM deferred to future enhancement)"
  - "Year-to-date-range conversion: officer years become full ranges (Jan 1 to Dec 31) for conservative overlap detection"
  - "Fuzzy company name matching via case-insensitive substring + stop-word removal (handles Inc/Corp/Ltd variants)"
  - "Compensation codes A/F excluded from per-insider aggregation, matching existing insider_trading.py pattern"

patterns-established:
  - "Officer background investigation: bio extraction -> Supabase cross-ref -> serial defendant flagging"
  - "Suitability as data completeness indicator (HIGH/MEDIUM/LOW), not person judgment"

requirements-completed: [GOV-01, GOV-02, GOV-03, GOV-04, GOV-05]

duration: 5min
completed: 2026-03-27
---

# Phase 135 Plan 01: Governance Intelligence Data Layer Summary

**Pydantic models + extraction logic for officer background investigation with serial defendant detection, shareholder rights inventory, and per-insider activity aggregation**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-27T07:24:28Z
- **Completed:** 2026-03-27T07:29:15Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- 6 new Pydantic models (PriorCompany, OfficerSCAExposure, OfficerBackground, ShareholderRightsProvision, ShareholderRightsInventory, PerInsiderActivity) for governance intelligence data layer
- Officer background extraction pipeline: regex bio parsing, Supabase SCA cross-reference, date overlap logic, serial defendant detection with fuzzy company name matching
- Per-insider sell aggregation from Form 4 InsiderTransaction records with 10b5-1 detection and %O/S calculation
- BoardProfile.cumulative_voting field closes the data gap for the 8-provision shareholder rights inventory
- 39 unit tests covering all models and extraction functions (TDD: RED -> GREEN)

## Task Commits

Each task was committed atomically:

1. **Task 1: Pydantic models + BoardProfile cumulative_voting** - `0e8b9bd3` (feat)
2. **Task 2: Officer background extraction with serial defendant detection** - `86e46241` (feat)

## Files Created/Modified
- `src/do_uw/models/governance_intelligence.py` - 6 Pydantic v2 models for governance intelligence
- `src/do_uw/stages/extract/officer_background.py` - 6 extraction functions: bio parsing, date overlap, Supabase query, serial defendant detection, suitability assessment, per-insider aggregation
- `src/do_uw/models/governance.py` - Added cumulative_voting SourcedValue[bool] field to BoardProfile
- `tests/models/test_governance_intelligence.py` - 18 model validation tests
- `tests/extract/test_officer_background.py` - 21 extraction logic unit tests

## Decisions Made
- Used regex-first approach for prior company extraction from bio text (LLM extraction deferred to future enhancement per plan guidance)
- Year-to-date-range conversion for date overlap: officer years become full date ranges (Jan 1 to Dec 31) to catch edge cases where officer's year overlaps with SCA class period
- Fuzzy company name matching uses case-insensitive substring + stop-word removal (strips Inc, Corp, Ltd, etc.) to handle "Acme Corp" vs "Acme Corporation" variations
- Per-insider aggregation excludes compensation codes A (award) and F (tax withhold), matching existing COMPENSATION_CODES pattern in insider_trading.py

## Deviations from Plan
None - plan executed exactly as written.

## Known Stubs
None - all models and extraction functions are fully implemented with real logic.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 6 models ready for Plan 02 context builders to consume
- Extraction functions ready to be called from governance context builder
- BoardProfile.cumulative_voting field ready for DEF 14A extraction population on next --fresh run

---
*Phase: 135-governance-intelligence*
*Completed: 2026-03-27*
