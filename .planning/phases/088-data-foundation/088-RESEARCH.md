# Phase 88: Data Foundation - Research

**Researched:** 2026-03-08
**Domain:** Stock data acquisition, return decomposition, maximum drawdown analysis
**Confidence:** HIGH

## Summary

Phase 88 extends the stock analysis pipeline in three ways: (1) expanding the daily data lookback from 1 year to 2 years, (2) adding 3-component return decomposition (market + sector + company-specific), and (3) computing peer-relative MDD ratios. All three build on existing infrastructure -- yfinance acquisition in `market_client.py`, extraction in `stock_performance.py`, and charting in `stages/render/charts/`.

The current system already acquires SPY and sector ETF data alongside company data, computes idiosyncratic volatility via a market model, and renders drawdown charts with sector ETF comparison. The 2-year lookback requires adding `history_2y` keys to market_client alongside the existing `history_1y`/`history_5y` keys. Return decomposition requires computing beta (company vs SPY) and sector beta (ETF vs SPY), then attributing returns. MDD ratio is a simple division of existing computations applied to sector ETF data.

**Primary recommendation:** Add a `history_2y` acquisition key, extend all 1Y-based metrics to optionally use 2Y data, add return decomposition fields to StockPerformance, and add MDD ratio to the drawdown chart stats -- all following existing patterns in the codebase.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| STOCK-07 | Daily stock data acquisition extended from 1-year to 2-year lookback for all metrics | Add `history_2y` key in market_client.py; update extraction to use 2Y data for drops, volatility, returns |
| STOCK-01 | Every stock return decomposed into 3 components: market + sector + company-specific residual | Use existing beta computation infrastructure in chart_computations.py; add decomposition fields to StockPerformance model |
| STOCK-03 | Peer-relative MDD ratio (company MDD / sector ETF MDD) for both 1Y and 5Y periods | Compute sector ETF MDD using existing `compute_max_drawdown()` and `compute_drawdown_series()`; store ratio on StockPerformance |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| yfinance | current | Stock price history, company info, sector ETF data | Already used; `period="2y"` is a valid parameter |
| Pydantic v2 | 2.x | Data models (StockPerformance, SourcedValue) | Project standard |
| matplotlib | current | Chart rendering | Already used for all stock charts |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| math (stdlib) | 3.12 | Beta, volatility, drawdown calculations | All computations are pure Python (no numpy) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pure Python math | numpy/scipy | Project explicitly uses pure Python for all chart computations -- no dependency needed |

## Architecture Patterns

### Current Data Flow (CRITICAL to understand)

```
ACQUIRE                     EXTRACT                      RENDER
market_client.py            stock_performance.py         charts/
  history_1y  ──────>  _compute_performance_metrics() ──> stock_chart_data.py
  history_5y  ──────>  _compute_sector_derived_metrics()  chart_computations.py
  sector_history_1y ─> find_single_day_drops()            drawdown_chart.py
  sector_history_5y ─> find_multi_day_drops()             volatility_chart.py
  spy_history_1y ───>  compute_sector_comparison()
  spy_history_5y ───>
  info ─────────────>
```

### Key: market_data dict keys
The system uses a flat dict (`acquired.market_data`) with string keys:
- `history_1y`, `history_5y` -- company price history
- `sector_history_1y`, `sector_history_5y` -- sector ETF history
- `spy_history_1y`, `spy_history_5y` -- S&P 500 history
- `sector_etf` -- sector ETF ticker string
- `info` -- yfinance company info dict

### Pattern: Adding new data to the pipeline
1. Add acquisition in `market_client.py` (`_collect_yfinance_data`)
2. Add model fields to `models/market.py` (StockPerformance)
3. Add extraction logic in `stock_performance.py`
4. Add chart data extraction in `stock_chart_data.py` if chart-relevant
5. Update chart rendering if visual changes needed
6. Update template if new display elements needed

### Recommended Changes Structure

```
src/do_uw/
├── stages/acquire/clients/market_client.py  # Add history_2y keys
├── models/market.py                          # Add decomposition + MDD ratio fields
├── stages/extract/stock_performance.py       # Use 2Y data, compute decomposition + MDD ratio
├── stages/render/charts/chart_computations.py # Add return_decomposition() helper
├── stages/render/charts/stock_chart_data.py  # Support 2Y period in extract_chart_data
├── stages/render/charts/drawdown_chart.py    # Add MDD ratio to stats header
└── templates/html/sections/market/           # Display decomposition table + MDD ratio
```

