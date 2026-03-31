---
phase: 4
plan: 4
subsystem: extract
tags: [stock-performance, drop-detection, volatility, max-drawdown, sector-comparison]
depends_on:
  requires: [04-02]
  provides: [stock_performance_extractor, stock_drops_module]
  affects: [04-10, 04-11]
tech_stack:
  added: []
  patterns: [500-line-split, public-helpers-for-testing]
key_files:
  created:
    - src/do_uw/stages/extract/stock_performance.py
    - src/do_uw/stages/extract/stock_drops.py
    - tests/test_stock_performance.py
  modified: []
decisions:
  - id: 04-04-01
    decision: Split into stock_performance.py (371L) + stock_drops.py (355L) for 500-line compliance
  - id: 04-04-02
    decision: Made compute_volatility and compute_max_drawdown public for direct unit testing
  - id: 04-04-03
    decision: get_close_prices uses float(str(val)) cast for pyright strict compliance
metrics:
  duration: 10m 18s
  completed: 2026-02-08
  tests_added: 22
  tests_total_after: 446
---

# Phase 4 Plan 4: Stock Performance Extractor Summary

Stock performance and drop detection extractor covering SECT4-01 (price metrics), SECT4-02 (performance table), and SECT4-03 (stock drop analysis) -- the #1 trigger for D&O securities class actions.

## What Was Built

### stock_drops.py (355 lines) -- Drop Detection Engine
- `find_single_day_drops()`: Scans daily returns for drops exceeding threshold (default -5%)
- `find_multi_day_drops()`: Rolling N-day returns with configurable period/threshold pairs (2d/-10%, 5d/-15%, 20d/-25%)
- `compute_sector_comparison()`: Compares drop against sector ETF to determine company-specific vs market-wide
- `attribute_triggers()`: Searches for 8-K filings and earnings dates within 3 calendar days of drops
- `get_close_prices()`, `get_dates()`, `compute_daily_returns()`: Shared data access with NaN/None filtering

### stock_performance.py (371 lines) -- Main Extractor
- `extract_stock_performance()`: Main entry returning (StockPerformance, StockDropAnalysis, ExtractionReport)
- `compute_volatility()`: Annualized volatility from trailing N-day returns (stdev * sqrt(252))
- `compute_max_drawdown()`: Peak-to-trough drawdown tracking
- Performance metrics: current_price, 52w high/low, decline from high, 1y/5y/YTD returns, beta
- ExtractionReport tracks 7 expected fields with coverage percentage

### tests (22 tests, all passing)
- Single-day drops: detection (3 known drops), stable stock (no drops), boundary (-5.0% exact)
- Multi-day drops: 5-day sequence detection, rising prices (no drops)
- Performance metrics: full metrics computed, max drawdown from known peak-to-trough, volatility positive, insufficient data
- Sector comparison: company-specific flag (stock > sector drop), not company-specific (sector > stock)
- Trigger attribution: earnings release matching, 8-K filing matching
- Graceful handling: empty market_data, NaN/None prices, no acquired_data
- Extraction report: coverage tracking, all-fields coverage
- Daily returns: computation accuracy, empty/single price
- Worst drop: correct identification of worst single-day event

## Decisions Made

| ID | Decision | Rationale |
|----|----------|-----------|
| 04-04-01 | Split stock_performance.py + stock_drops.py | Original was 705 lines; 500-line limit requires split |
| 04-04-02 | Public compute_volatility / compute_max_drawdown | Enables direct unit testing without pyright reportPrivateUsage |
| 04-04-03 | float(str(val)) for price parsing | pyright strict rejects float(object); str intermediate is safe for numeric strings |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] 500-line split required**
- **Found during:** Task 1
- **Issue:** Single file was 705 lines, exceeding 500-line limit
- **Fix:** Split into stock_performance.py (metrics + main entry) and stock_drops.py (drop detection + triggers)
- **Files created:** stock_drops.py (not in original plan)
- **Commit:** e84a63d

**2. [Rule 1 - Bug] pyright strict reportPrivateUsage**
- **Found during:** Task 2
- **Issue:** Tests importing _compute_max_drawdown and _compute_volatility caused pyright errors
- **Fix:** Renamed to public functions (compute_max_drawdown, compute_volatility) -- genuinely reusable
- **Commit:** 36dc487

## Commits

| Hash | Type | Description |
|------|------|-------------|
| e84a63d | feat | Stock performance extractor for SECT4-01/02/03 |
| 9889832 | test | 22 tests for stock performance and drop detection |
| 36dc487 | refactor | Make compute_volatility and compute_max_drawdown public |

## Next Phase Readiness

- Stock performance extractor ready for wiring into ExtractStage (04-10 or 04-11)
- Drop analysis feeds into F2 (Stock Decline) scoring factor
- Volatility feeds into F7 (Volatility) scoring factor
- Trigger attribution supports allegation mapping in SCORE stage
