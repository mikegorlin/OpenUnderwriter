---
phase: 90-drop-enhancements
verified: 2026-03-09T14:00:00Z
status: passed
score: 4/4 success criteria verified
---

# Phase 90: Drop Enhancements Verification Report

**Phase Goal:** Stock drop scoring reflects recency (recent drops matter more), each individual drop is decomposed to show whether the company or the market drove it, and unexplained drops trigger automatic investigation for contemporaneous disclosures
**Verified:** 2026-03-09T14:00:00Z
**Status:** passed
**Re-verification:** No -- initial verification

## Goal Achievement

### Observable Truths (from Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A drop from 3 months ago scores higher than an identical drop from 18 months ago -- the time-decay function visibly affects the drop severity ranking in the output | VERIFIED | `compute_decay_weight` uses 180-day half-life exponential decay (stock_drop_decay.py:21-46). `apply_decay_weights` sorts drops by `decay_weighted_severity` descending (line 84-87). Context builder sorts by `decay_weighted_severity` (market.py:347-354). HTML template footer states "Sorted by recency-weighted severity" (stock_drops.html.j2:97). 15 decay tests pass including half-life validation. |
| 2 | Each identified drop event shows its own 3-component decomposition (market / sector / company-specific) -- the underwriter can see at a glance whether a 15% drop was company-driven or a market-wide sell-off | VERIFIED | `decompose_drop` calls `compute_return_decomposition` and sets `market_pct`, `sector_pct`, `company_pct` on each drop (stock_drop_decomposition.py:17-84). HTML template shows Market/Sector/Company columns conditionally (stock_drops.html.j2:51-55, 78-85). Market-Driven badge renders when `is_market_driven` (line 83). Word renderer includes same columns (sect4_drop_tables.py:91-95). 9 decomposition tests pass. |
| 3 | Drops without a known catalyst trigger a reverse lookup that searches for contemporaneous 8-K filings and news -- any findings are attached to the drop as potential corrective disclosures | VERIFIED | `enrich_drops_with_reverse_lookup` skips drops with `trigger_event`, then tries `_find_8k_after_drop` (1-14 day window, D&O-relevant items only), falls back to `_search_web_for_disclosure` (stock_drop_enrichment.py:548-609). Pipeline calls this at step 8c (stock_performance.py:907-915). 15 reverse lookup tests pass. |
| 4 | The corrective disclosure enhancement surfaces previously unlinked 8-K/news items that coincide with significant drops | VERIFIED | Disclosure fields (`corrective_disclosure_type`, `corrective_disclosure_lag_days`, `corrective_disclosure_url`) populated by reverse lookup. HTML template shows Disclosure column with badge "8-K +3d" or "News +7d" format (stock_drops.html.j2:57-59, 87-91). Context builder formats via `_format_disclosure_badge` (market.py:38-45). F2 scoring applies 1.5x uplift for drops with disclosures (factor_scoring.py:476). |

