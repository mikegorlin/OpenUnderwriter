"""AI impact model definitions for industry-specific risk assessment.

Defines per-industry AI exposure areas with threat levels and activity
descriptions. Used by the AI risk scoring engine to set prior threat
baselines before extraction evidence adjusts scores.

SIC ranges match playbook_data.py / playbook_data_extra.py for consistency.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Industry-specific AI impact models
# ---------------------------------------------------------------------------

AI_IMPACT_MODELS: list[dict[str, Any]] = [
    {
        "id": "TECH_SAAS",
        "industry": "Technology / SaaS",
        "sic_ranges": [(3571, 3579), (3661, 3679), (3812, 3812), (7371, 7379)],
        "exposure_areas": {
            "revenue_displacement": {
                "weight": 0.35,
                "threat_level": "HIGH",
                "activities": [
                    "AI-native competitors replacing traditional SaaS",
                    "Copilot/agent features commoditizing core product",
                    "Open-source AI models reducing willingness to pay",
                ],
            },
            "cost_structure": {
                "weight": 0.15,
                "threat_level": "MEDIUM",
                "activities": [
                    "AI-driven development reducing engineering costs",
                    "Automated QA and testing",
                    "AI customer support reducing headcount",
                ],
            },
            "competitive_moat": {
                "weight": 0.30,
                "threat_level": "HIGH",
                "activities": [
                    "Data moats eroded by foundation models",
                    "Network effects weakened by AI interoperability",
                    "Switching costs reduced by AI-powered migration",
                ],
            },
            "workforce_automation": {
                "weight": 0.15,
                "threat_level": "MEDIUM",
                "activities": [
                    "AI coding assistants replacing junior engineers",
                    "Automated customer success workflows",
                    "AI-driven sales and marketing automation",
                ],
            },
            "regulatory_ip": {
                "weight": 0.05,
                "threat_level": "LOW",
                "activities": [
                    "AI-generated code IP ownership uncertainty",
                    "Open-source AI licensing complexity",
                ],
            },
        },
    },
    {
        "id": "BIOTECH_PHARMA",
        "industry": "Biotech / Pharma",
        "sic_ranges": [(2830, 2836), (2860, 2869), (3841, 3851), (8731, 8734)],
        "exposure_areas": {
            "revenue_displacement": {
                "weight": 0.15,
                "threat_level": "LOW",
                "activities": [
                    "AI-designed drugs competing with traditional pipelines",
                    "AI-accelerated generic development",
                ],
            },
            "cost_structure": {
                "weight": 0.30,
                "threat_level": "HIGH",
                "activities": [
                    "AI drug discovery reducing R&D timelines by 40-60%",
                    "AI clinical trial optimization and patient matching",
                    "Automated lab processes and compound screening",
                ],
            },
            "competitive_moat": {
                "weight": 0.20,
                "threat_level": "MEDIUM",
                "activities": [
                    "AI-first biotechs bypassing traditional discovery",
                    "Computational biology replacing wet-lab advantages",
                ],
            },
            "workforce_automation": {
                "weight": 0.10,
                "threat_level": "LOW",
                "activities": [
                    "Automated regulatory filing preparation",
                    "AI-powered pharmacovigilance monitoring",
                ],
            },
            "regulatory_ip": {
                "weight": 0.25,
                "threat_level": "HIGH",
                "activities": [
                    "AI-invented compound patentability challenges",
                    "FDA AI/ML regulatory framework uncertainty",
                    "AI-generated clinical data validation requirements",
                ],
            },
        },
    },
    {
        "id": "FINANCIAL_SERVICES",
        "industry": "Financial Services / Banking",
        "sic_ranges": [
            (6000, 6199),
            (6200, 6299),
            (6300, 6399),
            (6400, 6499),
            (6500, 6599),
        ],
        "exposure_areas": {
            "revenue_displacement": {
                "weight": 0.20,
                "threat_level": "MEDIUM",
                "activities": [
                    "AI-native fintech disrupting traditional banking",
                    "Robo-advisory replacing human wealth management",
                    "AI-powered lending platforms reducing margins",
                ],
            },
            "cost_structure": {
                "weight": 0.25,
                "threat_level": "HIGH",
                "activities": [
                    "AI fraud detection reducing loss ratios",
                    "Automated underwriting and credit decisioning",
                    "AI compliance monitoring and reporting",
                ],
            },
            "competitive_moat": {
                "weight": 0.20,
                "threat_level": "MEDIUM",
                "activities": [
                    "AI leveling playing field between large and small firms",
                    "Alternative data AI reducing information advantages",
                ],
            },
            "workforce_automation": {
                "weight": 0.25,
                "threat_level": "HIGH",
                "activities": [
                    "AI replacing back-office processing roles",
                    "Automated customer service and onboarding",
                    "AI-driven trading reducing human trader roles",
                ],
            },
            "regulatory_ip": {
                "weight": 0.10,
                "threat_level": "MEDIUM",
                "activities": [
                    "AI model explainability requirements (Fair Lending)",
                    "Algorithmic bias in credit decisions",
                    "AI in AML/KYC regulatory compliance",
                ],
            },
        },
    },
    {
        "id": "ENERGY_UTILITIES",
        "industry": "Energy / Utilities",
        "sic_ranges": [(1200, 1299), (1300, 1389), (2900, 2999), (4900, 4991)],
        "exposure_areas": {
            "revenue_displacement": {
                "weight": 0.10,
                "threat_level": "LOW",
                "activities": [
                    "AI-optimized distributed energy reducing utility demand",
                    "Smart grid AI enabling peer-to-peer energy trading",
                ],
            },
            "cost_structure": {
                "weight": 0.30,
                "threat_level": "HIGH",
                "activities": [
                    "AI predictive maintenance reducing downtime 30-50%",
                    "AI grid optimization and demand forecasting",
                    "Autonomous drilling and extraction operations",
                ],
            },
            "competitive_moat": {
                "weight": 0.15,
                "threat_level": "LOW",
                "activities": [
                    "AI enabling faster renewable energy integration",
                    "Digital twins reducing capital planning advantages",
                ],
            },
            "workforce_automation": {
                "weight": 0.30,
                "threat_level": "HIGH",
                "activities": [
                    "Autonomous inspection and maintenance drones",
                    "AI-driven field operations scheduling",
                    "Automated meter reading and billing",
                ],
            },
            "regulatory_ip": {
                "weight": 0.15,
                "threat_level": "MEDIUM",
                "activities": [
                    "AI in environmental compliance monitoring",
                    "Algorithmic rate-setting regulatory scrutiny",
                    "AI grid reliability requirements",
                ],
            },
        },
    },
    {
        "id": "HEALTHCARE",
        "industry": "Healthcare Services / Providers",
        "sic_ranges": [(8000, 8099), (5912, 5912), (5047, 5047)],
        "exposure_areas": {
            "revenue_displacement": {
                "weight": 0.20,
                "threat_level": "MEDIUM",
                "activities": [
                    "AI diagnostic tools reducing specialist referrals",
                    "Telehealth AI triage reducing ER visits",
                    "AI-powered virtual care replacing in-person visits",
                ],
            },
            "cost_structure": {
                "weight": 0.25,
                "threat_level": "HIGH",
                "activities": [
                    "AI clinical decision support reducing errors",
                    "Automated medical coding and billing",
                    "AI scheduling and resource optimization",
                ],
            },
            "competitive_moat": {
                "weight": 0.15,
                "threat_level": "MEDIUM",
                "activities": [
                    "AI enabling smaller providers to match large systems",
                    "Data advantages eroded by federated learning",
                ],
            },
            "workforce_automation": {
                "weight": 0.25,
                "threat_level": "HIGH",
                "activities": [
                    "AI radiology and pathology reducing specialist demand",
                    "Automated patient intake and documentation",
                    "AI nursing assistants and monitoring",
                ],
            },
            "regulatory_ip": {
                "weight": 0.15,
                "threat_level": "MEDIUM",
                "activities": [
                    "FDA SaMD (Software as Medical Device) approval complexity",
                    "HIPAA implications of AI data processing",
                    "AI liability in clinical decision-making",
                ],
            },
        },
    },
    {
        "id": "GENERIC",
        "industry": "General / Other Industries",
        "sic_ranges": [],
        "exposure_areas": {
            "revenue_displacement": {
                "weight": 0.25,
                "threat_level": "MEDIUM",
                "activities": [
                    "AI-enabled competitors disrupting traditional business",
                    "AI-powered alternatives reducing market share",
                ],
            },
            "cost_structure": {
                "weight": 0.20,
                "threat_level": "MEDIUM",
                "activities": [
                    "AI automation of routine business processes",
                    "AI-driven supply chain optimization",
                ],
            },
            "competitive_moat": {
                "weight": 0.25,
                "threat_level": "MEDIUM",
                "activities": [
                    "AI reducing barriers to entry in industry",
                    "AI leveling operational advantages",
                ],
            },
            "workforce_automation": {
                "weight": 0.20,
                "threat_level": "MEDIUM",
                "activities": [
                    "AI replacing administrative and clerical roles",
                    "Automated customer interaction workflows",
                ],
            },
            "regulatory_ip": {
                "weight": 0.10,
                "threat_level": "LOW",
                "activities": [
                    "General AI regulatory framework evolution",
                    "AI-related IP ownership questions",
                ],
            },
        },
    },
]
"""All 6 AI impact model definitions (5 verticals + GENERIC fallback)."""


# ---------------------------------------------------------------------------
# Model lookup
# ---------------------------------------------------------------------------

_GENERIC_MODEL: dict[str, Any] = AI_IMPACT_MODELS[-1]


def get_ai_impact_model(
    sic_code: int | None,
    playbook_id: str | None,
) -> dict[str, Any]:
    """Select the AI impact model for a company.

    Priority:
    1. Match by playbook_id (exact match on model 'id')
    2. Match by SIC code range
    3. Return GENERIC fallback

    Args:
        sic_code: Company SIC code (may be None)
        playbook_id: Active playbook ID from state (e.g. 'TECH_SAAS')

    Returns:
        The matching AI impact model dict.
    """
    # 1. Try playbook_id match
    if playbook_id is not None:
        for model in AI_IMPACT_MODELS:
            if model["id"] == playbook_id:
                return model

    # 2. Try SIC range match
    if sic_code is not None:
        for model in AI_IMPACT_MODELS:
            sic_ranges: list[tuple[int, int]] = model.get("sic_ranges", [])
            for low, high in sic_ranges:
                if low <= sic_code <= high:
                    return model

    # 3. GENERIC fallback
    return _GENERIC_MODEL
