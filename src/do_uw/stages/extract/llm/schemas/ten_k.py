"""10-K annual report extraction schema.

Comprehensive Pydantic model for extracting ALL D&O-relevant data from
a 10-K filing in a single LLM API call. Covers Items 1, 1A, 3, 5, 7,
7A, 8, 9A, and 10-14.

Also used for 20-F (foreign private issuer annual report) via the
schema registry, since 20-F covers equivalent content.
"""

from __future__ import annotations

import re
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, Field

from do_uw.stages.extract.llm.schemas.common import (
    ExtractedContingency,
    ExtractedLegalProceeding,
    ExtractedRiskFactor,
)


def _coerce_currency_float(v: Any) -> Any:
    """Strip currency symbols/commas so '$70.0' or '1,234.5' → float."""
    if isinstance(v, str):
        cleaned = re.sub(r"[^\d.\-]", "", v)
        if cleaned:
            return float(cleaned)
        return None
    return v


def _coerce_to_list(v: Any) -> Any:
    """Wrap a bare string in a list so 'foo' → ['foo']."""
    if isinstance(v, str):
        return [v] if v.strip() else []
    return v


# Reusable annotated types for LLM-resilient parsing
CurrencyFloat = Annotated[float | None, BeforeValidator(_coerce_currency_float)]
CoercedStrList = Annotated[list[str], BeforeValidator(_coerce_to_list)]


