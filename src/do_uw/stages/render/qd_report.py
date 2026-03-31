"""Question-driven D&O underwriting report renderer.

Reads a completed state.json and produces a clean HTML report organized
around underwriter questions. Each section follows the pattern:
  Answer (1-2 sentences with specific numbers) -> Evidence (tables/data) -> Flags (brain signals)

Usage:
    uv run python src/do_uw/stages/render/qd_report.py output/AAPL/

Produces: output/AAPL/AAPL_qd_report.html
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Utility: safe value extraction from SourcedValue or raw values
# ---------------------------------------------------------------------------


def _sv(obj: Any, default: Any = None) -> Any:
    """Extract value from SourcedValue dict or return raw value.

    State data uses SourcedValue pattern where values are nested as:
      {"value": X, "source": Y, "confidence": Z}
    This function handles both raw values and SourcedValue dicts.
    """
    if obj is None:
        return default
    if isinstance(obj, dict) and "value" in obj:
        v = obj["value"]
        return v if v is not None else default
    return obj


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Convert to float safely, handling 'N/A', '%' strings, and junk.

    Mirrors safe_float() from formatters.py but kept standalone to avoid
    import dependency issues when running as a script.
    """
    import re as _re

    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if not s or s.lower() in ("n/a", "none", "null", "-", "\u2014"):
        return default
    s = s.replace(",", "").replace("%", "").strip()
    m = _re.search(r"-?\d+(?:\.\d+)?", s)
    if m:
        return float(m.group())
    return default


def _fmt_currency(val: float | None, billions: bool = False) -> str:
    """Format a number as currency. Returns 'N/A' for None/zero."""
    if val is None or val == 0.0:
        return "N/A"
    if billions or abs(val) >= 1e9:
        return f"${val / 1e9:,.2f}B"
    if abs(val) >= 1e6:
        return f"${val / 1e6:,.1f}M"
    if abs(val) >= 1e3:
        return f"${val / 1e3:,.0f}K"
    return f"${val:,.2f}"


def _fmt_pct(val: float | None) -> str:
    """Format as percentage with one decimal."""
    if val is None:
        return "N/A"
    return f"{val:+.1f}%" if val != 0 else "0.0%"


def _fmt_number(val: float | None) -> str:
    """Format a plain number with comma separators."""
    if val is None:
        return "N/A"
    if abs(val) >= 1e6:
        return f"{val / 1e6:,.0f}M"
    if abs(val) >= 1e3:
        return f"{val / 1e3:,.0f}K"
    return f"{val:,.0f}"


def _fmt_ratio(val: float | None) -> str:
    """Format a ratio to 2 decimal places."""
    if val is None:
        return "N/A"
    return f"{val:.2f}"


def _e(text: str | None) -> str:
    """HTML-escape a string, returning empty string for None."""
    if text is None:
        return ""
    return escape(str(text))


# ---------------------------------------------------------------------------
# Financial helpers: extract line items from statement data
# ---------------------------------------------------------------------------


def _get_line_item(
    statements: dict[str, Any], statement_type: str, label_prefix: str, period: str | None = None
) -> float | None:
    """Extract a specific line item value from financial statements.

    Searches for a line item whose label starts with label_prefix (case-insensitive).
    If period is None, uses the most recent period available.
    Returns the raw float value or None.
    """
    stmt = statements.get(statement_type, {})
    line_items = stmt.get("line_items", [])
    periods = stmt.get("periods", [])

    if not line_items or not periods:
        return None

    target_period = period if period else (periods[-1] if periods else None)
    if not target_period:
        return None

    label_lower = label_prefix.lower()
    for item in line_items:
        if item.get("label", "").lower().startswith(label_lower):
            vals = item.get("values", {})
            val_entry = vals.get(target_period)
            if val_entry is not None:
                return _safe_float(_sv(val_entry))
    return None


def _get_latest_period(statements: dict[str, Any], statement_type: str) -> str | None:
    """Get the most recent period label from a statement."""
    stmt = statements.get(statement_type, {})
    periods = stmt.get("periods", [])
    return periods[-1] if periods else None


# ---------------------------------------------------------------------------
# Section builders: each returns (answer_html, evidence_html, flags_html)
# ---------------------------------------------------------------------------


def _build_company_snapshot(state: dict[str, Any]) -> tuple[str, str, str]:
    """Section 1: Who is this company?"""
    company = state.get("company", {})
    identity = company.get("identity", {})

    ticker = _sv(identity.get("ticker"), "Unknown")
    name = _sv(identity.get("legal_name"), ticker)
    sector = _sv(identity.get("sector"), "Unknown")
    sic_desc = _sv(identity.get("sic_description"), "")
    exchange = _sv(identity.get("exchange"), "")
    market_cap = _safe_float(_sv(company.get("market_cap")))
    employees = _safe_float(_sv(company.get("employee_count")))
    years_public = _safe_float(_sv(company.get("years_public")))
    bus_desc = _sv(company.get("business_description"), "")

    # Market cap tier
    if market_cap >= 200e9:
        cap_tier = "mega-cap"
    elif market_cap >= 10e9:
        cap_tier = "large-cap"
    elif market_cap >= 2e9:
        cap_tier = "mid-cap"
    elif market_cap >= 300e6:
        cap_tier = "small-cap"
    elif market_cap > 0:
        cap_tier = "micro-cap"
    else:
        cap_tier = "unknown-cap"

    answer = (
        f"<strong>{_e(name)}</strong> ({_e(ticker)}) is a {cap_tier} {_e(sector).lower()} company "
        f"trading on {_e(exchange)} with a market capitalization of {_fmt_currency(market_cap)}. "
    )
    if employees > 0:
        answer += f"The company employs approximately {_fmt_number(employees)} people "
    if years_public > 0:
        answer += f"and has been publicly traded for {int(years_public)} years. "
    if bus_desc:
        # Truncate at first 2 sentences for the answer
        sentences = bus_desc.split(". ")
        brief = ". ".join(sentences[:2]) + ("." if len(sentences) > 1 else "")
        answer += f"{_e(brief)}"

    # Evidence table
    evidence_rows = [
        ("Ticker", _e(ticker)),
        ("Legal Name", _e(name)),
        ("Exchange", _e(exchange)),
        ("Sector / SIC", f"{_e(sector)} / {_e(sic_desc)}"),
        ("Market Cap", _fmt_currency(market_cap)),
        ("Employees", _fmt_number(employees) if employees > 0 else "N/A"),
        ("Years Public", f"{int(years_public)}" if years_public > 0 else "N/A"),
        ("Filer Category", _e(_sv(company.get("filer_category"), "N/A"))),
    ]
    evidence = _render_kv_table(evidence_rows)

    return answer, evidence, ""


