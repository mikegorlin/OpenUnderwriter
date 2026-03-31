"""H1: Business & Operating Model dimension scorers (13 dimensions).

Scores structural hazard conditions related to the company's business model,
industry, geographic footprint, growth trajectory, and operating complexity.

Each scorer returns (raw_score, data_sources, evidence_notes).
"""

from __future__ import annotations

from typing import Any

# Sector risk tiers: sector code -> risk score (0-10 scale for H1-01)
_SECTOR_RISK: dict[str, float] = {
    "BIOT": 9.0,   # Biotech/Pharma pre-revenue
    "PHRM": 7.0,   # Pharma established
    "TECH": 7.0,   # Technology
    "CRYP": 8.0,   # Crypto/Digital
    "FINS": 5.0,   # Financial services
    "HLTH": 5.0,   # Healthcare services
    "CONS": 3.5,   # Consumer goods
    "TELE": 3.5,   # Telecom
    "MDIA": 3.5,   # Media/Entertainment
    "INDU": 2.5,   # Industrial
    "ENGY": 2.5,   # Energy
    "MATL": 2.5,   # Materials
    "TRAN": 2.5,   # Transportation
    "UTIL": 1.5,   # Utilities
    "REIT": 1.5,   # REITs
}

# Regulatory intensity by sector
_REGULATORY_INTENSITY: dict[str, float] = {
    "FINS": 5.0,   # EXTREME
    "BIOT": 4.5,   # EXTREME
    "PHRM": 4.5,
    "HLTH": 4.0,   # HIGH
    "ENGY": 3.5,   # HIGH
    "TELE": 3.0,   # MODERATE
    "TECH": 2.5,   # MODERATE (data privacy)
    "CONS": 2.0,   # LOW
    "INDU": 2.0,
    "MATL": 1.5,
    "TRAN": 2.5,
    "UTIL": 3.5,   # HIGH (PUC regulation)
    "REIT": 2.0,
    "MDIA": 2.0,
    "CRYP": 4.0,
}


def score_h1_dimension(
    dim_id: str,
    dim_config: dict[str, Any],
    data: dict[str, Any],
) -> tuple[float, list[str], list[str]]:
    """Dispatch to the appropriate H1 scorer."""
    scorers: dict[str, Any] = {
        "H1-01": _score_h1_01_industry,
        "H1-02": _score_h1_02_complexity,
        "H1-03": _score_h1_03_regulatory,
        "H1-04": _score_h1_04_geographic,
        "H1-05": _score_h1_05_revenue_model,
        "H1-06": _score_h1_06_concentration,
        "H1-07": _score_h1_07_capital_intensity,
        "H1-08": _score_h1_08_ma_activity,
        "H1-09": _score_h1_09_growth,
        "H1-10": _score_h1_10_dual_class,
        "H1-11": _score_h1_11_non_gaap,
        "H1-12": _score_h1_12_platform,
        "H1-13": _score_h1_13_ip,
    }
    scorer = scorers.get(dim_id)
    if scorer is None:
        return (0.0, [], [])
    return scorer(dim_config, data)


