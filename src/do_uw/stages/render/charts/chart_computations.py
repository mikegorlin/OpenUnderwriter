"""Pure Python financial computations for chart data.

Provides beta, volatility, and drawdown calculations without
numpy/scipy dependencies. Used by stock_chart_data.py and
the chart rendering modules.

All functions operate on plain Python lists of floats.
"""

from __future__ import annotations

import math

# Trading days per year for annualizing volatility.
_TRADING_DAYS_PER_YEAR = 252


# ---------------------------------------------------------------------------
# Beta computation
# ---------------------------------------------------------------------------


def compute_beta(returns_x: list[float], returns_market: list[float]) -> float | None:
    """Compute OLS beta: cov(x, m) / var(m).

    Pure Python -- no numpy/scipy dependency.

    Args:
        returns_x: Asset return series.
        returns_market: Market return series (same length).

    Returns:
        Beta coefficient, or None if insufficient data or zero variance.
    """
    n = min(len(returns_x), len(returns_market))
    if n < 10:
        return None

    rx = returns_x[:n]
    rm = returns_market[:n]

    mean_x = sum(rx) / n
    mean_m = sum(rm) / n

    cov_xm = sum((rx[i] - mean_x) * (rm[i] - mean_m) for i in range(n)) / n
    var_m = sum((rm[i] - mean_m) ** 2 for i in range(n)) / n

    if var_m < 1e-15:
        return None

    return cov_xm / var_m


# ---------------------------------------------------------------------------
# Rolling volatility
# ---------------------------------------------------------------------------


def compute_rolling_volatility(
    prices: list[float], window: int = 30,
) -> list[float]:
    """Compute annualized rolling volatility from a price series.

    Returns a list of annualized volatility values (one per price point).
    The first ``window`` values are set to 0.0 (insufficient lookback).

    Pure Python -- no numpy/scipy dependency.

    Args:
        prices: Daily price series.
        window: Lookback window in trading days.

    Returns:
        List of annualized volatility percentages (same length as prices).
    """
    if len(prices) < window + 1:
        return [0.0] * len(prices)

    # Daily log returns.
    returns: list[float] = [0.0]
    for i in range(1, len(prices)):
        if prices[i - 1] > 0 and prices[i] > 0:
            returns.append(math.log(prices[i] / prices[i - 1]))
        else:
            returns.append(0.0)

    result: list[float] = [0.0] * window
    sqrt_252 = math.sqrt(_TRADING_DAYS_PER_YEAR)

    for i in range(window, len(returns)):
        window_returns = returns[i - window + 1 : i + 1]
        mean_r = sum(window_returns) / window
        var_r = sum((r - mean_r) ** 2 for r in window_returns) / (window - 1)
        vol = math.sqrt(var_r) * sqrt_252 * 100.0  # Annualized, as percentage
        result.append(vol)

    return result


# ---------------------------------------------------------------------------
# Drawdown series
# ---------------------------------------------------------------------------


def compute_drawdown_series(prices: list[float]) -> list[float]:
    """Compute running drawdown percentages from a price series.

    Returns a list of drawdown values, always <= 0.
    Drawdown = (price - running_max) / running_max * 100.

    Args:
        prices: Daily price series.

    Returns:
        List of drawdown percentages (same length as prices).
    """
    if not prices:
        return []

    result: list[float] = []
    running_max = prices[0]

    for p in prices:
        if p > running_max:
            running_max = p
        if running_max > 0:
            dd = (p - running_max) / running_max * 100.0
        else:
            dd = 0.0
        result.append(dd)

    return result


# ---------------------------------------------------------------------------
# Daily returns helper
# ---------------------------------------------------------------------------


def compute_daily_returns(prices: list[float]) -> list[float]:
    """Compute simple daily returns from prices."""
    returns: list[float] = []
    for i in range(1, len(prices)):
        if prices[i - 1] > 0:
            returns.append((prices[i] - prices[i - 1]) / prices[i - 1])
        else:
            returns.append(0.0)
    return returns


# ---------------------------------------------------------------------------
# Annualized volatility (single value)
# ---------------------------------------------------------------------------


