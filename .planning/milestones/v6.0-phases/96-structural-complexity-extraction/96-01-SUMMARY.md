---
phase: 96-structural-complexity-extraction
plan: 01
subsystem: brain-signals
tags: [brain-yaml, text-signals, signal-routing, structural-complexity, disclosure-opacity]

# Dependency graph
requires:
  - phase: 33-03
    provides: BIZ.STRUCT signals (subsidiary_count, vie_spe, related_party) and text_signals infrastructure
provides:
  - 5 BIZ.STRUC brain signals with v3 schema (disclosure_complexity, nongaap, related_parties, obs_exposure, holding_structure)
  - 9 new text signal definitions for structural complexity keyword scanning
  - Signal field routing and mapper functions for all 5 signals
  - Output manifest entry and placeholder template for structural_complexity display group
affects: [100-display-integration, 99-scoring]

# Tech tracking
tech-stack:
  added: []
  patterns: [composite-score-from-text-signals, multi-source-signal-evaluation]

key-files:
  created:
    - src/do_uw/brain/signals/biz/structural.yaml
    - src/do_uw/templates/html/sections/company/structural_complexity.html.j2
  modified:
    - src/do_uw/stages/analyze/signal_field_routing.py
    - src/do_uw/stages/analyze/signal_mappers.py
    - src/do_uw/stages/analyze/text_signals.py
    - src/do_uw/brain/output_manifest.yaml

key-decisions:
  - "Composite scores derived from text signal counts rather than LLM extraction data, avoiding new state dependencies"
  - "Added vie_spe text signal definition (was referenced but undefined) as part of OBS exposure wiring"
  - "Threshold provenance sources use d_and_o_claims_analysis category to match contract test expectations"

patterns-established:
  - "BIZ.STRUC prefix: structural complexity signals using composite scores from text signal keyword counts"
  - "Text signals as numeric inputs: _text_signal_count() feeds composite score formulas in signal mappers"

requirements-completed: [STRUC-01, STRUC-02, STRUC-03, STRUC-04, STRUC-05]

# Metrics
duration: 5min
completed: 2026-03-10
---

# Phase 96 Plan 01: Structural Complexity Extraction Summary

**5 structural complexity brain signals (disclosure opacity, non-GAAP, related parties, OBS exposure, holding depth) with composite scoring from 10-K text signal keyword scanning**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-10T04:46:00Z
- **Completed:** 2026-03-10T04:51:12Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments
- Created 5 BIZ.STRUC brain signals with full v3 schema (acquisition, evaluation with red/yellow/clear thresholds, presentation)
- Added 9 new text signal definitions for structural complexity keyword scanning (VIE/SPE, guarantees, commitments, intercompany, holding layers, FLS density, SEC non-GAAP comments, non-GAAP measures, critical estimates)
- Wired composite score computation in signal mappers using existing extracted data -- no new acquisition or extraction needed
- Added structural_complexity group to output manifest with placeholder Jinja2 template

## Task Commits

Each task was committed atomically:

1. **Task 1: Create biz/structural.yaml with 5 signals and wire field routing** - `96f7d05` (feat)
2. **Task 2: Add text signal definitions and wire signal mappers** - `ccc27e7` (feat)
3. **Task 3: Wire signals to output manifest and verify full pipeline** - `deb371f` (feat)

## Files Created/Modified
- `src/do_uw/brain/signals/biz/structural.yaml` - 5 STRUC signals with full v3 schema
- `src/do_uw/stages/analyze/signal_field_routing.py` - FIELD_FOR_CHECK entries for all 5 signals
- `src/do_uw/stages/analyze/signal_mappers.py` - Composite score computation in _map_company_fields
- `src/do_uw/stages/analyze/text_signals.py` - 9 new keyword scan definitions
- `src/do_uw/brain/output_manifest.yaml` - structural_complexity group under business_profile
- `src/do_uw/templates/html/sections/company/structural_complexity.html.j2` - Placeholder template

## Decisions Made
- Used text signal keyword counting as the primary data source for composite scores rather than accessing LLM extraction data directly. This avoids coupling the mapper to the LLM extraction schema and leverages the existing text_signals infrastructure that already scans 10-K sections.
- Added the previously-missing `vie_spe` text signal definition (was referenced by signal_mappers but never defined in _SIGNAL_DEFS, causing DATA_UNAVAILABLE).
- Fixed threshold_provenance.source values to use `d_and_o_claims_analysis` instead of novel categories, matching the brain contract test's valid source set.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Added missing vie_spe text signal definition**
- **Found during:** Task 2 (text signal definitions)
- **Issue:** `vie_spe` was referenced by signal_mappers.py but never defined in _SIGNAL_DEFS, causing all VIE/SPE text signal lookups to return None
- **Fix:** Added vie_spe to _SIGNAL_DEFS scanning item8 and item7 for VIE/SPE keywords
- **Files modified:** src/do_uw/stages/analyze/text_signals.py
- **Verification:** Import and key lookup confirmed
- **Committed in:** ccc27e7 (Task 2 commit)

**2. [Rule 1 - Bug] Fixed threshold_provenance.source categories**
- **Found during:** Task 3 (brain contract test validation)
- **Issue:** Initial YAML used `sec_enforcement_trends` and `enron_era_reform_analysis` which aren't in the brain contract test's valid source set
- **Fix:** Changed both to `d_and_o_claims_analysis` (valid category) and moved descriptive text to rationale
- **Files modified:** src/do_uw/brain/signals/biz/structural.yaml
- **Committed in:** deb371f (Task 3 commit)

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both fixes necessary for correctness. No scope creep.

## Issues Encountered
- Pre-existing test failure in `test_threshold_provenance_categorized` caused by Phase 94's `BIZ.OPS.subsidiary_structure` signal using `'D&O underwriting practice'` instead of `'underwriting_practice'`. Not caused by Phase 96 changes, not in scope to fix.
- Pre-existing test failure in `test_two_column_layout` caused by Phase 95's missing `corporate_events.html.j2` template. Not caused by Phase 96 changes.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 5 structural complexity signals are defined, routed, and mapped
- Signals will fire during pipeline runs once 10-K text is available (text_signals scans filing sections)
- Phase 100 (Display Integration) will build the full rendering layout for structural_complexity data
- Phase 99 (Scoring) can now score structural complexity dimensions

---
*Phase: 96-structural-complexity-extraction*
*Completed: 2026-03-10*
