---
phase: 63-static-charts-visual-data
plan: "02"
subsystem: render/charts
tags: [sparklines, svg, design-system, chart-colors, inline-charts]
dependency_graph:
  requires: [63-01]
  provides: [render_sparkline, CHART_COLORS, sparkline-macro]
  affects: [market-context, financials-context, stock-performance-template, annual-comparison-template]
tech_stack:
  added: []
  patterns: [pure-svg-generation, inline-sparklines, unified-color-palette]
key_files:
  created:
    - src/do_uw/stages/render/charts/sparklines.py
    - src/do_uw/templates/html/components/sparkline.html.j2
    - tests/stages/render/test_sparklines.py
  modified:
    - src/do_uw/stages/render/design_system.py
    - src/do_uw/stages/render/charts/__init__.py
    - src/do_uw/stages/render/context_builders/market.py
    - src/do_uw/stages/render/context_builders/financials.py
    - src/do_uw/templates/html/components.css
    - src/do_uw/templates/html/sections/market/stock_performance.html.j2
    - src/do_uw/templates/html/sections/financial/annual_comparison.html.j2
    - tests/stages/render/test_chart_svg.py
decisions:
  - Pure SVG sparklines (no matplotlib) for lightweight inline rendering
  - CHART_COLORS is forward-looking unified palette; CREDIT_REPORT_LIGHT and BLOOMBERG_DARK preserved for backward compat
  - Sparklines sampled to ~12 points from raw price history for compact display
  - Timeline SVG already wired from 63-01 via _generate_chart_svgs and embed_chart macro
metrics:
  duration: ~8min
  completed: "2026-03-03"
  tasks_completed: 2
  tasks_total: 2
  tests_added: 18
  tests_total_passing: 156
---

# Phase 63 Plan 02: Inline SVG Sparklines + Timeline Chart + Design System Colors Summary

Pure SVG sparkline generator with auto trend detection, unified CHART_COLORS palette, and sparkline integration into stock performance and financial comparison templates.

## What Was Built

### Task 1: Sparkline SVG Generator and Unified Chart Color Palette (TDD)
- **sparklines.py**: Pure SVG sparkline generator -- no matplotlib dependency, pure string building
  - `render_sparkline(values, width, height, direction, color)` generates inline SVG
  - Auto-detects trend direction (up/down/flat) from first vs last value
  - Supports explicit direction and color overrides
  - Handles edge cases: empty list returns "", single value returns flat line
  - Area fill with 12% opacity below the sparkline line
  - Inline sizing via viewBox + preserveAspectRatio for text-level embedding
- **CHART_COLORS**: Unified color palette dict in design_system.py with 17 color entries
  - Core palette: navy, gold, positive, negative, neutral, accent_blue, accent_amber
  - Chart-specific: grid, bg, text, text_muted
  - Sparkline-specific: sparkline_up, sparkline_down, sparkline_flat, area alphas
- **15 tests** covering empty/single/multi-value, direction detection, color override, CHART_COLORS existence

### Task 2: Template Wiring, Context Builders, CSS
- **Context builders**: market.py generates stock_sparkline from 1Y price history (sampled to 12 points); financials.py generates revenue_sparkline, net_income_sparkline, total_assets_sparkline from multi-period line items
- **sparkline.html.j2 macro**: `{{ sparkline(svg_str, label) }}` wraps SVG in `<span class="sparkline-inline">` with |safe filter
- **CSS**: `.sparkline-inline` styles for inline-block vertical alignment
- **Template integration**: Stock performance heading shows 12-month price trend sparkline; Annual financial comparison table shows revenue and net income trend sparklines in metric label column
- **Timeline chart**: Already renders as SVG from 63-01 (verified _generate_chart_svgs includes "timeline" key)
- **3 additional tests**: Timeline SVG format parameter, sparkline context integration with/without data

## Deviations from Plan

None -- plan executed exactly as written. Timeline SVG conversion (Part A) was already complete from 63-01; verified and confirmed.

## Verification

- 31 sparkline + chart SVG tests pass
- 156 total render tests pass (zero regressions)
- Zero client-side JavaScript in chart code
- All sparkline colors sourced from CHART_COLORS in design_system.py
