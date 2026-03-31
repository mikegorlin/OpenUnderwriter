"""Miss risk computation and SCA relevance mapping.

Computes miss risk for forward-looking statements by comparing current
trajectory to guidance midpoint, adjusting by management credibility.
Maps high-risk misses to Securities Class Action (SCA) legal theories
using deterministic rules (not LLM-generated).

Miss risk algorithm (per CONTEXT.md):
- Gap > 10% = HIGH (2), 5-10% = MEDIUM (1), < 5% = LOW (0)
- Credibility adjustment: LOW (<50% beat) -> +1 level, HIGH (>80% beat) -> -1 level
- Cap at HIGH (2), floor at LOW (0)

SCA relevance mapping (deterministic):
- HIGH miss risk + material metric -> "10b-5: misleading forward guidance"
- HIGH miss risk + financial metric -> "10b-5: misleading forward guidance"
- MEDIUM miss risk + financial metric -> "Potential earnings fraud theory"
- MEDIUM miss risk + material non-financial -> "Potential operational misrepresentation"
- LOW or UNKNOWN -> "" (no SCA relevance)

Phase 117: Forward-Looking Risk Framework
"""

from __future__ import annotations

import logging

from do_uw.models.forward_looking import (
    CredibilityScore,
    ForwardStatement,
)

logger = logging.getLogger(__name__)

# Risk level names indexed by numeric level.
_RISK_LEVELS = ["LOW", "MEDIUM", "HIGH"]

# Material metrics -- revenue, EPS, net income, operating income.
_MATERIAL_METRICS = frozenset({
    "revenue", "eps", "earnings per share", "net income",
    "operating income", "total revenue", "net revenue",
    "earnings", "income from operations",
})

# Financial metrics -- anything involving dollar amounts or per-share values.
_FINANCIAL_METRICS = frozenset({
    "revenue", "eps", "earnings per share", "net income",
    "operating income", "total revenue", "net revenue",
    "gross profit", "ebitda", "ebit", "free cash flow",
    "operating cash flow", "profit margin", "gross margin",
    "operating margin", "net margin", "earnings",
    "income from operations", "revenue growth",
})


def compute_miss_risk(
    current_value: float | None,
    guidance_midpoint: float | None,
    credibility_level: str,
) -> str:
    """Compute miss risk from current value vs guidance midpoint.

    Per CONTEXT.md locked decision:
    - Gap > 10% = HIGH (2), 5-10% = MEDIUM (1), < 5% = LOW (0)
    - Credibility adjustment: LOW -> +1 (cap at 2), HIGH -> -1 (floor at 0)

    Args:
        current_value: Latest actual value (trailing metric).
        guidance_midpoint: Guided midpoint target.
        credibility_level: Management credibility (HIGH/MEDIUM/LOW/UNKNOWN).

    Returns:
        Risk level string: "HIGH", "MEDIUM", "LOW", or "UNKNOWN".
    """
    if current_value is None or guidance_midpoint is None:
        return "UNKNOWN"

    if abs(guidance_midpoint) < 0.001:
        return "UNKNOWN"

    # Compute gap as percentage of guidance.
    gap_pct = abs(current_value - guidance_midpoint) / abs(guidance_midpoint) * 100

    # Base risk from gap.
    # Per CONTEXT.md: >10% = HIGH, 5-10% = MEDIUM, <5% = LOW
    if gap_pct > 10:
        base_level = 2  # HIGH
    elif gap_pct >= 5:
        base_level = 1  # MEDIUM
    else:
        base_level = 0  # LOW

    # Credibility adjustment.
    adjustment = 0
    if credibility_level == "LOW":
        adjustment = 1
    elif credibility_level == "HIGH":
        adjustment = -1

    # Apply adjustment with bounds.
    adjusted = max(0, min(2, base_level + adjustment))

    return _RISK_LEVELS[adjusted]


