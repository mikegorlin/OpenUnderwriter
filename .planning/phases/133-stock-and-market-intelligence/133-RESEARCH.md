# Phase 133: Stock and Market Intelligence - Research

**Researched:** 2026-03-26
**Domain:** Stock market data extraction, decomposition, and rendering for D&O underwriting
**Confidence:** HIGH

## Summary

Phase 133 is primarily a WIRING and PRESENTATION phase, not a new-data-acquisition phase. The codebase already has extensive infrastructure for stock drop decomposition, volume spike detection, earnings tracking, analyst consensus, and return correlation -- but much of this data is either (a) computed but not displayed, (b) displayed only in the beta report but not in the main market section, or (c) acquired from yfinance but never processed. The gap is in surfacing hidden state data, adding cross-reference correlation, and building new tabular displays for data that currently exists only as chart overlays or raw acquired data.

Three critical architectural findings: (1) The main `market.html.j2` includes only 13 sub-templates but the `sections/market/` directory has 19 templates -- 6 are orphaned (only used in beta_report or nowhere). (2) yfinance acquires `eps_trend`, `eps_revisions`, `growth_estimates`, and `analyst_price_targets` but these are not rendered in any market context builder. (3) Volume spikes are detected and drawn as red bars on stock charts but have no tabular display anywhere.

**Primary recommendation:** Wire existing computed data to new template displays. Build 5 new context builder functions and 4 new/enhanced templates. Minimal model changes (add next-day/1-week return fields to EarningsQuarterRecord). No new external dependencies.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Full event card per >10% drop: date, magnitude, COMPANY/MARKET/SECTOR percentage split, catalyst (from 8-K/news), recovery days, and one-line D&O litigation theory mapping
- **D-02:** Multi-day consecutive drops consolidated into single events with per-day breakdown available
- **D-03:** Existing infrastructure handles most of drop attribution (stock_drop_decomposition.py already splits market/sector/company)
- **D-04:** Full reaction analysis table per quarter: date, EPS estimate vs actual, beat/miss flag, revenue estimate vs actual, day-of return, next-day return, 1-week return
- **D-05:** Earnings trust assessment as pattern narrative after the table
- **D-06:** Fix guidance/analyst conflation -- clearly separate analyst estimates from company-issued guidance
- **D-07:** Revision trend table: rating breakdown, price target range, plus 30d and 90d EPS revision direction
- **D-08:** Full event cross-reference: volume >2x 20-day average, cross-referenced with 8-K filings and news
- **D-09:** Existing volume_spikes.py detects threshold crossings; this phase adds event correlation layer and tabular display
- **D-10:** Dedicated metrics card: correlation vs sector ETF, vs SPY, R-squared, idiosyncratic risk %
- **D-11:** Optimize existing sources first (yfinance primary). No new API dependencies
- **D-12:** Surface hidden state data collected but not displayed
- **D-13:** Improve how currently-displayed market data is organized and presented

### Claude's Discretion
- Exact layout/CSS for drop event cards, earnings table, analyst table, volume table, correlation card
- How to consolidate multi-day drops algorithmically (gap tolerance, minimum cumulative threshold)
- Which state fields are "hidden" vs already displayed (audit during implementation)
- Where to place new displays within the existing market section structure

