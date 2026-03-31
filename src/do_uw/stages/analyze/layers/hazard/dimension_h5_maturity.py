"""H5: Public Company Maturity dimension scorers (5 dimensions).

Scores structural hazard conditions related to IPO recency, method of
going public, exchange membership, FPI status, and track record.

Each scorer returns (raw_score, data_sources, evidence_notes).
"""

from __future__ import annotations

from typing import Any

# Major exchanges (lower risk)
_MAJOR_EXCHANGES = {"NYSE", "NASDAQ", "Nasdaq", "New York Stock Exchange"}
_OTC_EXCHANGES = {"OTC", "OTCQX", "OTCQB", "OTC Markets", "Pink Sheets"}


def score_h5_dimension(
    dim_id: str,
    dim_config: dict[str, Any],
    data: dict[str, Any],
) -> tuple[float, list[str], list[str]]:
    """Dispatch to the appropriate H5 scorer."""
    scorers: dict[str, Any] = {
        "H5-01": _score_h5_01_ipo_recency,
        "H5-02": _score_h5_02_method,
        "H5-03": _score_h5_03_exchange,
        "H5-04": _score_h5_04_fpi,
        "H5-05": _score_h5_05_seasoning,
    }
    scorer = scorers.get(dim_id)
    if scorer is None:
        return (0.0, [], [])
    return scorer(dim_config, data)


def _score_h5_01_ipo_recency(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H5-01 IPO Recency. Scale 0-5. 3-year cliff model."""
    max_s = float(cfg.get("max_score", 5))
    yp = data.get("years_public")
    if yp is not None:
        y = int(yp)
        if y <= 1:
            return (5.0, ["SEC EDGAR"], [f"IPO {y} year(s) ago (EXTREME risk -- peak exposure)"])
        if y <= 3:
            return (4.0, ["SEC EDGAR"], [f"IPO {y} years ago (HIGH risk -- within 3-year cliff)"])
        if y <= 5:
            return (2.5, ["SEC EDGAR"], [f"IPO {y} years ago (MODERATE -- transitioning)"])
        if y <= 10:
            return (1.0, ["SEC EDGAR"], [f"IPO {y} years ago (LOW -- seasoned)"])
        return (0.0, ["SEC EDGAR"], [f"IPO {y} years ago (MINIMAL -- mature public company)"])
    return (0.0, [], [])


def _score_h5_02_method(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H5-02 Method of Going Public. Scale 0-3. (Mostly proxy/unavailable)."""
    max_s = float(cfg.get("max_score", 3))
    method = data.get("method", "")
    kw = data.get("keyword_hits", [])
    if method == "SPAC" or kw:
        return (
            3.0,
            ["Risk factor analysis", "Business description"],
            ["SPAC/de-SPAC origin -- elevated litigation risk (Section 11 exposure)"],
        )
    return (0.0, [], ["Traditional IPO or method not determinable (scored as standard)"])


def _score_h5_03_exchange(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H5-03 Exchange/Index Membership. Scale 0-2."""
    max_s = float(cfg.get("max_score", 2))
    exchange = data.get("exchange", "")
    if exchange in _OTC_EXCHANGES:
        return (2.0, ["SEC EDGAR"], [f"Listed on {exchange} (OTC -- limited oversight)"])
    if exchange in _MAJOR_EXCHANGES:
        return (0.0, ["SEC EDGAR"], [f"Listed on {exchange} (major exchange -- standard oversight)"])
    if exchange:
        return (0.5, ["SEC EDGAR"], [f"Listed on {exchange}"])
    return (0.0, [], [])


def _score_h5_04_fpi(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H5-04 FPI/ADR Status. Scale 0-2."""
    max_s = float(cfg.get("max_score", 2))
    is_fpi = data.get("is_fpi")
    if is_fpi is True:
        return (
            1.5,
            ["SEC EDGAR"],
            ["Foreign private issuer -- different disclosure regime, limited 10b-5 exposure"],
        )
    return (0.0, ["SEC EDGAR"], ["Domestic issuer (standard SEC reporting)"])


def _score_h5_05_seasoning(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H5-05 Seasoning/Track Record. Scale 0-3."""
    max_s = float(cfg.get("max_score", 3))
    yp = data.get("years_public")
    lit_count = data.get("prior_litigation_count", 0)
    evidence: list[str] = []
    score = 0.0

    if yp is not None:
        y = int(yp)
        if y < 5:
            score += 1.5
            evidence.append(f"Only {y} years as public company (limited track record)")
        elif y < 10:
            score += 0.5
            evidence.append(f"{y} years as public company (developing track record)")
        else:
            evidence.append(f"{y} years as public company (established)")

    if lit_count > 0:
        score += min(lit_count, 3) * 0.5
        evidence.append(f"{lit_count} prior litigation case(s)")

    return (min(score, max_s), ["SEC EDGAR", "Litigation history"], evidence)
