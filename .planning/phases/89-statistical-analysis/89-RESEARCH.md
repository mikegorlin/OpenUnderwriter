# Phase 89: Statistical Analysis - Research

**Researched:** 2026-03-09
**Domain:** Stock drop DDL/MDL exposure, abnormal return event studies, EWMA volatility regimes
**Confidence:** HIGH

## Summary

Phase 89 adds three statistical analysis capabilities: (1) DDL/MDL dollar exposure computation from market cap and worst stock drops with settlement estimates, (2) abnormal return computation on event days using the market model with t-statistic significance testing, and (3) EWMA volatility alongside simple rolling vol with regime classification. All three build directly on existing infrastructure -- the codebase already has market model regression (`compute_idiosyncratic_vol`), rolling volatility (`compute_rolling_volatility`), settlement prediction (`settlement_prediction.py`), and stock drop detection (`stock_drops.py`).

The critical finding is that DDL computation already exists in `stages/score/settlement_prediction.py::compute_ddl()` and DDL exposure is already displayed in the classification table (`sect2_company_hazard.py`). STOCK-02 requires a simpler, more direct computation (market_cap x worst_drop_pct with 1.8% settlement estimate) displayed in the pricing section, distinct from the existing multi-scenario settlement prediction. The abnormal return computation (STOCK-04) extends the existing market model regression to produce per-day AR values and t-statistics. EWMA volatility (STOCK-05) is a new computation but slots into the existing volatility chart infrastructure.

**Primary recommendation:** Add computations in `chart_computations.py`, store results on model fields (StockPerformance for EWMA/regime, StockDropEvent for AR/t-stat, new DDLExposure model for STOCK-02), and wire to extraction in `stock_performance.py`. All math is pure Python -- no new dependencies needed.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| STOCK-02 | DDL/MDL exposure = market_cap x worst_drop_pct, settlement = DDL x 1.8%, in pricing section | market_cap_yf field exists on StockPerformance; worst_single_day on StockDropAnalysis; settlement_prediction.py has compute_ddl() as reference; sect2_company_hazard.py already shows ddl_exposure_base_m |
| STOCK-04 | Abnormal returns via market model (AR = R_actual - alpha - beta*R_market) with t-stat >= 1.96 | compute_idiosyncratic_vol already does OLS regression; compute_beta does cov/var; StockDropEvent needs new AR/t-stat fields; estimation window/event window methodology documented in research report |
| STOCK-05 | EWMA volatility (lambda=0.94) + regime detection (low/normal/elevated/crisis) | compute_rolling_volatility exists for simple vol; volatility_chart.py renders vol subplot; StockPerformance needs ewma_vol and regime fields |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pure Python math | stdlib | All statistical computations | Project convention -- no numpy/scipy (chart_computations.py pattern) |
| Pydantic v2 | existing | Model field additions | Project state model pattern |
| matplotlib | existing | Chart rendering | Already used for volatility chart |

### Supporting
No new dependencies. All computations use existing pure-Python math patterns from `chart_computations.py`.

## Architecture Patterns

### Computation Location
All new pure computations go in `chart_computations.py` following the existing pattern:
- `compute_ewma_volatility()` -- new
- `compute_abnormal_returns()` -- new (extends existing regression pattern)
- `compute_ddl_exposure()` -- new (simplified version of settlement_prediction.compute_ddl)

### Model Field Additions

**StockPerformance** (market.py) -- add:
```python
ewma_vol_current: SourcedValue[float] | None  # Current EWMA vol (annualized %)
vol_regime: SourcedValue[str] | None  # LOW / NORMAL / ELEVATED / CRISIS
vol_regime_duration_days: int | None  # Days in current regime
```

**StockDropEvent** (market_events.py) -- add:
```python
abnormal_return_pct: float | None  # AR on drop day (%)
abnormal_return_t_stat: float | None  # t-statistic for AR
is_statistically_significant: bool  # |t| >= 1.96
market_model_alpha: float | None  # alpha from estimation window
market_model_beta: float | None  # beta from estimation window
```

