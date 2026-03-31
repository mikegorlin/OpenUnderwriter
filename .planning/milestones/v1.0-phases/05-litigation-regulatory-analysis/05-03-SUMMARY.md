---
phase: 05-litigation-regulatory-analysis
plan: 03
subsystem: extract
tags: [regulatory, deal-litigation, workforce, product, environmental, cybersecurity, whistleblower, FCPA, EEOC, OSHA]

# Dependency graph
requires:
  - phase: 05-01
    provides: "Litigation models (RegulatoryProceeding, DealLitigation, WorkforceProductEnvironmental, WhistleblowerIndicator), filing sections, claim_types.json"
provides:
  - "Regulatory proceedings extractor (10 agency types from filings + web search)"
  - "Deal litigation extractor (5 M&A litigation types with court/settlement detection)"
  - "Workforce/product/environmental extractor (8 claim categories with whistleblower indicators)"
affects: [05-05, phase-6-scoring, phase-7-render]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Multi-source text scanning (Item 3, Item 1A, 8-K, web search, blind spot)"
    - "3-tuple extractor return for models needing secondary output (whistleblower indicators)"
    - "Deduplication by type + description prefix across multiple sources"

key-files:
  created:
    - src/do_uw/stages/extract/regulatory_extract.py
    - src/do_uw/stages/extract/deal_litigation.py
    - src/do_uw/stages/extract/workforce_product.py
    - tests/test_regulatory_extract.py
    - tests/test_deal_litigation.py
    - tests/test_workforce_product.py
  modified: []

key-decisions:
  - "3-tuple return (model, whistleblower_list, report) for workforce_product extractor to populate both WPE and whistleblower_indicators on LitigationLandscape"
  - "Dedup by agency+description[:100] for regulatory, type+description[:100] for deal/workforce to handle cross-source overlap"
  - "Extract_section 200-char minimum means test Item 3 text must be padded sufficiently for integration tests"

patterns-established:
  - "Multi-source regulatory scanning: Item 3 (HIGH) -> Item 1A (MEDIUM) -> 8-K (MEDIUM) -> web/blind-spot (LOW)"
  - "Penalty amount extraction via $X million/billion regex with multiplier conversion"
  - "Court detection patterns for Delaware Chancery, S.D.N.Y., N.D. Cal."

# Metrics
duration: 6m 45s
completed: 2026-02-08
---

# Phase 5 Plan 3: Regulatory/Deal/Workforce Extractors Summary

**Three extractors covering 10 regulatory agencies, 5 deal litigation types, and 8 workforce/product/environmental claim categories with whistleblower indicator extraction**

## Performance

- **Duration:** 6m 45s
- **Started:** 2026-02-08T17:44:20Z
- **Completed:** 2026-02-08T17:51:05Z
- **Tasks:** 2
- **Files created:** 6

## Accomplishments
- Regulatory proceedings extractor detects DOJ, FTC, FDA, EPA, CFPB, OCC, OSHA, EEOC, STATE_AG, and FCPA from 10-K Item 3, Item 1A, 8-K filings, and web/blind-spot search
- Deal litigation extractor classifies merger objections, appraisals, disclosure-only settlements, Revlon claims, and fiduciary duty challenges with court and settlement amount detection
- Workforce/product/environmental extractor covers employment, EEOC, whistleblower, WARN, product recall, mass tort, environmental, and cybersecurity categories
- Whistleblower indicators extracted as separate return value for sub-orchestrator population
- 98 new tests (36 + 24 + 38), all passing; 669/670 full suite passing (1 pre-existing failure in parallel agent's sca_extractor)

## Task Commits

Each task was committed atomically:

1. **Task 1: Regulatory proceedings extractor (SECT6-06)** - `f91fc51` (feat)
2. **Task 2: Deal litigation + workforce/product/environmental (SECT6-07, SECT6-08)** - `430aad7` (feat)

## Files Created/Modified
- `src/do_uw/stages/extract/regulatory_extract.py` - Regulatory proceedings extraction from 10 agencies (421 lines)
- `src/do_uw/stages/extract/deal_litigation.py` - M&A deal litigation extraction with 5 types (350 lines)
- `src/do_uw/stages/extract/workforce_product.py` - Workforce/product/environmental extraction with 8 categories (422 lines)
- `tests/test_regulatory_extract.py` - 36 tests for regulatory extraction
- `tests/test_deal_litigation.py` - 24 tests for deal litigation extraction
- `tests/test_workforce_product.py` - 38 tests for workforce/product/environmental extraction

## Decisions Made
- **3-tuple return for workforce extractor:** The sub-orchestrator needs both the WPE model and a separate whistleblower indicator list. Returning (model, whistleblower_list, report) lets the wrapper unpack and populate both fields on LitigationLandscape.
- **Deduplication by type + description prefix:** Cross-source scanning (filings + web search) produces duplicates. Using agency/type + first 100 chars of description as dedup key eliminates N^2 blowup while keeping genuinely different findings.
- **Padding test Item 3 text:** The `extract_section` function rejects sections under 200 chars to filter table-of-contents false positives. Integration tests that use `_make_10k_with_item3()` must pad text to exceed this threshold.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test Item 3 text too short for section extraction**
- **Found during:** Task 2 (deal litigation integration tests)
- **Issue:** Two tests failed because the synthetic Item 3 text was under 200 chars, causing `extract_section()` to return empty string
- **Fix:** Padded test Item 3 text with repeated context sentences to exceed 200-char minimum
- **Files modified:** tests/test_deal_litigation.py
- **Verification:** All 62 tests pass after fix
- **Committed in:** 430aad7 (part of Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Minor test data adjustment. No scope creep.

## Issues Encountered
- Pre-existing test failure in `tests/test_sca_extractor.py::TestTimeHorizon::test_old_efts_case_filtered` from parallel agent 05-02's work. Confirmed not caused by 05-03 changes (fails on stash pop without 05-03 files present).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Three extractors ready for integration into litigation sub-orchestrator (05-05)
- workforce_product.py's 3-tuple return requires sub-orchestrator to unpack (model, whistleblowers, report) rather than standard 2-tuple
- All file line counts well under 500 (421, 350, 422)

---
*Phase: 05-litigation-regulatory-analysis*
*Completed: 2026-02-08*
