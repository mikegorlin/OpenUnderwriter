---
phase: 33-brain-driven-worksheet-architecture
plan: 04
subsystem: brain, extraction, models
tags: [enrichment-data, checks-json, subsection-mapping, yfinance, gics, sic, valuation-ratios]

# Dependency graph
requires:
  - phase: 33-01
    provides: "Initial v6_subsection_ids mapping and enrichment_data.py"
  - phase: 33-03
    provides: "Zero-coverage checks with v6_subsection_ids"
provides:
  - "36-subsection v6_subsection_ids mapping (down from 45)"
  - "Section 4 reorganization: 4.1=People Risk, 4.2=Structural Governance, 4.3=Transparency, 4.4=Activist"
  - "Easy-win yfinance fields: volume, valuation ratios, analyst count, GICS code"
  - "SIC-to-GICS 130-entry mapping config"
affects: [33-06, render, analyze, score]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "SIC->GICS config-driven mapping pattern via config/sic_gics_mapping.json"
    - "_populate_easy_win_fields helper pattern for batch field extraction from yfinance info dict"

key-files:
  created:
    - src/do_uw/config/sic_gics_mapping.json
    - tests/brain/test_subsection_reorg.py
    - tests/stages/extract/test_market_easy_wins.py
  modified:
    - src/do_uw/brain/enrichment_data.py
    - src/do_uw/brain/checks.json
    - src/do_uw/models/market.py
    - src/do_uw/models/market_events.py
    - src/do_uw/models/company.py
    - src/do_uw/stages/extract/stock_performance.py
    - src/do_uw/stages/extract/earnings_guidance.py
    - src/do_uw/stages/extract/company_profile.py
    - tests/brain/test_brain_enrich.py
    - tests/brain/test_enrichment_coverage.py
    - tests/brain/test_zero_coverage_checks.py

key-decisions:
  - "Added valuation ratios (pe_ratio, forward_pe, ev_ebitda, peg_ratio) directly to StockPerformance rather than creating a separate ValuationMetrics sub-model -- keeps the model flat and aligns with existing avg_daily_volume placement"
  - "GICS code resolved from SIC->GICS mapping config only (not yfinance sectorKey/industryKey) because yfinance does not expose the 8-digit GICS code directly -- it provides sector/industry names which are not reliably mappable to specific GICS codes"
  - "analyst_count on AnalystSentimentProfile mirrors coverage_count (both from numberOfAnalystOpinions) to provide an explicit field for the check engine while maintaining backward compatibility"

patterns-established:
  - "Config-driven industry mapping: SIC codes resolved to GICS via JSON config at src/do_uw/config/sic_gics_mapping.json"
  - "Easy-win extraction pattern: _populate_easy_win_fields() extracts multiple fields from a single yfinance dict in one pass"

requirements-completed: [SC1-question-specs, SC2-section-artifacts, SC3-acquisition-audit]

# Metrics
duration: 45min
completed: 2026-02-20
---

# Phase 33 Plan 04: Subsection Reorganization and Easy-Win Field Extraction Summary

**Codified 45->36 subsection reorganization into enrichment_data.py and checks.json, surfaced 7 easy-win yfinance fields (volume, PE, forward PE, EV/EBITDA, PEG, analyst count, GICS code) into state models with extraction and 130-entry SIC-GICS mapping**

## Performance

- **Duration:** ~45 min (across two context windows due to compaction)
- **Started:** 2026-02-20T~02:30:00Z
- **Completed:** 2026-02-21T03:21:56Z
- **Tasks:** 2
- **Files modified:** 13

## Accomplishments
- Reorganized enrichment_data.py SUBDOMAIN_TO_RISK_QUESTIONS and CHECK_TO_RISK_QUESTIONS from 45 to 36 subsection IDs, reflecting the question review's absorption of 1.5/1.7/1.10, Section 4 restructure (9->4 subsections), and 5.7+5.8+5.9 merge
- Regenerated v6_subsection_ids for all 396 checks in checks.json (125 checks updated, 0 violations)
- Created 130-entry SIC-to-GICS mapping config covering all major industries
- Added 7 new model fields across StockPerformance (5), AnalystSentimentProfile (1), and CompanyProfile (1)
- Populated all new fields from yfinance info dict during extraction with proper SourcedValue provenance
- Updated 3 existing test files for the new 36-subsection structure and wrote 37 new tests (16 reorg + 21 easy-win)

## Task Commits

Each task was committed atomically:

1. **Task 1: Reorganize subsection mappings (45->36)** - `db1bae9` + `6fcd765` (feat)
   - db1bae9: New files (sic_gics_mapping.json, test_subsection_reorg.py)
   - 6fcd765: Modified files (enrichment_data.py, 3 existing test files)
2. **Task 2: Surface easy-win yfinance fields** - `8f55770` (feat)