def _build_risk_verdict(state: dict[str, Any]) -> tuple[str, str, str]:
    """Section 2: Should I write this risk?"""
    scoring = state.get("scoring", {})
    tier_data = scoring.get("tier", {})
    tier_name = tier_data.get("tier", "Unknown") if isinstance(tier_data, dict) else str(tier_data)
    action = tier_data.get("action", "") if isinstance(tier_data, dict) else ""
    quality_score = _safe_float(scoring.get("quality_score"))
    composite_score = _safe_float(scoring.get("composite_score"))

    claim_prob = scoring.get("claim_probability", {})
    prob_band = claim_prob.get("band", "Unknown") if isinstance(claim_prob, dict) else "Unknown"
    prob_low = _safe_float(claim_prob.get("range_low_pct")) if isinstance(claim_prob, dict) else 0
    prob_high = _safe_float(claim_prob.get("range_high_pct")) if isinstance(claim_prob, dict) else 0
    base_rate = _safe_float(claim_prob.get("industry_base_rate_pct")) if isinstance(claim_prob, dict) else 0

    # Verdict color
    tier_upper = tier_name.upper()
    if tier_upper in ("WIN", "COMPETE"):
        verdict_class = "verdict-green"
        verdict_word = "Yes"
    elif tier_upper in ("CONSIDER",):
        verdict_class = "verdict-yellow"
        verdict_word = "Conditional"
    else:
        verdict_class = "verdict-red"
        verdict_word = "Caution"

    answer = (
        f'<span class="{verdict_class}">{_e(verdict_word)}</span> &mdash; '
        f"Tier: <strong>{_e(tier_name)}</strong>. "
        f"Quality score: <strong>{quality_score:.1f}/100</strong>. "
    )
    if action:
        answer += f"{_e(action)}. "
    answer += (
        f"Claim probability band: {_e(prob_band)} ({prob_low:.1f}%&ndash;{prob_high:.1f}%). "
        f"Industry base rate: {base_rate:.1f}%."
    )

    # Factor scores evidence
    factor_scores = scoring.get("factor_scores", [])
    if factor_scores:
        rows = ""
        total_deducted = 0.0
        total_max = 0.0
        for fs in factor_scores:
            fid = fs.get("factor_id", "")
            fname = fs.get("factor_name", "")
            deducted = _safe_float(fs.get("points_deducted"))
            max_pts = _safe_float(fs.get("max_points"))
            total_deducted += deducted
            total_max += max_pts
            pct_used = (deducted / max_pts * 100) if max_pts > 0 else 0
            bar_width = min(pct_used, 100)
            bar_color = "#e74c3c" if pct_used > 50 else "#f39c12" if pct_used > 25 else "#27ae60"
            rows += (
                f"<tr><td>{_e(fid)}</td><td>{_e(fname)}</td>"
                f"<td style='text-align:right'>{deducted:.1f}</td>"
                f"<td style='text-align:right'>{max_pts:.0f}</td>"
                f"<td><div class='bar-bg'><div class='bar-fill' "
                f"style='width:{bar_width:.0f}%;background:{bar_color}'></div></div></td></tr>"
            )
        evidence = (
            f"<table class='data-table'>"
            f"<thead><tr><th>Factor</th><th>Name</th><th>Deducted</th><th>Max</th><th>Usage</th></tr></thead>"
            f"<tbody>{rows}</tbody>"
            f"<tfoot><tr><td></td><td><strong>Total</strong></td>"
            f"<td style='text-align:right'><strong>{total_deducted:.1f}</strong></td>"
            f"<td style='text-align:right'><strong>{total_max:.0f}</strong></td>"
            f"<td></td></tr></tfoot>"
            f"</table>"
        )
    else:
        evidence = "<p>No factor scores available.</p>"

    return answer, evidence, ""


