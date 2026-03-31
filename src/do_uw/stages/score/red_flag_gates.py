"""CRF red flag gate evaluation for D&O underwriting.

Evaluates 11 Critical Red Flag (CRF) gates against extracted data.
Each triggered gate imposes a quality score CEILING.

CRF gates are evaluated BEFORE factor scoring per processing_rules
in red_flags.json: "Check ALL triggers BEFORE calculating factor scores".

CRF ID normalization: red_flags.json uses CRF-01 format;
scoring.json uses CRF-001 format. Both are normalized via
_normalize_crf_id() for comparison.
"""

from __future__ import annotations

import logging
import re
from datetime import date
from typing import Any

from do_uw.models.company import CompanyProfile
from do_uw.models.scoring import RedFlagResult
from do_uw.models.state import AnalysisState, ExtractedData

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------


def should_suppress_insolvency(state: AnalysisState) -> bool:
    """Single source of truth for CRF insolvency suppression.

    Suppresses insolvency CRF when company shows no distress signals:
    - Altman Z-Score > 3.0 (safe zone)
    - Current ratio > 0.5
    - No going concern opinion

    Consolidates logic from crf_bar_context.py, assembly_registry.py,
    scoring.py, and sect1_executive_tables.py.

    Returns True if insolvency CRF should be SUPPRESSED (company is healthy).
    Returns False if insolvency CRF should be SHOWN (company may be at risk).
    """
    extracted = getattr(state, "extracted", None)
    if extracted is None:
        return False
    financials = getattr(extracted, "financials", None)
    if financials is None:
        return False

    # Never suppress if going concern opinion exists
    audit = getattr(financials, "audit", None)
    if audit is not None:
        gc = getattr(audit, "going_concern", None)
        if gc is not None:
            gc_val = gc.value if hasattr(gc, "value") else gc
            if gc_val is True:
                return False

    # Extract Altman Z-Score
    altman_z: float | None = None
    distress = getattr(financials, "distress", None)
    if distress is not None:
        az = getattr(distress, "altman_z_score", None)
        if az is not None:
            score_val = getattr(az, "score", None)
            if score_val is not None:
                raw = getattr(score_val, "value", score_val)
                try:
                    altman_z = float(raw)
                except (TypeError, ValueError):
                    pass

    # Extract current ratio from liquidity
    current_ratio: float | None = None
    liq = getattr(financials, "liquidity", None)
    if liq is not None:
        liq_val = liq.value if hasattr(liq, "value") else liq
        if isinstance(liq_val, dict):
            cr = liq_val.get("current_ratio")
            if cr is not None:
                try:
                    current_ratio = float(cr)
                except (TypeError, ValueError):
                    pass

    # Suppress only when BOTH metrics indicate health
    if (
        altman_z is not None
        and altman_z > 3.0
        and current_ratio is not None
        and current_ratio > 0.5
    ):
        return True

    return False