**New DDLExposure fields on StockDropAnalysis or StockPerformance:**
```python
ddl_exposure: SourcedValue[float] | None  # market_cap x worst_drop_pct (USD)
mdl_exposure: SourcedValue[float] | None  # market_cap x max_drawdown (USD)
ddl_settlement_estimate: SourcedValue[float] | None  # DDL x 0.018 (USD)
```

### Data Flow
```
EXTRACT (stock_performance.py)
  -> compute EWMA vol + regime (chart_computations.py)
  -> compute abnormal returns per drop (chart_computations.py)
  -> compute DDL/MDL exposure (chart_computations.py)
  -> store on StockPerformance + StockDropEvent + StockDropAnalysis

RENDER (volatility_chart.py)
  -> add EWMA line to existing vol subplot
  -> add regime background shading

RENDER (sect2_company_hazard.py or sect1_findings.py)
  -> display DDL/MDL exposure in pricing-relevant table
```

### Existing Infrastructure to Leverage

1. **Market model regression** -- `compute_idiosyncratic_vol()` in `chart_computations.py` already:
   - Computes daily returns for company and SPY
   - Runs `compute_beta()` for OLS beta
   - Computes residual variance
   - Just needs: return alpha alongside beta, compute AR per day, add t-stat

2. **Rolling volatility** -- `compute_rolling_volatility()` already:
   - Computes 30-day rolling annualized vol
   - Returns list aligned with price series
   - EWMA is a direct variant using exponential weights instead of equal weights

3. **DDL computation** -- `settlement_prediction.py::compute_ddl()` already:
   - Takes market_cap and stock_drops
   - Computes market_cap * max_drop_magnitude
   - STOCK-02 wants a simplified version: market_cap * worst_drop_pct with 1.8% settlement multiplier

4. **Market cap** -- `StockPerformance.market_cap_yf` already populated from yfinance info dict

5. **SPY prices** -- already acquired as `spy_history_1y` / `spy_history_2y` in market_data

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| OLS regression | Custom matrix solver | Existing `compute_beta()` cov/var pattern | Already proven, extend to return alpha |
| Settlement estimate | Complex actuarial model | DDL x 1.8% (req says this) | STOCK-02 is intentionally simplified |
| Regime boundaries | ML clustering | Fixed percentile thresholds on historical vol | Deterministic, reproducible, auditable |

## Common Pitfalls

### Pitfall 1: Estimation Window Overlap
**What goes wrong:** Using the event day itself in the estimation window for alpha/beta biases the abnormal return calculation.
**Why it happens:** Lazy windowing that doesn't gap properly.
**How to avoid:** Estimation window must end at least 2 days before the event. Use 120 trading days ending 5 days before event.
**Warning signs:** AR values suspiciously close to zero for known-significant events.

### Pitfall 2: EWMA Lambda Sensitivity
**What goes wrong:** Different lambda values produce dramatically different vol estimates.
**Why it happens:** EWMA is highly sensitive to the decay parameter.
**How to avoid:** Use lambda=0.94 as specified (RiskMetrics standard). Do NOT make this configurable initially.
**Warning signs:** Vol spikes that don't match visual chart appearance.

### Pitfall 3: Regime Threshold Calibration
**What goes wrong:** Regime labels don't match intuition -- "crisis" for normal market conditions.
**Why it happens:** Using absolute vol thresholds instead of relative/historical ones.
**How to avoid:** Define regimes relative to the company's own historical vol distribution: low (<25th pctile), normal (25-75th), elevated (75-90th), crisis (>90th).
**Warning signs:** Every company showing same regime.

### Pitfall 4: DDL Double-Counting
**What goes wrong:** DDL exposure shown in two places with different values.
**Why it happens:** Existing `classification.ddl_exposure_base_m` uses a prospective assumed drop, while STOCK-02 uses actual worst drop.
**How to avoid:** Be explicit: STOCK-02 DDL uses ACTUAL worst observed drop. Classification DDL uses assumed scenarios. Label clearly.
**Warning signs:** Underwriter confusion about which number to use.

### Pitfall 5: T-Stat Denominator with Low Observation Count
**What goes wrong:** T-stat inflated when estimation window is too short.
**Why it happens:** Standard error underestimated with few observations.
**How to avoid:** Require minimum 60 trading days in estimation window. If less, skip t-stat and mark AR as "insufficient data."
**Warning signs:** |t| > 5 for modest drops.