def _build_key_risk_findings(state: dict[str, Any]) -> tuple[str, str, str]:
    """Section 3: What are the 3-5 things I MUST know?"""
    signals = state.get("analysis", {}).get("signal_results", {})
    company = state.get("company", {})
    name = _sv(company.get("identity", {}).get("legal_name"), state.get("ticker", "Company"))

    # Get triggered signals with do_context (the D&O interpretation)
    triggered = []
    for sig_id, sig in signals.items():
        if not isinstance(sig, dict):
            continue
        if sig.get("status") != "TRIGGERED":
            continue
        if sig.get("threshold_level") not in ("red", "yellow"):
            continue
        triggered.append(
            {
                "id": sig_id,
                "name": sig.get("signal_name", sig_id),
                "value": sig.get("value"),
                "threshold": sig.get("threshold_level", ""),
                "do_context": sig.get("do_context", ""),
                "factors": sig.get("factors", []),
                "category": sig.get("category", ""),
            }
        )

    # Sort: red before yellow, then by category (DECISION_DRIVING first)
    def _sort_key(s: dict[str, Any]) -> tuple[int, int, str]:
        t_order = 0 if s["threshold"] == "red" else 1
        c_order = 0 if s["category"] == "DECISION_DRIVING" else 1
        return (t_order, c_order, s["id"])

    triggered.sort(key=_sort_key)

    # Take top 5-8 most critical red signals
    top_signals = [s for s in triggered if s["threshold"] == "red"][:8]
    if len(top_signals) < 3:
        # Supplement with yellow
        yellows = [s for s in triggered if s["threshold"] == "yellow"]
        top_signals.extend(yellows[: 5 - len(top_signals)])

    red_count = sum(1 for s in triggered if s["threshold"] == "red")
    yellow_count = sum(1 for s in triggered if s["threshold"] == "yellow")

    answer = (
        f"<strong>{red_count}</strong> red flags and <strong>{yellow_count}</strong> caution signals "
        f"triggered for {_e(name)}. "
    )
    if top_signals:
        # Summarize the top finding
        top = top_signals[0]
        answer += f"Most critical: {_e(top['name'])}. "

    # Evidence: signal cards
    evidence = ""
    for sig in top_signals:
        ctx = sig["do_context"].strip() if sig["do_context"] else "No D&O context available."
        # Clean up the context — remove leading whitespace
        ctx = ctx.strip()
        threshold_badge = (
            '<span class="badge badge-red">RED</span>'
            if sig["threshold"] == "red"
            else '<span class="badge badge-yellow">YELLOW</span>'
        )
        factor_badges = " ".join(
            f'<span class="badge badge-factor">{_e(f)}</span>' for f in sig.get("factors", [])
        )
        val_display = sig["value"]
        if isinstance(val_display, float):
            val_display = f"{val_display:.2f}"

        evidence += (
            f"<div class='finding-card'>"
            f"<div class='finding-header'>{threshold_badge} {factor_badges} "
            f"<strong>{_e(sig['name'])}</strong> = {_e(str(val_display))}</div>"
            f"<div class='finding-body'>{_e(ctx)}</div>"
            f"</div>"
        )

    if not evidence:
        evidence = "<p>No significant risk signals triggered.</p>"

    # Flags: count summary
    flags = (
        f"<div class='flag-summary'>"
        f"<span class='badge badge-red'>{red_count} red</span> "
        f"<span class='badge badge-yellow'>{yellow_count} yellow</span> "
        f"of {len(signals)} signals evaluated"
        f"</div>"
    )

    return answer, evidence, flags


def _build_financial_health(state: dict[str, Any]) -> tuple[str, str, str]:
    """Section 4: Is this company financially sound?"""
    fin = state.get("extracted", {}).get("financials", {})
    statements = fin.get("statements", {})

    # Get most recent period
    latest = _get_latest_period(statements, "income_statement")
    prior_periods = statements.get("income_statement", {}).get("periods", [])
    prior = prior_periods[-2] if len(prior_periods) > 1 else None

    # Key metrics
    revenue = _get_line_item(statements, "income_statement", "total revenue", latest)
    revenue_prior = _get_line_item(statements, "income_statement", "total revenue", prior) if prior else None
    net_income = _get_line_item(statements, "income_statement", "net income", latest)
    gross_profit = _get_line_item(statements, "income_statement", "gross profit", latest)
    operating_income = _get_line_item(statements, "income_statement", "operating income", latest)

    total_assets = _get_line_item(statements, "balance_sheet", "total assets")
    total_liabilities = _get_line_item(statements, "balance_sheet", "total liabilities")
    equity = _get_line_item(statements, "balance_sheet", "total stockholders", )
    cash = _get_line_item(statements, "balance_sheet", "cash and cash")
    total_debt = _get_line_item(statements, "balance_sheet", "total debt")
    current_ratio = _get_line_item(statements, "balance_sheet", "current ratio")

    # Operating cash flow
    ocf = _get_line_item(statements, "cash_flow", "net cash from operating")

    # Revenue growth
    rev_growth = None
    if revenue and revenue_prior and revenue_prior > 0:
        rev_growth = (revenue - revenue_prior) / revenue_prior * 100

    # Margins
    gross_margin = (gross_profit / revenue * 100) if revenue and gross_profit else None
    operating_margin = (operating_income / revenue * 100) if revenue and operating_income else None
    net_margin = (net_income / revenue * 100) if revenue and net_income else None

    # Distress
    distress = fin.get("distress", {})
    altman = distress.get("altman_z_score", {}) if distress else {}
    beneish = distress.get("beneish_m_score", {}) if distress else {}
    altman_score = altman.get("score") if altman else None
    altman_zone = altman.get("zone", "N/A") if altman else "N/A"
    beneish_score = beneish.get("score") if beneish else None
    beneish_zone = beneish.get("zone", "N/A") if beneish else "N/A"

    # Build answer
    answer = ""
    if revenue:
        answer += f"Revenue: {_fmt_currency(revenue)} ({_e(latest or 'latest')})"
        if rev_growth is not None:
            direction = "grew" if rev_growth > 0 else "declined"
            answer += f", {direction} {abs(rev_growth):.1f}% year-over-year"
        answer += ". "
    if net_income:
        answer += f"Net income: {_fmt_currency(net_income)}. "
    if cash and total_debt:
        answer += f"Cash: {_fmt_currency(cash)}, total debt: {_fmt_currency(total_debt)}"
        net_debt = total_debt - cash
        answer += f" (net debt: {_fmt_currency(net_debt)}). "
    if altman_score is not None:
        answer += f"Altman Z-Score: {altman_score:.2f} ({_e(altman_zone)}). "
    if beneish_score is not None:
        answer += f"Beneish M-Score: {beneish_score:.2f} ({_e(beneish_zone)}). "
    if not answer:
        answer = "Financial data not available."

    # Evidence table
    evidence_rows = [
        ("Revenue", f"{_fmt_currency(revenue)} ({_e(latest or '')})" if revenue else "N/A"),
        ("Revenue Growth", f"{rev_growth:+.1f}%" if rev_growth is not None else "N/A"),
        ("Gross Margin", f"{gross_margin:.1f}%" if gross_margin is not None else "N/A"),
        ("Operating Margin", f"{operating_margin:.1f}%" if operating_margin is not None else "N/A"),
        ("Net Margin", f"{net_margin:.1f}%" if net_margin is not None else "N/A"),
        ("Net Income", _fmt_currency(net_income) if net_income else "N/A"),
        ("Total Assets", _fmt_currency(total_assets) if total_assets else "N/A"),
        ("Total Equity", _fmt_currency(equity) if equity else "N/A"),
        ("Cash", _fmt_currency(cash) if cash else "N/A"),
        ("Total Debt", _fmt_currency(total_debt) if total_debt else "N/A"),
        ("Current Ratio", _fmt_ratio(current_ratio) if current_ratio else "N/A"),
        ("Operating Cash Flow", _fmt_currency(ocf) if ocf else "N/A"),
        ("Altman Z-Score", f"{altman_score:.2f} ({_e(altman_zone)})" if altman_score else "N/A"),
        ("Beneish M-Score", f"{beneish_score:.2f} ({_e(beneish_zone)})" if beneish_score else "N/A"),
    ]
    evidence = _render_kv_table(evidence_rows)

    # Flags: financial signals that triggered
    sigs = state.get("analysis", {}).get("signal_results", {})
    fin_flags = []
    for sig_id, sig in sigs.items():
        if not isinstance(sig, dict):
            continue
        if sig.get("status") != "TRIGGERED":
            continue
        if sig_id.startswith("FIN."):
            fin_flags.append(
                f'<span class="badge badge-{sig.get("threshold_level", "yellow")}">'
                f'{_e(sig.get("signal_name", sig_id))}</span>'
            )
    flags = " ".join(fin_flags) if fin_flags else ""

    return answer, evidence, flags