def evaluate_red_flag_gates(
    red_flags_config: dict[str, Any],
    scoring_config: dict[str, Any],
    extracted: ExtractedData,
    company: CompanyProfile | None,
    analysis_results: dict[str, Any] | None = None,
) -> list[RedFlagResult]:
    """Evaluate all CRF gates (CRF-1 through CRF-17) against data.

    Args:
        red_flags_config: Parsed red_flags.json
        scoring_config: Parsed scoring.json (for ceiling values)
        extracted: Current extracted data
        company: Company profile (for SPAC price check)
        analysis_results: Optional analysis results for Phase 26 gates

    Returns:
        List of RedFlagResult for each CRF trigger.
    """
    from do_uw.stages.score.red_flag_gates_enhanced import (
        evaluate_phase26_trigger,
    )

    triggers = red_flags_config.get("escalation_triggers", [])
    ceilings_list = (
        scoring_config.get("critical_red_flag_ceilings", {}).get("ceilings", [])
    )

    # Build ceiling lookup by normalized CRF ID
    ceiling_map: dict[str, dict[str, Any]] = {}
    for ceiling in ceilings_list:
        crf_id = _normalize_crf_id(str(ceiling.get("id", "")))
        ceiling_map[crf_id] = ceiling

    results: list[RedFlagResult] = []
    for trigger in triggers:
        raw_id = str(trigger.get("id", ""))
        norm_id = _normalize_crf_id(raw_id)
        flag_name = str(trigger.get("name", ""))
        num = int(norm_id.split("-")[1]) if "-" in norm_id else 0

        # CRF-1 through CRF-11: original gates
        # CRF-12 through CRF-17: Phase 26 gates
        if num >= 12:
            fired, evidence = evaluate_phase26_trigger(
                norm_id, extracted, analysis_results,
            )
        else:
            fired, evidence = _evaluate_trigger(norm_id, extracted, company)

        # Look up ceiling from scoring.json or trigger config
        ceiling_entry = ceiling_map.get(norm_id, {})
        ceiling_score = int(
            ceiling_entry.get(
                "max_quality_score",
                trigger.get("max_quality_score", 100),
            )
        )
        max_tier = str(
            ceiling_entry.get("max_tier", trigger.get("max_tier", ""))
        )

        result = RedFlagResult(
            flag_id=norm_id,
            flag_name=flag_name,
            triggered=fired,
            ceiling_applied=ceiling_score if fired else None,
            max_tier=max_tier if fired else None,
            evidence=evidence,
        )
        results.append(result)

        if fired:
            logger.info(
                "CRF %s (%s) triggered: ceiling=%d, max_tier=%s",
                norm_id,
                flag_name,
                ceiling_score,
                max_tier,
            )

    return results


def _resolve_crf_ceiling(
    crf_entry: dict[str, Any],
    market_cap: float | None,
    analysis_results: dict[str, Any] | None = None,
) -> tuple[int, str]:
    """Resolve CRF ceiling using size-severity matrix or distress graduation.

    Priority:
    1. distress_graduation (CRF-13): graduated by Altman Z severity
    2. size_severity_matrix: graduated by company market cap
    3. Flat max_quality_score fallback

    Args:
        crf_entry: CRF ceiling config dict from scoring.json
        market_cap: Company market cap in USD, or None
        analysis_results: Optional dict with altman_z_score, going_concern, negative_equity

    Returns:
        (ceiling_score, max_tier)
    """
    flat_ceiling = int(crf_entry.get("max_quality_score", 100))
    flat_tier = str(crf_entry.get("max_tier", ""))

    # Check for distress graduation (CRF-13)
    graduation = crf_entry.get("distress_graduation")
    if graduation is not None:
        ar = analysis_results or {}
        # Going concern is most severe
        if ar.get("going_concern"):
            gc = graduation.get("going_concern", {})
            return int(gc.get("ceiling", flat_ceiling)), str(gc.get("max_tier", flat_tier))
        z_score = ar.get("altman_z_score")
        neg_eq = ar.get("negative_equity", False)
        if z_score is not None:
            # Severe: z < 1.0 with negative equity
            severe = graduation.get("severe", {})
            if z_score <= float(severe.get("z_max", 1.0)) and neg_eq:
                return int(severe.get("ceiling", flat_ceiling)), str(severe.get("max_tier", flat_tier))
            # Distress: z < 1.81
            distress = graduation.get("distress", {})
            if z_score <= float(distress.get("z_max", 1.81)):
                return int(distress.get("ceiling", flat_ceiling)), str(distress.get("max_tier", flat_tier))
            # Gray zone: z < 2.99
            gray = graduation.get("gray", {})
            if z_score <= float(gray.get("z_max", 2.99)):
                return int(gray.get("ceiling", flat_ceiling)), str(gray.get("max_tier", flat_tier))
        return flat_ceiling, flat_tier

    # Check for size-severity matrix
    matrix = crf_entry.get("size_severity_matrix")
    if matrix is None or market_cap is None:
        return flat_ceiling, flat_tier

    # Walk tiers from largest to smallest threshold
    for tier_name in ("mega_cap", "large_cap", "mid_cap", "small_cap", "micro_cap"):
        tier = matrix.get(tier_name)
        if tier is None:
            continue
        if market_cap >= float(tier["threshold_usd"]):
            return int(tier["ceiling"]), str(tier.get("max_tier", flat_tier))

    return flat_ceiling, flat_tier