def compute_annualized_vol(
    prices: list[float] | None, window: int = 90,
) -> float | None:
    """Compute annualized volatility over the last ``window`` trading days.

    Args:
        prices: Daily price series.
        window: Number of trailing trading days to use.

    Returns:
        Annualized volatility as percentage, or None if insufficient data.
    """
    if not prices or len(prices) < window + 1:
        return None

    recent = prices[-(window + 1):]
    returns: list[float] = []
    for i in range(1, len(recent)):
        if recent[i - 1] > 0 and recent[i] > 0:
            returns.append(math.log(recent[i] / recent[i - 1]))
        else:
            returns.append(0.0)

    if len(returns) < 2:
        return None

    n = len(returns)
    mean_r = sum(returns) / n
    var_r = sum((r - mean_r) ** 2 for r in returns) / (n - 1)
    return math.sqrt(var_r) * math.sqrt(_TRADING_DAYS_PER_YEAR) * 100.0


# ---------------------------------------------------------------------------
# Idiosyncratic volatility
# ---------------------------------------------------------------------------


def compute_idiosyncratic_vol(
    prices: list[float] | None,
    spy_prices: list[float] | None,
) -> float | None:
    """Compute idiosyncratic vol as residual from market model.

    idiosyncratic_vol = sqrt(total_var - beta^2 * market_var)

    Args:
        prices: Company daily price series.
        spy_prices: S&P 500 daily price series.

    Returns:
        Annualized idiosyncratic vol as percentage, or None.
    """
    if not prices or not spy_prices:
        return None

    comp_returns = compute_daily_returns(prices)
    mkt_returns = compute_daily_returns(spy_prices)

    n = min(len(comp_returns), len(mkt_returns))
    if n < 30:
        return None

    cr = comp_returns[:n]
    mr = mkt_returns[:n]

    beta = compute_beta(cr, mr)
    if beta is None:
        return None

    mean_c = sum(cr) / n
    mean_m = sum(mr) / n

    var_c = sum((c - mean_c) ** 2 for c in cr) / n
    var_m = sum((m - mean_m) ** 2 for m in mr) / n

    residual_var = var_c - (beta ** 2) * var_m
    if residual_var < 0:
        residual_var = 0.0

    return math.sqrt(residual_var) * math.sqrt(_TRADING_DAYS_PER_YEAR) * 100.0


# ---------------------------------------------------------------------------
# Sector beta
# ---------------------------------------------------------------------------


def compute_sector_beta(
    etf_prices: list[float] | None,
    spy_prices: list[float] | None,
) -> float | None:
    """Compute sector ETF beta by regressing ETF returns against SPY returns."""
    if not etf_prices or not spy_prices:
        return None
    etf_returns = compute_daily_returns(etf_prices)
    spy_returns = compute_daily_returns(spy_prices)
    return compute_beta(etf_returns, spy_returns)


# ---------------------------------------------------------------------------
# Return decomposition (3-component attribution)
# ---------------------------------------------------------------------------


def compute_return_decomposition(
    company_prices: list[float],
    spy_prices: list[float],
    sector_prices: list[float],
) -> dict[str, float] | None:
    """Decompose total return into market, sector, and company components.

    Formula:
        market_contribution = SPY return
        sector_contribution = sector ETF return - SPY return
        company_residual    = company return - sector ETF return
        total_return        = market + sector + company (by construction)

    Args:
        company_prices: Company daily price series.
        spy_prices: S&P 500 daily price series.
        sector_prices: Sector ETF daily price series.

    Returns:
        Dict with total_return, market_contribution, sector_contribution,
        company_residual (all as percentages), or None if data insufficient.
    """
    if (
        len(company_prices) < 2
        or len(spy_prices) < 2
        or len(sector_prices) < 2
    ):
        return None

    # Guard against zero start prices.
    if company_prices[0] <= 0 or spy_prices[0] <= 0 or sector_prices[0] <= 0:
        return None

    company_ret = (company_prices[-1] - company_prices[0]) / company_prices[0] * 100.0
    spy_ret = (spy_prices[-1] - spy_prices[0]) / spy_prices[0] * 100.0
    sector_ret = (sector_prices[-1] - sector_prices[0]) / sector_prices[0] * 100.0

    market_contribution = spy_ret
    sector_contribution = sector_ret - spy_ret
    company_residual = company_ret - sector_ret

    return {
        "total_return": company_ret,
        "market_contribution": market_contribution,
        "sector_contribution": sector_contribution,
        "company_residual": company_residual,
    }


