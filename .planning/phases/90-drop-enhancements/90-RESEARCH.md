# Phase 90: Drop Enhancements - Research

**Researched:** 2026-03-09
**Domain:** Stock drop scoring, return decomposition, corrective disclosure detection
**Confidence:** HIGH

## Summary

Phase 90 enhances stock drop analysis across three dimensions: time-decay weighting (recent drops score higher), per-drop return decomposition (market/sector/company attribution for each individual drop), and corrective disclosure reverse lookup (unexplained drops trigger search for 8-K filings and news in the days that follow). All three affect both the display layer (HTML table, Word table, context builder) and the F2 (Stock Decline) scoring factor.

The existing codebase provides strong foundations. `compute_return_decomposition()` in `chart_computations.py` already implements the 3-component decomposition formula for period-level returns -- it takes price arrays and returns market/sector/company percentages. `stock_drop_enrichment.py` already enriches drops from 8-K filings within a +/-3 day window and from web search results. The F2 scoring path (`factor_data.py` -> `factor_rules.py` -> `factor_scoring.py`) currently scores based on `decline_from_high` percentage with tier-based rules (F2-001 through F2-006), plus insider amplifiers and market cap multipliers. The three new scoring adjustments (decay, company-specific weighting, disclosure uplift) need to be integrated into this existing scoring pipeline.

**Primary recommendation:** Add new fields to `StockDropEvent` (decay_weight, market_pct, sector_pct, company_pct, disclosure_lag_days, disclosure_type), implement computation in `stock_performance.py` steps 8-10 area, modify F2 scoring to use drop-level contributions instead of just `decline_from_high`, and extend the HTML template and context builder with new columns.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Exponential decay with 6-month half-life: `weight = exp(-ln(2)/180 * days_ago)`
- At 6mo: ~50%, 12mo: ~25%, 18mo: ~12%, 24mo: ~6%
- Show decay weight as a visible column in the drops table (e.g., "0.87" or "87%")
- Drops table re-sorted by decay-weighted severity (magnitude x decay_weight), not raw magnitude
- Decay weight affects F2 (Stock Decline) factor score -- each drop's contribution multiplied by its decay weight
- Three inline columns added to drops table: Market, Sector, Company-Specific (consistent with Phase 88 period decomposition display)
- Full period decomposition for multi-day drops (first day open to last day close, not per-day breakdown)
- Drops where market contribution exceeds 50% get a "Market-Driven" badge/flag
- Company-specific percentage weights the drop's contribution to F2 scoring -- market-driven drops count less for D&O risk
- Reuse existing `compute_return_decomposition()` from chart_computations.py applied to price windows around each drop
- Search window: +1 to +14 days after drop for 8-K filings (existing +/-3 day forward lookup stays, this adds the reverse/delayed lookup)
- Web search fallback: Yes -- if no 8-K found, search Brave for company + drop date + keywords. Results marked LOW confidence
- Display: Linked badge with lag days (e.g., "8-K +3d" or "News +7d") next to trigger column
- Drops with confirmed corrective disclosure get a 1.5x scoring uplift in F2 -- drop + disclosure = stronger SCA trigger signal
- The three scoring adjustments (time-decay, company-specific weighting, disclosure uplift) all compound