# Compounding factor: each additional CRF's severity_weight is multiplied by this
_COMPOUNDING_FACTOR = 0.5
# Maximum total reduction from compounding (80% of primary ceiling)
_MAX_COMPOUNDING_REDUCTION = 0.80
# Absolute floor: compounded ceiling never goes below this
_COMPOUNDING_FLOOR = 5


def apply_crf_ceilings(
    composite_score: float,
    red_flag_results: list[RedFlagResult],
    scoring_config: dict[str, Any] | None = None,
    market_cap: float | None = None,
    analysis_results: dict[str, Any] | None = None,
) -> tuple[float, str | None] | tuple[float, str | None, list[dict[str, Any]]]:
    """Apply CRF ceilings to composite score with optional weighted compounding.

    When scoring_config is provided, uses size-conditioned ceilings and
    weighted compounding for multiple CRFs. When scoring_config is None,
    falls back to legacy "lowest ceiling wins" behavior.

    Returns:
        Without scoring_config: (quality_score, binding_ceiling_id)
        With scoring_config: (quality_score, binding_ceiling_id, ceiling_details)
    """
    # Legacy path: no config, use simple "lowest ceiling wins"
    if scoring_config is None:
        lowest_ceiling = float("inf")
        binding_id: str | None = None
        for result in red_flag_results:
            if result.triggered and result.ceiling_applied is not None:
                if result.ceiling_applied < lowest_ceiling:
                    lowest_ceiling = float(result.ceiling_applied)
                    binding_id = result.flag_id
        if lowest_ceiling < float("inf"):
            return min(composite_score, lowest_ceiling), binding_id
        return composite_score, None

    # New path: size-conditioned + weighted compounding
    ceilings_cfg = scoring_config.get("critical_red_flag_ceilings", {}).get("ceilings", [])
    ceiling_lookup: dict[str, dict[str, Any]] = {}
    for c in ceilings_cfg:
        norm = _normalize_crf_id(str(c.get("id", "")))
        ceiling_lookup[norm] = c

    # Resolve ceiling for each triggered CRF
    triggered: list[tuple[str, int, float]] = []  # (crf_id, resolved_ceiling, weight)
    details: list[dict[str, Any]] = []

    for result in red_flag_results:
        if not result.triggered or result.flag_id is None:
            continue
        norm_id = _normalize_crf_id(result.flag_id)
        cfg = ceiling_lookup.get(norm_id, {})
        ceiling, tier = _resolve_crf_ceiling(cfg, market_cap, analysis_results)
        weight = float(cfg.get("severity_weight", 0.15))  # default weight for unlisted CRFs
        triggered.append((norm_id, ceiling, weight))
        details.append({
            "crf_id": norm_id,
            "resolved_ceiling": ceiling,
            "resolved_tier": tier,
            "severity_weight": weight,
        })

    if not triggered:
        return composite_score, None, []

    # Sort by ceiling ascending (most severe first)
    triggered.sort(key=lambda t: t[1])

    # Primary ceiling = lowest resolved ceiling
    primary_id, primary_ceiling, _primary_weight = triggered[0]

    # Compound additional CRFs beyond primary
    total_reduction = 0.0
    for _crf_id, _ceiling, weight in triggered[1:]:
        total_reduction += weight * _COMPOUNDING_FACTOR

    # Cap total reduction
    total_reduction = min(total_reduction, _MAX_COMPOUNDING_REDUCTION)

    # Apply compounding
    final_ceiling = max(_COMPOUNDING_FLOOR, primary_ceiling * (1.0 - total_reduction))
    quality_score = min(composite_score, final_ceiling)

    # Annotate details with contribution info
    for i, d in enumerate(details):
        if i == 0:
            d["role"] = "primary" if d["crf_id"] == primary_id else "additional"
        d["role"] = d.get("role", "additional")
        d["contribution"] = d["severity_weight"] * _COMPOUNDING_FACTOR if d["role"] == "additional" else 0.0

    logger.info(
        "CRF ceilings: primary=%s ceiling=%d, %d additional, "
        "reduction=%.2f, final_ceiling=%.1f, quality=%.1f",
        primary_id, primary_ceiling, len(triggered) - 1,
        total_reduction, final_ceiling, quality_score,
    )

    return quality_score, primary_id, details


