"""Private helpers for financial sub-narratives.

Split from md_narrative.py for 500-line compliance.
These functions generate specific financial narrative components:
distress models, leverage, earnings quality, audit risk, and
D&O financial conclusions.
"""

from __future__ import annotations

from typing import Any

from do_uw.stages.render.formatters import format_currency, format_percentage


def distress_narrative(fin: Any) -> list[str]:
    """Generate distress model interpretation."""
    parts: list[str] = []
    z = fin.distress.altman_z_score
    o = fin.distress.ohlson_o_score
    p = fin.distress.piotroski_f_score

    if z and z.score is not None and o and o.score is not None:
        z_val, z_zone = z.score, str(z.zone)
        o_val, o_zone = o.score, str(o.zone)

        if z_zone == "safe" and o_zone == "safe":
            if z_val > 10:
                parts.append(
                    f"Financial health is exceptionally strong: Altman"
                    f" Z-Score of {z_val:.2f} (safe zone threshold: 2.99)"
                    f" indicates negligible bankruptcy risk. Ohlson O-Score"
                    f" of {o_val:.2f} confirms no distress signals."
                )
            else:
                parts.append(
                    f"Both distress models indicate stability: Z-Score"
                    f" {z_val:.2f} (safe above 2.99) and O-Score"
                    f" {o_val:.2f} (safe below 0.5)."
                )
        elif z_zone == "grey" or o_zone == "grey":
            parts.append(
                f"Distress indicators show mixed signals: Z-Score"
                f" {z_val:.2f} ({z_zone} zone) and O-Score {o_val:.2f}"
                f" ({o_zone} zone). Financial stress could limit"
                " litigation defense resources."
            )
        elif z_zone == "distress" or o_zone == "distress":
            parts.append(
                f"**Distress warning**: Z-Score {z_val:.2f} ({z_zone}"
                f" zone) and O-Score {o_val:.2f} ({o_zone} zone)"
                " indicate elevated bankruptcy risk. Directors face"
                " heightened fiduciary duty scrutiny near insolvency."
            )

    if p and p.score is not None:
        p_val = int(p.score)
        if p_val <= 3:
            parts.append(
                f"Piotroski F-Score of {p_val}/9 signals weak"
                " fundamentals across profitability, leverage, and"
                " operating efficiency dimensions."
            )
        elif p_val >= 7:
            parts.append(
                f"Piotroski F-Score of {p_val}/9 indicates strong"
                " fundamental quality."
            )
    return parts


def leverage_narrative(fin: Any) -> list[str]:
    """Generate leverage and debt narrative."""
    parts: list[str] = []
    if fin.leverage is not None:
        lev = fin.leverage.value
        dte = lev.get("debt_to_equity")
        ic = lev.get("interest_coverage")
        if dte is not None:
            if dte < 0.3:
                parts.append(
                    f"Capital structure is conservative with D/E ratio"
                    f" of {dte:.2f}, providing meaningful headroom"
                    " against financial covenant triggers."
                )
            elif dte > 2.0:
                parts.append(
                    f"Leverage is elevated with D/E ratio of {dte:.2f}."
                    " High debt-to-equity increases refinancing risk"
                    " and amplifies stock price sensitivity to earnings"
                    " misses."
                )
            else:
                parts.append(f"D/E ratio of {dte:.2f} is moderate.")
        if ic is not None and ic < 3.0:
            parts.append(
                f"Interest coverage of {ic:.1f}x is thin, raising"
                " concerns about debt service sustainability."
            )
    if fin.debt_structure is not None:
        ds = fin.debt_structure.value
        near_term = ds.get("near_term_maturities")
        if near_term and near_term > 0:
            parts.append(
                f"Near-term debt maturities of"
                f" {format_currency(near_term, compact=True)} require"
                " refinancing attention."
            )
    return parts


def earnings_quality_narrative(fin: Any) -> list[str]:
    """Generate earnings quality narrative."""
    parts: list[str] = []
    if fin.earnings_quality is not None:
        eq = fin.earnings_quality.value
        ocf = eq.get("ocf_to_ni")
        acr = eq.get("accruals_ratio")
        if ocf is not None:
            if ocf > 0.8:
                parts.append(
                    f"Earnings quality is healthy (OCF/NI: {ocf:.2f}),"
                    " indicating reported income is well-supported by"
                    " operating cash flows -- reducing restatement risk."
                )
            elif ocf < 0.5:
                parts.append(
                    f"**Earnings quality concern** (OCF/NI: {ocf:.2f}):"
                    " low cash conversion suggests reported income may"
                    " include material non-cash items, increasing"
                    " restatement risk and SCA exposure."
                )
        if acr is not None and acr > 0.1:
            parts.append(
                f"Accruals ratio of {acr:.2f} exceeds the 0.10"
                " threshold associated with earnings management risk."
            )
    if fin.tax_indicators is not None:
        tax = fin.tax_indicators.value
        etr = tax.get("effective_tax_rate")
        if etr is not None:
            etr_pct = etr * 100 if etr <= 1.0 else etr
            if etr_pct < 15:
                parts.append(
                    f"Effective tax rate of {etr_pct:.1f}% is below the"
                    " 21% U.S. statutory rate, warranting review of"
                    " uncertain tax positions and transfer pricing."
                )
    return parts


