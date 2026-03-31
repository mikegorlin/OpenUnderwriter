"""UW Analysis context builder — CR visual report layout prototype."""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders._uw_analysis_findings import (
    findings,
)
from do_uw.stages.render.context_builders._uw_analysis_investigative import (
    build_investigative_context,
)
from do_uw.stages.render.context_builders._uw_analysis_helpers import (
    badges,
    build_sector_industry_context,
    card_balance,
    card_mcap,
    card_profit,
    card_revenue,
    card_stock,
    card_valuation,
    extract_xbrl_revenue,
    extract_xbrl_shares,
    get_analysis_date,
    get_scoring_dict,
    get_yfinance_info,
    litigation,
    parse_tier,
    resolve_name,
    valuation_multiples_list,
)
from do_uw.stages.render.context_builders.uw_analysis_charts import (
    build_stock_chart_5y,
    build_stock_chart_svg,
)
from do_uw.stages.render.context_builders._uw_analysis_uw_metrics import (
    build_analyst_trend as _build_analyst_trend,
    build_earnings_beat_streak as _build_earnings_beat_streak,
    build_estimate_spread as _build_estimate_spread,
    build_key_dates as _build_key_dates,
    build_plaintiff_exposure as _build_plaintiff_exposure,
)
from do_uw.stages.render.context_builders.uw_analysis_infographics import (
    extract_total_assets,
    fmt_large_number,
    score_bar_cx,
    tier_score_segments,
)
from do_uw.stages.render.context_builders.uw_analysis_sections import (
    build_company_context,
    build_exec_summary_context,
    build_executive_risk_context,
    build_financial_context,
    build_forensic_composites_context,
    build_governance_context,
    build_litigation_context,
    build_ma_profile_context,
    build_market_extended_context,
    build_nlp_signals_context,
    build_peril_map_context,
    build_questions_context,
    build_scoring_context,
    build_settlement_prediction_context,
    build_temporal_signals_context,
    build_xbrl_forensics_context,
)
from do_uw.stages.render.context_builders._forward_scenarios import (
    build_forward_scenarios,
)
from do_uw.stages.render.context_builders.uw_questions import (
    build_uw_questions_context,
)
from do_uw.stages.render.context_builders._forward_calendar import (
    build_forward_calendar,
)
from do_uw.stages.render.context_builders._forward_credibility import (
    build_forward_credibility,
)
from do_uw.stages.render.context_builders._forward_short_sellers import (
    build_short_seller_alerts,
    derive_short_conviction,
)
from do_uw.stages.render.formatters import safe_float

logger = logging.getLogger(__name__)

# Badge color matches the score bar position — green=good, red=bad
_TIER_COLORS = {
    "WIN": "#16A34A",       # 86-100: green
    "PREFERRED": "#16A34A", # alias
    "WRITE": "#22C55E",     # 71-85: light green
    "WATCH": "#D97706",     # 51-70: amber
    "WALK": "#DC2626",      # 31-50: red
    "NO_TOUCH": "#7F1D1D",  # 0-30: dark red
}


