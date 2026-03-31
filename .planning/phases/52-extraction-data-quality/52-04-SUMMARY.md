---
phase: 52-extraction-data-quality
plan: 04
subsystem: extraction
tags: [volume-spikes, yfinance, signal-upgrade, web-search, brave-search]

# Dependency graph
requires:
  - phase: 49-brain-evolution
    provides: signal YAML framework and signal_mappers routing
provides:
  - Volume spike detection module (detect_volume_spikes)
  - STOCK.TRADE.volume_patterns upgraded from display to tiered evaluative signal
  - ACQUIRE-stage spike event correlation via Brave Search
  - StockPerformance model with volume_spike_count and volume_spike_events fields
affects: [render, score, analyze]

# Tech tracking
tech-stack:
  added: []
  patterns: [ACQUIRE-stage correlation helper, pre-correlated spike handoff to EXTRACT]

key-files:
  created:
    - src/do_uw/stages/extract/volume_spikes.py
    - src/do_uw/stages/acquire/spike_correlator.py
    - tests/test_volume_spikes.py
  modified:
    - src/do_uw/models/market.py
    - src/do_uw/stages/extract/stock_performance.py
    - src/do_uw/brain/signals/stock/insider.yaml
    - src/do_uw/stages/analyze/signal_mappers.py
    - src/do_uw/stages/analyze/signal_field_routing.py
    - src/do_uw/stages/acquire/orchestrator.py

key-decisions:
  - "Volume spike detection in EXTRACT, event correlation in ACQUIRE per CLAUDE.md MCP boundary"
  - "Pre-correlated spikes from ACQUIRE take priority in EXTRACT to avoid double computation"
  - "signal_mappers.py at 505 lines (was 502) -- tech debt, defer split to future plan"

patterns-established:
  - "ACQUIRE correlation helper: small focused module that takes pre-computed data and enriches via web search"
  - "Pre-correlated handoff: ACQUIRE stores results in market_data dict, EXTRACT checks for them before recomputing"

requirements-completed: [DQ-04]

# Metrics
duration: 4min
completed: 2026-02-28
---

# Phase 52 Plan 04: Volume Spike Detection Summary

**Volume spike detection with 20-day MA threshold (>= 2x), tiered signal upgrade, and ACQUIRE-stage Brave Search event correlation for spike catalysts**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-28T17:57:19Z
- **Completed:** 2026-02-28T18:01:49Z
- **Tasks:** 3
- **Files modified:** 9

## Accomplishments
- New volume_spikes.py module: detect_volume_spikes() computes spikes from yfinance history_1y using 20-day moving average, flags days with volume >= 2x average
- STOCK.TRADE.volume_patterns signal upgraded from display-only to tiered evaluative (0=clear, 1-2=yellow, 3+=red)
- New spike_correlator.py ACQUIRE helper: runs targeted Brave Search for each spike date to identify catalysts (earnings, lawsuits, analyst downgrades), budget-limited to top 5 spikes
- Full signal pipeline wiring: model fields, YAML upgrade, field routing, mapper, orchestrator integration
- 15 tests covering detection edge cases, correlation, and signal wiring verification

## Task Commits

Each task was committed atomically:

1. **Task 1: Create volume spike detection module and add model fields** - `19066ef` (feat)
2. **Task 2: Upgrade signal YAML, wire mapper, and add tests** - `1a59607` (feat)
3. **Task 3: Add ACQUIRE-stage spike event correlation via web search** - `b0d9644` (feat)

## Files Created/Modified
- `src/do_uw/stages/extract/volume_spikes.py` - Volume spike detection from yfinance history (94 lines)
- `src/do_uw/stages/acquire/spike_correlator.py` - ACQUIRE-stage spike correlation via web search (96 lines)
- `tests/test_volume_spikes.py` - 15 tests for detection, correlation, signal wiring
- `src/do_uw/models/market.py` - Added volume_spike_count and volume_spike_events to StockPerformance
- `src/do_uw/stages/extract/stock_performance.py` - Wired spike detection into extraction pipeline
- `src/do_uw/brain/signals/stock/insider.yaml` - Upgraded STOCK.TRADE.volume_patterns to tiered
- `src/do_uw/stages/analyze/signal_mappers.py` - Added volume_spike_count mapping
- `src/do_uw/stages/analyze/signal_field_routing.py` - Updated STOCK.TRADE.volume_patterns routing
- `src/do_uw/stages/acquire/orchestrator.py` - Added Phase B+++ spike correlation call

## Decisions Made
- Volume spike detection runs in EXTRACT (pure computation on existing data), event correlation runs in ACQUIRE (uses Brave Search MCP) per CLAUDE.md MCP boundary
- Pre-correlated spikes from ACQUIRE take priority over re-detection in EXTRACT to avoid double computation
- signal_mappers.py at 505 lines (was 502 pre-existing) -- tech debt acknowledged, defer split

## Deviations from Plan

None - plan executed exactly as written.

## Tech Debt Noted
- `signal_mappers.py` at 505 lines exceeds the 500-line anti-context-rot limit (was 502 pre-existing, added 3 lines). Needs a split in a future plan.
- `orchestrator.py` at 656 lines exceeds the 500-line limit (pre-existing issue, was ~625 before this plan added 31 lines). Already has documented debt.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Volume spike detection is fully wired into the extraction pipeline
- Event correlation will fire automatically when Brave Search is configured (search_fn is not None)
- Signal will be evaluated in ANALYZE stage via the tiered threshold system
- Ready for pipeline validation runs against real tickers (SNA, AAPL)

## Self-Check: PASSED

All 9 created/modified files verified present. All 3 task commits verified in git log.

---
*Phase: 52-extraction-data-quality*
*Completed: 2026-02-28*
