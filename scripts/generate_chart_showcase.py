#!/usr/bin/env python3
"""
Generate a comprehensive chart showcase comparing multiple charting libraries
for D&O underwriting reports. Uses real data from state.json.

Usage: python scripts/generate_chart_showcase.py
"""

import json
import math
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = PROJECT_ROOT / "output" / "AAPL" / "2026-03-22" / "state.json"
OUTPUT_PATH = PROJECT_ROOT / "output" / "AAPL" / "chart_showcase.html"
MPL_OUTPUT_DIR = PROJECT_ROOT / "output" / "AAPL" / "charts"

# ---------------------------------------------------------------------------
# Load state
# ---------------------------------------------------------------------------
print(f"Loading state from {STATE_PATH} ...")
with open(STATE_PATH) as f:
    state = json.load(f)

md = state["acquired_data"]["market_data"]
scoring = state["scoring"]

# ---------------------------------------------------------------------------
# Prepare data subsets as JSON-safe dicts
# ---------------------------------------------------------------------------

def weekly_resample(dates, closes, volumes, opens=None, highs=None, lows=None):
    """Resample daily data to weekly (last close per week)."""
    weekly_dates, weekly_close, weekly_vol = [], [], []
    weekly_open, weekly_high, weekly_low = [], [], []
    cur_week = None
    week_closes, week_vols = [], []
    week_opens, week_highs, week_lows = [], [], []
    week_date = None
    for i, d in enumerate(dates):
        dt = d[:10] if len(d) >= 10 else d
        # ISO week
        try:
            iso_week = datetime.strptime(dt, "%Y-%m-%d").isocalendar()[:2]
        except Exception:
            continue
        if cur_week is None:
            cur_week = iso_week
        if iso_week != cur_week:
            weekly_dates.append(week_date)
            weekly_close.append(week_closes[-1])
            weekly_vol.append(sum(week_vols))
            if opens:
                weekly_open.append(week_opens[0])
                weekly_high.append(max(week_highs))
                weekly_low.append(min(week_lows))
            week_closes, week_vols = [], []
            week_opens, week_highs, week_lows = [], [], []
            cur_week = iso_week
        week_date = dt
        week_closes.append(closes[i])
        week_vols.append(volumes[i])
        if opens:
            week_opens.append(opens[i])
            week_highs.append(highs[i])
            week_lows.append(lows[i])
    # last partial week
    if week_closes:
        weekly_dates.append(week_date)
        weekly_close.append(week_closes[-1])
        weekly_vol.append(sum(week_vols))
        if opens:
            weekly_open.append(week_opens[0])
            weekly_high.append(max(week_highs))
            weekly_low.append(min(week_lows))
    result = {"dates": weekly_dates, "close": weekly_close, "volume": weekly_vol}
    if opens:
        result["open"] = weekly_open
        result["high"] = weekly_high
        result["low"] = weekly_low
    return result


def clean_date(d):
    """Extract YYYY-MM-DD from datetime string."""
    if not d:
        return None
    return d[:10] if len(d) >= 10 else d


def safe_float(v, default=0.0):
    if v is None:
        return default
    try:
        return float(v)
    except (ValueError, TypeError):
        return default


# ---- 5-year data (weekly) ----
h5 = md["history_5y"]
h5_dates_clean = [clean_date(d) for d in h5["Date"]]
h5_weekly = weekly_resample(h5["Date"], h5["Close"], h5["Volume"],
                            h5["Open"], h5["High"], h5["Low"])

# ---- 2-year data (daily) ----
h2 = md["history_2y"]
h2_dates = [clean_date(d) for d in h2["Date"]]
h2_close = h2["Close"]
h2_volume = h2["Volume"]
h2_open = h2["Open"]
h2_high = h2["High"]
h2_low = h2["Low"]

# ---- 6-month data (daily OHLCV) ----
# Take last ~130 trading days
n6m = 130
h6m_dates = h2_dates[-n6m:]
h6m_open = h2_open[-n6m:]
h6m_high = h2_high[-n6m:]
h6m_low = h2_low[-n6m:]
h6m_close = h2_close[-n6m:]
h6m_volume = h2_volume[-n6m:]

# ---- Sector & SPY 2-year ----
sh2 = md["sector_history_2y"]
spy2 = md["spy_history_2y"]

# Compute % returns from start
def pct_returns(closes):
    if not closes or closes[0] == 0:
        return [0.0] * len(closes)
    base = closes[0]
    return [round((c / base - 1) * 100, 2) for c in closes]

perf_dates = [clean_date(d) for d in h2["Date"]]
perf_aapl = pct_returns(h2["Close"])
perf_sector = pct_returns(sh2["Close"])
perf_spy = pct_returns(spy2["Close"])

# ---- Earnings data ----
ed = md["earnings_dates"]
earnings_data = []
for i in range(len(ed["Earnings Date"])):
    dt = ed["Earnings Date"][i]
    if not dt:
        continue
    date_str = clean_date(dt)
    reported = ed["Reported EPS"][i]
    estimate = ed["EPS Estimate"][i]
    surprise = ed["Surprise(%)"][i]
    if reported is not None:
        earnings_data.append({
            "date": date_str,
            "reported": safe_float(reported),
            "estimate": safe_float(estimate),
            "surprise": safe_float(surprise),
        })

# ---- Insider transactions ----
it = md["insider_transactions"]
insider_data = []
for i in range(len(it["index"])):
    val = it["Value"][i]
    shares = it["Shares"][i]
    if val and val > 0:
        insider_data.append({
            "date": it["Start Date"][i],
            "insider": it["Insider"][i],
            "position": it["Position"][i],
            "shares": shares,
            "value": val,
        })

# ---- Risk factor scores ----
factor_scores = []
for fs in scoring["factor_scores"]:
    factor_scores.append({
        "id": fs["factor_id"],
        "name": fs["factor_name"],
        "deducted": round(safe_float(fs["points_deducted"]), 1),
        "max": fs["max_points"],
        "pct": round(safe_float(fs["points_deducted"]) / fs["max_points"] * 100, 1) if fs["max_points"] > 0 else 0,
    })

# ---- Financial metrics (annual) ----
ai_stmt = md.get("income_stmt", {})
bs_stmt = md.get("balance_sheet", {})
cf_stmt = md.get("cashflow", {})
fin_periods = ai_stmt.get("periods", [])
fin_li = ai_stmt.get("line_items", {})
bs_li = bs_stmt.get("line_items", {})
cf_li = cf_stmt.get("line_items", {}) if cf_stmt else {}

revenue_data = fin_li.get("Total Revenue", [])
net_income_data = fin_li.get("Net Income", [])
gross_profit_data = fin_li.get("Gross Profit", [])
total_debt_data = bs_li.get("Total Debt", [])
total_assets_data = bs_li.get("Total Assets", [])
total_equity_data = bs_li.get("Stockholders Equity", [])
op_cf_data = cf_li.get("Operating Cash Flow", []) if cf_li else []

# Build financial sparkline data
def safe_list(data, n):
    """Ensure list has n entries, filling None."""
    if not data:
        return [None] * n
    return [safe_float(v, None) for v in data[:n]]

n_periods = len(fin_periods)
fin_metrics = {
    "periods": [p[:4] for p in fin_periods],  # just years
    "revenue": safe_list(revenue_data, n_periods),
    "net_income": safe_list(net_income_data, n_periods),
    "gross_profit": safe_list(gross_profit_data, n_periods),
    "total_debt": safe_list(total_debt_data, n_periods),
    "total_assets": safe_list(total_assets_data, n_periods),
    "total_equity": safe_list(total_equity_data, n_periods),
}

# Compute margins
fin_metrics["gross_margin"] = []
fin_metrics["net_margin"] = []
for i in range(n_periods):
    rev = fin_metrics["revenue"][i]
    gp = fin_metrics["gross_profit"][i]
    ni = fin_metrics["net_income"][i]
    fin_metrics["gross_margin"].append(round(gp / rev * 100, 1) if rev and gp else None)
    fin_metrics["net_margin"].append(round(ni / rev * 100, 1) if rev and ni else None)

fin_metrics["debt_to_equity"] = []
for i in range(n_periods):
    td = fin_metrics["total_debt"][i]
    te = fin_metrics["total_equity"][i]
    fin_metrics["debt_to_equity"].append(round(td / te, 2) if td and te and te != 0 else None)

# ---- Governance risk scores ----
info = md.get("info", {})
gov_scores = {
    "audit_risk": info.get("auditRisk"),
    "board_risk": info.get("boardRisk"),
    "compensation_risk": info.get("compensationRisk"),
    "shareholder_rights_risk": info.get("shareHolderRightsRisk"),
    "overall_risk": info.get("overallRisk"),
}

# ---- Significant drops (>10%) ----
def find_significant_drops(dates, closes, threshold=-0.10):
    drops = []
    peak = closes[0]
    peak_date = dates[0]
    for i in range(1, len(closes)):
        if closes[i] > peak:
            peak = closes[i]
            peak_date = dates[i]
        drawdown = (closes[i] - peak) / peak
        if drawdown <= threshold:
            # Check if this is a new drop (not continuation)
            if not drops or dates[i] != drops[-1]["trough_date"]:
                drops.append({
                    "peak_date": peak_date,
                    "peak_price": round(peak, 2),
                    "trough_date": dates[i],
                    "trough_price": round(closes[i], 2),
                    "drop_pct": round(drawdown * 100, 1),
                })
    # Deduplicate — keep deepest drop per peak
    unique = {}
    for d in drops:
        key = d["peak_date"]
        if key not in unique or d["drop_pct"] < unique[key]["drop_pct"]:
            unique[key] = d
    return list(unique.values())

sig_drops = find_significant_drops(h2_dates, h2_close, -0.10)

# ---- DDL (Dollar Damages Line) exposure ----
def compute_ddl(dates, closes, market_caps_start):
    """Running max drawdown in dollar terms."""
    if not market_caps_start:
        market_caps_start = info.get("marketCap", 3.6e12)
    # Shares outstanding estimate
    shares = market_caps_start / closes[0] if closes[0] else 1e9
    running_max = closes[0]
    ddl_dates = []
    ddl_values = []
    for i in range(len(closes)):
        if closes[i] > running_max:
            running_max = closes[i]
        drawdown_per_share = running_max - closes[i]
        ddl = drawdown_per_share * shares
        ddl_dates.append(dates[i])
        ddl_values.append(round(ddl / 1e9, 2))  # in billions
    return ddl_dates, ddl_values

