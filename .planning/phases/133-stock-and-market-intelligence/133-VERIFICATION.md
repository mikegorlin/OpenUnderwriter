---
phase: 133-stock-and-market-intelligence
verified: 2026-03-27T05:30:00Z
status: passed
score: 10/10 must-haves verified
re_verification: true
previous_status: gaps_found
previous_score: 9/10
gaps_closed:
  - "Earnings reaction table shows real next-day and 1-week return values — compute_earnings_reactions() is now called in build_earnings_trust() via reaction_lookup pattern"
gaps_remaining: []
regressions: []
---

# Phase 133: Stock and Market Intelligence Verification Report

**Phase Goal:** Every significant stock event is investigated and attributed — underwriters see per-drop causation analysis, earnings reaction patterns, analyst consensus shifts, volume anomalies, and idiosyncratic risk metrics that directly inform loss causation defense assessment
**Verified:** 2026-03-27
**Status:** passed
**Re-verification:** Yes — after gap closure (Plan 133-03)

## Re-verification Context

Previous verification (2026-03-26) found 9/10 truths verified. The single gap was STOCK-04: `compute_earnings_reactions()` was a fully implemented, tested function that was never called in the pipeline, causing next-day and 1-week return columns to always render N/A.

Plan 133-03 closed this gap with two commits:
- `a478b8f7` — wired `compute_earnings_reactions()` into `build_earnings_trust()` using a `reaction_lookup` dict computed from `acquired_data.market_data["history_1y"]` and quarter dates from the model
- `6abfcbb4` — deduplicated local `_compute_correlation()` / `_compute_r_squared()` in `_market_correlation.py` by importing canonical functions from `chart_computations.py`

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | Every >10% drop shows COMPANY/MARKET/SECTOR attribution percentages and a D&O litigation theory one-liner | ✓ VERIFIED | `_market_display.py` `build_drop_events()` returns `do_theory` and `attribution_split` with market_pct/sector_pct/company_pct. `stock_drops.html.j2` renders attribution bar and D&O theory one-liner for drops >= 10%. (4 matches on do_theory/attribution_split — no regression) |
| 2  | Multi-day consecutive drops are consolidated into single events with per-day breakdown | ✓ VERIFIED | `build_drop_events()` populates `consolidated_days` and `is_multi_day` from `evt.drop_type == "MULTI_DAY"`. Template shows expandable per-day breakdown. (8 matches on is_multi_day/consolidated_days — no regression) |
| 3  | Earnings trust narrative connects beat/miss patterns to market reaction direction | ✓ VERIFIED | `build_earnings_trust()` generates `earnings_trust_narrative` from beat_rate, beat_sell_off patterns, consecutive_miss_count. (1 match — present) |
| 4  | Analyst consensus shows EPS revision trends (7d/30d) and price target range | ✓ VERIFIED | `build_eps_revision_trends()` and `build_analyst_targets()` both present. `analyst_revisions.html.j2` renders both tables. (2 matches — no regression) |
| 5  | Volume anomaly table lists >2x days cross-referenced with 8-K filings and news | ✓ VERIFIED | `build_volume_anomalies()` present in `_market_volume.py`, reads volume_spike_events, cross-references 8-K/news. (1 match — no regression) |
| 6  | Correlation metrics card shows correlation vs SPY, vs sector ETF, R-squared, idiosyncratic risk % | ✓ VERIFIED | `build_correlation_metrics()` in `_market_correlation.py` now imports canonical functions from `chart_computations.py` — local duplicates removed. (1 match — dedup confirmed, function still present) |
| 7  | EarningsQuarterRecord has next_day_return_pct and week_return_pct fields | ✓ VERIFIED | Both `SourcedValue[float] | None` fields present in `market_events.py`. (2 matches — no regression) |
| 8  | compute_earnings_reactions() computes multi-window returns from price history | ✓ VERIFIED | Function defined in `earnings_reactions.py`. 11 tests pass. (1 match — no regression) |
| 9  | compute_correlation() and compute_r_squared() available in chart_computations.py | ✓ VERIFIED | Both functions present in `chart_computations.py`. (2 matches — no regression) |
| 10 | Earnings reaction table shows per-earnings-date day-of/next-day/1-week returns (STOCK-04) | ✓ VERIFIED | `_market_acquired_data.py` line 13 imports `compute_earnings_reactions`. Line 542 calls it to build `computed_reactions`. Lines 545-547 build `reaction_lookup`. Lines 597-603 use the lookup to populate `next_day_return` and `week_return` in every reaction row, falling back to model fields when populated. The outdated "may not exist yet (Plan 01 dep)" comment was removed. New test `test_build_earnings_trust_populates_multi_window_returns` passes and asserts non-N/A values. |

