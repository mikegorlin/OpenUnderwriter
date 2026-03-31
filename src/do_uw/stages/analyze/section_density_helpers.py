"""Density helper functions split from section_assessments.py.

Contains jurisdiction risk classification and company-level density
computation. Extracted to keep section_assessments.py under the
project's 500-line limit (CLAUDE.md anti-pattern rule).

Phase 35-09: Split from section_assessments.py.
"""

from __future__ import annotations

from do_uw.models.density import DensityLevel, SectionDensity
from do_uw.models.state import AnalysisState

# High-risk jurisdictions for geographic exposure flagging.
# Moved from render/sections/sect2_company_details.py -- analytical
# classification belongs in ANALYZE, not RENDER.
_HIGH_RISK_JURISDICTIONS: set[str] = {
    "china", "russia", "iran", "north korea", "cuba", "syria",
    "venezuela", "myanmar", "belarus", "libya", "sudan",
}


def _classify_jurisdiction_risk(state: AnalysisState) -> list[str]:
    """Classify geographic jurisdictions as high-risk.

    Reads state.company.geographic_footprint and checks each geography
    against the _HIGH_RISK_JURISDICTIONS set (case-insensitive substring
    match).

    Returns a list of concern strings, e.g.:
        ["high_risk_jurisdiction:China", "high_risk_jurisdiction:Russia"]
    """
    concerns: list[str] = []
    if state.company is None:
        return concerns

    for sv_geo in state.company.geographic_footprint:
        geo = sv_geo.value
        # Extract jurisdiction name from various dict key patterns
        name = str(
            geo.get("jurisdiction", geo.get("region", geo.get("geography", "")))
        )
        if not name or name.lower() in ("unknown", "n/a", ""):
            continue

        name_lower = name.lower()
        for hr in _HIGH_RISK_JURISDICTIONS:
            if hr in name_lower:
                concerns.append(f"high_risk_jurisdiction:{name}")
                break

    return concerns


def compute_company_density(state: AnalysisState) -> SectionDensity:
    """Three-tier company section density assessment.

    Primarily driven by high-risk jurisdiction exposure. Additional
    company-level concerns can be added here in future.
    """
    concerns: list[str] = []
    critical_evidence: list[str] = []

    # Classify jurisdiction risk
    jurisdiction_concerns = _classify_jurisdiction_risk(state)
    if jurisdiction_concerns:
        concerns.extend(jurisdiction_concerns)

    # Determine level: any high-risk jurisdiction -> ELEVATED at minimum
    if critical_evidence:
        level = DensityLevel.CRITICAL
    elif concerns:
        level = DensityLevel.ELEVATED
    else:
        level = DensityLevel.CLEAN

    return SectionDensity(
        level=level,
        concerns=concerns,
        critical_evidence=critical_evidence,
    )
