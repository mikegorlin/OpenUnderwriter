"""H2: People & Management dimension scorers (8 dimensions).

Scores structural hazard conditions related to management experience,
expertise, board quality, founder dynamics, key person dependency,
turnover, and tone at the top.

Each scorer returns (raw_score, data_sources, evidence_notes).
"""

from __future__ import annotations

from typing import Any


def score_h2_dimension(
    dim_id: str,
    dim_config: dict[str, Any],
    data: dict[str, Any],
) -> tuple[float, list[str], list[str]]:
    """Dispatch to the appropriate H2 scorer."""
    scorers: dict[str, Any] = {
        "H2-01": _score_h2_01_experience,
        "H2-02": _score_h2_02_expertise,
        "H2-03": _score_h2_03_scale_mismatch,
        "H2-04": _score_h2_04_board_quality,
        "H2-05": _score_h2_05_founder_led,
        "H2-06": _score_h2_06_key_person,
        "H2-07": _score_h2_07_turnover,
        "H2-08": _score_h2_08_tone,
    }
    scorer = scorers.get(dim_id)
    if scorer is None:
        return (0.0, [], [])
    return scorer(dim_config, data)


def _score_h2_01_experience(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H2-01 Management Team Public Company Experience. Scale 0-5."""
    max_s = float(cfg.get("max_score", 5))
    execs = data.get("executives", [])
    evidence: list[str] = []
    score = 0.0

    ceo_found = False
    cfo_found = False
    for ex in execs:
        title = (ex.get("title") or "").lower()
        tenure = ex.get("tenure_years")
        bio = ex.get("bio") or ""

        if "ceo" in title or "chief executive" in title:
            ceo_found = True
            if tenure is not None and tenure < 2:
                score += 2.0
                evidence.append(f"CEO tenure {tenure:.1f}y (short -- elevated risk)")
            elif tenure is not None and tenure >= 10:
                evidence.append(f"CEO tenure {tenure:.1f}y (experienced)")
            elif tenure is not None:
                score += 1.0
                evidence.append(f"CEO tenure {tenure:.1f}y")
            if "first" in bio.lower() and "public" in bio.lower():
                score += 1.5
                evidence.append("CEO is first-time public company executive")

        elif "cfo" in title or "chief financial" in title:
            cfo_found = True
            if tenure is not None and tenure < 2:
                score += 1.5
                evidence.append(f"CFO tenure {tenure:.1f}y (short)")
            elif tenure is not None and tenure >= 5:
                evidence.append(f"CFO tenure {tenure:.1f}y (experienced)")
            elif tenure is not None:
                score += 0.5
                evidence.append(f"CFO tenure {tenure:.1f}y")

    # Don't penalize for missing profiles — that's an extraction gap, not risk

    return (min(score, max_s), ["DEF 14A executive biographies"], evidence)


def _score_h2_02_expertise(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H2-02 Industry Expertise Match. Scale 0-3."""
    max_s = float(cfg.get("max_score", 3))
    sector = data.get("sector", "")
    bios = data.get("exec_bios", [])
    evidence: list[str] = []

    if bios and sector:
        # Simple keyword matching for industry expertise
        sector_lower = sector.lower()
        match_count = sum(
            1 for bio in bios if bio and sector_lower in bio.lower()
        )
        if match_count >= 2:
            evidence.append(f"Multiple executives with {sector} industry background")
            return (0.5, ["DEF 14A biographies"], evidence)
        if match_count == 0:
            evidence.append(f"No executives with explicit {sector} background in bios")
            return (2.0, ["DEF 14A biographies"], evidence)
        evidence.append(f"{match_count} executive(s) with {sector} background")
        return (1.0, ["DEF 14A biographies"], evidence)

    # Proxy: governance score
    gov_total = data.get("governance_total")
    if gov_total is not None:
        score = max_s * (1.0 - float(gov_total) / 100.0)
        evidence.append(f"Proxy: governance score {gov_total} (inverse expertise estimate)")
        return (min(score, max_s), ["Governance quality score"], evidence)

    return (0.0, [], [])


def _score_h2_03_scale_mismatch(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H2-03 Scale Experience Mismatch. Scale 0-3. (Mostly unavailable)."""
    max_s = float(cfg.get("max_score", 3))
    kw = data.get("keyword_hits", [])
    if kw:
        return (
            max_s * 0.5,
            ["Risk factor keyword search"],
            [f"Proxy: {len(kw)} scale/growth keyword hits in risk factors"],
        )
    return (0.0, [], [])


def _score_h2_04_board_quality(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H2-04 Board Quality. Scale 0-5."""
    max_s = float(cfg.get("max_score", 5))
    score = 0.0
    evidence: list[str] = []

    ind_ratio = data.get("independence_ratio")
    if ind_ratio is not None:
        if float(ind_ratio) < 0.67:
            score += 2.0
            evidence.append(f"Independence ratio {float(ind_ratio):.0%} (below 67% -- weak)")
        elif float(ind_ratio) < 0.75:
            score += 1.0
            evidence.append(f"Independence ratio {float(ind_ratio):.0%} (below 75%)")
        else:
            evidence.append(f"Independence ratio {float(ind_ratio):.0%} (adequate)")

    overboarded = data.get("overboarded_count", 0)
    if overboarded and int(overboarded) > 0:
        score += min(int(overboarded), 2) * 1.0
        evidence.append(f"{overboarded} overboarded director(s)")

    board_size = data.get("board_size")
    if board_size is not None:
        if int(board_size) < 5:
            score += 1.0
            evidence.append(f"Small board ({board_size} members)")
        elif int(board_size) > 13:
            score += 0.5
            evidence.append(f"Large board ({board_size} members)")

    avg_ten = data.get("avg_tenure")
    if avg_ten is not None:
        if float(avg_ten) > 12:
            score += 1.0
            evidence.append(f"Avg director tenure {float(avg_ten):.1f}y (entrenched)")
        elif float(avg_ten) < 3:
            score += 0.5
            evidence.append(f"Avg director tenure {float(avg_ten):.1f}y (inexperienced)")

    return (min(score, max_s), ["DEF 14A", "Board forensic analysis"], evidence)


def _score_h2_05_founder_led(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H2-05 Founder-Led Risk. Scale 0-3."""
    max_s = float(cfg.get("max_score", 3))
    is_founder = data.get("is_founder_ceo")
    evidence: list[str] = []

    if is_founder is True:
        evidence.append("Founder CEO -- elevated control/entrenchment risk")
        return (2.0, ["DEF 14A biography"], evidence)
    if is_founder is False:
        evidence.append("Professional (non-founder) CEO")
        return (0.5, ["DEF 14A biography"], evidence)

    gov_total = data.get("governance_total")
    if gov_total is not None:
        evidence.append(f"Proxy: governance score {gov_total}")
        return (max_s * 0.3, ["Governance quality score"], evidence)

    return (0.0, [], [])


def _score_h2_06_key_person(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H2-06 Key Person Dependency. Scale 0-2. (LOW availability)."""
    max_s = float(cfg.get("max_score", 2))
    kw = data.get("keyword_hits", [])
    if kw:
        score = min(len(kw), 3) * 0.5
        return (
            min(score, max_s),
            ["Risk factor keyword search"],
            [f"Proxy: {len(kw)} key person dependency mentions in risk factors"],
        )
    return (0.0, [], [])


def _score_h2_07_turnover(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H2-07 Management Turnover. Scale 0-3."""
    max_s = float(cfg.get("max_score", 3))
    dep_count = data.get("departure_count", 0)
    red_flags = data.get("red_flags", [])
    stability = data.get("stability_score")
    evidence: list[str] = []
    score = 0.0

    if dep_count >= 3:
        score += 2.5
        evidence.append(f"{dep_count} executive departures in 18mo (HIGH turnover)")
    elif dep_count >= 1:
        score += 1.0
        evidence.append(f"{dep_count} executive departure(s) in 18mo")

    if red_flags:
        score += min(len(red_flags), 2) * 0.5
        evidence.append(f"Stability red flags: {', '.join(str(f) for f in red_flags[:2])}")

    if stability is not None:
        if float(stability) < 30:
            score += 1.0
            evidence.append(f"Stability score {stability}/100 (poor)")

    if not evidence:
        evidence.append("No recent management turnover detected")
    return (min(score, max_s), ["8-K filings", "Leadership stability analysis"], evidence)


def _score_h2_08_tone(
    cfg: dict[str, Any], data: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    """H2-08 Tone at the Top. Scale 0-3. Non-automatable -- generates meeting prep flag."""
    max_s = float(cfg.get("max_score", 3))
    tone = data.get("tone_trajectory")
    evasion = data.get("evasion_score")
    coherence = data.get("narrative_coherence")
    evidence: list[str] = []
    score = 0.0

    if tone == "DETERIORATING":
        score += 1.5
        evidence.append("Management tone trajectory: DETERIORATING")
    elif tone == "STABLE":
        score += 0.5
        evidence.append("Management tone trajectory: STABLE")

    if evasion is not None and float(evasion) > 0.5:
        score += 1.0
        evidence.append(f"Q&A evasion score {float(evasion):.2f} (elevated)")

    if coherence == "SIGNIFICANT_GAPS":
        score += 1.0
        evidence.append("Narrative coherence: SIGNIFICANT_GAPS between management claims and data")
    elif coherence == "MINOR_GAPS":
        score += 0.5
        evidence.append("Narrative coherence: MINOR_GAPS")

    # MEETING_PREP flag for underwriter attention
    evidence.append(
        "MEETING_PREP: Assess management candor, risk acknowledgment style, "
        "and alignment between public statements and operational reality."
    )

    has_real_data = any("tone" in e.lower() or "evasion" in e.lower() or "coherence" in e.lower()
                        for e in evidence if "MEETING_PREP" not in e)
    if not has_real_data:
        # No tone data available — don't penalize
        return (0.0, [], [])

    return (min(score, max_s), ["Earnings call analysis", "Sentiment profile"], evidence)