### Deferred Ideas (OUT OF SCOPE)
- "Executive Brief narrative boilerplate overhaul" -- belongs in a future rendering quality pass
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| STOCK-01 | Every >10% stock decline analyzed with COMPANY/MARKET/SECTOR attribution | `decompose_drop()` already computes this; `StockDropEvent` has `market_pct`, `sector_pct`, `company_pct` fields; existing `stock_drops.html.j2` already renders decomposition columns. Enhancement needed: event card format with D&O theory. |
| STOCK-02 | Each decline cross-referenced with 8-K filings and news for catalyst identification | `stock_drop_enrichment.py` already enriches from 8-K and web search; `trigger_category`, `trigger_description`, `do_assessment` fields exist. `stock_drop_catalyst.html.j2` exists but is NOT included in main market template. |
| STOCK-03 | Multi-day consecutive drops consolidated as single events | `_consolidate_overlapping_drops()` in `_market_display.py` already does this (merges drops within 5 calendar days). Enhancement: surface per-day breakdown. |
| STOCK-04 | Earnings reaction table: per-earnings date, EPS actual vs estimate, beat/miss, day-of/next-day/1-week returns | `EarningsQuarterRecord` has `stock_reaction_pct` (day-of only). `earnings_dates` from yfinance has dates+surprise. Need: add `next_day_return_pct` and `week_return_pct` fields, compute from price history. |
| STOCK-05 | Earnings trust assessment: pattern of beats/misses, market reaction on beats vs misses | `EarningsGuidanceAnalysis` has `beat_rate`, `consecutive_miss_count`, `philosophy`. Need: new trust narrative generator analyzing reaction-vs-result correlation. |
| STOCK-06 | Analyst consensus: rating breakdown, price target range, EPS revision trends (30d/90d) | `AnalystSentimentProfile` and `recommendation_breakdown` context exist. yfinance `eps_revisions` data is ACQUIRED but NOT rendered. `analyst_price_targets` also acquired but not used in market context. |
| STOCK-07 | Volume anomaly table: days with volume >2x 20-day average, cross-referenced with known events | `volume_spikes.py` detects spikes (returns date, volume, volume_multiple, price_change_pct). `volume_spike_events` field on `StockPerformance`. NO tabular template exists -- only red bar overlays on stock charts. |
| STOCK-08 | Return correlation metrics: vs sector ETF, vs SPY, R-squared, idiosyncratic risk % | `compute_idiosyncratic_vol()` and `compute_return_decomposition()` exist. `ChartData` has `company_beta`, `sector_beta`, `idiosyncratic_vol`. Stock chart template renders return attribution table. Need: dedicated correlation metrics card. |
</phase_requirements>

## Architecture Patterns

### Existing Data Flow
```
ACQUIRE (yfinance)
  → market_data dict (history_1y, earnings_dates, eps_revisions, etc.)
    → EXTRACT (stock_performance.py, volume_spikes.py, stock_drop_enrichment.py)
      → state.extracted.market (StockPerformance, StockDropAnalysis, EarningsGuidanceAnalysis, etc.)
        → RENDER context_builders (market.py, _market_display.py, _market_acquired_data.py)
          → template-ready dicts
            → Jinja2 templates (sections/market/*.html.j2)
```

### Recommended Project Structure for Changes
```
src/do_uw/
  models/
    market_events.py        # ADD: next_day_return_pct, week_return_pct to EarningsQuarterRecord
  stages/
    extract/
      stock_performance.py  # ADD: compute earnings reaction windows from price data
      earnings_reactions.py # NEW: dedicated earnings reaction computation module
    render/
      context_builders/
        market.py           # MODIFY: wire new context keys
        _market_display.py  # MODIFY: enhanced drop event card builder
        _market_acquired_data.py  # MODIFY: build eps_revisions, analyst_price_targets context
        _market_correlation.py    # NEW: return correlation metrics builder
        _market_volume.py         # NEW: volume anomaly table builder
  templates/html/sections/market/
    stock_drops.html.j2          # MODIFY: event card layout with D&O theory
    volume_anomalies.html.j2     # NEW: volume spike table with event cross-reference
    earnings_reaction.html.j2    # NEW: full earnings reaction table with multi-window returns
    analyst_revisions.html.j2    # NEW: EPS revision trends (30d/90d) display
    correlation_metrics.html.j2  # NEW: return correlation card
    market.html.j2               # MODIFY: add missing includes
```