**Score:** 4/4 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/models/market_events.py` | 9 new fields on StockDropEvent | VERIFIED | Lines 125-161: decay_weight, decay_weighted_severity, market_pct, sector_pct, company_pct, is_market_driven, corrective_disclosure_type, corrective_disclosure_lag_days, corrective_disclosure_url |
| `src/do_uw/stages/extract/stock_drop_decay.py` | compute_decay_weight, apply_decay_weights | VERIFIED | 98 lines, 180-day half-life, exponential decay, severity sorting |
| `src/do_uw/stages/extract/stock_drop_decomposition.py` | decompose_drop, decompose_drops | VERIFIED | 121 lines, reuses compute_return_decomposition, market-driven flag at >50% |
| `src/do_uw/stages/extract/stock_drop_enrichment.py` | enrich_drops_with_reverse_lookup, _find_8k_after_drop | VERIFIED | Lines 430-609, D&O-relevant items filter, web fallback, lag calculation |
| `src/do_uw/stages/extract/stock_performance.py` | Pipeline wiring for decay, decomposition, reverse lookup | VERIFIED | Steps 8a-8c at lines 888-916 |
| `src/do_uw/stages/score/factor_data.py` | drop_contributions data key | VERIFIED | Lines 145-159 |
| `src/do_uw/stages/score/factor_scoring.py` | _apply_drop_contribution_modifier | VERIFIED | Lines 141-145 (call site), 447-491 (function), compound formula: magnitude * decay * company_pct * disclosure_mult |
| `src/do_uw/stages/render/context_builders/market.py` | New columns in drop_events context | VERIFIED | Lines 389-395: decay_weight, market_pct, sector_pct, company_pct, market_driven, disclosure_badge |
| `src/do_uw/templates/html/sections/market/stock_drops.html.j2` | Recency, Market, Sector, Company, Disclosure columns | VERIFIED | Conditional display via has_decomp/has_disclosure, Market-Driven badge, Disclosure badge |
| `src/do_uw/stages/render/sections/sect4_drop_tables.py` | Word renderer with same columns | VERIFIED | Recency column (line 69, 85), decomposition columns (lines 91-95), Market-Driven badge (line 94-95), decay-weighted sort (lines 49-54) |
| `tests/stages/extract/test_stock_drop_decay.py` | Decay computation tests | VERIFIED | 136 lines, 15 tests pass |
| `tests/stages/extract/test_stock_drop_decomposition.py` | Per-drop decomposition tests | VERIFIED | 165 lines, 9 tests pass |
| `tests/stages/extract/test_stock_drop_enrichment_reverse.py` | Reverse 8-K lookup tests | VERIFIED | 221 lines, 15 tests pass |
| `tests/stages/score/test_factor_scoring_f2_decay.py` | F2 decay/disclosure scoring tests | VERIFIED | 191 lines, 9 tests pass |
| `tests/stages/render/test_market_context_drops.py` | Rendering tests | VERIFIED | 147 lines, 12 tests pass |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| stock_performance.py | stock_drop_decay.py | `from do_uw.stages.extract.stock_drop_decay import apply_decay_weights` | WIRED | Line 901 |
| stock_performance.py | stock_drop_decomposition.py | `from do_uw.stages.extract.stock_drop_decomposition import decompose_drops` | WIRED | Line 892 |
| stock_performance.py | stock_drop_enrichment.py | `enrich_drops_with_reverse_lookup` | WIRED | Lines 908, 913 |
| stock_drop_decomposition.py | chart_computations.py | `from do_uw.stages.render.charts.chart_computations import compute_return_decomposition` | WIRED | Line 12 |
| factor_scoring.py | factor_data.py | `drop_contributions` data key | WIRED | factor_data.py:159 sets key, factor_scoring.py:465 reads it |
| factor_scoring.py | F2 score_factor call | `_apply_drop_contribution_modifier` | WIRED | Called at line 143 for F2_stock_decline |
| context_builders/market.py | stock_drops.html.j2 | decay_weight, market_driven, disclosure_badge keys | WIRED | Context keys match template variables |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| STOCK-06 | 90-01, 90-02 | Corrective disclosure detection enhanced with reverse lookup -- unexplained drops trigger search for contemporaneous 8-K filings and news | SATISFIED | `enrich_drops_with_reverse_lookup` searches 8-K (1-14d window) and web results; sets corrective_disclosure_type/lag_days/url; displayed in HTML/Word |
| STOCK-08 | 90-01, 90-02 | Time-decay weighting applied to stock drops -- recent drops score higher than older ones using exponential decay function | SATISFIED | 180-day half-life exponential decay in `stock_drop_decay.py`; sorts drops by `decay_weighted_severity`; F2 scoring uses decay_weight as multiplier |
| STOCK-09 | 90-01, 90-02 | Per-drop return decomposition showing market/sector/company-specific attribution for every identified drop event | SATISFIED | `decompose_drop` uses `compute_return_decomposition`; sets market_pct/sector_pct/company_pct; Market-Driven badge at >50%; displayed in HTML/Word |

No orphaned requirements found -- REQUIREMENTS.md maps exactly STOCK-06, STOCK-08, STOCK-09 to Phase 90.

### Anti-Patterns Found

No TODO, FIXME, PLACEHOLDER, HACK, or stub patterns found in any Phase 90 files.

### Human Verification Required

### 1. Visual Drop Table Layout

**Test:** Run `underwrite AAPL --fresh` and open the HTML output. Scroll to the Significant Stock Drops table.
**Expected:** Table shows Recency, Market, Sector, Company columns with data. Market-Driven badge appears in blue on appropriate drops. Drops are sorted by recency-weighted severity (not raw magnitude). If any corrective disclosures found, Disclosure column appears with "8-K +Nd" badge.
**Why human:** Visual layout, column alignment, badge styling, and data quality require human inspection.

### 2. F2 Score Impact

**Test:** Compare F2 scoring sub-components in the output to verify compound modifier is reflected.
**Expected:** F2 evidence log shows "Drop contribution modifier: X.XXx" line. The modifier should be <1.0 when drops are old or market-driven, and >1.0 when drops have corrective disclosures.
**Why human:** Need to verify the modifier value is reasonable for the specific ticker's drop profile.

### 3. Word Document Parity

**Test:** Open the .docx output and compare the drops table to the HTML version.
**Expected:** Same columns (Recency, Market, Sector, Company, Market-Driven label) appear in the Word table. Sort order matches HTML.
**Why human:** Word table formatting cannot be verified programmatically.

### Gaps Summary

No gaps found. All 4 success criteria verified. All 15 artifacts pass three-level verification (exists, substantive, wired). All 7 key links confirmed. All 3 requirements satisfied. 60 tests pass. No anti-patterns detected.

---

_Verified: 2026-03-09T14:00:00Z_
_Verifier: Claude (gsd-verifier)_
