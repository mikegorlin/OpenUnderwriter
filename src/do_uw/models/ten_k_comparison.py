"""10-K year-over-year comparison models.

Tracks changes in risk factors, disclosures, controls, and legal
proceedings between consecutive annual filings. Produced by
stages/extract/ten_k_yoy.py, consumed by render context builders.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RiskFactorChange(BaseModel):
    """Tracks a risk factor's evolution across fiscal years."""

    title: str
    category: str  # LITIGATION, REGULATORY, FINANCIAL, OPERATIONAL, CYBER, ESG, AI, OTHER
    change_type: str  # NEW, REMOVED, ESCALATED, DE_ESCALATED, UNCHANGED, REORGANIZED, CONSOLIDATED_INTO
    current_severity: str  # HIGH, MEDIUM, LOW
    prior_severity: str | None = None  # None if NEW
    summary: str  # One-line description of what changed
    prior_title: str | None = None  # For REORGANIZED: what this was previously called
    new_title: str | None = None  # For CONSOLIDATED_INTO: what this was merged into


class DisclosureChange(BaseModel):
    """Tracks a specific disclosure change between years."""

    section: str  # risk_factors, mda, legal_proceedings, controls
    change_type: str  # NEW, REMOVED, MATERIAL_CHANGE
    description: str
    do_relevance: str  # HIGH, MEDIUM, LOW


class TenKYoYComparison(BaseModel):
    """Year-over-year 10-K comparison results."""

    current_year: str = Field(description="e.g. 'FY2025'")
    prior_year: str = Field(description="e.g. 'FY2024'")
    risk_factor_changes: list[RiskFactorChange] = Field(default_factory=list)
    new_risk_count: int = 0
    removed_risk_count: int = 0
    escalated_risk_count: int = 0
    reorganized_risk_count: int = 0
    disclosure_changes: list[DisclosureChange] = Field(default_factory=list)
    controls_changed: bool = False
    material_weakness_change: str | None = None  # APPEARED, REMEDIATED, None
    legal_proceedings_delta: int = 0  # net new proceedings