ddl_dates, ddl_values = compute_ddl(h2_dates, h2_close, info.get("marketCap"))

# ---- Suspicious windows: insider trades in 30 days before >5% drops ----
def find_suspicious_windows(dates, closes, insider_trades):
    """Find insider sales in 30 days before >5% stock drops."""
    # Find >5% drops
    drops_5pct = []
    peak = closes[0]
    peak_idx = 0
    for i in range(1, len(closes)):
        if closes[i] > peak:
            peak = closes[i]
            peak_idx = i
        dd = (closes[i] - peak) / peak
        if dd <= -0.05:
            drops_5pct.append({
                "date": dates[i],
                "peak_date": dates[peak_idx],
                "drop_pct": round(dd * 100, 1),
                "peak_price": round(peak, 2),
                "trough_price": round(closes[i], 2),
            })
    # Deduplicate by peak
    unique_drops = {}
    for d in drops_5pct:
        key = d["peak_date"]
        if key not in unique_drops or d["drop_pct"] < unique_drops[key]["drop_pct"]:
            unique_drops[key] = d
    drops_list = list(unique_drops.values())

    # For each drop, find insider trades in 30-day window before the drop started
    windows = []
    for drop in drops_list:
        peak_dt = datetime.strptime(drop["peak_date"], "%Y-%m-%d")
        window_start = peak_dt - timedelta(days=30)
        window_trades = []
        for t in insider_trades:
            try:
                t_dt = datetime.strptime(t["date"], "%Y-%m-%d")
            except Exception:
                continue
            if window_start <= t_dt <= peak_dt:
                window_trades.append(t)
        windows.append({
            "drop": drop,
            "window_start": window_start.strftime("%Y-%m-%d"),
            "window_end": drop["peak_date"],
            "trades": window_trades,
            "total_value": sum(t["value"] for t in window_trades),
        })
    return windows

suspicious_windows = find_suspicious_windows(h2_dates, h2_close, insider_data)

# ---- Volatility: rolling 30-day std ----
def rolling_volatility(closes, window=30):
    vols = []
    for i in range(len(closes)):
        if i < window:
            vols.append(None)
        else:
            subset = closes[i - window:i]
            mean = sum(subset) / len(subset)
            var = sum((x - mean) ** 2 for x in subset) / len(subset)
            daily_vol = math.sqrt(var) / mean * 100  # as % of price
            vols.append(round(daily_vol, 2))
    return vols

aapl_vol = rolling_volatility(h2_close)
sector_vol = rolling_volatility(sh2["Close"])

# ---- Market cap waterfall (quarterly) ----
qi = md.get("quarterly_income_stmt", {})
qi_periods = qi.get("periods", [])
qi_li = qi.get("line_items", {})
qi_revenue = qi_li.get("Total Revenue", [])
qi_net_income = qi_li.get("Net Income", [])


