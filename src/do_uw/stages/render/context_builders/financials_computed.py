"""Computed financial metrics — Tier A computable items.

Goodwill/equity ratio, capital allocation, debt service coverage,
refinancing risk, bankruptcy composite, and audit disclosure alerts.

All computations use safe_float() for numeric safety.
"""

from __future__ import annotations

from typing import Any

from do_uw.stages.render.formatters import (
    format_currency,
    safe_float,
)


def _find_line_item_value(
    items: list[Any], label: str, period_idx: int = 0,
) -> float | None:
    """Find a line item by label and return a specific period's value.

    Local copy to avoid circular import with financials.py.
    """
    search = label.lower().replace(" ", "_")
    for item in items:
        normalized = item.label.lower().replace(" ", "_")
        if normalized == search or search in normalized:
            vals = list(item.values.values())
            if len(vals) > period_idx and vals[period_idx] is not None:
                return float(vals[period_idx].value)
    return None


def build_goodwill_equity_ratio(stmts: Any, result: dict[str, Any]) -> None:
    """Compute goodwill + intangibles as % of stockholders' equity."""
    if stmts.balance_sheet is None:
        return
    bs = stmts.balance_sheet.line_items
    goodwill = _find_line_item_value(bs, "goodwill")
    intangibles = _find_line_item_value(bs, "intangible_assets")
    equity = _find_line_item_value(bs, "stockholders_equity")
    if equity is None:
        equity = _find_line_item_value(bs, "stockholders")
    if goodwill is None or equity is None or equity == 0:
        return
    gw = safe_float(goodwill, 0.0)
    intang = safe_float(intangibles, 0.0) if intangibles is not None else 0.0
    eq = safe_float(equity, 0.0)
    if eq == 0:
        return
    ratio_pct = (gw + intang) / eq * 100
    color = "red" if ratio_pct > 100 else ("amber" if ratio_pct > 50 else "green")
    result["goodwill_equity_pct"] = {
        "value": f"{ratio_pct:.1f}%",
        "raw": ratio_pct,
        "goodwill": format_currency(gw, compact=True),
        "intangibles": format_currency(intang, compact=True) if intang > 0 else None,
        "equity": format_currency(eq, compact=True),
        "color": color,
    }


def build_capital_allocation(stmts: Any, result: dict[str, Any]) -> None:
    """Build capital allocation view showing FCF deployment breakdown."""
    if stmts.cash_flow is None:
        return
    cf = stmts.cash_flow.line_items
    ocf_val = _find_line_item_value(cf, "operating_activities")
    capex_val = _find_line_item_value(cf, "capital_expenditures")
    fcf_val = _find_line_item_value(cf, "free_cash_flow")
    divs_val = _find_line_item_value(cf, "dividends_paid")
    buyback_val = _find_line_item_value(cf, "share_repurchases")
    debt_repay_val = _find_line_item_value(cf, "repayments_of_debt")
    if debt_repay_val is None:
        debt_repay_val = _find_line_item_value(cf, "repayment")

    if ocf_val is None or capex_val is None:
        return

    ocf = safe_float(ocf_val, 0.0)
    capex = abs(safe_float(capex_val, 0.0))
    fcf = safe_float(fcf_val, 0.0) if fcf_val is not None else (ocf - capex)
    divs = abs(safe_float(divs_val, 0.0)) if divs_val is not None else 0.0
    buybacks = abs(safe_float(buyback_val, 0.0)) if buyback_val is not None else 0.0
    debt_repay = abs(safe_float(debt_repay_val, 0.0)) if debt_repay_val is not None else 0.0

    if fcf == 0:
        return

    components: list[dict[str, Any]] = []
    total_deployed = 0.0

    if divs > 0:
        pct = divs / abs(fcf) * 100
        total_deployed += divs
        components.append({
            "label": "Dividends",
            "amount": format_currency(divs, compact=True),
            "pct_of_fcf": f"{pct:.1f}%",
            "raw_pct": pct,
        })
    if buybacks > 0:
        pct = buybacks / abs(fcf) * 100
        total_deployed += buybacks
        components.append({
            "label": "Share Repurchases",
            "amount": format_currency(buybacks, compact=True),
            "pct_of_fcf": f"{pct:.1f}%",
            "raw_pct": pct,
        })
    if capex > 0:
        pct = capex / abs(fcf) * 100
        total_deployed += capex
        components.append({
            "label": "Capital Expenditures",
            "amount": format_currency(capex, compact=True),
            "pct_of_fcf": f"{pct:.1f}%",
            "raw_pct": pct,
        })
    if debt_repay > 0:
        pct = debt_repay / abs(fcf) * 100
        total_deployed += debt_repay
        components.append({
            "label": "Debt Repayment",
            "amount": format_currency(debt_repay, compact=True),
            "pct_of_fcf": f"{pct:.1f}%",
            "raw_pct": pct,
        })

    total_pct = total_deployed / abs(fcf) * 100
    distributions_only = divs + buybacks
    dist_pct = distributions_only / abs(fcf) * 100 if fcf != 0 else 0
    buyback_pct = buybacks / abs(fcf) * 100 if fcf != 0 else 0

    color = "green"
    if dist_pct > 120:
        color = "red"
    elif buyback_pct > 80:
        color = "amber"

    result["capital_allocation"] = {
        "fcf": format_currency(fcf, compact=True),
        "fcf_raw": fcf,
        "components": components,
        "total_deployed_pct": f"{total_pct:.1f}%",
        "distributions_pct": f"{dist_pct:.1f}%",
        "color": color,
    }