def map_sca_relevance(
    miss_risk: str,
    is_material: bool = False,
    is_financial: bool = False,
) -> str:
    """Map miss risk to SCA legal theory using deterministic rules.

    Per CONTEXT.md locked decision -- deterministic mapping, NOT LLM-generated:
    - HIGH + material -> "10b-5: misleading forward guidance -- material metric
      miss creates scienter inference"
    - HIGH + financial -> "10b-5: misleading forward guidance -- financial metric
      miss supports fraud-on-the-market"
    - MEDIUM + financial -> "Potential earnings fraud theory -- moderate gap in
      financial metric guidance"
    - MEDIUM + material (non-financial) -> "Potential operational misrepresentation
      -- moderate gap may support Section 11 claim"
    - LOW or UNKNOWN -> "" (no SCA relevance)

    Args:
        miss_risk: Risk level (HIGH/MEDIUM/LOW/UNKNOWN).
        is_material: Whether the metric is material (revenue, EPS, net income, etc.).
        is_financial: Whether the metric involves dollar amounts or per-share values.

    Returns:
        SCA theory string, or empty string if no relevance.
    """
    if miss_risk in ("LOW", "UNKNOWN"):
        return ""

    if miss_risk == "HIGH":
        if is_material:
            return (
                "10b-5: misleading forward guidance -- "
                "material metric miss creates scienter inference"
            )
        if is_financial:
            return (
                "10b-5: misleading forward guidance -- "
                "financial metric miss supports fraud-on-the-market"
            )

    if miss_risk == "MEDIUM":
        if is_financial:
            return (
                "Potential earnings fraud theory -- "
                "moderate gap in financial metric guidance"
            )
        if is_material:
            return (
                "Potential operational misrepresentation -- "
                "moderate gap may support Section 11 claim"
            )

    return ""


def _classify_metric(metric_name: str) -> tuple[bool, bool]:
    """Classify a metric as material and/or financial.

    A metric is "material" if it's revenue, EPS, net income, or operating income.
    A metric is "financial" if it involves dollar amounts or per-share values.

    Returns:
        Tuple of (is_material, is_financial).
    """
    name_lower = metric_name.lower().strip()

    is_material = name_lower in _MATERIAL_METRICS
    is_financial = name_lower in _FINANCIAL_METRICS

    # Additional heuristic: if metric contains dollar-related terms, it's financial.
    if not is_financial:
        financial_markers = ("$", "per share", "margin", "profit", "income", "cash")
        for marker in financial_markers:
            if marker in name_lower:
                is_financial = True
                break

    # If metric contains revenue/eps/income terms, it's material.
    if not is_material:
        material_markers = ("revenue", "eps", "earnings", "income")
        for marker in material_markers:
            if marker in name_lower:
                is_material = True
                break

    return is_material, is_financial


def enrich_forward_statements(
    statements: list[ForwardStatement],
    credibility: CredibilityScore,
) -> list[ForwardStatement]:
    """Enrich forward statements with miss risk and SCA relevance.

    For each ForwardStatement with numeric data:
    1. Compute miss risk using credibility-adjusted gap analysis
    2. Classify metric as material/financial
    3. Map SCA relevance from miss risk + metric type
    4. Set rationale with gap percentage and credibility explanation

    Args:
        statements: List of ForwardStatements to enrich.
        credibility: CredibilityScore for adjustment.

    Returns:
        Enriched list of ForwardStatements (modified in-place and returned).
    """
    cred_level = credibility.credibility_level

    for stmt in statements:
        # Only compute miss risk for quantitative statements with numeric data.
        if stmt.guidance_midpoint is not None and stmt.current_value_numeric is not None:
            miss_risk = compute_miss_risk(
                current_value=stmt.current_value_numeric,
                guidance_midpoint=stmt.guidance_midpoint,
                credibility_level=cred_level,
            )
            stmt.miss_risk = miss_risk

            # Classify the metric.
            is_material, is_financial = _classify_metric(stmt.metric_name)

            # Map SCA relevance.
            stmt.sca_relevance = map_sca_relevance(
                miss_risk=miss_risk,
                is_material=is_material,
                is_financial=is_financial,
            )

            # Build rationale.
            if abs(stmt.guidance_midpoint) > 0.001:
                gap_pct = abs(stmt.current_value_numeric - stmt.guidance_midpoint) / abs(stmt.guidance_midpoint) * 100
                rationale_parts = [
                    f"{gap_pct:.1f}% gap between current ({stmt.current_value_numeric}) "
                    f"and guidance ({stmt.guidance_midpoint})",
                ]
                if cred_level in ("HIGH", "LOW"):
                    direction = "reduced" if cred_level == "HIGH" else "elevated"
                    rationale_parts.append(
                        f"Risk {direction} by {cred_level} management credibility "
                        f"({credibility.beat_rate_pct:.0f}% beat rate)"
                    )
                stmt.miss_risk_rationale = ". ".join(rationale_parts)
            else:
                stmt.miss_risk_rationale = "Unable to compute gap (guidance near zero)"
        else:
            stmt.miss_risk = "UNKNOWN"
            stmt.miss_risk_rationale = "No numeric guidance or current value available"

    return statements
