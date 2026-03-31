---
phase: 05-litigation-regulatory-analysis
plan: 01
subsystem: models
tags: [pydantic, litigation, sec-enforcement, filing-sections, config-json, strenum]

# Dependency graph
requires:
  - phase: 03-financial-data-extraction
    provides: "Filing section parsing (filing_sections.py), SourcedValue pattern, ExtractionReport pattern"
  - phase: 04-market-trading-governance-analysis
    provides: "Governance model split pattern (governance.py + governance_forensics.py)"
provides:
  - "LitigationLandscape with typed fields for all 12 SECT6 sub-areas"
  - "CaseDetail with two-layer classification (coverage_type + legal_theories)"
  - "SECEnforcementPipeline with 6-stage pipeline tracking"
  - "10 litigation detail sub-models in litigation_details.py"
  - "4 StrEnum types (CoverageType, LegalTheory, EnforcementStage, CaseStatus)"
  - "Item 3 and Item 1A section extraction from 10-K text"
  - "3 config JSON files (lead_counsel_tiers, claim_types, industry_theories)"
affects:
  - 05-02 (securities class action extractor needs CaseDetail + CoverageType)
  - 05-03 (SEC enforcement extractor needs SECEnforcementPipeline + EnforcementStage)
  - 05-04 (regulatory extractor needs RegulatoryProceeding + WorkforceProductEnvironmental)
  - 05-05 (defense/SOL/timeline extractors need DefenseAssessment + SOLWindow + LitigationTimelineEvent)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Litigation model split: litigation.py (~330 lines) + litigation_details.py (~430 lines)"
    - "StrEnum classification types for D&O coverage and legal theories"
    - "Backward-compat alias: SECEnforcement = SECEnforcementPipeline"

key-files:
  created:
    - src/do_uw/models/litigation_details.py
    - src/do_uw/config/lead_counsel_tiers.json
    - src/do_uw/config/claim_types.json
    - src/do_uw/config/industry_theories.json
    - tests/test_litigation_models.py
  modified:
    - src/do_uw/models/litigation.py
    - src/do_uw/models/__init__.py
    - src/do_uw/stages/extract/filing_sections.py
    - tests/test_acquire_extensions.py

key-decisions:
  - "event_date field name in LitigationTimelineEvent to avoid shadowing date type (from __future__ annotations + Pydantic field collision)"
  - "SECEnforcement = SECEnforcementPipeline backward-compat alias preserves Phase 3 imports"
  - "Item 1A inserted after Item 1, Item 3 after Item 1A in SECTION_DEFS ordering"

patterns-established:
  - "Litigation model hierarchy: litigation.py (enums + top-level) imports from litigation_details.py (sub-models)"
  - "Config JSON files in src/do_uw/config/ loaded via Path(__file__) pattern (same as xbrl_concepts, adverse_events)"

# Metrics
duration: 7m 44s
completed: 2026-02-08
---

# Phase 5 Plan 01: Litigation Foundation Models Summary

**Typed SECT6 litigation model hierarchy with 4 StrEnums, 10 detail sub-models, Item 3/1A section parsing, and 3 config JSON files for claim types, counsel tiers, and industry theories**

## Performance

- **Duration:** 7m 44s
- **Started:** 2026-02-08T17:33:19Z
- **Completed:** 2026-02-08T17:41:03Z
- **Tasks:** 2/2
- **Files modified:** 9 (5 created, 4 modified)
- **Tests:** 513 total (37 new, 476 existing, 0 failures)

## Accomplishments
- Expanded LitigationLandscape with typed fields for all 12 SECT6 sub-areas
- Created CaseDetail two-layer classification with CoverageType + LegalTheory StrEnums
- Added Item 3 (Legal Proceedings) and Item 1A (Risk Factors) section parsing
- Created 3 config JSON files for lead counsel tiers, claim types with SOL/repose, and industry-specific legal theories
- 37 comprehensive tests covering models, serialization, config loading, and section extraction

## Task Commits

Each task was committed atomically:

1. **Task 1: Expand litigation models into litigation.py + litigation_details.py** - `d701872` (feat)
2. **Task 2: Add Item 3 and Item 1A to filing_sections.py + create config files** - `273c936` (feat)

## Files Created/Modified
- `src/do_uw/models/litigation.py` - Expanded with 4 StrEnums, expanded CaseDetail, SECEnforcementPipeline, expanded LitigationLandscape (329 lines)
- `src/do_uw/models/litigation_details.py` - 10 sub-models: RegulatoryProceeding, DealLitigation, WorkforceProductEnvironmental, ForumProvisions, DefenseAssessment, IndustryClaimPattern, SOLWindow, ContingentLiability, WhistleblowerIndicator, LitigationTimelineEvent (432 lines)
- `src/do_uw/models/__init__.py` - Added all new exports (18 new symbols)
- `src/do_uw/stages/extract/filing_sections.py` - Added item1a and item3 to SECTION_DEFS (158 lines)
- `src/do_uw/config/lead_counsel_tiers.json` - Tier 1/2/3 plaintiff law firm lists with substring match strategy
- `src/do_uw/config/claim_types.json` - 9 claim types with SOL/repose years, triggers, and coverage types
- `src/do_uw/config/industry_theories.json` - 8 SIC ranges mapped to industry-specific legal theories
- `tests/test_litigation_models.py` - 37 tests across 8 test classes
- `tests/test_acquire_extensions.py` - Updated SECTION_DEFS count from 3 to 5

## Decisions Made
- **event_date field name:** Renamed `date` to `event_date` in LitigationTimelineEvent because `from __future__ import annotations` + Pydantic caused the field `date` to shadow the `date` type, triggering a TypeError during model construction
- **SECEnforcement backward-compat alias:** Preserved `SECEnforcement = SECEnforcementPipeline` alias so existing Phase 3 imports continue working
- **SECTION_DEFS ordering:** item1a after item1, item3 after item1a (logical document order, readability)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed field name collision in LitigationTimelineEvent**
- **Found during:** Task 1 (litigation model expansion)
- **Issue:** Field `date: date | None` in LitigationTimelineEvent shadowed the `date` type from `datetime` module. With `from __future__ import annotations`, Pydantic evaluated the annotation lazily and resolved `date` to the FieldInfo, not the type, causing `TypeError: unsupported operand type(s) for |: 'FieldInfo' and 'NoneType'`
- **Fix:** Renamed field from `date` to `event_date`
- **Files modified:** src/do_uw/models/litigation_details.py
- **Verification:** `LitigationLandscape()` serializes without error, pyright clean
- **Committed in:** d701872 (Task 1 commit)

**2. [Rule 1 - Bug] Updated existing test for expanded SECTION_DEFS count**
- **Found during:** Task 2 (full test suite regression check)
- **Issue:** `test_section_defs_has_three_sections` asserted `len(SECTION_DEFS) == 3`, but we added 2 new sections (item1a, item3) making it 5
- **Fix:** Updated assertion to `== 5` and added item1a/item3 to section name assertions
- **Files modified:** tests/test_acquire_extensions.py
- **Verification:** Full test suite passes (513/513)
- **Committed in:** 273c936 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both auto-fixes necessary for correctness. No scope creep.

## Issues Encountered
None beyond the auto-fixed deviations above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All SECT6 model types ready for Phase 5 extractors (plans 02-05)
- Item 3 and Item 1A parsing available for litigation extraction
- Config files provide claim type taxonomy, counsel tier classification, and industry theory mapping
- 513 tests passing, 0 lint/type errors, all files under 500 lines

---
*Phase: 05-litigation-regulatory-analysis*
*Completed: 2026-02-08*