def _build_stock_story(state: dict[str, Any]) -> tuple[str, str, str]:
    """Section 5: What's happening with the stock?"""
    market = state.get("extracted", {}).get("market", {})
    stock = market.get("stock", {})

    price = _safe_float(_sv(stock.get("current_price")))
    high_52w = _safe_float(_sv(stock.get("high_52w")))
    low_52w = _safe_float(_sv(stock.get("low_52w")))
    beta = _safe_float(_sv(stock.get("beta")))
    returns_1y = _safe_float(_sv(stock.get("returns_1y")))
    returns_5y = _safe_float(_sv(stock.get("returns_5y")))
    decline_from_high = _safe_float(_sv(stock.get("decline_from_high_pct")))
    volatility = _safe_float(_sv(stock.get("volatility_90d")))
    max_dd_1y = _safe_float(_sv(stock.get("max_drawdown_1y")))

    # Short interest
    si = market.get("short_interest", {})
    short_pct = _safe_float(_sv(si.get("short_pct_float"))) if isinstance(si, dict) else 0
    days_to_cover = _safe_float(_sv(si.get("days_to_cover"))) if isinstance(si, dict) else 0

    # Answer
    answer = ""
    if price > 0:
        answer += f"Current price: <strong>${price:.2f}</strong>. "
    if high_52w > 0 and low_52w > 0:
        answer += f"52-week range: ${low_52w:.2f}&ndash;${high_52w:.2f}"
        if decline_from_high != 0:
            answer += f" ({decline_from_high:+.1f}% from high)"
        answer += ". "
    if returns_1y != 0:
        answer += f"1-year return: {returns_1y:+.1f}%. "
    if beta > 0:
        answer += f"Beta: {beta:.2f}. "
    if short_pct > 0:
        characterization = "de minimis" if short_pct < 3 else "moderate" if short_pct < 10 else "elevated"
        answer += f"Short interest: {short_pct:.1f}% of float ({characterization}, {days_to_cover:.1f} days to cover). "
    if volatility > 0:
        answer += f"90-day volatility: {volatility:.1f}%. "
    if not answer:
        answer = "Stock data not available."

    # Evidence table
    evidence_rows = [
        ("Current Price", f"${price:.2f}" if price > 0 else "N/A"),
        ("52-Week High", f"${high_52w:.2f}" if high_52w > 0 else "N/A"),
        ("52-Week Low", f"${low_52w:.2f}" if low_52w > 0 else "N/A"),
        ("Decline from High", f"{decline_from_high:+.1f}%" if decline_from_high != 0 else "N/A"),
        ("1-Year Return", f"{returns_1y:+.1f}%" if returns_1y != 0 else "N/A"),
        ("5-Year Return", f"{returns_5y:+.1f}%" if returns_5y != 0 else "N/A"),
        ("Beta", f"{beta:.3f}" if beta > 0 else "N/A"),
        ("90-Day Volatility", f"{volatility:.1f}%" if volatility > 0 else "N/A"),
        ("Max Drawdown (1Y)", f"{max_dd_1y:.1f}%" if max_dd_1y != 0 else "N/A"),
        ("Short % Float", f"{short_pct:.2f}%" if short_pct > 0 else "N/A"),
        ("Days to Cover", f"{days_to_cover:.1f}" if days_to_cover > 0 else "N/A"),
    ]
    evidence = _render_kv_table(evidence_rows)

    # Drops table
    drops_data = market.get("stock_drops", {})
    multi_drops = drops_data.get("multi_day_drops", []) if isinstance(drops_data, dict) else []
    single_drops = drops_data.get("single_day_drops", []) if isinstance(drops_data, dict) else []
    all_drops = multi_drops + single_drops

    if all_drops:
        drop_rows = ""
        for d in all_drops[:6]:
            d_date = _sv(d.get("date"), "N/A")
            d_pct = _safe_float(_sv(d.get("drop_pct")))
            d_catalyst = _sv(d.get("catalyst"), "")
            d_ddl = _safe_float(_sv(d.get("ddl_exposure")))
            drop_rows += (
                f"<tr><td>{_e(str(d_date))}</td>"
                f"<td style='text-align:right;color:#e74c3c'>{d_pct:.1f}%</td>"
                f"<td>{_e(str(d_catalyst))[:80]}</td>"
                f"<td style='text-align:right'>{_fmt_currency(d_ddl) if d_ddl else 'N/A'}</td></tr>"
            )
        evidence += (
            f"<h4>Significant Stock Drops</h4>"
            f"<table class='data-table'>"
            f"<thead><tr><th>Date</th><th>Drop</th><th>Catalyst</th><th>DDL Exposure</th></tr></thead>"
            f"<tbody>{drop_rows}</tbody></table>"
        )

    # Flags
    sigs = state.get("analysis", {}).get("signal_results", {})
    stock_flags = []
    for sig_id, sig in sigs.items():
        if not isinstance(sig, dict):
            continue
        if sig.get("status") != "TRIGGERED":
            continue
        if sig_id.startswith("STOCK."):
            stock_flags.append(
                f'<span class="badge badge-{sig.get("threshold_level", "yellow")}">'
                f'{_e(sig.get("signal_name", sig_id))}</span>'
            )
    flags = " ".join(stock_flags) if stock_flags else ""

    return answer, evidence, flags


