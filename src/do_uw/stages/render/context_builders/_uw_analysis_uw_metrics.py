"""Underwriter priority metrics for uw analysis Page 0.

Earnings beat streak, estimate spread, plaintiff exposure matrix,
analyst trend, and key dates calendar — the metrics a 30-year D&O
underwriter looks for first.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.formatters import safe_float


def build_earnings_beat_streak(ctx: dict[str, Any], md: dict[str, Any]) -> None:
    """Compute consecutive EPS beat streak from earnings_history."""
    eh = md.get("earnings_history", {})
    if not isinstance(eh, dict):
        ctx["earnings_beat_streak"] = None
        return
    actuals = eh.get("epsActual", [])
    estimates = eh.get("epsEstimate", [])
    if not actuals or not estimates:
        ctx["earnings_beat_streak"] = None
        return
    beats = sum(1 for a, e in zip(actuals, estimates) if a is not None and e is not None and a > e)
    total = sum(1 for a, e in zip(actuals, estimates) if a is not None and e is not None)
    if total == 0:
        ctx["earnings_beat_streak"] = None
        return
    ctx["earnings_beat_streak"] = f"{beats}/{total}"
    ctx["earnings_beat_color"] = (
        "#16A34A" if beats == total else "#D97706" if beats >= total * 0.75 else "#DC2626"
    )
    ctx["earnings_beat_label"] = (
        "Consecutive Beats" if beats == total else "Beats" if beats > 0 else "Misses"
    )


def build_estimate_spread(ctx: dict[str, Any], md: dict[str, Any]) -> None:
    """Compute revenue estimate spread (high-low)/avg as SCA miss risk indicator."""
    rev_est = md.get("revenue_estimate", {})
    if not isinstance(rev_est, dict):
        ctx["estimate_spreads"] = None
        return
    periods = rev_est.get("period", [])
    avgs = rev_est.get("avg", [])
    lows = rev_est.get("low", [])
    highs = rev_est.get("high", [])
    spreads: list[dict[str, Any]] = []
    _labels = {"0q": "Current Q", "+1q": "Next Q", "0y": "Current Y", "+1y": "Next Y"}
    for i, period in enumerate(periods):
        if i >= len(avgs) or i >= len(lows) or i >= len(highs):
            break
        avg_v = safe_float(avgs[i], None)
        low_v = safe_float(lows[i], None)
        high_v = safe_float(highs[i], None)
        if avg_v and low_v and high_v and avg_v > 0:
            spread_pct = (high_v - low_v) / avg_v * 100
            color = "#16A34A" if spread_pct < 5 else "#D97706" if spread_pct < 10 else "#DC2626"
            spreads.append({
                "label": _labels.get(period, period),
                "spread_pct": f"{spread_pct:.0f}%",
                "spread_raw": spread_pct,
                "color": color,
                "avg": f"${avg_v / 1e9:.1f}B" if avg_v >= 1e9 else f"${avg_v / 1e6:.0f}M",
                "low": f"${low_v / 1e9:.1f}B" if low_v >= 1e9 else f"${low_v / 1e6:.0f}M",
                "high": f"${high_v / 1e9:.1f}B" if high_v >= 1e9 else f"${high_v / 1e6:.0f}M",
            })
    ctx["estimate_spreads"] = spreads if spreads else None


_PROB_LEVEL: dict[str, int] = {
    "VERY_LOW": 1, "LOW": 1, "MODERATE": 3, "ELEVATED": 4, "HIGH": 5, "CRITICAL": 5,
}
_PROB_COLOR: dict[str, str] = {
    "VERY_LOW": "#16A34A", "LOW": "#16A34A", "MODERATE": "#D97706",
    "ELEVATED": "#EA580C", "HIGH": "#DC2626", "CRITICAL": "#DC2626",
}


def build_plaintiff_exposure(ctx: dict[str, Any], state: AnalysisState) -> None:
    """Build compact plaintiff exposure matrix from peril_map for Page 0."""
    if not state.analysis:
        ctx["plaintiff_exposure"] = None
        return
    analysis = state.analysis if isinstance(state.analysis, dict) else (
        state.analysis.model_dump() if hasattr(state.analysis, "model_dump") else {}
    )
    pm = analysis.get("peril_map") if isinstance(analysis, dict) else None
    if not pm or not isinstance(pm, dict):
        ctx["plaintiff_exposure"] = None
        return
    assessments = pm.get("assessments", [])
    if not assessments:
        ctx["plaintiff_exposure"] = None
        return
    # Sort by probability level descending for visual impact
    rows: list[dict[str, Any]] = []
    for a in assessments:
        if not isinstance(a, dict):
            continue
        ptype = a.get("plaintiff_type", "")
        prob = a.get("probability_band", "")
        sev = a.get("severity_band", "")
        level = _PROB_LEVEL.get(prob, 1)
        color = _PROB_COLOR.get(prob, "#6B7280")
        rows.append({
            "type": ptype.replace("_", " ").title(),
            "level": level,
            "color": color,
            "prob": prob.replace("_", " ").title(),
            "sev": sev.replace("_", " ").title(),
        })
    rows.sort(key=lambda r: r["level"], reverse=True)
    ctx["plaintiff_exposure"] = rows


def build_analyst_trend(ctx: dict[str, Any], md: dict[str, Any]) -> None:
    """Summarize 90-day analyst upgrade/downgrade trend."""
    ud = md.get("upgrades_downgrades", {})
    if not isinstance(ud, dict):
        ctx["analyst_trend"] = None
        return
    dates = ud.get("GradeDate", [])
    actions = ud.get("Action", [])
    if not dates or not actions:
        ctx["analyst_trend"] = None
        return
    # Count actions in last 90 days
    from datetime import datetime, timedelta
    try:
        cutoff = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    except Exception:
        cutoff = "2000-01-01"
    ups = downs = maintains = reiterates = initiates = 0
    for d, a in zip(dates, actions):
        d_str = str(d)[:10] if d else ""
        if d_str >= cutoff:
            if a == "up":
                ups += 1
            elif a == "down":
                downs += 1
            elif a == "main":
                maintains += 1
            elif a == "reit":
                reiterates += 1
            elif a == "init":
                initiates += 1
    total = ups + downs + maintains + reiterates + initiates
    if total == 0:
        ctx["analyst_trend"] = None
        return
    # Determine trend direction
    if ups > downs + 1:
        direction = "IMPROVING"
        dir_color = "#16A34A"
    elif downs > ups + 1:
        direction = "DECLINING"
        dir_color = "#DC2626"
    else:
        direction = "STABLE"
        dir_color = "#D97706"
    ctx["analyst_trend"] = {
        "ups": ups,
        "downs": downs,
        "maintains": maintains,
        "reiterates": reiterates,
        "initiates": initiates,
        "total": total,
        "direction": direction,
        "direction_color": dir_color,
        "summary": (
            f"{ups} upgrade{'s' if ups != 1 else ''}, "
            f"{downs} downgrade{'s' if downs != 1 else ''}, "
            f"{maintains + reiterates} hold{'s' if (maintains + reiterates) != 1 else ''}"
        ),
    }


def build_key_dates(ctx: dict[str, Any], md: dict[str, Any], info: dict[str, Any]) -> None:
    """Build forward-looking key dates calendar from market data."""
    cal = md.get("calendar", {})
    if not isinstance(cal, dict):
        cal = {}
    dates: list[dict[str, str]] = []
    # Next earnings
    earnings = cal.get("Earnings Date", [])
    if isinstance(earnings, list) and earnings:
        dates.append({"event": "Next Earnings", "date": str(earnings[0]), "icon": "chart"})
    elif isinstance(earnings, str) and earnings:
        dates.append({"event": "Next Earnings", "date": earnings, "icon": "chart"})
    # Ex-dividend
    ex_div = cal.get("Ex-Dividend Date", "")
    if ex_div:
        dates.append({"event": "Ex-Dividend", "date": str(ex_div), "icon": "dollar"})
    # Dividend date
    div_date = cal.get("Dividend Date", "")
    if div_date:
        dates.append({"event": "Dividend Payment", "date": str(div_date), "icon": "dollar"})
    # Earnings estimate range for upcoming quarter
    e_avg = safe_float(cal.get("Earnings Average"), None)
    e_high = safe_float(cal.get("Earnings High"), None)
    e_low = safe_float(cal.get("Earnings Low"), None)
    if e_avg is not None:
        ctx["next_earnings_estimate"] = {
            "avg": f"${e_avg:.2f}",
            "high": f"${e_high:.2f}" if e_high is not None else "N/A",
            "low": f"${e_low:.2f}" if e_low is not None else "N/A",
        }
    else:
        ctx["next_earnings_estimate"] = None
    ctx["key_dates"] = dates if dates else None
