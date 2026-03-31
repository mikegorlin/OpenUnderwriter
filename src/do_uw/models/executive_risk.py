"""Pydantic models for executive forensics risk scoring.

Provides:
- IndividualRiskScore: Person-level risk assessment for D&O officers/directors
- BoardAggregateRisk: Weighted aggregate of all individual risk scores

Executive forensics evaluates each named officer and director across
six risk dimensions, applies role-based weighting (CEO=3.0, CFO=2.5, etc.),
and produces a board-level aggregate score. Time decay reduces the weight
of older findings.

Role weights and dimension ranges defined in config/executive_scoring.json.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class IndividualRiskScore(BaseModel):
    """Risk assessment for a single officer or director.

    Scores across six dimensions that sum to a 0-100 total:
    - Prior litigation (0-25): Previous SCA or derivative involvement
    - Regulatory enforcement (0-25): SEC, DOJ, state AG actions
    - Prior company failures (0-15): Past bankruptcies or severe distress
    - Insider trading patterns (0-10): Suspicious trading timing/volume
    - Negative news (0-10): Adverse media coverage
    - Tenure stability (0-5): Role changes, short tenures, departures

    Role weight amplifies the score in board aggregation:
    CEO=3.0, CFO=2.5, COO=2.0, GC=2.0, CAO=2.0, CTO=1.5, Director=1.0.
    """

    person_name: str = Field(description="Full name of the officer/director")
    role: str = Field(description="Current role (e.g., 'CEO', 'CFO', 'Director')")
    role_weight: float = Field(
        default=1.0,
        description="Role-based weight for aggregation (CEO=3.0, CFO=2.5, etc.)",
    )
    total_score: float = Field(
        default=0.0,
        description="Sum of all dimension scores (0-100)",
    )
    prior_litigation: float = Field(
        default=0.0,
        description="Prior litigation involvement score (0-25)",
    )
    regulatory_enforcement: float = Field(
        default=0.0,
        description="Regulatory enforcement history score (0-25)",
    )
    prior_company_failures: float = Field(
        default=0.0,
        description="Prior company failures/bankruptcies score (0-15)",
    )
    insider_trading_patterns: float = Field(
        default=0.0,
        description="Suspicious insider trading patterns score (0-10)",
    )
    negative_news: float = Field(
        default=0.0,
        description="Adverse news/media coverage score (0-10)",
    )
    tenure_stability: float = Field(
        default=0.0,
        description="Tenure and role stability score (0-5)",
    )
    time_decay_applied: bool = Field(
        default=False,
        description="Whether time decay was applied to older findings",
    )
    findings: list[str] = Field(
        default_factory=list,
        description="Human-readable findings supporting the score",
    )
    sources: list[str] = Field(
        default_factory=list,
        description="Data sources used for this assessment",
    )


class BoardAggregateRisk(BaseModel):
    """Weighted aggregate risk score for the entire board/management team.

    Combines individual risk scores using role-based weights. The weighted
    score represents the overall people risk for the D&O placement.

    Thresholds for risk levels defined in config/executive_scoring.json:
    low (<20), moderate (20-35), elevated (35-50), high (50-70), critical (>85).
    """

    weighted_score: float = Field(
        default=0.0,
        description="Role-weighted aggregate score (0-100)",
    )
    individual_scores: list[IndividualRiskScore] = Field(
        default_factory=list,
        description="Individual risk scores for all assessed persons",
    )
    highest_risk_individual: str = Field(
        default="",
        description="Name of the person with the highest weighted risk score",
    )
    key_findings: list[str] = Field(
        default_factory=list,
        description="Top-level findings across all individuals",
    )


__all__ = [
    "BoardAggregateRisk",
    "IndividualRiskScore",
]