### Pitfall 6: Existing Settlement Prediction Conflict
**What goes wrong:** STOCK-02's simple DDL x 1.8% contradicts the existing multi-scenario settlement prediction in `settlement_prediction.py`.
**Why it happens:** Two different models for overlapping concepts.
**How to avoid:** STOCK-02 is a quick-reference metric for underwriter pricing context. The full settlement prediction remains for detailed scenario analysis. Present them in different sections with clear labels.

## Code Examples

### EWMA Volatility (lambda=0.94)
```python
# Source: RiskMetrics methodology, verified against research report
def compute_ewma_volatility(
    prices: list[float],
    lam: float = 0.94,
) -> list[float]:
    """Compute EWMA volatility series from prices.

    Returns annualized vol percentages aligned with price series.
    First value is 0.0 (no prior data).
    """
    if len(prices) < 2:
        return [0.0] * len(prices)

    sqrt_252 = math.sqrt(252)
    result: list[float] = [0.0]

    # Seed with first return squared
    r0 = math.log(prices[1] / prices[0]) if prices[0] > 0 and prices[1] > 0 else 0.0
    ewma_var = r0 ** 2
    result.append(math.sqrt(ewma_var) * sqrt_252 * 100.0)

    for i in range(2, len(prices)):
        if prices[i - 1] > 0 and prices[i] > 0:
            r = math.log(prices[i] / prices[i - 1])
        else:
            r = 0.0
        ewma_var = lam * ewma_var + (1 - lam) * r ** 2
        result.append(math.sqrt(ewma_var) * sqrt_252 * 100.0)

    return result
```

### Abnormal Return with Market Model
```python
# Source: Brown & Warner (1985), verified against research report
def compute_abnormal_return(
    company_returns: list[float],
    market_returns: list[float],
    event_idx: int,
    estimation_window: int = 120,
    gap: int = 5,
) -> tuple[float, float, bool] | None:
    """Compute abnormal return and t-stat for a single event day.

    Returns (ar_pct, t_stat, is_significant) or None if insufficient data.
    """
    est_end = event_idx - gap
    est_start = est_end - estimation_window

    if est_start < 0 or event_idx >= len(company_returns):
        return None

    # Estimation window returns
    cr_est = company_returns[est_start:est_end]
    mr_est = market_returns[est_start:est_end]

    if len(cr_est) < 60:  # Minimum for reliable estimates
        return None

    # OLS: compute alpha and beta
    n = len(cr_est)
    mean_c = sum(cr_est) / n
    mean_m = sum(mr_est) / n

    cov = sum((cr_est[i] - mean_c) * (mr_est[i] - mean_m) for i in range(n)) / n
    var_m = sum((mr_est[i] - mean_m) ** 2 for i in range(n)) / n

    if var_m < 1e-15:
        return None

    beta = cov / var_m
    alpha = mean_c - beta * mean_m

    # Residual standard deviation from estimation window
    residuals = [cr_est[i] - alpha - beta * mr_est[i] for i in range(n)]
    res_var = sum(r ** 2 for r in residuals) / (n - 2)
    res_std = math.sqrt(res_var) if res_var > 0 else 0.0

    if res_std < 1e-15:
        return None

    # Event day abnormal return
    ar = company_returns[event_idx] - (alpha + beta * market_returns[event_idx])
    ar_pct = ar * 100.0

    # T-statistic
    t_stat = ar / res_std
    is_significant = abs(t_stat) >= 1.96

    return (ar_pct, t_stat, is_significant)
```

