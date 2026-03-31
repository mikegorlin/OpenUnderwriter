"""Governance intelligence models for Phase 135.

Provides typed Pydantic models for:
- Officer background investigation (GOV-01): prior companies, SCA exposures
- Serial defendant detection (GOV-02): flagging officers at prior SCA companies
- Shareholder rights inventory (GOV-03/GOV-04): 8-provision checklist + defense posture
- Per-insider activity detail (GOV-05): aggregated Form 4 data with 10b5-1 status

These models are the data layer consumed by context builders (Plan 02)
and template fragments for the governance intelligence section.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PriorCompany(BaseModel):
    """A prior company extracted from officer bio text (DEF 14A).

    Used for GOV-01 officer background and GOV-02 serial defendant
    cross-referencing against Supabase SCA database.
    """

    model_config = ConfigDict(frozen=False)

    company_name: str = ""
    role: str = ""
    years: str = ""  # e.g., "2015-2020"
    start_year: int | None = None
    end_year: int | None = None


class OfficerSCAExposure(BaseModel):
    """An SCA case at a prior company during officer's tenure (GOV-02).

    Created when date_ranges_overlap confirms the officer was at
    a company during an active SCA class period.
    """

    model_config = ConfigDict(frozen=False)

    company_name: str = ""
    case_caption: str = ""
    filing_date: str = ""
    class_period_start: str = ""
    class_period_end: str = ""
    officer_role_at_time: str = ""
    settlement_amount_m: float | None = None


class OfficerBackground(BaseModel):
    """Per-officer investigative background for GOV-01.

    Aggregates prior company history, SCA cross-references, personal
    litigation, and a data completeness suitability indicator.
    Suitability is NOT a judgment on the person -- it indicates how
    much data we were able to gather (HIGH/MEDIUM/LOW).
    """

    model_config = ConfigDict(frozen=False)

    name: str = ""
    title: str = ""
    prior_companies: list[PriorCompany] = Field(default_factory=list)
    sca_exposures: list[OfficerSCAExposure] = Field(default_factory=list)
    is_serial_defendant: bool = False
    personal_litigation: list[str] = Field(default_factory=list)
    suitability: str = "LOW"  # HIGH/MEDIUM/LOW data completeness
    suitability_reason: str = ""


class ShareholderRightsProvision(BaseModel):
    """Single shareholder rights provision for GOV-03 checklist.

    Represents one of 8 governance provisions with its status,
    defense classification, and D&O implication text.
    """

    model_config = ConfigDict(frozen=False)

    provision_name: str = ""
    status: str = ""  # Yes / No / N/A
    details: str = ""
    defense_strength: str = ""  # Protective / Shareholder-Friendly / Neutral
    do_implication: str = ""


class ShareholderRightsInventory(BaseModel):
    """Full 8-provision shareholder rights inventory for GOV-03/GOV-04.

    Aggregates individual provisions into an overall defense posture
    assessment (Strong/Moderate/Weak) based on protective vs
    shareholder-friendly provision counts.
    """

    model_config = ConfigDict(frozen=False)

    provisions: list[ShareholderRightsProvision] = Field(default_factory=list)
    overall_defense_posture: str = ""  # Strong / Moderate / Weak
    protective_count: int = 0
    shareholder_friendly_count: int = 0


class PerInsiderActivity(BaseModel):
    """Per-insider aggregated trading activity for GOV-05.

    Groups InsiderTransaction records by insider name with totals,
    10b5-1 plan status, and activity period. Sorted by total_sold_usd
    descending in display.
    """

    model_config = ConfigDict(frozen=False)

    name: str = ""
    position: str = ""
    total_sold_usd: float = 0.0
    total_sold_pct_os: float | None = None
    tx_count: int = 0
    has_10b5_1: bool = False
    activity_period_start: str = ""
    activity_period_end: str = ""
