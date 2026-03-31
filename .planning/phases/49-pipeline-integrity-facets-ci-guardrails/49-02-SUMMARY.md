---
phase: 49-pipeline-integrity-facets-ci-guardrails
plan: 02
subsystem: brain
tags: [facets, signals, yaml, display-spec, brain-metadata]

# Dependency graph
requires:
  - phase: 49-01
    provides: "Consistent signal terminology, brain/signals/ directory with 400 signals"
provides:
  - "facet field on all 400 brain signals (deterministic by prefix)"
  - "display spec (value_format, source_type) on all 400 brain signals"
  - "8 facet definition YAMLs covering all signal domains"
  - "9 total facet files (8 domain + red_flags cross-cutting)"
  - "BrainSignalEntry.facet field in schema"
affects: [49-03, 49-04, 49-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Facet assignment deterministic by signal ID prefix (BIZ->business_profile, etc.)"
    - "Display spec inference from threshold type and data_locations"
    - "Scripted bulk YAML metadata updates (never manual for 400 signals)"

key-files:
  created:
    - "src/do_uw/brain/facets/business_profile.yaml"
    - "src/do_uw/brain/facets/executive_risk.yaml"
    - "src/do_uw/brain/facets/filing_analysis.yaml"
    - "src/do_uw/brain/facets/financial_health.yaml"
    - "src/do_uw/brain/facets/forward_looking.yaml"
    - "src/do_uw/brain/facets/litigation.yaml"
    - "src/do_uw/brain/facets/market_activity.yaml"
    - "scripts/add_facet_display_to_signals.py"
    - "scripts/create_facet_definitions.py"
  modified:
    - "src/do_uw/brain/brain_signal_schema.py"
    - "src/do_uw/brain/facets/governance.yaml"
    - "src/do_uw/brain/signals/**/*.yaml (all 36 YAML files)"

key-decisions:
  - "Facet assignment purely deterministic by prefix -- no ambiguity or cross-cutting assignments except red_flags"
  - "Display spec value_format inferred from threshold type + name heuristics (pct, currency, count, boolean, etc.)"
  - "Display spec source_type inferred from required_data/data_locations priority chain"
  - "Governance facet rebuilt from scratch with all 85 GOV.* signals (was partial 12)"
  - "Existing complete display specs (23 from Phase 48) preserved, not overwritten"

patterns-established:
  - "Facet = grouping of signals by domain prefix, defined in brain/facets/*.yaml"
  - "Every signal has facet + display metadata for self-describing brain"

requirements-completed: [FACET-01, FACET-02, FACET-04]

# Metrics
duration: 4min
completed: 2026-02-26
---

# Phase 49 Plan 02: Facet Metadata & Definitions Summary

**Facet + display metadata on all 400 brain signals with 8 domain facet definition YAMLs for self-describing brain knowledge**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-02-26T19:38:47Z
- **Completed:** 2026-02-26T19:42:38Z
- **Tasks:** 2
- **Files modified:** 47

## Accomplishments
- Added `facet` field to all 400 signals via deterministic prefix mapping (BIZ->business_profile, FIN->financial_health, etc.)
- Added `display` spec (value_format, source_type, threshold_context) to all 400 signals via heuristic inference
- Created 7 new facet definition YAMLs with complete signal lists: business_profile (43), executive_risk (20), filing_analysis (15), financial_health (58), forward_looking (79), litigation (65), market_activity (35)
- Updated governance.yaml from partial (12 signals) to complete (85 signals)
- Cross-validated: all 400 signals appear in exactly one facet, zero duplicates, zero unknown IDs
- Brain build passes with all new metadata

## Task Commits

Each task was committed atomically:

1. **Task 1: Add facet + display fields to all signal YAMLs** - `d9da8ac` (feat)
2. **Task 2: Create facet definition YAMLs for all 8 domains** - `3d77187` (feat)

## Files Created/Modified

**New facet definitions (7):**
- `src/do_uw/brain/facets/business_profile.yaml` - 43 BIZ.* signals
- `src/do_uw/brain/facets/executive_risk.yaml` - 20 EXEC.* signals
- `src/do_uw/brain/facets/filing_analysis.yaml` - 15 NLP.* signals
- `src/do_uw/brain/facets/financial_health.yaml` - 58 FIN.* signals
- `src/do_uw/brain/facets/forward_looking.yaml` - 79 FWRD.* signals
- `src/do_uw/brain/facets/litigation.yaml` - 65 LIT.* signals
- `src/do_uw/brain/facets/market_activity.yaml` - 35 STOCK.* signals

**Updated:**
- `src/do_uw/brain/facets/governance.yaml` - Expanded from 12 to 85 GOV.* signals
- `src/do_uw/brain/brain_signal_schema.py` - Added `facet: str` field to BrainSignalEntry
- All 36 signal YAML files in `src/do_uw/brain/signals/` - Added facet + display fields

**Scripts:**
- `scripts/add_facet_display_to_signals.py` - Bulk facet + display metadata script
- `scripts/create_facet_definitions.py` - Facet definition YAML generator

## Decisions Made
- Facet assignment is purely deterministic by ID prefix (no ambiguity). This makes facet membership a derived property that can be validated automatically.
- Display spec value_format inferred from threshold type first, then name heuristics for currency/count/pct differentiation within tiered/numeric types.
- Display spec source_type inferred from required_data and data_locations keys with priority chain (SEC_DEF14A > SEC_10K > SEC_8K > MARKET_DATA > WEB > DERIVED).
- Governance facet rebuilt from scratch (was 12 hand-picked signals from Phase 48, now all 85 GOV.* signals).
- Existing complete display specs (23 signals from Phase 48) preserved unchanged -- script only fills in missing value_format/source_type.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Brain is now fully self-describing: every signal has facet + display metadata
- 9 facet definition files ready for render-audit command (Plan 04)
- CI validation (Plan 05) can verify bidirectional signal-to-facet integrity
- Brain build passes cleanly with all new metadata

## Self-Check: PASSED

All claims verified:
- All 12 key files exist (9 facet YAMLs, schema, 2 scripts)
- Both commits found (d9da8ac, 3d77187)
- 400/400 signals have facet field
- 400/400 signals have display spec
- 9 facet files in brain/facets/
- Zero duplicates, zero missing signal IDs

---
*Phase: 49-pipeline-integrity-facets-ci-guardrails*
*Completed: 2026-02-26*
