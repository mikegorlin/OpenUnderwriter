"""Density assessment models for three-tier section rendering.

Provides DensityLevel (CLEAN/ELEVATED/CRITICAL), SectionDensity with
per-subsection overrides, and PreComputedNarratives for LLM-generated
text pre-computed in BENCHMARK stage.

Phase 35 foundation -- every downstream plan depends on DensityLevel.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class DensityLevel(StrEnum):
    """Three-tier density assessment for section rendering.

    CLEAN: No concerns. Full tables/structure, green signals.
    ELEVATED: Some concerns -- amber indicators, "why this matters" context.
    CRITICAL: Severe issues -- forensic detail, deep dive sub-sections,
              cross-references, visual urgency cues.
    """

    CLEAN = "CLEAN"
    ELEVATED = "ELEVATED"
    CRITICAL = "CRITICAL"


def _default_concerns() -> list[str]:
    """Typed closure for concerns list default factory."""
    return []


def _default_evidence() -> list[str]:
    """Typed closure for critical_evidence list default factory."""
    return []


class SectionDensity(BaseModel):
    """Per-section density assessment with subsection granularity.

    level: Overall section density (worst subsection escalates).
    subsection_overrides: Per-subsection density keyed by subsection ID
        (e.g., "4.1_people_risk": CRITICAL).
    concerns: Specific concerns driving ELEVATED density (amber indicators).
    critical_evidence: Evidence chains driving CRITICAL density (deep dives).
    """

    level: DensityLevel = DensityLevel.CLEAN
    subsection_overrides: dict[str, DensityLevel] = Field(
        default_factory=dict,
        description=(
            "Per-subsection density overrides keyed by subsection ID "
            "(e.g., '4.1_people_risk': 'CRITICAL')"
        ),
    )
    concerns: list[str] = Field(
        default_factory=_default_concerns,
        description="Specific concerns driving ELEVATED density",
    )
    critical_evidence: list[str] = Field(
        default_factory=_default_evidence,
        description="Evidence chains driving CRITICAL density (deep dives)",
    )


def _default_meeting_questions() -> list[str]:
    """Typed closure for meeting_prep_questions list default factory."""
    return []


def _default_hallucination_warnings() -> list[str]:
    """Typed closure for hallucination_warnings list default factory."""
    return []


class SectionCommentary(BaseModel):
    """Dual-voice commentary for a single worksheet section.

    what_was_said: Factual summary of what the company disclosed.
    underwriting_commentary: D&O risk interpretation from underwriting perspective.
    confidence: HIGH/MEDIUM/LOW confidence in the commentary quality.
    hallucination_warnings: Any warnings about potential hallucination.
    """

    what_was_said: str = ""
    underwriting_commentary: str = ""
    confidence: str = "MEDIUM"
    hallucination_warnings: list[str] = Field(
        default_factory=_default_hallucination_warnings,
    )


class PreComputedCommentary(BaseModel):
    """Dual-voice commentary pre-computed for all worksheet sections.

    Each field corresponds to a major worksheet section. None means
    commentary was not generated for that section.
    """

    executive_brief: SectionCommentary | None = None
    financial: SectionCommentary | None = None
    market: SectionCommentary | None = None
    governance: SectionCommentary | None = None
    litigation: SectionCommentary | None = None
    scoring: SectionCommentary | None = None
    company: SectionCommentary | None = None
    meeting_prep: SectionCommentary | None = None


class PreComputedNarratives(BaseModel):
    """LLM-generated narratives pre-computed in BENCHMARK stage.

    RENDER reads these directly -- no narrative generation in RENDER.
    Each field corresponds to a major worksheet section.
    """

    executive_summary: str | None = None
    company: str | None = None
    financial: str | None = None
    market: str | None = None
    governance: str | None = None
    litigation: str | None = None
    scoring: str | None = None
    ai_risk: str | None = None
    meeting_prep_questions: list[str] = Field(
        default_factory=_default_meeting_questions,
        description="LLM-generated meeting prep questions tied to findings",
    )

    @field_validator("meeting_prep_questions", mode="before")
    @classmethod
    def _coerce_questions_to_strings(cls, v: list[object]) -> list[str]:
        """Coerce dict items to strings for LLM responses that return dicts.

        The LLM sometimes returns ``[{"question": "...", "trigger": "..."}]``
        instead of ``["..."]``.  Extract the ``question`` key when present;
        otherwise fall back to ``str()``.
        """
        if not isinstance(v, list):
            return v  # type: ignore[return-value]  # let Pydantic handle
        out: list[str] = []
        for item in v:
            if isinstance(item, dict):
                # Prefer 'question' key; fall back to first string value
                if "question" in item:
                    out.append(str(item["question"]))
                else:
                    first_str = next(
                        (str(val) for val in item.values() if val),
                        str(item),
                    )
                    out.append(first_str)
            else:
                out.append(str(item))
        return out


# ---------------------------------------------------------------------------
# Phase 130: Dual-voice commentary models
# ---------------------------------------------------------------------------
def _default_hallucination_warnings() -> list[str]:
    """Typed closure for hallucination_warnings list default factory."""
    return []


class SectionCommentary(BaseModel):
    """Dual-voice commentary for a single worksheet section.

    what_was_said: Factual data summary -- numbers, dates, names only.
    underwriting_commentary: D&O risk interpretation with SCA theory refs.
    confidence: HIGH/MEDIUM/LOW based on signal evaluation coverage.
    hallucination_warnings: Warnings from validate_narrative_amounts().
    """

    what_was_said: str = Field(
        default="",
        description="Factual data summary -- numbers, dates, names only",
    )
    underwriting_commentary: str = Field(
        default="",
        description="D&O risk interpretation with SCA litigation theory refs",
    )
    confidence: str = Field(
        default="MEDIUM",
        description="HIGH/MEDIUM/LOW based on signal evaluation coverage",
    )
    hallucination_warnings: list[str] = Field(
        default_factory=_default_hallucination_warnings,
        description="Warnings from validate_narrative_amounts()",
    )


class PreComputedCommentary(BaseModel):
    """LLM-generated dual-voice commentary pre-computed in BENCHMARK.

    Each field corresponds to one of the 8 analytical sections that
    receive dual-voice treatment. RENDER reads these directly.
    """

    executive_brief: SectionCommentary | None = None
    financial: SectionCommentary | None = None
    market: SectionCommentary | None = None
    governance: SectionCommentary | None = None
    litigation: SectionCommentary | None = None
    scoring: SectionCommentary | None = None
    company: SectionCommentary | None = None
    meeting_prep: SectionCommentary | None = None