def _build_litigation_exposure(state: dict[str, Any]) -> tuple[str, str, str]:
    """Section 6: What's the litigation risk?"""
    lit = state.get("extracted", {}).get("litigation", {})

    # Securities class actions
    sca_list = lit.get("securities_class_actions", [])
    sca_list = sca_list if isinstance(sca_list, list) else []

    # Derivative suits
    deriv_list = lit.get("derivative_suits", [])
    deriv_list = deriv_list if isinstance(deriv_list, list) else []

    # Summary
    lit_summary = _sv(lit.get("litigation_summary"), "")
    active_count = lit.get("active_matter_count")
    historical_count = lit.get("historical_matter_count")

    # Defense
    defense = lit.get("defense", {})
    defense_assessment = defense.get("defense_assessment") if isinstance(defense, dict) else None

    # SOL windows
    sol_map = lit.get("sol_map", [])
    sol_count = len(sol_map) if isinstance(sol_map, list) else 0

    # Answer
    answer = ""
    if lit_summary:
        answer = f"{_e(str(lit_summary))} "
    else:
        case_count = len(sca_list) + len(deriv_list)
        if case_count > 0:
            answer += f"{case_count} litigation matter(s) identified. "
        else:
            answer += "No active securities litigation matters identified. "
        if active_count is not None:
            answer += f"Active matters: {active_count}. "
        if historical_count is not None:
            answer += f"Historical matters: {historical_count}. "

    # Evidence: case table
    evidence = ""
    if sca_list:
        rows = ""
        for case in sca_list[:10]:
            case_name = _sv(case.get("case_name"), "Unknown")
            court = _sv(case.get("court"), "N/A")
            status = _sv(case.get("status"), "N/A")
            filing_date = _sv(case.get("filing_date"), "N/A")
            settlement = _sv(case.get("settlement_amount"))
            settlement_str = _fmt_currency(_safe_float(settlement)) if settlement else "N/A"

            rows += (
                f"<tr><td>{_e(str(case_name))}</td>"
                f"<td>{_e(str(court))}</td>"
                f"<td>{_e(str(status))}</td>"
                f"<td>{_e(str(filing_date))}</td>"
                f"<td style='text-align:right'>{settlement_str}</td></tr>"
            )
        evidence += (
            f"<h4>Securities Class Actions</h4>"
            f"<table class='data-table'>"
            f"<thead><tr><th>Case</th><th>Court</th><th>Status</th>"
            f"<th>Filed</th><th>Settlement</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>"
        )

    if not evidence:
        evidence = "<p>No securities litigation cases found in database.</p>"

    # SOL info
    if sol_count > 0:
        evidence += f"<p><strong>{sol_count}</strong> open statute of limitations window(s).</p>"

    # Flags
    sigs = state.get("analysis", {}).get("signal_results", {})
    lit_flags = []
    for sig_id, sig in sigs.items():
        if not isinstance(sig, dict):
            continue
        if sig.get("status") != "TRIGGERED":
            continue
        if sig_id.startswith("LIT."):
            lit_flags.append(
                f'<span class="badge badge-{sig.get("threshold_level", "yellow")}">'
                f'{_e(sig.get("signal_name", sig_id))}</span>'
            )
    flags = " ".join(lit_flags) if lit_flags else ""

    return answer, evidence, flags