### Volatility Regime Classification
```python
def classify_vol_regime(
    ewma_series: list[float],
    current_idx: int = -1,
) -> tuple[str, int]:
    """Classify current volatility regime based on historical distribution.

    Returns (regime_label, duration_days).
    Regimes: LOW (<25th pctile), NORMAL (25-75th), ELEVATED (75-90th), CRISIS (>90th).
    """
    valid = [v for v in ewma_series if v > 0]
    if not valid:
        return ("NORMAL", 0)

    sorted_vals = sorted(valid)
    n = len(sorted_vals)
    p25 = sorted_vals[int(n * 0.25)]
    p75 = sorted_vals[int(n * 0.75)]
    p90 = sorted_vals[int(n * 0.90)]

    current = ewma_series[current_idx] if ewma_series else 0.0

    if current <= p25:
        regime = "LOW"
    elif current <= p75:
        regime = "NORMAL"
    elif current <= p90:
        regime = "ELEVATED"
    else:
        regime = "CRISIS"

    # Count duration: how many consecutive days in same regime
    duration = 0
    for i in range(len(ewma_series) - 1, -1, -1):
        v = ewma_series[i]
        if v <= 0:
            continue
        if v <= p25:
            r = "LOW"
        elif v <= p75:
            r = "NORMAL"
        elif v <= p90:
            r = "ELEVATED"
        else:
            r = "CRISIS"
        if r == regime:
            duration += 1
        else:
            break

    return (regime, duration)
```

### DDL Exposure (STOCK-02)
```python
def compute_ddl_exposure(
    market_cap: float,
    worst_drop_pct: float,
    settlement_ratio: float = 0.018,
) -> dict[str, float]:
    """Compute DDL exposure and settlement estimate.

    Args:
        market_cap: Current market cap in USD.
        worst_drop_pct: Worst single-day drop as negative percentage (e.g., -15.3).
        settlement_ratio: Settlement as fraction of DDL (default 1.8%).

    Returns:
        Dict with ddl_amount, settlement_estimate.
    """
    magnitude = abs(worst_drop_pct) / 100.0
    ddl = market_cap * magnitude
    settlement = ddl * settlement_ratio
    return {
        "ddl_amount": ddl,
        "settlement_estimate": settlement,
    }
```

## Key Data Access Points

### Market Cap
- **Primary:** `state.extracted.market.stock.market_cap_yf` (SourcedValue[float], from yfinance info dict)
- **Fallback:** `state.company.market_cap` (SourcedValue[float], from XBRL/profile)
- Both populated during EXTRACT stage

### Worst Stock Drop
- `state.extracted.market.stock_drops.worst_single_day.drop_pct.value` (float, negative %)
- Already identified during extraction in `stock_performance.py`

### SPY Price Series (for market model)
- `state.acquired_data.market_data["spy_history_1y"]` / `["spy_history_2y"]`
- Already acquired, used by `compute_idiosyncratic_vol`

### Company Price Series
- `state.acquired_data.market_data["history_1y"]` / `["history_2y"]`
- Already acquired, dates from `get_dates()`, prices from `get_close_prices()`

### Existing Volatility Chart
- `volatility_chart.py::create_volatility_chart()` -- two-subplot chart
- Top: rolling 30-day vol with zones (green <20%, amber 20-40%, red >40%)
- Bottom: rolling 60-day beta
- Add EWMA line to top subplot, regime background to top subplot

## Rendering Targets

### STOCK-02: DDL Exposure Display
The requirement says "displayed in pricing section." Current options:
1. **sect2_company_hazard.py** -- already shows `ddl_exposure_base_m` in classification table
2. **sect1_findings.py** -- executive findings section, mentions DDL
3. **sect7_peril_map.py** -- has DDL settlement table with scenario rendering

**Recommendation:** Add DDL exposure (actual worst-drop-based) to `sect2_company_hazard.py` classification table alongside the existing prospective DDL. Also include in scoring section's severity scenarios context. Label distinction clearly: "Prospective DDL" (classification) vs "Observed DDL" (from actual drops).

### STOCK-04: Abnormal Return Display
- Per-drop AR and t-stat displayed in drop event details (stock chart drop annotations, drop table in HTML)
- Flag statistically significant drops with visual indicator
- Add to `StockDropEvent` model fields, render in existing drop detail sections

