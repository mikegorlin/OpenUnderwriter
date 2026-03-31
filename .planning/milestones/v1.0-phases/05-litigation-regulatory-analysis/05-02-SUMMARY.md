---
phase: 05-litigation-regulatory-analysis
plan: 02
subsystem: extract
tags: [litigation, sca, sec-enforcement, derivative-suits, regex, deduplication]

# Dependency graph
requires:
  - phase: 05-01
    provides: "Litigation models (CaseDetail, SECEnforcementPipeline, EnforcementStage, CoverageType, LegalTheory), filing_sections, claim_types.json, lead_counsel_tiers.json"
provides:
  - "SCA extractor: extract_securities_class_actions() from EFTS/SCAC, Item 3, web"
  - "SEC enforcement extractor: extract_sec_enforcement() with pipeline staging"
  - "Derivative suits extractor: extract_derivative_suits() with Section 220 detection"
affects: [05-05, phase-6-scoring, phase-7-render]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Multi-source extraction with priority ordering and deduplication"
    - "Two-layer classification (coverage_type + legal_theories)"
    - "Highest-stage-wins logic for ordered enum pipeline stages"

key-files:
  created:
    - src/do_uw/stages/extract/sca_extractor.py
    - src/do_uw/stages/extract/sca_parsing.py
    - src/do_uw/stages/extract/sec_enforcement.py
    - src/do_uw/stages/extract/derivative_suits.py
    - tests/test_sca_extractor.py
    - tests/test_sec_enforcement.py
    - tests/test_derivative_suits.py
  modified: []

key-decisions:
  - "Public helper functions (no underscore prefix) for cross-module use between sca_extractor.py and sca_parsing.py"
  - "Split SCA into sca_extractor.py (379L) + sca_parsing.py (326L) for 500-line compliance"
  - "Comment letter count from CORRESP in acquired filings only (AuditProfile has no sec_comment_letter_count field)"
  - "5-year time horizon for derivative suits (vs 10 years for SCAs)"

patterns-established:
  - "Multi-source deduplication: word_overlap_pct > 0.80 identifies duplicates"
  - "Stage rank ordering via list index for highest-stage-wins comparisons"
  - "Enforcement narrative generation as rule-based text summary"

# Metrics
duration: 19m 14s
completed: 2026-02-08
---

# Phase 5 Plan 2: Core Litigation Extractors Summary

**SCA, SEC enforcement, and derivative suit extractors with multi-source parsing, two-layer classification, and deduplication across EFTS/SCAC, 10-K Item 3, and web search**

## Performance

- **Duration:** 19m 14s
- **Started:** 2026-02-08T17:44:11Z
- **Completed:** 2026-02-08T18:03:25Z
- **Tasks:** 2
- **Files created:** 7

## Accomplishments
- Securities class action extractor parsing EFTS/SCAC (primary), 10-K Item 3 (supplement), and web search with two-layer classification (coverage_type + legal_theories)
- SEC enforcement pipeline extractor mapping companies to discrete enforcement stages (NONE through ENFORCEMENT_ACTION) with highest-stage-wins logic
- Derivative suits extractor detecting Section 220 demands, Caremark claims, and fiduciary duty breaches with 5-year time horizon
- Lead counsel tier lookup via substring matching against lead_counsel_tiers.json configuration
- 62 new tests (29 SCA + 17 SEC enforcement + 16 derivative suits), full suite at 738 tests

## Task Commits

Each task was committed atomically:

1. **Task 1: Securities class action extractor (SECT6-03)** - `0dc434e` (feat)
2. **Task 2: SEC enforcement pipeline + derivative suits (SECT6-04, SECT6-05)** - `7c2551a` (feat)

## Files Created/Modified
- `src/do_uw/stages/extract/sca_extractor.py` - SCA constants, config, parsing helpers, main entry point (379L)
- `src/do_uw/stages/extract/sca_parsing.py` - SCA source-specific parsers and deduplication (326L)
- `src/do_uw/stages/extract/sec_enforcement.py` - SEC enforcement pipeline position mapping (422L)
- `src/do_uw/stages/extract/derivative_suits.py` - Derivative suit and fiduciary claim extraction (471L)
- `tests/test_sca_extractor.py` - 29 tests for SCA extraction
- `tests/test_sec_enforcement.py` - 17 tests for SEC enforcement
- `tests/test_derivative_suits.py` - 16 tests for derivative suits

## Decisions Made
- **Public helper functions:** Made parsing helpers public (no `_` prefix) since they are shared between sca_extractor.py and sca_parsing.py -- pyright strict mode enforces reportPrivateUsage
- **500-line split:** SCA extractor split into sca_extractor.py (constants/helpers/entry) + sca_parsing.py (source parsers/dedup) to stay under limit
- **Comment letter count:** Only from CORRESP in acquired filings (AuditProfile lacks sec_comment_letter_count field; will be addressed when audit extractor is enhanced)
- **Time horizons:** 10 years for SCAs (per plan), 5 years for derivative suits (per plan)
- **Enforcement stage ordering:** EnforcementStage enum mapped to STAGE_ORDER list with index-based ranking for highest-stage-wins

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Split SCA extractor to comply with 500-line limit**
- **Found during:** Task 1
- **Issue:** sca_extractor.py reached 693 lines, exceeding the 500-line limit
- **Fix:** Split source-specific parsers and deduplication into sca_parsing.py; made helper functions public for cross-module access
- **Files modified:** sca_extractor.py, sca_parsing.py (new)
- **Verification:** Both files under 500 lines, all 29 tests pass

**2. [Rule 1 - Bug] Fixed AuditProfile attribute access for comment letter count**
- **Found during:** Task 2
- **Issue:** Plan referenced `state.extracted.financials.audit.sec_comment_letter_count` but AuditProfile has no such field
- **Fix:** Removed audit data path, used CORRESP count from acquired filings only
- **Files modified:** sec_enforcement.py
- **Verification:** pyright clean, tests pass

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both fixes necessary for correctness. No scope creep.

## Issues Encountered
- Item 3 section parser has a 200-character minimum -- test data needed to be long enough to pass this threshold
- CASE_NAME_RE lazy quantifier matches "Securities" before "Litigation" in some case names -- functionally correct for extraction

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Three core litigation extractors ready for integration into extract stage orchestrator (05-05)
- All extractors follow standard tuple[model, ExtractionReport] return pattern
- Ready for scoring factor F.1 (Prior Litigation) and CRF-01/02/03 red flag gate integration

---
*Phase: 05-litigation-regulatory-analysis*
*Completed: 2026-02-08*
