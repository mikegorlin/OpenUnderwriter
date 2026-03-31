"""Dossier extraction schemas for LLM-powered extraction.

Pydantic models for extracting Company Intelligence Dossier fields from
10-K filings. Split into 4 focused schemas targeting specific filing
sections to avoid context window bloat:

1. RevenueModelExtraction - Items 1 + 7 (business description, revenue model)
2. ASC606Extraction - Note 2 / revenue recognition footnote
3. EmergingRiskExtraction - Item 1A risk factors + MD&A
4. UnitEconomicsExtraction - MD&A + Items 1/7 (unit economics, waterfall)

Phase 118: Revenue Model & Company Intelligence Dossier
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Sub-models for nested lists
# ---------------------------------------------------------------------------


class ASC606ElementExtraction(BaseModel):
    """Single ASC 606 element extracted from revenue recognition footnote."""

    element: str = Field(default="", description="ASC 606 element (e.g., Performance Obligations)")
    approach: str = Field(default="", description="Company's approach to this element")
    complexity: str = Field(default="LOW", description="Complexity level: HIGH, MEDIUM, LOW")
    key_judgment: str = Field(default="", description="Key judgment or estimate involved")


class EmergingRiskItem(BaseModel):
    """Single emerging risk extracted from Item 1A or MD&A."""

    risk: str = Field(default="", description="Description of the emerging risk")
    probability: str = Field(default="", description="Probability: HIGH, MEDIUM, LOW")
    impact: str = Field(default="", description="Impact severity: HIGH, MEDIUM, LOW")
    timeframe: str = Field(default="", description="Expected timeframe (e.g., 12-24 months)")
    scoring_factor_ref: str = Field(
        default="", description="Scoring factor reference (e.g., F.7, F.9)"
    )
    current_status: str = Field(default="", description="Status: ACTIVE, MONITORING, MITIGATED")


class UnitEconomicItem(BaseModel):
    """Single unit economics metric extracted from MD&A."""

    metric_name: str = Field(default="", description="Metric name (e.g., Net Dollar Retention, ASP)")
    value: str = Field(default="", description="Value as found in filing")
    source_section: str = Field(default="", description="Filing section where found")
    is_disclosed: bool = Field(default=False, description="Whether explicitly disclosed vs inferred")


class WaterfallItem(BaseModel):
    """Single waterfall decomposition component."""

    label: str = Field(default="", description="Component label (e.g., Organic Growth)")
    value: str = Field(default="", description="Dollar or percentage value")
    is_growth_driver: bool = Field(default=False, description="Whether this is a growth driver")


# ---------------------------------------------------------------------------
# Main extraction schemas (one per focused LLM prompt)
# ---------------------------------------------------------------------------


class RevenueModelExtraction(BaseModel):
    """LLM extraction schema for revenue model details.

    Targets 10-K Items 1 (Business) and 7 (MD&A). Extracts the core
    revenue model attributes, revenue flow structure, and segment
    enrichments that go beyond what TenKExtraction captures.
    """

    # Core revenue model attributes
    model_type: str = Field(
        default="",
        description="Business model type: B2B, B2C, B2B2C, marketplace, platform",
    )
    pricing_model: str = Field(
        default="",
        description="Pricing model: subscription, per-unit, PMPM, usage-based, hybrid",
    )
    revenue_quality_tier: str = Field(
        default="",
        description="Revenue quality: Tier 1 contractual recurring, Tier 2 habitual, Tier 3 one-time",
    )
    recognition_method: str = Field(
        default="",
        description="Revenue recognition: over time, point in time, hybrid",
    )
    contract_duration: str = Field(
        default="",
        description="Typical contract duration (e.g., 12-36 months, month-to-month)",
    )

    # SaaS / retention metrics
    net_dollar_retention: str = Field(
        default="",
        description="Net dollar retention rate if disclosed (e.g., '115%'), or 'Not disclosed'",
    )
    gross_retention: str = Field(
        default="",
        description="Gross retention rate if disclosed, or 'Not disclosed'",
    )
    arpu: str = Field(
        default="",
        description="Average revenue per user/account if applicable, or 'Not applicable'",
    )

    # Risk context
    concentration_risk_summary: str = Field(
        default="",
        description="Summary of customer/geographic/product concentration risks",
    )
    regulatory_overlay: str = Field(
        default="",
        description="Key regulatory requirements affecting revenue model",
    )

    # Revenue flow diagram structure
    revenue_flow_nodes: list[dict[str, str]] = Field(
        default_factory=list,
        description="Nodes for revenue flow diagram: [{label, type: source|process|output}]",
    )
    revenue_flow_edges: list[dict[str, str]] = Field(
        default_factory=list,
        description="Edges for revenue flow: [{from_node, to_node, label}]",
    )
    revenue_flow_narrative: str = Field(
        default="",
        description="Key insight about how money flows through the business",
    )

    # Segment enrichment (enriches existing state.company.revenue_segments)
    segment_enrichments: list[dict[str, str]] = Field(
        default_factory=list,
        description="Per-segment enrichments: [{segment_name, growth_rate, rev_rec_method, key_risk}]",
    )


class ASC606Extraction(BaseModel):
    """LLM extraction schema for ASC 606 revenue recognition details.

    Targets 10-K Note 2 / revenue recognition footnote. Extracts the
    five-step model elements with complexity assessment and key judgments.
    """

    elements: list[ASC606ElementExtraction] = Field(
        default_factory=list,
        description="ASC 606 elements with approach, complexity, and key judgments",
    )
    billings_vs_revenue_gap: str = Field(
        default="",
        description="Narrative about deferred revenue trends and billings vs revenue divergence",
    )
    rev_rec_complexity_overall: str = Field(
        default="LOW",
        description="Overall revenue recognition complexity: LOW, MEDIUM, HIGH",
    )


class EmergingRiskExtraction(BaseModel):
    """LLM extraction schema for emerging risks.

    Targets 10-K Item 1A (Risk Factors) and MD&A. Extracts forward-looking
    risks with probability, impact assessment, and D&O scoring factor mapping.
    """

    risks: list[EmergingRiskItem] = Field(
        default_factory=list,
        description="Emerging risks with probability, impact, timeframe, and scoring factor ref",
    )


class UnitEconomicsExtraction(BaseModel):
    """LLM extraction schema for unit economics and revenue waterfall.

    Targets 10-K MD&A + Items 1/7. Extracts metrics appropriate to
    the revenue model category (SaaS vs manufacturing vs services) and
    YoY revenue waterfall decomposition components.
    """

    revenue_model_category: str = Field(
        default="",
        description="Revenue model: RECURRING, PROJECT, TRANSACTION, HYBRID -- determines applicable metrics",
    )
    metrics: list[UnitEconomicItem] = Field(
        default_factory=list,
        description="Unit economics metrics appropriate to the revenue model category",
    )
    waterfall_components: list[WaterfallItem] = Field(
        default_factory=list,
        description="YoY revenue waterfall bridge components",
    )