## Files Created/Modified
- `src/do_uw/brain/enrichment_data.py` - Updated SUBDOMAIN_TO_RISK_QUESTIONS and CHECK_TO_RISK_QUESTIONS for 36-subsection structure
- `src/do_uw/brain/checks.json` - Regenerated v6_subsection_ids for all 396 checks (125 updated)
- `src/do_uw/config/sic_gics_mapping.json` - 130-entry SIC-to-GICS code mapping
- `src/do_uw/models/market.py` - Added avg_daily_volume, pe_ratio, forward_pe, ev_ebitda, peg_ratio to StockPerformance
- `src/do_uw/models/market_events.py` - Added analyst_count to AnalystSentimentProfile
- `src/do_uw/models/company.py` - Added gics_code to CompanyProfile
- `src/do_uw/stages/extract/stock_performance.py` - Added _populate_easy_win_fields() for volume and valuation ratios
- `src/do_uw/stages/extract/earnings_guidance.py` - Added analyst_count population from numberOfAnalystOpinions
- `src/do_uw/stages/extract/company_profile.py` - Added _resolve_gics_code() with SIC->GICS mapping fallback
- `tests/brain/test_subsection_reorg.py` - 16 tests for reorganization validation
- `tests/brain/test_brain_enrich.py` - Updated NLP risk mapping assertion (4.6->4.3)
- `tests/brain/test_enrichment_coverage.py` - Updated for 36-subsection ID set
- `tests/brain/test_zero_coverage_checks.py` - Updated for merged subsection structure
- `tests/stages/extract/test_market_easy_wins.py` - 21 tests for easy-win field extraction

## Decisions Made
- Added valuation ratios directly to StockPerformance rather than creating a separate ValuationMetrics sub-model -- keeps the model flat and consistent with existing field placement
- GICS code resolved from SIC->GICS config mapping only (not yfinance sectorKey/industryKey) because yfinance does not expose the 8-digit GICS code directly
- analyst_count mirrors coverage_count on AnalystSentimentProfile to provide an explicit field for check engine routing while maintaining backward compatibility

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated 3 existing test files for 36-subsection structure**
- **Found during:** Task 1
- **Issue:** Existing brain tests (test_brain_enrich.py, test_enrichment_coverage.py, test_zero_coverage_checks.py) hardcoded old 45-subsection IDs (4.5, 4.6, 4.7, 4.8, 4.9, 5.8, 5.9). 9 tests failing after enrichment_data.py update.
- **Fix:** Updated all three test files: changed assertions from old to new subsection IDs, updated _V6_SECTION_RANGES, added _V6_VALID_SUBSECTION_IDS set, updated ZERO_COVERAGE_SUBSECTIONS from 5 to 3 subsections.
- **Files modified:** tests/brain/test_brain_enrich.py, tests/brain/test_enrichment_coverage.py, tests/brain/test_zero_coverage_checks.py
- **Verification:** All 246 brain tests pass
- **Committed in:** 6fcd765

**2. [Rule 3 - Blocking] No market_signals.py file exists -- extraction code located in stock_performance.py and earnings_guidance.py**
- **Found during:** Task 2
- **Issue:** Plan referenced `src/do_uw/stages/extract/market_signals.py` and `market_helpers.py` which do not exist. Market extraction is split across stock_performance.py (performance metrics, stock drops) and earnings_guidance.py (analyst sentiment).
- **Fix:** Placed _populate_easy_win_fields in stock_performance.py (where yfinance info dict is already consumed), analyst_count in earnings_guidance.py, and GICS code in company_profile.py.
- **Files modified:** src/do_uw/stages/extract/stock_performance.py, src/do_uw/stages/extract/earnings_guidance.py, src/do_uw/stages/extract/company_profile.py
- **Committed in:** 8f55770

---

**Total deviations:** 2 auto-fixed (1 bug fix, 1 blocking issue)
**Impact on plan:** Both auto-fixes were necessary for correctness. Test updates were required by the enrichment_data changes. File location deviation had no functional impact -- the extraction logic went into the correct existing files.

## Issues Encountered
- Task 1 required two commits because the first `git add` only staged new files (sic_gics_mapping.json, test_subsection_reorg.py), missing the modified files (enrichment_data.py, test files). Resolved by making a second commit with the remaining modified files.
- checks.json regeneration showed no git diff despite the Python script reporting 125 checks updated -- the formatted JSON output was byte-identical to what was already committed (the file had been pre-updated in an earlier session).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- 36-subsection structure is now codified and tested, ready for Section 4 governance rendering (33-06)
- All easy-win yfinance fields are available in state models for check evaluation and worksheet rendering
- SIC-GICS mapping enables industry-specific analysis for any company with SEC filings
- Pre-existing pyright issue in company_profile.py:218 (_validate_employee_count return type) is out of scope -- flagged as known issue

## Self-Check: PASSED

- [x] src/do_uw/config/sic_gics_mapping.json exists
- [x] tests/brain/test_subsection_reorg.py exists
- [x] tests/stages/extract/test_market_easy_wins.py exists
- [x] Commit db1bae9 found
- [x] Commit 6fcd765 found
- [x] Commit 8f55770 found

---
*Phase: 33-brain-driven-worksheet-architecture*
*Completed: 2026-02-20*
