"""H4: Governance Structure dimension scorers (8 dimensions).

Scores structural hazard conditions related to board structure, anti-takeover
provisions, audit quality, shareholder rights, compensation structure,
compliance infrastructure, and state of incorporation.

Each scorer returns (raw_score, data_sources, evidence_notes).
"""

from __future__ import annotations

from typing import Any

# States with weaker director protections
_WEAK_PROTECTION_STATES = {"NV", "Nevada", "WY", "Wyoming"}
_STANDARD_STATES = {"DE", "Delaware"}


def score_h4_dimension(
    dim_id: str,
    dim_config: dict[str, Any],
    data: dict[str, Any],
) -> tuple[float, list[str], list[str]]:
    """Dispatch to the appropriate H4 scorer."""
    scorers: dict[str, Any] = {
        "H4-01": _score_h4_01_ceo_chair,
        "H4-02": _score_h4_02_independence,
        "H4-03": _score_h4_03_anti_takeover,
        "H4-04": _score_h4_04_audit_committee,
        "H4-05": _score_h4_05_shareholder_rights,
        "H4-06": _score_h4_06_compensation,
        "H4-07": _score_h4_07_compliance,
        "H4-08": _score_h4_08_state,
    }
    scorer = scorers.get(dim_id)
    if scorer is None:
        return (0.0, [], [])
    return scorer(dim_config, data)