# -----------------------------------------------------------------------
# CRF ID normalization
# -----------------------------------------------------------------------


def _normalize_crf_id(raw_id: str) -> str:
    """Normalize CRF ID to consistent format.

    Handles both CRF-01 (red_flags.json) and CRF-001 (scoring.json).
    Normalizes to CRF-XX format (strips leading zeros from numeric part).

    Examples:
        CRF-001 -> CRF-1
        CRF-01  -> CRF-1
        CRF-11  -> CRF-11
        CRF-011 -> CRF-11
    """
    match = re.match(r"CRF-0*(\d+)", raw_id)
    if match:
        return f"CRF-{match.group(1)}"
    return raw_id


# -----------------------------------------------------------------------
# Per-trigger evaluation
# -----------------------------------------------------------------------


def _evaluate_trigger(
    crf_id: str,
    extracted: ExtractedData,
    company: CompanyProfile | None,
) -> tuple[bool, list[str]]:
    """Evaluate a single CRF trigger condition.

    Returns:
        (triggered: bool, evidence: list[str])
    """
    if crf_id == "CRF-1":
        return _check_active_sca(extracted)
    if crf_id == "CRF-2":
        return _check_wells_notice(extracted)
    if crf_id == "CRF-3":
        return _check_doj_investigation(extracted)
    if crf_id == "CRF-4":
        return _check_going_concern(extracted)
    if crf_id == "CRF-5":
        return _check_recent_restatement(extracted)
    if crf_id == "CRF-6":
        return _check_spac_under_5(extracted, company)
    if crf_id == "CRF-7":
        return _check_short_seller_report(extracted)
    if crf_id == "CRF-8":
        return _check_catastrophic_decline(extracted)
    if crf_id == "CRF-9":
        return _check_drop_7d(extracted)
    if crf_id == "CRF-10":
        return _check_drop_30d(extracted)
    if crf_id == "CRF-11":
        return _check_drop_90d(extracted)
    return False, []


def _check_active_sca(extracted: ExtractedData) -> tuple[bool, list[str]]:
    """CRF-1: Active securities class action."""
    lit = extracted.litigation
    if lit is None:
        return False, []
    for sca in lit.securities_class_actions:
        if sca.status is not None and sca.status.value.upper() == "ACTIVE":
            # Skip regulatory proceedings misclassified as SCAs
            if _is_regulatory_not_sca(sca):
                continue
            # Skip cases that lack all case specifics (boilerplate)
            if not _has_case_specificity(sca):
                logger.info("CRF-1: skipping non-specific case: %s",
                            getattr(sca.case_name, "value", ""))
                continue
            name = ""
            if sca.case_name is not None:
                name = sca.case_name.value
            # Check corroboration status
            corroborated = getattr(sca, "corroborated", None)
            if corroborated is False:
                return True, [f"Active SCA (unverified): {name}"]
            return True, [f"Active SCA: {name}"]
    return False, []