### Pattern 1: Context Builder Extension
**What:** Add new builder functions in existing files or new <500-line modules, following the established dict-return pattern
**When to use:** For every new display (volume anomalies, correlation metrics, earnings reactions)
**Example:**
```python
# Source: existing pattern in _market_acquired_data.py
def build_volume_anomalies(state: AnalysisState) -> dict[str, Any]:
    """Build volume anomaly table with event cross-reference."""
    md = _get_md_dict(state)
    stock = state.extracted.market.stock if state.extracted and state.extracted.market else None
    if not stock or not stock.volume_spike_events:
        return {}

    eight_k = state.extracted.market.eight_k_items if state.extracted and state.extracted.market else None
    rows = []
    for spike in stock.volume_spike_events:
        # Cross-reference with 8-K by date proximity...
        rows.append({...})
    return {"volume_anomalies": rows} if rows else {}
```

### Pattern 2: Template Fragment Include
**What:** New templates in `sections/market/` included in `market.html.j2`
**When to use:** Each new display gets its own template file
**Key rule:** Template reads from `mkt` dict (the market context), uses existing macros (kv_table, etc.)

### Pattern 3: Model Field Extension
**What:** Add fields to existing Pydantic models
**When to use:** When new computed data needs to persist in state
**Key rule:** All new fields MUST have default values (backward compatible with existing state.json)

### Anti-Patterns to Avoid
- **Don't create new extractors for already-acquired data:** yfinance already fetches eps_trend, eps_revisions, analyst_price_targets. Wire them through context builders, don't re-acquire.
- **Don't duplicate consolidation logic:** `_consolidate_overlapping_drops()` already exists for multi-day merge. Enhance it, don't rewrite.
- **Don't put business logic in templates:** D&O theory mapping should be in context builders or enrichment code, not Jinja2 conditionals.
- **Don't break existing displays:** All changes are ADDITIVE. Existing stock drops table, earnings guidance, analyst consensus stay intact.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Return decomposition | Custom market/sector/company split | `compute_return_decomposition()` in chart_computations.py | Already handles edge cases, zero guards, sign conventions |
| Volume spike detection | Custom volume analyzer | `detect_volume_spikes()` in volume_spikes.py | Already handles 20-day MA, threshold multiplier |
| Abnormal return event study | Custom AR calculator | `compute_abnormal_return()` in chart_computations.py | Already implements Brown & Warner 1985 market model |
| Idiosyncratic volatility | Custom residual calc | `compute_idiosyncratic_vol()` in chart_computations.py | Already computes beta, residual variance, annualization |
| Drop consolidation | Custom multi-day merge | `_consolidate_overlapping_drops()` in _market_display.py | Already handles weekend bridging, peak-to-trough |
| Drop enrichment | Custom 8-K/news cross-ref | `enrich_drops_from_8k()` + `enrich_drops_from_web()` in stock_drop_enrichment.py | Already maps item numbers to categories |

## Detailed Data Audit: Computed but NOT Displayed

### Fields on StockDropEvent computed but not surfaced as event card data:
| Field | Computed | Displayed | Gap |
|-------|----------|-----------|-----|
| `market_pct` | Yes (decompose_drop) | Yes (drops table Market column) | Already shown |
| `sector_pct` | Yes | Yes | Already shown |
| `company_pct` | Yes | Yes | Already shown |
| `abnormal_return_pct` | Yes (compute_abnormal_return) | Yes (AR column) | Already shown |
| `abnormal_return_t_stat` | Yes | Yes | Already shown |
| `market_model_alpha` | Yes | **NO** | Low priority, technical |
| `market_model_beta` | Yes | **NO** | Low priority, technical |
| `decay_weight` | Yes | Yes (Recency column) | Already shown |
| `decay_weighted_severity` | Yes | Yes | Already shown |
| `corrective_disclosure_type` | Yes | Yes (badge) | Already shown |
| `do_assessment` | Yes (enrichment) | Only in beta_report (stock_drop_catalyst.html.j2) | **GAP: Not in main market template** |
| `from_price` | Yes | Yes | Already shown |
| `volume` | Yes | Yes | Already shown |

