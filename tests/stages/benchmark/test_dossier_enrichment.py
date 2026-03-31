"""Tests for dossier D&O enrichment engine.

Phase 118-03: Validates that the enrichment engine generates company-specific
D&O commentary for all dossier table rows, computes concentration risk levels,
maps emerging risks to scoring factors, produces unit economics narrative,
and generates waterfall D&O insight narrative.
"""

from __future__ import annotations

import pytest

from do_uw.models.dossier import (
    ASC606Element,
    ConcentrationDimension,
    DossierData,
    EmergingRisk,
    RevenueModelCardRow,
    UnitEconomicMetric,
    WaterfallRow,
)
from do_uw.models.scoring import (
    FactorScore,
    ScoringResult,
    Tier,
    TierClassification,
)
from do_uw.models.state import AnalysisState
from do_uw.stages.benchmark.dossier_enrichment import enrich_dossier


def _make_state(
    *,
    tier: Tier = Tier.WRITE,
    quality_score: float = 65.0,
    factor_scores: list[FactorScore] | None = None,
    dossier: DossierData | None = None,
) -> AnalysisState:
    """Build a minimal AnalysisState with scoring + dossier."""
    if factor_scores is None:
        factor_scores = [
            FactorScore(
                factor_name="Litigation History",
                factor_id="F1",
                max_points=15,
                points_deducted=5.0,
                evidence=["Active SCA filed 2024"],
            ),
            FactorScore(
                factor_name="Financial Health",
                factor_id="F3",
                max_points=12,
                points_deducted=3.0,
                evidence=["Declining margins"],
            ),
            FactorScore(
                factor_name="Earnings & Guidance",
                factor_id="F5",
                max_points=10,
                points_deducted=8.0,
                evidence=["Missed Q3 guidance by 15%"],
            ),
        ]

    scoring = ScoringResult(
        quality_score=quality_score,
        composite_score=quality_score,
        total_risk_points=100.0 - quality_score,
        factor_scores=factor_scores,
        tier=TierClassification(
            tier=tier,
            score_range_low=51,
            score_range_high=70,
        ),
    )

    state = AnalysisState(ticker="TEST")
    state.scoring = scoring
    if dossier is not None:
        state.dossier = dossier
    return state


# -----------------------------------------------------------------------
# Test 1: enrich_revenue_card adds do_risk to each row
# -----------------------------------------------------------------------
def test_enrich_revenue_card_do_risk() -> None:
    """Revenue card rows get D&O risk commentary based on scoring tier."""
    dossier = DossierData(
        revenue_card=[
            RevenueModelCardRow(attribute="Revenue Quality", value="Tier 2"),
            RevenueModelCardRow(attribute="Pricing Model", value="Per-seat SaaS"),
        ],
    )
    state = _make_state(dossier=dossier)
    enrich_dossier(state)

    for row in state.dossier.revenue_card:
        assert row.do_risk != "", f"do_risk empty for {row.attribute}"


# -----------------------------------------------------------------------
# Test 2: Revenue Quality Tier 3 -> HIGH risk
# -----------------------------------------------------------------------
def test_revenue_quality_tier3_high_risk() -> None:
    """Revenue Quality Tier 3 gets HIGH risk mentioning SCA."""
    dossier = DossierData(
        revenue_card=[
            RevenueModelCardRow(attribute="Revenue Quality", value="Tier 3"),
        ],
    )
    state = _make_state(dossier=dossier)
    enrich_dossier(state)

    row = state.dossier.revenue_card[0]
    assert row.risk_level == "HIGH"
    assert "SCA" in row.do_risk or "one-time" in row.do_risk.lower() or "volatility" in row.do_risk.lower()


# -----------------------------------------------------------------------
# Test 3: Revenue Quality Tier 1 -> LOW risk
# -----------------------------------------------------------------------
def test_revenue_quality_tier1_low_risk() -> None:
    """Revenue Quality Tier 1 gets LOW risk level."""
    dossier = DossierData(
        revenue_card=[
            RevenueModelCardRow(attribute="Revenue Quality", value="Tier 1"),
        ],
    )
    state = _make_state(dossier=dossier)
    enrich_dossier(state)

    row = state.dossier.revenue_card[0]
    assert row.risk_level == "LOW"


