---
phase: 37-stock-charts-price-history-drop-analysis
plan: 03
subsystem: render
tags: [chart-pipeline, chart-dir, drop-tables, severity-tiers, recovery-time, word-renderer]

# Dependency graph
requires:
  - phase: 37-01
    provides: "Enhanced StockDropEvent with recovery_days, is_market_wide, trigger_source_url, cumulative_pct"
provides:
  - "Chart generation pipeline: RenderStage saves PNGs to chart_dir before calling renderers"
  - "Data-hash cache for chart images (SHA-256 of price data, skip regeneration if unchanged)"
  - "chart_dir threading through Word, Markdown, and PDF renderers"
  - "Drop detail tables with severity coloring, recovery time, trigger attribution"
  - "sect4_market_helpers.py: extracted stock stats and chart disk embedding helpers"
  - "get_drops_for_period() with 1Y (5%+) and 5Y (10%+/15%+ cumulative) filtering"
affects: [37-04, render]

# Tech tracking
tech-stack:
  added: []
  patterns: ["chart_dir pipeline: generate PNGs once, embed in all three renderers", "data-hash cache for chart regeneration skip"]

key-files:
  created:
    - "src/do_uw/stages/render/sections/sect4_drop_tables.py"
    - "src/do_uw/stages/render/sections/sect4_market_helpers.py"
  modified:
    - "src/do_uw/stages/render/__init__.py"
    - "src/do_uw/stages/render/word_renderer.py"
    - "src/do_uw/stages/render/sections/sect4_market.py"
    - "src/do_uw/templates/markdown/worksheet.md.j2"

key-decisions:
  - "Extract render_stock_stats, embed_chart_from_disk, sv_* to sect4_market_helpers.py for 500-line compliance"
  - "Extract get_drops_for_period to sect4_drop_tables.py to keep sect4_market.py under 500 lines"
  - "Keep existing _render_stock_drops in sect4_market_events.py (different D&O analysis purpose, no duplication)"
  - "Use data-hash cache with SHA-256 of price history Close arrays for chart regeneration skip"

patterns-established:
  - "chart_dir pipeline: generate all chart PNGs to output/TICKER/charts/, pass to all renderers"
  - "Section 4 chart_dir forwarding: word_renderer dispatches chart_dir only to Section 4 renderer"
  - "Disk-first chart embedding with inline fallback for backward compatibility"
  - "Drop severity tiers: FFF3CD (5-10%), FCE8E6 (10%+) matching ds.highlight_warn/highlight_bad"

requirements-completed: []

# Metrics
duration: 13min
completed: 2026-02-21
---

# Phase 37 Plan 03: Chart Pipeline + Drop Detail Tables Summary

**Chart generation pipeline saves PNGs to chart_dir with data-hash cache, threads through all renderers; drop detail tables with severity coloring, recovery time, and trigger attribution below stock charts**

## Performance

- **Duration:** 13 min
- **Started:** 2026-02-21T18:11:54Z
- **Completed:** 2026-02-21T18:24:59Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- RenderStage.run() generates stock_1y.png, stock_5y.png, radar.png to chart_dir before calling any renderer
- Data-hash caching: SHA-256 of price data inputs, writes .data_hash file, skips regeneration if unchanged
- chart_dir threaded through Word, Markdown, and PDF renderers via _render_secondary()
- Word renderer dispatch loop passes chart_dir to Section 4 renderer specifically
- sect4_market.py reads charts from disk (with inline fallback), reduced from 508 to 499 lines
- Drop detail tables with severity coloring (yellow 5-10%, red 10%+), recovery time, trigger attribution
- Summary line above each table with event counts by severity tier and type
- 1Y drops show all 5%+ events, 5Y shows only 10%+/15%+ cumulative

## Task Commits

Each task was committed atomically:

1. **Task 1: Chart generation pipeline + chart_dir threading** - `63228fe` (feat)
2. **Task 2: Drop detail table renderer** - `7a690c8` (feat)

