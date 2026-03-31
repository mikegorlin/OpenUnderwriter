---
phase: 119-stock-drop-catalysts-competitive-landscape-alt-data
plan: 04
subsystem: benchmark
tags: [d&o-assessment, stock-drops, competitive-landscape, alt-data, litigation-theory]

# Dependency graph
requires:
  - phase: 119-02
    provides: StockDropEvent catalyst fields, CompetitiveLandscape model
  - phase: 119-03
    provides: AltDataAssessments extraction (ESG, AI-washing, tariff, peer SCA)
provides:
  - generate_drop_do_assessments() maps 8 catalyst types to D&O litigation theories
  - generate_drop_pattern_narrative() summarizes overall drop pattern significance
  - enrich_competitive_landscape() adds do_commentary and per-moat do_risk
  - enrich_alt_data() populates do_relevance on ESG, AI-washing, tariff, peer SCA
affects: [119-05, 119-06]

# Tech tracking
tech-stack:
  added: []
  patterns: [catalyst-to-litigation-theory mapping, moat-erosion-risk templates]

key-files:
  created:
    - src/do_uw/stages/benchmark/stock_drop_narrative.py
    - src/do_uw/stages/benchmark/competitive_enrichment.py
    - src/do_uw/stages/benchmark/alt_data_enrichment.py
    - tests/stages/benchmark/test_stock_drop_narrative.py
    - tests/stages/benchmark/test_competitive_enrichment.py
    - tests/stages/benchmark/test_alt_data_enrichment.py
  modified: []

key-decisions:
  - "Used state.ticker as company name fallback (CompanyProfile.identity.legal_name may be None)"
  - "Moat do_risk only populated for Weak/Moderate moats (Strong moats = no erosion concern)"
  - "Alt data enrichment uses import-inside-function pattern for type narrowing"

patterns-established:
  - "Catalyst-to-theory mapping: _CATALYST_DO_MAP dict maps trigger_category to D&O litigation theory templates"
  - "Company name resolution: _get_company_name() with legal_name -> ticker -> 'Company' fallback chain"

requirements-completed: [STOCK-01, STOCK-03, DOSSIER-07, ALTDATA-01, ALTDATA-02, ALTDATA-03, ALTDATA-04]

# Metrics
duration: 6min
completed: 2026-03-20
---

# Phase 119 Plan 04: D&O Assessment Narratives Summary

**3 BENCHMARK enrichment modules mapping stock drop catalysts, competitive moat erosion, and alt data findings to specific D&O litigation theories with 42 TDD tests**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-20T17:03:38Z
- **Completed:** 2026-03-20T17:10:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- 8 catalyst types mapped to D&O litigation theories (earnings_miss -> 10(b), guidance_cut -> safe harbor failure, restatement -> Section 11 strict liability, etc.)
- Overall drop pattern narrative classifying catalytic vs gradual decline with D&O implications
- Competitive landscape enrichment with 7 moat-erosion risk templates (Scale, Switching, Brand, Network, Data, Regulatory, Distribution)
- 4 alt data D&O relevance narratives: ESG (Caremark duty), AI-washing (10(b)/SEC enforcement), tariff (Section 10(b) omission), peer SCA (contagion/copycat)

## Task Commits

Each task was committed atomically:

1. **Task 1: Stock drop D&O assessments + pattern narrative** - `b526d76d` (feat)
2. **Task 2: Competitive landscape + alt data D&O enrichment** - `aaa41022` (feat)

_Both tasks used TDD: tests written first, then implementation._

## Files Created/Modified
- `src/do_uw/stages/benchmark/stock_drop_narrative.py` - D&O assessment generation for each drop catalyst type
- `src/do_uw/stages/benchmark/competitive_enrichment.py` - Competitive landscape D&O commentary and per-moat erosion risk
- `src/do_uw/stages/benchmark/alt_data_enrichment.py` - Alt data D&O relevance narratives (ESG, AI-washing, tariff, peer SCA)
- `tests/stages/benchmark/test_stock_drop_narrative.py` - 19 tests covering all catalyst types + pattern narrative
- `tests/stages/benchmark/test_competitive_enrichment.py` - 10 tests covering moat enrichment + empty state
- `tests/stages/benchmark/test_alt_data_enrichment.py` - 13 tests covering all alt data assessment types

## Decisions Made
- Used `state.ticker` as company name fallback since CompanyProfile may be None in BENCHMARK stage -- matches dossier_enrichment.py pattern
- Moat do_risk only populated for Weak/Moderate strength (Strong moats don't need erosion risk narrative)
- Alt data enrichment uses singular/plural grammar for controversy/indicator counts

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed company name resolution**
- **Found during:** Task 2 (competitive enrichment)
- **Issue:** Plan referenced `state.company.name` which doesn't exist -- CompanyProfile has no `name` field
- **Fix:** Created `_get_company_name()` helper using `state.company.identity.legal_name.value` with fallback to `state.ticker`
- **Files modified:** competitive_enrichment.py, alt_data_enrichment.py
- **Verification:** All tests pass with ticker-based name resolution

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential fix for correct company name resolution. No scope creep.

## Issues Encountered
- SourcedValue requires `as_of` parameter -- test helper updated to include datetime
- AnalysisState requires `ticker` parameter -- tests updated to use `ticker="ACME"` pattern

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 3 enrichment modules ready for pipeline wiring in Plan 119-05/06
- Enrichment functions follow same pattern as dossier_enrichment.py (state mutation, logging)
- 42 tests provide regression safety for template integration

---
*Phase: 119-stock-drop-catalysts-competitive-landscape-alt-data*
*Completed: 2026-03-20*