def build_uw_analysis_context(
    state: AnalysisState,
    *,
    canonical: Any | None = None,
) -> dict[str, Any]:
    """Build context dict for the uw-analysis template section.

    Args:
        state: The analysis state.
        canonical: Optional CanonicalMetrics object for cross-section consistency.
    """
    info = get_yfinance_info(state)
    ticker = state.ticker or "?"
    scoring = get_scoring_dict(state)
    quality_score = safe_float(scoring.get("quality_score"), None)
    qs = int(quality_score) if quality_score is not None else 0
    tier_name, tier_action, prob_range = parse_tier(scoring.get("tier", {}))

    # Company logo — try multiple sources for reliability
    website = info.get("website", "")
    logo_url = ""
    if website:
        from urllib.parse import urlparse
        domain = urlparse(website).netloc or website.replace("https://", "").replace("http://", "").split("/")[0]
        if domain:
            # Google's favicon service is the most reliable
            logo_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=128"

    ctx: dict[str, Any] = {
        "ticker": ticker,
        "company_name": resolve_name(info, state, ticker),
        "sector": info.get("sector", ""),
        "industry": info.get("industry", ""),
        "sector_etf": info.get("sectorKey", ""),
        "logo_url": logo_url,
        "analysis_date": get_analysis_date(state),
        "quality_score": qs if quality_score is not None else "?",
        "tier_name": tier_name,
        "tier_action": tier_action,
        "probability_range": prob_range,
        "tier_color": _TIER_COLORS.get(tier_name, "#6B7280"),
        "score_bar_segments": tier_score_segments(),
        "score_bar_cx": score_bar_cx(float(qs)),
    }

    # Cross-section metrics: prefer canonical registry when available
    if canonical is not None and canonical.stock_price.raw is not None:
        price = canonical.stock_price.raw
    else:
        price = info.get("currentPrice") or info.get("previousClose")
    if canonical is not None and canonical.employees.raw is not None:
        emp = canonical.employees.raw
    else:
        emp = info.get("fullTimeEmployees")
    ebitda = info.get("ebitda")
    cash = info.get("totalCash")
    debt = info.get("totalDebt")
    assets = info.get("totalAssets") or extract_total_assets(state)
    if canonical is not None and canonical.high_52w.raw is not None:
        h52 = canonical.high_52w.raw
    else:
        h52 = info.get("fiftyTwoWeekHigh")
    if canonical is not None and canonical.low_52w.raw is not None:
        l52 = canonical.low_52w.raw
    else:
        l52 = info.get("fiftyTwoWeekLow")

    # Revenue: prefer canonical (XBRL-first) > XBRL direct > yfinance TTM
    if canonical is not None and canonical.revenue.raw is not None:
        rev = canonical.revenue.raw
    else:
        rev = extract_xbrl_revenue(state)
        if rev is None:
            rev = info.get("totalRevenue")

    # Shares outstanding: prefer XBRL (audited) over yfinance
    xbrl_shares = extract_xbrl_shares(state)

    # Market cap: prefer canonical > XBRL shares x price > yfinance
    if canonical is not None and canonical.market_cap.raw is not None:
        mc = canonical.market_cap.raw
    elif xbrl_shares and price:
        mc = xbrl_shares * price
    else:
        mc = info.get("marketCap")

    card_mcap(ctx, mc, rev, price, emp, cash, debt)
    card_stock(ctx, price, h52, l52, info)
    card_revenue(ctx, rev, state)
    card_profit(ctx, ebitda, rev, info, state)
    if not assets:
        assets = extract_total_assets(state)
    card_balance(ctx, cash, debt, assets, info, ebitda=ebitda, state=state)
    card_valuation(ctx, info)
    badges(ctx, info, price, h52)
    ctx["stock_chart_svg"] = build_stock_chart_svg(state)
    ctx["stock_chart_5y_svg"] = build_stock_chart_5y(state)
    findings(ctx, scoring, state)
    litigation(ctx, state, scoring)

    # Extended sections — manifest order: 1.9, 2, 3, 4, 5, 6, 7, 8, 9
    ctx["exec_summary"] = build_exec_summary_context(state)
    ctx["comp"] = build_company_context(state)
    ctx["ma_profile"] = build_ma_profile_context(state)
    ctx["market_ext"] = build_market_extended_context(state)
    ctx["fin"] = build_financial_context(state)
    ctx["gov"] = build_governance_context(state)
    ctx["lit_detail"] = build_litigation_context(state)
    ctx["sector_industry"] = build_sector_industry_context(state)
    ctx["score_detail"] = build_scoring_context(state)
    ctx["questions"] = build_questions_context(state)

    # Analysis data wiring — forensics, NLP, settlement, peril, exec risk, temporal
    ctx["forensic_composites"] = build_forensic_composites_context(state)
    ctx["xbrl_forensics"] = build_xbrl_forensics_context(state)
    ctx["nlp_dashboard"] = build_nlp_signals_context(state)
    ctx["settlement"] = build_settlement_prediction_context(state)
    ctx["peril"] = build_peril_map_context(state)
    ctx["exec_risk"] = build_executive_risk_context(state)
    ctx["temporal"] = build_temporal_signals_context(state)

    # Investigative analysis layer — data-driven findings
    ctx["investigative"] = build_investigative_context(state)

    # Section 3 extras: valuation multiples list for Stock & Market section
    ctx["valuation_multiples"] = valuation_multiples_list(ctx)
    # Short interest as raw number for template (badges already have formatted)
    sp = info.get("shortPercentOfFloat")
    ctx["short_interest_pct"] = f"{sp * 100:.1f}" if sp else None
    ctx["short_interest_ratio"] = (
        f"{info.get('shortRatio'):.1f}" if info.get("shortRatio") else None
    )

    # Underwriting Decision Framework -- must be LAST so answerers access all ctx keys
    ctx["uw_questions"] = build_uw_questions_context(state, ctx)

    # 3.x Analyst consensus
    analyst_rating = info.get("averageAnalystRating")
    rec_key = info.get("recommendationKey")
    num_analysts = info.get("numberOfAnalystOpinions")
    target_mean = safe_float(info.get("targetMeanPrice"), None)
    target_high = safe_float(info.get("targetHighPrice"), None)
    target_low = safe_float(info.get("targetLowPrice"), None)
    if rec_key or num_analysts:
        ctx["analyst_consensus"] = {
            "rating": str(analyst_rating) if analyst_rating else "",
            "recommendation": (rec_key or "").upper(),
            "num_analysts": num_analysts or 0,
            "target_mean": f"${target_mean:.2f}" if target_mean is not None else "N/A",
            "target_high": f"${target_high:.2f}" if target_high is not None else "N/A",
            "target_low": f"${target_low:.2f}" if target_low is not None else "N/A",
            "rec_color": (
                "#16A34A" if rec_key in ("buy", "strongBuy") else
                "#D97706" if rec_key in ("hold",) else "#DC2626"
            ),
        }
    else:
        ctx["analyst_consensus"] = None

    # 3.x Stock performance (52-week returns)
    w52_change = safe_float(info.get("52WeekChange"), None)
    sp500_change = safe_float(info.get("SandP52WeekChange"), None)
    ctx["stock_52w_change"] = f"{w52_change * 100:+.1f}%" if w52_change is not None else None
    ctx["sp500_52w_change"] = f"{sp500_change * 100:+.1f}%" if sp500_change is not None else None
    if w52_change is not None and sp500_change is not None:
        alpha = (w52_change - sp500_change) * 100
        ctx["stock_alpha"] = f"{alpha:+.1f}%"
        ctx["stock_alpha_color"] = "#16A34A" if alpha >= 0 else "#DC2626"
    else:
        ctx["stock_alpha"] = None
        ctx["stock_alpha_color"] = "#6B7280"

    # 3.x Dividend info
    div_rate = safe_float(info.get("dividendRate"), None)
    div_yield = safe_float(info.get("dividendYield"), None)
    payout_ratio = safe_float(info.get("payoutRatio"), None)
    ex_div_ts = info.get("exDividendDate")
    ex_div_date = ""
    if ex_div_ts and isinstance(ex_div_ts, (int, float)):
        from datetime import datetime, timezone
        try:
            ex_div_date = datetime.fromtimestamp(int(ex_div_ts), tz=timezone.utc).strftime("%Y-%m-%d")
        except Exception:
            ex_div_date = str(ex_div_ts)
    if div_rate is not None or div_yield is not None:
        ctx["dividend_info"] = {
            "rate": f"${div_rate:.2f}" if div_rate is not None else "N/A",
            "yield_pct": f"{div_yield * 100:.2f}%" if div_yield is not None else "N/A",
            "payout_ratio": f"{payout_ratio * 100:.1f}%" if payout_ratio is not None else "N/A",
            "ex_date": ex_div_date or "N/A",
        }
    else:
        ctx["dividend_info"] = None

    # 3.x Volume stats
    avg_vol = info.get("averageVolume")
    avg_vol_10d = info.get("averageDailyVolume10Day")
    if avg_vol or avg_vol_10d:
        ctx["volume_stats"] = {
            "avg_volume": f"{avg_vol / 1e6:.1f}M" if avg_vol else "N/A",
            "avg_volume_10d": f"{avg_vol_10d / 1e6:.1f}M" if avg_vol_10d else "N/A",
        }
    else:
        ctx["volume_stats"] = None

    # 3.x Institutional ownership % (for market section display)
    inst_pct = info.get("heldPercentInstitutions")
    ctx["institutional_pct_market"] = f"{inst_pct * 100:.1f}%" if inst_pct else None

    # 3.x Stock splits history from acquired market data
    stock_splits: list[dict[str, str]] = []
    if state.acquired_data and state.acquired_data.market_data:
        raw_splits = state.acquired_data.market_data.get("splits", {})
        if isinstance(raw_splits, dict) and raw_splits:
            from datetime import datetime
            _ratio_labels = {2.0: "2:1", 3.0: "3:1", 4.0: "4:1", 5.0: "5:1", 7.0: "7:1", 10.0: "10:1"}
            for date_str, ratio in sorted(raw_splits.items()):
                try:
                    dt = datetime.fromisoformat(date_str.replace(" ", "T"))
                    date_fmt = dt.strftime("%b %d, %Y")
                except Exception:
                    date_fmt = date_str[:10]
                ratio_f = safe_float(ratio, 0)
                ratio_label = _ratio_labels.get(ratio_f, f"{ratio_f:.0f}:1") if ratio_f else str(ratio)
                stock_splits.append({"date": date_fmt, "ratio": ratio_label})
    ctx["stock_splits"] = stock_splits if stock_splits else None

    # 3.x Short interest trend
    shares_short = info.get("sharesShort")
    shares_short_prior = info.get("sharesShortPriorMonth")
    if shares_short and shares_short_prior:
        si_change = shares_short - shares_short_prior
        si_change_pct = si_change / shares_short_prior * 100 if shares_short_prior > 0 else 0
        ctx["short_interest_trend"] = {
            "current": f"{shares_short / 1e6:.1f}M",
            "prior": f"{shares_short_prior / 1e6:.1f}M",
            "change_pct": f"{si_change_pct:+.1f}%",
            "direction": "UP" if si_change > 0 else "DOWN",
            "color": "#DC2626" if si_change > 0 else "#16A34A",
        }
    else:
        ctx["short_interest_trend"] = None

    # Underwriter priority metrics (earnings beats, estimate spread, plaintiff
    # exposure, analyst trend, key dates) — extracted to _uw_analysis_uw_metrics
    md_raw = state.acquired_data.market_data if state.acquired_data and state.acquired_data.market_data else {}
    mkt = md_raw if isinstance(md_raw, dict) else {}
    _build_earnings_beat_streak(ctx, mkt)
    _build_estimate_spread(ctx, mkt)
    _build_plaintiff_exposure(ctx, state)
    _build_analyst_trend(ctx, mkt)
    _build_key_dates(ctx, mkt, info)

    # Forward-looking context builders (Phase 136)
    try:
        ctx["forward_scenarios"] = build_forward_scenarios(state)
    except Exception:
        logger.warning("forward_scenarios builder failed", exc_info=True)
        ctx["forward_scenarios"] = {"scenarios_available": False}

    try:
        ctx["forward_calendar"] = build_forward_calendar(state)
    except Exception:
        logger.warning("forward_calendar builder failed", exc_info=True)
        ctx["forward_calendar"] = {"calendar_available": False}

    try:
        ctx["forward_credibility"] = build_forward_credibility(state)
    except Exception:
        logger.warning("forward_credibility builder failed", exc_info=True)
        ctx["forward_credibility"] = {"credibility_available": False}

    try:
        ctx["short_seller_alerts"] = build_short_seller_alerts(state)
    except Exception:
        logger.warning("short_seller_alerts builder failed", exc_info=True)
        ctx["short_seller_alerts"] = {"alerts_available": False}

    try:
        ctx["short_conviction"] = derive_short_conviction(state)
    except Exception:
        logger.warning("short_conviction builder failed", exc_info=True)
        ctx["short_conviction"] = {"conviction": "Stable", "conviction_color": "#D97706"}

    return ctx


