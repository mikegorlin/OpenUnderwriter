"""SC 13D and SC 13G ownership filing extraction schemas.

Separate schemas for activist (SC 13D) and passive (SC 13G) beneficial
ownership filings. SC 13D filings are particularly important for D&O
underwriting because they signal activist intent to influence management
or the board.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SC13DExtraction(BaseModel):
    """Extraction schema for SC 13D beneficial ownership filings.

    SC 13D is filed when an investor acquires 5%+ of a company's shares
    with the intent to influence management or the board. Critical for
    D&O underwriting as it signals activist pressure.
    """

    # ------------------------------------------------------------------
    # Filer identification
    # ------------------------------------------------------------------
    filer_name: str | None = Field(
        default=None,
        description="Name of the filing person or entity",
    )
    filer_type: str | None = Field(
        default=None,
        description="Type of filer: individual, hedge fund, activist fund, etc.",
    )

    # ------------------------------------------------------------------
    # Ownership details
    # ------------------------------------------------------------------
    shares_owned: int | None = Field(
        default=None,
        description="Total number of shares beneficially owned",
    )
    ownership_pct: float | None = Field(
        default=None,
        description="Percentage of outstanding shares beneficially owned",
    )

    # ------------------------------------------------------------------
    # Activist intent (Items 4 and 7 of SC 13D)
    # ------------------------------------------------------------------
    purpose: str | None = Field(
        default=None,
        description=(
            "Stated purpose of acquisition from Item 4, "
            "e.g. 'To engage with management regarding strategic alternatives'"
        ),
    )
    is_activist: bool | None = Field(
        default=None,
        description=(
            "Whether the filer intends to influence management, board, "
            "or corporate actions (vs. passive investment)"
        ),
    )
    demands: list[str] = Field(
        default_factory=lambda: [],
        description=(
            "Specific activist demands or proposals, "
            "e.g. ['Board representation', 'Strategic review', "
            "'Return capital to shareholders']"
        ),
    )

    # ------------------------------------------------------------------
    # General
    # ------------------------------------------------------------------
    source_passage: str = Field(
        default="",
        description="Key excerpt from the filing, max 300 chars",
    )


class SC13GExtraction(BaseModel):
    """Extraction schema for SC 13G beneficial ownership filings.

    SC 13G is the short-form version filed by passive institutional
    investors who own 5%+ but do not intend to influence the company.
    Less critical than SC 13D for D&O but still relevant for ownership
    concentration analysis.
    """

    # ------------------------------------------------------------------
    # Filer identification
    # ------------------------------------------------------------------
    filer_name: str | None = Field(
        default=None,
        description="Name of the filing person or entity",
    )
    filer_type: str | None = Field(
        default=None,
        description=(
            "Type of filer: institutional investment manager, "
            "qualified institutional buyer, etc."
        ),
    )

    # ------------------------------------------------------------------
    # Ownership details
    # ------------------------------------------------------------------
    shares_owned: int | None = Field(
        default=None,
        description="Total number of shares beneficially owned",
    )
    ownership_pct: float | None = Field(
        default=None,
        description="Percentage of outstanding shares beneficially owned",
    )

    # ------------------------------------------------------------------
    # Passive status
    # ------------------------------------------------------------------
    is_passive: bool = Field(
        default=True,
        description="Whether the investment is passive (should be True for 13G)",
    )

    # ------------------------------------------------------------------
    # General
    # ------------------------------------------------------------------
    source_passage: str = Field(
        default="",
        description="Key excerpt from the filing, max 300 chars",
    )