def _build_governance_profile(state: dict[str, Any]) -> tuple[str, str, str]:
    """Section 7: Who runs this company and are they problematic?"""
    gov = state.get("extracted", {}).get("governance", {})
    board = gov.get("board", {}) if isinstance(gov, dict) else {}
    comp = gov.get("compensation", {}) if isinstance(gov, dict) else {}
    leadership = gov.get("leadership", {}) if isinstance(gov, dict) else {}
    ownership = gov.get("ownership", {}) if isinstance(gov, dict) else {}

    board_size = _safe_float(_sv(board.get("size"))) if isinstance(board, dict) else 0
    independence = _safe_float(_sv(board.get("independence_ratio"))) if isinstance(board, dict) else 0
    avg_tenure = _safe_float(_sv(board.get("avg_tenure_years"))) if isinstance(board, dict) else 0
    ceo_chair = _sv(board.get("ceo_chair_duality"), False) if isinstance(board, dict) else False
    classified = _sv(board.get("classified_board"), False) if isinstance(board, dict) else False
    gender_div = _safe_float(_sv(board.get("board_gender_diversity_pct"))) if isinstance(board, dict) else 0

    say_on_pay = _safe_float(_sv(comp.get("say_on_pay_support_pct"))) if isinstance(comp, dict) else 0
    pay_ratio = _safe_float(_sv(comp.get("ceo_pay_ratio"))) if isinstance(comp, dict) else 0

    institutional_pct = _safe_float(_sv(ownership.get("institutional_pct"))) if isinstance(ownership, dict) else 0
    insider_pct = _safe_float(_sv(ownership.get("insider_pct"))) if isinstance(ownership, dict) else 0

    # Executives
    executives = leadership.get("executives", []) if isinstance(leadership, dict) else []
    departures = leadership.get("departures_18mo", []) if isinstance(leadership, dict) else []

    # Answer
    answer = ""
    if board_size > 0:
        answer += f"Board of {int(board_size)} directors, {independence * 100:.0f}% independent"
        if avg_tenure > 0:
            answer += f", average tenure {avg_tenure:.1f} years"
        answer += ". "
    if ceo_chair:
        answer += "CEO serves as board chair (duality). "
    if say_on_pay > 0:
        answer += f"Say-on-pay approval: {say_on_pay:.0f}%. "
    if pay_ratio > 0:
        answer += f"CEO pay ratio: {pay_ratio:.0f}:1. "
    if len(departures) > 0:
        answer += f"<strong>{len(departures)}</strong> key departure(s) in past 18 months. "
    if not answer:
        answer = "Governance data not available."

    # Evidence: board metrics + exec table
    evidence_rows = [
        ("Board Size", f"{int(board_size)}" if board_size > 0 else "N/A"),
        ("Independence", f"{independence * 100:.0f}%" if independence > 0 else "N/A"),
        ("Avg Tenure", f"{avg_tenure:.1f} years" if avg_tenure > 0 else "N/A"),
        ("CEO/Chair Duality", "Yes" if ceo_chair else "No"),
        ("Classified Board", "Yes" if classified else "No"),
        ("Gender Diversity", f"{gender_div:.1f}%" if gender_div > 0 else "N/A"),
        ("Say-on-Pay", f"{say_on_pay:.0f}%" if say_on_pay > 0 else "N/A"),
        ("CEO Pay Ratio", f"{pay_ratio:.0f}:1" if pay_ratio > 0 else "N/A"),
        ("Institutional Ownership", f"{institutional_pct:.1f}%" if institutional_pct > 0 else "N/A"),
        ("Insider Ownership", f"{insider_pct:.1f}%" if insider_pct > 0 else "N/A"),
    ]
    evidence = _render_kv_table(evidence_rows)

    # Executive table
    if executives:
        exec_rows = ""
        for ex in executives[:10]:
            ex_name = _sv(ex.get("name"), "Unknown")
            ex_title = _sv(ex.get("title"), "N/A")
            ex_tenure = _sv(ex.get("tenure_years"))
            tenure_str = f"{_safe_float(ex_tenure):.1f}y" if ex_tenure is not None else "N/A"
            exec_rows += (
                f"<tr><td>{_e(str(ex_name))}</td>"
                f"<td>{_e(str(ex_title))}</td>"
                f"<td>{tenure_str}</td></tr>"
            )
        evidence += (
            f"<h4>Executive Leadership</h4>"
            f"<table class='data-table'>"
            f"<thead><tr><th>Name</th><th>Title</th><th>Tenure</th></tr></thead>"
            f"<tbody>{exec_rows}</tbody></table>"
        )

    # Flags
    sigs = state.get("analysis", {}).get("signal_results", {})
    gov_flags = []
    for sig_id, sig in sigs.items():
        if not isinstance(sig, dict):
            continue
        if sig.get("status") != "TRIGGERED":
            continue
        if sig_id.startswith(("GOV.", "EXEC.")):
            gov_flags.append(
                f'<span class="badge badge-{sig.get("threshold_level", "yellow")}">'
                f'{_e(sig.get("signal_name", sig_id))}</span>'
            )
    flags = " ".join(gov_flags) if gov_flags else ""

    return answer, evidence, flags


