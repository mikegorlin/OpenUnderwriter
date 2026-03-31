---
phase: 143-stock-charts
plan: 02
subsystem: render
tags: [charts, market-section, template-reorder, visual-layout]
dependency_graph:
  requires: [143-01]
  provides: [charts-first-layout]
  affects: [market.html.j2, stock_charts.html.j2, market.md.j2, sect4_market.py]
tech_stack:
  added: []
  patterns: [charts-before-stats]
key_files:
  created: []
  modified:
    - src/do_uw/templates/html/sections/market.html.j2
    - src/do_uw/templates/html/sections/market/stock_charts.html.j2
    - src/do_uw/templates/markdown/sections/market.md.j2
    - src/do_uw/stages/render/sections/sect4_market.py
decisions:
  - Renamed chart heading from "Stock Performance" to "Price Charts" to avoid collision with stock_performance.html.j2 heading
metrics:
  duration: 3m 24s
  completed: "2026-03-28T05:06:00Z"
  tasks_completed: 1
  tasks_total: 2
  checkpoint_pending: true
---

# Phase 143 Plan 02: Market Section Chart Reorder Summary

Reordered Market section so stock charts are the first visual element across HTML, Word, and Markdown renderers.

## What Changed

### Task 1: Reorder templates so charts lead the Market section (4d139537)

Four files modified to move charts before stats tables:

1. **HTML template (market.html.j2)**: Swapped include order so `stock_charts.html.j2` renders before `stock_performance.html.j2` in the legacy fallback block.

2. **stock_charts.html.j2**: Changed heading from "Stock Performance" to "Price Charts" to differentiate from the stats table heading in stock_performance.html.j2.

3. **Word renderer (sect4_market.py)**: Moved `render_stock_stats()` call after all chart embedding (1Y, 5Y, drawdown, volatility, relative, drop analysis charts) instead of before them.

4. **Markdown template (market.md.j2)**: Added "Price Charts" heading with chart images before the "Stock Performance" stats table.

### Task 2: Visual verification (checkpoint:human-verify)

Status: **Ready for human verification**. This checkpoint requires running the pipeline for a known ticker and visually confirming:
- Charts appear as first visual element in Market section
- 1-year and 5-year charts display side by side
- Sector ETF overlay visible on both charts
- Event annotations present

## Deviations from Plan

None - plan executed exactly as written.

## Verification

- Render test suite: 1303 passed, 94 pre-existing failures (102 pre-existing on main), 0 new failures
- Template ordering confirmed: stock_charts.html.j2 on line 49, stock_performance.html.j2 on line 50

## Known Stubs

None.

## Self-Check: PASSED
