# Phase 4 Plan 10: Market + Governance Sub-Orchestrators Summary

**One-liner:** Sub-orchestrators wiring 7 SECT4 market and 6 SECT5 governance extractors into ExtractStage with try/except isolation and rule-based governance summary

## Metadata

- **Phase:** 4
- **Plan:** 10
- **Duration:** 4m 53s
- **Completed:** 2026-02-08
- **Subsystem:** extract
- **Tags:** orchestrator, market, governance, SECT4, SECT5

## Tasks Completed

| # | Task | Commit | Key Files |
|---|------|--------|-----------|
| 1 | Market + governance sub-orchestrators | 047abbd | extract_market.py (254L), extract_governance.py (425L) |
| 2 | Wire sub-orchestrators into ExtractStage | f953d32 | `__init__.py` (383L) |

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| Lazy imports inside try/except wrappers | Each extractor imports only on call, so a single broken extractor cannot crash the entire extract stage at import time |
| Intermediate state write before adverse/coherence | Adverse event scorer reads state.extracted.market; narrative coherence reads state.extracted.governance -- both need intermediate results |
| Rule-based governance summary with 5 dimensions | Mirrors financial narrative pattern: synthesizes leadership, board, compensation, ownership, sentiment/coherence into SourcedValue[str] LOW confidence |

## Implementation Details

### extract_market.py (254 lines)
- `run_market_extractors(state, reports)` -> `MarketSignals`
- 7 extractors in order: stock_performance, insider_trading, short_interest, earnings_guidance, analyst_sentiment, capital_markets, adverse_events
- Each wrapped in try/except with logger.warning on failure
- Writes intermediate market to state before adverse event scoring

### extract_governance.py (425 lines)
- `run_governance_extractors(state, reports)` -> `GovernanceData`
- 6 extractors in order: leadership, compensation, board_governance (receives compensation for scoring), ownership, sentiment, narrative_coherence
- Writes intermediate governance to state before narrative coherence
- Generates governance_summary: rule-based text from 5 dimensions

### ExtractStage __init__.py (383 lines)
- Phase 10: calls run_market_extractors after financial narrative
- Phase 11: calls run_governance_extractors after market
- Both sub-orchestrators append to shared reports list

## Deviations from Plan

None -- plan executed exactly as written.

## Files Created/Modified

### Created
- `src/do_uw/stages/extract/extract_market.py` (254 lines)
- `src/do_uw/stages/extract/extract_governance.py` (425 lines)

### Modified
- `src/do_uw/stages/extract/__init__.py` (374 -> 383 lines)

## Verification

- ruff check: All checks passed
- pyright strict: 0 errors, 0 warnings
- Import chain: Clean import verification
- All files under 500-line limit

## Next Phase Readiness

Plan 04-11 (tests) needs to add mocks for both sub-orchestrators in existing pipeline/CLI tests, plus unit tests for the new orchestrator functions.