def audit_narrative(fin: Any) -> list[str]:
    """Generate audit risk narrative."""
    parts: list[str] = []
    audit = fin.audit
    if audit.material_weaknesses:
        count = len(audit.material_weaknesses)
        parts.append(
            f"**{count} material weakness(es) in internal controls**"
            " identified -- a direct D&O exposure factor that"
            " significantly increases restatement and SCA risk."
        )
    if audit.going_concern and audit.going_concern.value:
        parts.append(
            "**Going concern qualification** from the auditor signals"
            " substantial doubt about continuing as a going concern."
        )
    if audit.auditor_name:
        name = audit.auditor_name.value
        is_big4 = audit.is_big4.value if audit.is_big4 else False
        tenure = audit.tenure_years.value if audit.tenure_years else None
        desc = f"Auditor: {name}"
        if is_big4:
            desc += " (Big 4)"
        if tenure is not None:
            desc += f", tenure: {tenure} years"
            if tenure > 20:
                desc += " -- extended tenure may raise independence concerns"
        parts.append(desc + ".")
    return parts


def financial_do_conclusion(fin: Any) -> str:
    """Generate D&O-specific financial conclusion."""
    risk_signals: list[str] = []
    z = fin.distress.altman_z_score
    if z and z.zone and str(z.zone) == "distress":
        risk_signals.append("distress-level financial health")
    if fin.audit.material_weaknesses:
        risk_signals.append("material weaknesses in internal controls")
    if fin.audit.going_concern and fin.audit.going_concern.value:
        risk_signals.append("going concern qualification")
    eq = fin.earnings_quality
    if eq and eq.value.get("ocf_to_ni") is not None:
        if eq.value["ocf_to_ni"] < 0.5:
            risk_signals.append("poor earnings quality")
    if not risk_signals:
        return (
            "From a D&O perspective, the financial profile supports"
            " standard underwriting terms."
        )
    return (
        f"D&O underwriting concern: {', '.join(risk_signals)}"
        " collectively elevate the probability of securities claims"
        " and should be reflected in pricing and terms."
    )


def financial_narrative_from_dict(fin: dict[str, Any]) -> str:
    """Legacy wrapper for dict-based financial narrative."""
    if not fin or not fin.get("has_income"):
        return ""
    parts: list[str] = []
    rev = fin.get("revenue", "N/A")
    ni = fin.get("net_income", "N/A")
    period = fin.get("latest_period", "")
    plabel = f" for {period}" if period else ""
    if rev != "N/A" and ni != "N/A":
        parts.append(
            f"The company reported revenue of {rev} and net income"
            f" of {ni}{plabel}."
        )
    z_score = fin.get("z_score", "N/A")
    z_zone = fin.get("z_zone", "N/A")
    o_score = fin.get("o_score", "N/A")
    o_zone = fin.get("o_zone", "N/A")
    if z_score != "N/A" and o_score != "N/A":
        parts.append(
            f"Distress models: Z-Score {z_score} ({z_zone}) and"
            f" O-Score {o_score} ({o_zone})."
        )
    return " ".join(parts) if parts else ""


def market_narrative_from_dict(mkt: dict[str, Any]) -> str:
    """Legacy wrapper for dict-based market narrative."""
    if not mkt:
        return ""
    pct = mkt.get("pct_off_high", "N/A")
    if pct == "N/A":
        return ""
    try:
        pct_val = abs(float(str(pct).replace("%", "").replace("-", "")))
    except ValueError:
        return ""
    current = mkt.get("current_price", "N/A")
    high = mkt.get("high_52w", "N/A")
    if pct_val < 15:
        return (
            f"The stock trades {pct} below its 52-week high ({high}),"
            " within normal trading variance."
        )
    if pct_val < 50:
        return (
            f"The stock has declined {pct} from its 52-week high"
            f" ({high} to {current}), increasing SCA filing probability."
        )
    return (
        f"The stock has suffered a severe {pct} decline from"
        f" its 52-week high ({high} to {current})."
    )


def insider_narrative_from_dict(mkt: dict[str, Any]) -> str:
    """Legacy wrapper for dict-based insider narrative."""
    summary = mkt.get("insider_summary", "")
    if not summary or "No insider trading data" in summary:
        return ""
    if "NET_SELLING" in summary:
        return "Insiders are net sellers over the measured period."
    if "NET_BUYING" in summary:
        return (
            "Insiders are net buyers -- a positive signal indicating"
            " management confidence."
        )
    return ""


_ = format_percentage  # suppress unused import (used in leverage_narrative)
