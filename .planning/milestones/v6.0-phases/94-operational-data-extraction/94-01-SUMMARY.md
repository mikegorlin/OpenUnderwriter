---
phase: 94-operational-data-extraction
plan: 01
subsystem: extract
tags: [brain-signals, yaml, pydantic, extraction, operational-data, workforce, subsidiary, resilience]

# Dependency graph
requires:
  - phase: 93-business-model-extraction
    provides: "BMOD signal patterns and converter/extraction architecture"
provides:
  - "3 BIZ.OPS brain signals (subsidiary_structure, workforce, resilience) in operations.yaml"
  - "operational_extraction.py with 3 extraction functions"
  - "LLM schema fields for workforce and resilience data"
  - "10-K converter functions for workforce and resilience"
  - "CompanyProfile model fields for operational data"
  - "Output manifest groups and stub templates for Phase 100"
affects: [100-display-integration, 99-scoring-integration]

# Tech tracking
tech-stack:
  added: []
  patterns: ["regex fallback extraction for workforce data", "regulatory regime classification for jurisdictions", "HHI-based geographic concentration scoring"]

key-files:
  created:
    - "src/do_uw/brain/signals/biz/operations.yaml"
    - "src/do_uw/stages/extract/operational_extraction.py"
    - "src/do_uw/templates/html/sections/company/operational_complexity.html.j2"
    - "src/do_uw/templates/html/sections/company/subsidiary_structure.html.j2"
    - "src/do_uw/templates/html/sections/company/workforce_distribution.html.j2"
    - "src/do_uw/templates/html/sections/company/operational_resilience.html.j2"
  modified:
    - "src/do_uw/models/company.py"
    - "src/do_uw/stages/extract/llm/schemas/ten_k.py"
    - "src/do_uw/stages/extract/ten_k_converters.py"
    - "src/do_uw/stages/extract/company_profile.py"
    - "src/do_uw/brain/output_manifest.yaml"
    - "src/do_uw/stages/render/context_builders/company.py"
    - "tests/stages/render/test_section_renderer.py"

key-decisions:
  - "Regulatory regime classification uses static sets: HIGH_REG for 28 jurisdictions with heavy regulation, LOW_REG from existing tax_havens config, MEDIUM_REG default"
  - "Geographic concentration uses HHI-based scoring (0-100) with special handling for top-1 >60% and top-2 >80% concentration"
  - "Workforce extraction has 3-tier fallback: LLM > regex on 10-K text > total employee count only"
  - "Created stub templates for 4 new manifest groups (Phase 100 will expand them)"

patterns-established:
  - "Operational extraction module follows same tuple[SourcedValue | None, ExtractionReport] pattern as other extractors"
  - "Multi-field signal thresholds documented as YAML comments (field key not supported by EvaluationThreshold schema)"

requirements-completed: [OPS-02, OPS-03, OPS-04]

# Metrics
duration: 8min
completed: 2026-03-10
---

# Phase 94 Plan 01: Operational Data Extraction Summary

**3 operational brain signals (subsidiary structure, workforce distribution, resilience) with full extraction pipeline, LLM schema, and manifest wiring**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-10T04:35:19Z
- **Completed:** 2026-03-10T04:43:32Z
- **Tasks:** 3
- **Files modified:** 13

## Accomplishments
- Created 3 brain signals in operations.yaml with full v3 schema (acquisition, evaluation with thresholds, presentation)
- Built extraction module with regulatory regime classification, workforce regex fallback, and HHI-based geographic concentration scoring
- Wired all extractors into pipeline orchestrator with LLM enrichment fallbacks
- Updated output manifest and context builders for Phase 100 template integration

## Task Commits

Each task was committed atomically:

1. **Task 1: Create brain signal YAML and model fields** - `ba71cf6` (feat)
2. **Task 2: Build extraction logic and wire to pipeline** - `e2d4ae1` (feat)
3. **Task 3: Wire signals to output manifest and context builders** - `5564911` (feat)

## Files Created/Modified
- `src/do_uw/brain/signals/biz/operations.yaml` - 3 BIZ.OPS signals with v3 schema
- `src/do_uw/stages/extract/operational_extraction.py` - Extraction functions for subsidiary, workforce, resilience
- `src/do_uw/models/company.py` - 3 new CompanyProfile fields
- `src/do_uw/stages/extract/llm/schemas/ten_k.py` - 7 new LLM extraction fields for workforce/resilience
- `src/do_uw/stages/extract/ten_k_converters.py` - convert_workforce_distribution, convert_operational_resilience
- `src/do_uw/stages/extract/company_profile.py` - Wired 3 extractors + LLM enrichment
- `src/do_uw/brain/output_manifest.yaml` - 4 new groups under business_profile
- `src/do_uw/stages/render/context_builders/company.py` - 3 new context fields
- `src/do_uw/templates/html/sections/company/*.html.j2` - 4 stub templates

## Decisions Made
- Regulatory regime classification: HIGH_REG for 28 jurisdictions with heavy financial/data regulation, LOW_REG from existing tax_havens config, MEDIUM_REG as default
- Geographic concentration scoring: HHI-based (0-100) with top-1 >60% mapping to 80+ and top-2 >80% mapping to 60-80
- Workforce extraction fallback chain: LLM extraction > regex on 10-K text > total employee count
- Stub templates created to prevent TemplateNotFound errors; Phase 100 will expand

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed unsupported 'field' key from evaluation thresholds**
- **Found during:** Task 3 (manifest and context wiring)
- **Issue:** EvaluationThreshold schema has extra="forbid" and only allows op/value/label. Plan specified a 'field' key for multi-field thresholds that doesn't exist in the schema.
- **Fix:** Converted 'field' keys to YAML comments (# applies to: field_name) preserving documentation while making YAML valid
- **Files modified:** src/do_uw/brain/signals/biz/operations.yaml
- **Verification:** BrainSignalEntry.model_validate() passes for all 3 signals
- **Committed in:** 5564911

**2. [Rule 3 - Blocking] Created stub Jinja2 templates for manifest groups**
- **Found during:** Task 3 (manifest and context wiring)
- **Issue:** Plan stated "renderer gracefully skips missing templates" but test_two_column_layout raised TemplateNotFound for new manifest groups
- **Fix:** Created 4 minimal stub templates (empty comment-only files) for Phase 100 to expand
- **Files modified:** src/do_uw/templates/html/sections/company/*.html.j2
- **Verification:** test_two_column_layout passes; all 943 render tests pass
- **Committed in:** 5564911

**3. [Rule 3 - Blocking] Updated fragment count test expectation**
- **Found during:** Task 3 (manifest and context wiring)
- **Issue:** test_company_fragment_count expected exactly 10 templates but now has 14 (10 original + 4 stubs)
- **Fix:** Updated assertion from 10 to 14
- **Files modified:** tests/stages/render/test_section_renderer.py
- **Verification:** All render tests pass
- **Committed in:** 5564911

---

**Total deviations:** 3 auto-fixed (1 bug, 2 blocking)
**Impact on plan:** All auto-fixes necessary for correctness and test passage. No scope creep.

## Issues Encountered
None beyond the auto-fixed deviations.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Operational data extraction pipeline complete and wired
- Stub templates ready for Phase 100 (Display Integration) to expand with full rendering
- Signal evaluation will be wired in Phase 99 (Scoring Integration)
- Data will be populated on next pipeline run with --fresh flag

---
*Phase: 94-operational-data-extraction*
*Completed: 2026-03-10*
