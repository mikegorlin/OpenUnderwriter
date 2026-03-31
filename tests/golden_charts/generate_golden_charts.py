"""Generate golden reference PNGs for visual consistency testing.

Uses FIXED synthetic data (no external APIs) so output is deterministic.
Calls actual chart creation functions from src/do_uw/stages/render/charts/.

Usage:
    uv run python tests/golden_charts/generate_golden_charts.py
"""
from __future__ import annotations

import math
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

_NOW = datetime(2024, 6, 15, tzinfo=timezone.utc)

# Ensure project is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

import matplotlib
matplotlib.use("Agg")

OUTPUT_DIR = Path(__file__).resolve().parent

# Fixed seed for reproducibility
SEED = 42


# ---------------------------------------------------------------------------
# Synthetic data builders
# ---------------------------------------------------------------------------

def _generate_price_series(
    n: int, start: float = 100.0, drift: float = 0.0003, vol: float = 0.02,
    seed: int = SEED,
) -> tuple[list[datetime], list[float]]:
    """Generate deterministic synthetic price data."""
    rng = random.Random(seed)
    start_date = datetime(2024, 1, 2)
    dates: list[datetime] = []
    prices: list[float] = [start]
    dates.append(start_date)

    for i in range(1, n):
        dt = start_date + timedelta(days=i)
        # Skip weekends
        if dt.weekday() >= 5:
            continue
        ret = drift + vol * rng.gauss(0, 1)
        prices.append(prices[-1] * (1 + ret))
        dates.append(dt)

    # Trim to exact n
    return dates[:n], prices[:n]


def _generate_volume(n: int, seed: int = SEED) -> list[float]:
    """Generate synthetic volume data."""
    rng = random.Random(seed + 1)
    base = 5_000_000
    return [base * (0.5 + rng.random()) for _ in range(n)]


def _build_chart_data(period: str = "1Y") -> Any:
    """Build a synthetic ChartData for stock/drawdown/volatility charts."""
    from do_uw.stages.render.charts.stock_chart_data import ChartData

    n = 252 if period == "1Y" else 1260
    dates, prices = _generate_price_series(n, start=100.0, seed=SEED)
    etf_dates, etf_prices = _generate_price_series(n, start=50.0, drift=0.0002, seed=SEED + 10)
    spy_dates, spy_prices = _generate_price_series(n, start=450.0, drift=0.0001, seed=SEED + 20)
    volumes = _generate_volume(n, seed=SEED + 30)

    # Inject some drops
    from do_uw.models.market_events import StockDropEvent
    from do_uw.models.common import SourcedValue

    drops: list[StockDropEvent] = []
    if n >= 100:
        drops.append(StockDropEvent(
            date=SourcedValue(value=dates[50].isoformat(), source="synthetic", confidence="HIGH", as_of=_NOW),
            drop_pct=SourcedValue(value=-8.5, source="synthetic", confidence="HIGH", as_of=_NOW),
            trigger_category="earnings_miss",
            trigger_description="Q2 earnings miss",
            is_company_specific=True,
            is_market_wide=False,
            recovery_days=12,
            sector_return_pct=SourcedValue(value=-1.2, source="synthetic", confidence="HIGH", as_of=_NOW),
        ))
        drops.append(StockDropEvent(
            date=SourcedValue(value=dates[120].isoformat(), source="synthetic", confidence="HIGH", as_of=_NOW),
            drop_pct=SourcedValue(value=-12.3, source="synthetic", confidence="HIGH", as_of=_NOW),
            trigger_category="guidance_cut",
            trigger_description="FY guidance lowered",
            is_company_specific=True,
            is_market_wide=False,
            recovery_days=25,
            sector_return_pct=SourcedValue(value=-3.5, source="synthetic", confidence="HIGH", as_of=_NOW),
        ))

    # Earnings events
    earnings_events: list[dict[str, Any]] = []
    for offset in [60, 150, 210]:
        if offset < len(dates):
            earnings_events.append({
                "date": dates[offset],
                "surprise_pct": 2.5 if offset == 60 else -1.8,
            })

    return ChartData(
        dates=dates,
        prices=prices,
        etf_dates=etf_dates,
        etf_prices=etf_prices,
        etf_ticker="XLK",
        spy_dates=spy_dates,
        spy_prices=spy_prices,
        drops=drops,
        ticker="SYNTH",
        period=period,
        volumes=volumes,
        earnings_events=earnings_events,
        company_beta=1.15,
        sector_beta=0.95,
        company_vol_90d=28.5,
        sector_vol_90d=22.3,
    )


