"""Pydantic models for forensic composite scoring in the ANALYZE stage.

Provides:
- ForensicZone: Integrity zone classification (HIGH_INTEGRITY through CRITICAL)
- SubScore: Component score within a forensic composite
- FinancialIntegrityScore: Overall financial integrity composite (FIS)
- RevenueQualityScore: Revenue quality composite (RQS)
- CashFlowQualityScore: Cash flow quality composite (CFQS)

Forensic composites combine multiple detection models (Beneish, Dechow,
Montier, Sloan, etc.) into unified 0-100 scores with zone classifications.
Always displayed as score gauges with alerts only on threshold breach.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class ForensicZone(StrEnum):
    """Zone classification for forensic composite scores.

    Maps a 0-100 score into risk categories. Thresholds defined
    in config/forensic_models.json.

    HIGH_INTEGRITY: 80-100 -- strong financial reporting quality
    ADEQUATE: 60-80 -- acceptable, no red flags
    CONCERNING: 40-60 -- warrants deeper review
    WEAK: 20-40 -- material concerns present
    CRITICAL: 0-20 -- severe financial integrity issues
    """

    HIGH_INTEGRITY = "HIGH_INTEGRITY"
    ADEQUATE = "ADEQUATE"
    CONCERNING = "CONCERNING"
    WEAK = "WEAK"
    CRITICAL = "CRITICAL"


class SubScore(BaseModel):
    """Component score within a forensic composite.

    Each sub-score represents one analytical dimension (e.g.,
    manipulation detection, accrual quality) with its own 0-100
    score, component breakdown, and evidence trail.
    """

    name: str = Field(description="Sub-score name (e.g., 'manipulation_detection')")
    score: float = Field(
        default=0.0,
        description="Component score (0-100, higher = better integrity)",
    )
    components: dict[str, float] = Field(
        default_factory=dict,
        description="Individual model outputs (e.g., {'beneish': 75, 'dechow': 80})",
    )
    evidence: str = Field(
        default="",
        description="Human-readable explanation of this sub-score",
    )


class FinancialIntegrityScore(BaseModel):
    """Financial Integrity Score (FIS) -- the primary forensic composite.

    Combines five analytical dimensions into a weighted 0-100 score:
    - Manipulation detection (30%): Beneish M-Score, Dechow F-Score, Montier C-Score
    - Accrual quality (20%): Enhanced Sloan ratio, accrual intensity, NI/CFO divergence
    - Revenue quality (20%): DSO trend, AR divergence, Q4 concentration, deferred revenue
    - Cash flow quality (15%): Quality of Earnings, Cash Conversion, CapEx Adequacy
    - Audit risk (15%): Material weakness, auditor changes, restatements, going concern

    Weights defined in config/forensic_models.json.
    """

    overall_score: float = Field(
        default=0.0,
        description="Weighted composite score (0-100, higher = more integrity)",
    )
    zone: ForensicZone = Field(
        default=ForensicZone.ADEQUATE,
        description="Zone classification based on overall_score",
    )
    manipulation_detection: SubScore = Field(
        default_factory=lambda: SubScore(name="manipulation_detection"),
        description="Manipulation detection sub-score (30% weight)",
    )
    accrual_quality: SubScore = Field(
        default_factory=lambda: SubScore(name="accrual_quality"),
        description="Accrual quality sub-score (20% weight)",
    )
    revenue_quality: SubScore = Field(
        default_factory=lambda: SubScore(name="revenue_quality"),
        description="Revenue quality sub-score (20% weight)",
    )
    cash_flow_quality: SubScore = Field(
        default_factory=lambda: SubScore(name="cash_flow_quality"),
        description="Cash flow quality sub-score (15% weight)",
    )
    audit_risk: SubScore = Field(
        default_factory=lambda: SubScore(name="audit_risk"),
        description="Audit risk sub-score (15% weight)",
    )
    sub_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Individual model raw outputs for reference",
    )


class RevenueQualityScore(BaseModel):
    """Revenue Quality Score (RQS) -- focused revenue integrity composite.

    Evaluates revenue recognition quality through four dimensions:
    - DSO trend (30%): Days Sales Outstanding trajectory
    - AR divergence (25%): Accounts Receivable vs. Revenue divergence
    - Q4 concentration (25%): Quarterly revenue distribution anomalies
    - Deferred revenue (20%): Deferred revenue pattern analysis

    Weights defined in config/forensic_models.json.
    """

    overall_score: float = Field(
        default=0.0,
        description="Weighted composite score (0-100)",
    )
    zone: ForensicZone = Field(
        default=ForensicZone.ADEQUATE,
        description="Zone classification based on overall_score",
    )
    dso_trend: SubScore = Field(
        default_factory=lambda: SubScore(name="dso_trend"),
        description="DSO trend sub-score (30% weight)",
    )
    ar_divergence: SubScore = Field(
        default_factory=lambda: SubScore(name="ar_divergence"),
        description="AR divergence sub-score (25% weight)",
    )
    q4_concentration: SubScore = Field(
        default_factory=lambda: SubScore(name="q4_concentration"),
        description="Q4 concentration sub-score (25% weight)",
    )
    deferred_revenue: SubScore = Field(
        default_factory=lambda: SubScore(name="deferred_revenue"),
        description="Deferred revenue sub-score (20% weight)",
    )


class CashFlowQualityScore(BaseModel):
    """Cash Flow Quality Score (CFQS) -- cash flow integrity composite.

    Evaluates cash flow quality through three dimensions:
    - Quality of Earnings (40%): CFO/NI ratio and consistency
    - Cash Conversion (35%): Free cash flow conversion efficiency
    - CapEx Adequacy (25%): Capital expenditure sustainability

    Weights derived from forensic_models.json financial_integrity_score
    cash_flow_quality component.
    """

    overall_score: float = Field(
        default=0.0,
        description="Weighted composite score (0-100)",
    )
    zone: ForensicZone = Field(
        default=ForensicZone.ADEQUATE,
        description="Zone classification based on overall_score",
    )
    quality_of_earnings: SubScore = Field(
        default_factory=lambda: SubScore(name="quality_of_earnings"),
        description="Quality of Earnings sub-score (40% weight)",
    )
    cash_conversion: SubScore = Field(
        default_factory=lambda: SubScore(name="cash_conversion"),
        description="Cash conversion sub-score (35% weight)",
    )
    capex_adequacy: SubScore = Field(
        default_factory=lambda: SubScore(name="capex_adequacy"),
        description="CapEx adequacy sub-score (25% weight)",
    )


__all__ = [
    "CashFlowQualityScore",
    "FinancialIntegrityScore",
    "ForensicZone",
    "RevenueQualityScore",
    "SubScore",
]
