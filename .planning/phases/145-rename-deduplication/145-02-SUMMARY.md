---
phase: 145-rename-deduplication
plan: 02
subsystem: render
tags: [templates, dedup, jinja2, html]

requires:
  - phase: 145-01
    provides: uw_analysis rename (beta_report -> uw_analysis across codebase)
provides:
  - Deduped headline metrics across all section templates
  - Automated dedup verification test (8 tests)
affects: [render, templates, key_stats, identity, company]

tech-stack:
  added: []
  patterns:
    - "Home section pattern: each headline metric has one authoritative display location"
    - "Header bar is the ONLY allowed cross-section duplicate for MCap/Revenue/Price/Employees"

key-files:
  created:
    - tests/stages/render/test_dedup_metrics.py
  modified:
    - src/do_uw/templates/html/sections/key_stats.html.j2
    - src/do_uw/templates/html/sections/identity.html.j2
    - src/do_uw/templates/html/sections/company.html.j2

key-decisions:
  - "company_profile.html.j2 spectrum bars kept — analytical/classification use, not headline display"
  - "risk_classification.html.j2 market cap tier label kept — analytical use, not dollar value"
  - "page0_dashboard.html.j2 revenue card kept — shows growth sparkline and EV/Revenue (analytical)"

patterns-established:
  - "DEDUP home sections: Revenue=Financial, MCap=Dashboard, Price=Stock&Market, Board=Governance"

requirements-completed: [DEDUP-01, DEDUP-02, DEDUP-03, DEDUP-04]

duration: 6min
completed: 2026-03-28
---

# Phase 145 Plan 02: Metric Dedup Summary

**Removed redundant headline metric displays from 3 templates; stock price panel from key_stats, market_cap/revenue from identity and company KPI cards, with 8-test enforcement suite**

## What Was Done

### Task 1: Remove redundant headline metrics from non-home templates
- **key_stats.html.j2**: Removed entire stock price panel (lines 142-174) including stock charts, price display, 52-week range bar. Home = Stock & Market section.
- **identity.html.j2**: Removed Market Cap and Revenue (TTM) from paired KV table. Kept Employees and IPO/Listed date.
- **company.html.j2**: Removed Market Cap and Revenue KPI cards from company section strip. Kept Employees and Years Public.
- **company_profile.html.j2**: No changes — spectrum bars are analytical/classification displays (tier labels), not standalone headline values.
- **risk_classification.html.j2**: No changes — "Market Cap Tier" is a classification label, not the dollar amount.
- **page0_dashboard.html.j2**: No changes — it IS the home for Market Cap (per D-05), and revenue card provides analytical growth context.

### Task 2: Create dedup verification test
- Created `tests/stages/render/test_dedup_metrics.py` with 8 test functions
- Verifies header bar has exactly MCap/Revenue/Price/Employees (DEDUP-03)
- Verifies non-home sections no longer display headline metrics (DEDUP-04)
- Verifies home sections still contain their metrics (DEDUP-02)
- All 8 tests pass

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 | 5989fd9f | refactor(145-02): remove redundant headline metrics from non-home templates |
| 2 | a5653a33 | test(145-02): add dedup verification test for home section rules |

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED
