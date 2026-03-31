# Phase 37: Stock Charts, Price History & Drop Analysis - Research

**Researched:** 2026-02-21
**Domain:** matplotlib charting, yfinance data acquisition, multi-format rendering pipeline
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Chart type:** Area chart with filled area under price line
- **Price axis:** Dual axis -- company actual dollar price on left axis, sector ETF/S&P indexed on right axis
- **Color scheme:** Bloomberg Terminal dark theme -- dark background, bright colored lines
- **Reference model:** Bloomberg Terminal GP (graph) function aesthetic
- **Area fill:** Green fill when price is above starting level, red fill when below -- clear directional risk signal
- **Stats header:** Key metrics displayed in header bar above chart (current price, 52W H/L, total return, company vs sector return, alpha)
- **Drop annotations:** Red markers/dots on chart at drop dates, PLUS detailed drop table below each chart
- **Full detail per drop event:** Date, drop %, recovery time (trading days to recover), trigger event, company-specific vs market-wide label, source link (8-K URL or news article)
- **Severity tiers:** 5-10% drops shown as yellow/notable, 10%+ drops shown as red/critical
- **Unknown triggers:** Best-effort hypothesis BUT mark as "Unconfirmed -- Requires Investigation"
- **Market-wide events:** Tag drops correlating with S&P 500/sector drops >3% on same day as "Market-Wide Event"
- **Recovery time:** Trading days until stock recovered to pre-drop level
- **Event grouping:** Group consecutive daily drops into single events with cumulative drop percentage
- **Summary line:** Brief overview before table
- **Source links:** Each trigger explanation includes link to source
- **5Y chart density:** Weekly data aggregation, only show drops >10% or cumulative >15%
- **1Y chart:** Full daily data, all 5%+ drops annotated
- **Two overlays:** Both sector ETF (dashed) AND S&P 500 (dotted) on same chart
- **ETF selection:** Auto-map from SIC/GICS sector to standard sector ETF
- **Divergence bands:** Shade gap between company and sector lines when >10% divergence
- **Performance stats:** Company return, sector return, alpha in chart header
- **Image format:** PNG for all formats
- **Chart size:** Full page width, ~400px tall
- **Placement:** Section 2: Market Data (NOTE: this is Section 4 in current code)
- **Caching:** Cache chart images keyed by hash of price data

### Claude's Discretion
- Exact Bloomberg dark theme hex colors
- Chart library choice (matplotlib, plotly, etc.)
- Legend placement and typography
- Handling companies with no sector ETF
- Divergence band opacity and styling
- Chart DPI/resolution

### Deferred Ideas (OUT OF SCOPE)
(None specified)
</user_constraints>

## Summary

Phase 37 requires a complete overhaul of the stock chart pipeline. The existing chart code (`stock_charts.py`, 410 lines) is fundamentally broken due to a **key mismatch**: it reads `market_data["price_history"]` but acquisition stores data at `market_data["history_1y"]`/`market_data["history_5y"]`. The chart visual style must change from the current white-background indexed-to-100 line chart to a Bloomberg Terminal dark theme with dual-axis area charts, conditional green/red fills, sector ETF + S&P 500 overlays, and annotated drop events.

Beyond the chart rewrite, this phase requires **new data acquisition** (sector ETF and S&P 500 price histories via yfinance), **enhanced drop analysis** (recovery time calculation, event grouping, market-wide event tagging), a **chart generation + caching pipeline** that saves PNG files to disk for all three output formats, and **drop detail tables** with full event metadata below each chart.

**Primary recommendation:** Use matplotlib (already a dependency at >=3.9.0) with `dark_background` style sheet and custom Bloomberg-inspired colors. Rewrite `stock_charts.py` as a new module. Add sector ETF + SPY acquisition to `market_client.py`. Build a chart generation step in `RenderStage.run()` that saves PNGs to a `chart_dir` before calling any renderer.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| matplotlib | >=3.9.0 | Chart rendering | Already in project, `dark_background` style built-in, `fill_between` for area charts, `twinx()` for dual axes |
| yfinance | >=1.1.0 | ETF + SPY data acquisition | Already used for all market data, supports `yf.download()` for multiple tickers |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| hashlib (stdlib) | n/a | Chart cache key generation | Hash price data arrays to detect cache invalidation |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| matplotlib | plotly (already in deps) | plotly produces interactive HTML charts but PNG export requires kaleido dependency; matplotlib is simpler for static PNG charts in Word/PDF; matplotlib is already used for all other charts in the project |

**Recommendation: matplotlib.** The project already uses matplotlib for radar, ownership, timeline, and the broken stock charts. Using plotly would introduce a second chart styling system. matplotlib's `dark_background` style + `fill_between` + `twinx()` + `axvspan` provide everything needed for the Bloomberg dark theme with conditional fills, dual axes, and divergence bands.

## Architecture Patterns

### Current Codebase Structure (files that need changes)
```
src/do_uw/
  stages/
    acquire/
      clients/
        market_client.py          # ADD: sector ETF + SPY history acquisition
    extract/
      stock_performance.py        # MODIFY: add recovery time, event grouping
      stock_drops.py              # MODIFY: add market-wide event tagging
    render/
      __init__.py                 # MODIFY: add chart generation + chart_dir flow
      charts/
        stock_charts.py           # REWRITE: Bloomberg dark theme, dual axis, area fills
        stock_chart_data.py       # NEW: data extraction layer (split from charts)
      chart_helpers.py            # MODIFY: add save_chart_to_disk helper
      sections/
        sect4_market.py           # MODIFY: add drop detail table
        sect4_market_events.py    # MODIFY: enhanced drop event rendering
      design_system.py            # MODIFY: add Bloomberg dark theme colors
  templates/
    markdown/worksheet.md.j2      # MODIFY: drop table, chart references
    html/sections/market.html.j2  # MODIFY: drop table, chart references
```

### Pattern 1: Data Key Mismatch Fix
**What:** The chart code reads `market_data["price_history"]` but acquisition stores as `market_data["history_1y"]`/`market_data["history_5y"]`. The history data is a dict with keys `Close`, `Date`, `Open`, `High`, `Low`, `Volume` (column-oriented lists from `_dataframe_to_dict()`).
**Current broken code (stock_charts.py lines 148-160):**
```python
# BROKEN: reads non-existent key
price_history: Any = market_data.get("price_history", {})
prices_raw: Any = price_history.get(period, price_history.get("prices", []))
```
**What it should read:**
```python
# CORRECT: use actual keys from market_client.py
key = "history_1y" if period == "1Y" else "history_5y"
history: dict[str, Any] = market_data.get(key, {})
# History is column-oriented: {"Close": [...], "Date": [...], ...}
```
**The extraction layer already handles this correctly** in `stock_performance.py` line 295-298:
```python
raw_1y = market_data.get("history_1y", {})
raw_5y = market_data.get("history_5y", {})
```

### Pattern 2: Chart Generation + Disk Save Flow
**What:** Currently charts are generated inline as `BytesIO` and only embedded in Word docs. PDF/HTML renderers expect `chart_dir` with saved PNG files but `chart_dir` is always `None`.
**Fix:** Add a chart generation step in `RenderStage.run()` that:
1. Creates a temp `chart_dir` (e.g., `output/TICKER/charts/`)
2. Calls each chart generator, gets `BytesIO`
3. Writes BytesIO to `chart_dir/stock_1y.png`, `stock_5y.png`, etc.
4. Passes `chart_dir` to all three renderers
5. Word renderer continues using BytesIO (or reads from disk)
6. PDF/HTML renderers read from `chart_dir` as base64

**Expected `chart_dir` filenames** (from `pdf_renderer.py` `_load_chart_images`):
```python
chart_files = {
    "stock_1y": "stock_1y.png",
    "stock_5y": "stock_5y.png",
    "radar": "radar.png",
    "ownership": "ownership.png",
    "timeline": "timeline.png",
}
```

### Pattern 3: Dual-Axis Area Chart with Bloomberg Theme
**What:** Company price on left Y-axis (dollars), sector ETF + S&P 500 on right Y-axis (indexed to 100). Dark background, green/red conditional fill.
**Implementation approach:**
```python
plt.style.use('dark_background')
fig, ax1 = plt.subplots(figsize=(10, 5), dpi=200)
ax2 = ax1.twinx()

# Left axis: company dollar price with green/red area fill
base_price = prices[0]
ax1.fill_between(dates, prices, base_price,
    where=[p >= base_price for p in prices],
    color='#00FF88', alpha=0.3, interpolate=True)
ax1.fill_between(dates, prices, base_price,
    where=[p < base_price for p in prices],
    color='#FF4444', alpha=0.3, interpolate=True)
ax1.plot(dates, prices, color='#00FF88', linewidth=1.5)

# Right axis: sector ETF and S&P 500 indexed
ax2.plot(etf_dates, etf_indexed, '--', color='#FFD700', linewidth=1)
ax2.plot(spy_dates, spy_indexed, ':', color='#87CEEB', linewidth=1)
```

### Pattern 4: Sector ETF + SPY Acquisition
**What:** Add sector ETF and S&P 500 (SPY) history to market data acquisition.
**Where:** `market_client.py` -- add to `_collect_yfinance_data()`:
```python
# Sector ETF history (determined from sectors.json via sector code)
sector_etf = _get_sector_etf_ticker(info)
if sector_etf:
    result["sector_etf"] = sector_etf
    result["sector_history_1y"] = _safe_get_history(yf.Ticker(sector_etf), "1y")
    result["sector_history_5y"] = _safe_get_history(yf.Ticker(sector_etf), "5y")

# S&P 500 benchmark
result["spy_history_1y"] = _safe_get_history(yf.Ticker("SPY"), "1y")
result["spy_history_5y"] = _safe_get_history(yf.Ticker("SPY"), "5y")
```

### Pattern 5: Recovery Time Calculation
**What:** For each drop event, count trading days until stock recovered to pre-drop level.
**Algorithm:**
```python
def compute_recovery_days(
    prices: list[float], dates: list[str], drop_idx: int
) -> int | None:
    """Count trading days from drop to recovery of pre-drop level."""
    pre_drop_price = prices[drop_idx - 1]
    for i in range(drop_idx + 1, len(prices)):
        if prices[i] >= pre_drop_price:
            return i - drop_idx
    return None  # Never recovered in analysis period
```

### Pattern 6: Event Grouping (Consecutive Drops)
**What:** Group consecutive daily drops into single events with cumulative drop %.
**Algorithm:** If day N has a drop and day N+1 also has a drop, merge them into one event. The cumulative drop is the total decline from the pre-event price to the post-event price. The event date is the first day. Period_days = number of consecutive drop days.

### Pattern 7: Market-Wide Event Tagging
**What:** Compare each company drop against S&P 500 + sector ETF on same day. If SPY dropped >3% on same day, tag as "Market-Wide Event".
**Data source:** SPY and sector ETF daily returns already available from new acquisition.

### Anti-Patterns to Avoid
- **Do not use `market_data["price_history"]`:** This key does not exist. Use `history_1y`/`history_5y`.
- **Do not generate charts inline without saving to disk:** All three output formats need chart access. Generate once, save to disk, embed in all.
- **Do not create a single massive chart file:** The new stock_charts.py will be complex. Split into data extraction (stock_chart_data.py) and rendering (stock_charts.py).
- **Do not use plotly for static PNG charts:** matplotlib is the project standard and produces identical results without additional dependencies.
- **Do not hardcode ETF tickers:** Use the existing `sectors.json` -> `sector_etfs` mapping.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Dark theme styling | Custom color overrides on every element | `plt.style.use('dark_background')` | Built-in style handles text, grid, axes, background consistently |
| Dual Y-axis alignment | Manual scale calculations | `ax1.twinx()` | Matplotlib handles axis alignment and independent scaling |
| Conditional area fill | Manual polygon calculations | `ax1.fill_between(where=...)` with `interpolate=True` | Handles intersection points automatically |
| Sector ETF mapping | Hardcoded dict | `brain/sectors.json` -> `sector_etfs` | Already maintained configuration with 12+ sector mappings |
| Price data extraction | New yfinance wrapper | Existing `_safe_get_history()` | Already handles errors, NaN, empty DataFrames |
| Date parsing | Custom date handling | Existing `get_dates()` + `get_close_prices()` | Already in `stock_drops.py`, handles edge cases |

**Key insight:** Most of the data infrastructure already exists. The main work is (a) fixing the key mismatch, (b) adding ETF/SPY acquisition, (c) rewriting the chart rendering style, and (d) wiring up the chart-to-disk-to-renderers pipeline.

## Common Pitfalls

### Pitfall 1: yfinance DataFrame Column Structure After `_dataframe_to_dict()`
**What goes wrong:** Assuming history data is a list of `{date, close, price}` dicts. It's actually column-oriented: `{"Date": [...], "Close": [...], "High": [...]}`.
**Why it happens:** The existing `_dataframe_to_dict()` calls `df.reset_index().to_dict(orient="list")` which produces column-oriented output, not row-oriented.
**How to avoid:** Always use `get_close_prices(history)` and `get_dates(history)` from `stock_drops.py` to extract data from history dicts.
**Warning signs:** Chart shows no data, `_parse_price_list` returns None because it expects `[{date, close}]` dicts.

### Pitfall 2: The 500-Line File Limit
**What goes wrong:** `stock_charts.py` is already 410 lines. A Bloomberg dark theme with stats header, dual axis, area fills, divergence bands, drop markers, and legend will easily exceed 500 lines.
**Why it happens:** Chart code is naturally verbose with matplotlib.
**How to avoid:** Split into: (a) `stock_chart_data.py` -- data extraction and preparation (~200 lines), (b) `stock_charts.py` -- rendering and styling (~400 lines), (c) `stock_chart_helpers.py` if needed for stats header and legend.
**Warning signs:** Single file growing past 350 lines during implementation.

### Pitfall 3: sect4_market.py Already Over 500 Lines
**What goes wrong:** `sect4_market.py` is already 508 lines and needs additions for drop detail tables.
**Why it happens:** Section 4 has the most sub-sections of any section.
**How to avoid:** The drop detail table should go in `sect4_market_events.py` (currently 497 lines -- also close to limit). May need to split market events further.
**Warning signs:** Any file exceeding 500 lines must be split per CLAUDE.md rules.

### Pitfall 4: ETF/SPY Data Not Available for All Companies
**What goes wrong:** Some companies may have no sector mapping, or ETF data may fail to download.
**Why it happens:** Edge cases: foreign companies, unusual SIC codes, yfinance failures.
**How to avoid:** Every ETF/SPY data path must have graceful fallback. Chart renders with just company price if overlays unavailable. Stats header shows "N/A" for unavailable metrics.
**Warning signs:** NoneType errors in chart rendering when ETF data is None.

### Pitfall 5: Dual-Axis Scale Confusion
**What goes wrong:** Left axis (dollar price) and right axis (indexed 100) can mislead if not clearly labeled.
**Why it happens:** Dual-axis charts are inherently misleading if not designed carefully.
**How to avoid:** Clear axis labels: left axis = "$" with company ticker, right axis = "Indexed (100)" with ETF/SPY tickers. Different line styles (solid vs dashed vs dotted).
**Warning signs:** User confusion about which line maps to which axis.

### Pitfall 6: Chart Cache Key Collisions
**What goes wrong:** Cache key based only on ticker misses data changes.
**Why it happens:** Price data changes daily; cached chart images become stale.
**How to avoid:** Hash the actual price data arrays (or their length + last date) into the cache key.
**Warning signs:** Charts showing stale data after re-acquisition.

### Pitfall 7: Recovery Time "Never Recovered"
**What goes wrong:** If a stock drops and never recovers within the analysis period, recovery time is undefined.
**Why it happens:** Analysis period ends before recovery.
**How to avoid:** Return `None` for recovery time and display as "Not recovered" in the drop table.
**Warning signs:** IndexError when searching for recovery past end of price array.

### Pitfall 8: Event Grouping Complexity
**What goes wrong:** Grouping consecutive drops into single events is algorithmically tricky -- what constitutes "consecutive"? Do weekends count? What about flat days between drops?
**Why it happens:** Markets have weekends, holidays, and sideways trading days.
**How to avoid:** Group by contiguous trading days where each day's return is negative (not just <-5%). The cumulative drop is from first day's open to last day's close. Allow 1 flat/up day in the middle to handle mid-drop bounces.
**Warning signs:** Too many or too few grouped events compared to reality.

## Code Examples

### Bloomberg Dark Theme Color Palette (Recommended)
```python
# Bloomberg Terminal GP-inspired colors for dark chart background
BLOOMBERG_DARK = {
    "bg": "#1B1B1D",          # Near-black background
    "grid": "#2A2A2C",        # Subtle dark gray grid
    "text": "#D4D4D6",        # Light gray text
    "text_muted": "#8E8E90",  # Muted secondary text
    "price_up": "#00C853",    # Green for gains (Bloomberg green)
    "price_down": "#FF1744",  # Red for losses
    "fill_up": "#00C85333",   # Green fill (20% opacity)
    "fill_down": "#FF174433", # Red fill (20% opacity)
    "etf_line": "#FFD700",    # Gold for sector ETF (dashed)
    "spy_line": "#4FC3F7",    # Light blue for S&P 500 (dotted)
    "divergence": "#FFD70020",# Gold divergence band (12% opacity)
    "drop_yellow": "#FFEB3B", # Yellow for 5-10% drops
    "drop_red": "#FF1744",    # Red for 10%+ drops
    "stat_header_bg": "#252527",  # Slightly lighter header bar
    "stat_header_text": "#FFFFFF", # White stats text
}
```

### Stats Header Implementation Pattern
```python
# Stats header as a figure subtitle or custom axes above the main chart
fig = plt.figure(figsize=(10, 5.5), dpi=200, facecolor=BLOOMBERG_DARK["bg"])
# Header axes (no frame, just text)
ax_header = fig.add_axes([0.05, 0.88, 0.9, 0.10])  # left, bottom, width, height
ax_header.set_facecolor(BLOOMBERG_DARK["stat_header_bg"])
ax_header.set_xlim(0, 1)
ax_header.set_ylim(0, 1)
ax_header.axis("off")

stats = [
    ("Price", f"${current_price:.2f}"),
    ("52W H/L", f"${high:.2f} / ${low:.2f}"),
    ("1Y Return", f"{return_1y:+.1f}%"),
    ("vs Sector", f"{alpha:+.1f}%"),
]
for i, (label, val) in enumerate(stats):
    x = 0.05 + i * 0.22
    ax_header.text(x, 0.6, label, fontsize=7, color=BLOOMBERG_DARK["text_muted"])
    ax_header.text(x, 0.15, val, fontsize=10, color=BLOOMBERG_DARK["stat_header_text"],
                   fontweight="bold")
```

### fill_between with Green/Red Conditional Fill
```python
# Source: matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.fill_between.html
base = prices[0]  # Starting price level
ax.fill_between(
    dates, prices, base,
    where=[p >= base for p in prices],
    color=BLOOMBERG_DARK["price_up"],
    alpha=0.2, interpolate=True, label="_nolegend_",
)
ax.fill_between(
    dates, prices, base,
    where=[p < base for p in prices],
    color=BLOOMBERG_DARK["price_down"],
    alpha=0.2, interpolate=True, label="_nolegend_",
)
```

### Chart-to-Disk Pipeline (RenderStage.run)
```python
# In render/__init__.py RenderStage.run():
chart_dir = output_dir / "charts"
chart_dir.mkdir(parents=True, exist_ok=True)

# Generate all charts and save to disk
_generate_all_charts(state, chart_dir, ds)

# Pass chart_dir to all renderers
render_word_document(state, docx_path, ds, chart_dir=chart_dir)
render_markdown(state, md_path, ds, chart_dir=chart_dir)
render_html_pdf(state, pdf_path, ds, chart_dir=chart_dir)
```

### Recovery Time Calculation
```python
def compute_recovery_days(
    prices: list[float], drop_idx: int, period_days: int = 1,
) -> int | None:
    """Trading days from drop end until price recovers to pre-drop level."""
    pre_drop_idx = max(0, drop_idx - period_days)
    pre_drop_price = prices[pre_drop_idx]

    for i in range(drop_idx + 1, len(prices)):
        if prices[i] >= pre_drop_price:
            return i - drop_idx
    return None  # Not recovered in analysis period
```

### Sector ETF + SPY Acquisition Addition
```python
# In market_client.py _collect_yfinance_data():
# After existing data collection...

# Sector ETF determination (from yfinance sector -> sectors.json mapping)
info = result.get("info", {})
sector = info.get("sector", "")
sector_etf = _resolve_sector_etf(sector)
if sector_etf:
    result["sector_etf"] = sector_etf
    result["sector_history_1y"] = _safe_get_history(yf.Ticker(sector_etf), "1y")
    result["sector_history_5y"] = _safe_get_history(yf.Ticker(sector_etf), "5y")

# S&P 500 benchmark (always acquire)
spy = yf.Ticker("SPY")
result["spy_history_1y"] = _safe_get_history(spy, "1y")
result["spy_history_5y"] = _safe_get_history(spy, "5y")
```

## Existing Codebase Key Findings

### Data Flow (Current, Broken)
```
ACQUIRE (market_client.py)
  -> market_data["history_1y"]  (dict: {Close: [], Date: [], ...})
  -> market_data["history_5y"]  (dict: {Close: [], Date: [], ...})
  -> market_data["info"]        (dict: yfinance info)
  -> NO sector_history, NO SPY history

EXTRACT (stock_performance.py)
  -> reads market_data["history_1y"] CORRECTLY
  -> reads market_data["history_5y"] CORRECTLY
  -> produces StockPerformance, StockDropAnalysis

RENDER (stock_charts.py)
  -> reads market_data["price_history"]  <-- DOES NOT EXIST (broken key)
  -> reads market_data["etf_history"]    <-- DOES NOT EXIST (never acquired)
  -> charts always return None
```

### Data Flow (Target, Fixed)
```
ACQUIRE (market_client.py)
  -> market_data["history_1y"]          (existing, unchanged)
  -> market_data["history_5y"]          (existing, unchanged)
  -> market_data["info"]                (existing, unchanged)
  -> market_data["sector_etf"]          (NEW: ETF ticker string)
  -> market_data["sector_history_1y"]   (NEW: ETF 1Y history dict)
  -> market_data["sector_history_5y"]   (NEW: ETF 5Y history dict)
  -> market_data["spy_history_1y"]      (NEW: SPY 1Y history dict)
  -> market_data["spy_history_5y"]      (NEW: SPY 5Y history dict)

EXTRACT (stock_performance.py + stock_drops.py)
  -> reads history_1y/5y              (unchanged)
  -> reads sector_history             (now "sector_history_1y")
  -> NEW: compute recovery_days per drop event
  -> NEW: group consecutive drops into single events
  -> NEW: tag market-wide events using SPY data
  -> produces enhanced StockDropEvent (with recovery_days, is_market_wide)

RENDER (stock_charts.py -- REWRITTEN)
  -> reads history_1y/5y CORRECTLY
  -> reads sector_history_1y/5y
  -> reads spy_history_1y/5y
  -> Bloomberg dark theme, dual axis, area fills
  -> saves PNGs to chart_dir
  -> all 3 renderers (Word, MD, PDF) embed charts
```

