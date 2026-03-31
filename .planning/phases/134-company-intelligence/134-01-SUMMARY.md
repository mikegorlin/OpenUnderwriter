---
phase: 134-company-intelligence
plan: 01
subsystem: extract
tags: [pydantic, risk-factors, supply-chain, supabase, sca, sector-d-o]

requires:
  - phase: 133-stock-and-market-intelligence
    provides: "Market intelligence data layer pattern"
provides:
  - "ConcentrationDimension, SupplyChainDependency, PeerSCARecord, SectorDOConcern Pydantic models"
  - "RiskFactorProfile classification (STANDARD/NOVEL/ELEVATED) and do_implication fields"
  - "classify_risk_factors deterministic classification function"
  - "extract_supply_chain regex-based 10-K dependency extraction"
  - "query_peer_sca_filings batch Supabase query with in. filter"
  - "sector_do_concerns.json config covering 9 sectors with D&O litigation theories"
affects: [134-02, render, extract, acquire]

tech-stack:
  added: []
  patterns: ["span-overlap dedup for regex extraction", "batch Supabase in. filter for peer queries"]

key-files:
  created:
    - src/do_uw/models/company_intelligence.py
    - src/do_uw/stages/extract/risk_factor_classify.py
    - src/do_uw/stages/extract/supply_chain_extract.py
    - config/sector_do_concerns.json
    - tests/models/test_company_intelligence.py
    - tests/stages/extract/test_risk_factor_classify.py
    - tests/stages/extract/test_supply_chain_extract.py
    - tests/stages/acquire/test_supabase_batch.py
  modified:
    - src/do_uw/models/state.py
    - src/do_uw/stages/acquire/clients/supabase_litigation.py

key-decisions:
  - "Deterministic risk factor classification (no LLM) using difflib.SequenceMatcher with 0.6 threshold"
  - "Span-overlap dedup strategy for supply chain extraction instead of context-window fingerprint"
  - "Batch peer SCA uses Supabase in. filter for single HTTP request regardless of ticker count"
  - "9 sectors in config with 3-5 concerns each, all naming specific legal theories"

patterns-established:
  - "TDD red-green for data layer modules: test models first, then extraction logic"
  - "Category-to-implication dict mapping for D&O litigation theory assignment"

requirements-completed: [COMP-01, COMP-04, COMP-05, COMP-07]

duration: 8min
completed: 2026-03-27
---

# Phase 134 Plan 01: Company Intelligence Data Layer Summary

**4 Pydantic models, risk factor classification with STANDARD/NOVEL/ELEVATED taxonomy, supply chain regex extraction, batch peer SCA query, and 9-sector D&O concern config -- all tested with 51 passing tests**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-27T06:21:15Z
- **Completed:** 2026-03-27T06:29:00Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- 4 new Pydantic models for company intelligence sub-sections (ConcentrationDimension, SupplyChainDependency, PeerSCARecord, SectorDOConcern)
- RiskFactorProfile backward-compatible extension with classification and do_implication fields
- Deterministic risk factor classifier using fuzzy title matching for YoY escalation detection
- Supply chain dependency extraction from 10-K Item 1/1A with switching cost assessment
- Batch peer SCA query using Supabase in. filter (single HTTP request for multiple tickers)
- sector_do_concerns.json covering 9 sectors with 3-5 D&O litigation theories each

## Task Commits

Each task was committed atomically:

1. **Task 1: Pydantic models + RiskFactorProfile extension + sector D&O config**
   - `57bcfb80` (test: failing tests for company intelligence models)
   - `f8203ab5` (feat: models, state extension, sector config)
2. **Task 2: Risk factor classification + supply chain extraction + batch peer SCA query**
   - `84014de2` (test: failing tests for classification, supply chain, batch SCA)
   - `3acbbedf` (feat: risk classification, supply chain extraction, batch peer SCA)

## Files Created/Modified
- `src/do_uw/models/company_intelligence.py` - 4 Pydantic models for company intelligence data
- `src/do_uw/models/state.py` - RiskFactorProfile extended with classification + do_implication
- `config/sector_do_concerns.json` - 9 sectors with D&O litigation theories
- `src/do_uw/stages/extract/risk_factor_classify.py` - Deterministic STANDARD/NOVEL/ELEVATED classification
- `src/do_uw/stages/extract/supply_chain_extract.py` - Regex-based 10-K supply chain extraction
- `src/do_uw/stages/acquire/clients/supabase_litigation.py` - Added query_peer_sca_filings batch function
- `tests/models/test_company_intelligence.py` - 14 model validation tests
- `tests/stages/extract/test_risk_factor_classify.py` - 11 classification tests
- `tests/stages/extract/test_supply_chain_extract.py` - 9 supply chain extraction tests
- `tests/stages/acquire/test_supabase_batch.py` - 5 batch query tests

## Decisions Made
- Deterministic classification without LLM: NOVEL (is_new_this_year), ELEVATED (HIGH severity + escalated/no prior match), STANDARD (everything else). Sufficient for phase 134; LLM-based classification can be added later.
- difflib.SequenceMatcher with 0.6 threshold for title matching (same approach as ten_k_yoy.py).
- Span-overlap dedup for supply chain extraction: context-window fingerprints failed on short texts; match span overlap detection is position-aware and handles all text lengths.
- 9 sectors in config: Technology, Healthcare/Pharma, Financial Services, Industrials/Manufacturing, Consumer/Retail, Energy, Real Estate, Utilities, Communications/Media.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed dedup strategy in supply chain extraction**
- **Found during:** Task 2 (supply chain extraction)
- **Issue:** Context-window fingerprint dedup collapsed when text was shorter than 2x context window (200 chars), causing all matches to share the same fingerprint and only the first being kept.
- **Fix:** Replaced context-window fingerprint with span-overlap detection using (start, end) tuples. Two matches are duplicates only if their character spans physically overlap.
- **Files modified:** src/do_uw/stages/extract/supply_chain_extract.py
- **Verification:** test_multiple_dependencies_found now passes (finds 3 deps in multi-sentence text)
- **Committed in:** 3acbbedf (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Bug fix necessary for correctness. No scope creep.

## Issues Encountered
None beyond the dedup bug caught by tests.

## Known Stubs
None - all models have real defaults and all extraction functions produce complete data.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 4 Pydantic models ready for Plan 02 context builders and templates
- classify_risk_factors ready to wire into extract pipeline
- extract_supply_chain ready to wire into extract pipeline
- query_peer_sca_filings ready to wire into acquire pipeline
- sector_do_concerns.json ready for context builder to load and match by SIC

## Self-Check: PASSED

All 6 files found, all 4 commits verified, all 11 acceptance criteria met, 51 tests passing.

---
*Phase: 134-company-intelligence*
*Completed: 2026-03-27*