# ---------------------------------------------------------------------------
# Generate matplotlib chart
# ---------------------------------------------------------------------------
def generate_matplotlib_chart():
    """Generate a high-quality matplotlib stock chart."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from matplotlib.patches import Rectangle
        import numpy as np
    except ImportError:
        print("WARNING: matplotlib not available, skipping matplotlib chart")
        return None

    MPL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = MPL_OUTPUT_DIR / "stock_performance_mpl.png"

    # Prepare data
    dates_dt = [datetime.strptime(d, "%Y-%m-%d") for d in h2_dates]
    closes = np.array(h2_close)
    volumes = np.array(h2_volume)

    # Sector and SPY
    sector_closes = np.array(sh2["Close"])
    spy_closes = np.array(spy2["Close"])

    # Normalize to % return
    aapl_ret = (closes / closes[0] - 1) * 100
    sector_ret = (sector_closes / sector_closes[0] - 1) * 100
    spy_ret = (spy_closes / spy_closes[0] - 1) * 100

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), height_ratios=[3, 1],
                                     gridspec_kw={"hspace": 0.05})
    fig.patch.set_facecolor("#0f1117")

    for ax in (ax1, ax2):
        ax.set_facecolor("#1a1d29")
        ax.tick_params(colors="#8b8fa3", labelsize=9)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["bottom"].set_color("#2a2d3a")
        ax.spines["left"].set_color("#2a2d3a")
        ax.grid(True, color="#2a2d3a", linewidth=0.5, alpha=0.5)

    # Price chart
    ax1.plot(dates_dt, aapl_ret, color="#4fc3f7", linewidth=1.5, label="AAPL", zorder=3)
    ax1.plot(dates_dt, sector_ret, color="#ff9800", linewidth=1.0, alpha=0.7, label="Sector ETF", zorder=2)
    ax1.plot(dates_dt, spy_ret, color="#66bb6a", linewidth=1.0, alpha=0.7, label="S&P 500", zorder=2)
    ax1.fill_between(dates_dt, aapl_ret, 0, where=(aapl_ret >= 0),
                      color="#4fc3f7", alpha=0.1, zorder=1)
    ax1.fill_between(dates_dt, aapl_ret, 0, where=(aapl_ret < 0),
                      color="#ef5350", alpha=0.15, zorder=1)
    ax1.axhline(y=0, color="#555", linewidth=0.8, linestyle="--")

    # Mark earnings dates
    for e in earnings_data:
        try:
            edt = datetime.strptime(e["date"], "%Y-%m-%d")
            if dates_dt[0] <= edt <= dates_dt[-1]:
                idx = min(range(len(dates_dt)), key=lambda j: abs((dates_dt[j] - edt).days))
                color = "#66bb6a" if e["surprise"] >= 0 else "#ef5350"
                ax1.axvline(x=edt, color=color, alpha=0.3, linewidth=0.8, linestyle=":")
                ax1.plot(edt, aapl_ret[idx], "o", color=color, markersize=6, zorder=4)
        except Exception:
            pass

    # Mark insider sales
    for ins in insider_data[:10]:
        try:
            idt = datetime.strptime(ins["date"], "%Y-%m-%d")
            if dates_dt[0] <= idt <= dates_dt[-1]:
                idx = min(range(len(dates_dt)), key=lambda j: abs((dates_dt[j] - idt).days))
                ax1.plot(idt, aapl_ret[idx], "v", color="#ff5252", markersize=8,
                         alpha=0.8, zorder=5)
        except Exception:
            pass

    ax1.set_ylabel("Return (%)", color="#8b8fa3", fontsize=10)
    ax1.legend(loc="upper left", fontsize=9, facecolor="#1a1d29", edgecolor="#2a2d3a",
               labelcolor="#c8ccd8")
    ax1.set_title("AAPL — 2-Year Performance vs Benchmarks with Earnings & Insider Activity",
                   color="#e0e2ea", fontsize=13, fontweight="bold", pad=15)
    ax1.set_xticklabels([])

    # Volume
    colors_vol = ["#4fc3f7" if closes[i] >= closes[max(0, i - 1)] else "#ef5350"
                  for i in range(len(closes))]
    ax2.bar(dates_dt, volumes / 1e6, width=1.5, color=colors_vol, alpha=0.6)
    ax2.set_ylabel("Vol (M)", color="#8b8fa3", fontsize=10)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    fig.autofmt_xdate(rotation=0)

    # Add annotation
    final_ret = aapl_ret[-1]
    ax1.annotate(f"AAPL: {final_ret:+.1f}%", xy=(dates_dt[-1], aapl_ret[-1]),
                 xytext=(-80, 15), textcoords="offset points",
                 color="#4fc3f7", fontsize=10, fontweight="bold",
                 arrowprops=dict(arrowstyle="->", color="#4fc3f7", lw=1.2))

    plt.savefig(output_file, dpi=300, bbox_inches="tight", facecolor="#0f1117")
    plt.close()
    print(f"  Matplotlib chart saved to {output_file}")

    # Read as base64 for embedding
    import base64
    with open(output_file, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


mpl_b64 = generate_matplotlib_chart()

# ---------------------------------------------------------------------------
# Build JSON data blobs for JavaScript
# ---------------------------------------------------------------------------
js_data = {
    # 5-year weekly
    "h5_weekly": h5_weekly,
    # 2-year daily
    "h2": {"dates": h2_dates, "close": h2_close, "volume": h2_volume,
            "open": h2_open, "high": h2_high, "low": h2_low},
    # 6-month daily OHLCV
    "h6m": {"dates": h6m_dates, "open": h6m_open, "high": h6m_high,
             "low": h6m_low, "close": h6m_close, "volume": h6m_volume},
    # Performance comparison
    "perf": {"dates": perf_dates, "aapl": perf_aapl, "sector": perf_sector, "spy": perf_spy},
    # Earnings
    "earnings": earnings_data,
    # Insider trades
    "insiders": insider_data,
    # Factor scores
    "factors": factor_scores,
    # Financial metrics
    "financials": fin_metrics,
    # Governance
    "governance": gov_scores,
    # Significant drops
    "sig_drops": sig_drops,
    # DDL
    "ddl": {"dates": ddl_dates, "values": ddl_values},
    # Suspicious windows
    "suspicious": suspicious_windows,
    # Volatility
    "volatility": {"dates": h2_dates, "aapl": aapl_vol, "sector": sector_vol},
    # Company info
    "info": {
        "marketCap": info.get("marketCap"),
        "beta": info.get("beta"),
        "shortRatio": info.get("shortRatio"),
        "shortPercentOfFloat": info.get("shortPercentOfFloat"),
        "trailingPE": info.get("trailingPE"),
        "forwardPE": info.get("forwardPE"),
    },
    # Scoring
    "scoring": {
        "composite": scoring.get("composite_score"),
        "tier": scoring.get("tier", {}).get("tier"),
    },
    # Quarterly financials
    "quarterly": {
        "periods": qi_periods,
        "revenue": [safe_float(v, None) for v in qi_li.get("Total Revenue", [])],
        "net_income": [safe_float(v, None) for v in qi_li.get("Net Income", [])],
        "ebitda": [safe_float(v, None) for v in qi_li.get("EBITDA", [])],
    },
}

# ---------------------------------------------------------------------------
# HTML Template
# ---------------------------------------------------------------------------
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>D&O Underwriting Chart Showcase — AAPL</title>
<style>
  :root {{
    --bg: #0f1117;
    --card-bg: #1a1d29;
    --card-border: #2a2d3a;
    --text: #c8ccd8;
    --text-dim: #8b8fa3;
    --accent: #4fc3f7;
    --red: #ef5350;
    --green: #66bb6a;
    --orange: #ff9800;
    --purple: #ab47bc;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    padding: 2rem;
  }}
  h1 {{
    font-size: 2rem;
    color: #fff;
    margin-bottom: 0.5rem;
  }}
  h1 span {{ color: var(--accent); }}
  .subtitle {{
    color: var(--text-dim);
    font-size: 0.95rem;
    margin-bottom: 2rem;
  }}
  /* TOC */
  .toc {{
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 12px;
    padding: 1.5rem 2rem;
    margin-bottom: 3rem;
  }}
  .toc h2 {{
    color: var(--accent);
    font-size: 1.1rem;
    margin-bottom: 1rem;
  }}
  .toc-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 0.5rem;
  }}
  .toc a {{
    color: var(--text);
    text-decoration: none;
    padding: 0.3rem 0.5rem;
    border-radius: 6px;
    font-size: 0.9rem;
    display: block;
    transition: background 0.15s;
  }}
  .toc a:hover {{ background: rgba(79, 195, 247, 0.1); color: var(--accent); }}
  .toc a .num {{ color: var(--text-dim); margin-right: 0.5rem; }}

  /* Library section */
  .lib-section {{
    margin-bottom: 4rem;
  }}
  .lib-header {{
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1.5rem;
    padding-bottom: 0.75rem;
    border-bottom: 2px solid var(--card-border);
  }}
  .lib-header h2 {{
    font-size: 1.5rem;
    color: #fff;
  }}
  .lib-badge {{
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  .badge-lw {{ background: rgba(79, 195, 247, 0.15); color: var(--accent); }}
  .badge-echarts {{ background: rgba(171, 71, 188, 0.15); color: var(--purple); }}
  .badge-chartjs {{ background: rgba(255, 152, 0, 0.15); color: var(--orange); }}
  .badge-d3 {{ background: rgba(102, 187, 106, 0.15); color: var(--green); }}
  .badge-mpl {{ background: rgba(239, 83, 80, 0.15); color: var(--red); }}

  /* Chart card */
  .chart-card {{
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
  }}
  .chart-card h3 {{
    font-size: 1.15rem;
    color: #fff;
    margin-bottom: 0.25rem;
  }}
  .chart-card .do-relevance {{
    color: var(--text-dim);
    font-size: 0.85rem;
    margin-bottom: 1rem;
    padding-left: 0.75rem;
    border-left: 3px solid var(--accent);
  }}
  .chart-card .do-relevance strong {{ color: var(--accent); }}
  .chart-container {{
    width: 100%;
    min-height: 400px;
    position: relative;
  }}
  .chart-container canvas {{
    width: 100% !important;
  }}
  .lib-tag {{
    position: absolute;
    top: 1rem;
    right: 1rem;
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 600;
    background: rgba(0,0,0,0.5);
    color: var(--text-dim);
  }}
  .na-notice {{
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 300px;
    color: var(--text-dim);
    font-size: 1.1rem;
    border: 1px dashed var(--card-border);
    border-radius: 8px;
  }}
  .chart-card .insight {{
    margin-top: 0.75rem;
    padding: 0.75rem 1rem;
    background: rgba(79, 195, 247, 0.05);
    border-radius: 8px;
    font-size: 0.85rem;
    color: var(--text-dim);
  }}
  .chart-card .insight strong {{ color: var(--accent); }}

  /* D3 specific */
  .d3-chart svg {{
    width: 100%;
    overflow: visible;
  }}
  .d3-chart .axis text {{ fill: var(--text-dim); font-size: 11px; }}
  .d3-chart .axis line, .d3-chart .axis path {{ stroke: var(--card-border); }}

  /* Score card grid */
  .score-grid {{
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 0.75rem;
    margin-bottom: 1.5rem;
  }}
  .score-tile {{
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--card-border);
    border-radius: 8px;
    padding: 0.75rem;
    text-align: center;
  }}
  .score-tile .val {{ font-size: 1.5rem; font-weight: 700; }}
  .score-tile .lbl {{ font-size: 0.75rem; color: var(--text-dim); }}

  /* Summary stats */
  .summary-bar {{
    display: flex;
    gap: 2rem;
    margin-bottom: 2rem;
    padding: 1rem 1.5rem;
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 12px;
    flex-wrap: wrap;
  }}
  .summary-bar .stat {{
    text-align: center;
  }}
  .summary-bar .stat .val {{
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--accent);
  }}
  .summary-bar .stat .lbl {{
    font-size: 0.75rem;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
</style>

<!-- Chart Libraries -->
<script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="https://d3js.org/d3.v7.min.js"></script>

</head>
<body>

<h1>D&O Underwriting <span>Chart Showcase</span></h1>
<p class="subtitle">
  Apple Inc. (AAPL) &mdash; Composite Score: {scoring.get("composite_score", 0):.1f} &mdash;
  Tier: {scoring.get("tier", {}).get("tier", "N/A")} &mdash;
  Generated {datetime.now().strftime("%Y-%m-%d %H:%M")}
</p>

<!-- Summary bar -->
<div class="summary-bar">
  <div class="stat"><div class="val">${info.get("marketCap", 0) / 1e12:.2f}T</div><div class="lbl">Market Cap</div></div>
  <div class="stat"><div class="val">{info.get("beta", 0):.2f}</div><div class="lbl">Beta</div></div>
  <div class="stat"><div class="val">{info.get("trailingPE", 0):.1f}x</div><div class="lbl">Trailing P/E</div></div>
  <div class="stat"><div class="val">{info.get("shortPercentOfFloat", 0) * 100:.2f}%</div><div class="lbl">Short % Float</div></div>
  <div class="stat"><div class="val">{len(insider_data)}</div><div class="lbl">Insider Sales (2Y)</div></div>
  <div class="stat"><div class="val">{len(sig_drops)}</div><div class="lbl">Sig. Drops (&gt;10%)</div></div>
  <div class="stat"><div class="val">${max(ddl_values):.1f}B</div><div class="lbl">Peak DDL Exposure</div></div>
</div>

<!-- Table of Contents -->
<div class="toc">
  <h2>Table of Contents</h2>
  <div class="toc-grid">
    <a href="#lw-area5y"><span class="num">1.</span> 5-Year Price (LW Charts)</a>
    <a href="#lw-earnings"><span class="num">2.</span> Earnings Markers (LW Charts)</a>
    <a href="#lw-candle"><span class="num">3.</span> 6-Mo Candlestick (LW Charts)</a>
    <a href="#ec-perf"><span class="num">4.</span> Performance Comparison (ECharts)</a>
    <a href="#ec-insider"><span class="num">5.</span> Insider Activity Timeline (ECharts)</a>
    <a href="#ec-earnings"><span class="num">6.</span> Earnings Reaction (ECharts)</a>
    <a href="#ec-ddl"><span class="num">7.</span> DDL Exposure Area (ECharts)</a>
    <a href="#cj-radar"><span class="num">8.</span> Risk Factor Radar (Chart.js)</a>
    <a href="#cj-prob"><span class="num">9.</span> Probability Decomposition (Chart.js)</a>
    <a href="#cj-fin"><span class="num">10.</span> Financial Dashboard (Chart.js)</a>
    <a href="#d3-suspicious"><span class="num">11.</span> Suspicious Trading Windows (D3)</a>
    <a href="#d3-waterfall"><span class="num">12.</span> Market Cap Waterfall (D3)</a>
    <a href="#ec-drops"><span class="num">13.</span> Significant Drops Analysis (ECharts)</a>
    <a href="#ec-vol"><span class="num">14.</span> Volatility Profile (ECharts)</a>
    <a href="#cj-gov"><span class="num">15.</span> Governance Risk Radar (Chart.js)</a>
    <a href="#mpl-perf"><span class="num">16.</span> Best Performance Chart (Matplotlib)</a>
  </div>
</div>

<!-- ================================================================== -->
<!-- Data injection -->
<script>
const DATA = {json.dumps(js_data, default=str)};
</script>

<!-- ================================================================== -->
<!-- SECTION 1: Lightweight Charts -->
<!-- ================================================================== -->
<div class="lib-section">
  <div class="lib-header">
    <h2>Lightweight Charts (TradingView)</h2>
    <span class="lib-badge badge-lw">Lightweight Charts</span>
  </div>

  <!-- 1. 5-Year Area Chart -->
  <div class="chart-card" id="lw-area5y">
    <h3>1. Five-Year Price History with Volume</h3>
    <div class="do-relevance">
      <strong>D&O Relevance — Loss Causation:</strong> Long-term price trajectory reveals whether current price
      is near all-time highs (lower DDL exposure) or in a sustained decline (higher exposure).
      Weekly smoothing shows the macro trend without daily noise.
    </div>
    <span class="lib-tag">Lightweight Charts</span>
    <div class="chart-container" id="lw-area5y-chart" style="height:500px;"></div>
  </div>

  <!-- 2. 2-Year with Earnings Markers -->
  <div class="chart-card" id="lw-earnings">
    <h3>2. Two-Year Price with Earnings Events</h3>
    <div class="do-relevance">
      <strong>D&O Relevance — Earnings Fraud / Guidance:</strong> Maps earnings dates to price moves.
      Consistent beats with minimal price reaction = well-managed expectations.
      Misses followed by drops = potential misrepresentation claim.
    </div>
    <span class="lib-tag">Lightweight Charts</span>
    <div class="chart-container" id="lw-earnings-chart" style="height:500px;"></div>
  </div>

  <!-- 3. 6-Month Candlestick -->
  <div class="chart-card" id="lw-candle">
    <h3>3. Six-Month Candlestick with Volume</h3>
    <div class="do-relevance">
      <strong>D&O Relevance — Recent Volatility:</strong> OHLC bars show daily price ranges and gaps.
      Large gap-downs on earnings or news = potential corrective disclosure events.
      Volume spikes on red days suggest institutional selling.
    </div>
    <span class="lib-tag">Lightweight Charts</span>
    <div class="chart-container" id="lw-candle-chart" style="height:500px;"></div>
  </div>
</div>

<!-- ================================================================== -->
<!-- SECTION 2: ECharts -->
<!-- ================================================================== -->
<div class="lib-section">
  <div class="lib-header">
    <h2>Apache ECharts</h2>
    <span class="lib-badge badge-echarts">ECharts</span>
  </div>

  <!-- 4. Performance Comparison -->
  <div class="chart-card" id="ec-perf">
    <h3>4. Performance vs Benchmarks (2-Year % Return)</h3>
    <div class="do-relevance">
      <strong>D&O Relevance — Loss Causation / Market-wide defense:</strong> If the stock tracks the market,
      defendants argue market forces caused the loss (truth-on-the-market defense). Company-specific
      underperformance isolates the stock-specific loss component for DDL calculation.
    </div>
    <span class="lib-tag">ECharts</span>
    <div class="chart-container" id="ec-perf-chart" style="height:450px;"></div>
  </div>

  <!-- 5. Insider Activity Timeline -->
  <div class="chart-card" id="ec-insider">
    <h3>5. Insider Trading Activity on Price Chart</h3>
    <div class="do-relevance">
      <strong>D&O Relevance — Scienter:</strong> Insider sales before drops are THE smoking gun for
      securities fraud claims. Plaintiffs use this to establish that officers/directors KNEW about
      problems and sold to avoid personal losses. Pattern of sales &gt; $1M before significant drops
      dramatically increases claim severity.
    </div>
    <span class="lib-tag">ECharts</span>
    <div class="chart-container" id="ec-insider-chart" style="height:500px;"></div>
  </div>

  <!-- 6. Earnings Reaction -->
  <div class="chart-card" id="ec-earnings">
    <h3>6. Earnings Surprise vs Price Reaction</h3>
    <div class="do-relevance">
      <strong>D&O Relevance — Guidance Fraud / Materiality:</strong> EPS surprise % shows management
      guidance accuracy. Consistent beats suggest conservative guidance (good). Misses trigger
      10b-5 class actions. Bar height = surprise magnitude, color = beat/miss.
    </div>
    <span class="lib-tag">ECharts</span>
    <div class="chart-container" id="ec-earnings-chart" style="height:400px;"></div>
  </div>

  <!-- 7. DDL Exposure -->
  <div class="chart-card" id="ec-ddl">
    <h3>7. Dollar Damages Line (DDL) Exposure</h3>
    <div class="do-relevance">
      <strong>D&O Relevance — Severity / Limits Adequacy:</strong> The DDL represents the maximum
      shareholder loss from peak-to-trough. This is the starting point for damages calculation in
      any securities class action. Peak DDL x retention rate = potential settlement exposure.
      Underwriters use this to size tower limits.
    </div>
    <span class="lib-tag">ECharts</span>
    <div class="chart-container" id="ec-ddl-chart" style="height:400px;"></div>
  </div>

  <!-- 13. Significant Drops -->
  <div class="chart-card" id="ec-drops">
    <h3>13. Significant Stock Drops Analysis (&gt;10%)</h3>
    <div class="do-relevance">
      <strong>D&O Relevance — Corrective Disclosure:</strong> Each &gt;10% drop is a potential
      class period ending date. Plaintiffs identify the corrective disclosure that triggered the
      drop. If the drop coincides with earnings miss, restatement, or regulatory action, it
      significantly strengthens the claim. Market-wide drops are defensible; company-specific are not.
    </div>
    <span class="lib-tag">ECharts</span>
    <div class="chart-container" id="ec-drops-chart" style="height:450px;"></div>
  </div>

  <!-- 14. Volatility Profile -->
  <div class="chart-card" id="ec-vol">
    <h3>14. Volatility Profile (30-Day Rolling vs Sector)</h3>
    <div class="do-relevance">
      <strong>D&O Relevance — Pricing / Frequency:</strong> Higher volatility = higher probability
      of triggering DDL thresholds. Volatility spikes around events indicate market uncertainty.
      Sustained high vol vs sector suggests company-specific risk factors. Used directly in
      D&O pricing models.
    </div>
    <span class="lib-tag">ECharts</span>
    <div class="chart-container" id="ec-vol-chart" style="height:400px;"></div>
  </div>
</div>

<!-- ================================================================== -->
<!-- SECTION 3: Chart.js -->
<!-- ================================================================== -->
<div class="lib-section">
  <div class="lib-header">
    <h2>Chart.js</h2>
    <span class="lib-badge badge-chartjs">Chart.js</span>
  </div>

  <!-- 8. Risk Factor Radar -->
  <div class="chart-card" id="cj-radar">
    <h3>8. Risk Factor Radar — 10-Factor D&O Scoring</h3>
    <div class="do-relevance">
      <strong>D&O Relevance — Risk Profile:</strong> Spider chart showing how each of 10 risk
      factors contributes to the overall D&O risk score. Factors at the perimeter = high risk.
      Allows underwriters to immediately see which risk dimensions are elevated.
      Score: {scoring.get("composite_score", 0):.1f}/100 ({scoring.get("tier", {}).get("tier", "N/A")}).
    </div>
    <span class="lib-tag">Chart.js</span>
    <div class="chart-container" id="cj-radar-chart" style="height:450px;"><canvas id="radar-canvas"></canvas></div>
  </div>

  <!-- 9. Probability Decomposition -->
  <div class="chart-card" id="cj-prob">
    <h3>9. Claim Probability Decomposition</h3>
    <div class="do-relevance">
      <strong>D&O Relevance — Pricing:</strong> Breaks down the claim probability into component
      risk factors. Each bar segment represents one factor's contribution. Total bar = overall
      claim probability estimate. Used to justify premium loading on specific risk dimensions.
    </div>
    <span class="lib-tag">Chart.js</span>
    <div class="chart-container" id="cj-prob-chart" style="height:300px;"><canvas id="prob-canvas"></canvas></div>
  </div>

  <!-- 10. Financial Dashboard -->
  <div class="chart-card" id="cj-fin">
    <h3>10. Financial Health Dashboard — 5-Year Trends</h3>
    <div class="do-relevance">
      <strong>D&O Relevance — Going Concern / Financial Distress:</strong> Revenue decline, margin
      compression, debt accumulation, and cash burn signal financial distress — a leading indicator
      for D&O claims. Factor F8 (Financial Distress) uses these metrics. Altman Z &lt; 1.81 = danger zone.
    </div>
    <span class="lib-tag">Chart.js</span>
    <div class="chart-container" id="cj-fin-chart" style="min-height:500px;">
      <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">
        <div><canvas id="fin-revenue"></canvas></div>
        <div><canvas id="fin-net-income"></canvas></div>
        <div><canvas id="fin-gross-margin"></canvas></div>
        <div><canvas id="fin-net-margin"></canvas></div>
        <div><canvas id="fin-debt-equity"></canvas></div>
        <div><canvas id="fin-total-debt"></canvas></div>
      </div>
    </div>
  </div>

  <!-- 15. Governance Risk Radar -->
  <div class="chart-card" id="cj-gov">
    <h3>15. Governance Risk Radar (ISS Scores)</h3>
    <div class="do-relevance">
      <strong>D&O Relevance — Fiduciary Duty / Board Quality:</strong> ISS governance risk scores
      (1=low risk, 10=high risk) across audit, board, compensation, and shareholder rights.
      High compensation risk ({gov_scores.get("compensationRisk", "N/A")}/10) may indicate excessive pay
      that draws derivative suits. Overall risk: {gov_scores.get("overallRisk", "N/A")}/10.
    </div>
    <span class="lib-tag">Chart.js</span>
    <div class="chart-container" id="cj-gov-chart" style="height:400px;"><canvas id="gov-canvas"></canvas></div>
  </div>
</div>

<!-- ================================================================== -->
<!-- SECTION 4: D3.js -->
<!-- ================================================================== -->
<div class="lib-section">
  <div class="lib-header">
    <h2>D3.js</h2>
    <span class="lib-badge badge-d3">D3.js</span>
  </div>

  <!-- 11. Suspicious Trading Windows -->
  <div class="chart-card" id="d3-suspicious">
    <h3>11. Suspicious Trading Windows — The Smoking Gun Chart</h3>
    <div class="do-relevance">
      <strong>D&O Relevance — Scienter / Insider Trading:</strong> This is the single most important
      chart for D&O underwriting. It overlays insider sales on the price chart with 30-day shaded
      windows before every &gt;5% drop. Insider sales inside these windows are the primary evidence
      plaintiffs use to establish scienter (guilty knowledge). {len([w for w in suspicious_windows if w["total_value"] > 0])}
      windows contain insider activity totaling
      ${sum(w["total_value"] for w in suspicious_windows) / 1e6:.1f}M.
    </div>
    <span class="lib-tag">D3.js</span>
    <div class="chart-container d3-chart" id="d3-suspicious-chart" style="height:500px;"></div>
  </div>

  <!-- 12. Market Cap Waterfall -->
  <div class="chart-card" id="d3-waterfall">
    <h3>12. Quarterly Market Cap Waterfall</h3>
    <div class="do-relevance">
      <strong>D&O Relevance — Severity / Damages:</strong> Shows market cap gains and losses by
      quarter. Large quarterly losses = potential class period boundaries. Cumulative market cap
      trajectory determines maximum DDL exposure. Underwriters use this to assess whether limits
      are adequate relative to the risk.
    </div>
    <span class="lib-tag">D3.js</span>
    <div class="chart-container d3-chart" id="d3-waterfall-chart" style="height:450px;"></div>
  </div>
</div>

<!-- ================================================================== -->
<!-- SECTION 5: Matplotlib -->
<!-- ================================================================== -->
<div class="lib-section">
  <div class="lib-header">
    <h2>Matplotlib</h2>
    <span class="lib-badge badge-mpl">Matplotlib / Python</span>
  </div>

  <div class="chart-card" id="mpl-perf">
    <h3>16. Best Performance Chart — 300 DPI Publication Quality</h3>
    <div class="do-relevance">
      <strong>D&O Relevance — Full Context:</strong> Combines price performance vs benchmarks,
      earnings event markers, and insider trade markers in a single view. The definitive chart
      for underwriting submissions and meeting decks. 300 DPI for print quality.
    </div>
    <span class="lib-tag">Matplotlib (Python)</span>
    <div class="chart-container" style="text-align:center;">
      {"<img src='data:image/png;base64," + mpl_b64 + "' style='max-width:100%; border-radius:8px;' />" if mpl_b64 else '<div class="na-notice">Matplotlib not available — install with: uv pip install matplotlib</div>'}
    </div>
  </div>
</div>

<!-- ================================================================== -->
<!-- JavaScript: Build all charts -->
<!-- ================================================================== -->
<script>
// Utility
function parseDate(s) {{
  if (!s) return null;
  return s.substring(0, 10);
}}

// ================================================================
// 1. LIGHTWEIGHT CHARTS
// ================================================================

// --- 5-Year Area Chart ---
(function() {{
  const container = document.getElementById('lw-area5y-chart');
  const chart = LightweightCharts.createChart(container, {{
    width: container.clientWidth,
    height: 500,
    layout: {{ background: {{ type: 'solid', color: '#1a1d29' }}, textColor: '#8b8fa3' }},
    grid: {{ vertLines: {{ color: '#2a2d3a' }}, horzLines: {{ color: '#2a2d3a' }} }},
    timeScale: {{ borderColor: '#2a2d3a', timeVisible: false }},
    rightPriceScale: {{ borderColor: '#2a2d3a' }},
    crosshair: {{ mode: LightweightCharts.CrosshairMode.Normal }},
  }});

  const d = DATA.h5_weekly;
  // Area series with color based on direction
  const areaSeries = chart.addAreaSeries({{
    topColor: 'rgba(79, 195, 247, 0.3)',
    bottomColor: 'rgba(79, 195, 247, 0.02)',
    lineColor: '#4fc3f7',
    lineWidth: 2,
  }});
  const areaData = d.dates.map((dt, i) => ({{ time: dt, value: d.close[i] }}));
  areaSeries.setData(areaData);

  // Volume
  const volSeries = chart.addHistogramSeries({{
    priceFormat: {{ type: 'volume' }},
    priceScaleId: 'vol',
  }});
  chart.priceScale('vol').applyOptions({{
    scaleMargins: {{ top: 0.85, bottom: 0 }},
  }});
  const volData = d.dates.map((dt, i) => ({{
    time: dt,
    value: d.volume[i],
    color: (i > 0 && d.close[i] >= d.close[i-1]) ? 'rgba(102,187,106,0.4)' : 'rgba(239,83,80,0.4)',
  }}));
  volSeries.setData(volData);

  chart.timeScale().fitContent();
  new ResizeObserver(() => chart.applyOptions({{ width: container.clientWidth }})).observe(container);
}})();

// --- 2-Year with Earnings Markers ---
(function() {{
  const container = document.getElementById('lw-earnings-chart');
  const chart = LightweightCharts.createChart(container, {{
    width: container.clientWidth,
    height: 500,
    layout: {{ background: {{ type: 'solid', color: '#1a1d29' }}, textColor: '#8b8fa3' }},
    grid: {{ vertLines: {{ color: '#2a2d3a' }}, horzLines: {{ color: '#2a2d3a' }} }},
    timeScale: {{ borderColor: '#2a2d3a' }},
    rightPriceScale: {{ borderColor: '#2a2d3a' }},
  }});

  const d = DATA.h2;
  const lineSeries = chart.addLineSeries({{
    color: '#4fc3f7',
    lineWidth: 2,
  }});
  const lineData = d.dates.map((dt, i) => ({{ time: dt, value: d.close[i] }}));
  lineSeries.setData(lineData);

  // Volume
  const volSeries = chart.addHistogramSeries({{
    priceFormat: {{ type: 'volume' }},
    priceScaleId: 'vol',
  }});
  chart.priceScale('vol').applyOptions({{
    scaleMargins: {{ top: 0.85, bottom: 0 }},
  }});
  const volData = d.dates.map((dt, i) => ({{
    time: dt,
    value: d.volume[i],
    color: (i > 0 && d.close[i] >= d.close[i-1]) ? 'rgba(102,187,106,0.3)' : 'rgba(239,83,80,0.3)',
  }}));
  volSeries.setData(volData);

  // Earnings markers
  const markers = [];
  DATA.earnings.forEach(e => {{
    const dt = parseDate(e.date);
    if (!dt) return;
    // Check if in range
    if (dt < d.dates[0] || dt > d.dates[d.dates.length - 1]) return;
    const isBeat = e.surprise >= 0;
    markers.push({{
      time: dt,
      position: isBeat ? 'belowBar' : 'aboveBar',
      color: isBeat ? '#66bb6a' : '#ef5350',
      shape: isBeat ? 'arrowUp' : 'arrowDown',
      text: (e.surprise >= 0 ? '+' : '') + e.surprise.toFixed(1) + '%',
    }});
  }});
  markers.sort((a, b) => a.time < b.time ? -1 : 1);
  lineSeries.setMarkers(markers);

  chart.timeScale().fitContent();
  new ResizeObserver(() => chart.applyOptions({{ width: container.clientWidth }})).observe(container);
}})();

// --- 6-Month Candlestick ---
(function() {{
  const container = document.getElementById('lw-candle-chart');
  const chart = LightweightCharts.createChart(container, {{
    width: container.clientWidth,
    height: 500,
    layout: {{ background: {{ type: 'solid', color: '#1a1d29' }}, textColor: '#8b8fa3' }},
    grid: {{ vertLines: {{ color: '#2a2d3a' }}, horzLines: {{ color: '#2a2d3a' }} }},
    timeScale: {{ borderColor: '#2a2d3a' }},
    rightPriceScale: {{ borderColor: '#2a2d3a' }},
  }});

  const d = DATA.h6m;
  const candleSeries = chart.addCandlestickSeries({{
    upColor: '#66bb6a',
    downColor: '#ef5350',
    borderDownColor: '#ef5350',
    borderUpColor: '#66bb6a',
    wickDownColor: '#ef5350',
    wickUpColor: '#66bb6a',
  }});
  const candleData = d.dates.map((dt, i) => ({{
    time: dt,
    open: d.open[i],
    high: d.high[i],
    low: d.low[i],
    close: d.close[i],
  }}));
  candleSeries.setData(candleData);

  // Volume
  const volSeries = chart.addHistogramSeries({{
    priceFormat: {{ type: 'volume' }},
    priceScaleId: 'vol',
  }});
  chart.priceScale('vol').applyOptions({{
    scaleMargins: {{ top: 0.85, bottom: 0 }},
  }});
  const volData = d.dates.map((dt, i) => ({{
    time: dt,
    value: d.volume[i],
    color: d.close[i] >= d.open[i] ? 'rgba(102,187,106,0.4)' : 'rgba(239,83,80,0.4)',
  }}));
  volSeries.setData(volData);

  chart.timeScale().fitContent();
  new ResizeObserver(() => chart.applyOptions({{ width: container.clientWidth }})).observe(container);
}})();

// ================================================================
// 2. ECHARTS
// ================================================================

// --- Performance Comparison ---
(function() {{
  const el = document.getElementById('ec-perf-chart');
  const chart = echarts.init(el, null, {{ renderer: 'canvas' }});
  const d = DATA.perf;
  // Sample every 5th point for smoother rendering
  const step = 3;
  const dates = d.dates.filter((_, i) => i % step === 0);
  const aapl = d.aapl.filter((_, i) => i % step === 0);
  const sector = d.sector.filter((_, i) => i % step === 0);
  const spy = d.spy.filter((_, i) => i % step === 0);

  chart.setOption({{
    backgroundColor: '#1a1d29',
    tooltip: {{
      trigger: 'axis',
      backgroundColor: '#2a2d3a',
      borderColor: '#3a3d4a',
      textStyle: {{ color: '#c8ccd8', fontSize: 12 }},
      formatter: function(params) {{
        let s = params[0].axisValue + '<br/>';
        params.forEach(p => {{
          s += p.marker + ' ' + p.seriesName + ': <b>' + p.value.toFixed(1) + '%</b><br/>';
        }});
        return s;
      }},
    }},
    legend: {{
      data: ['AAPL', 'Sector ETF', 'S&P 500'],
      textStyle: {{ color: '#8b8fa3' }},
      top: 10,
    }},
    grid: {{ left: 60, right: 30, top: 50, bottom: 40 }},
    xAxis: {{
      type: 'category',
      data: dates,
      axisLabel: {{ color: '#8b8fa3', fontSize: 10, rotate: 0,
        formatter: v => v.substring(0,7) }},
      axisLine: {{ lineStyle: {{ color: '#2a2d3a' }} }},
      splitLine: {{ show: false }},
    }},
    yAxis: {{
      type: 'value',
      axisLabel: {{ color: '#8b8fa3', formatter: '{{value}}%' }},
      axisLine: {{ lineStyle: {{ color: '#2a2d3a' }} }},
      splitLine: {{ lineStyle: {{ color: '#2a2d3a', type: 'dashed' }} }},
    }},
    series: [
      {{
        name: 'AAPL', type: 'line', data: aapl, smooth: true, lineStyle: {{ width: 2.5 }},
        itemStyle: {{ color: '#4fc3f7' }},
        areaStyle: {{ color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          {{ offset: 0, color: 'rgba(79,195,247,0.3)' }}, {{ offset: 1, color: 'rgba(79,195,247,0.02)' }}
        ]) }},
        symbol: 'none',
      }},
      {{
        name: 'Sector ETF', type: 'line', data: sector, smooth: true,
        lineStyle: {{ width: 1.5, type: 'dashed' }}, itemStyle: {{ color: '#ff9800' }}, symbol: 'none',
      }},
      {{
        name: 'S&P 500', type: 'line', data: spy, smooth: true,
        lineStyle: {{ width: 1.5, type: 'dashed' }}, itemStyle: {{ color: '#66bb6a' }}, symbol: 'none',
      }},
    ],
  }});
  new ResizeObserver(() => chart.resize()).observe(el);
}})();

// --- Insider Activity Timeline ---
(function() {{
  const el = document.getElementById('ec-insider-chart');
  const chart = echarts.init(el, null, {{ renderer: 'canvas' }});
  const d = DATA.h2;
  const ins = DATA.insiders;

  // Price line data
  const step = 2;
  const dates = d.dates.filter((_, i) => i % step === 0);
  const closes = d.close.filter((_, i) => i % step === 0);

  // Insider scatter — find closest price for each insider trade
  const insiderPoints = ins.map(t => {{
    let closestIdx = 0;
    let minDist = Infinity;
    for (let i = 0; i < d.dates.length; i++) {{
      const dist = Math.abs(new Date(d.dates[i]) - new Date(t.date));
      if (dist < minDist) {{ minDist = dist; closestIdx = i; }}
    }}
    return {{
      value: [t.date, d.close[closestIdx]],
      symbolSize: Math.max(8, Math.min(30, Math.sqrt(t.value / 500000))),
      insider: t.insider,
      tradeValue: t.value,
      shares: t.shares,
    }};
  }});

  chart.setOption({{
    backgroundColor: '#1a1d29',
    tooltip: {{
      trigger: 'item',
      backgroundColor: '#2a2d3a',
      borderColor: '#3a3d4a',
      textStyle: {{ color: '#c8ccd8', fontSize: 12 }},
    }},
    legend: {{
      data: ['AAPL Price', 'Insider Sales'],
      textStyle: {{ color: '#8b8fa3' }},
      top: 10,
    }},
    grid: {{ left: 60, right: 30, top: 50, bottom: 40 }},
    xAxis: {{
      type: 'category',
      data: dates,
      axisLabel: {{ color: '#8b8fa3', fontSize: 10, formatter: v => v.substring(0,7) }},
      axisLine: {{ lineStyle: {{ color: '#2a2d3a' }} }},
    }},
    yAxis: {{
      type: 'value',
      axisLabel: {{ color: '#8b8fa3', formatter: '${{value}}' }},
      axisLine: {{ lineStyle: {{ color: '#2a2d3a' }} }},
      splitLine: {{ lineStyle: {{ color: '#2a2d3a', type: 'dashed' }} }},
    }},
    series: [
      {{
        name: 'AAPL Price', type: 'line', data: closes, smooth: true,
        lineStyle: {{ width: 2, color: '#4fc3f7' }}, itemStyle: {{ color: '#4fc3f7' }},
        symbol: 'none',
        areaStyle: {{ color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          {{ offset: 0, color: 'rgba(79,195,247,0.15)' }}, {{ offset: 1, color: 'rgba(79,195,247,0.01)' }}
        ]) }},
      }},
      {{
        name: 'Insider Sales', type: 'scatter',
        data: insiderPoints,
        itemStyle: {{ color: '#ef5350', borderColor: '#fff', borderWidth: 1 }},
        tooltip: {{
          formatter: function(p) {{
            const d = p.data;
            return '<b>' + d.insider + '</b><br/>' +
              'Date: ' + d.value[0] + '<br/>' +
              'Price: $' + d.value[1].toFixed(2) + '<br/>' +
              'Shares: ' + d.shares.toLocaleString() + '<br/>' +
              'Value: $' + (d.tradeValue / 1e6).toFixed(1) + 'M';
          }},
        }},
      }},
    ],
  }});
  new ResizeObserver(() => chart.resize()).observe(el);
}})();

// --- Earnings Reaction ---
(function() {{
  const el = document.getElementById('ec-earnings-chart');
  const chart = echarts.init(el, null, {{ renderer: 'canvas' }});
  const e = DATA.earnings.filter(x => x.surprise !== null).reverse();

  chart.setOption({{
    backgroundColor: '#1a1d29',
    tooltip: {{
      trigger: 'axis',
      backgroundColor: '#2a2d3a',
      borderColor: '#3a3d4a',
      textStyle: {{ color: '#c8ccd8' }},
      formatter: function(params) {{
        const p = params[0];
        const d = e[p.dataIndex];
        return '<b>' + d.date.substring(0,10) + '</b><br/>' +
          'EPS Estimate: $' + d.estimate.toFixed(2) + '<br/>' +
          'Reported EPS: $' + d.reported.toFixed(2) + '<br/>' +
          'Surprise: ' + (d.surprise >= 0 ? '+' : '') + d.surprise.toFixed(1) + '%';
      }},
    }},
    grid: {{ left: 60, right: 30, top: 30, bottom: 60 }},
    xAxis: {{
      type: 'category',
      data: e.map(x => x.date.substring(0,10)),
      axisLabel: {{ color: '#8b8fa3', fontSize: 10, rotate: 45 }},
      axisLine: {{ lineStyle: {{ color: '#2a2d3a' }} }},
    }},
    yAxis: {{
      type: 'value',
      name: 'Surprise %',
      nameTextStyle: {{ color: '#8b8fa3' }},
      axisLabel: {{ color: '#8b8fa3', formatter: '{{value}}%' }},
      axisLine: {{ lineStyle: {{ color: '#2a2d3a' }} }},
      splitLine: {{ lineStyle: {{ color: '#2a2d3a', type: 'dashed' }} }},
    }},
    series: [{{
      type: 'bar',
      data: e.map(x => ({{
        value: x.surprise,
        itemStyle: {{ color: x.surprise >= 0 ? '#66bb6a' : '#ef5350' }},
      }})),
      barWidth: '60%',
      label: {{
        show: true,
        position: 'top',
        formatter: p => (p.value >= 0 ? '+' : '') + p.value.toFixed(1) + '%',
        color: '#8b8fa3',
        fontSize: 10,
      }},
    }}],
  }});
  new ResizeObserver(() => chart.resize()).observe(el);
}})();

// --- DDL Exposure ---
(function() {{
  const el = document.getElementById('ec-ddl-chart');
  const chart = echarts.init(el, null, {{ renderer: 'canvas' }});
  const d = DATA.ddl;
  const step = 3;
  const dates = d.dates.filter((_, i) => i % step === 0);
  const vals = d.values.filter((_, i) => i % step === 0);

  chart.setOption({{
    backgroundColor: '#1a1d29',
    tooltip: {{
      trigger: 'axis',
      backgroundColor: '#2a2d3a',
      borderColor: '#3a3d4a',
      textStyle: {{ color: '#c8ccd8' }},
      formatter: p => p[0].axisValue + '<br/>DDL Exposure: <b>$' + p[0].value.toFixed(1) + 'B</b>',
    }},
    grid: {{ left: 80, right: 30, top: 30, bottom: 40 }},
    xAxis: {{
      type: 'category',
      data: dates,
      axisLabel: {{ color: '#8b8fa3', fontSize: 10, formatter: v => v.substring(0,7) }},
      axisLine: {{ lineStyle: {{ color: '#2a2d3a' }} }},
    }},
    yAxis: {{
      type: 'value',
      name: 'DDL ($B)',
      nameTextStyle: {{ color: '#8b8fa3' }},
      axisLabel: {{ color: '#8b8fa3', formatter: '${{value}}B' }},
      axisLine: {{ lineStyle: {{ color: '#2a2d3a' }} }},
      splitLine: {{ lineStyle: {{ color: '#2a2d3a', type: 'dashed' }} }},
    }},
    series: [{{
      type: 'line',
      data: vals,
      smooth: true,
      lineStyle: {{ width: 2, color: '#ef5350' }},
      itemStyle: {{ color: '#ef5350' }},
      symbol: 'none',
      areaStyle: {{
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          {{ offset: 0, color: 'rgba(239,83,80,0.4)' }},
          {{ offset: 1, color: 'rgba(239,83,80,0.02)' }},
        ]),
      }},
      markLine: {{
        data: [{{ type: 'max', name: 'Peak DDL' }}],
        label: {{ formatter: p => '$' + p.value.toFixed(1) + 'B', color: '#ef5350' }},
        lineStyle: {{ color: '#ef5350', type: 'dashed' }},
      }},
    }}],
  }});
  new ResizeObserver(() => chart.resize()).observe(el);
}})();

// --- Significant Drops ---
(function() {{
  const el = document.getElementById('ec-drops-chart');
  const chart = echarts.init(el, null, {{ renderer: 'canvas' }});
  const d = DATA.h2;
  const drops = DATA.sig_drops;

  const step = 2;
  const dates = d.dates.filter((_, i) => i % step === 0);
  const closes = d.close.filter((_, i) => i % step === 0);

  // Mark areas for each drop
  const markAreas = drops.map(drop => [
    {{ xAxis: drop.peak_date, itemStyle: {{ color: 'rgba(239,83,80,0.1)' }} }},
    {{ xAxis: drop.trough_date }},
  ]);

  const markPoints = drops.map(drop => ({{
    coord: [drop.trough_date, drop.trough_price],
    value: drop.drop_pct + '%',
    symbol: 'pin',
    symbolSize: 40,
    itemStyle: {{ color: '#ef5350' }},
    label: {{ color: '#fff', fontSize: 10 }},
  }}));

  chart.setOption({{
    backgroundColor: '#1a1d29',
    tooltip: {{
      trigger: 'axis',
      backgroundColor: '#2a2d3a',
      borderColor: '#3a3d4a',
      textStyle: {{ color: '#c8ccd8' }},
    }},
    grid: {{ left: 60, right: 30, top: 30, bottom: 40 }},
    xAxis: {{
      type: 'category',
      data: dates,
      axisLabel: {{ color: '#8b8fa3', fontSize: 10, formatter: v => v.substring(0,7) }},
      axisLine: {{ lineStyle: {{ color: '#2a2d3a' }} }},
    }},
    yAxis: {{
      type: 'value',
      axisLabel: {{ color: '#8b8fa3', formatter: '${{value}}' }},
      axisLine: {{ lineStyle: {{ color: '#2a2d3a' }} }},
      splitLine: {{ lineStyle: {{ color: '#2a2d3a', type: 'dashed' }} }},
    }},
    series: [{{
      type: 'line',
      data: closes,
      smooth: true,
      lineStyle: {{ width: 2, color: '#4fc3f7' }},
      itemStyle: {{ color: '#4fc3f7' }},
      symbol: 'none',
      markArea: {{ data: markAreas }},
      markPoint: {{ data: markPoints }},
    }}],
  }});
  new ResizeObserver(() => chart.resize()).observe(el);
}})();

// --- Volatility Profile ---
(function() {{
  const el = document.getElementById('ec-vol-chart');
  const chart = echarts.init(el, null, {{ renderer: 'canvas' }});
  const d = DATA.volatility;
  const step = 3;
  const dates = d.dates.filter((_, i) => i % step === 0);
  const aapl = d.aapl.filter((_, i) => i % step === 0);
  const sector = d.sector.filter((_, i) => i % step === 0);

  chart.setOption({{
    backgroundColor: '#1a1d29',
    tooltip: {{
      trigger: 'axis',
      backgroundColor: '#2a2d3a',
      borderColor: '#3a3d4a',
      textStyle: {{ color: '#c8ccd8' }},
      formatter: function(params) {{
        let s = params[0].axisValue + '<br/>';
        params.forEach(p => {{
          if (p.value != null) s += p.marker + ' ' + p.seriesName + ': <b>' + p.value.toFixed(2) + '%</b><br/>';
        }});
        return s;
      }},
    }},
    legend: {{
      data: ['AAPL Volatility', 'Sector Volatility'],
      textStyle: {{ color: '#8b8fa3' }},
      top: 10,
    }},
    grid: {{ left: 60, right: 30, top: 50, bottom: 40 }},
    xAxis: {{
      type: 'category',
      data: dates,
      axisLabel: {{ color: '#8b8fa3', fontSize: 10, formatter: v => v.substring(0,7) }},
      axisLine: {{ lineStyle: {{ color: '#2a2d3a' }} }},
    }},
    yAxis: {{
      type: 'value',
      name: '30-Day Vol (%)',
      nameTextStyle: {{ color: '#8b8fa3' }},
      axisLabel: {{ color: '#8b8fa3', formatter: '{{value}}%' }},
      axisLine: {{ lineStyle: {{ color: '#2a2d3a' }} }},
      splitLine: {{ lineStyle: {{ color: '#2a2d3a', type: 'dashed' }} }},
    }},
    series: [
      {{
        name: 'AAPL Volatility', type: 'line', data: aapl, smooth: true,
        lineStyle: {{ width: 2, color: '#4fc3f7' }}, itemStyle: {{ color: '#4fc3f7' }}, symbol: 'none',
        areaStyle: {{ color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          {{ offset: 0, color: 'rgba(79,195,247,0.2)' }}, {{ offset: 1, color: 'rgba(79,195,247,0.01)' }}
        ]) }},
      }},
      {{
        name: 'Sector Volatility', type: 'line', data: sector, smooth: true,
        lineStyle: {{ width: 1.5, color: '#ff9800', type: 'dashed' }},
        itemStyle: {{ color: '#ff9800' }}, symbol: 'none',
      }},
    ],
  }});
  new ResizeObserver(() => chart.resize()).observe(el);
}})();

// ================================================================
// 3. CHART.JS
// ================================================================

// --- Risk Factor Radar ---
(function() {{
  const ctx = document.getElementById('radar-canvas').getContext('2d');
  const f = DATA.factors;
  new Chart(ctx, {{
    type: 'radar',
    data: {{
      labels: f.map(x => x.id + ' ' + x.name),
      datasets: [{{
        label: 'Risk % (points deducted / max)',
        data: f.map(x => x.pct),
        backgroundColor: 'rgba(79, 195, 247, 0.2)',
        borderColor: '#4fc3f7',
        borderWidth: 2,
        pointBackgroundColor: f.map(x => x.pct > 50 ? '#ef5350' : x.pct > 25 ? '#ff9800' : '#66bb6a'),
        pointBorderColor: '#fff',
        pointRadius: 5,
      }}, {{
        label: 'Max Exposure (100%)',
        data: f.map(() => 100),
        backgroundColor: 'rgba(239, 83, 80, 0.05)',
        borderColor: 'rgba(239, 83, 80, 0.3)',
        borderWidth: 1,
        borderDash: [5, 5],
        pointRadius: 0,
      }}],
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        legend: {{
          labels: {{ color: '#8b8fa3' }},
        }},
        tooltip: {{
          callbacks: {{
            label: function(ctx) {{
              const i = ctx.dataIndex;
              const d = f[i];
              return d.id + ': ' + d.deducted + '/' + d.max + ' pts (' + d.pct + '%)';
            }},
          }},
        }},
      }},
      scales: {{
        r: {{
          beginAtZero: true,
          max: 100,
          ticks: {{ color: '#8b8fa3', backdropColor: 'transparent', stepSize: 25 }},
          grid: {{ color: '#2a2d3a' }},
          angleLines: {{ color: '#2a2d3a' }},
          pointLabels: {{
            color: '#c8ccd8',
            font: {{ size: 11 }},
          }},
        }},
      }},
    }},
  }});
}})();

// --- Probability Decomposition ---
(function() {{
  const ctx = document.getElementById('prob-canvas').getContext('2d');
  const f = DATA.factors;
  const total = f.reduce((s, x) => s + x.deducted, 0);
  const colors = [
    '#ef5350', '#ff7043', '#ff9800', '#ffc107', '#66bb6a',
    '#4fc3f7', '#ab47bc', '#7e57c2', '#26a69a', '#78909c',
  ];

  new Chart(ctx, {{
    type: 'bar',
    data: {{
      labels: ['D&O Risk Decomposition'],
      datasets: f.map((x, i) => ({{
        label: x.id + ' ' + x.name + ' (' + x.deducted + 'pts)',
        data: [x.deducted],
        backgroundColor: colors[i],
        borderWidth: 0,
      }})),
    }},
    options: {{
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        legend: {{
          position: 'bottom',
          labels: {{ color: '#8b8fa3', font: {{ size: 10 }}, boxWidth: 12, padding: 8 }},
        }},
        tooltip: {{
          callbacks: {{
            label: ctx => ctx.dataset.label,
          }},
        }},
      }},
      scales: {{
        x: {{
          stacked: true,
          ticks: {{ color: '#8b8fa3' }},
          grid: {{ color: '#2a2d3a' }},
          title: {{ display: true, text: 'Risk Points Deducted', color: '#8b8fa3' }},
        }},
        y: {{
          stacked: true,
          ticks: {{ color: '#8b8fa3' }},
          grid: {{ display: false }},
        }},
      }},
    }},
  }});
}})();

// --- Financial Dashboard (6 small charts) ---
(function() {{
  const fm = DATA.financials;
  const periods = fm.periods.slice().reverse();

  function makeSmallChart(canvasId, label, data, color, format) {{
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    const vals = data.slice().reverse();
    new Chart(ctx.getContext('2d'), {{
      type: 'bar',
      data: {{
        labels: periods,
        datasets: [{{
          label: label,
          data: vals,
          backgroundColor: color + '80',
          borderColor: color,
          borderWidth: 1,
          borderRadius: 3,
        }}],
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: true,
        plugins: {{
          legend: {{ display: false }},
          title: {{ display: true, text: label, color: '#c8ccd8', font: {{ size: 13 }} }},
          tooltip: {{
            callbacks: {{
              label: ctx => {{
                const v = ctx.raw;
                if (format === 'B') return '$' + (v / 1e9).toFixed(1) + 'B';
                if (format === '%') return v.toFixed(1) + '%';
                if (format === 'x') return v.toFixed(2) + 'x';
                return v;
              }},
            }},
          }},
        }},
        scales: {{
          x: {{ ticks: {{ color: '#8b8fa3' }}, grid: {{ display: false }} }},
          y: {{
            ticks: {{
              color: '#8b8fa3',
              callback: function(v) {{
                if (format === 'B') return '$' + (v / 1e9).toFixed(0) + 'B';
                if (format === '%') return v + '%';
                if (format === 'x') return v + 'x';
                return v;
              }},
            }},
            grid: {{ color: '#2a2d3a' }},
          }},
        }},
      }},
    }});
  }}

  makeSmallChart('fin-revenue', 'Revenue', fm.revenue, '#4fc3f7', 'B');
  makeSmallChart('fin-net-income', 'Net Income', fm.net_income, '#66bb6a', 'B');
  makeSmallChart('fin-gross-margin', 'Gross Margin', fm.gross_margin, '#ff9800', '%');
  makeSmallChart('fin-net-margin', 'Net Margin', fm.net_margin, '#ab47bc', '%');
  makeSmallChart('fin-debt-equity', 'Debt / Equity', fm.debt_to_equity, '#ef5350', 'x');
  makeSmallChart('fin-total-debt', 'Total Debt', fm.total_debt, '#78909c', 'B');
}})();

// --- Governance Risk Radar ---
(function() {{
  const ctx = document.getElementById('gov-canvas').getContext('2d');
  const g = DATA.governance;
  const labels = ['Audit Risk', 'Board Risk', 'Compensation Risk', 'Shareholder Rights', 'Overall Risk'];
  const values = [g.audit_risk, g.board_risk, g.compensation_risk, g.shareholder_rights_risk, g.overall_risk];

  new Chart(ctx, {{
    type: 'radar',
    data: {{
      labels: labels,
      datasets: [{{
        label: 'ISS Governance Score (1=Low, 10=High Risk)',
        data: values,
        backgroundColor: 'rgba(171, 71, 188, 0.2)',
        borderColor: '#ab47bc',
        borderWidth: 2,
        pointBackgroundColor: values.map(v => v >= 7 ? '#ef5350' : v >= 4 ? '#ff9800' : '#66bb6a'),
        pointBorderColor: '#fff',
        pointRadius: 6,
      }}],
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        legend: {{
          labels: {{ color: '#8b8fa3' }},
        }},
      }},
      scales: {{
        r: {{
          beginAtZero: true,
          max: 10,
          ticks: {{ color: '#8b8fa3', backdropColor: 'transparent', stepSize: 2 }},
          grid: {{ color: '#2a2d3a' }},
          angleLines: {{ color: '#2a2d3a' }},
          pointLabels: {{ color: '#c8ccd8', font: {{ size: 13 }} }},
        }},
      }},
    }},
  }});
}})();

// ================================================================
// 4. D3.js
// ================================================================

// --- Suspicious Trading Windows ---
(function() {{
  const container = document.getElementById('d3-suspicious-chart');
  const margin = {{ top: 20, right: 30, bottom: 40, left: 70 }};
  const width = container.clientWidth - margin.left - margin.right;
  const height = 460 - margin.top - margin.bottom;

  const svg = d3.select(container).append('svg')
    .attr('width', width + margin.left + margin.right)
    .attr('height', height + margin.top + margin.bottom)
    .append('g')
    .attr('transform', `translate(${{margin.left}},${{margin.top}})`);

  const d = DATA.h2;
  const parseTime = d3.timeParse('%Y-%m-%d');
  const priceData = d.dates.map((dt, i) => ({{ date: parseTime(dt), close: d.close[i] }})).filter(x => x.date);

  const x = d3.scaleTime()
    .domain(d3.extent(priceData, p => p.date))
    .range([0, width]);

  const y = d3.scaleLinear()
    .domain([d3.min(priceData, p => p.close) * 0.95, d3.max(priceData, p => p.close) * 1.05])
    .range([height, 0]);

  // Axes
  svg.append('g')
    .attr('class', 'axis')
    .attr('transform', `translate(0,${{height}})`)
    .call(d3.axisBottom(x).ticks(8).tickFormat(d3.timeFormat('%b \'%y')));

  svg.append('g')
    .attr('class', 'axis')
    .call(d3.axisLeft(y).ticks(6).tickFormat(d => '$' + d.toFixed(0)));

  // Grid
  svg.selectAll('.hgrid')
    .data(y.ticks(6))
    .enter().append('line')
    .attr('x1', 0).attr('x2', width)
    .attr('y1', d => y(d)).attr('y2', d => y(d))
    .attr('stroke', '#2a2d3a').attr('stroke-dasharray', '3,3');

  // Suspicious windows (30-day shaded areas before drops)
  DATA.suspicious.forEach(w => {{
    const ws = parseTime(w.window_start);
    const we = parseTime(w.window_end);
    if (!ws || !we) return;
    const hasTrades = w.total_value > 0;
    svg.append('rect')
      .attr('x', x(ws))
      .attr('width', Math.max(1, x(we) - x(ws)))
      .attr('y', 0)
      .attr('height', height)
      .attr('fill', hasTrades ? 'rgba(239,83,80,0.15)' : 'rgba(255,152,0,0.08)')
      .attr('stroke', hasTrades ? '#ef5350' : 'none')
      .attr('stroke-width', hasTrades ? 1 : 0)
      .attr('stroke-dasharray', '4,4');
  }});

  // Price line
  const line = d3.line()
    .x(p => x(p.date))
    .y(p => y(p.close))
    .curve(d3.curveMonotoneX);

  svg.append('path')
    .datum(priceData.filter((_, i) => i % 2 === 0))
    .attr('fill', 'none')
    .attr('stroke', '#4fc3f7')
    .attr('stroke-width', 2)
    .attr('d', line);

  // Insider trade markers
  const ins = DATA.insiders;
  ins.forEach(t => {{
    const dt = parseTime(t.date);
    if (!dt) return;
    // Find closest price
    let closestPrice = 0;
    let minDist = Infinity;
    priceData.forEach(p => {{
      const dist = Math.abs(p.date - dt);
      if (dist < minDist) {{ minDist = dist; closestPrice = p.close; }}
    }});
    const r = Math.max(4, Math.min(15, Math.sqrt(t.value / 1e6) * 5));
    svg.append('circle')
      .attr('cx', x(dt))
      .attr('cy', y(closestPrice))
      .attr('r', r)
      .attr('fill', 'rgba(239,83,80,0.7)')
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5)
      .append('title')
      .text(t.insider + ': $' + (t.value / 1e6).toFixed(1) + 'M on ' + t.date);
  }});

  // Drop arrows
  DATA.sig_drops.forEach(drop => {{
    const dt = parseTime(drop.trough_date);
    if (!dt) return;
    svg.append('text')
      .attr('x', x(dt))
      .attr('y', y(drop.trough_price) + 20)
      .attr('text-anchor', 'middle')
      .attr('fill', '#ef5350')
      .attr('font-size', '11px')
      .attr('font-weight', 'bold')
      .text(drop.drop_pct + '%');
  }});

  // Legend
  const legend = svg.append('g').attr('transform', `translate(${{width - 250}}, 10)`);
  const items = [
    {{ color: '#4fc3f7', label: 'AAPL Price' }},
    {{ color: '#ef5350', label: 'Insider Sale (size = value)' }},
    {{ color: 'rgba(239,83,80,0.15)', label: 'Window with insider trades', type: 'rect' }},
    {{ color: 'rgba(255,152,0,0.08)', label: '30-day pre-drop window', type: 'rect' }},
  ];
  items.forEach((item, i) => {{
    if (item.type === 'rect') {{
      legend.append('rect').attr('x', 0).attr('y', i * 20).attr('width', 14).attr('height', 14)
        .attr('fill', item.color).attr('stroke', item.color === 'rgba(239,83,80,0.15)' ? '#ef5350' : 'none');
    }} else {{
      legend.append('circle').attr('cx', 7).attr('cy', i * 20 + 7).attr('r', 5).attr('fill', item.color);
    }}
    legend.append('text').attr('x', 20).attr('y', i * 20 + 12)
      .attr('fill', '#8b8fa3').attr('font-size', '11px').text(item.label);
  }});

  // Resize
  new ResizeObserver(() => {{
    const newWidth = container.clientWidth - margin.left - margin.right;
    d3.select(container).select('svg').attr('width', newWidth + margin.left + margin.right);
    x.range([0, newWidth]);
    // Simplified: full redraw would be needed for proper resize
  }}).observe(container);
}})();

// --- Market Cap Waterfall ---
(function() {{
  const container = document.getElementById('d3-waterfall-chart');
  const margin = {{ top: 20, right: 30, bottom: 60, left: 80 }};
  const width = container.clientWidth - margin.left - margin.right;
  const height = 410 - margin.top - margin.bottom;

  const svg = d3.select(container).append('svg')
    .attr('width', width + margin.left + margin.right)
    .attr('height', height + margin.top + margin.bottom)
    .append('g')
    .attr('transform', `translate(${{margin.left}},${{margin.top}})`);

  // Compute quarterly market caps from stock prices
  const d = DATA.h2;
  const parseTime = d3.timeParse('%Y-%m-%d');
  const mcap0 = DATA.info.marketCap;
  const sharesEst = mcap0 / d.close[d.close.length - 1];

  // Group by quarter
  const quarters = {{}};
  d.dates.forEach((dt, i) => {{
    const date = new Date(dt);
    const q = 'Q' + (Math.floor(date.getMonth() / 3) + 1) + ' ' + date.getFullYear();
    if (!quarters[q]) quarters[q] = [];
    quarters[q].push(d.close[i]);
  }});

  const qLabels = Object.keys(quarters);
  const qMcaps = qLabels.map(q => {{
    const prices = quarters[q];
    return prices[prices.length - 1] * sharesEst / 1e12; // in trillions
  }});

  // Waterfall: compute deltas
  const waterfall = [];
  for (let i = 0; i < qLabels.length; i++) {{
    const prev = i === 0 ? qMcaps[0] : qMcaps[i - 1];
    const delta = i === 0 ? 0 : qMcaps[i] - prev;
    const start = i === 0 ? 0 : waterfall[i - 1].end;
    waterfall.push({{
      label: qLabels[i],
      delta: delta,
      start: i === 0 ? 0 : (delta >= 0 ? start : start + delta),
      end: i === 0 ? qMcaps[0] : start + delta,
      value: qMcaps[i],
      isFirst: i === 0,
    }});
  }}

  const x = d3.scaleBand()
    .domain(qLabels)
    .range([0, width])
    .padding(0.3);

  const allVals = waterfall.flatMap(w => [w.start, w.end, w.value]);
  const y = d3.scaleLinear()
    .domain([Math.min(0, d3.min(allVals)) * 0.95, d3.max(allVals) * 1.05])
    .range([height, 0]);

  svg.append('g')
    .attr('class', 'axis')
    .attr('transform', `translate(0,${{height}})`)
    .call(d3.axisBottom(x))
    .selectAll('text')
    .attr('transform', 'rotate(-45)')
    .style('text-anchor', 'end');

  svg.append('g')
    .attr('class', 'axis')
    .call(d3.axisLeft(y).ticks(6).tickFormat(d => '$' + d.toFixed(1) + 'T'));

  // Grid
  svg.selectAll('.hgrid')
    .data(y.ticks(6))
    .enter().append('line')
    .attr('x1', 0).attr('x2', width)
    .attr('y1', d => y(d)).attr('y2', d => y(d))
    .attr('stroke', '#2a2d3a').attr('stroke-dasharray', '3,3');

  // Bars
  waterfall.forEach(w => {{
    const barHeight = Math.abs(y(0) - y(Math.abs(w.isFirst ? w.value : w.delta)));
    const barY = w.isFirst
      ? y(w.value)
      : (w.delta >= 0 ? y(w.end) : y(w.start - w.delta));

    svg.append('rect')
      .attr('x', x(w.label))
      .attr('width', x.bandwidth())
      .attr('y', w.isFirst ? y(w.value) : (w.delta >= 0 ? y(w.end) : y(w.end - w.delta)))
      .attr('height', w.isFirst ? y(0) - y(w.value) : Math.abs(y(0) - y(Math.abs(w.delta))))
      .attr('fill', w.isFirst ? '#4fc3f7' : (w.delta >= 0 ? '#66bb6a' : '#ef5350'))
      .attr('rx', 3);

    // Value label
    svg.append('text')
      .attr('x', x(w.label) + x.bandwidth() / 2)
      .attr('y', (w.isFirst ? y(w.value) : (w.delta >= 0 ? y(w.end) : y(w.end - w.delta))) - 5)
      .attr('text-anchor', 'middle')
      .attr('fill', '#8b8fa3')
      .attr('font-size', '10px')
      .text(w.isFirst
        ? '$' + w.value.toFixed(2) + 'T'
        : (w.delta >= 0 ? '+' : '') + '$' + w.delta.toFixed(2) + 'T');

    // Connector line
    if (!w.isFirst) {{
      svg.append('line')
        .attr('x1', x(w.label) - 2)
        .attr('x2', x(w.label) + x.bandwidth() + 2)
        .attr('y1', y(w.end))
        .attr('y2', y(w.end))
        .attr('stroke', '#555')
        .attr('stroke-dasharray', '2,2');
    }}
  }});

  // Y-axis label
  svg.append('text')
    .attr('transform', 'rotate(-90)')
    .attr('y', -60).attr('x', -height / 2)
    .attr('text-anchor', 'middle')
    .attr('fill', '#8b8fa3')
    .attr('font-size', '12px')
    .text('Market Cap');
}})();

</script>

</body>
</html>"""

# ---------------------------------------------------------------------------
# Write output
# ---------------------------------------------------------------------------
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_PATH, "w") as f:
    f.write(html)

print(f"\nChart showcase written to {OUTPUT_PATH}")
print(f"File size: {OUTPUT_PATH.stat().st_size / 1024:.0f} KB")
print(f"\nCharts generated:")
print(f"  Lightweight Charts: 3 (5yr area, 2yr earnings, 6mo candlestick)")
print(f"  ECharts: 6 (performance, insider, earnings, DDL, drops, volatility)")
print(f"  Chart.js: 4 (risk radar, probability, financial dashboard x6, governance)")
print(f"  D3.js: 2 (suspicious windows, market cap waterfall)")
print(f"  Matplotlib: 1 (publication-quality performance)")
print(f"  Total: 16 charts across 5 libraries")