## Files Created/Modified
- `src/do_uw/stages/render/__init__.py` - Added _generate_chart_images(), _compute_chart_data_hash(), chart_dir pipeline in run() (326 lines)
- `src/do_uw/stages/render/word_renderer.py` - Added chart_dir parameter, Section 4 dispatch with chart_dir kwarg (413 lines)
- `src/do_uw/stages/render/sections/sect4_market.py` - chart_dir support, drop table integration, extracted helpers (499 lines)
- `src/do_uw/stages/render/sections/sect4_market_helpers.py` - NEW: render_stock_stats, embed_chart_from_disk, sv_* helpers (97 lines)
- `src/do_uw/stages/render/sections/sect4_drop_tables.py` - NEW: render_drop_detail_table, get_drops_for_period (253 lines)
- `src/do_uw/templates/markdown/worksheet.md.j2` - Added 5Y chart reference alongside 1Y

## Decisions Made
- **500-line compliance via extraction**: Created sect4_market_helpers.py for stock stats, chart disk embedding, and SourcedValue formatters; moved get_drops_for_period to sect4_drop_tables.py. Brought sect4_market.py from 508 to 499 lines.
- **Keep existing stock drops table**: The existing _render_stock_drops in sect4_market_events.py serves a different purpose (D&O class period analysis) than the new drop detail table (chart companion with recovery time, severity tiers). No duplication.
- **Data-hash cache**: SHA-256 of Close price array endpoints (first 3 + last 3 values + length) per price history key. Sufficient for detecting data changes without hashing entire arrays.
- **Disk-first with inline fallback**: sect4_market.py tries chart_dir PNGs first, falls back to inline BytesIO generation if chart_dir is None or files missing. Ensures backward compatibility.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] sect4_market.py exceeded 500-line limit after modifications**
- **Found during:** Task 1 (chart_dir integration)
- **Issue:** sect4_market.py grew from 508 to 555 lines after adding chart_dir support, _render_stock_stats, and _embed_chart_from_disk
- **Fix:** Created sect4_market_helpers.py and extracted render_stock_stats, embed_chart_from_disk, sv_str, sv_pct, sv_float
- **Files modified:** sect4_market.py, sect4_market_helpers.py (new)
- **Verification:** sect4_market.py at 499 lines, all imports pass
- **Committed in:** 63228fe (Task 1 commit)

**2. [Rule 3 - Blocking] sect4_market.py re-exceeded 500-line limit after Task 2 additions**
- **Found during:** Task 2 (drop table integration)
- **Issue:** Adding _get_drops_for_period and import/call code pushed sect4_market.py to 532 lines
- **Fix:** Moved get_drops_for_period to sect4_drop_tables.py; condensed docstring and _render_heading
- **Files modified:** sect4_market.py, sect4_drop_tables.py
- **Verification:** sect4_market.py at 499 lines, all 147 render tests pass
- **Committed in:** 7a690c8 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (2 blocking -- 500-line limit)
**Impact on plan:** Both necessary for code standards compliance. No scope creep -- just refactoring to maintain file size limits.

## Issues Encountered
- Pre-existing test failures in test_render_outputs.py (test_render_stage_calls_all_renderers, test_render_pdf_returns_none_without_weasyprint) confirmed by running against base commit. Not caused by this plan's changes.
- Pre-existing brain/checks.json test failures (test_brain_enrich, test_brain_loader, test_check_classification) from unstaged checks.json modifications. Not caused by this plan's changes.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Chart generation pipeline operational: PNGs saved to chart_dir, all three renderers receive chart_dir
- Drop detail tables ready with full event metadata below each chart period
- Plan 04 (Bloomberg dark theme chart rewrite) can now use the chart_dir pipeline
- Pre-generated charts from disk means PDF/HTML renderers can access charts without inline generation

## Self-Check: PASSED

All files verified present. All commits verified in git log.

---
*Phase: 37-stock-charts-price-history-drop-analysis*
*Completed: 2026-02-21*
