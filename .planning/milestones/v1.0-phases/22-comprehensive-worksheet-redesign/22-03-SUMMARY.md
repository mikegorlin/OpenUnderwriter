---
phase: 22
plan: 03
subsystem: render
tags: [financial-health, docx, conditional-formatting, distress, audit, debt]
depends_on: [22-01]
provides: [sect3-v2-renderer, audit-risk-split, income-statement-tables]
affects: [22-07, 22-08]
tech_stack:
  added: []
  patterns: [narrative-first-rendering, zone-coloring, margin-computation]
key_files:
  created:
    - src/do_uw/stages/render/sections/sect3_audit.py
  modified:
    - src/do_uw/stages/render/sections/sect3_financial.py
    - src/do_uw/stages/render/sections/sect3_tables.py
    - tests/test_render_sections_1_4.py
decisions:
  - Combined Tasks 1 and 2 into single commit (circular dependency - sect3_financial imports sect3_audit)
  - Moved income statement rendering to sect3_tables.py alongside balance sheet/cash flow
  - Narrative engine takes priority over stored narrative for analyst-quality prose
  - Distress panel includes D&O Context column explaining underwriting significance
  - Zone labels use descriptive text (Safe, Grey Zone, Distress) instead of raw enum values
metrics:
  duration: 8m 16s
  completed: 2026-02-11
---

# Phase 22 Plan 03: Financial Health v2 Renderer Summary

**One-liner:** Three-file financial health renderer with narrative lead, income/BS/CF tables with conditional formatting, distress panel with zone coloring and D&O context, earnings quality assessment, and full audit risk/debt analysis split file.

## What Was Done

### sect3_financial.py (384 lines) -- Main orchestrator
- **Narrative-first approach**: Uses `financial_narrative()` engine for analyst-quality interpretive prose citing specific dollar amounts, margins, and D&O conclusions. Falls back to stored `financial_health_narrative` SourcedValue if engine returns empty.
- **Distress Indicators Panel**: All four models (Altman Z-Score, Beneish M-Score, Ohlson O-Score, Piotroski F-Score) in a single table with Score, Zone, Trajectory, and D&O Context columns. Zone cells get conditional shading (blue=safe, amber=grey, red=distress). Trajectory shows 4-quarter trend direction (improving/stable/declining).
- **Earnings Quality Summary**: OCF/Net Income, Accruals Ratio, Revenue Quality with assessment coloring and source citation.
- **Audit delegation**: Calls `render_audit_risk()` from new sect3_audit.py.
- **Peer Group**: Unchanged from v1, renders top-10 peers with market cap, revenue, similarity score.

### sect3_tables.py (417 lines) -- All statement tables
- **Income Statement**: Multi-period table with conditional formatting on YoY Change column. Red for >10% deterioration, amber for 5-10%, blue for >10% improvement (NO green). Added margin metrics to `_METRIC_DIRECTION` dict.
- **Balance Sheet**: Multi-period table + inline key ratios (Current Ratio, Debt/Equity, Debt/Assets, Cash/Assets) with assessment coloring.
- **Cash Flow**: Multi-period table + Free Cash Flow callout with D&O context for negative FCF.
- **Key Ratios Comparison**: Company vs peer group average when liquidity/leverage data available.
- Preserved `_get_conditional_shading()` public function for existing test compatibility.

### sect3_audit.py (448 lines) -- New split file
- **Audit Risk Assessment**: 9-row table (Auditor, Big 4, Tenure, Opinion, Going Concern, Material Weaknesses, Significant Deficiencies, Restatements, CAMs) with red shading on high-risk items.
- **D&O Context**: Rich explanatory text for material weaknesses (scienter evidence), restatements (class period endpoints), going concern (insolvency doctrine), CAMs (litigation targeting), and extended tenure (independence concerns). Each with risk level indicators.
- **Debt Structure**: Leverage ratios + instrument details from LLM extraction + covenant status + refinancing risk. Conditional coloring for elevated leverage.
- **Debt Maturity Schedule**: Year-by-year from LLM extraction with near-term maturity highlight.
- **Critical Accounting Estimates**: Effective tax rate, deferred tax assets, uncertain tax positions from LLM MD&A.

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Single commit for Tasks 1+2 | Circular dependency: sect3_financial.py imports render_audit_risk from sect3_audit.py. Tests cannot pass without both files present. |
| Income statement in sect3_tables.py not sect3_financial.py | Keeps sect3_financial.py under 500 lines (was 659 with income rendering) and groups all statement tables in one module |
| Narrative engine priority over stored narrative | Produces richer, more contextual prose with D&O conclusions rather than generic summaries |
| D&O Context column in distress panel | Underwriters need to understand why each model matters for their assessment, not just see raw scores |
| Zone labels as descriptive text | "Grey Zone" is more meaningful to underwriters than raw "GREY" enum value |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Tasks 1 and 2 committed together**
- **Found during:** Task 1 execution
- **Issue:** sect3_financial.py imports `render_audit_risk` from sect3_audit.py. Tests fail without both files.
- **Fix:** Created sect3_audit.py as part of Task 1 execution, committed together.
- **Commit:** 6d4e7a5

**2. [Rule 1 - Bug] Test assertions updated for v2 behavior**
- **Found during:** Task 1 verification
- **Issue:** Tests expected v1 text ("Revenue growing" from stored narrative, "GREY" from raw zone enum). V2 uses narrative engine output and descriptive zone labels.
- **Fix:** Updated test assertions to match v2 behavior while preserving test intent.
- **Files modified:** tests/test_render_sections_1_4.py
- **Commit:** 6d4e7a5

## Verification Results

- 22/22 tests pass
- 0 pyright errors across all three files
- All files under 500 lines (384 + 417 + 448)
- `render_section_3(doc, state, ds) -> None` signature unchanged