### Fields on StockPerformance computed but not rendered:
| Field | Computed | Displayed | Gap |
|-------|----------|-----------|-----|
| `volume_spike_events` | Yes (detect_volume_spikes) | **NO** (only chart overlays) | **STOCK-07 gap** |
| `volume_spike_count` | Yes | **NO** | Count shown in chart header only |
| `idiosyncratic_vol` | Yes | Via volatility signal evidence only | **STOCK-08 gap -- not as dedicated card** |
| `ewma_vol_current` | Yes | Yes (via volatility signals) | Displayed |
| `vol_regime` | Yes | Yes | Displayed |
| `returns_1y_market/sector/company` | Yes | Yes (return attribution table) | Displayed |
| `mdd_ratio_1y/5y` | Yes | **NO** | **Not rendered anywhere** |
| `sector_mdd_1y/5y` | Yes | **NO** | **Not rendered** |
| `sector_vol_90d` | Yes | **NO** | **Not rendered** |
| `sector_beta` | Yes | **NO** | **Not rendered** |
| `beta_ratio` | Yes | **NO** | **Not rendered** |

### yfinance Data Acquired but NOT Rendered in Market Section:
| Data Key | Acquired | Rendered | Gap |
|----------|----------|----------|-----|
| `eps_trend` | Yes (market_client.py:210) | **NO** | **STOCK-06: EPS revision data** |
| `eps_revisions` | Yes (market_client.py:211) | **NO** | **STOCK-06: 7d/30d/90d revision counts** |
| `growth_estimates` | Yes (market_client.py:212) | Only in forward_risk_map | Not in market section |
| `analyst_price_targets` | Yes (market_client.py:176) | **NO** | **STOCK-06: target price range** |
| `earnings_dates` | Yes (market_client.py:173) | Chart overlays only | **STOCK-04: need for reaction table dates** |

### Templates That Exist but Are NOT Included in main market.html.j2:
| Template | In beta_report | In market.html.j2 | Action |
|----------|----------------|---------------------|--------|
| `stock_drop_catalyst.html.j2` | Yes (line 1257) | **NO** | Add to market.html.j2 |
| `earnings_history.html.j2` | Yes (line 1259) | **NO** | Add to market.html.j2 |
| `forward_estimates.html.j2` | Yes (line 1261) | **NO** | Add to market.html.j2 |
| `upgrades_downgrades.html.j2` | Yes (line 1263) | **NO** | Add to market.html.j2 |
| `news_articles.html.j2` | Yes (line 967) | **NO** | Add to market.html.j2 |
| `stock_performance_summary.html.j2` | **NO** | **NO** | Orphaned -- evaluate usefulness |

## Implementation Architecture per Requirement

### STOCK-01/02/03: Drop Attribution Event Cards
**What exists:**
- `StockDropEvent` model: 30+ fields including decomposition, AR, t-stat, trigger, D&O assessment
- `decompose_drop()`: market/sector/company split
- `stock_drop_enrichment.py`: 8-K + web search catalyst identification
- `_consolidate_overlapping_drops()`: multi-day merge
- `stock_drops.html.j2`: full table with all columns
- `stock_drop_catalyst.html.j2`: D&O assessment narrative (NOT included in main template)

**What needs changing:**
1. Include `stock_drop_catalyst.html.j2` in `market.html.j2` (1-line change)
2. Enhance drop event display to card format: each >10% drop gets a visual card with magnitude bar, attribution pie, catalyst, recovery timeline, and D&O theory one-liner
3. The D&O theory mapping already exists in `do_assessment` field. Ensure it populates for all >10% drops.

**Complexity:** LOW -- mostly template restructuring + include fix.

### STOCK-04/05: Earnings Reaction Table
**What exists:**
- `EarningsQuarterRecord`: has `stock_reaction_pct` (day-of only)
- `earnings_dates` from yfinance: has dates, EPS surprise
- `earnings_history` from yfinance: has epsActual, epsEstimate, epsDifference, surprisePercent
- `earnings_history.html.j2`: 4-quarter table (in beta_report only)
- `earnings_guidance.html.j2`: quarter-by-quarter table with Est EPS, Actual, Result, Miss Mag, Stock Rxn

