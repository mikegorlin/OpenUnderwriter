---
phase: 117-forward-looking-risk-framework
plan: 02
subsystem: extract, analyze
tags: [forward-looking, llm-extraction, credibility, miss-risk, sca-mapping, earnings, yfinance]

# Dependency graph
requires:
  - phase: 117-forward-looking-risk-framework (plan 01)
    provides: ForwardLookingData Pydantic models, LLM extraction schema, AnalysisState integration
provides:
  - Forward statement LLM extraction from 10-K/8-K filings (extract_forward_statements)
  - Growth estimate extraction from yfinance market data
  - Management credibility scoring from historical beat/miss records (compute_credibility_score)
  - Miss risk computation with credibility-adjusted gap analysis (compute_miss_risk)
  - Deterministic SCA relevance mapping for D&O litigation theories (map_sca_relevance)
  - Forward statement enrichment combining miss risk + SCA + rationale (enrich_forward_statements)
affects: [117-03, 117-04, 117-05, 117-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "LLM extraction with mocked _run_llm_extraction for testability"
    - "Credibility scoring from yfinance EarningsQuarterRecord data"
    - "Deterministic SCA mapping (not LLM-generated) for legal theory classification"
    - "Metric classification (material/financial) for SCA relevance dispatch"

key-files:
  created:
    - src/do_uw/stages/extract/forward_statements.py
    - src/do_uw/stages/analyze/credibility_engine.py
    - src/do_uw/stages/analyze/miss_risk.py
    - tests/stages/extract/test_forward_statements.py
    - tests/stages/analyze/test_credibility_engine.py
    - tests/stages/analyze/test_miss_risk.py
  modified: []

key-decisions:
  - "Miss risk uses >= 5 for MEDIUM threshold (5% gap IS medium risk, not low)"
  - "Credibility engine maps MEET results to INLINE for credibility assessment (not counted as beat or miss)"
  - "Forward statement extraction caps at 3 filings per type to bound LLM cost"
  - "SCA mapping is purely deterministic with metric classification heuristics for material/financial dispatch"

patterns-established:
  - "Mock _run_llm_extraction for unit testing LLM extraction modules"
  - "Credibility scoring pattern: yfinance earnings -> CredibilityQuarter records -> aggregate beat rate -> level"
  - "Gap-based risk with credibility adjustment: base_level +/- 1, capped at [0, 2]"

requirements-completed: [FORWARD-01, FORWARD-02, FORWARD-03, FORWARD-05, FORWARD-06]

# Metrics
duration: 15min
completed: 2026-03-19
---

# Phase 117 Plan 02: Extraction & Analysis Engines Summary

**LLM-powered forward statement extraction from 10-K/8-K, credibility scoring from yfinance earnings history, and credibility-adjusted miss risk with deterministic SCA relevance mapping**

## Performance

- **Duration:** 15 min
- **Started:** 2026-03-19T23:57:39Z
- **Completed:** 2026-03-20T00:12:39Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Forward statement extraction from SEC filings via LLM with support for both quantitative and qualitative guidance companies
- Management credibility engine computing beat rate from yfinance EPS estimates vs actuals with HIGH/MEDIUM/LOW/UNKNOWN classification
- Miss risk algorithm implementing CONTEXT.md thresholds (>10% HIGH, >=5% MEDIUM, <5% LOW) with credibility adjustment (+1 for LOW, -1 for HIGH credibility)
- Deterministic SCA relevance mapping: HIGH+material -> 10b-5, MEDIUM+financial -> earnings fraud theory
- 38 tests across 3 test files, all passing

## Task Commits

Each task was committed atomically:

1. **Task 1: Forward statement extraction + credibility engine** - `cc89b4e6` (feat)
2. **Task 2: Miss risk computation + SCA relevance mapping** - `1c069d35` (feat)

_Note: TDD tasks -- tests written first, then implementation._

## Files Created/Modified
- `src/do_uw/stages/extract/forward_statements.py` - LLM extraction of forward statements, catalysts, and growth estimates from SEC filings + yfinance
- `src/do_uw/stages/analyze/credibility_engine.py` - Management credibility scoring from historical earnings beat/miss records
- `src/do_uw/stages/analyze/miss_risk.py` - Gap-based miss risk with credibility adjustment and deterministic SCA mapping
- `tests/stages/extract/test_forward_statements.py` - 7 tests for extraction module
- `tests/stages/analyze/test_credibility_engine.py` - 8 tests for credibility engine
- `tests/stages/analyze/test_miss_risk.py` - 23 tests for miss risk and SCA mapping

## Decisions Made
- Used `>= 5` (not `> 5`) for MEDIUM threshold so exactly 5% gap is classified as MEDIUM risk, aligning with CONTEXT.md "5-10% = MEDIUM" specification
- Credibility engine maps EarningsResult.MEET to "INLINE" (not BEAT or MISS) for accurate credibility assessment
- Forward statement extraction caps at 3 filings per type (10-K, 20-F, 8-K) to control LLM cost while still capturing multiple filing types
- SCA mapping uses metric classification heuristics (material_markers, financial_markers) for dispatch beyond exact string matching

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed 5% gap boundary classification**
- **Found during:** Task 2 (miss risk tests)
- **Issue:** Initial implementation used `> 5` for MEDIUM threshold, causing exactly 5% gap to be classified as LOW instead of MEDIUM
- **Fix:** Changed to `>= 5` to match CONTEXT.md specification "5-10% = MEDIUM"
- **Files modified:** src/do_uw/stages/analyze/miss_risk.py
- **Verification:** test_exact_5_pct_gap_is_medium passes
- **Committed in:** 1c069d35 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Essential for correct threshold behavior. No scope creep.

## Issues Encountered
- Pre-existing test failures in `tests/stages/benchmark/test_monitoring_triggers.py` and `tests/stages/benchmark/test_quick_screen.py` (modules from future plans not yet implemented). Also pre-existing `test_threshold_provenance_categorized` failure documented in 117-01-SUMMARY.md. None related to this plan's changes.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All 3 extraction/analysis engines ready for pipeline integration
- `extract_forward_statements` populates ForwardStatement, CatalystEvent, GrowthEstimate models
- `compute_credibility_score` produces CredibilityScore from state.extracted.market.earnings_guidance
- `compute_miss_risk` + `enrich_forward_statements` ready for post-extraction enrichment
- Plans 03-06 can import these functions directly for pipeline wiring, context building, and rendering

---
*Phase: 117-forward-looking-risk-framework*
*Completed: 2026-03-19*
