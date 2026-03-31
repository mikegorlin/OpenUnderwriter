---
phase: 119-stock-drop-catalysts-competitive-landscape-alt-data
plan: 01
subsystem: models
tags: [pydantic, competitive-landscape, alt-data, esg, ai-washing, tariff, peer-sca]

requires:
  - phase: 118-revenue-model-company-intelligence-dossier
    provides: DossierData model pattern, AnalysisState wiring pattern
provides:
  - CompetitiveLandscape, PeerRow, MoatDimension models (dossier 5.7)
  - AltDataAssessments, ESGRisk, AIWashingRisk, TariffExposure, PeerSCACheck models
  - StockDropEvent from_price, volume, do_assessment fields
  - AnalysisState transient pipeline fields (stock_patterns, multi_horizon_returns, analyst_consensus, drop_narrative)
affects: [119-02-extraction, 119-03-enrichment, 119-04-context-builders, 119-05-templates, 119-06-wiring]

tech-stack:
  added: []
  patterns:
    - "ConfigDict(frozen=False) on all new models"
    - "All str fields default to empty string, lists use default_factory"
    - "Alt data as top-level AnalysisState field (not nested in DossierData)"
    - "Explicit transient pipeline fields on AnalysisState (Pydantic v2 ignores arbitrary attrs)"

key-files:
  created:
    - src/do_uw/models/competitive_landscape.py
    - src/do_uw/models/alt_data.py
    - tests/models/test_competitive_landscape.py
    - tests/models/test_alt_data.py
  modified:
    - src/do_uw/models/market_events.py
    - src/do_uw/models/dossier.py
    - src/do_uw/models/state.py

key-decisions:
  - "AltDataAssessments placed on AnalysisState directly, not inside DossierData -- alt data is a separate analytical concern"
  - "4 transient pipeline fields declared explicitly on AnalysisState because Pydantic v2 extra='ignore' silently drops arbitrary attrs"

patterns-established:
  - "Phase 119 models follow Phase 118 DossierData pattern: ConfigDict(frozen=False), Field defaults, top-level state wiring"

requirements-completed: [STOCK-01, STOCK-02, DOSSIER-07, ALTDATA-01, ALTDATA-02, ALTDATA-03, ALTDATA-04]

duration: 4min
completed: 2026-03-20
---

# Phase 119 Plan 01: Data Models Summary

**CompetitiveLandscape + AltDataAssessments Pydantic models with StockDropEvent fields and AnalysisState transient pipeline wiring**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-20T16:52:18Z
- **Completed:** 2026-03-20T16:56:00Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Created CompetitiveLandscape model with PeerRow and MoatDimension sub-models for dossier section 5.7
- Created AltDataAssessments model with ESGRisk, AIWashingRisk, TariffExposure, PeerSCACheck sub-models
- Added from_price, volume, do_assessment fields to StockDropEvent for catalyst enrichment
- Wired CompetitiveLandscape into DossierData, AltDataAssessments into AnalysisState
- Added 4 explicit transient pipeline fields to AnalysisState for Phase 119 inter-stage data passing
- 19 new TDD tests, 134 total model tests passing (zero regressions)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create CompetitiveLandscape + AltDataAssessments models** - `7eba1246` (feat, TDD)
2. **Task 2: Wire StockDropEvent fields + models into DossierData/AnalysisState + transient fields** - `2623ffa5` (feat)

## Files Created/Modified
- `src/do_uw/models/competitive_landscape.py` - CompetitiveLandscape, PeerRow, MoatDimension models
- `src/do_uw/models/alt_data.py` - AltDataAssessments, ESGRisk, AIWashingRisk, TariffExposure, PeerSCACheck
- `tests/models/test_competitive_landscape.py` - 7 tests for competitive landscape models
- `tests/models/test_alt_data.py` - 12 tests for alt data models
- `src/do_uw/models/market_events.py` - Added from_price, volume, do_assessment to StockDropEvent
- `src/do_uw/models/dossier.py` - Wired competitive_landscape field, removed deferred note
- `src/do_uw/models/state.py` - Added alt_data + 4 transient pipeline fields

## Decisions Made
- AltDataAssessments placed as top-level AnalysisState field (not inside DossierData) because alt data is a separate analytical concern
- 4 transient pipeline fields (stock_patterns, multi_horizon_returns, analyst_consensus, drop_narrative) declared explicitly on AnalysisState because Pydantic v2 with extra='ignore' silently drops arbitrary attribute assignment

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All 5 new model classes importable and tested
- Contract layer stable for downstream plans (extraction, enrichment, context builders, templates, wiring)
- StockDropEvent ready for catalyst enrichment in 119-02
- CompetitiveLandscape ready for LLM extraction in 119-02
- AltDataAssessments ready for alt data extraction in 119-02
- Transient pipeline fields ready for inter-stage data passing

---
*Phase: 119-stock-drop-catalysts-competitive-landscape-alt-data*
*Completed: 2026-03-20*
