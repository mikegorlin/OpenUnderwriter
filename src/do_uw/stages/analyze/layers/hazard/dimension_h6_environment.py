"""H6: External Environment dimension scorers (7 dimensions).

Scores environmental hazard conditions that are largely external to the
company: market cycle, regulatory spotlight, litigation waves, political
environment, interest rates, plaintiff attorney activity, geopolitical risk.

Many H6 dimensions are config-driven defaults, scored at moderate level
because they reflect market-wide conditions that affect all companies.

Each scorer returns (raw_score, data_sources, evidence_notes).
"""

from __future__ import annotations

from typing import Any

# Sectors currently under regulatory spotlight (updated periodically via config)
_REGULATORY_SPOTLIGHT: dict[str, float] = {
    "TECH": 2.5,   # AI regulation, antitrust, data privacy
    "CRYP": 3.0,   # SEC enforcement, classification uncertainty
    "BIOT": 2.0,   # FDA scrutiny, drug pricing
    "FINS": 2.0,   # Banking supervision, consumer protection
    "HLTH": 1.5,   # Billing practices, No Surprises Act
    "ENGY": 1.5,   # Climate regulation, methane rules
}

# Sectors currently in litigation wave
_LITIGATION_WAVE: dict[str, float] = {
    "TECH": 2.0,   # AI/data privacy class actions
    "CRYP": 3.0,   # Exchange collapses, fraud allegations
    "BIOT": 2.0,   # Clinical trial failures
    "FINS": 1.5,   # Rate manipulation, lending practices
}


def score_h6_dimension(
    dim_id: str,
    dim_config: dict[str, Any],
    data: dict[str, Any],
) -> tuple[float, list[str], list[str]]:
    """Dispatch to the appropriate H6 scorer."""
    scorers: dict[str, Any] = {
        "H6-01": _score_h6_01_market_cycle,
        "H6-02": _score_h6_02_regulatory_spotlight,
        "H6-03": _score_h6_03_litigation_wave,
        "H6-04": _score_h6_04_political,
        "H6-05": _score_h6_05_interest_rate,
        "H6-06": _score_h6_06_plaintiff_activity,
        "H6-07": _score_h6_07_geopolitical,
    }
    scorer = scorers.get(dim_id)
    if scorer is None:
        return (0.0, [], [])
    return scorer(dim_config, data)


def _score_h6_01_market_cycle(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H6-01 Market Cycle Position. Scale 0-3. Config default."""
    max_s = float(cfg.get("max_score", 3))
    # Default to moderate -- market cycle is system-wide
    default = cfg.get("default_value", 1.5)
    return (
        min(float(default), max_s),
        ["Config default"],
        ["Market cycle scored at config default (moderate -- apply system-wide)"],
    )


def _score_h6_02_regulatory_spotlight(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H6-02 Industry Regulatory Spotlight. Scale 0-3."""
    max_s = float(cfg.get("max_score", 3))
    sector = data.get("sector", "")
    score = _REGULATORY_SPOTLIGHT.get(sector or "", 1.0)
    return (
        min(score, max_s),
        ["Industry regulatory analysis"],
        [f"Sector '{sector}' regulatory spotlight level: {score}/{max_s}"],
    )


def _score_h6_03_litigation_wave(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H6-03 Industry Litigation Wave. Scale 0-3."""
    max_s = float(cfg.get("max_score", 3))
    sector = data.get("sector", "")
    score = _LITIGATION_WAVE.get(sector or "", 0.5)
    return (
        min(score, max_s),
        ["Industry litigation trend analysis"],
        [f"Sector '{sector}' litigation wave level: {score}/{max_s}"],
    )


def _score_h6_04_political(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H6-04 Political/Policy Environment. Scale 0-2. Config default."""
    max_s = float(cfg.get("max_score", 2))
    default = cfg.get("default_value", 1.0)
    return (
        min(float(default), max_s),
        ["Config default"],
        ["Political/policy environment at config default (moderate)"],
    )


def _score_h6_05_interest_rate(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H6-05 Interest Rate Environment. Scale 0-2. Config default."""
    max_s = float(cfg.get("max_score", 2))
    default = cfg.get("default_value", 1.0)
    return (
        min(float(default), max_s),
        ["Config default"],
        ["Interest rate environment at config default"],
    )


def _score_h6_06_plaintiff_activity(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H6-06 Plaintiff Attorney Activity. Scale 0-max_score. Config default.

    Uses 50% of max_score as baseline when no specific data is available,
    which maps to MODERATE (not CRITICAL).
    """
    max_s = float(cfg.get("max_score", 2))
    default = cfg.get("default_value", max_s * 0.5)
    return (
        min(float(default), max_s),
        ["Config default"],
        ["Plaintiff attorney activity at moderate baseline (no specific data)"],
    )


def _score_h6_07_geopolitical(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H6-07 Geopolitical Risk. Scale 0-3."""
    max_s = float(cfg.get("max_score", 3))
    regions = data.get("geographic_regions", 0)
    kw = data.get("keyword_hits", [])
    evidence: list[str] = []
    score = 0.0

    if regions >= 10:
        score += 2.0
        evidence.append(f"{regions} geographic regions (significant international exposure)")
    elif regions >= 4:
        score += 1.0
        evidence.append(f"{regions} geographic regions (moderate international exposure)")
    elif regions >= 2:
        score += 0.5
        evidence.append(f"{regions} geographic regions (limited international)")

    if kw:
        score += min(len(kw), 2) * 0.5
        evidence.append(f"Geopolitical keyword hits: {', '.join(kw[:2])}")

    if not evidence:
        score = 0.5
        evidence.append("Geopolitical exposure at baseline default")
    return (min(score, max_s), ["10-K geographic disclosure"], evidence)