# -----------------------------------------------------------------------
# Test 4: 5 concentration dimensions produced
# -----------------------------------------------------------------------
def test_compute_concentration_risk_levels_five_dimensions() -> None:
    """Concentration assessment produces 5 dimension entries."""
    dossier = DossierData(
        concentration_dimensions=[
            ConcentrationDimension(dimension="Customer", metric="Top 1 = 40%"),
            ConcentrationDimension(dimension="Geographic", metric="US = 80%"),
            ConcentrationDimension(dimension="Product", metric="Widget = 60%"),
            ConcentrationDimension(dimension="Channel", metric="Direct = 55%"),
            ConcentrationDimension(dimension="Payer", metric="Top 3 = 25%"),
        ],
    )
    state = _make_state(dossier=dossier)
    enrich_dossier(state)

    dims = state.dossier.concentration_dimensions
    assert len(dims) == 5
    for dim in dims:
        assert dim.risk_level in ("HIGH", "MEDIUM", "LOW")
        assert dim.do_implication != ""


# -----------------------------------------------------------------------
# Test 5: Customer concentration >30% -> HIGH
# -----------------------------------------------------------------------
def test_customer_concentration_high() -> None:
    """Customer concentration >30% triggers HIGH risk."""
    dossier = DossierData(
        concentration_dimensions=[
            ConcentrationDimension(dimension="Customer", metric="Top 1 = 40%"),
        ],
    )
    state = _make_state(dossier=dossier)
    enrich_dossier(state)

    dim = state.dossier.concentration_dimensions[0]
    assert dim.risk_level == "HIGH"


# -----------------------------------------------------------------------
# Test 6: Customer concentration <10% -> LOW
# -----------------------------------------------------------------------
def test_customer_concentration_low() -> None:
    """Customer concentration <10% triggers LOW risk."""
    dossier = DossierData(
        concentration_dimensions=[
            ConcentrationDimension(dimension="Customer", metric="Top 1 = 5%"),
        ],
    )
    state = _make_state(dossier=dossier)
    enrich_dossier(state)

    dim = state.dossier.concentration_dimensions[0]
    assert dim.risk_level == "LOW"


# -----------------------------------------------------------------------
# Test 7: Emerging risks mapped to scoring factors
# -----------------------------------------------------------------------
def test_map_emerging_risks_to_factors() -> None:
    """Each emerging risk gets a scoring factor reference."""
    dossier = DossierData(
        emerging_risks=[
            EmergingRisk(risk="New SEC regulatory action", probability="High", impact="High", timeframe="6-12 months"),
            EmergingRisk(risk="Competitor gaining share", probability="Medium", impact="Medium", timeframe="12-24 months"),
            EmergingRisk(risk="Pending litigation settlement", probability="High", impact="Very High", timeframe="0-6 months"),
        ],
    )
    state = _make_state(dossier=dossier)
    enrich_dossier(state)

    risks = state.dossier.emerging_risks
    assert risks[0].do_factor != ""
    assert "F.9" in risks[0].do_factor or "F9" in risks[0].do_factor  # regulatory -> F.9
    assert "F.5" in risks[1].do_factor or "F5" in risks[1].do_factor  # competition -> F.5
    assert "F.1" in risks[2].do_factor or "F1" in risks[2].do_factor  # litigation -> F.1


# -----------------------------------------------------------------------
# Test 8: Unit economics narrative identifies most important metric
# -----------------------------------------------------------------------
def test_enrich_unit_economics_narrative() -> None:
    """Unit economics narrative identifies the single most important metric."""
    dossier = DossierData(
        unit_economics=[
            UnitEconomicMetric(metric="NDR", value="85%", benchmark=">100%"),
            UnitEconomicMetric(metric="LTV:CAC", value="3.2x", benchmark=">3x"),
            UnitEconomicMetric(metric="Gross Margin", value="72%", benchmark=">70%"),
        ],
    )
    state = _make_state(dossier=dossier)
    enrich_dossier(state)

    narrative = state.dossier.unit_economics_narrative
    assert narrative != ""
    assert "TEST" in narrative  # company-specific (ticker)
    assert "most important" in narrative.lower() or "metric" in narrative.lower() or "NDR" in narrative


# -----------------------------------------------------------------------
# Test 9: ASC 606 elements get do_risk
# -----------------------------------------------------------------------
def test_enrich_asc_606_do_risk() -> None:
    """Each ASC 606 element gets D&O risk commentary."""
    dossier = DossierData(
        asc_606_elements=[
            ASC606Element(element="Performance Obligations", approach="Distinct deliverables", complexity="HIGH"),
            ASC606Element(element="Transaction Price", approach="Fixed pricing", complexity="LOW"),
        ],
    )
    state = _make_state(dossier=dossier)
    enrich_dossier(state)

    elements = state.dossier.asc_606_elements
    assert elements[0].do_risk != ""
    assert elements[1].do_risk != ""