def _score_h1_01_industry(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H1-01 Industry Sector Risk Tier. Scale 0-10."""
    max_s = float(cfg.get("max_score", 10))
    sector = data.get("sector", "")
    # Unknown sectors get moderate default (4.0) — not 0.0
    score = _SECTOR_RISK.get(sector or "", 4.0)
    evidence = [f"Sector '{sector}' maps to risk score {score}/{max_s}"]
    return (min(score, max_s), ["SEC EDGAR sector classification"], evidence)


def _score_h1_02_complexity(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H1-02 Business Model Complexity. Scale 0-5."""
    max_s = float(cfg.get("max_score", 5))
    score = 0.0
    evidence: list[str] = []
    seg_count = data.get("segment_count", 0)
    if seg_count >= 4:
        score += 2.0
        evidence.append(f"{seg_count} operating segments (HIGH complexity)")
    elif seg_count >= 2:
        score += 1.0
        evidence.append(f"{seg_count} operating segments (MODERATE)")
    op = data.get("operational_complexity", {})
    if isinstance(op, dict):
        if op.get("vie_present") or op.get("has_vie"):
            score += 1.5
            evidence.append("VIE/off-balance-sheet entities present")
        if op.get("dual_class") or op.get("has_dual_class"):
            score += 0.5
            evidence.append("Dual-class or special structure")
    kw = data.get("keyword_hits", [])
    if kw and not evidence:
        score = max_s * 0.4
        evidence.append(f"Proxy: {len(kw)} complexity keyword hits in risk factors")
    return (min(score, max_s), ["10-K segment reporting"], evidence)


def _score_h1_03_regulatory(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H1-03 Regulatory Intensity. Scale 0-5."""
    max_s = float(cfg.get("max_score", 5))
    sector = data.get("sector", "")
    score = _REGULATORY_INTENSITY.get(sector or "", 0.0)
    evidence = [f"Sector '{sector}' regulatory intensity: {score}/{max_s}"]
    return (min(score, max_s), ["SIC/NAICS regulatory mapping"], evidence)


def _score_h1_04_geographic(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H1-04 Geographic Complexity. Scale 0-5."""
    max_s = float(cfg.get("max_score", 5))
    score = 0.0
    evidence: list[str] = []
    regions = data.get("geographic_regions", 0)
    subs = data.get("subsidiary_count")
    if regions >= 10 or (subs and subs > 50):
        score += 3.0
        evidence.append(f"{regions} geographic regions, {subs or '?'} subsidiaries (HIGH)")
    elif regions >= 4 or (subs and subs > 10):
        score += 2.0
        evidence.append(f"{regions} regions, {subs or '?'} subsidiaries (MODERATE)")
    elif regions >= 2:
        score += 1.0
        evidence.append(f"{regions} regions (LOW)")
    kw = data.get("keyword_hits", [])
    if kw and not evidence:
        score = max_s * 0.4
        evidence.append(f"Proxy: {len(kw)} geographic keyword hits")
    return (min(score, max_s), ["10-K geographic disclosure", "Exhibit 21"], evidence)


def _score_h1_05_revenue_model(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H1-05 Revenue Model Manipulation Surface. Scale 0-5."""
    max_s = float(cfg.get("max_score", 5))
    score = 0.0
    evidence: list[str] = []
    eq = data.get("earnings_quality", {})
    if isinstance(eq, dict):
        rq = eq.get("revenue_quality")
        if rq is not None and isinstance(rq, (int, float)):
            if rq < 0.5:
                score = 4.0
                evidence.append(f"Revenue quality score {rq:.2f} (HIGH risk)")
            elif rq < 0.7:
                score = 2.5
                evidence.append(f"Revenue quality score {rq:.2f} (MODERATE)")
            else:
                score = 1.0
                evidence.append(f"Revenue quality score {rq:.2f} (LOW risk)")
    kw = data.get("keyword_hits", [])
    if kw and not evidence:
        score = max_s * 0.5
        evidence.append(f"Proxy: revenue recognition keywords found: {', '.join(kw[:3])}")
    return (min(score, max_s), ["10-K revenue recognition notes"], evidence)


def _score_h1_06_concentration(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H1-06 Customer/Supplier Concentration. Scale 0-3."""
    max_s = float(cfg.get("max_score", 3))
    score = 0.0
    evidence: list[str] = []
    custs = data.get("customer_concentration", [])
    for c in custs:
        if isinstance(c, dict):
            pct = c.get("revenue_pct") or c.get("pct")
            if pct and float(pct) > 25:
                score += 2.0
                evidence.append(f"Customer >25% revenue ({pct}%): HIGH concentration")
                break
            if pct and float(pct) > 10:
                score += 1.0
                evidence.append(f"Customer >10% revenue ({pct}%): MODERATE")
                break
    supps = data.get("supplier_concentration", [])
    if supps:
        score += 0.5
        evidence.append(f"{len(supps)} material supplier(s) disclosed")
    if not evidence:
        evidence.append("No significant concentration disclosed")
    return (min(score, max_s), ["10-K customer/supplier disclosures"], evidence)


def _score_h1_07_capital_intensity(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H1-07 Capital Intensity. Scale 0-3."""
    max_s = float(cfg.get("max_score", 3))
    score = 0.0
    evidence: list[str] = []
    capex = data.get("capex")
    rev = data.get("revenue")
    ppe = data.get("ppe")
    ta = data.get("total_assets")
    if capex and rev and rev > 0:
        ratio = capex / rev * 100
        if ratio > 15:
            score += 2.0
            evidence.append(f"CapEx/Revenue {ratio:.1f}% (HIGH)")
        elif ratio > 5:
            score += 1.0
            evidence.append(f"CapEx/Revenue {ratio:.1f}% (MODERATE)")
        else:
            evidence.append(f"CapEx/Revenue {ratio:.1f}% (LOW)")
    if ppe and ta and ta > 0:
        ppe_ratio = ppe / ta * 100
        if ppe_ratio > 50:
            score += 1.0
            evidence.append(f"PP&E/Assets {ppe_ratio:.1f}% (HIGH)")
        elif ppe_ratio > 20:
            score += 0.5
            evidence.append(f"PP&E/Assets {ppe_ratio:.1f}% (MODERATE)")
    return (min(score, max_s), ["10-K financials"], evidence)


def _score_h1_08_ma_activity(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H1-08 M&A Activity. Scale 0-5."""
    max_s = float(cfg.get("max_score", 5))
    score = 0.0
    evidence: list[str] = []
    changes = data.get("business_changes", [])
    acq_count = sum(1 for c in changes if c and "acqui" in str(c).lower())
    if acq_count >= 3:
        score += 2.0
        evidence.append(f"{acq_count} acquisitions noted (serial acquirer)")
    elif acq_count >= 1:
        score += 1.0
        evidence.append(f"{acq_count} acquisition(s) noted")
    gw = data.get("goodwill")
    ta = data.get("total_assets")
    if gw is not None and ta and ta > 0:
        gw_pct = gw / ta * 100
        if gw_pct > 30:
            score += 2.0
            evidence.append(f"Goodwill {gw_pct:.1f}% of assets (HIGH)")
        elif gw_pct > 10:
            score += 1.0
            evidence.append(f"Goodwill {gw_pct:.1f}% of assets (MODERATE)")
        else:
            evidence.append(f"Goodwill {gw_pct:.1f}% of assets (LOW)")
    kw = data.get("keyword_hits", [])
    if kw and not evidence:
        score = max_s * 0.4
        evidence.append(f"Proxy: {len(kw)} M&A keyword hits in risk factors")
    if not evidence:
        evidence.append("No significant M&A activity detected")
    return (min(score, max_s), ["10-K business combinations", "Balance sheet"], evidence)


def _score_h1_09_growth(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H1-09 Speed of Growth. Scale 0-5."""
    max_s = float(cfg.get("max_score", 5))
    yoy = data.get("yoy_growth")
    evidence: list[str] = []
    if yoy is not None:
        yoy_f = float(yoy)
        if yoy_f > 50:
            score = 5.0
            evidence.append(f"Revenue growth {yoy_f:.1f}% (VERY HIGH -- controls likely lagging)")
        elif yoy_f > 30:
            score = 4.0
            evidence.append(f"Revenue growth {yoy_f:.1f}% (HIGH)")
        elif yoy_f > 15:
            score = 2.5
            evidence.append(f"Revenue growth {yoy_f:.1f}% (MODERATE)")
        elif yoy_f > 5:
            score = 1.0
            evidence.append(f"Revenue growth {yoy_f:.1f}% (LOW)")
        elif yoy_f < -10:
            score = 2.0
            evidence.append(f"Revenue decline {yoy_f:.1f}% (restructuring/distress risk)")
        else:
            score = 0.5
            evidence.append(f"Revenue growth {yoy_f:.1f}% (STABLE)")
        return (min(score, max_s), ["10-K financials", "yfinance"], evidence)
    # Proxy: employee count only
    emp = data.get("employee_count")
    if emp:
        evidence.append(f"Proxy: {emp} employees (growth rate unavailable)")
        return (max_s * 0.4, ["10-K employee data"], evidence)
    return (0.0, [], [])


def _score_h1_10_dual_class(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H1-10 Dual-Class Share Structure. Scale 0-3."""
    max_s = float(cfg.get("max_score", 3))
    has_dc = data.get("has_dual_class")
    evidence: list[str] = []
    # Definitive boolean check takes priority — no proxy heuristics
    if has_dc is False:
        evidence.append("Single-class structure (one-share-one-vote)")
        return (0.0, ["Proxy statement"], evidence)
    if has_dc is True:
        ctrl = data.get("control_pct")
        econ = data.get("economic_pct")
        if ctrl and econ and econ > 0:
            spread = ctrl / econ
            if spread > 3:
                evidence.append(f"Dual-class: {ctrl}% control / {econ}% economic (VERY HIGH spread)")
                return (min(3.0, max_s), ["Proxy statement", "Ownership analysis"], evidence)
            evidence.append(f"Dual-class: {ctrl}% control / {econ}% economic")
            return (min(2.0, max_s), ["Proxy statement"], evidence)
        evidence.append("Dual-class structure present")
        return (min(2.0, max_s), ["Proxy statement"], evidence)
    # No definitive data — score at zero (no evidence of dual-class)
    return (0.0, [], [])


def _score_h1_11_non_gaap(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H1-11 Non-GAAP Reliance. Scale 0-3."""
    max_s = float(cfg.get("max_score", 3))
    evidence: list[str] = []
    eq = data.get("earnings_quality", {})
    if isinstance(eq, dict) and eq.get("accruals_ratio") is not None:
        ar = float(eq["accruals_ratio"])
        if abs(ar) > 0.1:
            evidence.append(f"Accruals ratio {ar:.3f} suggests non-GAAP divergence")
            return (min(2.0, max_s), ["10-K earnings quality"], evidence)
    kw = data.get("keyword_hits", [])
    if kw:
        score = min(len(kw), 3) * 0.8
        evidence.append(f"Proxy: {len(kw)} non-GAAP keyword hits in risk factors")
        return (min(score, max_s), ["Risk factor keyword search"], evidence)
    return (0.5, [], ["No non-GAAP reliance indicators found"])


def _score_h1_12_platform(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H1-12 Technology Platform Dependency. Scale 0-2.

    Sector-aware: non-tech companies (SIC not 7xxx) require explicit
    dependency language alongside keywords, or a higher hit threshold,
    to avoid false positives from generic business language.
    """
    max_s = float(cfg.get("max_score", 2))
    kw = data.get("keyword_hits", [])
    if not kw:
        return (0.0, [], ["No platform dependency indicators"])
    # Sector-aware threshold: tech sectors use lower bar
    sector = data.get("sector", "")
    is_tech = sector in ("TECH", "CRYP", "MDIA")
    # For non-tech sectors, require more hits or explicit risk language
    dependency_lang = any(
        phrase in kw_text.lower()
        for kw_text in kw
        for phrase in ("dependent on", "reliance on", "significant risk", "critical to")
    ) if kw else False
    threshold = 3 if is_tech else 5
    if len(kw) >= threshold or (not is_tech and dependency_lang and len(kw) >= 2):
        return (min(2.0, max_s), ["Risk factor analysis"], [f"Platform dependency: {len(kw)} mentions (sector: {sector})"])
    if is_tech and kw:
        return (min(1.0, max_s), ["Risk factor analysis"], [f"Platform dependency indicated: {kw[0]}"])
    if not is_tech and len(kw) < threshold:
        return (min(0.5, max_s), ["Risk factor analysis"], [f"Low platform keyword count ({len(kw)}) for non-tech sector"])
    return (min(1.0, max_s), ["Risk factor analysis"], [f"Platform dependency indicated: {kw[0]}"])


def _score_h1_13_ip(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H1-13 Intellectual Property Dependency. Scale 0-2."""
    max_s = float(cfg.get("max_score", 2))
    patent_count = data.get("patent_count", 0)
    kw = data.get("keyword_hits", [])
    score = 0.0
    evidence: list[str] = []
    if patent_count > 50:
        score += 1.0
        evidence.append(f"{patent_count} AI patents (significant IP portfolio)")
    if kw:
        score += min(len(kw), 2) * 0.5
        evidence.append(f"IP keyword hits: {', '.join(kw[:2])}")
    if not evidence:
        evidence.append("No significant IP dependency indicators")
    return (min(score, max_s), ["Patent data", "Risk factors"], evidence)