def _build_factor_scores() -> list[Any]:
    """Build synthetic FactorScore list for radar chart."""
    from do_uw.models.scoring import FactorScore

    factors = [
        ("F1", "Accounting Quality", 15, 6.0),
        ("F2", "Revenue Concentration", 10, 3.5),
        ("F3", "Governance Structure", 12, 8.0),
        ("F4", "Litigation History", 15, 2.0),
        ("F5", "Regulatory Exposure", 10, 5.5),
        ("F6", "Market Volatility", 10, 7.0),
        ("F7", "Insider Activity", 8, 1.5),
        ("F8", "Debt Coverage", 10, 4.0),
        ("F9", "Restatement Risk", 5, 0.0),
        ("F10", "Executive Turnover", 5, 3.0),
    ]
    return [
        FactorScore(
            factor_id=fid, factor_name=name,
            max_points=mp, points_deducted=pd,
        )
        for fid, name, mp, pd in factors
    ]


def _build_ownership() -> Any:
    """Build synthetic OwnershipAnalysis for ownership chart."""
    from do_uw.models.governance_forensics import OwnershipAnalysis
    from do_uw.models.common import SourcedValue

    return OwnershipAnalysis(
        institutional_pct=SourcedValue(value=62.5, source="synthetic", confidence="HIGH", as_of=_NOW),
        insider_pct=SourcedValue(value=5.3, source="synthetic", confidence="HIGH", as_of=_NOW),
        top_holders=[
            SourcedValue(value={"name": "Vanguard Group", "pct": 8.2}, source="synthetic", confidence="HIGH", as_of=_NOW),
            SourcedValue(value={"name": "BlackRock", "pct": 6.7}, source="synthetic", confidence="HIGH", as_of=_NOW),
            SourcedValue(value={"name": "State Street", "pct": 4.1}, source="synthetic", confidence="HIGH", as_of=_NOW),
            SourcedValue(value={"name": "Fidelity", "pct": 3.8}, source="synthetic", confidence="HIGH", as_of=_NOW),
            SourcedValue(value={"name": "Capital Group", "pct": 2.9}, source="synthetic", confidence="HIGH", as_of=_NOW),
        ],
        has_dual_class=SourcedValue(value=False, source="synthetic", confidence="HIGH", as_of=_NOW),
    )


# ---------------------------------------------------------------------------
# Chart generation functions
# ---------------------------------------------------------------------------

