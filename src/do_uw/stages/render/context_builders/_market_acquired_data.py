"""Market data builders from acquired_data.market_data (raw yfinance).

Private helper module for market.py — extracts earnings history, analyst
recommendations, news articles, upgrades/downgrades, forward estimates,
and 8-K events from LLM extractions.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.extract.earnings_reactions import compute_earnings_reactions
from do_uw.stages.render.formatters import safe_float
from do_uw.stages.render.state_paths import (
    get_earnings_dates,
    get_market_history,
)

# 8-K item descriptions (shared with market.py)
_EIGHT_K_ITEM_NAMES: dict[str, str] = {
    "1.01": "Entry into Material Agreement",
    "1.02": "Termination of Material Agreement",
    "1.03": "Bankruptcy/Receivership",
    "2.01": "Completion of Acquisition/Disposition",
    "2.02": "Results of Operations (Earnings)",
    "2.03": "Creation of Direct Financial Obligation",
    "2.04": "Triggering of Off-Balance Sheet Arrangement",
    "2.05": "Costs for Exit/Disposal Activities",
    "2.06": "Material Impairments",
    "3.01": "Notice of Delisting/Listing Transfer",
    "3.02": "Unregistered Sales of Equity Securities",
    "3.03": "Material Modification to Rights of Security Holders",
    "4.01": "Changes in Registrant's Certifying Accountant",
    "4.02": "Non-Reliance on Previously Issued Financials",
    "5.01": "Changes in Control of Registrant",
    "5.02": "Departure/Appointment of Directors or Officers",
    "5.03": "Amendments to Articles/Bylaws",
    "5.04": "Temporary Suspension of Trading Under EBP",
    "5.05": "Amendments to Code of Ethics",
    "5.06": "Change in Shell Company Status",
    "5.07": "Submission of Matters to Vote of Security Holders",
    "5.08": "Shareholder Nominations (Proxy Access)",
    "7.01": "Regulation FD Disclosure",
    "8.01": "Other Events",
    "9.01": "Financial Statements and Exhibits",
}

_SEVERITY_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


def _get_md_dict(state: AnalysisState) -> dict[str, Any]:
    """Get market_data as a plain dict from state."""
    if not state.acquired_data or not state.acquired_data.market_data:
        return {}
    md = state.acquired_data.market_data
    if isinstance(md, dict):
        return md
    return md.model_dump() if hasattr(md, "model_dump") else {}


def build_eight_k_from_llm(state: AnalysisState) -> dict[str, Any]:
    """Build 8-K event context from LLM extractions when extracted data is empty."""
    if not state.acquired_data or not state.acquired_data.llm_extractions:
        return {}
    llm = state.acquired_data.llm_extractions
    if not isinstance(llm, dict):
        return {}

    filings: list[dict[str, Any]] = []
    item_freq: dict[str, int] = {}
    flags: list[str] = []
    do_critical_count = 0
    has_departure = False
    has_restatement = False

    for key, val in sorted(llm.items()):
        if "8-K" not in key and "8-k" not in key:
            continue
        if not isinstance(val, dict):
            continue

        event_date = val.get("event_date") or ""
        event_type = val.get("event_type") or ""
        items_covered = val.get("items_covered") or []
        description = val.get("event_description") or ""
        departing = val.get("departing_officer") or ""
        dep_title = val.get("departing_officer_title") or ""
        successor = val.get("successor") or ""

        if not description:
            if departing:
                description = f"{departing}"
                if dep_title:
                    description += f" ({dep_title})"
                description += " departure"
                if successor:
                    description += f"; successor: {successor}"
            elif event_type:
                description = event_type.split(" ", 1)[1] if " " in event_type else event_type

        for item_num in items_covered:
            item_freq[item_num] = item_freq.get(item_num, 0) + 1

        is_critical = False
        do_severity = "LOW"
        for item_num in items_covered:
            if item_num in ("4.01", "4.02"):
                do_severity = "CRITICAL"
                is_critical = True
                has_restatement = has_restatement or item_num == "4.02"
            elif item_num in ("5.02", "2.05", "2.06"):
                do_severity = max(
                    do_severity, "HIGH", key=lambda x: _SEVERITY_ORDER[x]
                )
                is_critical = True
                has_departure = has_departure or item_num == "5.02"
            elif item_num in ("2.02",):
                do_severity = max(
                    do_severity, "MEDIUM", key=lambda x: _SEVERITY_ORDER[x]
                )

        if is_critical:
            do_critical_count += 1

        items_display = ", ".join(items_covered) if items_covered else "N/A"
        filings.append({
            "date": event_date[:10] if event_date else "",
            "items": items_display,
            "titles": description[:200],
            "do_severity": do_severity,
            "is_critical": is_critical,
            "do_critical_items": ", ".join(
                i for i in items_covered if i in ("4.01", "4.02", "5.02", "2.05", "2.06")
            ),
        })

    if not filings:
        return {}

    filings.sort(key=lambda x: x["date"], reverse=True)

    if has_restatement:
        flags.append("Restatement/Non-Reliance (Item 4.02)")
    if has_departure:
        flags.append("Officer Departure (Item 5.02)")

    freq_list: list[dict[str, Any]] = []
    for item_num, count in sorted(item_freq.items(), key=lambda x: x[1], reverse=True):
        item_desc = _EIGHT_K_ITEM_NAMES.get(item_num, item_num)
        is_do = item_num in ("4.01", "4.02", "5.02", "2.05", "2.06")
        freq_list.append({"item": item_num, "description": item_desc, "count": count, "is_do_critical": is_do})

    return {
        "total_filings": len(filings),
        "do_critical_count": do_critical_count,
        "filings": filings,
        "item_frequency": freq_list,
        "do_flags": flags,
        "has_restatement": has_restatement,
        "has_auditor_change": False,
        "has_officer_departure": has_departure,
    }


def build_earnings_history(state: AnalysisState) -> dict[str, Any]:
    """Build earnings history (4 quarters: estimate vs actual vs surprise)."""
    md = _get_md_dict(state)
    eh = md.get("earnings_history", {})
    if not eh or not isinstance(eh, dict):
        return {}

    quarters = eh.get("quarter", [])
    actuals = eh.get("epsActual", [])
    estimates = eh.get("epsEstimate", [])
    diffs = eh.get("epsDifference", [])
    surprises = eh.get("surprisePercent", [])

    rows: list[dict[str, str]] = []
    for i in range(min(len(quarters), 4)):
        q = quarters[i] if i < len(quarters) else ""
        q_label = q
        if q and len(q) >= 7:
            try:
                month = int(q[5:7])
                year = q[:4]
                qn = (month - 1) // 3 + 1
                q_label = f"Q{qn} {year}"
            except (ValueError, IndexError):
                pass
        actual = safe_float(actuals[i] if i < len(actuals) else None, None)
        estimate = safe_float(estimates[i] if i < len(estimates) else None, None)
        diff = safe_float(diffs[i] if i < len(diffs) else None, None)
        surprise = safe_float(surprises[i] if i < len(surprises) else None, None)
        # Clamp surprise to ±100% — values beyond that are EPS surprise
        # on near-zero estimates (e.g. +41076%), not meaningful percentages.
        if surprise is not None and abs(surprise) > 1.0:
            surprise = None

        result_tag = "BEAT" if diff is not None and diff > 0 else ("MISS" if diff is not None and diff < 0 else "MEET")

        rows.append({
            "quarter": q_label,
            "eps_estimate": f"${estimate:.2f}" if estimate is not None else "N/A",
            "eps_actual": f"${actual:.2f}" if actual is not None else "N/A",
            "eps_difference": f"${diff:+.2f}" if diff is not None else "N/A",
            "surprise_pct": f"{surprise * 100:+.1f}%" if surprise is not None else "N/A",
            "result": result_tag,
        })

    return {"earnings_history": rows} if rows else {}


def build_recommendation_breakdown(state: AnalysisState) -> dict[str, Any]:
    """Build analyst recommendation breakdown (strongBuy/buy/hold/sell/strongSell)."""
    md = _get_md_dict(state)
    rec = md.get("recommendations", {})
    if not rec or not isinstance(rec, dict):
        return {}

    strong_buy_list = rec.get("strongBuy", [])
    buy_list = rec.get("buy", [])
    hold_list = rec.get("hold", [])
    sell_list = rec.get("sell", [])
    strong_sell_list = rec.get("strongSell", [])

    if not strong_buy_list and not buy_list:
        return {}

    sb = strong_buy_list[0] if strong_buy_list else 0
    b = buy_list[0] if buy_list else 0
    h = hold_list[0] if hold_list else 0
    s = sell_list[0] if sell_list else 0
    ss = strong_sell_list[0] if strong_sell_list else 0
    total = sb + b + h + s + ss

    if total == 0:
        return {}

    return {
        "recommendation_breakdown": {
            "strong_buy": sb, "buy": b, "hold": h, "sell": s, "strong_sell": ss,
            "total": total,
            "buy_pct": f"{(sb + b) / total * 100:.0f}%",
            "sell_pct": f"{(s + ss) / total * 100:.0f}%",
        }
    }


def _extract_article_url(content: dict[str, Any]) -> str:
    """Extract URL string from yfinance news content dict.

    yfinance wraps URLs in nested dicts like {"url": "...", "site": "..."}.
    This extracts the plain URL string from canonicalUrl or clickThroughUrl.
    """
    for key in ("canonicalUrl", "clickThroughUrl"):
        raw = content.get(key, "")
        if isinstance(raw, dict):
            url = raw.get("url", "")
            if url:
                return str(url)
        elif isinstance(raw, str) and raw:
            return raw
    return ""


def build_news_articles(state: AnalysisState) -> dict[str, Any]:
    """Build news article list from market_data.news.

    Filters to company-specific articles (title must mention ticker or company name).
    Generic market articles are excluded.
    """
    md = _get_md_dict(state)
    news = md.get("news", [])
    if not news or not isinstance(news, list):
        return {}

    # Build filter keywords from company info
    ticker = (state.ticker or "").upper()
    company_name = ""
    if state.company:
        company_name = getattr(state.company, "name", "") or ""
    # Use company name words (>3 chars) as keywords for matching
    name_keywords = [w.lower() for w in company_name.split() if len(w) > 3]
    ticker_lower = ticker.lower()

    articles: list[dict[str, str]] = []
    for item in news[:20]:  # Check more items since we filter
        if not isinstance(item, dict):
            continue
        content = item.get("content", {})
        if not isinstance(content, dict):
            continue
        title = content.get("title", "")
        if not title:
            continue

        # Filter: title must mention ticker or company name keyword
        title_lower = title.lower()
        is_relevant = (
            ticker_lower in title_lower
            or any(kw in title_lower for kw in name_keywords if kw)
        )
        if not is_relevant:
            # Also check summary for company mentions
            summary = (content.get("summary", "") or "").lower()
            is_relevant = (
                ticker_lower in summary
                or any(kw in summary for kw in name_keywords if kw)
            )
        if not is_relevant:
            continue

        provider = content.get("provider", {})
        provider_name = provider.get("displayName", "") if isinstance(provider, dict) else ""
        pub_date = content.get("pubDate", "")
        if pub_date and "T" in str(pub_date):
            pub_date = str(pub_date).split("T")[0]
        articles.append({
            "title": title,
            "provider": provider_name,
            "date": str(pub_date)[:10] if pub_date else "",
            "url": _extract_article_url(content),
        })
        if len(articles) >= 10:
            break

    return {"news_articles": articles} if articles else {}


def build_upgrades_downgrades(state: AnalysisState) -> dict[str, Any]:
    """Build recent analyst upgrades/downgrades table (most recent 10)."""
    md = _get_md_dict(state)
    ud = md.get("upgrades_downgrades", {})
    if not ud or not isinstance(ud, dict):
        return {}

    dates = ud.get("GradeDate", [])
    firms = ud.get("Firm", [])
    to_grades = ud.get("ToGrade", [])
    from_grades = ud.get("FromGrade", [])
    actions = ud.get("Action", [])

    if not dates:
        return {}

    rows: list[dict[str, str]] = []
    for i in range(min(len(dates), 10)):
        date_str = str(dates[i])[:10] if i < len(dates) else ""
        firm = firms[i] if i < len(firms) else ""
        to_grade = to_grades[i] if i < len(to_grades) else ""
        from_grade = from_grades[i] if i < len(from_grades) else ""
        action = actions[i] if i < len(actions) else ""

        action_type = str(action).lower()
        is_upgrade = "up" in action_type or action_type == "init"
        is_downgrade = "down" in action_type

        rows.append({
            "date": date_str, "firm": firm,
            "from_grade": from_grade or "\u2014", "to_grade": to_grade,
            "action": action.title() if action else "",
            "is_upgrade": is_upgrade, "is_downgrade": is_downgrade,
        })

    return {"upgrades_downgrades": rows} if rows else {}


def _fmt_billions(v: float | None) -> str:
    """Format a number as $XB or $XM."""
    if v is None:
        return "N/A"
    if abs(v) >= 1e9:
        return f"${v / 1e9:.1f}B"
    if abs(v) >= 1e6:
        return f"${v / 1e6:.0f}M"
    return f"${v:,.0f}"


def build_forward_estimates(state: AnalysisState) -> dict[str, Any]:
    """Build forward EPS and revenue estimate tables."""
    md = _get_md_dict(state)
    result: dict[str, Any] = {}
    period_labels = {"0q": "Current Q", "+1q": "Next Q", "0y": "This Year", "+1y": "Next Year"}

    # EPS estimates
    eps_est = md.get("earnings_estimate", {})
    if eps_est and isinstance(eps_est, dict):
        periods = eps_est.get("period", [])
        avgs = eps_est.get("avg", [])
        lows = eps_est.get("low", [])
        highs = eps_est.get("high", [])
        year_agos = eps_est.get("yearAgoEps", [])
        growths = eps_est.get("growth", [])
        num_analysts = eps_est.get("numberOfAnalysts", [])

        rows: list[dict[str, str]] = []
        for i in range(min(len(periods), 4)):
            p = periods[i] if i < len(periods) else ""
            avg = safe_float(avgs[i] if i < len(avgs) else None, None)
            low = safe_float(lows[i] if i < len(lows) else None, None)
            high = safe_float(highs[i] if i < len(highs) else None, None)
            ya = safe_float(year_agos[i] if i < len(year_agos) else None, None)
            gr = safe_float(growths[i] if i < len(growths) else None, None)
            na_count = num_analysts[i] if i < len(num_analysts) else 0
            rows.append({
                "period": period_labels.get(p, p),
                "avg": f"${avg:.2f}" if avg is not None else "N/A",
                "low": f"${low:.2f}" if low is not None else "N/A",
                "high": f"${high:.2f}" if high is not None else "N/A",
                "year_ago": f"${ya:.2f}" if ya is not None else "N/A",
                "growth": f"{gr * 100:+.1f}%" if gr is not None else "N/A",
                "analysts": str(na_count),
            })
        if rows:
            result["eps_estimates"] = rows

    # Revenue estimates
    rev_est = md.get("revenue_estimate", {})
    if rev_est and isinstance(rev_est, dict):
        periods = rev_est.get("period", [])
        avgs = rev_est.get("avg", [])
        lows = rev_est.get("low", [])
        highs = rev_est.get("high", [])
        growths = rev_est.get("growth", [])
        num_analysts = rev_est.get("numberOfAnalysts", [])

        rows_rev: list[dict[str, str]] = []
        for i in range(min(len(periods), 4)):
            p = periods[i] if i < len(periods) else ""
            avg = safe_float(avgs[i] if i < len(avgs) else None, None)
            low = safe_float(lows[i] if i < len(lows) else None, None)
            high = safe_float(highs[i] if i < len(highs) else None, None)
            gr = safe_float(growths[i] if i < len(growths) else None, None)
            na_count = num_analysts[i] if i < len(num_analysts) else 0
            rows_rev.append({
                "period": period_labels.get(p, p),
                "avg": _fmt_billions(avg), "low": _fmt_billions(low), "high": _fmt_billions(high),
                "growth": f"{gr * 100:+.1f}%" if gr is not None else "N/A",
                "analysts": str(na_count),
            })
        if rows_rev:
            result["revenue_estimates"] = rows_rev

    return result


def build_eps_revision_trends(state: AnalysisState) -> dict[str, Any]:
    """Build EPS revision trend table from yfinance eps_revisions data.

    Shows analyst revision activity across time windows (7d, 30d)
    and periods (current quarter, next quarter, current year, next year).
    """
    md = _get_md_dict(state)
    revisions = md.get("eps_revisions", {})
    if not revisions or not isinstance(revisions, dict):
        return {}

    period_labels = {
        "0q": "Current Qtr", "+1q": "Next Qtr",
        "0y": "Current Year", "+1y": "Next Year",
    }

    # yfinance eps_revisions: keys may have inconsistent casing (downLast7Days vs downLast7days)
    up_7 = revisions.get("upLast7days", revisions.get("upLast7Days", {}))
    down_7 = revisions.get("downLast7days", revisions.get("downLast7Days", {}))
    up_30 = revisions.get("upLast30days", revisions.get("upLast30Days", {}))
    down_30 = revisions.get("downLast30days", revisions.get("downLast30Days", {}))

    # Data can be dict keyed by period OR list indexed by period order
    periods = revisions.get("period", ["0q", "+1q", "0y", "+1y"])

    def _get_val(data: Any, period_key: str, idx: int) -> int:
        """Extract value from dict-by-period or list-by-index format."""
        if isinstance(data, dict):
            return int(safe_float(data.get(period_key, 0), 0))
        if isinstance(data, list) and idx < len(data):
            return int(safe_float(data[idx], 0))
        return 0

    if not up_7 and not up_30 and not down_7 and not down_30:
        return {}

    rows: list[dict[str, Any]] = []
    for i, period_key in enumerate(periods if isinstance(periods, list) else ["0q", "+1q", "0y", "+1y"]):
        u7 = _get_val(up_7, period_key, i)
        d7 = _get_val(down_7, period_key, i)
        u30 = _get_val(up_30, period_key, i)
        d30 = _get_val(down_30, period_key, i)

        net = u30 - d30
        if net > 0:
            direction = "up"
        elif net < 0:
            direction = "down"
        else:
            direction = "flat"

        rows.append({
            "period": period_labels.get(period_key, period_key),
            "up_7d": u7, "down_7d": d7,
            "up_30d": u30, "down_30d": d30,
            "net_direction": direction,
        })

    return {"eps_revisions": rows} if rows else {}


def build_analyst_targets(state: AnalysisState) -> dict[str, Any]:
    """Build analyst price target range data.

    Shows low/mean/high price targets, current price, upside/downside
    percentage, and number of covering analysts.
    """
    md = _get_md_dict(state)
    targets = md.get("analyst_price_targets", {})
    if not targets or not isinstance(targets, dict):
        return {}

    # yfinance uses targetLowPrice/targetMeanPrice/targetHighPrice keys
    low = safe_float(targets.get("low", targets.get("targetLowPrice")), None)
    current_target = safe_float(
        targets.get("current", targets.get("mean", targets.get("targetMeanPrice"))),
        None,
    )
    high = safe_float(targets.get("high", targets.get("targetHighPrice")), None)
    n_analysts = int(safe_float(targets.get("numberOfAnalysts", 0), 0))
    # yfinance also provides currentPrice directly in this dict
    yf_current = safe_float(targets.get("currentPrice"), None)

    if current_target is None and low is None and high is None:
        return {}

    # Get current stock price — prefer extracted, fall back to yfinance target dict
    current_price: float | None = None
    if state.extracted and state.extracted.market:
        stock = state.extracted.market.stock
        if stock.current_price:
            current_price = safe_float(stock.current_price.value, None)
    if current_price is None:
        current_price = yf_current

    # Compute upside
    upside_pct: str = "N/A"
    if current_target is not None and current_price is not None and current_price > 0:
        pct = (current_target - current_price) / current_price * 100
        upside_pct = f"{pct:+.1f}%"

    return {"analyst_targets": {
        "low": f"${low:.2f}" if low is not None else "N/A",
        "mean": f"${current_target:.2f}" if current_target is not None else "N/A",
        "high": f"${high:.2f}" if high is not None else "N/A",
        "current": f"${current_price:.2f}" if current_price is not None else "N/A",
        "upside_pct": upside_pct,
        "analyst_count": n_analysts,
    }}


def build_earnings_trust(state: AnalysisState) -> dict[str, Any]:
    """Build earnings trust narrative and reaction data for templates.

    Analyzes beat/miss patterns against stock reactions to assess market
    trust in earnings quality. Returns both a narrative string and a list
    of per-quarter reaction data for the earnings_reaction template.
    """
    eg = None
    if state.extracted and state.extracted.market:
        eg = state.extracted.market.earnings_guidance
    if not eg or not eg.quarters:
        return {}

    # Compute multi-window returns using longest available price history
    # Prefer 5y > 3y > 2y > 1y to cover as many earnings quarters as possible
    history_long = get_market_history(state, window="5y")
    earnings_date_data = get_earnings_dates(state)

    # Extract actual earnings dates from yfinance earnings_dates dict
    # Format: {"Earnings Date": ["2026-01-29 16:00:00-04:00", ...], ...}
    raw_dates: list[str] = []
    if isinstance(earnings_date_data, dict):
        ed_list = earnings_date_data.get("Earnings Date", [])
        if isinstance(ed_list, list):
            raw_dates = [str(d) for d in ed_list if d]

    # Also try extracting dates from the quarters themselves (if date-formatted)
    quarter_dates: list[str] = []
    for q in eg.quarters:
        if q.quarter and len(q.quarter) >= 10:
            quarter_dates.append(q.quarter[:10])

    # Use whichever source has actual dates
    reaction_source: list[str] = quarter_dates if quarter_dates else raw_dates

    # Compute multi-window returns
    computed_reactions = compute_earnings_reactions(reaction_source, history_long)

    # Build lookup: date -> computed returns
    reaction_lookup: dict[str, dict[str, Any]] = {}
    for cr in computed_reactions:
        reaction_lookup[cr["date"]] = cr

    # Also build index-based mapping: yfinance earnings dates align 1:1 with quarters
    # So reaction_lookup_by_idx[i] corresponds to eg.quarters[i]
    reaction_by_idx: dict[int, dict[str, Any]] = {}
    if raw_dates and not quarter_dates:
        for i, rd in enumerate(raw_dates):
            clean = rd[:10] if len(rd) >= 10 else rd
            if clean in reaction_lookup:
                reaction_by_idx[i] = reaction_lookup[clean]

    # Build per-quarter reaction rows
    reaction_rows: list[dict[str, str]] = []
    beat_count = 0
    miss_count = 0
    beat_sell_off_count = 0
    severe_miss_count = 0
    total_beat_reaction = 0.0
    total_miss_reaction = 0.0

    for qtr_idx, qtr in enumerate(eg.quarters[:16]):
        result = (qtr.result or "").upper()

        # EPS estimate: use midpoint of low/high consensus
        eps_est_str = "N/A"
        if qtr.consensus_eps_low and qtr.consensus_eps_high:
            lo = safe_float(qtr.consensus_eps_low.value, None)
            hi = safe_float(qtr.consensus_eps_high.value, None)
            if lo is not None and hi is not None:
                mid = (lo + hi) / 2
                eps_est_str = f"${mid:.2f}"
        elif qtr.consensus_eps_low:
            lo = safe_float(qtr.consensus_eps_low.value, None)
            if lo is not None:
                eps_est_str = f"${lo:.2f}"

        eps_actual_str = f"${qtr.actual_eps.value:.2f}" if qtr.actual_eps else "N/A"

        # Resolve computed reaction for this quarter (date-based or index-based)
        qtr_date = (qtr.quarter or "")[:10]
        cr = reaction_lookup.get(qtr_date, {})
        if not cr:
            cr = reaction_by_idx.get(qtr_idx, {})

        # Day-of return: prefer model field, fall back to computed reaction
        # Clamp to ±100% — yfinance Surprise(%) is EPS surprise, not stock return.
        # Values like +41076% are EPS surprise on near-zero estimates, not real returns.
        day_of = safe_float(
            qtr.stock_reaction_pct.value if qtr.stock_reaction_pct else None, None,
        )
        if day_of is not None and abs(day_of) > 100:
            day_of = None  # Discard implausible EPS surprise masquerading as stock return
        if day_of is None:
            if "day_of_return" in cr:
                day_of = cr["day_of_return"]

        # Multi-window returns: prefer model fields, fall back to computed reactions
        next_day = None
        week_ret = None

        # Check model fields first
        if getattr(qtr, "next_day_return_pct", None) is not None:
            next_day = safe_float(qtr.next_day_return_pct.value, None)
        if getattr(qtr, "week_return_pct", None) is not None:
            week_ret = safe_float(qtr.week_return_pct.value, None)

        # Fall back to computed reactions from price history (cr already resolved above)
        if next_day is None and "next_day_return" in cr:
            next_day = cr["next_day_return"]
        if week_ret is None and "week_return" in cr:
            week_ret = cr["week_return"]

        # Track beat/miss patterns
        if result == "BEAT":
            beat_count += 1
            if day_of is not None:
                total_beat_reaction += day_of
                if day_of < 0:
                    beat_sell_off_count += 1
        elif result == "MISS":
            miss_count += 1
            if day_of is not None:
                total_miss_reaction += day_of
                if day_of < -5:
                    severe_miss_count += 1

        reaction_rows.append({
            "quarter": qtr.quarter or "N/A",
            "eps_estimate": eps_est_str,
            "eps_actual": eps_actual_str,
            "result": result if result in ("BEAT", "MISS", "MEET") else "N/A",
            "day_of_return": f"{day_of:+.1f}%" if day_of is not None else "N/A",
            "next_day_return": f"{next_day:+.1f}%" if next_day is not None else "N/A",
            "week_return": f"{week_ret:+.1f}%" if week_ret is not None else "N/A",
        })

    total_qtrs = beat_count + miss_count
    if total_qtrs == 0:
        return {"earnings_reaction": reaction_rows} if reaction_rows else {}

    beat_rate_val = safe_float(
        eg.beat_rate.value if eg.beat_rate else None, None,
    )
    if beat_rate_val is None and total_qtrs > 0:
        beat_rate_val = beat_count / total_qtrs

    # Generate trust narrative
    narrative = ""
    if beat_rate_val is not None and beat_rate_val > 0.75:
        beat_sell_rate = beat_sell_off_count / beat_count if beat_count > 0 else 0.0
        if beat_sell_rate > 0.5:
            narrative = (
                f"Company beat {beat_count} of {total_qtrs} quarters but stock "
                f"sold off on {beat_sell_off_count} of {beat_count} beats, "
                f"suggesting market distrust of earnings quality. This pattern "
                f"supports plaintiff allegations of inflated expectations."
            )
        elif beat_sell_rate < 0.3:
            positive_beats = beat_count - beat_sell_off_count
            narrative = (
                f"Company beat {beat_count} of {total_qtrs} quarters with "
                f"positive market reactions on {positive_beats} beats. Strong "
                f"earnings credibility reduces loss causation exposure."
            )
        else:
            narrative = (
                f"Company beat {beat_count} of {total_qtrs} quarters. "
                f"Mixed market reactions ({beat_sell_off_count} sell-offs on "
                f"beats) suggest nuanced earnings quality assessment."
            )
    elif eg.consecutive_miss_count >= 2:
        narrative = (
            f"Company has missed {eg.consecutive_miss_count} consecutive "
            f"quarters. Consecutive misses increase probability of guidance "
            f"manipulation allegations under Section 10b-5."
        )
    elif total_qtrs > 0:
        avg_beat = total_beat_reaction / beat_count if beat_count > 0 else 0.0
        avg_miss = total_miss_reaction / miss_count if miss_count > 0 else 0.0
        narrative = (
            f"Beat rate: {beat_count}/{total_qtrs} quarters. "
            f"Avg reaction on beat: {avg_beat:+.1f}%, on miss: {avg_miss:+.1f}%."
        )

    result_dict: dict[str, Any] = {}
    if reaction_rows:
        result_dict["earnings_reaction"] = reaction_rows
    if narrative:
        result_dict["earnings_trust_narrative"] = narrative
    # Summary stats for template
    if total_qtrs > 0:
        result_dict["earnings_trust_summary"] = {
            "beat_rate": f"{beat_rate_val * 100:.0f}%" if beat_rate_val is not None else "N/A",
            "beat_count": beat_count,
            "miss_count": miss_count,
            "total_quarters": total_qtrs,
            "beat_sell_off_count": beat_sell_off_count,
            "severe_miss_count": severe_miss_count,
        }

    return result_dict
