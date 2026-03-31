"""Per-section data extractors for LLM narrative prompts.

Split from narrative_data.py for 500-line compliance.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.sca_counter import get_active_genuine_scas


def _company_name(state: AnalysisState) -> str | None:
    """Extract company legal name from state."""
    if state.company and state.company.identity.legal_name:
        return state.company.identity.legal_name.value
    return None


def _factor_data(state: AnalysisState, factor_id: str) -> dict[str, Any]:
    """Extract scoring factor deduction data."""
    if not state.scoring or not state.scoring.factor_scores:
        return {}
    for f in state.scoring.factor_scores:
        if f.factor_id == factor_id:
            key = factor_id.lower()
            return {
                f"{key}_points_deducted": f.points_deducted,
                f"{key}_max_points": f.max_points,
                f"{key}_evidence": f.evidence[:5],
            }
    return {}


def extract_company(state: AnalysisState) -> dict[str, Any]:
    """Extract company profile data for LLM narrative prompt."""
    data: dict[str, Any] = {}
    if not state.company:
        return data
    prof = state.company
    identity = prof.identity
    data["legal_name"] = identity.legal_name.value if identity.legal_name else None
    data["ticker"] = state.ticker
    data["sector"] = str(identity.sector.value) if identity.sector else None
    if identity.sic_code:
        data["sic_code"] = identity.sic_code.value
    data["market_cap"] = float(prof.market_cap.value) if prof.market_cap else None
    if prof.employee_count:
        data["employees"] = prof.employee_count.value
    if prof.years_public is not None:
        data["years_public"] = prof.years_public
    if prof.business_description and prof.business_description.value:
        desc = str(prof.business_description.value)
        data["business_description"] = desc[:400]
    if prof.filer_category and prof.filer_category.value:
        data["filer_category"] = prof.filer_category.value
    if prof.risk_classification:
        data["risk_classification"] = prof.risk_classification.value
    if prof.do_exposure_factors:
        data["exposure_factors"] = [
            f.value.get("factor", "") for f in prof.do_exposure_factors[:5]
        ]
    # Revenue segments
    if prof.revenue_segments:
        segs = []
        for seg_sv in prof.revenue_segments[:5]:
            seg = seg_sv.value
            segs.append(
                {
                    "name": seg.get("name", seg.get("segment", "")),
                    "revenue": seg.get("revenue"),
                    "percentage": seg.get("percentage"),
                }
            )
        data["revenue_segments"] = segs
    # Geographic footprint
    if prof.geographic_footprint:
        data["geographic_footprint"] = [
            str(g.value.get("jurisdiction", g.value.get("region", "")))
            for g in prof.geographic_footprint[:5]
        ]
    # FPI status
    if identity.is_fpi:
        data["is_fpi"] = True
    return data


def extract_financial(state: AnalysisState) -> dict[str, Any]:
    """Extract financial health data for LLM narrative prompt."""
    data: dict[str, Any] = {}
    if not state.extracted:
        return data
    fin = state.extracted.financials
    if not fin:
        return data

    # Company name for context
    cn = _company_name(state)
    if cn:
        data["company_name"] = cn

    # Revenue and income from XBRL-reconciled income statement line items
    # (FIX-01: uses XBRL-sourced data, not LLM extraction, to prevent hallucination)
    stmts = fin.statements
    if stmts.income_statement and stmts.income_statement.line_items:
        items = stmts.income_statement.line_items
        for label_key in (
            "total_revenue",
            "net_income",
            "earnings_per_share",
            "operating_income",
            "gross_profit",
        ):
            for item in items:
                norm = item.label.lower().replace(" ", "_")
                if label_key in norm:
                    vals = list(item.values.values())
                    if vals and vals[0] is not None:
                        data[label_key] = float(vals[0].value)
                        if len(vals) > 1 and vals[1] is not None:
                            data[f"{label_key}_prior"] = float(vals[1].value)
                    break

    # Distress models -- all 4 with scores AND zones
    d = fin.distress
    data["altman_z"] = d.altman_z_score.score if d.altman_z_score else None
    data["altman_zone"] = str(d.altman_z_score.zone) if d.altman_z_score else None
    data["ohlson_o"] = d.ohlson_o_score.score if d.ohlson_o_score else None
    data["ohlson_zone"] = (
        str(d.ohlson_o_score.zone)
        if d.ohlson_o_score and hasattr(d.ohlson_o_score, "zone")
        else None
    )
    if d.piotroski_f_score:
        data["piotroski_f"] = d.piotroski_f_score.score
        data["piotroski_zone"] = (
            str(d.piotroski_f_score.zone) if hasattr(d.piotroski_f_score, "zone") else None
        )
    if d.beneish_m_score:
        data["beneish_m"] = d.beneish_m_score.score
        data["beneish_zone"] = (
            str(d.beneish_m_score.zone) if hasattr(d.beneish_m_score, "zone") else None
        )

    # Debt structure
    debt = fin.debt_structure
    if debt and debt.value and isinstance(debt.value, dict):
        total_debt = debt.value.get("total_debt")
        if total_debt is not None:
            data["total_debt"] = float(total_debt)
    # Liquidity ratios
    if fin.liquidity and fin.liquidity.value and isinstance(fin.liquidity.value, dict):
        liq = fin.liquidity.value
        data["current_ratio"] = liq.get("current_ratio")
        data["quick_ratio"] = liq.get("quick_ratio")
    # Leverage ratios
    if fin.leverage and fin.leverage.value and isinstance(fin.leverage.value, dict):
        lev = fin.leverage.value
        data["debt_to_equity"] = lev.get("debt_to_equity")
        data["interest_coverage"] = lev.get("interest_coverage")
    # Earnings quality
    if (
        fin.earnings_quality
        and fin.earnings_quality.value
        and isinstance(fin.earnings_quality.value, dict)
    ):
        eq = fin.earnings_quality.value
        data["ocf_to_ni"] = eq.get("ocf_to_ni")
        data["accrual_ratio"] = eq.get("accrual_ratio")
    # Audit profile
    audit = fin.audit
    if audit:
        data["has_material_weakness"] = (
            bool(audit.material_weaknesses) if audit.material_weaknesses else False
        )
        data["going_concern"] = bool(audit.going_concern.value) if audit.going_concern else None
        if audit.auditor_name:
            data["auditor"] = audit.auditor_name.value
        if audit.tenure_years:
            data["auditor_tenure_years"] = audit.tenure_years.value

    # Scoring factor F3 (Financial Health) contribution
    data.update(_factor_data(state, "F3"))

    # Triggered check count
    if state.analysis and state.analysis.signal_results:
        fin_checks = {
            k: v
            for k, v in state.analysis.signal_results.items()
            if isinstance(v, dict) and k.startswith("FIN.")
        }
        data["fin_checks_total"] = len(fin_checks)
        data["fin_triggered"] = sum(
            1 for v in fin_checks.values() if v.get("status") == "TRIGGERED"
        )
    return data


def extract_market(state: AnalysisState) -> dict[str, Any]:
    """Extract market events data for LLM narrative prompt."""
    data: dict[str, Any] = {}
    if not state.extracted or not state.extracted.market:
        return data
    mkt = state.extracted.market
    stock = mkt.stock

    # Company name for context
    cn = _company_name(state)
    if cn:
        data["company_name"] = cn

    # Stock price data
    if stock.current_price:
        data["current_price"] = float(stock.current_price.value)
    if stock.high_52w:
        data["high_52w"] = float(stock.high_52w.value)
    if stock.low_52w:
        data["low_52w"] = float(stock.low_52w.value)
    data["decline_from_high_pct"] = (
        float(stock.decline_from_high_pct.value) if stock.decline_from_high_pct else None
    )
    if stock.sector_relative_performance:
        data["sector_relative_pct"] = float(
            stock.sector_relative_performance.value,
        )

    # Short interest
    si = mkt.short_interest
    data["short_pct_float"] = float(si.short_pct_float.value) if si.short_pct_float else None
    if si.trend_6m and si.trend_6m.value:
        data["short_trend_6m"] = str(si.trend_6m.value)

    # Stock drops
    drops = mkt.stock_drops
    if drops.worst_single_day and drops.worst_single_day.drop_pct:
        data["worst_drop_pct"] = float(
            drops.worst_single_day.drop_pct.value,
        )
        if drops.worst_single_day.date:
            data["worst_drop_date"] = str(drops.worst_single_day.date.value)
        if drops.worst_single_day.trigger_event:
            data["worst_drop_trigger"] = str(
                drops.worst_single_day.trigger_event.value,
            )
    if getattr(drops, "significant_drops", None):
        data["significant_drops_count"] = len(drops.significant_drops)

    # Insider activity
    ia = mkt.insider_analysis
    if ia.net_buying_selling and ia.net_buying_selling.value:
        data["insider_direction"] = str(ia.net_buying_selling.value)
    # Compute total insider selling value from transactions
    total_sell_value = 0.0
    for txn in ia.transactions:
        if txn.transaction_type == "SELL" and txn.total_value and txn.total_value.value:
            total_sell_value += float(txn.total_value.value)
    if total_sell_value > 0:
        data["total_insider_selling"] = total_sell_value
    if ia.pct_10b5_1 and ia.pct_10b5_1.value is not None:
        data["pct_10b5_1"] = float(ia.pct_10b5_1.value)
    if ia.cluster_events:
        data["cluster_event_count"] = len(ia.cluster_events)

    # Executive departures
    if state.extracted.governance:
        gov = state.extracted.governance
        departures = gov.leadership.departures_18mo
        if departures:
            data["departures_18mo"] = len(departures)
            unplanned = [d for d in departures if d.departure_type == "UNPLANNED"]
            data["unplanned_departures"] = len(unplanned)
            dep_details = []
            for dep in departures[:5]:
                dep_details.append(
                    {
                        "name": dep.name.value if dep.name else "",
                        "title": dep.title.value if dep.title else "",
                        "type": dep.departure_type or "",
                    }
                )
            data["departure_details"] = dep_details

    # Analyst consensus
    analyst = mkt.analyst
    if analyst.consensus and analyst.consensus.value:
        data["analyst_consensus"] = str(analyst.consensus.value)
        data["recent_downgrades"] = analyst.recent_downgrades
        data["recent_upgrades"] = analyst.recent_upgrades

    # Scoring factors F2 (Stock Drop) and F7 (Insider Selling)
    data.update(_factor_data(state, "F2"))
    data.update(_factor_data(state, "F7"))
    return data


def extract_governance(state: AnalysisState) -> dict[str, Any]:
    """Extract governance data for LLM narrative prompt."""
    data: dict[str, Any] = {}
    if not state.extracted or not state.extracted.governance:
        return data

    # Company name for context
    cn = _company_name(state)
    if cn:
        data["company_name"] = cn

    gov = state.extracted.governance
    board = gov.board
    data["independence_ratio"] = (
        float(board.independence_ratio.value) if board.independence_ratio else None
    )
    data["ceo_chair_duality"] = (
        bool(board.ceo_chair_duality.value) if board.ceo_chair_duality else None
    )
    if board.size:
        data["board_size"] = board.size.value if hasattr(board.size, "value") else board.size
    if board.avg_tenure_years:
        data["avg_board_tenure"] = (
            board.avg_tenure_years.value
            if hasattr(board.avg_tenure_years, "value")
            else board.avg_tenure_years
        )
    gs = gov.governance_score
    data["total_score"] = float(gs.total_score.value) if gs.total_score else None
    # Executive details
    leadership = gov.leadership
    if leadership and leadership.executives:
        execs = []
        for e in leadership.executives[:6]:
            name = e.name.value if e.name and e.name.value else ""
            title = e.title.value if e.title and e.title.value else ""
            tenure = e.tenure_years
            execs.append({"name": name, "title": title, "tenure_years": tenure})
        data["executives"] = execs
        data["exec_count"] = len(leadership.executives)
        data["execs_with_tenure"] = sum(
            1 for e in leadership.executives if e.tenure_years is not None
        )
    # Board forensic profiles
    if gov.board_forensics:
        directors = []
        for b in gov.board_forensics[:8]:
            name = b.name.value if b.name and b.name.value else ""
            is_ind = b.is_independent.value if b.is_independent else None
            tenure = b.tenure_years.value if b.tenure_years else None
            quals = b.qualifications.value if getattr(b, "qualifications", None) else ""
            directors.append(
                {
                    "name": name,
                    "independent": is_ind,
                    "tenure_years": tenure,
                    "qualifications": quals[:100],
                }
            )
        data["directors"] = directors
        data["director_count"] = len(gov.board_forensics)
    # Compensation data
    comp = gov.comp_analysis
    if comp.say_on_pay_pct is not None:
        data["say_on_pay_pct"] = float(comp.say_on_pay_pct.value)
    if comp.ceo_total_comp is not None:
        ceo_val = float(comp.ceo_total_comp.value)
        # Filter out year-as-comp extraction bugs
        if ceo_val > 50_000 and not (1990 <= ceo_val <= 2035):
            data["ceo_total_comp"] = ceo_val
    if comp.comp_mix:
        data["comp_mix"] = comp.comp_mix

    # Anti-takeover provisions
    if board.classified_board and board.classified_board.value:
        data["classified_board"] = True
    if board.dual_class_structure and board.dual_class_structure.value:
        data["dual_class"] = True
    if board.overboarded_count is not None:
        data["overboarded_count"] = int(board.overboarded_count.value)

    # Scoring factor F6 (Governance) contribution
    data.update(_factor_data(state, "F6"))

    # Triggered governance checks
    if state.analysis and state.analysis.signal_results:
        gov_checks = {
            k: v
            for k, v in state.analysis.signal_results.items()
            if isinstance(v, dict) and k.startswith("GOV.")
        }
        data["gov_checks_total"] = len(gov_checks)
        data["gov_triggered"] = sum(
            1 for v in gov_checks.values() if v.get("status") == "TRIGGERED"
        )
    return data


def extract_litigation(state: AnalysisState) -> dict[str, Any]:
    """Extract litigation data for LLM narrative prompt."""
    data: dict[str, Any] = {}
    if not state.extracted or not state.extracted.litigation:
        return data

    # Company name for context
    cn = _company_name(state)
    if cn:
        data["company_name"] = cn

    lit = state.extracted.litigation

    # Active SCA details -- uses canonical counter to exclude DOJ_FCPA and
    # other regulatory cases misclassified as SCAs (Plan 129-01/02 fix).
    active_scas = get_active_genuine_scas(state)
    data["active_sca_count"] = len(active_scas)
    sca_details = []
    for c in active_scas[:5]:
        detail: dict[str, Any] = {}
        if c.case_name:
            detail["case_name"] = c.case_name.value
        if c.class_period_start and c.class_period_end:
            detail["class_period"] = f"{c.class_period_start.value} to {c.class_period_end.value}"
        if c.lead_counsel and c.lead_counsel.value:
            detail["lead_counsel"] = c.lead_counsel.value
        if c.lead_counsel_tier and c.lead_counsel_tier.value:
            detail["lead_counsel_tier"] = c.lead_counsel_tier.value
        sca_details.append(detail)
    if sca_details:
        data["sca_details"] = sca_details

    # Settlement history
    if getattr(lit, "settlement_history", None):
        settlements = []
        for s in getattr(lit, "settlement_history", [])[:5]:
            sd: dict[str, Any] = {}
            if hasattr(s, "amount") and s.amount:
                sd["amount"] = (
                    float(s.amount.value) if hasattr(s.amount, "value") else float(s.amount)
                )
            if hasattr(s, "date") and s.date:
                sd["date"] = str(s.date.value) if hasattr(s.date, "value") else str(s.date)
            settlements.append(sd)
        if settlements:
            data["settlement_history"] = settlements

    data["derivative_count"] = len(lit.derivative_suits)

    # SEC enforcement
    sec = lit.sec_enforcement
    data["sec_stage"] = sec.highest_confirmed_stage.value if sec.highest_confirmed_stage else None

    data["open_sol_count"] = len([w for w in lit.sol_map if w.window_open])

    # Litigation reserve
    if lit.total_litigation_reserve and lit.total_litigation_reserve.value:
        data["litigation_reserve"] = float(lit.total_litigation_reserve.value)

    # Defense assessment
    if lit.defense and lit.defense.overall_defense_strength:
        data["defense_strength"] = str(
            lit.defense.overall_defense_strength.value,
        )

    # Industry patterns
    if lit.industry_patterns:
        data["industry_patterns"] = [
            str(
                p.legal_theory.value
                if p.legal_theory
                else p.description.value
                if p.description
                else ""
            )
            for p in lit.industry_patterns[:3]
        ]

    # Sector SCA filing rate from benchmark
    if state.benchmark and state.benchmark.inherent_risk:
        ir = state.benchmark.inherent_risk
        data["sector_filing_rate_pct"] = ir.sector_base_rate_pct
        data["company_adjusted_rate_pct"] = ir.company_adjusted_rate_pct

    # Scoring factors F1 (Litigation History), F5 (Regulatory), F9 (Industry)
    for fid in ("F1", "F5", "F9"):
        data.update(_factor_data(state, fid))

    return data