### STOCK-05: EWMA + Regime Display
- EWMA line added to existing volatility chart top subplot (alongside simple rolling vol)
- Regime classification as background shading on vol chart (replacing or augmenting static zones)
- Current regime label in vol chart header stats
- Regime field on StockPerformance for use in scoring/analysis

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Static vol zones (20%/40%) | Relative regime detection from own history | Phase 89 | More meaningful than fixed thresholds |
| Simple rolling vol only | EWMA + rolling vol dual display | Phase 89 | EWMA responds faster to vol changes |
| Drop events without significance | Market model AR with t-stat | Phase 89 | Distinguishes statistically significant drops |
| Prospective DDL only | Prospective + observed DDL | Phase 89 | Actual-drop DDL more relevant for pricing |

## Open Questions

1. **MDL vs DDL for STOCK-02**
   - What we know: Requirement says DDL (market_cap x worst_drop_pct). Research report also defines MDL (market_cap x max_drawdown from peak).
   - What's unclear: Whether to also compute MDL or only DDL.
   - Recommendation: Compute both. DDL = market_cap x worst_single_day_drop. MDL = market_cap x max_drawdown. Show both.

2. **Where exactly is "pricing section"?**
   - What we know: sect2_company_hazard already shows DDL. sect7_peril_map shows settlement scenarios. sect1_market_context shows market pricing.
   - What's unclear: Which section the user considers the "pricing section."
   - Recommendation: Add to sect2_company_hazard classification table (simplest, already has DDL). Consider also adding a summary card in sect1_findings.

3. **Regime thresholds: relative vs absolute?**
   - What we know: Requirement doesn't specify threshold method. Research suggests relative (percentile-based).
   - Recommendation: Use percentile-based on company's own history. More meaningful than fixed absolute thresholds. Fall back to absolute if history too short (<60 days).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | pyproject.toml |
| Quick run command | `uv run pytest tests/test_stock_performance.py -x` |
| Full suite command | `uv run pytest` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| STOCK-02 | DDL = market_cap x worst_drop, settlement = DDL x 1.8% | unit | `uv run pytest tests/stages/render/charts/test_chart_computations.py -x -k ddl` | No - Wave 0 |
| STOCK-04 | AR = R_actual - alpha - beta*R_market, t-stat significance | unit | `uv run pytest tests/stages/render/charts/test_chart_computations.py -x -k abnormal` | No - Wave 0 |
| STOCK-05 | EWMA vol with lambda=0.94, regime classification | unit | `uv run pytest tests/stages/render/charts/test_chart_computations.py -x -k ewma` | No - Wave 0 |
| STOCK-04 | AR stored on StockDropEvent after extraction | integration | `uv run pytest tests/test_stock_performance.py -x -k abnormal` | No - Wave 0 |
| STOCK-05 | EWMA and regime stored on StockPerformance after extraction | integration | `uv run pytest tests/test_stock_performance.py -x -k ewma` | No - Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/stages/render/charts/test_chart_computations.py tests/test_stock_performance.py -x`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** Full suite green before verify

### Wave 0 Gaps
- [ ] `tests/stages/render/charts/test_chart_computations.py` -- add test_compute_ewma_volatility, test_compute_abnormal_return, test_compute_ddl_exposure, test_classify_vol_regime
- [ ] `tests/test_stock_performance.py` -- add test_extraction_populates_ewma_regime, test_extraction_populates_abnormal_returns, test_extraction_populates_ddl_exposure

## Sources

### Primary (HIGH confidence)
- Codebase: `chart_computations.py` -- existing regression, vol, drawdown computations
- Codebase: `stock_performance.py` -- extraction pipeline, market_data access patterns
- Codebase: `settlement_prediction.py` -- existing DDL computation reference
- Codebase: `volatility_chart.py` -- existing chart structure
- Codebase: `market.py` / `market_events.py` -- current model fields
- Research: `.planning/research/stock-performance-do-research.md` -- DDL/MDL methodology, event study formulas, regime detection

### Secondary (MEDIUM confidence)
- RiskMetrics EWMA lambda=0.94 standard (well-established industry practice)
- Brown & Warner (1985) event study methodology (standard academic reference)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all pure Python, no new deps, existing patterns
- Architecture: HIGH -- direct extension of Phase 88 infrastructure
- Pitfalls: HIGH -- formulas well-documented in research report, existing code as reference
- Rendering targets: MEDIUM -- "pricing section" location ambiguous, multiple candidates

**Research date:** 2026-03-09
**Valid until:** 2026-04-09
