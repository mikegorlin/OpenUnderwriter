---
phase: 145-rename-deduplication
plan: "03"
subsystem: render
tags: [tests, dedup, provenance, financial]
dependency_graph:
  requires: [145-02]
  provides: [clean-test-suite, revenue-provenance]
  affects: [test_key_stats.py, financial.html.j2, beta_report_sections.py]
tech_stack:
  added: []
  patterns: [provenance-sub-label, xbrl-fallback-chain]
key_files:
  created: []
  modified:
    - tests/stages/render/test_key_stats.py
    - src/do_uw/stages/render/context_builders/beta_report_sections.py
    - src/do_uw/templates/html/sections/financial.html.j2
decisions:
  - Kept stock-chart fixture keys in _base_key_stats for parallel worktree compatibility (template not yet modified by 145-01); keys become unused after merge
  - Revenue provenance uses XBRL income statement period as primary source (HIGH), yfinance as fallback (MEDIUM)
  - Provenance displayed via kpi_strip sub_label field rather than a separate div, maintaining existing card component API
metrics:
  duration: 164s
  completed: "2026-03-28"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 3
---

# Phase 145 Plan 03: Gap Closure -- Test Fixes and Revenue Provenance Summary

Revenue provenance wired from XBRL income statement into Financial section KPI card; two broken stock-chart test functions removed from test_key_stats.py.

## Task Results

### Task 1: Fix broken test_key_stats tests for removed stock price panel
- **Commit:** 92fe0456
- **Action:** Deleted `test_renders_stock_charts` and `test_recent_ipo_hides_5y_chart` -- both asserted on stock price panel content that belongs in `stock_market.html.j2` per D-05 dedup rules. Retained stock-chart fixture keys in `_base_key_stats` for parallel worktree compatibility (template still has the panel in this worktree; 145-01 removes it in a parallel branch). 12 remaining tests pass.

### Task 2: Wire revenue provenance into Financial section template
- **Commit:** 89b53517
- **Action:** Added `revenue_source`, `revenue_as_of`, `revenue_confidence` to `build_financial_context` return dict. Provenance derived from XBRL income statement periods (HIGH confidence) with yfinance fallback (MEDIUM). Template updated to display provenance as the Revenue KPI card sub_label (e.g., "FY2024 . XBRL . HIGH").

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Retained stock fixture keys for parallel worktree compatibility**
- **Found during:** Task 1
- **Issue:** Plan specified removing stock-chart keys from `_base_key_stats` fixture, but the template in this worktree still has the stock panel (145-01 removes it in a parallel branch). Removing keys caused all 11 remaining tests to fail with `UndefinedError: 'dict object' has no attribute 'stock_price'`.
- **Fix:** Kept stock-chart keys in fixture. They become unused after 145-01 merges and removes the stock panel from the template.
- **Files modified:** tests/stages/render/test_key_stats.py

**2. [Rule 3 - Blocking] Adapted file paths for pre-rename worktree**
- **Found during:** Task 2
- **Issue:** Plan referenced `uw_analysis_sections.py` and `sections/report/financial.html.j2` but this worktree has the pre-rename names (`beta_report_sections.py` and `sections/financial.html.j2`). 145-01 performs the rename in a parallel branch.
- **Fix:** Applied changes to the existing file names. After merge, 145-01's rename will carry these changes forward.
- **Files modified:** beta_report_sections.py, financial.html.j2

## Known Stubs

None -- all provenance data is wired to real XBRL extraction output.

## Verification

- `uv run pytest tests/stages/render/test_key_stats.py -v` -- 12/12 passed
- `grep revenue_source beta_report_sections.py` -- 4 matches confirming provenance keys
- `grep revenue_as_of financial.html.j2` -- 1 match confirming template wiring