# ---------------------------------------------------------------------------
# MDD ratio (company drawdown vs sector drawdown)
# ---------------------------------------------------------------------------


def compute_mdd_ratio(
    company_prices: list[float],
    sector_prices: list[float],
) -> float | None:
    """Compute company MDD / sector MDD ratio.

    A ratio > 1 means the company draws down more than its sector.
    Returns None when sector MDD is near zero (>= -0.5%) or data
    is insufficient.

    Args:
        company_prices: Company daily price series.
        sector_prices: Sector ETF daily price series.

    Returns:
        MDD ratio (positive float), or None.
    """
    from do_uw.stages.extract.stock_performance import compute_max_drawdown

    company_mdd = compute_max_drawdown(company_prices)
    sector_mdd = compute_max_drawdown(sector_prices)

    if company_mdd is None or sector_mdd is None:
        return None

    # Sector MDD near zero means no meaningful drawdown to compare against.
    if sector_mdd >= -0.5:
        return None

    return company_mdd / sector_mdd


# ---------------------------------------------------------------------------
# DDL / MDL exposure computation (Phase 89 - STOCK-02)
# ---------------------------------------------------------------------------


def compute_ddl_exposure(
    market_cap: float,
    worst_drop_pct: float,
    max_drawdown_pct: float | None = None,
    settlement_ratio: float = 0.018,
) -> dict[str, float | None]:
    """Compute DDL exposure and settlement estimate from actual worst drop.

    DDL (Dollar Loss Liability) = market_cap x |worst_drop_pct| / 100.
    MDL (Maximum Drawdown Liability) = market_cap x |max_drawdown_pct| / 100.
    Settlement estimate = DDL x settlement_ratio (default 1.8%).

    Args:
        market_cap: Current market cap in USD.
        worst_drop_pct: Worst single-day drop as percentage (e.g. -15.3).
        max_drawdown_pct: Max peak-to-trough drawdown percentage (optional).
        settlement_ratio: Settlement as fraction of DDL (default 1.8%).

    Returns:
        Dict with ddl_amount, mdl_amount (or None), settlement_estimate.
    """
    magnitude = abs(worst_drop_pct) / 100.0
    ddl = market_cap * magnitude
    settlement = ddl * settlement_ratio

    mdl: float | None = None
    if max_drawdown_pct is not None:
        mdl = market_cap * abs(max_drawdown_pct) / 100.0

    return {
        "ddl_amount": ddl,
        "mdl_amount": mdl,
        "settlement_estimate": settlement,
    }


# ---------------------------------------------------------------------------
# Abnormal return event study (Phase 89 - STOCK-04)
# ---------------------------------------------------------------------------


def compute_abnormal_return(
    company_returns: list[float],
    market_returns: list[float],
    event_idx: int,
    estimation_window: int = 120,
    gap: int = 5,
) -> tuple[float, float, bool] | None:
    """Compute abnormal return and t-stat for a single event day.

    Uses the market model (Brown & Warner 1985): AR = R_actual - alpha - beta * R_market.
    Estimation window ends ``gap`` days before event to avoid contamination.

    Args:
        company_returns: Daily simple returns for company.
        market_returns: Daily simple returns for market (same length).
        event_idx: Index of event day in the returns arrays.
        estimation_window: Number of trading days for alpha/beta estimation.
        gap: Days between estimation window end and event day.

    Returns:
        Tuple of (ar_pct, t_stat, is_significant) or None if insufficient data.
    """
    est_end = event_idx - gap
    est_start = est_end - estimation_window

    if est_start < 0 or event_idx >= len(company_returns):
        return None

    # Estimation window returns
    cr_est = company_returns[est_start:est_end]
    mr_est = market_returns[est_start:est_end]

    if len(cr_est) < 60:
        return None

    # OLS regression: alpha + beta * R_market
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