### Files Needing Modification (with current line counts)
| File | Lines | Change Type | Risk |
|------|-------|-------------|------|
| `stages/acquire/clients/market_client.py` | 252 | Add ETF + SPY acquisition | LOW -- additive |
| `stages/extract/stock_performance.py` | 421 | Add recovery time, fix sector key | MEDIUM -- existing logic |
| `stages/extract/stock_drops.py` | 355 | Add event grouping, market-wide tagging | MEDIUM -- algorithm additions |
| `stages/render/charts/stock_charts.py` | 410 | **REWRITE** -- Bloomberg theme | HIGH -- complete rewrite |
| `stages/render/chart_helpers.py` | 193 | Add save_chart_to_disk | LOW -- additive |
| `stages/render/__init__.py` | 233 | Add chart generation + chart_dir | MEDIUM -- pipeline change |
| `stages/render/sections/sect4_market.py` | **508** | Drop detail table (ALREADY OVER LIMIT) | HIGH -- needs split first |
| `stages/render/sections/sect4_market_events.py` | 497 | Enhanced drop rendering | MEDIUM -- close to limit |
| `stages/render/design_system.py` | 199 | Add Bloomberg colors | LOW -- additive |
| `models/market_events.py` | 455 | Add recovery_days, is_market_wide to StockDropEvent | LOW -- additive |
| `templates/markdown/worksheet.md.j2` | ~500 | Drop table template | LOW -- template changes |
| `templates/html/sections/market.html.j2` | 137 | Drop table + chart references | LOW -- template changes |

### Pre-Existing Infrastructure to Reuse
1. **Sector ETF mapping:** `brain/sectors.json` -> `sector_etfs` -- 12+ sectors mapped to primary ETF tickers
2. **Sector ETF lookup function:** `stages/extract/peer_group.py` -> `_get_sector_etf(sector_code)` -- already returns ETF ticker from sector code
3. **PeerGroup.sector_etf field:** `state.extracted.financials.peer_group.sector_etf` -- already populated during EXTRACT
4. **History data extraction helpers:** `stock_drops.py` -> `get_close_prices()`, `get_dates()`, `compute_daily_returns()`
5. **Chart save/embed pipeline:** `chart_helpers.py` -> `save_chart_to_bytes()`, `embed_chart()`
6. **PDF chart loading:** `pdf_renderer.py` -> `_load_chart_images(chart_dir)` -- expects `stock_1y.png`, `stock_5y.png`
7. **HTML chart embedding:** `templates/html/components/charts.html.j2` -> `embed_chart()` macro -- base64 embedding
8. **MD chart reference:** `templates/markdown/worksheet.md.j2` -> `{% if chart_dir %}![Stock Performance](images/stock_1y.png)`
9. **Trigger attribution:** `stock_drops.py` -> `attribute_triggers()` -- 8-K + earnings date matching

### StockDropEvent Model (Current Fields)
```python
class StockDropEvent(BaseModel):
    date: SourcedValue[str] | None           # Drop date
    drop_pct: SourcedValue[float] | None     # Percentage decline
    drop_type: str                            # SINGLE_DAY or MULTI_DAY
    period_days: int = 1                      # Duration in trading days
    sector_return_pct: SourcedValue[float] | None  # Sector on same period
    is_company_specific: bool                 # Company > sector decline
    trigger_event: SourcedValue[str] | None  # "earnings_release", "8-K_filing"
    close_price: float | None                # Closing price on drop date
```

