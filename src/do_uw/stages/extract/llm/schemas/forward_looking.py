"""Forward-looking statement extraction schema.

Pydantic models for LLM extraction of forward-looking statements,
guidance changes, and catalyst events from 10-K and 8-K filings.
Follows the same patterns as ten_k.py: optional fields with defaults,
BeforeValidator coercions for LLM output resilience.

Phase 117: Forward-Looking Risk Framework
"""

from __future__ import annotations

import re
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, Field


def _coerce_currency_float(v: Any) -> Any:
    """Strip currency symbols/commas so '$70.0' or '1,234.5' -> float."""
    if isinstance(v, str):
        cleaned = re.sub(r"[^\d.\-]", "", v)
        if cleaned:
            return float(cleaned)
        return None
    return v


CurrencyFloat = Annotated[float | None, BeforeValidator(_coerce_currency_float)]


class ExtractedForwardStatement(BaseModel):
    """Single forward-looking statement extracted from a filing.

    Captures both quantitative guidance (specific numeric targets)
    and qualitative forward claims (growth expectations, market plans).
    """

    metric: str = Field(
        default="",
        description="The metric being guided (revenue, EPS, margin, growth rate, etc.)",
    )
    target_value: str = Field(
        default="",
        description="Guided value or range (e.g., '$4.50-$4.70 EPS', '15-17% growth')",
    )
    target_numeric_low: CurrencyFloat = Field(
        default=None,
        description="Low end of guidance range (numeric)",
    )
    target_numeric_high: CurrencyFloat = Field(
        default=None,
        description="High end of guidance range (numeric)",
    )
    timeframe: str = Field(
        default="",
        description="When (FY2026, Q2 2026, next 12 months)",
    )
    context: str = Field(
        default="",
        description="Surrounding context from filing (max 300 chars)",
    )
    is_quantitative: bool = Field(
        default=False,
        description="True if specific numbers provided",
    )
    filing_section: str = Field(
        default="",
        description="Where found: MD&A, Risk Factors, Outlook, etc.",
    )


class ExtractedGuidanceChange(BaseModel):
    """A change in previously issued guidance.

    Tracks raises, cuts, withdrawals, and reaffirmations.
    """

    change_type: str = Field(
        default="",
        description="RAISE, CUT, WITHDRAW, REAFFIRM",
    )
    metric: str = Field(
        default="",
        description="Metric affected",
    )
    prior_value: str = Field(
        default="",
        description="Previous guidance",
    )
    new_value: str = Field(
        default="",
        description="Updated guidance",
    )
    date: str = Field(
        default="",
        description="Date of change (YYYY-MM-DD)",
    )


class ExtractedCatalyst(BaseModel):
    """A forward catalyst event mentioned in filings.

    Events that could materially affect company value and
    create D&O exposure if outcome is negative.
    """

    event: str = Field(
        default="",
        description="The catalyst event",
    )
    expected_timing: str = Field(
        default="",
        description="When expected",
    )
    potential_impact: str = Field(
        default="",
        description="Impact if negative",
    )
    mentioned_in: str = Field(
        default="",
        description="Filing section where mentioned",
    )


class ForwardLookingExtraction(BaseModel):
    """Complete forward-looking extraction from a single filing.

    Aggregates all forward statements, guidance changes, and catalysts
    found in one 10-K or 8-K filing. One model per filing, one API call.
    """

    forward_statements: list[ExtractedForwardStatement] = Field(
        default_factory=list,
        description="All forward-looking statements found in filing",
    )
    guidance_changes: list[ExtractedGuidanceChange] = Field(
        default_factory=list,
        description="Any changes to previously issued guidance",
    )
    catalyst_events: list[ExtractedCatalyst] = Field(
        default_factory=list,
        description="Forward catalyst events mentioned in filing",
    )
    provides_numeric_guidance: bool = Field(
        default=False,
        description="True if company provides explicit numeric guidance",
    )
    guidance_summary: str = Field(
        default="",
        description="1-2 sentence summary of forward outlook",
    )
