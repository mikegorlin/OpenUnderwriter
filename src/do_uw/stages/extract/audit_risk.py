"""Audit risk profile extraction from 10-K filings.

Extracts auditor identity, tenure, opinion type, going concern warnings,
material weaknesses, restatements, late filings, SEC comment letters,
and critical audit matters (CAMs) from 10-K text and XBRL data.

Covers SECT3-12 (audit risk) for D&O underwriting.

Usage:
    audit_profile, report = extract_audit_risk(state)
    state.extracted.financials.audit = audit_profile
"""

from __future__ import annotations

import logging
from typing import Any, cast

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.financials import AuditProfile
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.audit_risk_helpers import (
    check_late_filing,
    count_comment_letters,
    extract_auditor_name,
    extract_cams,
    extract_going_concern,
    extract_material_weaknesses,
    extract_opinion_type,
    extract_restatements,
    extract_tenure,
)
from do_uw.stages.extract.sourced import (
    get_company_facts,
    get_filing_texts,
    get_filings,
    now,
    sourced_str,
)
from do_uw.stages.extract.validation import (
    ExtractionReport,
    create_report,
    log_report,
)

logger = logging.getLogger(__name__)

# Expected fields for the extraction report.
EXPECTED_FIELDS: list[str] = [
    "auditor_name",
    "is_big4",
    "tenure_years",
    "opinion_type",
    "going_concern",
    "material_weaknesses",
    "restatements",
    "late_filings",
    "comment_letters",
    "critical_audit_matters",
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _count_amendment_filings(state: AnalysisState) -> tuple[int, int]:
    """Count 10-K/A and 10-Q/A filings from SEC filing history.

    Returns:
        Tuple of (10-K/A count, 10-Q/A count).
    """
    if state.acquired_data is None:
        return 0, 0

    count_10k_a = 0
    count_10q_a = 0

    # Check filings dict for amendment filing types
    for form_type in ("10-K/A", "10-KSB/A"):
        filings = state.acquired_data.filings.get(form_type, [])
        count_10k_a += len(filings)

    for form_type in ("10-Q/A", "10-QSB/A"):
        filings = state.acquired_data.filings.get(form_type, [])
        count_10q_a += len(filings)

    # Also check filing_documents for downloaded amendment text
    for form_type in ("10-K/A", "10-KSB/A"):
        docs = state.acquired_data.filing_documents.get(form_type, [])
        if docs and count_10k_a == 0:
            count_10k_a = len(docs)

    for form_type in ("10-Q/A", "10-QSB/A"):
        docs = state.acquired_data.filing_documents.get(form_type, [])
        if docs and count_10q_a == 0:
            count_10q_a = len(docs)

    if count_10k_a > 0:
        logger.warning(
            "RESTATEMENT ALERT: %d 10-K/A amendment filing(s) detected",
            count_10k_a,
        )
    if count_10q_a > 0:
        logger.info(
            "Amendment detected: %d 10-Q/A filing(s)", count_10q_a,
        )

    return count_10k_a, count_10q_a


def _get_filing_text_combined(state: AnalysisState) -> str:
    """Get combined filing text from all available 10-K sections."""
    filings = get_filings(state)
    texts = get_filing_texts(filings)
    parts: list[str] = []
    for key in ("10-K_item8", "item8", "10-K_item9a", "item9a",
                "10-K_item1", "item1", "10-K_item7", "item7"):
        val = str(texts.get(key, ""))
        if val.strip():
            parts.append(val)
    return " ".join(parts)


def _get_auditor_report_text(state: AnalysisState) -> str:
    """Get the auditor report section (Item 8 or full filing)."""
    filings = get_filings(state)
    texts = get_filing_texts(filings)
    # Auditor report is typically in Item 8.
    for key in ("10-K_item8", "item8"):
        val = str(texts.get(key, ""))
        if val.strip():
            return val
    # Fall back to all text.
    return _get_filing_text_combined(state)


# ---------------------------------------------------------------------------
# LLM enrichment
# ---------------------------------------------------------------------------


def _enrich_from_llm(
    state: AnalysisState, profile: AuditProfile,
) -> None:
    """Enrich audit risk with LLM-extracted Item 9A controls data.

    Strategy:
    - XBRL going concern and opinion type are NEVER overridden by LLM
    - Material weakness detail: LLM replaces (richer than regex)
    - Significant deficiencies: LLM fills (not available from regex)
    - Remediation status: LLM fills (not available from regex)
    - Auditor name/tenure: LLM supplements only when regex is empty
    """
    from do_uw.stages.extract.llm_helpers import get_llm_ten_k

    llm_ten_k = get_llm_ten_k(state)
    if llm_ten_k is None:
        return

    from do_uw.stages.extract.ten_k_converters import convert_controls_assessment

    controls: dict[str, Any] = convert_controls_assessment(llm_ten_k)

    # Material weakness detail: LLM provides richer descriptions.
    # Filter out auditor methodology boilerplate even from LLM output.
    from do_uw.stages.extract.audit_risk_helpers import (
        _is_auditor_methodology_boilerplate,
    )

    mw_detail = cast(
        list[SourcedValue[str]], controls.get("material_weakness_detail", [])
    )
    mw_detail = [
        mw for mw in mw_detail
        if not _is_auditor_methodology_boilerplate(mw.value)
    ]
    if mw_detail and not profile.material_weaknesses:
        # Regex found nothing; use LLM detail
        profile.material_weaknesses.extend(mw_detail)

    # Significant deficiencies: new field not available from regex
    sig_def = cast(
        list[SourcedValue[str]], controls.get("significant_deficiencies", [])
    )
    if sig_def:
        profile.significant_deficiencies.extend(sig_def)

    # Remediation status: new field not available from regex
    rem_status = cast(
        SourcedValue[str] | None, controls.get("remediation_status")
    )
    if rem_status is not None and rem_status.value and profile.remediation_status is None:
        profile.remediation_status = rem_status

    # Auditor name: supplement only when regex/XBRL left empty
    auditor_name_sv = cast(
        SourcedValue[str] | None, controls.get("auditor_name")
    )
    if auditor_name_sv is not None and auditor_name_sv.value and profile.auditor_name is None:
        profile.auditor_name = auditor_name_sv

    # Auditor tenure: supplement only when regex left empty
    tenure_sv = cast(
        SourcedValue[int] | None, controls.get("auditor_tenure_years")
    )
    if tenure_sv is not None and profile.tenure_years is None:
        profile.tenure_years = tenure_sv

    logger.info("SECT3: Enriched audit risk with LLM Item 9A data")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def extract_audit_risk(
    state: AnalysisState,
) -> tuple[AuditProfile, ExtractionReport]:
    """Extract audit risk profile from 10-K filing text and XBRL data.

    Populates AuditProfile with auditor identity, tenure, opinion type,
    going concern, material weaknesses, restatements, late filing status,
    comment letters, and critical audit matters.

    Args:
        state: AnalysisState with acquired_data populated.

    Returns:
        Tuple of (AuditProfile, ExtractionReport).
    """
    profile = AuditProfile()
    found: list[str] = []
    warnings: list[str] = []
    source_filing = "10-K text + XBRL Company Facts"

    facts = get_company_facts(state)
    auditor_text = _get_auditor_report_text(state)
    full_text = _get_filing_text_combined(state)

    if not auditor_text.strip() and not facts:
        warnings.append("No filing text or XBRL data available")
        report = create_report(
            extractor_name="audit_risk",
            expected=EXPECTED_FIELDS,
            found=found,
            source_filing=source_filing,
            warnings=warnings,
        )
        log_report(report)
        return profile, report

    # 1. Auditor identity.
    auditor_name, is_big4 = extract_auditor_name(auditor_text, facts)
    if auditor_name:
        profile.auditor_name = sourced_str(
            auditor_name, "10-K auditor report", Confidence.HIGH,
        )
        found.append("auditor_name")
        profile.is_big4 = SourcedValue[bool](
            value=is_big4, source="10-K auditor report",
            confidence=Confidence.HIGH, as_of=now(),
        )
        found.append("is_big4")

    # 2. Auditor tenure.
    tenure = extract_tenure(auditor_text)
    if tenure is not None:
        profile.tenure_years = SourcedValue[int](
            value=tenure, source="10-K auditor report",
            confidence=Confidence.MEDIUM, as_of=now(),
        )
        found.append("tenure_years")

    # 3. Opinion type.
    opinion = extract_opinion_type(auditor_text)
    if opinion != "unknown":
        profile.opinion_type = sourced_str(
            opinion, "10-K auditor report", Confidence.HIGH,
        )
        found.append("opinion_type")

    # 4. Going concern.
    has_going_concern = extract_going_concern(full_text)
    profile.going_concern = SourcedValue[bool](
        value=has_going_concern,
        source="10-K full text search",
        confidence=Confidence.HIGH,
        as_of=now(),
    )
    found.append("going_concern")

    # 5. Material weaknesses.
    weaknesses = extract_material_weaknesses(full_text)
    for weakness in weaknesses:
        profile.material_weaknesses.append(
            sourced_str(weakness, "10-K Item 9A SOX 404", Confidence.HIGH)
        )
    found.append("material_weaknesses")

    # 6. Restatements.
    restatement_items = extract_restatements(full_text)
    for item in restatement_items:
        profile.restatements.append(
            SourcedValue[dict[str, str]](
                value=item, source="10-K text analysis",
                confidence=Confidence.HIGH, as_of=now(),
            )
        )
    found.append("restatements")

    # 7. Late filings.
    is_late = check_late_filing(state)
    if is_late:
        warnings.append("10-K filed after SEC deadline")
    found.append("late_filings")

    # 8. Comment letters.
    comment_count = count_comment_letters(state)
    if comment_count > 0:
        warnings.append(f"SEC comment letters found: {comment_count}")
    found.append("comment_letters")

    # 9. Critical Audit Matters.
    cams = extract_cams(auditor_text)
    for cam in cams:
        profile.critical_audit_matters.append(
            sourced_str(cam, "10-K PCAOB auditor report", Confidence.HIGH)
        )
    found.append("critical_audit_matters")

    # 10. LLM enrichment (Item 9A controls).
    _enrich_from_llm(state, profile)

    # 11. Amendment filing counts (restatement indicators from SEC filing history).
    profile.amendment_filing_10k_count, profile.amendment_filing_10q_count = (
        _count_amendment_filings(state)
    )
    if profile.amendment_filing_10k_count > 0:
        warnings.append(
            f"10-K/A amendment filings: {profile.amendment_filing_10k_count}"
        )
        found.append("amendment_filing_10k_count")
    if profile.amendment_filing_10q_count > 0:
        found.append("amendment_filing_10q_count")

    report = create_report(
        extractor_name="audit_risk",
        expected=EXPECTED_FIELDS,
        found=found,
        source_filing=source_filing,
        warnings=warnings,
    )
    log_report(report)

    return profile, report
