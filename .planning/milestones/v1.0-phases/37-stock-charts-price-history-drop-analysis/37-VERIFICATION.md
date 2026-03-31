---
phase: 37-stock-charts-price-history-drop-analysis
verified: 2026-02-21T19:00:00Z
status: passed
score: 5/5 success criteria verified
re_verification: false
gaps: []
human_verification:
  - test: "Open a Word document for any ticker and verify 1Y/5Y Bloomberg charts render correctly"
    expected: "Dark-background chart with company area fill, dashed gold ETF line, dotted blue SPY line, stats header showing price/52W H/L/return/sector/alpha, yellow/red drop markers with percentage annotations"
    why_human: "matplotlib rendering correctness and visual quality cannot be verified programmatically"
  - test: "Run pipeline for a ticker with recent drops and check drop detail table"
    expected: "Table below chart with date, drop %, recovery days, trigger event, Company-Specific/Market-Wide classification, and source URL or '--'. Unknown triggers show 'Unconfirmed -- Requires Investigation'. Summary line above: 'N significant stock decline events detected in the 1Y period: X critical (>10%), Y notable (5-10%). Z were company-specific, W were market-wide.'"
    why_human: "Trigger attribution depends on real 8-K filing data alignment with drop dates; cannot test without live pipeline run"
  - test: "Verify WeasyPrint fallback PDF includes 5Y chart"
    expected: "pdf/worksheet.html.j2 is the WeasyPrint fallback template; it currently only embeds stock_1y inline. Unless Playwright is always available, the fallback PDF omits the 5Y chart."
    why_human: "Template gap found in WeasyPrint fallback path — verify whether Playwright is always present in deployment or if fallback 5Y chart embedding matters"
---

# Phase 37: Stock Charts / Price History / Drop Analysis Verification Report

**Phase Goal:** Stock performance charts (1Y and 5Y) render in all three output formats with annotated 5%+ drop events, sector ETF comparison lines, and trigger explanations. Every significant stock drop is explained. The daily price history acquired from yfinance flows through to chart generation without data loss or key mismatches.