### Claude's Discretion
- Exact exponential decay lambda constant (should yield 6-month half-life)
- Web search query templates for corrective disclosure fallback
- Threshold for "Market-Driven" badge (50% market contribution suggested, Claude can adjust)
- How to handle drops where decomposition data is unavailable (missing sector ETF data)
- Disclosure uplift multiplier calibration (1.5x suggested, Claude can adjust based on literature)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| STOCK-06 | Corrective disclosure detection enhanced with reverse lookup -- unexplained drops trigger search for contemporaneous 8-K filings and news | Existing `_find_8k_near_date()` handles +/-3d; extend with new `_find_8k_after_drop()` for +1 to +14d window. Web search fallback uses existing `_search_web_results_for_drop()` pattern. New fields on StockDropEvent for disclosure metadata |
| STOCK-08 | Time-decay weighting applied to stock drops -- recent drops score higher than older ones using exponential decay function | Pure math: `exp(-ln(2)/180 * days_ago)`. New `decay_weight` field on StockDropEvent. F2 scoring modified to use weighted drop contributions |
| STOCK-09 | Per-drop return decomposition showing market/sector/company-specific attribution for every identified drop event | Reuse `compute_return_decomposition()` from `chart_computations.py` by extracting price sub-arrays around each drop's date window. New fields: market_pct, sector_pct, company_pct on StockDropEvent |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python math | stdlib | `exp()`, `log()` for decay computation | No external deps needed for exponential decay |
| Pydantic v2 | existing | New fields on StockDropEvent | Already the model framework |
| chart_computations.py | existing | `compute_return_decomposition()` | Already implements 3-component decomposition |
| stock_drop_enrichment.py | existing | 8-K enrichment pipeline | Extend, don't replace |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| datetime | stdlib | Days-ago calculation for decay | Computing decay_weight for each drop |
| httpx | existing | Web search for disclosure fallback | Only if Brave Search MCP unavailable |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Exponential decay | Linear decay | Exponential better models actuarial time-sensitivity -- user chose exponential |
| 50% market-driven threshold | Statistical significance test | Simpler is better for display; AR/t-stat already covers statistical significance |

## Architecture Patterns

### Recommended Changes by File

```
src/do_uw/
  models/
    market_events.py           # Add 6 fields to StockDropEvent
  stages/
    extract/
      stock_performance.py     # Add per-drop decomposition step, decay computation
      stock_drop_enrichment.py # Add reverse 8-K lookup (+1 to +14d), web search fallback
      stock_drop_decay.py      # NEW: Decay weight computation (keep stock_performance.py <500 lines)
      stock_drop_decomposition.py  # NEW: Per-drop decomposition logic
    score/
      factor_data.py           # Modify _get_f2_data() to pass drop-level data
      factor_scoring.py        # Modify F2 scoring to use weighted drop contributions
      factor_rules.py          # Update _match_f2_rule() if needed
  stages/render/
    context_builders/market.py # Add new columns to drop_events list
    sections/sect4_drop_tables.py  # Add new columns to Word table
  templates/html/sections/market/
    stock_drops.html.j2        # Add Recency, Market, Sector, Company, Disclosure columns
```

### Pattern 1: Per-Drop Decomposition
**What:** For each StockDropEvent, extract the price sub-array from drop start to drop end for company, SPY, and sector ETF, then call `compute_return_decomposition()`.
**When to use:** After drops are identified (step 2-3 in stock_performance.py) but before enrichment (step 8).
**Example:**
```python
from do_uw.stages.render.charts.chart_computations import compute_return_decomposition

def decompose_drop(
    drop: StockDropEvent,
    company_prices: list[float],
    spy_prices: list[float],
    sector_prices: list[float],
    dates: list[str],
) -> StockDropEvent:
    """Add 3-component decomposition to a single drop event."""
    if not drop.date:
        return drop

    drop_date = drop.date.value[:10]
    start_idx = _find_price_index(dates, drop_date)
    if start_idx is None:
        return drop

    end_idx = start_idx + max(drop.period_days, 1)
    end_idx = min(end_idx, len(company_prices) - 1)

    # Extract price windows (need at least 2 points)
    co_window = company_prices[start_idx:end_idx + 1]
    spy_window = spy_prices[start_idx:end_idx + 1]
    sec_window = sector_prices[start_idx:end_idx + 1]

    result = compute_return_decomposition(co_window, spy_window, sec_window)
    if result:
        drop.market_pct = result["market_contribution"]
        drop.sector_pct = result["sector_contribution"]
        drop.company_pct = result["company_residual"]
    return drop
```