def _has_case_specificity(sca: Any) -> bool:
    """Check if case has at least one specific detail.

    Returns True if case has ANY of: named plaintiff (' v. ' / ' vs. '),
    court/jurisdiction, case number pattern, or specific filing date.
    Cases failing ALL checks are treated as boilerplate.
    """
    # Named plaintiff (case name contains " v. " or " vs. ")
    cn = getattr(sca, "case_name", None)
    if cn is not None:
        name = cn.value if hasattr(cn, "value") else str(cn)
        name_upper = name.upper()
        if " V. " in name_upper or " VS. " in name_upper or "IN RE " in name_upper:
            return True

    # Court or jurisdiction
    court = getattr(sca, "court", None)
    if court is not None:
        court_val = court.value if hasattr(court, "value") else str(court)
        if court_val and court_val.strip():
            return True

    # Case number pattern (e.g. "1:24-cv-01234")
    case_num = getattr(sca, "case_number", None)
    if case_num is not None:
        num_val = case_num.value if hasattr(case_num, "value") else str(case_num)
        if num_val and re.search(r"\d+[:\-].*\d+", num_val):
            return True

    # Specific filing date (not None, not year-only)
    fd = getattr(sca, "filing_date", None)
    if fd is not None:
        fd_val = fd.value if hasattr(fd, "value") else fd
        if fd_val is not None:
            return True

    return False


def _is_regulatory_not_sca(sca: Any) -> bool:
    """Check if an SCA entry is NOT actually a securities class action.

    The LLM extractor places ALL Item 3 legal proceedings into the
    securities_class_actions list. Many are environmental, employment,
    product liability, or regulatory cases that should NOT trigger
    CRF-1 (Active SCA). A real SCA must have securities-related
    legal theories (10b-5, Section 11, Section 14a) or explicit
    securities/class-action indicators in the case name/allegations.
    """
    from do_uw.stages.analyze.signal_mappers_ext import _is_boilerplate_litigation

    # 1. Check coverage_type for REGULATORY
    ct = getattr(sca, "coverage_type", None)
    if ct is not None:
        ct_val = ct.value.upper() if hasattr(ct, "value") else str(ct).upper()
        if "REGULATORY" in ct_val:
            return True

    # 2. Check for boilerplate case names
    cn = getattr(sca, "case_name", None)
    if cn is not None:
        name = cn.value if hasattr(cn, "value") else str(cn)
        if _is_boilerplate_litigation(name.upper()):
            return True

    # 3. Check if case lacks securities theories — the definitive test.
    # A real SCA must have at least one securities-related legal theory.
    # If it only has non-securities theories (ENVIRONMENTAL, ANTITRUST,
    # PRODUCT_LIABILITY, etc.), it's not an SCA regardless of coverage_type.
    if not _has_securities_indicators(sca):
        return True

    return False


# Securities theories that indicate a genuine SCA
_SECURITIES_THEORIES = {
    "RULE_10B5", "SECTION_11", "SECTION_14A",
    "10B-5", "10B5", "SECURITIES_FRAUD",
}

# Keywords in case name/allegations that indicate securities litigation.
# "CLASS ACTION" alone is too broad — merchant/antitrust class actions
# (e.g. Visa interchange MDL) are not securities litigation.
_SECURITIES_CASE_KEYWORDS = (
    "SECURITIES", "SHAREHOLDER CLASS",
    "10B-5", "10(B)", "SECTION 11", "SECTION 14",
    "SECURITIES FRAUD", "STOCK FRAUD",
    "SECURITIES CLASS ACTION",
    "IN RE ", "SEC. LIT.", "SECURITIES LITIGATION",
)

# Phrases that indicate a class action is NOT securities-related
_NON_SECURITIES_CLASS_KEYWORDS = (
    "INTERCHANGE", "MERCHANT", "ANTITRUST", "PRICE-FIXING",
    "PRICE FIXING", "MDL", "CONSUMER CLASS", "PATENT",
    "COVERED LITIGATION",
)