**What needs building:**
1. **New fields on `EarningsQuarterRecord`:** `next_day_return_pct` and `week_return_pct` (both SourcedValue[float] | None)
2. **New extraction function** in `stages/extract/earnings_reactions.py`:
   - Input: `earnings_dates` (has dates), `history_1y` (has daily prices)
   - For each earnings date: look up price at T+0, T+1, T+5 (or nearest trading day)
   - Compute day-of, next-day, 1-week returns
   - Populate `EarningsQuarterRecord` with all three windows
3. **Revenue estimate vs actual:** yfinance `earnings_history` has EPS only. Revenue data is in `revenue_estimate` (forward only). For historical revenue beat/miss, would need quarterly income statement data.
4. **Earnings trust assessment narrative:** New function analyzing the correlation between beat/miss result and stock reaction direction. Pattern: "beat but stock fell" = market distrust.
5. **Template enhancement:** Modify `earnings_guidance.html.j2` to add next-day and 1-week return columns.

**Complexity:** MEDIUM -- new extraction logic for multi-window returns + trust narrative.

### STOCK-06: Analyst Consensus + EPS Revision Trends
**What exists:**
- `AnalystSentimentProfile`: coverage_count, consensus, recommendation_mean, target_price_mean/high/low, recent_upgrades/downgrades
- `recommendation_breakdown` context: strongBuy/buy/hold/sell/strongSell counts with bar chart
- `analyst_consensus.html.j2`: recommendation bar + consensus + upgrades/downgrades
- yfinance data acquired but unused: `eps_revisions` (7day/30day/90day up/down counts), `eps_trend` (current/7day/30day/60day/90day EPS estimates), `analyst_price_targets` (low/current/mean/high/number)

**What needs building:**
1. **New context builder function** `build_eps_revision_trends(state)` in `_market_acquired_data.py`:
   - Read `eps_revisions` from acquired_data.market_data
   - Format 7d/30d/90d revision counts (up/down) for display
   - Compute revision direction signal (net up vs net down)
2. **New context builder function** `build_analyst_targets(state)`:
   - Read `analyst_price_targets` from acquired_data.market_data
   - Format low/current/mean/high target prices
   - Compute upside/downside % from current price
3. **New template** `analyst_revisions.html.j2`:
   - EPS revision trend table: period (7d/30d/90d), revisions up, revisions down, net direction
   - Price target range card: low/mean/high with current price marker
4. **Wire into market.html.j2**

**Complexity:** LOW -- data already acquired, just needs context builder + template.

### STOCK-07: Volume Anomaly Table
**What exists:**
- `detect_volume_spikes()` in `volume_spikes.py`: returns list of {date, volume, avg_volume, volume_multiple, price_change_pct}
- `volume_spike_events` on `StockPerformance`: populated during extraction
- `render_volume_bars()` in `stock_chart_overlays.py`: draws red bars on charts
- NO tabular display exists

**What needs building:**
1. **New context builder function** `build_volume_anomalies(state)`:
   - Read `stock.volume_spike_events` from state
   - Cross-reference each spike date with 8-K filings (by date proximity, +/- 2 business days)
   - Cross-reference with news articles (from `acquired_data.market_data.news`)
   - Return table rows: date, volume, multiple, price change, catalyst found, event type
2. **New template** `volume_anomalies.html.j2`:
   - Table with: Date, Volume (with multiple annotation), Price Change, Event/Catalyst
   - Color-coded: spike + negative price change = red row; spike + positive = amber
3. **Include in market.html.j2** after stock_drops section

**Complexity:** MEDIUM -- cross-reference logic is new work.

