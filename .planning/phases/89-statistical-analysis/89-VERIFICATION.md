---
phase: 89-statistical-analysis
verified: 2026-03-09T13:00:00Z
status: passed
score: 4/4 success criteria verified
must_haves:
  truths:
    - "Pricing section shows DDL exposure (market_cap x worst_drop_pct) and settlement (DDL x 1.8%)"
    - "Event days with abnormal returns flagged with t-stats, |t| >= 1.96 highlighted as significant"
    - "Stock analysis shows both rolling vol and EWMA vol (lambda=0.94) with regime classification"
    - "Volatility regime transitions visible with duration tracking"
  artifacts:
    - path: "src/do_uw/stages/render/charts/chart_computations.py"
      provides: "compute_ddl_exposure, compute_abnormal_return, compute_ewma_volatility, classify_vol_regime"
    - path: "src/do_uw/models/market.py"
      provides: "ewma_vol_current, vol_regime, vol_regime_duration_days on StockPerformance"
    - path: "src/do_uw/models/market_events.py"
      provides: "AR fields on StockDropEvent, DDL fields on StockDropAnalysis"
    - path: "src/do_uw/stages/extract/stock_performance.py"
      provides: "Wiring of EWMA, AR, DDL computations into extraction pipeline"
    - path: "src/do_uw/stages/render/charts/volatility_chart.py"
      provides: "EWMA overlay + regime shading on volatility chart"
    - path: "src/do_uw/stages/render/context_builders/market.py"
      provides: "DDL, settlement, AR, regime fields exported for templates"
    - path: "src/do_uw/templates/html/sections/market/stock_drops.html.j2"
      provides: "DDL exposure card, AR/t-stat columns, significance flags"
  key_links:
    - from: "stock_performance.py"
      to: "chart_computations.py"
      via: "import compute_ewma_volatility, compute_abnormal_return, compute_ddl_exposure, classify_vol_regime"
    - from: "volatility_chart.py"
      to: "chart_computations.py"
      via: "import compute_ewma_volatility, classify_vol_regime"
    - from: "context_builders/market.py"
      to: "StockDropAnalysis model"
      via: "reads ddl_exposure, ddl_settlement_estimate, abnormal_return fields"
    - from: "stock_drops.html.j2"
      to: "context_builders/market.py"
      via: "template variables mkt.ddl_exposure, mkt.ddl_settlement_estimate, evt.abnormal_return"
---

# Phase 89: Statistical Analysis Verification Report

**Phase Goal:** The system quantifies DDL/MDL dollar exposure from stock drops, identifies statistically significant abnormal returns on event days, and classifies market volatility into regimes that inform underwriting risk assessment
**Verified:** 2026-03-09T13:00:00Z
**Status:** passed
**Re-verification:** No -- initial verification

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Pricing section shows DDL exposure (market_cap x worst_drop_pct) and settlement (DDL x 1.8%) | VERIFIED | `compute_ddl_exposure` in chart_computations.py (L351-384), wired in stock_performance.py `_compute_ddl_for_drops` (L644-680), rendered via context_builders/market.py (L378-385) into stock_drops.html.j2 (L16-30) DDL card |
| 2 | Event days with abnormal returns flagged with t-stats, |t| >= 1.96 highlighted as significant | VERIFIED | `compute_abnormal_return` in chart_computations.py (L392-457) returns (ar_pct, t_stat, is_significant); wired per-drop in stock_performance.py `_compute_abnormal_returns_for_drops` (L581-641); template shows AR/t-stat columns conditionally with `**` significance flag (stock_drops.html.j2 L34-77) |
| 3 | Stock analysis shows both rolling vol and EWMA vol (lambda=0.94) with regime classification | VERIFIED | `compute_ewma_volatility` (L465-500) produces annualized EWMA series; `classify_vol_regime` (L508-562) classifies into LOW/NORMAL/ELEVATED/CRISIS; volatility_chart.py renders EWMA as orange dashed line (L170-178) alongside rolling 30d vol (L162-167), with regime in header stats (L473-484) |
| 4 | Volatility regime transitions visible with duration tracking | VERIFIED | `_render_regime_shading` in volatility_chart.py (L220-277) draws axvspan segments per regime period; regime label + duration shown in chart header (L483-484); extraction stores vol_regime_duration_days on StockPerformance (L578) |