# Non-securities theories — cases with ONLY these are not SCAs
_NON_SECURITIES_THEORIES = {
    "ENVIRONMENTAL", "PRODUCT_LIABILITY", "EMPLOYMENT_DISCRIMINATION",
    "WHISTLEBLOWER", "ANTITRUST", "FCPA", "CYBER_PRIVACY",
    "DERIVATIVE_DUTY", "ERISA",
}


def _has_securities_indicators(sca: Any) -> bool:
    """Check if case has any securities-related indicators.

    Returns True only if case has securities legal theories or
    securities keywords in case name/allegations. Returns False
    if the case has non-securities indicators (antitrust, interchange,
    merchant class actions) or COMMERCIAL_ENTITY coverage type without
    any securities-specific keywords.
    """
    # Gather all text for non-securities keyword check
    all_text_parts: list[str] = []
    cn = getattr(sca, "case_name", None)
    if cn is not None:
        all_text_parts.append(
            (cn.value if hasattr(cn, "value") else str(cn)).upper()
        )
    allegations = getattr(sca, "allegations", [])
    for alg in allegations:
        val = alg.value.upper() if hasattr(alg, "value") else str(alg).upper()
        all_text_parts.append(val)
    all_text = " ".join(all_text_parts)

    # Early exit: if non-securities class action keywords appear,
    # require explicit securities theories to override
    has_non_sec = any(kw in all_text for kw in _NON_SECURITIES_CLASS_KEYWORDS)

    # Check legal theories
    theories = getattr(sca, "legal_theories", [])
    if theories:
        theory_values = set()
        for t in theories:
            val = t.value.upper() if hasattr(t, "value") else str(t).upper()
            theory_values.add(val)
        # If ANY securities theory present, it's an SCA
        if theory_values & _SECURITIES_THEORIES:
            return True
        # If theories present but ALL are non-securities, not an SCA
        if theory_values and theory_values <= _NON_SECURITIES_THEORIES:
            return False

    # If non-securities keywords found and no securities theories, not an SCA
    if has_non_sec:
        return False

    # COMMERCIAL_ENTITY coverage without securities keywords is not an SCA
    ct = getattr(sca, "coverage_type", None)
    if ct is not None:
        ct_val = ct.value.upper() if hasattr(ct, "value") else str(ct).upper()
        if "COMMERCIAL" in ct_val:
            # Only treat as SCA if securities keywords are present
            if not any(kw in all_text for kw in _SECURITIES_CASE_KEYWORDS):
                return False

    # Check case name for securities keywords
    if any(kw in all_text for kw in _SECURITIES_CASE_KEYWORDS):
        return True

    # No securities indicators found — not an SCA
    return False


def _check_wells_notice(extracted: ExtractedData) -> tuple[bool, list[str]]:
    """CRF-2: Wells Notice disclosed."""
    lit = extracted.litigation
    if lit is None:
        return False, []
    enf = lit.sec_enforcement
    # Check highest_confirmed_stage for WELLS_NOTICE or higher
    if enf.highest_confirmed_stage is not None:
        stage = enf.highest_confirmed_stage.value.upper()
        if stage in ("WELLS_NOTICE", "ENFORCEMENT_ACTION"):
            return True, [f"SEC enforcement stage: {stage}"]
    # Also check pipeline_position
    if enf.pipeline_position is not None:
        pos = enf.pipeline_position.value.upper()
        if "WELLS" in pos:
            return True, [f"Wells Notice: pipeline_position={pos}"]
    return False, []