### STOCK-08: Return Correlation Metrics Card
**What exists:**
- `compute_beta()`: company beta vs SPY
- `compute_sector_beta()`: sector ETF beta vs SPY
- `compute_idiosyncratic_vol()`: residual volatility after market model
- `compute_return_decomposition()`: 1Y and 5Y attribution
- `ChartData` stores: `company_beta`, `sector_beta`, `idiosyncratic_vol`
- Return attribution table in `stock_charts.html.j2`

**What needs building:**
1. **New context builder function** `build_correlation_metrics(state)`:
   - Compute: correlation coefficient (company vs SPY), correlation (company vs sector ETF)
   - R-squared from market model (beta^2 * var_market / var_company)
   - Idiosyncratic risk % = (1 - R^2) * 100
   - Already have beta and idio_vol; need R^2 computation
2. **New computation** in `chart_computations.py`:
   - `compute_r_squared(company_prices, spy_prices)` -> float
   - `compute_correlation(prices_a, prices_b)` -> float
3. **New template** `correlation_metrics.html.j2`:
   - Card layout with 4 key metrics: Correlation vs SPY, Correlation vs Sector, R-squared, Idiosyncratic Risk %
   - D&O interpretation: high idiosyncratic = harder for plaintiff to prove loss causation from market-wide factors; low R^2 = company-specific risk dominates
4. **Include in market.html.j2**

**Complexity:** LOW -- most math already exists, just needs R^2 and correlation additions.

## Common Pitfalls

### Pitfall 1: Orphaned Templates Not Getting Context Data
**What goes wrong:** Template is included in market.html.j2 but the context builder doesn't populate the keys it expects
**Why it happens:** beta_report.html.j2 uses a different context builder path than market.html.j2
**How to avoid:** Trace every template variable to its context builder. The main market section uses `extract_market()` from `market.py`. All new data must flow through that function.
**Warning signs:** Template renders blank sections or shows "N/A" for everything

### Pitfall 2: Missing safe_float() on yfinance Data
**What goes wrong:** `float()` crashes on "N/A", None, or concatenated junk strings from yfinance
**Why it happens:** yfinance returns inconsistent types across data categories
**How to avoid:** Use `safe_float()` from `stages/render/formatters.py` for ALL numeric conversions
**Warning signs:** TypeError or ValueError in context builders during render

### Pitfall 3: earnings_dates Date Format Inconsistency
**What goes wrong:** yfinance earnings_dates uses timestamps that may be epoch integers, datetime objects, or strings depending on yfinance version
**Why it happens:** yfinance's `get_earnings_dates()` has inconsistent return format
**How to avoid:** Use robust date parsing that handles all three formats (see `_extract_next_earnings()` pattern in market.py)
**Warning signs:** Empty earnings reaction table even when earnings_dates data exists

### Pitfall 4: Multi-Day Drop Double-Counting
**What goes wrong:** A 5-day selloff appears as 5 separate "events" in the event cards
**Why it happens:** Existing `_consolidate_overlapping_drops()` merges overlapping windows but the merge gap is 5 calendar days -- holidays could create gaps
**How to avoid:** Verify consolidation works correctly for the ticker being tested. Inspect both the consolidated list and the raw list lengths.
**Warning signs:** Same date range appearing in multiple event cards

### Pitfall 5: Template Not Included After Creating It
**What goes wrong:** New template file created but never added to market.html.j2 include list
**Why it happens:** Easy to forget the include step after building the template
**How to avoid:** Checklist: (1) Create context builder function, (2) Wire into extract_market(), (3) Create template, (4) Add include to market.html.j2
**Warning signs:** Template file exists but content never appears in output

### Pitfall 6: Breaking Existing Earnings Guidance Display
**What goes wrong:** Modifying earnings_guidance.html.j2 breaks the existing quarter-by-quarter table
**Why it happens:** Template has complex conditional logic for optional columns (miss_mag, stock_reaction)
**How to avoid:** ADD new columns, don't restructure existing ones. Use the same `ns_qtr.show_*` pattern for new optional columns.
**Warning signs:** Existing test_market_templates.py tests fail

## Code Examples

