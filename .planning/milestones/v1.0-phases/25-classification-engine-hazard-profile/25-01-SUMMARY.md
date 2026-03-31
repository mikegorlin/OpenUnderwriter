---
phase: 25-classification-engine-hazard-profile
plan: 01
subsystem: models, classification, config
tags: [pydantic, classification, hazard-profile, config-driven, pure-function, ies]

# Dependency graph
requires:
  - phase: 24-check-calibration-knowledge-enrichment
    provides: Five-layer architecture definition, hazard taxonomy with 7 categories and 55 dimensions
provides:
  - ClassificationResult and MarketCapTier Pydantic models (Layer 1)
  - HazardProfile, HazardDimensionScore, CategoryScore, InteractionEffect, HazardCategory Pydantic models (Layer 2)
  - classification.json with 5 market cap tiers, 12 sector rates, IPO age decay, IES breakpoints
  - hazard_weights.json with 7 categories and 55 dimension definitions
  - hazard_interactions.json with 5 named interaction patterns and dynamic detection config
  - classify_company() pure function with 41 unit tests
  - AnalysisState extended with classification and hazard_profile fields
affects: [25-02-PLAN (hazard engine uses models and configs), 25-03-PLAN (pipeline integration uses classify_company)]

# Tech tracking
tech-stack:
  added: []
  patterns: [config-driven classification, 3-year IPO cliff model, pure function with config injection]

key-files:
  created:
    - src/do_uw/models/classification.py
    - src/do_uw/models/hazard_profile.py
    - src/do_uw/config/classification.json
    - src/do_uw/config/hazard_weights.json
    - src/do_uw/config/hazard_interactions.json
    - src/do_uw/stages/classify/__init__.py
    - src/do_uw/stages/classify/classification_engine.py
    - src/do_uw/stages/classify/severity_bands.py
    - tests/test_classification.py
  modified:
    - src/do_uw/models/__init__.py
    - src/do_uw/models/state.py

key-decisions:
  - "55 dimensions retained (not 47) -- plan referenced '47' but research taxonomy H1(13)+H2(8)+H3(8)+H4(8)+H5(5)+H6(7)+H7(6) = 55. Plan directive 'do not trim' followed."
  - "Filing rate capped at 25% sanity ceiling to prevent unreasonable results from extreme combinations"
  - "PIPELINE_STAGES kept at 7 -- classification runs as pre-ANALYZE sub-step, not a formal pipeline stage"

patterns-established:
  - "Config injection pattern: classify_company() takes config dict parameter, load_classification_config() loads from disk"
  - "Pure function pattern: classify_company() is deterministic, no side effects, no state mutation"
  - "IPO cliff model: 3-year cliff (2.8x), transition (1.5x), seasoned (1.0x) -- inclusive boundaries"

# Metrics
duration: 8m 28s
completed: 2026-02-12
---

# Phase 25 Plan 01: Classification Engine & Models Summary

**Config-driven classification engine with 3-variable filing rate computation (market cap tier, sector, IPO age), plus complete Pydantic models and config files for the 55-dimension hazard profile system**

## Performance

- **Duration:** 8m 28s
- **Started:** 2026-02-12T04:25:06Z
- **Completed:** 2026-02-12T04:33:34Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- Built Layer 1 classification engine: classify_company() pure function that takes 3 inputs and produces a deterministic base filing rate + severity band, all values from classification.json
- Created complete Pydantic model hierarchy for both Layer 1 (ClassificationResult, MarketCapTier) and Layer 2 (HazardProfile, HazardDimensionScore, CategoryScore, InteractionEffect, HazardCategory)
- Built 3 comprehensive JSON config files: classification.json (5 tiers, 12 sectors, IPO decay), hazard_weights.json (7 categories, 55 dimensions with scoring scales), hazard_interactions.json (5 named patterns + dynamic detection)
- Extended AnalysisState with classification and hazard_profile optional fields without breaking the 7-stage pipeline
- Wrote 41 unit tests covering all tier boundaries, IPO cliff model, sector lookups, severity bands, DDL computation, and end-to-end integration

## Task Commits

Each task was committed atomically:

1. **Task 1: Pydantic models, config files, and AnalysisState extension** - `77f0e5e` (feat)
2. **Task 2: Classification engine and unit tests** - `bed00f5` (feat)

## Files Created/Modified
- `src/do_uw/models/classification.py` - ClassificationResult and MarketCapTier Pydantic models
- `src/do_uw/models/hazard_profile.py` - HazardProfile, HazardDimensionScore, CategoryScore, InteractionEffect, HazardCategory models
- `src/do_uw/models/__init__.py` - Updated with re-exports for all new models
- `src/do_uw/models/state.py` - Extended AnalysisState with classification and hazard_profile fields
- `src/do_uw/config/classification.json` - Market cap tiers, sector rates, IPO age decay, IES breakpoints
- `src/do_uw/config/hazard_weights.json` - 7 categories with weights, 55 dimension definitions
- `src/do_uw/config/hazard_interactions.json` - 5 named interaction patterns, dynamic detection config
- `src/do_uw/stages/classify/__init__.py` - Package init with re-exports
- `src/do_uw/stages/classify/classification_engine.py` - classify_company() pure function and helpers
- `src/do_uw/stages/classify/severity_bands.py` - Severity band lookup by market cap tier
- `tests/test_classification.py` - 41 unit tests for the classification engine

## Decisions Made
- **55 dimensions retained instead of 47:** The plan said "47 dimensions" but the actual research taxonomy (H1:13 + H2:8 + H3:8 + H4:8 + H5:5 + H6:7 + H7:6) totals 55. The plan's directive "do not trim" was followed. The "47" appears to have been a counting error propagated through planning documents.
- **25% filing rate ceiling:** Added a sanity cap of 25% to prevent extreme combinations (e.g., mega-cap biotech IPO) from producing unreasonable filing rates.
- **PIPELINE_STAGES unchanged at 7:** Classification will run as a pre-ANALYZE sub-step, not as a formal pipeline stage, to avoid test breakage.
- **Inclusive cliff boundaries:** IPO age cliff model uses inclusive boundaries (year 3 is still cliff period, year 5 is still transition period).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Dimension count: 55 instead of plan-specified 47**
- **Found during:** Task 1 (hazard_weights.json creation)
- **Issue:** Plan specified "47 dimensions" but the full taxonomy H1-01 through H7-06 (13+8+8+8+5+7+6) = 55 dimensions
- **Fix:** Included all 55 dimensions per the "do not trim" directive, matching the complete research taxonomy
- **Files modified:** src/do_uw/config/hazard_weights.json
- **Verification:** JSON loads successfully, all dimension IDs present
- **Committed in:** 77f0e5e (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (plan document had incorrect count, research taxonomy followed)
**Impact on plan:** Minor -- the number was wrong in the plan but the intent ("keep all dimensions") was clear. Plan 02 benefits from having all dimensions available.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All models importable by Plan 02 (hazard engine) which is executing in parallel
- classify_company() function ready for Plan 03 (pipeline integration)
- Config files ready for both Plan 02 (hazard_weights.json, hazard_interactions.json) and Plan 03 (classification.json)
- 1462 tests passing (41 new, 1 pre-existing failure in MRNA ground truth unrelated to this plan)

---
*Phase: 25-classification-engine-hazard-profile*
*Completed: 2026-02-12*