def _build_insider_activity(state: dict[str, Any]) -> tuple[str, str, str]:
    """Section 8: Are insiders signaling anything?"""
    market = state.get("extracted", {}).get("market", {})
    insider = market.get("insider_trading", {})

    net_bs = _sv(insider.get("net_buying_selling")) if isinstance(insider, dict) else None
    total_sold = _safe_float(_sv(insider.get("total_sold_value"))) if isinstance(insider, dict) else 0
    total_bought = _safe_float(_sv(insider.get("total_bought_value"))) if isinstance(insider, dict) else 0
    ceo_cfo_pct = _safe_float(_sv(insider.get("ceo_cfo_pct_sold"))) if isinstance(insider, dict) else 0
    clusters = insider.get("cluster_events", []) if isinstance(insider, dict) else []
    has_10b5_1 = _sv(insider.get("has_10b5_1_modifications")) if isinstance(insider, dict) else None

    # Answer
    if total_sold > 0 or total_bought > 0:
        net_direction = "selling" if total_sold > total_bought else "buying"
        answer = (
            f"Net insider {net_direction}. "
            f"Total sold: {_fmt_currency(total_sold)}. "
            f"Total bought: {_fmt_currency(total_bought)}. "
        )
        if ceo_cfo_pct > 0:
            answer += f"CEO/CFO sold {ceo_cfo_pct:.0f}% of holdings. "
        if clusters:
            answer += f"{len(clusters)} cluster selling event(s) detected. "
        if has_10b5_1:
            answer += "10b5-1 plan modifications detected. "
    elif net_bs is not None:
        answer = f"Net insider position: {_e(str(net_bs))}. "
    else:
        answer = "Insider transaction data not available for this company."

    # Evidence table
    evidence_rows = [
        ("Net Direction", _e(str(net_bs)) if net_bs else "N/A"),
        ("Total Sold", _fmt_currency(total_sold) if total_sold > 0 else "N/A"),
        ("Total Bought", _fmt_currency(total_bought) if total_bought > 0 else "N/A"),
        ("CEO/CFO % Sold", f"{ceo_cfo_pct:.0f}%" if ceo_cfo_pct > 0 else "N/A"),
        ("Cluster Events", str(len(clusters)) if clusters else "0"),
        ("10b5-1 Modifications", "Yes" if has_10b5_1 else "No"),
    ]
    evidence = _render_kv_table(evidence_rows)

    # Flags
    sigs = state.get("analysis", {}).get("signal_results", {})
    insider_flags = []
    for sig_id, sig in sigs.items():
        if not isinstance(sig, dict):
            continue
        if sig.get("status") != "TRIGGERED":
            continue
        if "INSIDER" in sig_id:
            insider_flags.append(
                f'<span class="badge badge-{sig.get("threshold_level", "yellow")}">'
                f'{_e(sig.get("signal_name", sig_id))}</span>'
            )
    flags = " ".join(insider_flags) if insider_flags else ""

    return answer, evidence, flags


# ---------------------------------------------------------------------------
# HTML rendering helpers
# ---------------------------------------------------------------------------


def _render_kv_table(rows: list[tuple[str, str]]) -> str:
    """Render a list of (key, value) tuples as a 2-column table."""
    html = "<table class='kv-table'><tbody>"
    for key, val in rows:
        html += f"<tr><td class='kv-key'>{key}</td><td class='kv-val'>{val}</td></tr>"
    html += "</tbody></table>"
    return html


def _render_section(
    section_number: int, question: str, answer: str, evidence: str, flags: str
) -> str:
    """Render one section card with the Answer -> Evidence -> Flags pattern."""
    flags_html = ""
    if flags:
        flags_html = f"<div class='section-flags'><h4>Triggered Signals</h4>{flags}</div>"

    return f"""
    <div class="section-card" id="section-{section_number}">
      <div class="section-header">
        <span class="section-num">{section_number}</span>
        <h2>{_e(question)}</h2>
      </div>
      <div class="section-answer">{answer}</div>
      <div class="section-evidence">{evidence}</div>
      {flags_html}
    </div>
    """


# ---------------------------------------------------------------------------
# CSS Design
# ---------------------------------------------------------------------------

_CSS = """
:root {
  --bg: #f8f9fa;
  --card-bg: #ffffff;
  --text: #1a1a2e;
  --text-secondary: #4a4a6a;
  --border: #e8e8ef;
  --accent: #2563eb;
  --accent-light: #dbeafe;
  --red: #dc2626;
  --red-light: #fef2f2;
  --yellow: #d97706;
  --yellow-light: #fffbeb;
  --green: #059669;
  --green-light: #ecfdf5;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
  font-size: 14px;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}

.report-container {
  max-width: 960px;
  margin: 0 auto;
  padding: 24px 16px;
}

/* Header */
.report-header {
  background: linear-gradient(135deg, #1e293b, #334155);
  color: white;
  padding: 32px;
  border-radius: 12px;
  margin-bottom: 24px;
}
.report-header h1 {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.5px;
  margin-bottom: 4px;
}
.report-header .subtitle {
  font-size: 14px;
  color: #94a3b8;
  font-weight: 400;
}
.report-header .meta {
  margin-top: 16px;
  display: flex;
  gap: 24px;
  font-size: 13px;
  color: #cbd5e1;
}
.report-header .meta strong {
  color: white;
}

/* Navigation */
.nav-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 24px;
  padding: 12px;
  background: var(--card-bg);
  border-radius: 8px;
  border: 1px solid var(--border);
}
.nav-bar a {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  text-decoration: none;
  padding: 4px 10px;
  border-radius: 4px;
  transition: all 0.15s;
}
.nav-bar a:hover {
  background: var(--accent-light);
  color: var(--accent);
}

/* Section cards */
.section-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 10px;
  margin-bottom: 20px;
  overflow: hidden;
}
.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  background: #fafbfc;
}
.section-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: var(--accent);
  color: white;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}
.section-header h2 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
}
.section-answer {
  padding: 16px 20px;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text);
  border-bottom: 1px solid var(--border);
}
.section-answer strong {
  color: var(--accent);
}
.section-evidence {
  padding: 16px 20px;
}
.section-evidence h4 {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin: 16px 0 8px 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.section-flags {
  padding: 12px 20px;
  background: #f9fafb;
  border-top: 1px solid var(--border);
}
.section-flags h4 {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

/* Tables */
.kv-table {
  width: 100%;
  border-collapse: collapse;
}
.kv-table td {
  padding: 6px 12px;
  font-size: 13px;
  border-bottom: 1px solid #f0f0f5;
}
.kv-table .kv-key {
  font-weight: 500;
  color: var(--text-secondary);
  width: 40%;
  white-space: nowrap;
}
.kv-table .kv-val {
  color: var(--text);
  font-variant-numeric: tabular-nums;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.data-table thead th {
  text-align: left;
  padding: 8px 12px;
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-secondary);
  border-bottom: 2px solid var(--border);
  background: #fafbfc;
}
.data-table tbody td {
  padding: 8px 12px;
  border-bottom: 1px solid #f0f0f5;
  vertical-align: top;
}
.data-table tfoot td {
  padding: 8px 12px;
  border-top: 2px solid var(--border);
}

/* Badges */
.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.3px;
  margin: 2px;
}
.badge-red {
  background: var(--red-light);
  color: var(--red);
  border: 1px solid #fecaca;
}
.badge-yellow {
  background: var(--yellow-light);
  color: var(--yellow);
  border: 1px solid #fde68a;
}
.badge-green {
  background: var(--green-light);
  color: var(--green);
  border: 1px solid #a7f3d0;
}
.badge-factor {
  background: var(--accent-light);
  color: var(--accent);
  border: 1px solid #93c5fd;
}

/* Bar chart in scoring */
.bar-bg {
  width: 100px;
  height: 8px;
  background: #f0f0f5;
  border-radius: 4px;
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s;
}

/* Verdict */
.verdict-green { color: var(--green); font-weight: 700; font-size: 16px; }
.verdict-yellow { color: var(--yellow); font-weight: 700; font-size: 16px; }
.verdict-red { color: var(--red); font-weight: 700; font-size: 16px; }

/* Finding cards */
.finding-card {
  border: 1px solid var(--border);
  border-radius: 8px;
  margin-bottom: 10px;
  overflow: hidden;
}
.finding-header {
  padding: 8px 12px;
  background: #fafbfc;
  border-bottom: 1px solid var(--border);
  font-size: 13px;
}
.finding-body {
  padding: 10px 12px;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}

/* Flag summary */
.flag-summary {
  padding: 8px 0;
}

/* Footer */
.report-footer {
  text-align: center;
  padding: 24px;
  font-size: 12px;
  color: var(--text-secondary);
}

/* Print */
@media print {
  body { background: white; }
  .report-container { max-width: 100%; padding: 0; }
  .nav-bar { display: none; }
  .section-card { break-inside: avoid; }
  .report-header { background: #1e293b !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
}
"""


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------


