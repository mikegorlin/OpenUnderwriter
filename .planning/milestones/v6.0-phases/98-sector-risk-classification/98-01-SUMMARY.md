---
phase: 98-sector-risk-classification
plan: 01
subsystem: brain
tags: [gics, sector-classification, hazard-tier, claim-patterns, regulatory, peer-comparison, yaml, reference-data]

requires:
  - phase: 97-external-environment-assessment
    provides: ENVR signal pattern (v3 schema, extraction module pattern)
provides:
  - 4 SECT brain signal YAML definitions (SECT.hazard_tier, SECT.claim_patterns, SECT.regulatory_overlay, SECT.peer_comparison)
  - 4 static reference data tables in brain/config/ with D&O study provenance
  - Sector classification extraction module (extract_sector_signals)
  - GICS -> SIC fallback chain for sector identification
affects: [98-02, 99-scoring, 100-display, render]

tech-stack:
  added: []
  patterns: [REFERENCE_DATA acquisition type, static YAML reference tables with provenance metadata, 3-level GICS fallback chain]

key-files:
  created:
    - src/do_uw/brain/config/sector_hazard_tiers.yaml
    - src/do_uw/brain/config/sector_claim_patterns.yaml
    - src/do_uw/brain/config/sector_regulatory_overlay.yaml
    - src/do_uw/brain/config/sector_peer_benchmarks.yaml
    - src/do_uw/brain/signals/biz/sector.yaml
    - src/do_uw/stages/extract/sector_classification.py
    - tests/test_sector_signals.py
  modified: []

key-decisions:
  - "YAML format for reference data tables (alongside existing JSON config files)"
  - "3-level fallback: GICS sub-industry -> GICS sector -> Moderate default"
  - "SIC -> GICS resolution via sic_gics_mapping.json when GICS unavailable"
  - "Peer comparison uses absolute deviation >1 std_dev as outlier threshold"

patterns-established:
  - "REFERENCE_DATA acquisition type for static lookup signals"
  - "Brain config YAML with metadata.sources provenance block"
  - "Module-level cached YAML loading with global variables"

requirements-completed: [SECT-01, SECT-02, SECT-03, SECT-04]

duration: 7min
completed: 2026-03-10
---

# Phase 98 Plan 01: Sector Risk Classification Summary

**4 SECT brain signals with GICS-based hazard tiers, claim patterns, regulatory overlay, and peer benchmarks from D&O study reference data**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-10T15:51:55Z
- **Completed:** 2026-03-10T15:59:00Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- 4 static reference data YAML tables with full provenance from Cornerstone Research, NERA, and SCAC studies
- 4 SECT brain signal definitions with v3 schema, sector_risk group, and acquisition/evaluation/presentation blocks
- Extraction module with 3-level GICS fallback chain (sub-industry -> sector -> default) and SIC resolution
- 18 passing unit tests covering lookup, fallback, edge cases, and integration

## Task Commits

Each task was committed atomically:

1. **Task 1: Create 4 reference data tables and 4 SECT brain signal YAML definitions** - `128c508` (feat)
2. **Task 2: Create sector extraction module with TDD (RED)** - `c07bd8f` (test)
3. **Task 2: Create sector extraction module with TDD (GREEN)** - `2b1293a` (feat)

## Files Created/Modified
- `src/do_uw/brain/config/sector_hazard_tiers.yaml` - GICS sub-industry to D&O hazard tier mapping (35+ sub-industries + 11 sector fallbacks)
- `src/do_uw/brain/config/sector_claim_patterns.yaml` - Top 3 claim theories per GICS industry group (20 groups)
- `src/do_uw/brain/config/sector_regulatory_overlay.yaml` - Named regulators and intensity per GICS group (22 groups)
- `src/do_uw/brain/config/sector_peer_benchmarks.yaml` - Sector median D&O risk dimensions for all 11 GICS sectors
- `src/do_uw/brain/signals/biz/sector.yaml` - 4 SECT signal definitions with v3 schema
- `src/do_uw/stages/extract/sector_classification.py` - Extraction module computing 4 signal values
- `tests/test_sector_signals.py` - 18 unit tests for sector extraction

## Decisions Made
- Used YAML format for reference data tables to match brain signal convention (alongside existing JSON config)
- 3-level hazard tier fallback: GICS 8-digit sub-industry -> 2-digit sector -> "Moderate" default
- SIC -> GICS resolution via existing sic_gics_mapping.json when company has no GICS code
- Peer comparison outlier threshold: >1 standard deviation from sector median on any dimension
- Filing rates and tier assignments calibrated from Cornerstone/NERA/SCAC aggregate data (not company-level)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- SECT signal definitions ready for wiring into signal mapper and output manifest
- Extraction module ready for integration into EXTRACT stage pipeline
- Reference data tables portable (brain portability principle maintained)

---
*Phase: 98-sector-risk-classification*
*Completed: 2026-03-10*