### Anti-Patterns to Avoid
- **Breaking 1Y chart rendering**: The 1Y charts must continue to work. The 2Y data is an extension, not a replacement. Charts still show 1Y and 5Y -- the 2Y data feeds metric computation (drops, volatility).
- **Duplicating beta computation**: `compute_beta()` already exists in `chart_computations.py`. Reuse it for return decomposition.
- **Hardcoding sector ETF tickers**: Sector ETF resolution already goes through `_resolve_sector_etf()` -> `brain/config/sectors.json`. Use the same mechanism.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Beta computation | Custom OLS regression | `chart_computations.compute_beta()` | Already pure Python, tested, handles edge cases |
| Sector ETF resolution | Hardcoded ETF map | `_resolve_sector_etf()` in market_client.py | Uses brain/config/sectors.json, covers 11 sectors |
| Max drawdown | New MDD function | `stock_performance.compute_max_drawdown()` | Already computes MDD from price list |
| Daily returns | New return calculator | `chart_computations.compute_daily_returns()` | Already exists, handles zero prices |
| Price extraction | Custom parser | `stock_drops.get_close_prices()` / `get_dates()` | Handles NaN, None, type coercion |

## Common Pitfalls

### Pitfall 1: yfinance `period="2y"` data reliability
**What goes wrong:** yfinance may return incomplete data for 2Y requests, especially for recently listed companies or foreign tickers.
**Why it happens:** Yahoo Finance API is unstable; some tickers have incomplete history.
**How to avoid:** Already handled by the pattern -- `_safe_get_history()` returns empty dict on failure, and all downstream code checks for empty data gracefully. Just add `history_2y` using the same `_safe_get_history(yf_ticker, "2y")` call.
**Warning signs:** `len(prices_2y) < 252` (less than one year of data in a 2Y request).

### Pitfall 2: Return decomposition requires aligned time series
**What goes wrong:** Company, SPY, and sector ETF may have different trading days (holidays, halts).
**Why it happens:** Different exchanges, stock-specific halts.
**How to avoid:** Use date-aligned returns. The existing `compute_beta()` function takes two return series and uses `min(len(rx), len(rm))` for alignment. The decomposition should work similarly -- align by taking the common date range.
**Warning signs:** Company and SPY return series have significantly different lengths.

### Pitfall 3: MDD ratio division by zero
**What goes wrong:** Sector ETF MDD could be 0 (no drawdown in period) or very small.
**Why it happens:** Bull market periods, stable sector ETFs.
**How to avoid:** Guard against zero/near-zero sector MDD. If sector MDD is >-0.5%, report ratio as N/A or 1.0.
**Warning signs:** `sector_mdd >= -0.5` (essentially no drawdown).

### Pitfall 4: Cache invalidation with new data keys
**What goes wrong:** Adding `history_2y` to market_client but old cached data lacks it.
**Why it happens:** Cache key is `yfinance:{ticker}:market:{today}` -- daily invalidation handles this for fresh runs, but cached runs within the same day won't re-acquire.
**How to avoid:** The `--fresh` flag bypasses cache. For first deployment, user should use `--fresh`. The daily cache key rotation handles subsequent runs.
**Warning signs:** `history_2y` is missing from `market_data` after a non-fresh run.

### Pitfall 5: 2Y data doubling state.json size
**What goes wrong:** 2Y of daily data is ~500 data points per series (company + sector + SPY = ~1500 additional points). State JSON grows.
**Why it happens:** History dicts contain Open, High, Low, Close, Volume, Dividends, Stock Splits columns.
**How to avoid:** This is manageable -- the existing 5Y data already has ~1250 points per series. 2Y adds less than that. State.json files are already 50-100MB for full runs. Not a practical concern.

### Pitfall 6: Breaking drop detection window
**What goes wrong:** Stock drops are currently detected from `history_1y`. Switching to `history_2y` changes the drop count and may surface old drops that aren't relevant.
**Why it happens:** More data = more potential drops.
**How to avoid:** STOCK-07 says "2-year lookback for all metrics (drops, volatility, returns)". This is intentional -- the requirement explicitly includes drops. But the `StockDropAnalysis.analysis_period_months` field should be updated from 18 to 24. The template and scoring should handle more drops gracefully.

