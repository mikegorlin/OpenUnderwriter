"""H7: Emerging / Modern Hazards dimension scorers (6 dimensions).

Scores structural hazard conditions related to AI governance, cybersecurity,
ESG/climate exposure, crypto involvement, social media persona, and
workforce/labor model.

Many H7 dimensions rely on proxy signals (risk factor keyword searches)
as dedicated extraction pipelines may not exist for all emerging risks.

Each scorer returns (raw_score, data_sources, evidence_notes).
"""

from __future__ import annotations

from typing import Any

# Sectors with elevated ESG/climate sensitivity
_ESG_SENSITIVE: dict[str, float] = {
    "ENGY": 2.5,   # Fossil fuels, emissions
    "UTIL": 2.0,   # Power generation, coal
    "MATL": 1.5,   # Mining, chemicals
    "INDU": 1.0,   # Manufacturing emissions
    "TRAN": 1.5,   # Transportation emissions
}


def score_h7_dimension(
    dim_id: str,
    dim_config: dict[str, Any],
    data: dict[str, Any],
) -> tuple[float, list[str], list[str]]:
    """Dispatch to the appropriate H7 scorer."""
    scorers: dict[str, Any] = {
        "H7-01": _score_h7_01_ai,
        "H7-02": _score_h7_02_cyber,
        "H7-03": _score_h7_03_esg,
        "H7-04": _score_h7_04_crypto,
        "H7-05": _score_h7_05_social_media,
        "H7-06": _score_h7_06_workforce,
    }
    scorer = scorers.get(dim_id)
    if scorer is None:
        return (0.0, [], [])
    return scorer(dim_config, data)


def _score_h7_01_ai(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H7-01 AI Adoption/Governance. Scale 0-3."""
    max_s = float(cfg.get("max_score", 3))
    ai_score = data.get("ai_score")
    disclosure = data.get("disclosure_data", {})
    kw = data.get("keyword_hits", [])
    evidence: list[str] = []
    score = 0.0

    if ai_score is not None:
        # AI risk score 0-100; higher = more AI-exposed
        ais = float(ai_score)
        if ais > 70:
            score = 2.5
            evidence.append(f"AI risk score {ais:.0f}/100 (HIGH exposure)")
        elif ais > 40:
            score = 1.5
            evidence.append(f"AI risk score {ais:.0f}/100 (MODERATE)")
        else:
            score = 0.5
            evidence.append(f"AI risk score {ais:.0f}/100 (LOW)")

        mentions = disclosure.get("mention_count", 0)
        if mentions > 20:
            evidence.append(f"{mentions} AI mentions in filings (significant focus)")
        sentiment = disclosure.get("sentiment", "UNKNOWN")
        if sentiment == "THREAT":
            score += 0.5
            evidence.append("AI framed primarily as THREAT in disclosures")
    elif kw:
        score = min(len(kw), 3) * 0.7
        evidence.append(f"Proxy: {len(kw)} AI keyword hits in risk factors")
    else:
        evidence.append("No AI risk assessment data available")

    return (min(score, max_s), ["AI risk assessment", "10-K risk factors"], evidence)


def _score_h7_02_cyber(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H7-02 Cybersecurity Governance. Scale 0-3."""
    max_s = float(cfg.get("max_score", 3))
    kw = data.get("keyword_hits", [])
    if len(kw) >= 4:
        return (
            2.5,
            ["Risk factor analysis"],
            [f"Significant cybersecurity disclosure ({len(kw)} risk factor mentions -- high exposure)"],
        )
    if len(kw) >= 2:
        return (
            1.5,
            ["Risk factor analysis"],
            [f"Moderate cybersecurity disclosure ({len(kw)} mentions)"],
        )
    if kw:
        return (
            0.5,
            ["Risk factor analysis"],
            [f"Minimal cybersecurity disclosure ({len(kw)} mention)"],
        )
    return (0.5, [], ["No cybersecurity risk factor mentions -- may indicate under-disclosure"])


def _score_h7_03_esg(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H7-03 ESG/Climate Exposure. Scale 0-3."""
    max_s = float(cfg.get("max_score", 3))
    kw = data.get("keyword_hits", [])
    sector = data.get("sector", "")
    evidence: list[str] = []
    score = 0.0

    # Sector sensitivity baseline
    sector_score = _ESG_SENSITIVE.get(sector or "", 0.0)
    if sector_score > 0:
        score += sector_score
        evidence.append(f"Sector '{sector}' has inherent ESG/climate sensitivity ({sector_score})")

    # Risk factor mentions
    if kw:
        score += min(len(kw), 3) * 0.3
        evidence.append(f"{len(kw)} ESG/climate keyword hits in risk factors")

    if not evidence:
        evidence.append("No ESG/climate exposure indicators found")

    return (min(score, max_s), ["10-K risk factors", "Industry analysis"], evidence)


def _score_h7_04_crypto(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H7-04 Crypto/Digital Asset Exposure. Scale 0-2."""
    max_s = float(cfg.get("max_score", 2))
    kw = data.get("keyword_hits", [])
    if len(kw) >= 3:
        return (2.0, ["Risk factor analysis"], [f"Significant crypto/digital asset exposure ({len(kw)} mentions)"])
    if kw:
        return (1.0, ["Risk factor analysis"], [f"Some crypto/digital asset exposure ({len(kw)} mention(s))"])
    return (0.0, [], ["No crypto/digital asset exposure detected"])


def _score_h7_05_social_media(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H7-05 Social Media/Public Persona. Scale 0-2. (LOW availability)."""
    max_s = float(cfg.get("max_score", 2))
    sentiment = data.get("social_media_sentiment")
    if sentiment == "NEGATIVE":
        return (
            1.5,
            ["Sentiment profile"],
            ["Social media sentiment: NEGATIVE -- elevated public persona risk"],
        )
    if sentiment == "POSITIVE":
        return (0.0, ["Sentiment profile"], ["Social media sentiment: POSITIVE"])
    if sentiment:
        return (0.5, ["Sentiment profile"], [f"Social media sentiment: {sentiment}"])
    return (0.0, [], [])


def _score_h7_06_workforce(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H7-06 Workforce/Labor Model Risk. Scale 0-2."""
    max_s = float(cfg.get("max_score", 2))
    kw = data.get("keyword_hits", [])
    emp = data.get("employee_count")
    evidence: list[str] = []
    score = 0.0

    if kw:
        score = min(len(kw), 3) * 0.5
        evidence.append(f"Workforce/labor keyword hits: {', '.join(kw[:2])}")

    if emp is not None and int(emp) > 50000:
        score += 0.5
        evidence.append(f"Large workforce ({int(emp):,} employees) -- labor risk surface")

    if not evidence:
        evidence.append("No workforce/labor model risk indicators found")

    return (min(score, max_s), ["10-K risk factors", "Employee data"], evidence)