**Verified:** 2026-02-21T19:00:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (Derived from Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | 1Y and 5Y stock charts render in Word, Markdown, and PDF with company price, sector ETF overlay (dashed), and SPY overlay (dotted) | VERIFIED | `stock_charts.py` implements all 8 sub-systems; `render/__init__.py` generates PNGs to `chart_dir`; Word/MD/HTML renderers all receive `chart_dir`; Playwright PDF uses `market.html.j2` with both charts. WeasyPrint fallback omits 5Y — flagged for human review. |
| 2 | All 5%+ single-day drops annotated on chart with date/percentage; drop table shows date, magnitude, trigger, company-specific vs market-wide | VERIFIED | `_render_drop_markers()` places colored dots with `{pct:+.1f}%` annotations. `sect4_drop_tables.py` renders full table with all required columns. Summary line counts by severity/type. |
| 3 | Price history key mismatch fixed: chart generator reads `history_1y`/`history_5y` from `acquired_data.market_data` | VERIFIED | `stock_chart_data.py` `extract_chart_data()` explicitly uses `hist_key = "history_1y" if period == "1Y" else "history_5y"`. Test `test_extract_chart_data_correct_keys` confirms this and passes. |
| 4 | Sector ETF acquired: `market_client.py` acquires sector ETF history alongside company history using `brain/sectors.json` | VERIFIED | `_resolve_sector_etf()` reads `brain/sectors.json` via `sector_etfs[code]["primary"]`. `_collect_yfinance_data()` acquires `sector_history_1y`, `sector_history_5y`, `spy_history_1y`, `spy_history_5y`. All 13 ETF resolution tests pass. |
| 5 | Every significant drop has trigger attribution: 8-K within ±3 days, earnings date within ±3 days, or "Requires investigation" | VERIFIED | `attribute_triggers()` searches 8-K dates and earnings dates within 3 days; populates `trigger_source_url` from accession number (SEC EDGAR URL). `_format_trigger()` returns "Unconfirmed -- Requires Investigation" when no trigger identified. |

**Score:** 5/5 truths verified

---

## Required Artifacts

### Plan 01: Acquisition + Drop Analysis Enhancement

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/stages/acquire/clients/market_client.py` | ETF + SPY history acquisition | VERIFIED | 322 lines. `_resolve_sector_etf()` at line 47 reads `brain/sectors.json`. Acquires `sector_history_1y/5y`, `spy_history_1y/5y`. Docstring updated. |
| `src/do_uw/models/market_events.py` | Enhanced `StockDropEvent` with 4 new fields | VERIFIED | 470 lines. Fields `recovery_days`, `is_market_wide`, `trigger_source_url`, `cumulative_pct` present at lines 72-87. |
| `src/do_uw/stages/extract/stock_drop_analysis.py` | New: recovery time, event grouping, market-wide tagging | VERIFIED | 220 lines. `compute_recovery_days()`, `group_consecutive_drops()`, `tag_market_wide_events()` all present and substantive. |
| `src/do_uw/stages/extract/stock_drops.py` | Updated `attribute_triggers()` with `trigger_source_url` population | VERIFIED | 376 lines. `_get_8k_dates()` returns `list[tuple[str, str]]`. `attribute_triggers()` constructs SEC EDGAR URL from accession. |

### Plan 02: Bloomberg Chart Renderer

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/stages/render/charts/stock_chart_data.py` | Data extraction layer with `extract_chart_data` | VERIFIED | 316 lines. `ChartData` dataclass, `extract_chart_data()`, `compute_chart_stats()`, `index_to_base()`, `aggregate_weekly()` all present. Reads correct keys. |
| `src/do_uw/stages/render/charts/stock_charts.py` | Bloomberg dark theme rendering with `BLOOMBERG_DARK` | VERIFIED | 463 lines. All 8 sub-systems: theme, area fill, stats header, ETF overlay, SPY overlay, drop markers, divergence bands, backward-compat exports. |
| `src/do_uw/stages/render/design_system.py` | `BLOOMBERG_DARK` color palette | VERIFIED | `BLOOMBERG_DARK` dict at line 89 with 15 color keys. Listed in `__all__` at line 215. |

### Plan 03: Chart Pipeline + Drop Tables

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/stages/render/__init__.py` | Chart generation pipeline with `_compute_chart_data_hash` | VERIFIED | 326 lines. `_compute_chart_data_hash()`, `_generate_chart_images()`, `_render_secondary()` all present. `chart_dir` passed to all three renderers. |
| `src/do_uw/stages/render/word_renderer.py` | `chart_dir` threading through dispatch loop | VERIFIED | 413 lines. `render_word_document()` accepts `chart_dir`; dispatch loop passes it to Section 4 renderer specifically. |
| `src/do_uw/stages/render/sections/sect4_drop_tables.py` | Drop detail table with `render_drop_detail_table` | VERIFIED | 253 lines. Full table with all 6 columns, severity coloring, summary line, `get_drops_for_period()`. |
| `src/do_uw/stages/render/sections/sect4_market.py` | Chart_dir support + drop table integration | VERIFIED | 499 lines (at limit). `render_section_4()` accepts `chart_dir`, embeds from disk with inline fallback, calls `render_drop_detail_table()`. |

### Plan 04: Tests

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tests/stages/acquire/test_market_client_etf.py` | 13 ETF resolution tests | VERIFIED | 68 lines. All 11 yfinance sector-to-ETF mappings tested, plus unknown and empty edge cases. All 13 PASS. |
| `tests/stages/extract/test_stock_drops_enhanced.py` | 12 recovery/grouping/market-wide tests | VERIFIED | 197 lines. `compute_recovery_days`, `group_consecutive_drops`, `tag_market_wide_events` all tested. All 12 PASS. |
| `tests/stages/render/test_stock_charts.py` | 18 chart pipeline tests | VERIFIED | 451 lines. PNG output, correct keys, 5Y weekly aggregation, stats, backward compat, template embedding. All 18 PASS. |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `market_client.py` | `brain/sectors.json` | `_resolve_sector_etf()` reads `sector_etfs[code]["primary"]` | WIRED | Pattern `sector_etfs.*primary` found. 13 ETF resolution tests pass. |
| `stock_drop_analysis.py` | `models/market_events.py` | `StockDropEvent` fields `recovery_days`, `is_market_wide`, `cumulative_pct` | WIRED | All 4 new fields imported and used. `_merge_group()` sets `cumulative_pct`. `tag_market_wide_events()` sets `is_market_wide`. |
| `stock_chart_data.py` | `acquired_data.market_data` | Keys `history_1y`, `sector_history_1y`, `spy_history_1y` | WIRED | `extract_chart_data()` uses correct keys. No `price_history` usage. Test confirms. |
| `stock_charts.py` | `stock_chart_data.py` | `extract_chart_data()` call | WIRED | Import at line 24-28. Called at line 50. |
| `render/__init__.py` | `word_renderer.py` | `render_word_document(state, docx_path, ds, chart_dir=chart_dir)` | WIRED | Line 77. `chart_dir` kwarg explicitly passed. |
| `word_renderer.py` | `sect4_market.py` | `renderer_fn(doc, state, ds, chart_dir=chart_dir)` for Section 4 | WIRED | Lines 388-390. Conditional on `section_name == "Section 4: Market & Trading"`. |
| `sect4_market.py` | `sect4_drop_tables.py` | `render_drop_detail_table()` call | WIRED | Imported at line 39-41. Called at lines 234 and 238. |
| `stock_performance.py` | `stock_drop_analysis.py` | `compute_recovery_days`, `group_consecutive_drops`, `tag_market_wide_events` | WIRED | Imported at lines 37-39. Called at lines 385, 392, 412-413. Full pipeline wiring confirmed. |

---

## Anti-Patterns Found

None of the phase 37 implementation files contain TODO/FIXME/placeholder stubs, empty implementations, or console-only handlers. The `_add_placeholder_section` in `word_renderer.py` is a legitimate error-handling fallback (not a stub), and was pre-existing to this phase.

The one structural note: `sect4_market.py` is at exactly 499 lines — one line under the 500-line limit. This is tight but compliant.

---

## Human Verification Required

### 1. Bloomberg Chart Visual Quality

**Test:** Run the pipeline for any ticker (e.g., AAPL) and open the generated Word document. Navigate to Section 4: Market & Trading.
**Expected:** Two charts appear: 1Y and 5Y. Each chart has a dark background (near-black), a green/red area fill under the company price line, a dashed gold line for the sector ETF, a dotted light blue line for SPY, and a stats header bar at the top showing ticker, price, 52W H/L, return, sector return, and alpha. Drop events appear as yellow (5-10%) or red (10%+) dots with percentage annotations below them.
**Why human:** matplotlib rendering correctness and the visual correctness of conditional fill (green above start price, red below) cannot be verified programmatically without rendering.

### 2. Drop Detail Table with Real Data

**Test:** Run the pipeline for a ticker that has had real drop events (e.g., a company with a known earnings miss or news event). Check Section 4 below the charts.
**Expected:** A summary line appears ("N significant stock decline events detected in the 1Y period: X critical (>10%), Y notable (5-10%). Z were company-specific, W were market-wide."), followed by a table with columns: Date, Drop %, Recovery, Trigger Event, Type, Source. Drops matching 8-K filings within ±3 days show an SEC EDGAR URL. Drops with no nearby event show "Unconfirmed -- Requires Investigation".
**Why human:** Trigger attribution depends on real 8-K accession numbers aligning with drop dates; synthetic tests confirm the logic but cannot confirm real-world data alignment.

### 3. WeasyPrint Fallback PDF Chart Coverage

**Test:** On a system without Playwright installed, run the pipeline. Open the generated PDF.
**Expected:** The PDF contains a stock chart for the 1Y period. Whether the 5Y chart also appears depends on whether the WeasyPrint fallback path (`pdf/worksheet.html.j2`) is updated.
**Why human:** The `pdf/worksheet.html.j2` (WeasyPrint fallback) currently only embeds `stock_1y` (line 186), not `stock_5y`. The primary Playwright path uses `html/sections/market.html.j2` which has both. Verify whether the WeasyPrint fallback gap matters in deployment (if Playwright is always available, this is a non-issue).

---

## Gaps Summary

No blocking gaps found. All five success criteria are verified:

1. **SC1 (Chart rendering in all formats):** Fully wired for Word, Markdown, and Playwright HTML/PDF. The WeasyPrint fallback PDF omits the 5Y chart, but this is the fallback path, not the primary. Flagged for human confirmation.

2. **SC2 (Drop annotation and table):** Drop markers with color/percentage rendered by `_render_drop_markers()`. Full drop detail table with all 6 required columns rendered by `sect4_drop_tables.py`. Summary line present.

3. **SC3 (Key mismatch fixed):** `extract_chart_data()` reads `history_1y`/`history_5y` directly. The old broken `price_history` key is absent from all new code. Test coverage confirms.

4. **SC4 (Sector ETF acquired):** `market_client.py` acquires sector ETF and SPY history via `brain/sectors.json` lookup. All 11 yfinance sectors mapped.

5. **SC5 (Drop trigger attribution):** `attribute_triggers()` searches 8-K filings and earnings dates within ±3 days, populates `trigger_source_url` with SEC EDGAR URL from accession number, and `_format_trigger()` returns "Unconfirmed -- Requires Investigation" for unknown triggers.

**Test results:** 43/43 new tests pass. All pre-existing render tests continue to pass.

---

_Verified: 2026-02-21T19:00:00Z_
_Verifier: Claude (gsd-verifier)_