**Score:** 4/4 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/stages/render/charts/chart_computations.py` | 4 computation functions | VERIFIED | compute_ddl_exposure (L351), compute_abnormal_return (L392), compute_ewma_volatility (L465), classify_vol_regime (L508) -- all substantive implementations, no stubs |
| `src/do_uw/models/market.py` | 3 fields on StockPerformance | VERIFIED | ewma_vol_current (L136), vol_regime (L140), vol_regime_duration_days (L144) -- all SourcedValue or int with None defaults |
| `src/do_uw/models/market_events.py` | 5 AR fields on StockDropEvent, 3 DDL fields on StockDropAnalysis | VERIFIED | StockDropEvent: abnormal_return_pct (L105), abnormal_return_t_stat (L109), is_statistically_significant (L113), market_model_alpha (L117), market_model_beta (L121); StockDropAnalysis: ddl_exposure (L155), mdl_exposure (L159), ddl_settlement_estimate (L163) |
| `src/do_uw/stages/extract/stock_performance.py` | Wiring of all computations | VERIFIED | _compute_ewma_and_regime (L550-578), _compute_abnormal_returns_for_drops (L581-641), _compute_ddl_for_drops (L644-680) -- all called from main extract_stock_performance (L755, L877, L882) |
| `src/do_uw/stages/render/charts/volatility_chart.py` | EWMA overlay + regime shading | VERIFIED | EWMA line plotted (L170-178), _render_regime_shading draws axvspan per regime segment (L220-277), regime in header (L473-484) |
| `src/do_uw/stages/render/context_builders/market.py` | DDL, AR, regime fields exported | VERIFIED | ewma_vol (L210), vol_regime (L212), vol_regime_duration (L214), AR/t-stat/sig per drop (L355-373), ddl_exposure/settlement (L378-385) |
| `src/do_uw/templates/html/sections/market/stock_drops.html.j2` | DDL card, AR columns, sig flags | VERIFIED | DDL card (L16-30), conditional AR/t-stat columns (L34-63), significance footnote (L75-77) |
| `tests/stages/render/charts/test_chart_computations.py` | Unit tests for computation functions | VERIFIED | 29 tests for DDL, AR, EWMA, regime (per summary; confirmed tests pass) |
| `tests/models/test_market_fields.py` | Model field tests | VERIFIED | 14 tests for field defaults and backward compat |
| `tests/stages/extract/test_stock_performance.py` | Integration tests | VERIFIED | 11 integration tests for EWMA, AR, DDL pipeline wiring |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| stock_performance.py | chart_computations.py | import classify_vol_regime, compute_abnormal_return, compute_ddl_exposure, compute_ewma_volatility | WIRED | L41-46 imports all 4 functions; each called in dedicated helper functions |
| volatility_chart.py | chart_computations.py | import compute_ewma_volatility, classify_vol_regime | WIRED | L21-25 imports; L87-88 calls both; results passed to subplot and header |
| context_builders/market.py | StockPerformance/StockDropAnalysis | reads ewma_vol, vol_regime, ddl_exposure, AR fields | WIRED | L209-214 exports vol fields, L355-385 exports AR and DDL fields |
| stock_drops.html.j2 | context_builders/market.py | template vars mkt.ddl_exposure, evt.abnormal_return, evt.t_stat, evt.significant | WIRED | L17-30 DDL card, L34-63 AR columns, L75-77 footnote |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-----------|-------------|--------|----------|
| STOCK-02 | 89-01, 89-02 | DDL/MDL exposure computed as market_cap x worst_drop_pct with settlement estimate (DDL x 1.8%) | SATISFIED | compute_ddl_exposure function + extraction wiring + DDL card in template |
| STOCK-04 | 89-01, 89-02 | Abnormal returns via market model with t-stat significance (|t| >= 1.96) | SATISFIED | compute_abnormal_return function + per-drop wiring + AR columns in template |
| STOCK-05 | 89-01, 89-02 | EWMA volatility (lambda=0.94) with regime detection (low/normal/elevated/crisis) | SATISFIED | compute_ewma_volatility + classify_vol_regime functions + chart overlay + regime shading |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| stock_performance.py | - | File is 925 lines (exceeds 500-line project rule) | INFO | Pre-existing violation (was 770 lines before phase 89). Phase 89 added 145 lines. Acknowledged in summary as out-of-scope for this phase. |

### Human Verification Required

### 1. DDL Dollar Amount Accuracy

**Test:** Run `underwrite V` or `underwrite RPM`, open HTML, check stock drops section for DDL Exposure card
**Expected:** Shows formatted dollar amount (e.g. "$1.5B") and settlement estimate (e.g. "$27.0M")
**Why human:** Cannot verify actual dollar formatting and contextual placement without visual inspection

### 2. EWMA Overlay on Volatility Chart

**Test:** Open volatility chart in HTML output after pipeline run
**Expected:** Orange dashed line (EWMA) visible alongside blue solid line (rolling 30d vol); regime shading in background (subtle green/amber/red tints); regime label + duration in header stats
**Why human:** Chart visual quality and legend readability require visual inspection

### 3. AR Significance Flags in Drop Table

**Test:** Check stock drops table in HTML output
**Expected:** AR and t-stat columns appear when data exists; significant drops marked with `**`; footnote explains AR methodology
**Why human:** Conditional column rendering and visual indicator quality need visual check

### Gaps Summary

No gaps found. All 4 success criteria from ROADMAP.md are verified through code-level inspection:
- All 4 computation functions are substantive implementations (not stubs)
- All 11 model fields exist with correct types and defaults
- Extraction pipeline calls all computation functions in the correct order
- Rendering pipeline exports all fields and templates display them
- All 54 tests pass (29 computation + 14 model + 11 integration)
- All 4 commits verified in git history

The only notable item is `stock_performance.py` at 925 lines (exceeding the 500-line project rule), but this is a pre-existing issue acknowledged as out-of-scope.

---

_Verified: 2026-03-09T13:00:00Z_
_Verifier: Claude (gsd-verifier)_
