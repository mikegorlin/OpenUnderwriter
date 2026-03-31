"""Shared sub-models for LLM extraction schemas.

These lightweight models are used across multiple filing-type schemas.
They are intentionally flat (max 2 levels nesting) to comply with
Anthropic structured output limits. All fields are optional with
defaults since the LLM may not find every piece of information.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ExtractedPerson(BaseModel):
    """A person mentioned in a filing (officer, director, insider)."""

    name: str = ""
    title: str | None = None
    age: int | None = None
    tenure_years: float | None = None


class MoneyAmount(BaseModel):
    """A monetary amount with currency and optional period context."""

    amount: float | None = None
    currency: str = "USD"
    period: str | None = Field(
        default=None, description="Fiscal period, e.g. 'FY2025', 'Q3 2024'"
    )


class ExtractedContingency(BaseModel):
    """ASC 450 contingent liability from 10-K footnotes.

    IMPORTANT: Only extract LITIGATION-related contingencies (lawsuits,
    regulatory actions, settlements, legal claims). Do NOT include
    warranty reserves, product guarantees, tax positions, or
    environmental remediation obligations.
    """

    description: str = ""
    classification: str | None = Field(
        default=None,
        description="ASC 450: probable, reasonably_possible, remote",
    )
    contingency_type: str | None = Field(
        default=None,
        description=(
            "Type: 'litigation', 'regulatory', 'warranty', 'tax', "
            "'environmental', 'other'. Used to filter litigation reserves."
        ),
    )
    accrued_amount: float | None = Field(
        default=None,
        description="Accrued amount in USD (millions — e.g. 176.0 means $176M)",
    )
    range_low: float | None = Field(
        default=None, description="Low end of range of possible loss in USD"
    )
    range_high: float | None = Field(
        default=None, description="High end of range of possible loss in USD"
    )
    source_passage: str = Field(
        default="", description="Exact quote from filing, max 200 chars"
    )


class ExtractedLegalProceeding(BaseModel):
    """A legal proceeding disclosed in a filing (Item 3, 10-Q, 8-K)."""

    case_name: str = ""
    court: str | None = Field(
        default=None, description="Court name, e.g. 'S.D.N.Y.'"
    )
    filing_date: str | None = Field(
        default=None, description="Date complaint was filed (YYYY-MM-DD)"
    )
    allegations: str | None = Field(
        default=None,
        description="Brief description of claims (10b-5, Section 11, etc.)",
    )
    status: str | None = Field(
        default=None,
        description="Case status: ACTIVE, SETTLED, DISMISSED, APPEAL",
    )
    settlement_amount: float | None = Field(
        default=None,
        description=(
            "Settlement amount in USD if status is SETTLED or resolved. "
            "IMPORTANT: Always extract this for settled cases — check "
            "footnotes, Item 3, and 8-K disclosures for settlement "
            "amounts. Use millions (e.g. 176.0 means $176M)."
        ),
    )
    class_period_start: str | None = Field(
        default=None, description="Start of alleged class period (YYYY-MM-DD)"
    )
    class_period_end: str | None = Field(
        default=None, description="End of alleged class period (YYYY-MM-DD)"
    )
    legal_theories: list[str] = Field(
        default_factory=lambda: [],
        description="Legal theories invoked, e.g. ['10b-5', 'Section 11', 'ERISA']",
    )
    named_defendants: list[str] = Field(
        default_factory=lambda: [],
        description="Individual officer/director defendants named in the case",
    )
    accrued_amount: float | None = Field(
        default=None,
        description="Accrued amount from contingent liability footnote in USD",
    )
    source_passage: str = Field(
        default="",
        description="Exact quote from filing, max 200 chars",
    )


class ExtractedRiskFactor(BaseModel):
    """A risk factor from Item 1A or 10-Q risk factor updates."""

    title: str = ""
    category: str = Field(
        default="OTHER",
        description=(
            "Category: LITIGATION, REGULATORY, FINANCIAL, "
            "OPERATIONAL, CYBER, ESG, AI, OTHER"
        ),
    )
    severity: str = Field(
        default="MEDIUM",
        description="Severity assessment: HIGH, MEDIUM, LOW",
    )
    is_new_this_year: bool = Field(
        default=False,
        description="True if this risk factor was added or materially changed",
    )
    source_passage: str = Field(
        default="",
        description="Key excerpt from the risk factor text, max 500 chars",
    )


class ExtractedDirector(BaseModel):
    """A board director from a DEF 14A proxy statement."""

    name: str = ""
    age: int | None = None
    independent: bool | None = Field(
        default=None, description="Whether the director is classified as independent"
    )
    tenure_years: float | None = None
    committees: list[str] = Field(
        default_factory=lambda: [],
        description="Committee memberships (Audit, Compensation, Nominating, etc.)",
    )
    other_boards: list[str] = Field(
        default_factory=lambda: [],
        description="Other public company boards the director serves on",
    )
    qualifications: str = Field(
        default="",
        description=(
            "Director qualifications and experience from proxy bio: "
            "prior executive roles, industry expertise, relevant degrees, "
            "and why this person is qualified to serve on this board. Max 300 chars."
        ),
    )
    qualification_tags: list[str] = Field(
        default_factory=lambda: [],
        description=(
            "Structured qualification tags from director bio. "
            "Use ONLY these values: 'industry_expertise', 'financial_expert', "
            "'legal_regulatory', 'technology', 'public_company_experience', "
            "'prior_c_suite'. Set each tag that applies based on the director's "
            "biography, experience, and qualifications described in the proxy."
        ),
    )
    source_passage: str = Field(
        default="",
        description="Brief excerpt from the proxy bio, max 200 chars",
    )


class ExtractedCompensation(BaseModel):
    """Named executive officer compensation from Summary Compensation Table."""

    name: str = ""
    title: str | None = None
    salary: float | None = Field(
        default=None, description="Base salary in USD"
    )
    bonus: float | None = Field(
        default=None, description="Bonus in USD"
    )
    stock_awards: float | None = Field(
        default=None, description="Stock awards value in USD"
    )
    option_awards: float | None = Field(
        default=None, description="Option awards value in USD"
    )
    non_equity_incentive: float | None = Field(
        default=None, description="Non-equity incentive plan compensation in USD"
    )
    other_comp: float | None = Field(
        default=None, description="All other compensation in USD"
    )
    total_comp: float | None = Field(
        default=None, description="Total compensation in USD"
    )
    background: str = Field(
        default="",
        description=(
            "Executive background from proxy bio: prior roles, industry experience, "
            "education, and qualifications for current position. Max 300 chars."
        ),
    )
    source_passage: str = Field(
        default="",
        description="Excerpt from SCT or comp discussion, max 200 chars",
    )