### Computing Earnings Multi-Window Returns
```python
# Pattern: use earnings_dates for timing, history_1y for price lookup
def compute_earnings_reactions(
    earnings_dates: dict[str, Any],
    history_1y: dict[str, Any],
) -> list[dict[str, Any]]:
    """Compute day-of, next-day, 1-week returns for each earnings date."""
    closes = _extract_column(history_1y, "Close")  # from volume_spikes.py pattern
    dates = _extract_dates(history_1y)

    results = []
    for earnings_date in earnings_dates:
        idx = _find_nearest_date_idx(dates, earnings_date)
        if idx is None:
            continue
        # Day-of return: close[idx] vs close[idx-1]
        day_of = _pct_change(closes, idx - 1, idx)
        # Next-day: close[idx+1] vs close[idx-1]
        next_day = _pct_change(closes, idx - 1, min(idx + 1, len(closes) - 1))
        # 1-week: close[idx+5] vs close[idx-1]
        week = _pct_change(closes, idx - 1, min(idx + 5, len(closes) - 1))
        results.append({
            "date": earnings_date,
            "day_of_return": day_of,
            "next_day_return": next_day,
            "week_return": week,
        })
    return results
```

### Building EPS Revision Context
```python
# Pattern: follows build_forward_estimates() in _market_acquired_data.py
def build_eps_revision_trends(state: AnalysisState) -> dict[str, Any]:
    """Build EPS revision trend display from yfinance eps_revisions data."""
    md = _get_md_dict(state)
    revisions = md.get("eps_revisions", {})
    if not revisions or not isinstance(revisions, dict):
        return {}

    # eps_revisions has: upLast7days, upLast30days, downLast7days, downLast30days
    # per period (0q, +1q, 0y, +1y)
    periods = revisions.get("period", [])
    up_7 = revisions.get("upLast7days", [])
    up_30 = revisions.get("upLast30days", [])
    down_7 = revisions.get("downLast7days", [])
    down_30 = revisions.get("downLast30days", [])
    # ... build rows ...
    return {"eps_revisions": rows} if rows else {}
```

### Computing Correlation and R-Squared
```python
# Pattern: extends chart_computations.py
def compute_correlation(
    prices_a: list[float], prices_b: list[float],
) -> float | None:
    """Compute Pearson correlation of daily returns."""
    returns_a = compute_daily_returns(prices_a)
    returns_b = compute_daily_returns(prices_b)
    n = min(len(returns_a), len(returns_b))
    if n < 30:
        return None
    ra, rb = returns_a[:n], returns_b[:n]
    mean_a = sum(ra) / n
    mean_b = sum(rb) / n
    cov = sum((ra[i] - mean_a) * (rb[i] - mean_b) for i in range(n)) / n
    std_a = math.sqrt(sum((x - mean_a) ** 2 for x in ra) / n)
    std_b = math.sqrt(sum((x - mean_b) ** 2 for x in rb) / n)
    if std_a < 1e-15 or std_b < 1e-15:
        return None
    return cov / (std_a * std_b)

def compute_r_squared(
    company_prices: list[float], spy_prices: list[float],
) -> float | None:
    """R-squared from market model regression."""
    corr = compute_correlation(company_prices, spy_prices)
    if corr is None:
        return None
    return corr ** 2
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Volume spikes as chart overlays only | Phase 133: tabular display with event cross-ref | This phase | STOCK-07 |
| Single earnings reaction window | Multi-window (day-of, next-day, 1-week) | This phase | STOCK-04 |
| Analyst consensus as single label | Breakdown bar + revision trends + targets | This phase | STOCK-06 |
| Drop table without D&O theory | Event cards with litigation theory mapping | This phase | STOCK-01/02 |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pyproject.toml [tool.pytest.ini_options] |
| Quick run command | `uv run pytest tests/stages/render/test_market_templates.py tests/stages/render/test_market_context_drops.py -x -q` |
| Full suite command | `uv run pytest tests/ -x -q` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| STOCK-01 | >10% drops have M/S/C attribution | unit | `uv run pytest tests/stages/render/test_market_context_drops.py -x -q` | Yes |
| STOCK-02 | Drops cross-referenced with 8-K | unit | `uv run pytest tests/stages/render/test_stock_catalyst_context.py -x -q` | Yes |
| STOCK-03 | Multi-day consolidation | unit | `uv run pytest tests/stages/render/test_market_context_drops.py -x -q -k consolidate` | Yes |
| STOCK-04 | Earnings reaction multi-window | unit | `uv run pytest tests/stages/extract/test_earnings_reactions.py -x -q` | Wave 0 |
| STOCK-05 | Earnings trust narrative | unit | `uv run pytest tests/stages/render/test_earnings_trust.py -x -q` | Wave 0 |
| STOCK-06 | Analyst revisions rendered | unit | `uv run pytest tests/stages/render/test_market_templates.py -x -q -k analyst` | Partial |
| STOCK-07 | Volume anomaly table | unit | `uv run pytest tests/stages/render/test_volume_anomalies.py -x -q` | Wave 0 |
| STOCK-08 | Correlation metrics card | unit | `uv run pytest tests/stages/render/test_correlation_metrics.py -x -q` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/stages/render/test_market_templates.py tests/stages/render/test_market_context_drops.py -x -q`
- **Per wave merge:** `uv run pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/stages/extract/test_earnings_reactions.py` -- covers STOCK-04
- [ ] `tests/stages/render/test_earnings_trust.py` -- covers STOCK-05
- [ ] `tests/stages/render/test_volume_anomalies.py` -- covers STOCK-07
- [ ] `tests/stages/render/test_correlation_metrics.py` -- covers STOCK-08