### Pattern 2: Time-Decay Weighting
**What:** Compute exponential decay weight for each drop based on days since drop.
**When to use:** After drops are fully constructed, before sorting for display.
**Example:**
```python
import math
from datetime import date

HALF_LIFE_DAYS = 180  # 6 months
DECAY_LAMBDA = math.log(2) / HALF_LIFE_DAYS  # ~0.003851

def compute_decay_weight(drop_date_str: str) -> float:
    """Compute exponential decay weight: exp(-lambda * days_ago)."""
    try:
        drop_date = date.fromisoformat(drop_date_str[:10])
        days_ago = (date.today() - drop_date).days
        return math.exp(-DECAY_LAMBDA * max(days_ago, 0))
    except (ValueError, TypeError):
        return 0.0
```

### Pattern 3: Corrective Disclosure Reverse Lookup
**What:** For unexplained drops, search +1 to +14 days AFTER the drop for 8-K filings that may explain it (delayed disclosure). Falls back to web search.
**When to use:** After initial 8-K enrichment (+/-3d), as a second pass for still-unexplained drops.
**Key insight:** The existing `_find_8k_near_date()` uses +/-3 days. The reverse lookup needs a FORWARD-ONLY window (+1 to +14d) to find delayed disclosures. This is a separate function, not a modification of the existing one.
```python
def _find_8k_after_drop(
    docs: list[dict[str, Any]],
    drop_date: str,
    max_lag_days: int = 14,
) -> list[tuple[dict[str, Any], int]]:
    """Find 8-K filings 1-14 days AFTER the drop date.

    Returns list of (doc, lag_days) tuples sorted by lag.
    """
    target = datetime.strptime(drop_date[:10], "%Y-%m-%d")
    matched: list[tuple[dict[str, Any], int]] = []
    for doc in docs:
        filing_date = doc.get("filing_date", "")
        if not filing_date:
            continue
        fd = datetime.strptime(filing_date[:10], "%Y-%m-%d")
        lag = (fd - target).days
        if 1 <= lag <= max_lag_days:
            matched.append((doc, lag))
    matched.sort(key=lambda x: x[1])  # Closest first
    return matched
```

### Pattern 4: Compound F2 Scoring
**What:** Each drop's contribution to F2 is: `magnitude * decay_weight * company_specific_pct * disclosure_multiplier`
**When to use:** Replace the current single `decline_from_high` approach with a drop-by-drop contribution sum.
**Key insight:** The current F2 scoring uses only `decline_from_high` (a single number). The new approach needs to aggregate individual drop contributions. The existing F2 rule structure (F2-001 through F2-006 with threshold tiers) should remain for the base score, but drop-level modifiers (decay, company %, disclosure) act as multipliers on the contribution.

### Anti-Patterns to Avoid
- **Don't modify `_find_8k_near_date()` window**: The existing +/-3d window serves a different purpose (forward-looking trigger identification). The reverse lookup is a separate function with a forward-only +1 to +14d window.
- **Don't put decay/decomposition in scoring layer**: These are data enrichment operations that belong in EXTRACT, not SCORE. The scoring layer should consume pre-computed fields.
- **Don't break the existing sort**: The context builder currently sorts by raw magnitude. Change sorting to decay-weighted severity, but keep raw magnitude available for display.
- **Don't add more than 500 lines to stock_performance.py**: It's already 925 lines. Extract new logic into separate modules.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Return decomposition | Custom per-drop math | `compute_return_decomposition()` from chart_computations.py | Already tested, already produces market/sector/company split |
| 8-K date matching | New date proximity logic | Extend `_find_8k_near_date()` pattern from stock_drop_enrichment.py | Same date parsing, same doc structure |
| Exponential decay | Custom decay function | `math.exp(-lambda * days)` | Standard math, one line |

## Common Pitfalls

### Pitfall 1: Price Array Index Alignment
**What goes wrong:** Company, SPY, and sector ETF price arrays may have different lengths or different date alignments due to trading halts, holidays, or data gaps.
**Why it happens:** yfinance returns data per-symbol independently. Sector ETFs may have different trading histories.
**How to avoid:** Use date-indexed lookup, not positional indexing. For per-drop decomposition, extract prices by date range, not by array slice index. The existing `get_dates()` + `_find_price_index()` pattern handles this.
**Warning signs:** Decomposition percentages don't sum to total return; market_contribution is wildly different from SPY return.