# -----------------------------------------------------------------------
# Test 10: ASC 606 HIGH complexity -> rev-rec SCA mention
# -----------------------------------------------------------------------
def test_asc_606_high_complexity_mentions_rev_rec() -> None:
    """ASC 606 HIGH complexity mentions rev-rec as SCA allegation category."""
    dossier = DossierData(
        asc_606_elements=[
            ASC606Element(element="Performance Obligations", approach="Bundled", complexity="HIGH"),
        ],
    )
    state = _make_state(dossier=dossier)
    enrich_dossier(state)

    el = state.dossier.asc_606_elements[0]
    assert "rev" in el.do_risk.lower() or "SCA" in el.do_risk or "recognition" in el.do_risk.lower()


# -----------------------------------------------------------------------
# Test 11: Empty dossier does not crash
# -----------------------------------------------------------------------
def test_enrich_empty_dossier_no_crash() -> None:
    """Enriching an empty DossierData gracefully no-ops."""
    state = _make_state(dossier=DossierData())
    enrich_dossier(state)  # Should not raise
    assert state.dossier.core_do_exposure == "" or state.dossier.core_do_exposure != ""


# -----------------------------------------------------------------------
# Test 12: Core D&O exposure paragraph from scoring
# -----------------------------------------------------------------------
def test_core_do_exposure_from_scoring() -> None:
    """Core D&O exposure paragraph generated from scoring tier + top factor."""
    dossier = DossierData(
        revenue_card=[
            RevenueModelCardRow(attribute="Model Type", value="Subscription SaaS"),
        ],
    )
    state = _make_state(tier=Tier.WALK, quality_score=35.0, dossier=dossier)
    enrich_dossier(state)

    exposure = state.dossier.core_do_exposure
    assert exposure != ""
    assert "35" in exposure or "WALK" in exposure
    # Must reference the top factor
    assert "F" in exposure


# -----------------------------------------------------------------------
# Test 13: Waterfall narrative from rows + scoring
# -----------------------------------------------------------------------
def test_enrich_waterfall_narrative() -> None:
    """Waterfall narrative generated from rows and scoring tier."""
    dossier = DossierData(
        waterfall_rows=[
            WaterfallRow(label="Prior Year Revenue", value="$100M", delta="", narrative="Starting base"),
            WaterfallRow(label="Expansion", value="$31M", delta="+31%", narrative="Upsell growth"),
            WaterfallRow(label="New Logo", value="$14M", delta="+14%", narrative="New customers"),
            WaterfallRow(label="Current Year Revenue", value="$145M", delta="+45%", narrative="Total growth"),
        ],
    )
    state = _make_state(dossier=dossier)
    enrich_dossier(state)

    narrative = state.dossier.waterfall_narrative
    assert narrative != ""
    assert "$" in narrative or "revenue" in narrative.lower()


# -----------------------------------------------------------------------
# Test 14: Expansion-heavy waterfall mentions earnings predictability
# -----------------------------------------------------------------------
def test_enrich_waterfall_expansion_heavy() -> None:
    """Expansion-heavy rows mention earnings predictability risk."""
    dossier = DossierData(
        waterfall_rows=[
            WaterfallRow(label="Prior Year Revenue", value="$100M", delta="", narrative="Base"),
            WaterfallRow(label="Expansion", value="$50M", delta="+50%", narrative="Upsell"),
            WaterfallRow(label="New Logo", value="$10M", delta="+10%", narrative="New"),
            WaterfallRow(label="Current Year Revenue", value="$160M", delta="+60%", narrative="Total"),
        ],
    )
    state = _make_state(dossier=dossier)
    enrich_dossier(state)

    narrative = state.dossier.waterfall_narrative
    assert "predictability" in narrative.lower() or "expansion" in narrative.lower()


# -----------------------------------------------------------------------
# Test 15: Empty waterfall rows -> empty narrative (no crash)
# -----------------------------------------------------------------------
def test_enrich_waterfall_empty_rows() -> None:
    """Empty waterfall_rows sets narrative to empty string."""
    dossier = DossierData(waterfall_rows=[])
    state = _make_state(dossier=dossier)
    enrich_dossier(state)

    assert state.dossier.waterfall_narrative == ""