def render_qd_report(output_dir: str | Path) -> Path:
    """Load state.json from output_dir and produce a question-driven HTML report.

    Returns the path to the generated HTML file.
    """
    output_path = Path(output_dir)
    state_file = output_path / "state.json"

    if not state_file.exists():
        raise FileNotFoundError(f"state.json not found in {output_path}")

    logger.info("Loading state from %s", state_file)
    with open(state_file, encoding="utf-8") as f:
        state: dict[str, Any] = json.load(f)

    ticker = state.get("ticker", "UNKNOWN")
    company_name = _sv(state.get("company", {}).get("identity", {}).get("legal_name"), ticker)
    created_at = state.get("created_at", "")
    # Format date
    try:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        date_str = dt.strftime("%B %d, %Y at %H:%M UTC")
    except (ValueError, AttributeError):
        date_str = created_at

    # Build sections
    sections_config = [
        (1, "Who is this company?", _build_company_snapshot),
        (2, "Should I write this risk?", _build_risk_verdict),
        (3, "What are the 3-5 things I MUST know?", _build_key_risk_findings),
        (4, "Is this company financially sound?", _build_financial_health),
        (5, "What's happening with the stock?", _build_stock_story),
        (6, "What's the litigation risk?", _build_litigation_exposure),
        (7, "Who runs this company and are they problematic?", _build_governance_profile),
        (8, "Are insiders signaling anything?", _build_insider_activity),
    ]

    sections_html = ""
    nav_links = ""
    for num, question, builder in sections_config:
        try:
            answer, evidence, flags = builder(state)
        except Exception as exc:
            logger.error("Error building section %d (%s): %s", num, question, exc)
            answer = f"Error generating this section: {_e(str(exc))}"
            evidence = ""
            flags = ""
        sections_html += _render_section(num, question, answer, evidence, flags)
        nav_links += f'<a href="#section-{num}">{num}. {_e(question)}</a>'

    # Scoring quick stats for header
    scoring = state.get("scoring", {})
    tier_data = scoring.get("tier", {})
    tier_name = tier_data.get("tier", "N/A") if isinstance(tier_data, dict) else "N/A"
    quality_score = _safe_float(scoring.get("quality_score"))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>D&amp;O Underwriting Report &mdash; {_e(ticker)}</title>
  <style>{_CSS}</style>
</head>
<body>
  <div class="report-container">
    <div class="report-header">
      <h1>{_e(company_name)} ({_e(ticker)})</h1>
      <div class="subtitle">D&amp;O Liability Underwriting &mdash; Question-Driven Report</div>
      <div class="meta">
        <span>Tier: <strong>{_e(tier_name)}</strong></span>
        <span>Quality Score: <strong>{quality_score:.1f}/100</strong></span>
        <span>Generated: <strong>{_e(date_str)}</strong></span>
      </div>
    </div>

    <div class="nav-bar">{nav_links}</div>

    {sections_html}

    <div class="report-footer">
      D&amp;O Underwriting Worksheet System &mdash; Question-Driven Report &mdash; {_e(ticker)} &mdash; {_e(date_str)}
    </div>
  </div>
</body>
</html>"""

    # Write output
    output_file = output_path / f"{ticker}_qd_report.html"
    output_file.write_text(html, encoding="utf-8")
    logger.info("Question-driven report written to %s", output_file)
    return output_file


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import platform

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if len(sys.argv) < 2:
        print("Usage: python qd_report.py <output_dir>")
        print("Example: python qd_report.py output/AAPL/")
        sys.exit(1)

    output_dir = sys.argv[1]
    try:
        result_path = render_qd_report(output_dir)
        print(f"Report generated: {result_path}")

        # Try to open in browser
        if platform.system() == "Darwin":
            subprocess.run(["open", str(result_path)], check=False)
        elif platform.system() == "Linux":
            subprocess.run(["xdg-open", str(result_path)], check=False)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
