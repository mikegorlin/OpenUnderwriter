---
phase: 93-business-model-extraction
plan: 01
subsystem: brain-signals
tags: [brain-yaml, llm-extraction, pydantic, ten-k, company-profile, bmod]

# Dependency graph
requires: []
provides:
  - "6 brain signals for business model dimensions (biz/model.yaml)"
  - "LLM extraction schema for revenue model, key person, lifecycle, disruption, margins"
  - "CompanyProfile fields and extraction wiring for BMOD data"
affects: [94-operational-data-extraction, 98-sector-risk-mapping, 99-scoring-integration, 100-display-integration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "v3 brain signal schema with acquisition/evaluation/presentation blocks"
    - "Composite risk score converters (0-N scoring from multiple indicators)"
    - "String-parsing converters for structured segment data"

key-files:
  created: []
  modified:
    - "src/do_uw/brain/signals/biz/model.yaml"
    - "src/do_uw/stages/extract/llm/schemas/ten_k.py"
    - "src/do_uw/models/company.py"
    - "src/do_uw/stages/extract/ten_k_converters.py"
    - "src/do_uw/stages/extract/company_profile.py"

key-decisions:
  - "revenue_model_type uses MEDIUM confidence since LLM classification is judgment-based"
  - "key_person risk_score is additive 0-3 (founder=1, tenure>10yr=1, no succession=1)"
  - "disruption risk level derives from threat count: >=3=HIGH, >=1=MODERATE, 0=LOW"
  - "segment margin change computed in basis points for threshold comparison"

patterns-established:
  - "BMOD converter pattern: parse LLM string formats into structured SourcedValue dicts"
  - "Composite risk scoring: multiple boolean/numeric indicators summed to 0-N score"

requirements-completed: [BMOD-01, BMOD-02, BMOD-03, BMOD-04, BMOD-05, BMOD-06]

# Metrics
duration: 4min
completed: 2026-03-10
---

# Phase 93 Plan 01: Business Model Extraction Summary

**6 brain signals for revenue type, concentration risk, key person dependency, lifecycle, disruption, and margins with LLM extraction wiring to CompanyProfile**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-10T03:36:46Z
- **Completed:** 2026-03-10T03:40:42Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Defined 13 total BIZ.MODEL signals (8 existing + 5 new) with full v3 schema
- Upgraded BIZ.MODEL.revenue_type from display-only to classification with evaluation thresholds
- Extended TenKExtraction with 7 new fields for LLM extraction of business model dimensions
- Added 5 CompanyProfile fields and 5 converter functions with structured risk scoring
- All 135 company-related tests pass with zero regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Define 6 business model signals in YAML and extend LLM extraction schema** - `1a4403a` (feat)
2. **Task 2: Add CompanyProfile model fields and wire extraction from LLM data** - `b8a2d21` (feat)

## Files Created/Modified
- `src/do_uw/brain/signals/biz/model.yaml` - 13 BIZ.MODEL signals with v3 schema (acquisition/evaluation/presentation blocks)
- `src/do_uw/stages/extract/llm/schemas/ten_k.py` - 7 new LLM extraction fields for business model dimensions
- `src/do_uw/models/company.py` - 5 new CompanyProfile fields for BMOD data
- `src/do_uw/stages/extract/ten_k_converters.py` - 5 new converter functions with string parsing and risk scoring
- `src/do_uw/stages/extract/company_profile.py` - Wiring converters into _enrich_from_llm pipeline

## Decisions Made
- Revenue model type uses MEDIUM confidence (LLM classification is judgment-based, not audited data)
- Key person risk score is additive 0-3 from three binary indicators, matching signal threshold structure
- Disruption risk level thresholds based on threat count (simple, auditable heuristic)
- Segment margin change in basis points enables direct comparison with signal thresholds (200bps/500bps)
- convert_disruption_risk always returns a result (even with 0 threats = LOW) to distinguish "assessed as low risk" from "not assessed"

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Signal definitions ready for signal engine evaluation once field resolvers are wired
- LLM extraction fields will populate on next --fresh pipeline run
- CompanyProfile fields available for rendering in Phase 100
- concentration_risk_composite field resolver needed (multi-input composite -- will be wired in scoring integration phase 99)

## Self-Check: PASSED

All 5 modified files verified present. Both task commits (1a4403a, b8a2d21) verified in git log. SUMMARY.md created.

---
*Phase: 93-business-model-extraction*
*Completed: 2026-03-10*