### Pitfall 2: Multi-Day Drop Window Definition
**What goes wrong:** For multi-day drops, using per-day decomposition instead of full-period (first open to last close).
**Why it happens:** Tempting to decompose each day separately and sum. User explicitly chose full-period decomposition.
**How to avoid:** For a multi-day drop with `period_days=5`, extract prices[start_idx] and prices[start_idx+5] as the two endpoints. Pass these as a 2-element array to `compute_return_decomposition()`.
**Warning signs:** Per-drop decomposition values don't match the period return.

### Pitfall 3: Decay Weight for Future Dates
**What goes wrong:** If drop date is in the future (data error), decay weight becomes > 1.0.
**How to avoid:** `max(days_ago, 0)` in the decay formula ensures weight never exceeds 1.0.

### Pitfall 4: F2 Scoring Backward Compatibility
**What goes wrong:** Changing F2 scoring methodology causes score regressions for existing tickers, breaking QA baselines.
**Why it happens:** Current F2 uses `decline_from_high` as a single scalar. New approach weights individual drops.
**How to avoid:** Keep the existing F2 rule structure (F2-001 through F2-006) as the BASE score. Apply decay, company-specific, and disclosure adjustments as multipliers/modifiers on top, similar to how the insider amplifier already works in `factor_scoring.py`.
**Warning signs:** Significant score changes for previously-analyzed tickers (> 2 points).

### Pitfall 5: Missing Sector ETF Data
**What goes wrong:** Some sectors have no ETF mapped, or sector ETF data is unavailable. Per-drop decomposition returns None.
**How to avoid:** When decomposition unavailable, set market_pct/sector_pct/company_pct to None. Display "N/A" in template. For scoring, treat missing decomposition as 100% company-specific (conservative assumption for D&O).
**Warning signs:** All drops showing N/A for decomposition columns.

### Pitfall 6: Reverse Lookup False Positives
**What goes wrong:** An 8-K filed 10 days after a drop may be completely unrelated (routine filing).
**Why it happens:** 14-day window is wide enough to catch routine filings.
**How to avoid:** Filter reverse-lookup 8-K by item type. Only D&O-relevant items (2.02 earnings, 4.02 restatement, 5.02 mgmt departure, 2.06 impairment) should be treated as corrective disclosures. Routine 8.01/9.01 items should not trigger the 1.5x uplift.
**Warning signs:** All drops getting disclosure badges for routine filings.

## Code Examples

### New StockDropEvent Fields
```python
# In models/market_events.py, add to StockDropEvent:

# --- Phase 90: Drop Enhancement Fields ---
decay_weight: float | None = Field(
    default=None,
    description="Exponential decay weight (0-1) based on recency. 6-month half-life.",
)
decay_weighted_severity: float | None = Field(
    default=None,
    description="abs(drop_pct) * decay_weight -- for sorting and scoring",
)
market_pct: float | None = Field(
    default=None,
    description="Market (SPY) contribution to this drop (%)",
)
sector_pct: float | None = Field(
    default=None,
    description="Sector contribution to this drop (%)",
)
company_pct: float | None = Field(
    default=None,
    description="Company-specific residual of this drop (%)",
)
is_market_driven: bool = Field(
    default=False,
    description="True if market contribution > 50% of total drop",
)
corrective_disclosure_type: str = Field(
    default="",
    description="Type of corrective disclosure found: '8-K', 'news', or ''",
)
corrective_disclosure_lag_days: int | None = Field(
    default=None,
    description="Days between drop and corrective disclosure (1-14)",
)
corrective_disclosure_url: str = Field(
    default="",
    description="URL to the corrective disclosure (8-K or news article)",
)
```