def build_debt_service_coverage(
    stmts: Any, fin: Any, result: dict[str, Any],
) -> None:
    """Compute FCF / total debt service coverage ratio."""
    if stmts.cash_flow is None:
        return
    cf = stmts.cash_flow.line_items
    fcf_val = _find_line_item_value(cf, "free_cash_flow")
    if fcf_val is None:
        ocf = _find_line_item_value(cf, "operating_activities")
        capex = _find_line_item_value(cf, "capital_expenditures")
        if ocf is not None and capex is not None:
            fcf_val = safe_float(ocf, 0.0) - abs(safe_float(capex, 0.0))

    interest_paid = _find_line_item_value(cf, "interest_paid")
    if interest_paid is None and stmts.income_statement is not None:
        interest_paid = _find_line_item_value(
            stmts.income_statement.line_items, "interest_expense",
        )

    debt_repay = _find_line_item_value(cf, "repayments_of_debt")
    if debt_repay is None:
        debt_repay = _find_line_item_value(cf, "repayment")

    if fcf_val is None:
        return

    fcf = safe_float(fcf_val, 0.0)
    interest = abs(safe_float(interest_paid, 0.0)) if interest_paid is not None else 0.0
    repay = abs(safe_float(debt_repay, 0.0)) if debt_repay is not None else 0.0
    total_service = interest + repay
    if total_service == 0:
        return

    ratio = fcf / total_service
    color = "red" if ratio < 1.0 else ("amber" if ratio < 2.0 else "green")
    result["debt_service_coverage"] = {
        "value": f"{ratio:.2f}x",
        "raw": ratio,
        "fcf": format_currency(fcf, compact=True),
        "interest": format_currency(interest, compact=True),
        "debt_repayment": format_currency(repay, compact=True),
        "color": color,
    }


def build_refinancing_risk(
    stmts: Any, fin: Any, result: dict[str, Any],
) -> None:
    """Compute refinancing risk from short-term debt concentration + cash."""
    if stmts.balance_sheet is None:
        return
    bs = stmts.balance_sheet.line_items
    st_debt = _find_line_item_value(bs, "short_term_debt")
    if st_debt is None:
        st_debt = _find_line_item_value(bs, "current_portion")
    if st_debt is None:
        st_debt = _find_line_item_value(bs, "debt_current")
    total_debt = _find_line_item_value(bs, "total_debt")
    if total_debt is None:
        lt_debt = _find_line_item_value(bs, "long_term_debt")
        if lt_debt is not None and st_debt is not None:
            total_debt = safe_float(st_debt, 0.0) + safe_float(lt_debt, 0.0)

    if st_debt is None or total_debt is None or safe_float(total_debt, 0.0) == 0:
        return

    st = safe_float(st_debt, 0.0)
    total = safe_float(total_debt, 0.0)
    st_pct = st / total * 100

    days_cash: float | None = None
    liq_sv = getattr(fin, "liquidity", None)
    if liq_sv is not None:
        liq = liq_sv.value if hasattr(liq_sv, "value") else liq_sv
        if isinstance(liq, dict):
            dch = liq.get("days_cash_on_hand")
            if dch is not None:
                days_cash = safe_float(dch, None)

    color = "green"
    if st_pct > 40 and (days_cash is not None and days_cash < 90):
        color = "red"
    elif st_pct > 30:
        color = "amber"

    result["refinancing_risk"] = {
        "st_debt_pct": f"{st_pct:.1f}%",
        "raw_pct": st_pct,
        "st_debt": format_currency(st, compact=True),
        "total_debt": format_currency(total, compact=True),
        "days_cash": f"{days_cash:.0f}" if days_cash is not None else "N/A",
        "color": color,
    }


