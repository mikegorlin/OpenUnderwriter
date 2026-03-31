"""H3: Financial Structure dimension scorers (8 dimensions).

Scores structural hazard conditions related to leverage, off-balance-sheet
exposure, goodwill, earnings quality, cash flow, pre-revenue status,
related-party transactions, and capital markets activity.

Each scorer returns (raw_score, data_sources, evidence_notes).
"""

from __future__ import annotations

from typing import Any


def score_h3_dimension(
    dim_id: str,
    dim_config: dict[str, Any],
    data: dict[str, Any],
) -> tuple[float, list[str], list[str]]:
    """Dispatch to the appropriate H3 scorer."""
    scorers: dict[str, Any] = {
        "H3-01": _score_h3_01_leverage,
        "H3-02": _score_h3_02_obs,
        "H3-03": _score_h3_03_goodwill,
        "H3-04": _score_h3_04_earnings_quality,
        "H3-05": _score_h3_05_cf_divergence,
        "H3-06": _score_h3_06_pre_revenue,
        "H3-07": _score_h3_07_related_party,
        "H3-08": _score_h3_08_capital_markets,
    }
    scorer = scorers.get(dim_id)
    if scorer is None:
        return (0.0, [], [])
    return scorer(dim_config, data)


def _score_h3_01_leverage(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H3-01 Leverage. Scale 0-5."""
    max_s = float(cfg.get("max_score", 5))
    d2e = data.get("debt_to_equity")
    d2ebitda = data.get("debt_to_ebitda")
    evidence: list[str] = []
    score = 0.0

    if d2e is not None:
        d2e_f = float(d2e)
        if d2e_f > 3.0:
            score += 3.0
            evidence.append(f"Debt/Equity {d2e_f:.2f} (HIGH leverage)")
        elif d2e_f > 1.5:
            score += 2.0
            evidence.append(f"Debt/Equity {d2e_f:.2f} (MODERATE)")
        elif d2e_f > 0.5:
            score += 1.0
            evidence.append(f"Debt/Equity {d2e_f:.2f} (LOW-MODERATE)")
        elif d2e_f < 0:
            score += 3.5
            evidence.append(f"Debt/Equity {d2e_f:.2f} (negative equity -- VERY HIGH)")
        else:
            evidence.append(f"Debt/Equity {d2e_f:.2f} (LOW)")

    if d2ebitda is not None:
        d2eb = float(d2ebitda)
        if d2eb > 5.0:
            score += 2.0
            evidence.append(f"Net Debt/EBITDA {d2eb:.1f}x (HIGH)")
        elif d2eb > 3.0:
            score += 1.0
            evidence.append(f"Net Debt/EBITDA {d2eb:.1f}x (MODERATE)")

    return (min(score, max_s), ["10-K balance sheet", "SECT3 leverage ratios"], evidence)


def _score_h3_02_obs(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H3-02 Off-Balance Sheet Exposure. Scale 0-3."""
    max_s = float(cfg.get("max_score", 3))
    kw = data.get("keyword_hits", [])
    if len(kw) >= 3:
        return (
            2.5,
            ["Risk factor keyword search"],
            [f"Multiple OBS indicators: {', '.join(kw[:3])}"],
        )
    if kw:
        return (
            1.5,
            ["Risk factor keyword search"],
            [f"OBS indicator: {kw[0]}"],
        )
    return (0.0, [], ["No off-balance-sheet exposure indicators found"])


def _score_h3_03_goodwill(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H3-03 Goodwill-Heavy Balance Sheet. Scale 0-3."""
    max_s = float(cfg.get("max_score", 3))
    gw_pct = data.get("goodwill_pct")
    evidence: list[str] = []

    if gw_pct is not None:
        gw_f = float(gw_pct)
        if gw_f > 30:
            evidence.append(f"Goodwill {gw_f:.1f}% of assets (HIGH -- impairment risk)")
            return (3.0, ["10-K balance sheet"], evidence)
        if gw_f > 15:
            evidence.append(f"Goodwill {gw_f:.1f}% of assets (MODERATE)")
            return (1.5, ["10-K balance sheet"], evidence)
        if gw_f > 5:
            evidence.append(f"Goodwill {gw_f:.1f}% of assets (LOW)")
            return (0.5, ["10-K balance sheet"], evidence)
        evidence.append(f"Goodwill {gw_f:.1f}% of assets (MINIMAL)")
        return (0.0, ["10-K balance sheet"], evidence)

    return (0.0, [], ["No goodwill data available"])


def _score_h3_04_earnings_quality(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H3-04 Earnings Quality. Scale 0-5."""
    max_s = float(cfg.get("max_score", 5))
    score = 0.0
    evidence: list[str] = []

    m_score = data.get("m_score")
    m_zone = data.get("m_score_zone", "")
    if m_score is not None:
        ms = float(m_score)
        if ms > -1.78 or str(m_zone).lower() == "distress":
            score += 3.0
            evidence.append(f"Beneish M-Score {ms:.2f} -- above manipulation threshold")
        elif ms > -2.22 or str(m_zone).lower() == "grey":
            score += 1.5
            evidence.append(f"Beneish M-Score {ms:.2f} -- grey zone")
        else:
            evidence.append(f"Beneish M-Score {ms:.2f} -- safe zone")

    eq = data.get("earnings_quality", {})
    if isinstance(eq, dict):
        ocf_ni = eq.get("ocf_to_ni")
        if ocf_ni is not None:
            ratio = float(ocf_ni)
            if ratio < 0.5:
                score += 1.5
                evidence.append(f"OCF/NI ratio {ratio:.2f} (cash earnings divergence)")
            elif ratio < 0.8:
                score += 0.5
                evidence.append(f"OCF/NI ratio {ratio:.2f} (moderate)")
        ar = eq.get("accruals_ratio")
        if ar is not None:
            arr = float(ar)
            if abs(arr) > 0.1:
                score += 1.0
                evidence.append(f"Accruals ratio {arr:.3f} (elevated)")

    return (min(score, max_s), ["10-K financials", "Distress indicators"], evidence)


def _score_h3_05_cf_divergence(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H3-05 Cash Flow Divergence. Scale 0-3."""
    max_s = float(cfg.get("max_score", 3))
    ocf = data.get("operating_cash_flow")
    ni = data.get("net_income")
    evidence: list[str] = []

    if ocf is not None and ni is not None:
        ocf_f = float(ocf)
        ni_f = float(ni)
        if ni_f != 0:
            ratio = ocf_f / ni_f
            if ratio < 0.5:
                evidence.append(f"OCF/NI ratio {ratio:.2f} -- significant divergence")
                return (2.5, ["Cash flow statement"], evidence)
            if ratio < 0.8:
                evidence.append(f"OCF/NI ratio {ratio:.2f} -- moderate divergence")
                return (1.5, ["Cash flow statement"], evidence)
            evidence.append(f"OCF/NI ratio {ratio:.2f} -- aligned")
            return (0.5, ["Cash flow statement"], evidence)
        if ni_f == 0 and ocf_f < 0:
            evidence.append("Net income zero but negative OCF -- cash drain")
            return (2.0, ["Cash flow statement"], evidence)

    return (0.0, [], [])


def _score_h3_06_pre_revenue(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H3-06 Pre-Revenue / Cash Burn. Scale 0-5."""
    max_s = float(cfg.get("max_score", 5))
    rev = data.get("revenue")
    ocf = data.get("operating_cash_flow")
    cash = data.get("cash")
    evidence: list[str] = []

    if rev is not None and float(rev) <= 0:
        score = 4.0
        evidence.append("Pre-revenue company -- binary outcome risk")
        if ocf is not None and cash is not None and float(ocf) < 0:
            burn = abs(float(ocf))
            if cash and burn > 0:
                runway = float(cash) / burn
                if runway < 12:
                    score = 5.0
                    evidence.append(f"Cash runway ~{runway:.0f} months (CRITICAL)")
                elif runway < 24:
                    evidence.append(f"Cash runway ~{runway:.0f} months")
        return (min(score, max_s), ["10-K financials"], evidence)

    if ocf is not None and float(ocf) < 0:
        score = 2.0
        evidence.append(f"Negative operating cash flow: ${float(ocf)/1e6:.0f}M")
        if cash is not None and float(ocf) < 0:
            burn = abs(float(ocf))
            if cash and burn > 0:
                runway = float(cash) / burn
                evidence.append(f"Cash runway ~{runway:.0f} months")
                if runway < 18:
                    score = 3.0
        return (min(score, max_s), ["10-K financials"], evidence)

    if rev is not None and float(rev) > 0:
        evidence.append("Revenue-generating company with positive cash flow profile")
        return (0.0, ["10-K financials"], evidence)

    return (0.0, [], [])


def _score_h3_07_related_party(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H3-07 Related Party Transactions. Scale 0-2."""
    max_s = float(cfg.get("max_score", 2))
    rpt_count = data.get("related_party_count", 0)
    kw = data.get("keyword_hits", [])
    evidence: list[str] = []

    if rpt_count >= 3:
        evidence.append(f"{rpt_count} related-party transactions disclosed (HIGH)")
        return (2.0, ["DEF 14A", "10-K notes"], evidence)
    if rpt_count >= 1:
        evidence.append(f"{rpt_count} related-party transaction(s) disclosed")
        return (1.0, ["DEF 14A", "10-K notes"], evidence)
    if kw:
        evidence.append(f"Proxy: {len(kw)} related-party keyword hits")
        return (1.0, ["Risk factor keyword search"], evidence)
    return (0.0, [], ["No related-party transactions identified"])


def _score_h3_08_capital_markets(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H3-08 Capital Markets Activity. Scale 0-3."""
    max_s = float(cfg.get("max_score", 3))
    activities = data.get("activities", [])
    kw = data.get("keyword_hits", [])
    evidence: list[str] = []

    if activities:
        score = min(len(activities), 3) * 1.0
        evidence.append(f"{len(activities)} capital markets activities detected")
        if any("shelf" in str(a).lower() for a in activities):
            evidence.append("Active shelf registration")
        return (min(score, max_s), ["SEC filings", "Capital markets analysis"], evidence)
    if kw:
        evidence.append(f"Proxy: {len(kw)} capital markets keyword hits")
        return (min(len(kw) * 0.8, max_s), ["Risk factor keyword search"], evidence)
    return (0.0, [], ["No recent capital markets activity detected"])