def _check_doj_investigation(
    extracted: ExtractedData,
) -> tuple[bool, list[str]]:
    """CRF-3: DOJ criminal investigation.

    Only triggers for CRIMINAL DOJ proceedings. Civil antitrust,
    civil rights, or other non-criminal DOJ actions do not qualify.
    """
    lit = extracted.litigation
    if lit is None:
        return False, []
    # Check pipeline signals for explicit criminal DOJ terms
    for signal in lit.sec_enforcement.pipeline_signals:
        sig_val = signal.value.upper()
        if "CRIMINAL" in sig_val and ("DOJ" in sig_val or "JUSTICE" in sig_val):
            return True, [f"DOJ criminal signal: {signal.value}"]
    # Check regulatory proceedings for criminal DOJ actions
    for proc in lit.regulatory_proceedings:
        proc_dict = proc.value
        agency = str(proc_dict.get("agency", "")).upper()
        desc = str(proc_dict.get("description", "")).upper()
        proc_type = str(proc_dict.get("type", "")).upper()
        is_doj = "DOJ" in agency or "DEPARTMENT OF JUSTICE" in agency
        if not is_doj:
            continue
        # Skip civil proceedings (antitrust, civil rights, etc.)
        is_civil = any(
            term in desc or term in proc_type
            for term in ("CIVIL", "ANTITRUST", "CIVIL RIGHTS")
        )
        if is_civil:
            continue
        # Only trigger if explicitly criminal
        is_criminal = "CRIMINAL" in desc or "CRIMINAL" in proc_type
        if is_criminal:
            return True, [f"DOJ criminal: {proc_dict.get('type', '')}"]
    return False, []


def _check_going_concern(extracted: ExtractedData) -> tuple[bool, list[str]]:
    """CRF-4: Going concern opinion."""
    fin = extracted.financials
    if fin is None:
        return False, []
    if fin.audit.going_concern is not None and fin.audit.going_concern.value:
        return True, ["Going concern opinion in most recent audit"]
    return False, []


def _check_recent_restatement(
    extracted: ExtractedData,
) -> tuple[bool, list[str]]:
    """CRF-5: Restatement in past 12 months."""
    fin = extracted.financials
    if fin is None:
        return False, []
    for rst in fin.audit.restatements:
        rst_dict = rst.value
        rst_date_str = rst_dict.get("date", "")
        if rst_date_str:
            try:
                rst_date = date.fromisoformat(rst_date_str)
                months = (date.today() - rst_date).days / 30.4
                if months < 12:
                    return True, [f"Restatement {months:.0f} months ago"]
            except (ValueError, TypeError):
                pass
    return False, []


def _check_spac_under_5(
    extracted: ExtractedData, company: CompanyProfile | None
) -> tuple[bool, list[str]]:
    """CRF-6: SPAC <18 months AND stock <$5."""
    from do_uw.stages.score.red_flag_gates_enhanced import check_spac_under_5
    return check_spac_under_5(extracted, company)


def _check_short_seller_report(
    extracted: ExtractedData,
) -> tuple[bool, list[str]]:
    """CRF-7: Named in short seller report within 6 months."""
    from do_uw.stages.score.red_flag_gates_enhanced import check_short_seller_report
    return check_short_seller_report(extracted)


def _check_catastrophic_decline(
    extracted: ExtractedData,
) -> tuple[bool, list[str]]:
    """CRF-8: Stock decline >60% from 52-week high."""
    from do_uw.stages.score.red_flag_gates_enhanced import check_catastrophic_decline
    return check_catastrophic_decline(extracted)


def _check_drop_7d(extracted: ExtractedData) -> tuple[bool, list[str]]:
    """CRF-9: Stock drop >10% in last 7 days."""
    from do_uw.stages.score.red_flag_gates_enhanced import check_recent_drop
    return check_recent_drop(extracted, days=7, threshold=10.0, label="7-day")


def _check_drop_30d(extracted: ExtractedData) -> tuple[bool, list[str]]:
    """CRF-10: Stock drop >15% in last 30 days."""
    from do_uw.stages.score.red_flag_gates_enhanced import check_recent_drop
    return check_recent_drop(extracted, days=30, threshold=15.0, label="30-day")


def _check_drop_90d(extracted: ExtractedData) -> tuple[bool, list[str]]:
    """CRF-11: Stock drop >25% in last 90 days."""
    from do_uw.stages.score.red_flag_gates_enhanced import check_recent_drop
    return check_recent_drop(extracted, days=90, threshold=25.0, label="90-day")