def build_bankruptcy_composite(fin: Any, result: dict[str, Any]) -> None:
    """Compute unified bankruptcy risk score (0-100) from multiple models."""
    score = 0
    components: list[dict[str, Any]] = []
    distress = fin.distress

    # Altman Z-Score: <1.8 = 30pts, <3.0 = 15pts
    z = distress.altman_z_score
    if z and z.score is not None:
        z_val = safe_float(z.score, 3.0)
        if z_val < 1.8:
            score += 30
            components.append({"label": "Altman Z-Score", "value": f"{z_val:.2f}", "points": 30, "status": "Distress zone"})
        elif z_val < 3.0:
            score += 15
            components.append({"label": "Altman Z-Score", "value": f"{z_val:.2f}", "points": 15, "status": "Grey zone"})
        else:
            components.append({"label": "Altman Z-Score", "value": f"{z_val:.2f}", "points": 0, "status": "Safe zone"})

    # Going concern: 40pts
    audit = fin.audit
    gc = audit.going_concern
    if gc is not None:
        gc_val = gc.value if hasattr(gc, "value") else gc
        if gc_val is True:
            score += 40
            components.append({"label": "Going Concern", "value": "Yes", "points": 40, "status": "Disclosed"})
        else:
            components.append({"label": "Going Concern", "value": "No", "points": 0, "status": "Not disclosed"})

    # Current ratio: <0.5 = 20pts
    liq_sv = getattr(fin, "liquidity", None)
    if liq_sv is not None:
        liq = liq_sv.value if hasattr(liq_sv, "value") else liq_sv
        if isinstance(liq, dict):
            cr = liq.get("current_ratio")
            if cr is not None:
                cr_f = safe_float(cr, 1.0)
                if cr_f < 0.5:
                    score += 20
                    components.append({"label": "Current Ratio", "value": f"{cr_f:.2f}", "points": 20, "status": "Critical"})
                else:
                    components.append({"label": "Current Ratio", "value": f"{cr_f:.2f}", "points": 0, "status": "Adequate"})

            dch = liq.get("days_cash_on_hand")
            if dch is not None:
                dch_f = safe_float(dch, 90.0)
                if dch_f < 30:
                    score += 10
                    components.append({"label": "Days Cash", "value": f"{dch_f:.0f}", "points": 10, "status": "Critical"})
                else:
                    components.append({"label": "Days Cash", "value": f"{dch_f:.0f}", "points": 0, "status": "Adequate"})

    if not components:
        return

    color = "red" if score > 50 else ("amber" if score > 25 else "green")
    result["bankruptcy_composite"] = {
        "score": score,
        "color": color,
        "components": components,
    }


def build_audit_disclosure_alerts(
    signal_results: dict[str, Any] | None,
    fin: Any,
    result: dict[str, Any],
) -> None:
    """Build alert cards for restatement, auditor change, MW, Q4 loading."""
    from do_uw.stages.render.context_builders._signal_fallback import safe_get_result

    alerts: list[dict[str, Any]] = []

    # 1. Restatement history
    restate_sig = safe_get_result(signal_results, "FIN.ACCT.restatement")
    if restate_sig and getattr(restate_sig, "status", "") == "TRIGGERED":
        alerts.append({
            "type": "restatement",
            "severity": "red",
            "title": "Restatement History",
            "detail": restate_sig.evidence or "10-K/A filing detected",
            "do_context": restate_sig.do_context or "",
        })

    # 2. Auditor change
    auditor_sig = safe_get_result(signal_results, "GOV.EFFECT.auditor_change")
    if auditor_sig:
        val = getattr(auditor_sig, "value", None)
        status = getattr(auditor_sig, "status", "")
        if val is True or status == "TRIGGERED":
            alerts.append({
                "type": "auditor_change",
                "severity": "red",
                "title": "Auditor Change Detected",
                "detail": auditor_sig.evidence or "8-K Item 4.01 auditor change detected",
                "do_context": auditor_sig.do_context or "",
            })

    # 3. Material weakness
    mw_sig = safe_get_result(signal_results, "FIN.ACCT.material_weakness")
    if mw_sig and getattr(mw_sig, "status", "") == "TRIGGERED":
        alerts.append({
            "type": "material_weakness",
            "severity": "red",
            "title": "Material Weakness in Internal Controls",
            "detail": mw_sig.evidence or "Material weakness disclosed in 10-K",
            "do_context": mw_sig.do_context or "",
        })

    # 4. Q4 revenue loading
    q4_sig = safe_get_result(signal_results, "FIN.QUALITY.q4_revenue_concentration")
    if q4_sig:
        status = getattr(q4_sig, "status", "")
        if status in ("TRIGGERED", "ELEVATED"):
            q4_val = getattr(q4_sig, "value", None)
            detail = (
                f"Q4 represents {q4_val}% of annual revenue"
                if q4_val else "Q4 revenue concentration detected"
            )
            alerts.append({
                "type": "q4_loading",
                "severity": "amber",
                "title": "Q4 Revenue Loading",
                "detail": detail,
                "do_context": q4_sig.do_context or "",
            })

    result["audit_disclosure_alerts"] = alerts