def _save_png(fig: Any, name: str) -> Path:
    """Save figure to PNG and return path."""
    import matplotlib.pyplot as plt
    path = OUTPUT_DIR / f"{name}.png"
    fig.savefig(str(path), dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path


def generate_stock_charts() -> list[Path]:
    """Generate stock chart golden references."""
    import io
    import matplotlib.pyplot as plt
    from do_uw.stages.render.chart_style_registry import resolve_colors

    paths: list[Path] = []
    for period, suffix in [("1Y", "stock_1y"), ("5Y", "stock_5y")]:
        data = _build_chart_data(period)
        c = resolve_colors("stock", "png")

        # Use dark_background for stock charts
        plt.style.use("dark_background")
        fig = plt.figure(figsize=(10, 6.5), dpi=200, facecolor=c["bg"])

        ax = fig.add_subplot(111)
        ax.set_facecolor(c["bg"])
        ax.plot(data.dates, data.prices, color=c["price_up"], linewidth=1.5, label="SYNTH")
        ax.set_title(f"SYNTH Stock ({period})", color=c["text"], fontweight="bold")
        ax.tick_params(colors=c["text"])
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        ax.grid(alpha=0.3, color=c["grid"])

        path = _save_png(fig, suffix)
        paths.append(path)
        plt.style.use("default")

    return paths


def generate_drawdown_charts() -> list[Path]:
    """Generate drawdown chart golden references."""
    import matplotlib.pyplot as plt
    from do_uw.stages.render.charts.chart_computations import compute_drawdown_series
    from do_uw.stages.render.chart_style_registry import resolve_colors

    paths: list[Path] = []
    for period, suffix in [("1Y", "drawdown_1y"), ("5Y", "drawdown_5y")]:
        data = _build_chart_data(period)
        c = resolve_colors("drawdown", "png")
        dd = compute_drawdown_series(data.prices)

        fig = plt.figure(figsize=(10, 4), dpi=200, facecolor=c["bg"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(c["bg"])
        min_len = min(len(data.dates), len(dd))
        ax.fill_between(data.dates[:min_len], dd[:min_len], 0,
                         color=c.get("price_down", "#B91C1C"), alpha=0.25)
        ax.plot(data.dates[:min_len], dd[:min_len],
                color=c.get("price_down", "#B91C1C"), linewidth=1.2)
        ax.set_title(f"Drawdown ({period})", fontweight="bold")
        ax.axhline(y=0, color=c.get("text_muted", "#6B7280"), linewidth=0.5)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        ax.grid(alpha=0.3, color=c["grid"])

        path = _save_png(fig, suffix)
        paths.append(path)

    return paths


def generate_volatility_charts() -> list[Path]:
    """Generate volatility chart golden references."""
    import matplotlib.pyplot as plt
    from do_uw.stages.render.charts.chart_computations import compute_rolling_volatility
    from do_uw.stages.render.chart_style_registry import get_chart_style, resolve_colors

    paths: list[Path] = []
    for period, suffix in [("1Y", "volatility_1y"), ("5Y", "volatility_5y")]:
        data = _build_chart_data(period)
        c = resolve_colors("volatility", "png")
        vol = compute_rolling_volatility(data.prices, window=30)
        vol_colors = get_chart_style("volatility").colors

        fig = plt.figure(figsize=(10, 4), dpi=200, facecolor=c["bg"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(c["bg"])
        warmup = 30
        min_len = min(len(data.dates), len(vol))
        ax.plot(data.dates[warmup:min_len], vol[warmup:min_len],
                color=c.get("header_bg", "#0B1D3A"), linewidth=1.5)
        ax.axhline(y=20, color=str(vol_colors.get("regime_low", "#16A34A")),
                    linewidth=0.5, linestyle=":")
        ax.axhline(y=40, color=str(vol_colors.get("regime_crisis", "#B91C1C")),
                    linewidth=0.5, linestyle=":")
        ax.set_title(f"Volatility ({period})", fontweight="bold")
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        ax.grid(alpha=0.3, color=c["grid"])

        path = _save_png(fig, suffix)
        paths.append(path)

    return paths


def generate_radar_chart() -> Path:
    """Generate radar chart golden reference."""
    import matplotlib.pyplot as plt
    from do_uw.stages.render.chart_style_registry import get_chart_style

    factor_scores = _build_factor_scores()
    rc = get_chart_style("radar").colors

    labels: list[str] = []
    values: list[float] = []
    for fs in factor_scores:
        max_pts = fs.max_points if fs.max_points > 0 else 1
        fraction = min(fs.points_deducted / max_pts, 1.0)
        labels.append(f"{fs.factor_id}\n{fs.factor_name}")
        values.append(fraction)

    n = len(labels)
    angles = [i * 2 * math.pi / n for i in range(n)]
    values_closed = [*values, values[0]]
    angles_closed = [*angles, angles[0]]

    fig = plt.figure(figsize=(7, 7), dpi=200)
    ax = fig.add_subplot(111, polar=True)

    fill_color = str(rc.get("fill", "#1A1446"))
    outline_color = str(rc.get("outline", "#FFD000"))

    ax.fill(angles_closed, values_closed, color=fill_color, alpha=0.25)
    ax.plot(angles_closed, values_closed, color=outline_color, linewidth=2.5)
    ax.scatter(angles, values, color=fill_color, s=50, zorder=5)
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, fontsize=7)
    ax.set_ylim(0, 1.0)
    ax.set_title("10-Factor Risk Profile", fontweight="bold", pad=25)
    fig.tight_layout()

    return _save_png(fig, "radar")


def generate_ownership_chart() -> Path:
    """Generate ownership chart golden reference."""
    import matplotlib.pyplot as plt
    from do_uw.stages.render.chart_style_registry import get_chart_style

    oc = get_chart_style("ownership").colors

    labels = ["Institutional (62.5%)", "Insider (5.3%)", "Retail Float (32.2%)"]
    values = [62.5, 5.3, 32.2]
    colors = [
        str(oc.get("institutional", "#1A1446")),
        str(oc.get("insider", "#FFD000")),
        str(oc.get("retail", "#B0B0B0")),
    ]

    fig = plt.figure(figsize=(6, 4.5), dpi=200)
    ax = fig.add_subplot(111)

    ax.pie(values, labels=None, colors=colors, autopct="%1.1f%%",
           startangle=90, pctdistance=0.78,
           wedgeprops={"width": 0.4, "edgecolor": "white", "linewidth": 2})
    ax.text(0, 0, "Ownership\nStructure", ha="center", va="center",
            fontsize=10, fontweight="bold",
            color=str(oc.get("institutional", "#1A1446")))
    ax.set_title("Ownership Structure", fontweight="bold", fontsize=12, pad=15)
    fig.tight_layout()

    return _save_png(fig, "ownership")


def generate_drop_analysis_chart() -> Path:
    """Generate drop analysis chart golden reference."""
    import matplotlib.pyplot as plt
    from do_uw.stages.render.chart_style_registry import resolve_colors

    data = _build_chart_data("1Y")
    c = resolve_colors("drop_analysis", "png")

    fig = plt.figure(figsize=(10, 4), dpi=200, facecolor=c["bg"])
    ax = fig.add_subplot(111)
    ax.set_facecolor(c["bg"])
    ax.plot(data.dates, data.prices, color=c.get("price_up", "#16A34A"), linewidth=1.2)

    # Mark drops
    for drop in data.drops:
        if drop.date and drop.drop_pct:
            from datetime import datetime as dt
            drop_date = dt.fromisoformat(drop.date.value[:10])
            idx = min(range(len(data.dates)), key=lambda i: abs((data.dates[i] - drop_date).total_seconds()))
            ax.plot(drop_date, data.prices[idx], "o",
                    color=c.get("price_down", "#B91C1C"), markersize=8)

    ax.set_title("Drop Analysis (1Y)", fontweight="bold")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.grid(alpha=0.3, color=c["grid"])

    return _save_png(fig, "drop_analysis_1y")


def generate_relative_chart() -> Path:
    """Generate relative performance chart golden reference."""
    import matplotlib.pyplot as plt
    from do_uw.stages.render.charts.stock_chart_data import index_to_base
    from do_uw.stages.render.chart_style_registry import resolve_colors

    data = _build_chart_data("1Y")
    c = resolve_colors("relative_performance", "png")
    company_idx = index_to_base(data.prices, 100.0)
    etf_idx = index_to_base(data.etf_prices, 100.0) if data.etf_prices else None

    fig = plt.figure(figsize=(10, 4), dpi=200, facecolor=c["bg"])
    ax = fig.add_subplot(111)
    ax.set_facecolor(c["bg"])

    min_len = min(len(data.dates), len(company_idx))
    ax.plot(data.dates[:min_len], company_idx[:min_len],
            color=c.get("header_bg", "#0B1D3A"), linewidth=2.0, label="SYNTH")
    if etf_idx and data.etf_dates:
        etf_len = min(len(data.etf_dates), len(etf_idx))
        ax.plot(data.etf_dates[:etf_len], etf_idx[:etf_len],
                linestyle="--", color=c.get("etf_line", "#D4A843"), linewidth=1.5, label="XLK")
    ax.axhline(y=100, color=c.get("text_muted", "#6B7280"), linewidth=0.5)
    ax.set_title("Relative Performance (1Y)", fontweight="bold")
    ax.legend(fontsize=7)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.grid(alpha=0.3, color=c["grid"])

    return _save_png(fig, "relative_1y")


def generate_timeline_chart() -> Path:
    """Generate timeline chart golden reference."""
    import matplotlib.pyplot as plt
    from do_uw.stages.render.chart_style_registry import get_chart_style, resolve_colors
    from datetime import date

    c = resolve_colors("timeline", "png")
    tl_colors = get_chart_style("timeline").colors

    events = [
        (date(2023, 3, 15), "case_filing", "SCA Filing"),
        (date(2023, 8, 20), "settlement", "Settlement $5M"),
        (date(2024, 1, 10), "regulatory", "FDA Warning"),
        (date(2024, 5, 5), "stock_drop", "10% drop"),
        (date(2024, 9, 12), "enforcement_action", "SEC Investigation"),
    ]

    fig = plt.figure(figsize=(8, 4), dpi=200, facecolor=c["bg"])
    ax = fig.add_subplot(111)
    ax.set_facecolor(c["bg"])

    for i, (evt_date, evt_type, desc) in enumerate(events):
        color = str(tl_colors.get(evt_type, c.get("text_muted", "#999999")))
        ax.scatter([evt_date], [i], c=color, s=60, zorder=5)
        ax.annotate(desc, (evt_date, i), xytext=(8, 0), textcoords="offset points",
                    fontsize=7, va="center")

    ax.set_title("Litigation Timeline", fontweight="bold", fontsize=11)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.grid(axis="x", alpha=0.3, color=c["grid"])
    fig.tight_layout()

    return _save_png(fig, "timeline")


def generate_sparklines() -> list[Path]:
    """Generate sparkline golden references (as PNG screenshots of SVG)."""
    from do_uw.stages.render.charts.sparklines import render_sparkline

    paths: list[Path] = []
    # Save sparkline SVGs as text files (not PNGs -- sparklines are SVG)
    for name, values, direction in [
        ("sparkline_up", [10, 12, 11, 15, 18, 20], "up"),
        ("sparkline_down", [20, 18, 15, 12, 10, 8], "down"),
        ("sparkline_flat", [10, 10.5, 9.8, 10.2, 10.1, 10], "flat"),
    ]:
        svg = render_sparkline(values, direction=direction)
        path = OUTPUT_DIR / f"{name}.svg"
        path.write_text(svg)
        paths.append(path)

    return paths


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Generate all golden reference images."""
    print("Generating golden reference charts...")
    all_paths: list[Path] = []

    all_paths.extend(generate_stock_charts())
    all_paths.extend(generate_drawdown_charts())
    all_paths.extend(generate_volatility_charts())
    all_paths.append(generate_radar_chart())
    all_paths.append(generate_ownership_chart())
    all_paths.append(generate_drop_analysis_chart())
    all_paths.append(generate_relative_chart())
    all_paths.append(generate_timeline_chart())
    all_paths.extend(generate_sparklines())

    print(f"\nGenerated {len(all_paths)} golden references:")
    for p in all_paths:
        size = p.stat().st_size
        suffix = p.suffix
        if suffix == ".png":
            from PIL import Image
            img = Image.open(p)
            print(f"  {p.name}: {img.width}x{img.height}px ({size:,} bytes)")
        else:
            print(f"  {p.name}: {suffix} ({size:,} bytes)")


if __name__ == "__main__":
    main()
