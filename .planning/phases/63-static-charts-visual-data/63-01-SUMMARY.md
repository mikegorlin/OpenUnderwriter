---
phase: 63-static-charts-visual-data
plan: 01
subsystem: render
tags: [charts, svg, css-tabs, matplotlib, html]
dependency_graph:
  requires: [Phase 59 HTML Visual Polish]
  provides: [inline SVG charts, CSS-only tabbed financials]
  affects: [html_renderer, pdf_renderer, chart_helpers, chart templates]
tech_stack:
  added: []
  patterns: [SVG inline embedding, CSS radio-button tabs, dual format="png"|"svg"]
key_files:
  created:
    - src/do_uw/templates/html/charts.css
    - tests/stages/render/test_chart_svg.py
  modified:
    - src/do_uw/stages/render/chart_helpers.py
    - src/do_uw/stages/render/charts/stock_charts.py
    - src/do_uw/stages/render/charts/radar_chart.py
    - src/do_uw/stages/render/charts/ownership_chart.py
    - src/do_uw/stages/render/charts/timeline_chart.py
    - src/do_uw/stages/render/charts/__init__.py
    - src/do_uw/stages/render/__init__.py
    - src/do_uw/stages/render/html_renderer.py
    - src/do_uw/templates/html/components/charts.html.j2
    - src/do_uw/templates/html/sections/financial_statements.html.j2
    - src/do_uw/templates/html/components.css
    - src/do_uw/templates/html/base.html.j2
decisions:
  - "charts.css split from components.css to keep both under 500-line limit"
  - "SVG charts always use CREDIT_REPORT_LIGHT colors (white bg for HTML embedding)"
  - "embed_chart macro checks chart_svgs first, falls back to chart_images PNG base64"
  - "timeline_chart.py also gains format=svg for consistency across all chart modules"
metrics:
  duration_seconds: 500
  completed: "2026-03-03"
  tests_added: 13
  tests_total_passing: 495
  files_created: 2
  files_modified: 12
---

# Phase 63 Plan 01: SVG Charts + CSS-Only Tabbed Financials Summary

**One-liner:** Inline SVG chart pipeline (stock/radar/ownership/timeline) with CSS-only tabbed financial statements -- zero client-side JS.

## What Was Done

### Task 1: SVG Output Path + Chart Module Conversion (TDD)

Added `save_chart_to_svg(fig)` to `chart_helpers.py` that produces clean inline SVG strings (no XML declaration, width="100%", viewBox preserved). Added `format="svg"|"png"` parameter to all four chart modules:

- `stock_charts.py` -- create_stock_chart + backward-compat aliases
- `radar_chart.py` -- create_radar_chart
- `ownership_chart.py` -- create_ownership_chart
- `timeline_chart.py` -- create_litigation_timeline

SVG format returns `str`, PNG format returns `io.BytesIO` (backward compat for Word renderer). SVG always uses CREDIT_REPORT_LIGHT colors.

### Task 2: HTML Pipeline Wiring + CSS Tabs

- Added `_generate_chart_svgs()` to render `__init__.py` -- generates all charts as SVG strings
- Wired `chart_svgs` dict into `build_html_context()` alongside existing `chart_images`
- Updated `embed_chart` Jinja2 macro to prefer SVG (`{{ svg_data | safe }}`) with PNG fallback
- Rewrote `financial_statements.html.j2` with CSS-only radio-button tabs (Income / Balance / Cash Flow)
- Created `charts.css` for tab styles + SVG responsive sizing (split from components.css to stay under 500 lines)
- Print/PDF: all 3 statements expanded, tab UI hidden via `@media print`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] timeline_chart.py missing format parameter**
- **Found during:** Task 2, Part A
- **Issue:** `_generate_chart_svgs()` called `create_litigation_timeline(format="svg")` but timeline_chart.py lacked the parameter, which would cause a TypeError
- **Fix:** Added `format` parameter and SVG return path to timeline_chart.py (same pattern as other chart modules)
- **Files modified:** `src/do_uw/stages/render/charts/timeline_chart.py`
- **Commit:** d6fa3bd

**2. [Rule 3 - Blocking] components.css exceeded 500-line limit**
- **Found during:** Task 2, Part E
- **Issue:** Adding tab CSS + SVG styles pushed components.css to 534 lines (limit: 500)
- **Fix:** Created separate `charts.css` file and included it in `base.html.j2`, per plan's fallback instruction
- **Files created:** `src/do_uw/templates/html/charts.css`
- **Commit:** d6fa3bd

## Verification

- 13 new SVG chart tests pass
- 350 render tests pass (zero regression)
- 495 total stage tests pass
- Zero client-side JS charting dependencies in render templates
- `tab-radio` pattern present in financial_statements.html.j2
- `save_chart_to_svg` exists in chart_helpers.py
- SVG output starts with `<svg`, contains `viewBox`, no `<?xml` declaration

## Self-Check: PASSED