### StockDropEvent Model (Needed Additions)
```python
# NEW fields needed:
recovery_days: int | None = None          # Trading days to recover
is_market_wide: bool = False              # SPY dropped >3% same day
trigger_source_url: str = ""              # URL to 8-K or news article
cumulative_pct: float | None = None       # For grouped events: total decline
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| White background charts | Bloomberg dark theme industry standard | Decision for Phase 37 | Complete visual overhaul |
| Indexed-to-100 single axis | Dual axis (dollars + indexed) | Decision for Phase 37 | More intuitive price reading |
| Simple line chart | Area chart with green/red fill | Decision for Phase 37 | Clear directional risk signal |
| No ETF/SPY overlay | Sector ETF + S&P 500 overlays | Decision for Phase 37 | Relative performance context |
| Drops listed as text | Full drop detail table with recovery time | Decision for Phase 37 | Actionable underwriting intelligence |

## Open Questions

1. **Weekly aggregation method for 5Y chart**
   - What we know: User wants weekly data for 5Y, not daily
   - What's unclear: Should we use Friday close, weekly average, or weekly OHLC?
   - Recommendation: Use Friday close (or last trading day of week) -- simplest and most standard for financial charts. yfinance supports `interval="1wk"` directly.

2. **Source links for trigger events**
   - What we know: Each drop trigger should include a source link. 8-K filings have SEC EDGAR URLs.
   - What's unclear: How to get source URLs for news-driven events? Current trigger attribution only matches dates, not specific documents.
   - Recommendation: For 8-K triggers, construct SEC EDGAR URL from accession number (already in `filing_documents`). For earnings triggers, link to earnings date on Yahoo Finance. For unmatched triggers, mark as "Unconfirmed -- Requires Investigation" per user decision. This is best-effort, not complete.

3. **Chart placement context ("Section 2: Market Data")**
   - What we know: CONTEXT.md says "Section 2: Market Data" but current code has market data in Section 4.
   - What's unclear: Is this a typo or an intentional reorganization?
   - Recommendation: Keep charts in Section 4 (current location). The section numbering reference in CONTEXT.md likely refers to "Section 4: Market" since all market content is there. Changing section order is out of scope.

4. **5Y chart drop threshold interaction with event grouping**
   - What we know: 5Y shows only >10% single-day or >15% cumulative. Event grouping merges consecutive drops.
   - What's unclear: Should grouping happen before or after threshold filtering for 5Y?
   - Recommendation: Group first, then filter. A series of -4% daily drops grouping to -15% cumulative should appear on the 5Y chart even though no single day hit 10%.

## Sources

### Primary (HIGH confidence)
- Codebase analysis: direct file reads of all files listed in Architecture Patterns section
- `stock_charts.py` (lines 148-160): confirmed key mismatch `price_history` vs `history_1y`
- `market_client.py` (line 97-100): confirmed acquisition stores as `history_1y`/`history_5y`
- `pdf_renderer.py` (lines 72-76): confirmed expected chart filenames
- `brain/sectors.json` (lines 95-109): confirmed sector ETF mapping exists
- [matplotlib dark_background docs](https://matplotlib.org/stable/gallery/style_sheets/dark_background.html)
- [matplotlib fill_between docs](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.fill_between.html)
- [matplotlib twinx docs](https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.twinx.html)

### Secondary (MEDIUM confidence)
- [Bloomberg Terminal dark theme for matplotlib](https://github.com/the-rccg/Dark-Color-Theme-for-MatplotLib) - inspiration for color palette
- [yfinance documentation](https://ranaroussi.github.io/yfinance/) - multi-ticker download API

### Tertiary (LOW confidence)
- Exact Bloomberg Terminal hex colors are approximations based on screenshots and community themes, not official Bloomberg specifications

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- matplotlib already in use, API well-documented
- Architecture: HIGH -- all data flow paths traced through codebase
- Pitfalls: HIGH -- identified from actual code analysis (key mismatches, line limits, None handling)
- Bloomberg colors: MEDIUM -- approximated from community themes, not official spec

**Research date:** 2026-02-21
**Valid until:** 2026-03-21 (stable domain, no fast-moving dependencies)