### Context Builder Extension
```python
# In context_builders/market.py, inside the drop_events loop, add:

# Phase 90 columns
"decay_weight": f"{evt.decay_weight:.0%}" if evt.decay_weight is not None else "N/A",
"market_pct": f"{evt.market_pct:+.1f}%" if evt.market_pct is not None else "N/A",
"sector_pct": f"{evt.sector_pct:+.1f}%" if evt.sector_pct is not None else "N/A",
"company_pct": f"{evt.company_pct:+.1f}%" if evt.company_pct is not None else "N/A",
"market_driven": "Market-Driven" if evt.is_market_driven else "",
"disclosure_badge": _format_disclosure_badge(evt),
```

### Sorting Change
```python
# Replace current sort in context_builders/market.py:
# OLD: sorted by abs(drop_pct) descending
# NEW: sorted by decay_weighted_severity descending
sorted_drops = sorted(
    all_drops,
    key=lambda d: d.decay_weighted_severity if d.decay_weighted_severity is not None else 0,
    reverse=True,
)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single `decline_from_high` for F2 | Drop-by-drop weighted contributions | Phase 90 | More nuanced scoring that accounts for recency, attribution, and disclosure |
| Raw magnitude sort in drops table | Decay-weighted severity sort | Phase 90 | Underwriter sees current risk first |
| Forward-only 8-K lookup (+/-3d) | Forward (+/-3d) + reverse (+1 to +14d) | Phase 90 | Catches delayed disclosures that confirm SCA pattern |
| Binary company-specific flag | Percentage-based attribution | Phase 90 | Quantifies how much of each drop is company-driven |

## Open Questions

1. **F2 Scoring Architecture Change**
   - What we know: Current F2 uses a single `decline_from_high` scalar to match rules F2-001 through F2-006. The new approach needs drop-level contributions.
   - What's unclear: Whether to (a) keep `decline_from_high` as the base and add drop-level modifiers, or (b) replace with a sum of weighted drop contributions.
   - Recommendation: Option (a) -- keep `decline_from_high` as the base rule matcher and add a new modifier step (like the existing insider amplifier) that adjusts the score based on drop-level weights. This preserves backward compatibility.

2. **Web Search Budget for Corrective Disclosure**
   - What we know: Brave Search has 2,000 free queries/month. Each unexplained drop could consume a query.
   - What's unclear: How many unexplained drops a typical ticker has (could be 5-15).
   - Recommendation: Limit web search to top 5 unexplained drops by magnitude. Use existing acquired web_search_results first (already in state from ACQUIRE stage). Only make new Brave queries if those are insufficient.

3. **stock_performance.py Line Count**
   - What we know: Already at 925 lines, 500-line limit in CLAUDE.md.
   - What's unclear: Whether to split now or add minimally.
   - Recommendation: Extract new logic into `stock_drop_decay.py` and `stock_drop_decomposition.py`. Keep stock_performance.py as the orchestrator that calls into these modules, consistent with how `stock_drop_enrichment.py` was already extracted.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pyproject.toml |
| Quick run command | `uv run pytest tests/stages/extract/test_stock_drops_enhanced.py -x` |
| Full suite command | `uv run pytest tests/ -x --timeout=30` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| STOCK-08 | Decay weight computed correctly for various ages | unit | `uv run pytest tests/stages/extract/test_stock_drop_decay.py -x` | No -- Wave 0 |
| STOCK-08 | 6-month-old drop has ~50% weight | unit | `uv run pytest tests/stages/extract/test_stock_drop_decay.py::test_half_life -x` | No -- Wave 0 |
| STOCK-08 | Drops re-sorted by decay-weighted severity | unit | `uv run pytest tests/stages/extract/test_stock_drop_decay.py::test_sort_order -x` | No -- Wave 0 |
| STOCK-08 | F2 score reflects decay weighting | unit | `uv run pytest tests/stages/score/test_factor_scoring_f2_decay.py -x` | No -- Wave 0 |
| STOCK-09 | Per-drop decomposition returns 3 components | unit | `uv run pytest tests/stages/extract/test_stock_drop_decomposition.py -x` | No -- Wave 0 |
| STOCK-09 | Market-Driven badge when market > 50% | unit | `uv run pytest tests/stages/extract/test_stock_drop_decomposition.py::test_market_driven -x` | No -- Wave 0 |
| STOCK-09 | Multi-day drops use full-period decomposition | unit | `uv run pytest tests/stages/extract/test_stock_drop_decomposition.py::test_multi_day -x` | No -- Wave 0 |
| STOCK-06 | Reverse 8-K lookup finds filings +1 to +14d after drop | unit | `uv run pytest tests/stages/extract/test_stock_drop_enrichment_reverse.py -x` | No -- Wave 0 |
| STOCK-06 | Disclosure badge shows lag days | unit | `uv run pytest tests/stages/extract/test_stock_drop_enrichment_reverse.py::test_badge -x` | No -- Wave 0 |
| STOCK-06 | F2 disclosure uplift applies 1.5x | unit | `uv run pytest tests/stages/score/test_factor_scoring_f2_decay.py::test_disclosure_uplift -x` | No -- Wave 0 |
| STOCK-08 | 3-month drop scores higher than identical 18-month drop | integration | `uv run pytest tests/stages/extract/test_stock_drop_decay.py::test_recency_ordering -x` | No -- Wave 0 |
| STOCK-09 | Context builder includes new columns | unit | `uv run pytest tests/stages/render/test_market_context.py -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/stages/extract/test_stock_drop_decay.py tests/stages/extract/test_stock_drop_decomposition.py tests/stages/extract/test_stock_drop_enrichment_reverse.py -x`
- **Per wave merge:** `uv run pytest tests/ -x --timeout=60`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/stages/extract/test_stock_drop_decay.py` -- covers STOCK-08 (decay weight computation, sorting)
- [ ] `tests/stages/extract/test_stock_drop_decomposition.py` -- covers STOCK-09 (per-drop decomposition)
- [ ] `tests/stages/extract/test_stock_drop_enrichment_reverse.py` -- covers STOCK-06 (reverse 8-K lookup, web fallback)
- [ ] `tests/stages/score/test_factor_scoring_f2_decay.py` -- covers F2 scoring modifications (decay, company %, disclosure uplift)
- [ ] `tests/stages/render/test_market_context.py` -- covers context builder new columns (may partially exist)

