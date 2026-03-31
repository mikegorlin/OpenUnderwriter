"""Company Intelligence Dossier data models.

Provides Pydantic v2 models for the Company Intelligence Dossier section
of the D&O underwriting worksheet:
- 5.1: Business description and core D&O exposure
- 5.2: Revenue flow diagram and narrative
- 5.3: Revenue model card (attribute/value/risk table)
- 5.4: Segment dossiers and concentration dimensions
- 5.5: Unit economics metrics
- 5.6: Revenue waterfall (YoY bridge)
- 5.7: Competitive landscape + moat assessment
- 5.8: Emerging risks
- 5.9: ASC 606 revenue recognition and billings vs revenue

These models are populated in EXTRACT and consumed by RENDER
for the company intelligence dossier section of the worksheet.

Phase 118: Revenue Model & Company Intelligence Dossier
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from do_uw.models.competitive_landscape import CompetitiveLandscape


class RevenueModelCardRow(BaseModel):
    """Single row in the Revenue Model Card table (subsection 5.3).

    Captures a key attribute of the revenue model with its D&O risk implication.
    """

    model_config = ConfigDict(frozen=False)

    attribute: str = Field(default="", description="Revenue model attribute (e.g., Model Type, Pricing)")
    value: str = Field(default="", description="Value or description for this attribute")
    do_risk: str = Field(default="", description="D&O risk implication of this attribute")
    risk_level: str = Field(default="LOW", description="Risk level: HIGH, MEDIUM, LOW")


class ConcentrationDimension(BaseModel):
    """Single concentration dimension analysis (subsection 5.4).

    Covers Customer, Geographic, Product, Channel, and Payer concentration.
    """

    model_config = ConfigDict(frozen=False)

    dimension: str = Field(default="", description="Concentration type: Customer, Geographic, Product, Channel, Payer")
    metric: str = Field(default="", description="Quantified concentration metric (e.g., Top 3 = 65%)")
    risk_level: str = Field(default="LOW", description="Risk level: HIGH, MEDIUM, LOW")
    do_implication: str = Field(default="", description="D&O litigation implication of this concentration")


class EmergingRisk(BaseModel):
    """Emerging risk that may affect future D&O exposure (subsection 5.8).

    Captures forward-looking threats with probability, impact, and D&O mapping.
    """

    model_config = ConfigDict(frozen=False)

    risk: str = Field(default="", description="Description of the emerging risk")
    probability: str = Field(default="", description="Probability: HIGH, MEDIUM, LOW")
    impact: str = Field(default="", description="Impact severity: HIGH, MEDIUM, LOW")
    timeframe: str = Field(default="", description="Expected timeframe (e.g., 12-24 months)")
    do_factor: str = Field(default="", description="How this risk maps to D&O exposure or SCA theory")
    status: str = Field(default="", description="Current status: ACTIVE, MONITORING, MITIGATED")


class ASC606Element(BaseModel):
    """ASC 606 revenue recognition element (subsection 5.9).

    Each element of the five-step ASC 606 model with complexity and D&O risk.
    """

    model_config = ConfigDict(frozen=False)

    element: str = Field(default="", description="ASC 606 element (e.g., Performance Obligations)")
    approach: str = Field(default="", description="Company's approach to this element")
    complexity: str = Field(default="LOW", description="Complexity level: HIGH, MEDIUM, LOW")
    do_risk: str = Field(default="", description="D&O risk from this revenue recognition element")


class UnitEconomicMetric(BaseModel):
    """Unit economics metric with benchmark comparison (subsection 5.5).

    Captures key unit economics (LTV:CAC, payback, margins) with industry benchmarks.
    """

    model_config = ConfigDict(frozen=False)

    metric: str = Field(default="", description="Metric name (e.g., LTV:CAC Ratio)")
    value: str = Field(default="", description="Company's value for this metric")
    benchmark: str = Field(default="", description="Industry benchmark for comparison")
    assessment: str = Field(default="", description="Assessment of company vs benchmark")
    do_risk: str = Field(default="", description="D&O risk implication of this metric")


class WaterfallRow(BaseModel):
    """Revenue waterfall bridge row (subsection 5.6).

    Single row in the YoY revenue waterfall showing component changes.
    """

    model_config = ConfigDict(frozen=False)

    label: str = Field(default="", description="Waterfall component label")
    value: str = Field(default="", description="Dollar or percentage value")
    delta: str = Field(default="", description="Change from prior period")
    narrative: str = Field(default="", description="Explanation of this component's change")


class RevenueSegmentDossier(BaseModel):
    """Per-segment revenue dossier (subsection 5.4).

    Detailed breakdown of a single revenue segment with D&O exposure mapping.
    """

    model_config = ConfigDict(frozen=False)

    segment_name: str = Field(default="", description="Name of the revenue segment")
    revenue_pct: str = Field(default="", description="Percentage of total revenue")
    growth_rate: str = Field(default="", description="Segment growth rate")
    rev_rec_method: str = Field(default="", description="Revenue recognition method for this segment")
    do_exposure: str = Field(default="", description="D&O exposure specific to this segment")
    risk_level: str = Field(default="LOW", description="Risk level: HIGH, MEDIUM, LOW")


class DossierData(BaseModel):
    """Top-level Company Intelligence Dossier data container.

    Aggregates all subsections of the dossier. Placed as a top-level field
    on AnalysisState because dossier data spans extraction through rendering.

    Subsections:
    - 5.1: Business description + core D&O exposure
    - 5.2: Revenue flow diagram + narrative
    - 5.3: Revenue model card
    - 5.4: Segment dossiers + concentration dimensions
    - 5.5: Unit economics
    - 5.6: Revenue waterfall
    - 5.7: Competitive landscape + moat assessment
    - 5.8: Emerging risks
    - 5.9: ASC 606 + billings vs revenue
    """

    model_config = ConfigDict(frozen=False)

    # 5.1: Business Description
    business_description_plain: str = Field(
        default="", description="Plain-language business description for underwriters"
    )
    core_do_exposure: str = Field(
        default="", description="Core D&O exposure narrative for this business model"
    )

    # 5.2: Revenue Flow
    revenue_flow_diagram: str = Field(
        default="", description="Mermaid or text-based revenue flow diagram"
    )
    revenue_flow_narrative: str = Field(
        default="", description="Narrative explaining how money flows through the business"
    )

    # 5.3: Revenue Model Card
    revenue_card: list[RevenueModelCardRow] = Field(
        default_factory=list, description="Revenue model attribute/value/risk rows"
    )

    # 5.4: Segment Dossiers & Concentration
    segment_dossiers: list[RevenueSegmentDossier] = Field(
        default_factory=list, description="Per-segment revenue dossier entries"
    )
    concentration_dimensions: list[ConcentrationDimension] = Field(
        default_factory=list, description="Concentration analysis across 5 dimensions"
    )

    # 5.5: Unit Economics
    unit_economics: list[UnitEconomicMetric] = Field(
        default_factory=list, description="Key unit economics metrics with benchmarks"
    )
    unit_economics_narrative: str = Field(
        default="", description="Narrative assessment of unit economics health"
    )

    # 5.6: Revenue Waterfall
    waterfall_rows: list[WaterfallRow] = Field(
        default_factory=list, description="YoY revenue waterfall bridge rows"
    )
    waterfall_narrative: str = Field(
        default="", description="Narrative explaining revenue bridge changes"
    )

    # 5.7: Competitive Landscape (Phase 119)
    competitive_landscape: CompetitiveLandscape = Field(
        default_factory=CompetitiveLandscape,
        description="Competitive landscape and moat assessment",
    )

    # 5.8: Emerging Risks
    emerging_risks: list[EmergingRisk] = Field(
        default_factory=list, description="Forward-looking emerging risks with D&O mapping"
    )

    # 5.9: ASC 606 & Billings vs Revenue
    asc_606_elements: list[ASC606Element] = Field(
        default_factory=list, description="ASC 606 five-step model elements with complexity"
    )
    billings_vs_revenue_narrative: str = Field(
        default="", description="Analysis of billings vs recognized revenue divergence"
    )

    # Metadata
    source_filings: list[str] = Field(
        default_factory=list, description="Filing accession numbers used for extraction"
    )
    extraction_confidence: str = Field(
        default="MEDIUM", description="Overall extraction confidence: HIGH, MEDIUM, LOW"
    )
