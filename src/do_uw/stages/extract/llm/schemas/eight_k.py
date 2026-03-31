"""8-K current report extraction schema.

Comprehensive Pydantic model for extracting D&O-relevant data from
8-K current reports in a single LLM API call. Covers all material
event Items (1.01, 1.02, 2.01, 2.02, 2.05, 2.06, 4.01, 4.02,
5.02, 5.03, 5.05, 8.01).

8-Ks are flat documents covering a single event (or a few related
events). The schema is designed as one flat model with all fields
optional -- a given 8-K will only populate the subset relevant to
its Item coverage.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class EightKExtraction(BaseModel):
    """Complete extraction schema for 8-K current reports.

    One model, one API call. All fields optional with defaults.
    A given 8-K covers one or a few Items, so most fields will be null.
    """

    # ------------------------------------------------------------------
    # Filing metadata
    # ------------------------------------------------------------------
    event_date: str | None = Field(
        default=None,
        description="Date of the reported event (YYYY-MM-DD)",
    )
    event_type: str | None = Field(
        default=None,
        description=(
            "Primary Item number and title, e.g. "
            "'2.02 Results of Operations and Financial Condition'"
        ),
    )
    items_covered: list[str] = Field(
        default_factory=lambda: [],
        description=(
            "All Item numbers covered in this 8-K, "
            "e.g. ['2.02', '9.01']. MUST be populated."
        ),
    )

    # ------------------------------------------------------------------
    # Item 1.01: Entry into a Material Definitive Agreement
    # ------------------------------------------------------------------
    agreement_type: str | None = Field(
        default=None,
        description=(
            "Type of agreement: merger, credit agreement, "
            "license, settlement, etc."
        ),
    )
    counterparty: str | None = Field(
        default=None,
        description="Name of the other party to the agreement",
    )
    agreement_summary: str | None = Field(
        default=None,
        description="Brief summary of key agreement terms, max 300 chars",
    )

    # ------------------------------------------------------------------
    # Item 1.02: Termination of a Material Definitive Agreement
    # ------------------------------------------------------------------
    terminated_agreement: str | None = Field(
        default=None,
        description="Name/type of the terminated agreement",
    )
    termination_reason: str | None = Field(
        default=None,
        description="Reason for termination (breach, expiration, mutual, etc.)",
    )
    termination_counterparty: str | None = Field(
        default=None,
        description="Name of the counterparty to the terminated agreement",
    )

    # ------------------------------------------------------------------
    # Item 2.01: Completion of Acquisition or Disposition of Assets
    # ------------------------------------------------------------------
    transaction_type: str | None = Field(
        default=None,
        description="Type: acquisition, disposition, merger, divestiture",
    )
    target_name: str | None = Field(
        default=None,
        description="Name of the acquired or disposed entity/assets",
    )
    transaction_value: float | None = Field(
        default=None,
        description="Transaction value in USD",
    )

    # ------------------------------------------------------------------
    # Item 2.02: Results of Operations and Financial Condition
    # ------------------------------------------------------------------
    revenue: float | None = Field(
        default=None,
        description="Revenue reported for the period in USD",
    )
    eps: float | None = Field(
        default=None,
        description="Earnings per share (diluted) reported",
    )
    guidance_update: str | None = Field(
        default=None,
        description=(
            "Any guidance update or revision, e.g. "
            "'Lowered FY2025 revenue guidance to $4.5B-$4.7B'"
        ),
    )

    # ------------------------------------------------------------------
    # Item 2.05: Costs Associated with Exit or Disposal Activities
    # ------------------------------------------------------------------
    restructuring_type: str | None = Field(
        default=None,
        description=(
            "Type of restructuring: layoffs, facility closure, "
            "segment exit, organizational restructuring"
        ),
    )
    restructuring_charge: float | None = Field(
        default=None,
        description="Total restructuring charge in USD",
    )
    restructuring_description: str | None = Field(
        default=None,
        description="Brief description of the restructuring plan, max 300 chars",
    )

    # ------------------------------------------------------------------
    # Item 2.06: Material Impairments
    # ------------------------------------------------------------------
    impairment_type: str | None = Field(
        default=None,
        description=(
            "Type of impairment: goodwill, intangible assets, "
            "long-lived assets, investments"
        ),
    )
    impairment_amount: float | None = Field(
        default=None,
        description="Impairment charge amount in USD",
    )
    impairment_description: str | None = Field(
        default=None,
        description="Brief description of what triggered the impairment, max 300 chars",
    )

    # ------------------------------------------------------------------
    # Item 4.01: Changes in Registrant's Certifying Accountant
    # ------------------------------------------------------------------
    former_auditor: str | None = Field(
        default=None,
        description="Name of the former auditing firm",
    )
    new_auditor: str | None = Field(
        default=None,
        description="Name of the new auditing firm",
    )
    auditor_disagreements: bool | None = Field(
        default=None,
        description=(
            "Whether there were disagreements between registrant "
            "and former auditor on accounting matters"
        ),
    )

    # ------------------------------------------------------------------
    # Item 4.02: Non-Reliance on Previously Issued Financial Statements
    # ------------------------------------------------------------------
    restatement_periods: list[str] = Field(
        default_factory=lambda: [],
        description=(
            "Periods affected by restatement, "
            "e.g. ['Q1 2024', 'Q2 2024', 'FY2023']"
        ),
    )
    restatement_reason: str | None = Field(
        default=None,
        description="Reason for the restatement or non-reliance determination",
    )

    # ------------------------------------------------------------------
    # Item 5.02: Departure/Appointment of Directors or Officers
    # ------------------------------------------------------------------
    departing_officer: str | None = Field(
        default=None,
        description="Name of the departing officer or director",
    )
    departing_officer_title: str | None = Field(
        default=None,
        description="Title of the departing officer, e.g. 'Chief Financial Officer'",
    )
    departure_reason: str | None = Field(
        default=None,
        description=(
            "Reason for departure: resignation, retirement, "
            "termination, death, etc."
        ),
    )
    successor: str | None = Field(
        default=None,
        description="Name of the successor, if announced",
    )
    is_termination: bool | None = Field(
        default=None,
        description="Whether the departure was an involuntary termination",
    )

    # ------------------------------------------------------------------
    # Item 5.03: Amendments to Articles of Incorporation or Bylaws
    # ------------------------------------------------------------------
    bylaws_amendment_type: str | None = Field(
        default=None,
        description=(
            "Type of amendment: forum selection, supermajority voting, "
            "advance notice, officer exculpation, etc."
        ),
    )
    bylaws_amendment_summary: str | None = Field(
        default=None,
        description="Brief summary of what changed in the governing documents, max 300 chars",
    )

    # ------------------------------------------------------------------
    # Item 5.05: Amendment to Code of Ethics or Waiver
    # ------------------------------------------------------------------
    ethics_change_type: str | None = Field(
        default=None,
        description="'amendment' or 'waiver'",
    )
    ethics_change_person: str | None = Field(
        default=None,
        description="Name/title of person granted the waiver, if applicable",
    )
    ethics_change_summary: str | None = Field(
        default=None,
        description="Brief description of the ethics code change, max 300 chars",
    )

    # ------------------------------------------------------------------
    # Item 8.01: Other Events
    # ------------------------------------------------------------------
    event_description: str | None = Field(
        default=None,
        description="Description of other material events, max 300 chars",
    )

    # ------------------------------------------------------------------
    # General
    # ------------------------------------------------------------------
    source_passage: str = Field(
        default="",
        description="Key excerpt from the 8-K, max 300 chars",
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