## Code Examples

### 1. Adding 2Y acquisition in market_client.py

```python
# In _collect_yfinance_data(), after existing history_1y:
# Price history: 2 year daily (STOCK-07).
result["history_2y"] = _safe_get_history(yf_ticker, "2y")

# Also acquire sector ETF and SPY 2Y:
result["sector_history_2y"] = _safe_get_history(etf_ticker, "2y")
result["spy_history_2y"] = _safe_get_history(spy, "2y")
```

### 2. Return decomposition computation

```python
def compute_return_decomposition(
    company_prices: list[float],
    spy_prices: list[float],
    sector_prices: list[float],
) -> dict[str, float] | None:
    """Decompose total return into market + sector + company-specific.

    R_total = R_market + (R_sector - R_market) + (R_company - R_sector)
            = market_contribution + sector_contribution + company_residual

    This is a simple return attribution, not a factor model.
    The three components sum exactly to R_total.
    """
    if not company_prices or not spy_prices or not sector_prices:
        return None
    if len(company_prices) < 2 or len(spy_prices) < 2 or len(sector_prices) < 2:
        return None

    r_company = (company_prices[-1] - company_prices[0]) / company_prices[0] * 100.0
    r_market = (spy_prices[-1] - spy_prices[0]) / spy_prices[0] * 100.0
    r_sector = (sector_prices[-1] - sector_prices[0]) / sector_prices[0] * 100.0

    return {
        "total_return": round(r_company, 2),
        "market_contribution": round(r_market, 2),
        "sector_contribution": round(r_sector - r_market, 2),
        "company_residual": round(r_company - r_sector, 2),
    }
```

### 3. MDD ratio computation

```python
def compute_mdd_ratio(
    company_prices: list[float],
    sector_prices: list[float],
) -> float | None:
    """Compute company MDD / sector ETF MDD ratio.

    A ratio > 1.0 means the company drew down more than its sector.
    A ratio of 2.0 means the company's worst drawdown was twice the sector's.
    """
    company_mdd = compute_max_drawdown(company_prices)
    sector_mdd = compute_max_drawdown(sector_prices)

    if company_mdd is None or sector_mdd is None:
        return None
    if sector_mdd >= -0.5:
        # Sector had no meaningful drawdown
        return None

    return round(company_mdd / sector_mdd, 2)
```

### 4. New StockPerformance model fields