**Score:** 10/10 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/models/market_events.py` | Extended EarningsQuarterRecord with next_day_return_pct, week_return_pct | ✓ VERIFIED | Both fields present (2 grep matches) — no regression |
| `src/do_uw/stages/extract/earnings_reactions.py` | Earnings reaction multi-window return computation | ✓ VERIFIED | `compute_earnings_reactions` defined, 11 tests pass, now imported and called in `_market_acquired_data.py` — no longer orphaned |
| `src/do_uw/stages/render/charts/chart_computations.py` | Correlation and R-squared computations | ✓ VERIFIED | `compute_correlation`, `compute_r_squared`, `compute_daily_returns` all present (2 matches) |
| `src/do_uw/stages/render/context_builders/_market_volume.py` | Volume anomaly table context builder with 8-K cross-reference | ✓ VERIFIED | `build_volume_anomalies()` present — no regression |
| `src/do_uw/stages/render/context_builders/_market_correlation.py` | Return correlation metrics context builder — deduped | ✓ VERIFIED | Local `_compute_correlation()` and `_compute_r_squared()` removed; now imports canonical functions from `chart_computations.py` (lines 14-19). `build_correlation_metrics()` still present. |
| `src/do_uw/stages/render/context_builders/_market_acquired_data.py` | build_earnings_trust calls compute_earnings_reactions | ✓ VERIFIED | Import at line 13, call at line 542, reaction_lookup at lines 545-547, fallback lookups at lines 582-584 and 599-603 |
| `src/do_uw/templates/html/sections/market/earnings_reaction.html.j2` | Earnings reaction table with multi-window returns | ✓ VERIFIED | File present with all required columns |
| `src/do_uw/templates/html/sections/market/volume_anomalies.html.j2` | Volume anomaly table with event cross-reference | ✓ VERIFIED | File present — no regression |
| `src/do_uw/templates/html/sections/market/analyst_revisions.html.j2` | EPS revision trends and price target range | ✓ VERIFIED | File present — no regression |
| `src/do_uw/templates/html/sections/market/correlation_metrics.html.j2` | Return correlation metrics card | ✓ VERIFIED | File present — no regression |
| `src/do_uw/templates/html/sections/market.html.j2` | Updated include list (was 22, now 23) | ✓ VERIFIED | 23 `{% include %}` directives found (was 22 in initial verification — one addition, no removals) |
| `tests/stages/extract/test_earnings_reactions.py` | Tests for earnings reaction computation | ✓ VERIFIED | 11 tests pass |
| `tests/stages/render/test_chart_computations_correlation.py` | Tests for correlation and R-squared | ✓ VERIFIED | 8 tests pass |
| `tests/stages/render/test_market_context_phase133.py` | Tests for all new context builders, including gap closure test | ✓ VERIFIED | 12 tests collected (up from 11); includes `test_build_earnings_trust_populates_multi_window_returns` |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `_market_acquired_data.py` | `_market_display.py` build_drop_events() | do_theory + attribution_split return keys | ✓ WIRED | No regression — 4 matches confirmed |
| `market.py` extract_market() | `_market_volume.py`, `_market_correlation.py`, `_market_acquired_data.py` | result.update() calls | ✓ WIRED | No regression — all builders still present |
| `market.html.j2` | New template files | Jinja2 `{% include %}` | ✓ WIRED | 23 includes present — no regression |
| `earnings_reactions.py` | EarningsQuarterRecord model fields | `compute_earnings_reactions()` called in `build_earnings_trust()` via `reaction_lookup` | ✓ WIRED | **Gap closed.** Import at line 13, call at line 542, lookup populated at lines 545-547, applied at lines 597-603. |
| `_market_correlation.py` | `chart_computations.py` | Import of `compute_correlation`, `compute_r_squared` | ✓ WIRED | **Tech debt resolved.** Local duplicate functions removed; canonical imports at lines 14-19. |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `earnings_reaction.html.j2` | `mkt.earnings_reaction[].day_of_return` | `build_earnings_trust()` reads `qtr.stock_reaction_pct.value` from EarningsQuarterRecord; falls back to `reaction_lookup["day_of_return"]` | Yes — primary field populated by existing extract stage; computed fallback now also wired | ✓ FLOWING |
| `earnings_reaction.html.j2` | `mkt.earnings_reaction[].next_day_return` | `build_earnings_trust()` checks model field `next_day_return_pct` first; falls back to `reaction_lookup[qtr_date]["next_day_return"]` computed by `compute_earnings_reactions()` from `history_1y` price data | Yes — `compute_earnings_reactions()` called at line 542 with price history from `acquired_data.market_data["history_1y"]` | ✓ FLOWING |
| `earnings_reaction.html.j2` | `mkt.earnings_reaction[].week_return` | `build_earnings_trust()` checks model field `week_return_pct` first; falls back to `reaction_lookup[qtr_date]["week_return"]` | Yes — same `compute_earnings_reactions()` call populates week window | ✓ FLOWING |
| `volume_anomalies.html.j2` | `mkt.volume_anomalies` | `build_volume_anomalies()` reads `state.extracted.market.stock.volume_spike_events` | Real data from extract stage if volume spikes detected | ✓ FLOWING |
| `correlation_metrics.html.j2` | `mkt.correlation_metrics` | `build_correlation_metrics()` reads `state.acquired_data.market_data["history_1y"]`; now uses canonical `compute_correlation`/`compute_r_squared` from `chart_computations.py` | Real price history from yfinance acquisition | ✓ FLOWING |
| `analyst_revisions.html.j2` | `mkt.eps_revisions`, `mkt.analyst_targets` | `build_eps_revision_trends/targets()` reads `acquired_data.market_data["eps_revisions"]`, `["analyst_price_targets"]` | Real data from yfinance acquisition conditional on keys being present | ✓ FLOWING (conditional on yfinance providing these keys) |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| compute_earnings_reactions tests pass | `uv run pytest tests/stages/extract/test_earnings_reactions.py -q` | 11 passed | ✓ PASS |
| compute_correlation/r_squared tests pass | `uv run pytest tests/stages/render/test_chart_computations_correlation.py -q` | 8 passed | ✓ PASS |
| Phase 133 context builder tests pass (all 12 including gap closure test) | `uv run pytest tests/stages/render/test_market_context_phase133.py -q` | 12 passed | ✓ PASS |
| Market template + drops regression tests | `uv run pytest tests/stages/render/test_market_templates.py tests/stages/render/test_market_context_drops.py -q` | 29 passed | ✓ PASS |
| All 60 phase 133 tests pass | `uv run pytest tests/stages/render/test_market_context_phase133.py tests/stages/extract/test_earnings_reactions.py tests/stages/render/test_chart_computations_correlation.py tests/stages/render/test_market_templates.py tests/stages/render/test_market_context_drops.py -q` | 60 passed | ✓ PASS |
| compute_earnings_reactions() called in pipeline | `grep -n "compute_earnings_reactions" _market_acquired_data.py` | Import at line 13, call at line 542 | ✓ PASS |
| Local duplicate correlation functions removed | `grep -n "def _compute_correlation\|def _compute_r_squared" _market_correlation.py` | No matches | ✓ PASS |
| Canonical correlation imported from chart_computations | `grep -n "compute_correlation," _market_correlation.py` | Line 15 | ✓ PASS |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| STOCK-01 | 133-02 | Every >10% stock decline analyzed with attribution (COMPANY/MARKET/SECTOR) | ✓ SATISFIED | `build_drop_events()` returns `attribution_split`; `stock_drops.html.j2` renders attribution bar — no regression |
| STOCK-02 | 133-02 | Each decline cross-referenced with 8-K filings and news, D&O risk assessment | ✓ SATISFIED | D&O theory mapping in `_market_display.py`; 8-K cross-reference in `build_volume_anomalies()` — no regression |
| STOCK-03 | 133-02 | Multi-day consecutive drops consolidated as single events | ✓ SATISFIED | `is_multi_day` flag and `consolidated_days` list in `build_drop_events()` — no regression |
| STOCK-04 | 133-01, 133-03 | Earnings reaction table: per-earnings date, EPS actual vs estimate, beat/miss, day-of/next-day/1-week returns | ✓ SATISFIED | **Gap closed by Plan 133-03.** `compute_earnings_reactions()` is now called in `build_earnings_trust()` at line 542. `reaction_lookup` provides next_day_return and week_return for each quarter whose date is covered by price history. Test `test_build_earnings_trust_populates_multi_window_returns` passes and asserts non-N/A values. |
| STOCK-05 | 133-02 | Earnings trust assessment: pattern of beats/misses, market reaction on beats vs misses | ✓ SATISFIED | `build_earnings_trust()` generates narrative from beat_rate, beat_sell_off patterns, consecutive_miss_count — no regression |
| STOCK-06 | 133-02 | Analyst consensus display: rating breakdown, price target range, EPS revision trends | ✓ SATISFIED | `build_eps_revision_trends()` and `build_analyst_targets()` present — no regression |
| STOCK-07 | 133-02 | Volume anomaly table: days with volume >2x 20-day average, cross-referenced with known events | ✓ SATISFIED | `build_volume_anomalies()` in `_market_volume.py` — no regression |
| STOCK-08 | 133-01, 133-02 | Return correlation metrics: correlation vs sector ETF, vs SPY, R-squared, idiosyncratic risk % | ✓ SATISFIED | `build_correlation_metrics()` now uses canonical functions from `chart_computations.py`; dedup is a quality improvement, no behavior change — no regression |

---

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| No new anti-patterns | All previous blockers resolved | — | — |

Previous blockers resolved:
- `earnings_reactions.py` was orphaned — now imported and called in `_market_acquired_data.py`
- "may not exist yet (Plan 01 dep)" comment removed from `build_earnings_trust()`
- Local duplicate `_compute_correlation()` / `_compute_r_squared()` removed from `_market_correlation.py`

---

### Human Verification Items

The following items from initial verification required a pipeline run to confirm. With STOCK-04 gap now closed by static code analysis, they remain recommended but are not blocking automated verification:

#### 1. Earnings Reaction — Next-Day / 1-Week Returns Actually Populated

**Test:** Run `underwrite AAPL --fresh`, open the HTML worksheet, navigate to the Market section, find "Earnings Reaction Analysis"
**Expected:** Day-Of Return column shows real percentage values. Next-Day Return and 1-Week Return columns also show actual computed values (e.g., +1.2%, -3.4%) — not N/A across the board.
**Why human:** Full pipeline run needed to confirm `history_1y` is present in `acquired_data.market_data` and that quarter dates align with price history dates.

#### 2. Correlation Metrics Card — Renders with Real Data

**Test:** Run against a company with at least 1 year of history. Find "Return Correlation Analysis" card in Market section.
**Expected:** Corr. vs SPY shows a value (e.g., "0.74"), R-Squared shows a value, Idiosyncratic Risk shows a percentage with colored badge.
**Why human:** Requires `spy_history_1y` to be present in `acquired_data.market_data` — cannot verify without running the full pipeline.

---

### Gaps Summary

No gaps remain. All 10 observable truths are verified. All 8 requirements (STOCK-01 through STOCK-08) are satisfied.

The single gap from initial verification (STOCK-04) was closed by Plan 133-03 in two commits:
1. `a478b8f7` — `compute_earnings_reactions()` is now imported and called inside `build_earnings_trust()`. The `reaction_lookup` dict maps each quarter date to its computed day-of, next-day, and 1-week returns. The fallback pattern (model fields first, computed reactions second) is clean and future-proof.
2. `6abfcbb4` — Local duplicate correlation functions removed from `_market_correlation.py`; canonical imports from `chart_computations.py` now used. No behavior change.

60 tests pass across 5 test files with zero regressions.

---

_Verified: 2026-03-27_
_Verifier: Claude (gsd-verifier)_
_Re-verification: Yes — after Plan 133-03 gap closure_