class TenKExtraction(BaseModel):
    """Complete extraction schema for 10-K annual reports.

    One model, one API call. All fields optional with defaults so the
    LLM returns whatever it can find. Fields are organized by 10-K Item
    for clarity but the entire filing is sent as one document.
    """

    # ------------------------------------------------------------------
    # Filing metadata (extracted from document header)
    # ------------------------------------------------------------------
    fiscal_year_end: str | None = Field(
        default=None,
        description="Fiscal year end date, e.g. 'December 31, 2024'",
    )
    period_of_report: str | None = Field(
        default=None,
        description="Period of report, e.g. '2024-12-31' or 'December 31, 2024'",
    )

    # ------------------------------------------------------------------
    # Item 1: Business
    # ------------------------------------------------------------------
    business_description: str | None = Field(
        default=None,
        description=(
            "Comprehensive 4-6 sentence business narrative covering: "
            "(1) what the company does — core business, products, and services; "
            "(2) how they generate revenue — business model, key revenue streams "
            "and their relative importance; "
            "(3) how they earn — profitability drivers, margins, and competitive "
            "advantages. Write as a clear, professional narrative suitable for "
            "an insurance underwriting report."
        ),
    )
    revenue_segments: CoercedStrList = Field(
        default_factory=lambda: [],
        description=(
            "Revenue segments or product lines mentioned, "
            "e.g. ['Cloud Services: 60%', 'Licensing: 40%']"
        ),
    )
    geographic_regions: CoercedStrList = Field(
        default_factory=lambda: [],
        description=(
            "Geographic revenue breakdown, "
            "e.g. ['United States: 55%', 'International: 45%']"
        ),
    )
    employee_count: int | None = Field(
        default=None,
        description=(
            "Total number of individual employees (headcount). "
            "If the filing says 'approximately 62 thousand' or '62,000', "
            "return 62000. Always return the full integer count, "
            "not abbreviated thousands. For example: 61500, not 61.5 or 62."
        ),
    )
    customer_concentration: CoercedStrList = Field(
        default_factory=lambda: [],
        description=(
            "Major customer concentration disclosures, "
            "e.g. ['Customer A is 15% of revenue']"
        ),
    )
    supplier_concentration: CoercedStrList = Field(
        default_factory=lambda: [],
        description="Key supplier dependencies or single-source risks",
    )
    competitive_position: str | None = Field(
        default=None,
        description="Brief summary of competitive position and key competitors",
    )
    regulatory_environment: str | None = Field(
        default=None,
        description="Key regulatory bodies and compliance requirements",
    )
    is_dual_class: bool | None = Field(
        default=None,
        description="Whether the company has a dual-class share structure",
    )
    has_vie: bool | None = Field(
        default=None,
        description="Whether the company consolidates variable interest entities",
    )

    # --- Item 1: Workforce (Human Capital) ---
    domestic_employee_count: int | None = Field(
        default=None,
        description="Number of domestic (US) employees if disclosed separately",
    )
    international_employee_count: int | None = Field(
        default=None,
        description="Number of international (non-US) employees if disclosed separately",
    )
    unionized_employee_count: int | None = Field(
        default=None,
        description="Number of unionized employees or employees covered by collective bargaining agreements",
    )
    unionized_employee_pct: float | None = Field(
        default=None,
        description="Percentage of employees covered by collective bargaining agreements (0-100)",
    )

    # --- Item 1: Operational Resilience ---
    primary_operations_geography: str | None = Field(
        default=None,
        description="Where the company's primary operations/manufacturing/facilities are concentrated (e.g. 'United States', 'China and Southeast Asia')",
    )
    single_facility_dependency: bool | None = Field(
        default=None,
        description="Whether the company depends on a single critical facility or manufacturing site",
    )
    supply_chain_description: str | None = Field(
        default=None,
        description="Brief description of supply chain depth and key dependencies (e.g. 'vertically integrated', 'relies on single-source suppliers for key components', 'diversified global supply chain')",
    )

    # ------------------------------------------------------------------
    # Item 1: Business Model Dimensions (v6.0 BMOD)
    # ------------------------------------------------------------------
    revenue_model_type: str | None = Field(
        default=None,
        description=(
            "Classify the primary revenue model as one of: RECURRING (subscriptions, "
            "licenses, maintenance contracts), PROJECT (long-term contracts, construction, "
            "consulting engagements), TRANSACTION (per-unit sales, fee-per-transaction), "
            "or HYBRID (meaningful mix of multiple types). Base classification on revenue "
            "recognition policies in Item 1 and notes to financial statements."
        ),
    )
    is_founder_led: bool | None = Field(
        default=None,
        description=(
            "Whether the current CEO is the company founder or co-founder. "
            "Check Item 10 or proxy statement references."
        ),
    )
    ceo_tenure_years: int | None = Field(
        default=None,
        description=(
            "Number of years the current CEO has been in the CEO role. "
            "Compute from appointment date if mentioned."
        ),
    )
    has_succession_plan: bool | None = Field(
        default=None,
        description=(
            "Whether the company discloses a CEO/executive succession plan. "
            "Look for explicit succession planning language in proxy/10-K."
        ),
    )
    segment_lifecycle_stages: CoercedStrList = Field(
        default_factory=lambda: [],
        description=(
            "For each reported segment, classify its lifecycle stage: "
            "'GROWTH' (revenue growing >10% YoY), 'MATURE' (stable, <10% growth), "
            "or 'DECLINING' (negative growth). Format: "
            "['Segment Name: GROWTH (15% YoY)', 'Segment B: DECLINING (-5% YoY)']"
        ),
    )
    disruption_threats: CoercedStrList = Field(
        default_factory=lambda: [],
        description=(
            "Specific competitive or technological threats to the business model "
            "mentioned in Item 1 or Item 1A risk factors. Focus on existential "
            "threats: new entrants, technology shifts, regulatory changes that "
            "could disrupt the core business model. "
            "e.g. ['AI-driven automation threatening consulting revenue', "
            "'Generic competition after patent expiry in 2025']"
        ),
    )
    segment_margins: CoercedStrList = Field(
        default_factory=lambda: [],
        description=(
            "Operating margin by segment if disclosed in segment reporting. "
            "Format: ['Segment Name: 25.3% (prior year: 27.1%)', "
            "'Segment B: 12.0% (prior year: 14.5%)']. "
            "Include prior year for trend analysis."
        ),
    )

    # ------------------------------------------------------------------
    # Item 1A: Risk Factors
    # ------------------------------------------------------------------
    risk_factors: list[ExtractedRiskFactor] = Field(
        default_factory=lambda: [],
        description=(
            "Top 25 most significant risk factors. Prioritize D&O-relevant "
            "risks: litigation, regulatory, financial restatement, "
            "cybersecurity, executive misconduct"
        ),
    )

    # ------------------------------------------------------------------
    # Item 3: Legal Proceedings
    # ------------------------------------------------------------------
    legal_proceedings: list[ExtractedLegalProceeding] = Field(
        default_factory=lambda: [],
        description="All legal proceedings disclosed in Item 3",
    )

    # ------------------------------------------------------------------
    # Item 5: Market for Registrant's Common Equity
    # ------------------------------------------------------------------
    stock_exchange: str | None = Field(
        default=None,
        description="Primary stock exchange, e.g. 'NASDAQ', 'NYSE'",
    )
    share_repurchase_amount: CurrencyFloat = Field(
        default=None,
        description="Total share repurchase amount in USD during the period",
    )

    # ------------------------------------------------------------------
    # Item 7: Management's Discussion and Analysis (MD&A)
    # ------------------------------------------------------------------
    revenue_trend: str | None = Field(
        default=None,
        description=(
            "Revenue trend summary: growing/declining/stable with "
            "percentage, e.g. 'Growing 12% YoY'"
        ),
    )
    margin_trend: str | None = Field(
        default=None,
        description=(
            "Operating/gross margin trend, "
            "e.g. 'Gross margin declined from 65% to 61%'"
        ),
    )
    key_financial_concerns: CoercedStrList = Field(
        default_factory=lambda: [],
        description=(
            "Key concerns or challenges mentioned in MD&A, "
            "e.g. ['Rising input costs', 'Foreign exchange headwinds']"
        ),
    )
    critical_accounting_estimates: CoercedStrList = Field(
        default_factory=lambda: [],
        description=(
            "Critical accounting estimates and policies mentioned, "
            "e.g. ['Revenue recognition', 'Goodwill impairment testing']"
        ),
    )
    guidance_language: str | None = Field(
        default=None,
        description=(
            "Any forward-looking statements or guidance language "
            "from MD&A, max 300 chars"
        ),
    )
    non_gaap_measures: CoercedStrList = Field(
        default_factory=lambda: [],
        description=(
            "Non-GAAP financial measures used, "
            "e.g. ['Adjusted EBITDA', 'Free Cash Flow', 'Non-GAAP EPS']"
        ),
    )

    # ------------------------------------------------------------------
    # Item 7A: Quantitative and Qualitative Disclosures About Market Risk
    # ------------------------------------------------------------------
    interest_rate_risk: str | None = Field(
        default=None,
        description="Interest rate risk exposure summary",
    )
    currency_risk: str | None = Field(
        default=None,
        description="Foreign currency risk exposure summary",
    )
    commodity_risk: str | None = Field(
        default=None,
        description="Commodity price risk exposure summary",
    )

    # ------------------------------------------------------------------
    # Item 8: Financial Statements (footnote highlights only)
    # ------------------------------------------------------------------
    going_concern: bool = Field(
        default=False,
        description="Whether a going concern qualification is present",
    )
    going_concern_detail: str | None = Field(
        default=None,
        description="Going concern language if present, max 300 chars",
    )
    material_weaknesses: CoercedStrList = Field(
        default_factory=lambda: [],
        description=(
            "Actual material weaknesses in internal controls FOUND by management "
            "or auditors. Only include findings like 'We identified a material "
            "weakness in...' or 'Management identified a material weakness...'. "
            "Do NOT include standard audit methodology language that describes "
            "the audit process (e.g., 'assessing the risk that a material "
            "weakness exists' or 'obtaining an understanding of internal control')."
        ),
    )
    debt_instruments: CoercedStrList = Field(
        default_factory=lambda: [],
        description=(
            "Key debt instruments with terms, "
            "e.g. ['$500M Senior Notes due 2027 at 4.5%']"
        ),
    )
    credit_facility_detail: str | None = Field(
        default=None,
        description="Revolving credit facility details (amount, maturity, terms)",
    )
    covenant_status: str | None = Field(
        default=None,
        description=(
            "Covenant compliance status and any near-breach situations"
        ),
    )
    contingent_liabilities: list[ExtractedContingency] = Field(
        default_factory=lambda: [],
        description=(
            "ASC 450 contingent liabilities from footnotes. "
            "Focus on LITIGATION and REGULATORY contingencies "
            "(lawsuits, settlements, enforcement actions, legal reserves). "
            "Set contingency_type for each. Include accrued amounts in "
            "millions USD (e.g. 176.0 = $176M). Exclude warranty reserves "
            "and tax positions unless they are litigation-related."
        ),
    )
    tax_rate_notes: str | None = Field(
        default=None,
        description="Effective tax rate and any notable tax positions",
    )
    stock_comp_detail: str | None = Field(
        default=None,
        description="Stock-based compensation total and key details",
    )

    # ------------------------------------------------------------------
    # Business Combinations / Acquisitions (from footnotes)
    # ------------------------------------------------------------------
    goodwill_balance: CurrencyFloat | None = Field(
        default=None,
        description=(
            "Total goodwill on balance sheet in millions USD. "
            "Extract from footnote on goodwill or balance sheet."
        ),
    )
    acquisitions_total_spend: CurrencyFloat | None = Field(
        default=None,
        description=(
            "Total cash paid for acquisitions during the fiscal year in millions USD. "
            "Extract from cash flow statement or business combination footnote."
        ),
    )
    acquisitions: CoercedStrList = Field(
        default_factory=lambda: [],
        description=(
            "List of acquisitions completed during or after the fiscal year. "
            "Include company name, approximate date, deal value if disclosed, "
            "and strategic rationale. "
            "e.g. ['Acquired Shazam (2018, ~$400M, music recognition technology)', "
            "'Acquired Intel modem business (2019, ~$1B, 5G modem development)']"
        ),
    )
    goodwill_change_description: str | None = Field(
        default=None,
        description=(
            "Summary of goodwill changes during the year: additions from "
            "acquisitions, impairments, and net change. Max 300 chars."
        ),
    )

    # ------------------------------------------------------------------
    # Item 9A: Controls and Procedures
    # ------------------------------------------------------------------
    has_material_weakness: bool = Field(
        default=False,
        description="Whether any material weakness is reported in Item 9A",
    )
    material_weakness_detail: CoercedStrList = Field(
        default_factory=lambda: [],
        description=(
            "Details of each actual material weakness REPORTED by management "
            "or identified by auditors. Only include substantive findings "
            "(e.g., 'ineffective IT general controls over financial reporting'). "
            "Do NOT include standard PCAOB audit methodology language that "
            "describes audit procedures (e.g., 'assessing the risk that a "
            "material weakness exists', 'testing and evaluating the design "
            "and operating effectiveness of internal control')."
        ),
    )
    significant_deficiencies: CoercedStrList = Field(
        default_factory=lambda: [],
        description="Significant deficiencies in internal controls",
    )
    remediation_status: str | None = Field(
        default=None,
        description="Status of remediation for any control deficiencies",
    )
    auditor_attestation: str | None = Field(
        default=None,
        description=(
            "Auditor's attestation on internal controls "
            "(required for accelerated filers)"
        ),
    )

    # ------------------------------------------------------------------
    # Items 10-14: Directors, Officers, Governance
    # ------------------------------------------------------------------
    auditor_name: str | None = Field(
        default=None,
        description="Independent registered public accounting firm name",
    )
    auditor_tenure_years: int | None = Field(
        default=None,
        description="Number of years the current auditor has served",
    )
    auditor_opinion_type: str | None = Field(
        default=None,
        description=(
            "Audit opinion type: unqualified, qualified, adverse, disclaimer"
        ),
    )
    related_party_transactions: CoercedStrList = Field(
        default_factory=lambda: [],
        description=(
            "Related party transactions disclosed, "
            "e.g. ['CEO's brother-in-law provides consulting services']"
        ),
    )

    # ------------------------------------------------------------------
    # Brain-requested fields (dynamic extraction targets)
    # ------------------------------------------------------------------
    brain_fields: dict[str, object] = Field(
        default_factory=dict,
        description=(
            "Additional fields requested by the underwriting brain. "
            "Extract as key-value pairs if found in the document."
        ),
    )