```python
# Return decomposition fields
returns_1y_market: SourcedValue[float] | None = Field(
    default=None,
    description="1Y return: market (SPY) contribution component",
)
returns_1y_sector: SourcedValue[float] | None = Field(
    default=None,
    description="1Y return: sector contribution component (sector ETF return - SPY return)",
)
returns_1y_company: SourcedValue[float] | None = Field(
    default=None,
    description="1Y return: company-specific residual (company return - sector ETF return)",
)
returns_5y_market: SourcedValue[float] | None = Field(
    default=None,
    description="5Y return: market (SPY) contribution component",
)
returns_5y_sector: SourcedValue[float] | None = Field(
    default=None,
    description="5Y return: sector contribution component",
)
returns_5y_company: SourcedValue[float] | None = Field(
    default=None,
    description="5Y return: company-specific residual",
)

# MDD ratio fields
mdd_ratio_1y: SourcedValue[float] | None = Field(
    default=None,
    description="Company MDD / sector ETF MDD ratio for 1Y (>1 = worse than sector)",
)
mdd_ratio_5y: SourcedValue[float] | None = Field(
    default=None,
    description="Company MDD / sector ETF MDD ratio for 5Y (>1 = worse than sector)",
)
max_drawdown_5y: SourcedValue[float] | None = Field(
    default=None,
    description="Maximum peak-to-trough drawdown in trailing 5 years",
)
sector_mdd_1y: SourcedValue[float] | None = Field(
    default=None,
    description="Sector ETF maximum drawdown over trailing 1 year",
)
sector_mdd_5y: SourcedValue[float] | None = Field(
    default=None,
    description="Sector ETF maximum drawdown over trailing 5 years",
)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 1Y daily data only | 1Y + 5Y daily data | Existing | 5Y used for charts, 1Y for metrics |
| Simple alpha (company - sector) | 3-component decomposition | Phase 88 | Separates market from sector from company |
| MDD absolute only | MDD + peer-relative ratio | Phase 88 | Contextualizes drawdown vs sector norm |
| yfinance period="1y" | yfinance period="2y" | Phase 88 | More data for drop detection and volatility |

## Open Questions

1. **Should 2Y data replace 1Y data or supplement it?**
   - What we know: STOCK-07 says "extended from 1-year to 2-year lookback for all metrics". The success criteria says "acquires 2 years of daily stock data (not 1 year)".
   - What's unclear: Whether `history_1y` should still be acquired separately, or if the 2Y data subsumes it.
   - Recommendation: Keep `history_1y` for backward compatibility (chart rendering uses it). Add `history_2y` as the new primary source for metric computation. The 1Y chart can simply use the last 252 points of the 2Y data, or continue using `history_1y` directly. Safest to keep both.

2. **Where to display return decomposition?**
   - What we know: Success criteria says "stock analysis section shows every major return period broken into three labeled components".
   - What's unclear: Whether this goes in existing chart stats headers, a new table, or both.
   - Recommendation: Add a return decomposition table below the stock charts, showing 1Y and 5Y decomposition side by side. Also add to the chart stats headers if space allows. The existing `compute_chart_stats()` in `stock_chart_data.py` already shows total_return_pct and sector_return_pct -- extend with decomposition.

3. **Should all downstream metrics switch from 1Y to 2Y immediately?**
   - What we know: "All downstream stock metrics (drops, volatility, scoring) use the 2-year daily dataset as their input" is a success criterion.
   - What's unclear: Whether this breaks scoring expectations (more drops = potentially different scores).
   - Recommendation: Switch to 2Y for drops and volatility computation. Update `analysis_period_months` from 18 to 24. Existing scoring thresholds should handle this gracefully since they're based on drop magnitude, not count.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pyproject.toml |
| Quick run command | `uv run pytest tests/test_stock_performance.py -x` |
| Full suite command | `uv run pytest` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| STOCK-07 | 2Y data acquired and used for metrics | unit | `uv run pytest tests/stages/acquire/test_market_client_2y.py -x` | No -- Wave 0 |
| STOCK-01 | Return decomposition sums to total | unit | `uv run pytest tests/test_return_decomposition.py -x` | No -- Wave 0 |
| STOCK-03 | MDD ratio computed for 1Y and 5Y | unit | `uv run pytest tests/test_mdd_ratio.py -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/test_stock_performance.py tests/stages/acquire/test_market_client_etf.py -x`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/stages/acquire/test_market_client_2y.py` -- verifies 2Y keys acquired
- [ ] `tests/test_return_decomposition.py` -- verifies 3-component decomposition sums to total
- [ ] `tests/test_mdd_ratio.py` -- verifies MDD ratio computation, handles zero sector MDD

## Sources

### Primary (HIGH confidence)
- Codebase analysis: `src/do_uw/stages/acquire/clients/market_client.py` -- current acquisition logic, yfinance `period` parameter usage
- Codebase analysis: `src/do_uw/stages/extract/stock_performance.py` -- current metric computation flow
- Codebase analysis: `src/do_uw/stages/render/charts/chart_computations.py` -- existing beta, volatility, drawdown functions
- Codebase analysis: `src/do_uw/stages/render/charts/stock_chart_data.py` -- chart data extraction, key naming conventions
- Codebase analysis: `src/do_uw/models/market.py` -- StockPerformance model structure
- Codebase analysis: `src/do_uw/stages/render/charts/drawdown_chart.py` -- existing drawdown chart with sector comparison
- Project research: `.planning/research/stock-performance-do-research.md` -- D&O underwriting context, MDD methodology, event study standards

### Secondary (MEDIUM confidence)
- yfinance API: `period` parameter accepts "2y" as valid value (verified from yfinance documentation and codebase usage of "1y" and "5y")
- Return decomposition formula: Standard Brinson attribution (R_total = R_market + R_sector_excess + R_company_residual) -- well-established quantitative finance methodology

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all libraries already in use, no new dependencies
- Architecture: HIGH - all changes follow existing patterns visible in codebase
- Pitfalls: HIGH - identified from actual code inspection of edge cases

**Research date:** 2026-03-08
**Valid until:** 2026-04-08 (stable domain, no fast-moving dependencies)