def _score_h4_01_ceo_chair(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H4-01 CEO/Chair Combined. Scale 0-2."""
    max_s = float(cfg.get("max_score", 2))
    combined = data.get("ceo_chair_combined")
    if combined is True:
        return (2.0, ["DEF 14A"], ["CEO and Chair roles combined -- concentrated authority"])
    if combined is False:
        return (0.0, ["DEF 14A"], ["CEO and Chair roles separated"])
    # Proxy from governance score
    ccs = data.get("ceo_chair_score")
    if ccs is not None:
        score = max_s * (1.0 - float(ccs) / 10.0) if float(ccs) <= 10 else max_s * 0.5
        return (min(score, max_s), ["Governance quality score"], [f"Proxy: CEO/Chair score {ccs}"])
    return (0.0, [], [])


def _score_h4_02_independence(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H4-02 Board Independence. Scale 0-3."""
    max_s = float(cfg.get("max_score", 3))
    ratio = data.get("independence_ratio")
    if ratio is not None:
        r = float(ratio)
        if r < 0.5:
            return (3.0, ["DEF 14A"], [f"Independence ratio {r:.0%} (critically low)"])
        if r < 0.67:
            return (2.0, ["DEF 14A"], [f"Independence ratio {r:.0%} (below recommended)"])
        if r < 0.75:
            return (1.0, ["DEF 14A"], [f"Independence ratio {r:.0%} (adequate)"])
        return (0.0, ["DEF 14A"], [f"Independence ratio {r:.0%} (strong)"])
    # Proxy
    is_score = data.get("independence_score")
    if is_score is not None:
        score = max_s * (1.0 - float(is_score) / 10.0) if float(is_score) <= 10 else 1.5
        return (min(score, max_s), ["Governance quality score"], [f"Proxy: independence score {is_score}"])
    return (0.0, [], [])


def _score_h4_03_anti_takeover(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H4-03 Anti-Takeover Provisions. Scale 0-3."""
    max_s = float(cfg.get("max_score", 3))
    classified = data.get("classified_board")
    evidence: list[str] = []
    score = 0.0
    if classified is True:
        score += 1.5
        evidence.append("Classified (staggered) board")
    elif classified is False:
        evidence.append("Annual board elections")
    gov_total = data.get("governance_total")
    if gov_total is not None and not evidence:
        score = max_s * (1.0 - float(gov_total) / 100.0)
        evidence.append(f"Proxy: governance score {gov_total}")
    return (min(score, max_s), ["DEF 14A", "Governance analysis"], evidence)


def _score_h4_04_audit_committee(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H4-04 Audit Committee Quality. Scale 0-3."""
    max_s = float(cfg.get("max_score", 3))
    cs = data.get("committee_score")
    gov_total = data.get("governance_total")
    evidence: list[str] = []
    if cs is not None:
        csf = float(cs)
        if csf < 3:
            evidence.append(f"Committee quality score {csf}/10 (weak)")
            return (2.0, ["Governance quality score"], evidence)
        if csf < 6:
            evidence.append(f"Committee quality score {csf}/10 (moderate)")
            return (1.0, ["Governance quality score"], evidence)
        evidence.append(f"Committee quality score {csf}/10 (strong)")
        return (0.0, ["Governance quality score"], evidence)
    if gov_total is not None:
        score = max_s * (1.0 - float(gov_total) / 100.0)
        evidence.append(f"Proxy: governance total {gov_total}")
        return (min(score, max_s), ["Governance quality score"], evidence)
    return (0.0, [], [])


def _score_h4_05_shareholder_rights(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H4-05 Shareholder Rights. Scale 0-2."""
    max_s = float(cfg.get("max_score", 2))
    gov_total = data.get("governance_total")
    if gov_total is not None:
        g = float(gov_total)
        if g < 30:
            return (2.0, ["Governance quality score"], [f"Governance score {g}/100 (weak shareholder protections)"])
        if g < 60:
            return (1.0, ["Governance quality score"], [f"Governance score {g}/100 (moderate)"])
        return (0.0, ["Governance quality score"], [f"Governance score {g}/100 (strong)"])
    return (0.0, [], [])


def _score_h4_06_compensation(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H4-06 Compensation Structure. Scale 0-3."""
    max_s = float(cfg.get("max_score", 3))
    score = 0.0
    evidence: list[str] = []
    comp_mix = data.get("comp_mix", {})
    clawback = data.get("has_clawback")
    pay_ratio = data.get("ceo_pay_ratio")
    sop = data.get("say_on_pay_pct")

    if isinstance(comp_mix, dict):
        var_pct = comp_mix.get("equity", 0) + comp_mix.get("bonus", 0)
        if var_pct > 80:
            score += 0.5
            evidence.append(f"Variable pay {var_pct:.0f}% (heavily incentive-based)")

    if clawback is False:
        score += 1.0
        evidence.append("No clawback policy")
    elif clawback is True:
        evidence.append("Clawback policy in place")

    if pay_ratio is not None and float(pay_ratio) > 300:
        score += 1.0
        evidence.append(f"CEO pay ratio {float(pay_ratio):.0f}:1 (elevated)")

    if sop is not None:
        sp = float(sop)
        if sp < 70:
            score += 1.0
            evidence.append(f"Say-on-pay support {sp:.0f}% (LOW -- shareholder dissatisfaction)")
        elif sp < 85:
            score += 0.5
            evidence.append(f"Say-on-pay support {sp:.0f}% (below comfort)")

    return (min(score, max_s), ["DEF 14A compensation tables"], evidence)


def _score_h4_07_compliance(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H4-07 Compliance Infrastructure (SOX 404). Scale 0-3."""
    max_s = float(cfg.get("max_score", 3))
    mw = data.get("material_weaknesses", [])
    gc = data.get("going_concern")
    evidence: list[str] = []
    score = 0.0

    if mw:
        score += min(len(mw), 2) * 1.5
        evidence.append(f"{len(mw)} material weakness(es) disclosed")
    if gc is True:
        score += 1.5
        evidence.append("Going concern qualification present")

    gov_total = data.get("governance_total")
    if gov_total is not None and not evidence:
        score = max_s * (1.0 - float(gov_total) / 100.0)
        evidence.append(f"Proxy: governance score {gov_total}")

    if not evidence:
        evidence.append("No material weaknesses or going concern issues identified")
    return (min(score, max_s), ["10-K audit report", "SOX 404 assessment"], evidence)


def _score_h4_08_state(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H4-08 State of Incorporation. Scale 0-2."""
    max_s = float(cfg.get("max_score", 2))
    state = data.get("state", "")
    if state in _WEAK_PROTECTION_STATES:
        return (2.0, ["SEC EDGAR"], [f"Incorporated in {state} (weak director protections)"])
    if state in _STANDARD_STATES:
        return (0.5, ["SEC EDGAR"], [f"Incorporated in {state} (standard D&O protections)"])
    if state:
        return (0.5, ["SEC EDGAR"], [f"Incorporated in {state}"])
    return (0.0, [], [])
