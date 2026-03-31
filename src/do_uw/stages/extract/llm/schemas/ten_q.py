"""10-Q quarterly report extraction schema.

Pydantic model for extracting D&O-relevant data from 10-Q quarterly
reports in a single LLM API call. Focuses on quarterly changes and
new developments rather than comprehensive annual data (that is the
10-K schema's job).

Also used for 6-K (foreign private issuer quarterly report) via the
schema registry.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from do_uw.stages.extract.llm.schemas.common import (
    ExtractedLegalProceeding,
    ExtractedRiskFactor,
)


class TenQExtraction(BaseModel):
    """Complete extraction schema for 10-Q quarterly reports.

    One model, one API call. Focused on quarterly changes and new
    developments since the last filing. All fields optional with defaults.
    """

    # ------------------------------------------------------------------
    # Filing metadata
    # ------------------------------------------------------------------
    quarter: str | None = Field(
        default=None,
        description="Quarter identifier, e.g. 'Q1 2025', 'Q3 2024'",
    )
    period_end: str | None = Field(
        default=None,
        description="Period end date, e.g. '2025-03-31'",
    )

    # ------------------------------------------------------------------
    # Financial highlights
    # ------------------------------------------------------------------
    revenue: float | None = Field(
        default=None,
        description="Total revenue for the quarter in USD",
    )
    net_income: float | None = Field(
        default=None,
        description="Net income (loss) for the quarter in USD",
    )
    eps: float | None = Field(
        default=None,
        description="Diluted earnings per share for the quarter",
    )

    # ------------------------------------------------------------------
    # Prior-year comparison (from 10-Q's comparison columns)
    # ------------------------------------------------------------------
    prior_year_revenue: float | None = Field(
        default=None,
        description=(
            "Revenue for the same YTD period in the prior year, "
            "from the 10-Q comparison column. E.g., for a Q2 filing "
            "this is the 6-month YTD revenue from the prior fiscal year."
        ),
    )
    prior_year_net_income: float | None = Field(
        default=None,
        description=(
            "Net income for the same YTD period in the prior year, "
            "from the 10-Q comparison column."
        ),
    )
    prior_year_eps: float | None = Field(
        default=None,
        description=(
            "Diluted EPS for the same YTD period in the prior year, "
            "from the 10-Q comparison column."
        ),
    )

    # ------------------------------------------------------------------
    # Legal proceedings (NEW matters since last filing)
    # ------------------------------------------------------------------
    new_legal_proceedings: list[ExtractedLegalProceeding] = Field(
        default_factory=lambda: [],
        description=(
            "Only NEW legal proceedings disclosed since the last filing. "
            "Do not include matters previously reported."
        ),
    )
    legal_proceedings_updates: list[str] = Field(
        default_factory=lambda: [],
        description=(
            "Updates to previously reported matters, "
            "e.g. ['Smith v. Acme: Motion to dismiss granted']"
        ),
    )

    # ------------------------------------------------------------------
    # Going concern and controls
    # ------------------------------------------------------------------
    going_concern: bool = Field(
        default=False,
        description="Whether a going concern qualification is present",
    )
    going_concern_detail: str | None = Field(
        default=None,
        description="Going concern language if present, max 300 chars",
    )
    material_weaknesses: list[str] = Field(
        default_factory=lambda: [],
        description="Material weaknesses in internal controls disclosed",
    )

    # ------------------------------------------------------------------
    # Risk factors (only new or materially changed)
    # ------------------------------------------------------------------
    new_risk_factors: list[ExtractedRiskFactor] = Field(
        default_factory=lambda: [],
        description=(
            "Only NEW or materially changed risk factors since the "
            "last annual report. Skip risk factors carried forward unchanged."
        ),
    )

    # ------------------------------------------------------------------
    # MD&A highlights
    # ------------------------------------------------------------------
    management_discussion_highlights: list[str] = Field(
        default_factory=lambda: [],
        description=(
            "Key changes or concerns from MD&A, "
            "e.g. ['Revenue declined 8% due to macro headwinds', "
            "'Announced restructuring affecting 500 employees']"
        ),
    )

    # ------------------------------------------------------------------
    # Subsequent events
    # ------------------------------------------------------------------
    subsequent_events: list[str] = Field(
        default_factory=lambda: [],
        description=(
            "Events occurring after quarter end but before filing, "
            "e.g. ['Acquired XYZ Corp for $500M on April 15']"
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