# ---------------------------------------------------------------------------
# EWMA volatility (Phase 89 - STOCK-05)
# ---------------------------------------------------------------------------


def compute_ewma_volatility(
    prices: list[float],
    lam: float = 0.94,
) -> list[float]:
    """Compute EWMA volatility series from prices (RiskMetrics, lambda=0.94).

    Returns annualized volatility percentages aligned with price series.
    First value is always 0.0 (no prior data to compute return).

    Args:
        prices: Daily price series.
        lam: EWMA decay factor (default 0.94, RiskMetrics standard).

    Returns:
        List of annualized EWMA volatility values (same length as prices).
    """
    if len(prices) < 2:
        return [0.0] * len(prices)

    sqrt_252 = math.sqrt(_TRADING_DAYS_PER_YEAR)
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


# ---------------------------------------------------------------------------
# Volatility regime classification (Phase 89 - STOCK-05)
# ---------------------------------------------------------------------------


def classify_vol_regime(
    ewma_series: list[float],
    current_idx: int = -1,
) -> tuple[str, int]:
    """Classify current volatility regime based on historical distribution.

    Regimes are defined by percentiles of the company's own EWMA vol history:
    - LOW: below 25th percentile
    - NORMAL: 25th to 75th percentile
    - ELEVATED: 75th to 90th percentile
    - CRISIS: above 90th percentile

    Args:
        ewma_series: EWMA vol series from compute_ewma_volatility.
        current_idx: Index to classify (default -1 = last).

    Returns:
        Tuple of (regime_label, duration_days).
    """
    valid = [v for v in ewma_series if v > 0]
    if not valid:
        return ("NORMAL", 0)

    sorted_vals = sorted(valid)
    n = len(sorted_vals)
    p25 = sorted_vals[int(n * 0.25)]
    p75 = sorted_vals[int(n * 0.75)]
    p90 = sorted_vals[min(int(n * 0.90), n - 1)]

    current = ewma_series[current_idx] if ewma_series else 0.0

    def _label(v: float) -> str:
        if v <= p25:
            return "LOW"
        elif v <= p75:
            return "NORMAL"
        elif v <= p90:
            return "ELEVATED"
        else:
            return "CRISIS"

    regime = _label(current)

    # Count consecutive days in same regime from end
    duration = 0
    for i in range(len(ewma_series) - 1, -1, -1):
        v = ewma_series[i]
        if v <= 0:
            continue
        if _label(v) == regime:
            duration += 1
        else:
            break

    return (regime, duration)


# ---------------------------------------------------------------------------
# Correlation and R-squared
# ---------------------------------------------------------------------------


def compute_correlation(
    prices_a: list[float], prices_b: list[float],
) -> float | None:
    """Compute Pearson correlation of daily returns between two price series.

    Returns None if fewer than 30 overlapping return observations or zero variance.

    Args:
        prices_a: First daily price series.
        prices_b: Second daily price series.

    Returns:
        Pearson correlation coefficient, or None.
    """
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
    company_prices: list[float], benchmark_prices: list[float],
) -> float | None:
    """R-squared from Pearson correlation of daily returns.

    R^2 = corr^2. Measures proportion of company return variance
    explained by the benchmark.

    Args:
        company_prices: Company daily price series.
        benchmark_prices: Benchmark (e.g., SPY) daily price series.

    Returns:
        R-squared value, or None if correlation cannot be computed.
    """
    corr = compute_correlation(company_prices, benchmark_prices)
    if corr is None:
        return None
    return corr ** 2


__all__ = [
    "classify_vol_regime",
    "compute_abnormal_return",
    "compute_annualized_vol",
    "compute_beta",
    "compute_correlation",
    "compute_daily_returns",
    "compute_ddl_exposure",
    "compute_drawdown_series",
    "compute_ewma_volatility",
    "compute_idiosyncratic_vol",
    "compute_mdd_ratio",
    "compute_r_squared",
    "compute_return_decomposition",
    "compute_rolling_volatility",
    "compute_sector_beta",
]