## Sources

### Primary (HIGH confidence)
- `src/do_uw/stages/render/charts/chart_computations.py` lines 260-306 -- `compute_return_decomposition()` implementation verified
- `src/do_uw/stages/extract/stock_drop_enrichment.py` -- Full enrichment pipeline reviewed (478 lines)
- `src/do_uw/models/market_events.py` lines 34-125 -- StockDropEvent model with all existing fields
- `src/do_uw/stages/score/factor_data.py` lines 127-156 -- `_get_f2_data()` implementation
- `src/do_uw/stages/score/factor_rules.py` lines 89-104 -- `_match_f2_rule()` with F2-001 through F2-006
- `src/do_uw/stages/score/factor_scoring.py` lines 126-156 -- F2 insider amplifier and market cap multiplier pattern
- `src/do_uw/stages/extract/stock_performance.py` lines 770-924 -- Drop detection, enrichment, and DDL computation flow
- `src/do_uw/stages/render/context_builders/market.py` lines 322-375 -- Drop events context builder
- `src/do_uw/templates/html/sections/market/stock_drops.html.j2` -- Complete HTML template for drops table
- `src/do_uw/stages/render/sections/sect4_drop_tables.py` -- Word renderer drop tables (253 lines)
- `src/do_uw/brain/config/scoring.json` -- F2 scoring config with rules and points

### Secondary (MEDIUM confidence)
- CONTEXT.md user decisions -- exact decay formula, window sizes, multipliers

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all components already exist in codebase, just need extension
- Architecture: HIGH -- clear insertion points identified, existing patterns to follow
- Pitfalls: HIGH -- based on direct code review of existing data structures and alignment issues

**Research date:** 2026-03-09
**Valid until:** 2026-04-09 (stable -- internal codebase patterns unlikely to change)