## Open Questions

1. **Revenue estimate vs actual for earnings reaction table**
   - What we know: yfinance `earnings_history` has EPS only. `revenue_estimate` has forward estimates but not historical actuals.
   - What's unclear: Whether we can get historical quarterly revenue beat/miss from the quarterly income statement data that's already acquired
   - Recommendation: For Phase 133, show EPS columns only. Revenue beat/miss requires cross-referencing quarterly income statement dates with estimate periods -- defer to future enhancement if needed.

2. **Analyst price targets availability**
   - What we know: `_safe_get_analyst_targets()` is called but the data format depends on yfinance version
   - What's unclear: Whether the returned dict consistently has low/current/mean/high fields
   - Recommendation: Build context builder with defensive coding (safe_float for all values). If data is empty, section simply won't render.

3. **30d/90d EPS revision window data granularity**
   - What we know: yfinance `eps_revisions` has upLast7days, upLast30days, downLast7days, downLast30days
   - What's unclear: Whether 90-day revision data is available (yfinance may only have 7d and 30d)
   - Recommendation: Display what's available. If 90d not in data, show 7d and 30d only and note "90-day revision data not available."

## Sources

### Primary (HIGH confidence)
- Codebase inspection: All source files read directly from `/Users/gorlin/projects/UW/do-uw/src/`
- Model definitions: `market_events.py` (719 lines), `market.py` (432 lines) -- field-by-field audit
- Context builders: `market.py`, `_market_display.py`, `_market_acquired_data.py`, `market_evaluative.py` -- function-by-function audit
- Templates: all 19 files in `sections/market/` -- include chain traced
- Acquisition: `market_client.py` -- all yfinance data keys documented

### Secondary (MEDIUM confidence)
- yfinance data format assumptions based on existing parser code patterns in `_market_acquired_data.py`

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, all existing Python/Jinja2/Pydantic
- Architecture: HIGH -- follows established context builder + template pattern
- Pitfalls: HIGH -- based on observed code patterns and existing workarounds
- Data availability: MEDIUM -- yfinance data format for eps_revisions/analyst_price_targets assumed from field names

**Research date:** 2026-03-26
**Valid until:** 2026-04-26 (stable -- no external dependency changes expected)
