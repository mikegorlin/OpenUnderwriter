"""Capital filing extraction schema for S-3, S-1, and 424B filings.

Covers shelf registration statements (S-3), full registration
statements (S-1/IPO), and prospectus supplements (424B). These
filings are relevant for D&O underwriting because securities
offerings create Section 11/12 liability windows.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CapitalFilingExtraction(BaseModel):
    """Extraction schema for S-3, S-1, and 424B capital market filings.

    One model covers all capital filing types since they share the same
    core structure: offering details, use of proceeds, risk factors,
    and underwriter information. All fields optional with defaults.
    """

    # ------------------------------------------------------------------
    # Offering details
    # ------------------------------------------------------------------
    offering_type: str | None = Field(
        default=None,
        description=(
            "Type of offering: IPO, Secondary, Shelf Registration, "
            "ATM (at-the-market), Follow-on, PIPE"
        ),
    )
    securities_type: str | None = Field(
        default=None,
        description=(
            "Type of securities offered: Common Stock, Preferred Stock, "
            "Debt Securities, Convertible Notes, Warrants, Units"
        ),
    )
    offering_amount: float | None = Field(
        default=None,
        description="Total offering amount in USD (aggregate)",
    )
    share_count: int | None = Field(
        default=None,
        description="Number of shares being offered",
    )
    price_per_share: float | None = Field(
        default=None,
        description="Price per share or unit in USD",
    )

    # ------------------------------------------------------------------
    # Underwriters
    # ------------------------------------------------------------------
    underwriters: list[str] = Field(
        default_factory=lambda: [],
        description=(
            "Names of underwriters or placement agents, "
            "e.g. ['Goldman Sachs', 'Morgan Stanley', 'J.P. Morgan']"
        ),
    )

    # ------------------------------------------------------------------
    # Dilution and proceeds
    # ------------------------------------------------------------------
    dilution_pct: float | None = Field(
        default=None,
        description=(
            "Dilution percentage to existing shareholders "
            "from the offering"
        ),
    )
    use_of_proceeds: str | None = Field(
        default=None,
        description=(
            "Stated use of proceeds, e.g. 'General corporate purposes "
            "and working capital' or 'Repay outstanding debt'"
        ),
    )

    # ------------------------------------------------------------------
    # Risk factors
    # ------------------------------------------------------------------
    risk_factors_count: int | None = Field(
        default=None,
        description="Number of risk factors disclosed in the filing",
    )

    # ------------------------------------------------------------------
    # General
    # ------------------------------------------------------------------
    source_passage: str = Field(
        default="",
        description="Key excerpt from the filing, max 300 chars",
    )
