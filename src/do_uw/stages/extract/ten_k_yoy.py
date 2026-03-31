"""10-K year-over-year comparison: diff risk factors, controls, legal, MD&A.

Compares the two most recent 10-K LLM extractions to identify material
changes in disclosures. Uses difflib.SequenceMatcher for fuzzy risk
factor title matching (no external dependencies).

Public API:
    compute_yoy_comparison(state) -> TenKYoYComparison | None
"""

from __future__ import annotations

import logging
import re
from difflib import SequenceMatcher
from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.models.ten_k_comparison import (
    DisclosureChange,
    RiskFactorChange,
    TenKYoYComparison,
)

logger = logging.getLogger(__name__)

# Minimum similarity ratio for two risk factor titles to be considered a match.
_TITLE_MATCH_THRESHOLD = 0.6

# Lower threshold used when high NEW+REMOVED count suggests bulk reorganization.
_TITLE_MATCH_THRESHOLD_REORG = 0.4

# Minimum word overlap for reorganization detection (fraction or absolute count).
_REORG_WORD_OVERLAP_FRACTION = 0.3
_REORG_WORD_OVERLAP_MIN_COUNT = 3

# More aggressive thresholds when bulk reorganization is detected.
_REORG_WORD_OVERLAP_FRACTION_AGGRESSIVE = 0.2
_REORG_WORD_OVERLAP_MIN_COUNT_AGGRESSIVE = 2

# Common stop words to exclude from word-overlap comparison.
_STOP_WORDS = frozenset(
    {
        "and",
        "the",
        "of",
        "to",
        "in",
        "for",
        "a",
        "an",
        "or",
        "by",
        "on",
        "from",
        "with",
        "our",
        "we",
        "may",
        "could",
        "that",
        "are",
        "is",
        "be",
        "as",
        "its",
        "their",
        "this",
        "these",
        "those",
        "not",
    }
)

# Severity ordering for escalation/de-escalation detection.
_SEVERITY_RANK: dict[str, int] = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_yoy_comparison(
    state: AnalysisState,
) -> TenKYoYComparison | None:
    """Compare the two most recent 10-K extractions in state.

    Returns None if fewer than 2 10-K extractions are available.
    """
    if state.acquired_data is None:
        return None

    extractions = _collect_ten_k_extractions(state)
    if len(extractions) < 2:
        logger.info(
            "YoY comparison: need >= 2 10-K extractions, have %d",
            len(extractions),
        )
        return None

    # extractions sorted newest-first
    current = extractions[0]
    prior = extractions[1]

    current_year = _fiscal_year_label(current)
    prior_year = _fiscal_year_label(prior)

    # Risk factor comparison
    risk_changes = _compare_risk_factors(
        current.get("risk_factors", []),
        prior.get("risk_factors", []),
    )

    # Post-process: detect reorganized/consolidated risk factors
    risk_changes = _detect_reorganizations(risk_changes)

    # LLM semantic matching: identify remaining NEW/REMOVED pairs that are
    # the same risk reworded (catches what word-overlap misses)
    risk_changes = _semantic_match_remaining(risk_changes)

    new_count = sum(1 for r in risk_changes if r.change_type == "NEW")
    removed_count = sum(1 for r in risk_changes if r.change_type == "REMOVED")
    escalated_count = sum(1 for r in risk_changes if r.change_type == "ESCALATED")
    reorganized_count = sum(1 for r in risk_changes if r.change_type == "REORGANIZED")

    # Controls comparison
    controls_changed, mw_change = _compare_controls(current, prior)

    # Legal proceedings delta
    legal_delta = _compare_legal_proceedings(current, prior)

    # Disclosure changes from MD&A, controls, legal
    disclosure_changes = _build_disclosure_changes(
        current,
        prior,
        controls_changed,
        mw_change,
        legal_delta,
    )

    result = TenKYoYComparison(
        current_year=current_year,
        prior_year=prior_year,
        risk_factor_changes=risk_changes,
        new_risk_count=new_count,
        removed_risk_count=removed_count,
        escalated_risk_count=escalated_count,
        reorganized_risk_count=reorganized_count,
        disclosure_changes=disclosure_changes,
        controls_changed=controls_changed,
        material_weakness_change=mw_change,
        legal_proceedings_delta=legal_delta,
    )

    logger.info(
        "YoY comparison (%s vs %s): %d risk changes "
        "(%d new, %d removed, %d escalated, %d reorganized), "
        "%d disclosure changes, legal delta %+d",
        current_year,
        prior_year,
        len(risk_changes),
        new_count,
        removed_count,
        escalated_count,
        reorganized_count,
        len(disclosure_changes),
        legal_delta,
    )

    return result


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------


def _collect_ten_k_extractions(
    state: AnalysisState,
) -> list[dict[str, Any]]:
    """Collect 10-K LLM extractions, sorted by filing date descending."""
    if state.acquired_data is None:
        return []

    llm_extractions = state.acquired_data.llm_extractions
    ten_k_items: list[tuple[str, dict[str, Any]]] = []

    for key, value in llm_extractions.items():
        # Keys are "10-K:accession" or "20-F:accession"
        if not key.startswith(("10-K:", "20-F:")):
            continue
        if not isinstance(value, dict):
            continue
        # Get filing_date from the filing_documents list
        filing_date = _find_filing_date(state, key)
        ten_k_items.append((filing_date, value))

    # Sort by filing date descending (newest first)
    ten_k_items.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in ten_k_items]


def _find_filing_date(state: AnalysisState, extraction_key: str) -> str:
    """Find the filing date for a given extraction key.

    Extraction keys are 'form_type:accession'. We look up the
    corresponding filing_documents entry for the filing date.
    """
    if state.acquired_data is None:
        return ""
    parts = extraction_key.split(":", 1)
    if len(parts) != 2:
        return ""
    form_type, accession = parts

    docs = state.acquired_data.filing_documents.get(form_type, [])
    for doc in docs:
        if doc.get("accession") == accession:
            return doc.get("filing_date", "")
    return ""


def _fiscal_year_label(extraction: dict[str, Any]) -> str:
    """Derive a fiscal year label like 'FY2025' from extraction metadata."""
    period = extraction.get("period_of_report") or ""
    fy_end = extraction.get("fiscal_year_end") or ""

    # Try to extract year from period_of_report (e.g. '2024-12-31')
    for source in (period, fy_end):
        match = re.search(r"20\d{2}", source)
        if match:
            return f"FY{match.group()}"

    return "FY????"


# ---------------------------------------------------------------------------
# Reorganization detection
# ---------------------------------------------------------------------------


def _content_words(title: str) -> set[str]:
    """Extract content words from a risk factor title, excluding stop words."""
    words = set(re.findall(r"[a-z]+", title.lower()))
    return words - _STOP_WORDS


def _detect_reorganizations(
    changes: list[RiskFactorChange],
) -> list[RiskFactorChange]:
    """Detect risk factors that were reorganized/consolidated, not truly new/removed.

    When companies restructure their risk factor disclosures, individual items
    may be split, merged, or renamed. This function uses word-overlap analysis
    to identify NEW/REMOVED pairs that are actually the same risk reworded.

    A NEW item is reclassified as REORGANIZED if any REMOVED item shares
    sufficient word overlap (>=30% of the larger set, or >=3 content words).
    The matched REMOVED item is reclassified as CONSOLIDATED_INTO.
    """
    new_items = [(i, c) for i, c in enumerate(changes) if c.change_type == "NEW"]
    removed_items = [(i, c) for i, c in enumerate(changes) if c.change_type == "REMOVED"]

    if not new_items or not removed_items:
        return changes

    matched_removed_indices: set[int] = set()

    for _ni, new_change in new_items:
        new_words = _content_words(new_change.title)
        if not new_words:
            continue

        best_overlap = 0
        best_ri: int | None = None
        best_removed_change: RiskFactorChange | None = None

        for ri, removed_change in removed_items:
            if ri in matched_removed_indices:
                continue
            rem_words = _content_words(removed_change.title)
            if not rem_words:
                continue

            overlap = new_words & rem_words
            overlap_count = len(overlap)
            max_len = max(len(new_words), len(rem_words))
            similarity = overlap_count / max_len if max_len > 0 else 0.0

            if (
                similarity >= _REORG_WORD_OVERLAP_FRACTION
                or overlap_count >= _REORG_WORD_OVERLAP_MIN_COUNT
            ):
                if overlap_count > best_overlap:
                    best_overlap = overlap_count
                    best_ri = ri
                    best_removed_change = removed_change

        if best_ri is not None and best_removed_change is not None:
            # Reclassify the NEW item as REORGANIZED
            new_change.change_type = "REORGANIZED"
            new_change.prior_title = best_removed_change.title
            new_change.summary = f"Reorganized from: {best_removed_change.title}"

            # Reclassify the REMOVED item as CONSOLIDATED_INTO
            best_removed_change.change_type = "CONSOLIDATED_INTO"
            best_removed_change.new_title = new_change.title
            best_removed_change.summary = f"Consolidated into: {new_change.title}"

            matched_removed_indices.add(best_ri)

    reorg_count = len(matched_removed_indices)
    if reorg_count > 0:
        logger.info(
            "Reorganization detection: %d NEW+REMOVED pairs reclassified "
            "as reorganized/consolidated",
            reorg_count,
        )

    return changes


# ---------------------------------------------------------------------------
# LLM semantic matching for remaining unmatched NEW/REMOVED pairs
# ---------------------------------------------------------------------------


def _semantic_match_remaining(
    changes: list[RiskFactorChange],
) -> list[RiskFactorChange]:
    """Use LLM to identify remaining NEW/REMOVED pairs that describe the same risk.

    After title matching and word-overlap reorganization detection, some
    genuinely reworded risk factors still appear as NEW+REMOVED because
    the titles share no words (e.g., "Litigation Risk" vs "Dispute
    Resolution Exposure"). This function sends the remaining unmatched
    pairs to the LLM for semantic comparison.

    Skips if no LLM is available or if there are too few unmatched items.
    """
    new_items = [(i, c) for i, c in enumerate(changes) if c.change_type == "NEW"]
    removed_items = [(i, c) for i, c in enumerate(changes) if c.change_type == "REMOVED"]

    # Need at least 1 of each to compare
    if not new_items or not removed_items:
        return changes

    # Skip if too many items (would be expensive and low signal)
    # Raised from 20→30 to handle bulk reorganizations (e.g., Apple FY2024→FY2025)
    if len(new_items) > 30 or len(removed_items) > 30:
        logger.info(
            "Semantic matching skipped: too many unmatched items (%d new, %d removed)",
            len(new_items),
            len(removed_items),
        )
        return changes

    # Build the LLM prompt
    new_list = "\n".join(f"  NEW-{i}: {c.title}" for i, (_, c) in enumerate(new_items))
    removed_list = "\n".join(f"  REM-{i}: {c.title}" for i, (_, c) in enumerate(removed_items))

    prompt = (
        "You are comparing risk factors between two consecutive 10-K annual "
        "reports. After automated title matching, the following risk factors "
        "remain unmatched.\n\n"
        f"NEW risk factors (in current year, not matched to prior year):\n{new_list}\n\n"
        f"REMOVED risk factors (in prior year, not matched to current year):\n{removed_list}\n\n"
        "Identify pairs where a NEW item and a REMOVED item describe "
        "SUBSTANTIALLY THE SAME RISK, just with different wording or "
        "reorganized structure. A match means the underlying risk concern "
        "is the same even if the title changed completely.\n\n"
        "Respond with ONLY matched pairs, one per line, in this exact format:\n"
        "NEW-0 = REM-2\n"
        "NEW-3 = REM-1\n\n"
        "If no pairs match, respond with: NONE\n"
        "Be conservative — only match pairs where the underlying risk is "
        "clearly the same. Do not match items that are merely in the same "
        "category (e.g., two different litigation risks are NOT the same)."
    )

    try:
        import os

        try:
            import openai as _openai
        except ImportError:
            logger.debug("OpenAI not available; skipping semantic matching")
            return changes

        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            return changes

        client = _openai.OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
        )
        response = client.chat.completions.create(
            model="deepseek-chat",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )

        result_text = response.choices[0].message.content.strip()
        if result_text == "NONE" or not result_text:
            logger.info("Semantic matching: no additional matches found")
            return changes

        # Parse matches
        import re as _re

        match_count = 0
        for line in result_text.split("\n"):
            m = _re.match(r"NEW-(\d+)\s*=\s*REM-(\d+)", line.strip())
            if not m:
                continue
            new_idx = int(m.group(1))
            rem_idx = int(m.group(2))

            if new_idx >= len(new_items) or rem_idx >= len(removed_items):
                continue

            _change_idx_new, new_change = new_items[new_idx]
            _change_idx_rem, rem_change = removed_items[rem_idx]

            # Reclassify
            new_change.change_type = "REORGANIZED"
            new_change.prior_title = rem_change.title
            new_change.summary = f"Semantic match: reorganized from '{rem_change.title}'"

            rem_change.change_type = "CONSOLIDATED_INTO"
            rem_change.new_title = new_change.title
            rem_change.summary = f"Semantic match: consolidated into '{new_change.title}'"
            match_count += 1

        if match_count > 0:
            logger.info(
                "Semantic matching: %d additional NEW+REMOVED pairs reclassified as reorganized",
                match_count,
            )

    except Exception as exc:
        logger.warning(
            "Semantic matching failed (non-fatal): %s",
            exc,
        )

    return changes


# ---------------------------------------------------------------------------
# Risk factor comparison
# ---------------------------------------------------------------------------


def _get_body_text(rf: dict[str, Any]) -> str:
    """Extract body/description text from a risk factor dict."""
    for key in ("description", "body", "text", "content", "source_passage"):
        val = rf.get(key, "")
        if isinstance(val, str) and len(val) > 20:
            return val
    return ""


def _compare_risk_factors(
    current_rfs: list[dict[str, Any]],
    prior_rfs: list[dict[str, Any]],
) -> list[RiskFactorChange]:
    """Compare risk factors between two years using multi-pass matching.

    Pass 1: Fuzzy title matching (SequenceMatcher >= 0.6)
    Pass 2: Body text matching for unmatched items (catches rewrites)
    Pass 3: If high unmatched count suggests bulk reorganization, lower thresholds
    """
    changes: list[RiskFactorChange] = []

    matched_prior_indices: set[int] = set()
    current_matches: dict[int, int] = {}  # current_idx -> prior_idx

    # --- Pass 1: Title matching ---
    for ci, current_rf in enumerate(current_rfs):
        best_ratio = 0.0
        best_pi = -1
        c_title = _normalize_title(current_rf.get("title", ""))

        for pi, prior_rf in enumerate(prior_rfs):
            if pi in matched_prior_indices:
                continue
            p_title = _normalize_title(prior_rf.get("title", ""))
            ratio = SequenceMatcher(None, c_title, p_title).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_pi = pi

        if best_ratio >= _TITLE_MATCH_THRESHOLD and best_pi >= 0:
            current_matches[ci] = best_pi
            matched_prior_indices.add(best_pi)

    # --- Pass 2: Body text matching for unmatched items ---
    # When companies rewrite risk factor titles, the body text often retains
    # similar content. Use body/description field for cross-matching.
    unmatched_current = [ci for ci in range(len(current_rfs)) if ci not in current_matches]
    unmatched_prior = [pi for pi in range(len(prior_rfs)) if pi not in matched_prior_indices]

    if unmatched_current and unmatched_prior:
        for ci in list(unmatched_current):
            c_body = _get_body_text(current_rfs[ci])
            if not c_body:
                continue
            c_body_words = _content_words(c_body)
            best_overlap = 0
            best_pi = -1

            for pi in unmatched_prior:
                if pi in matched_prior_indices:
                    continue
                p_body = _get_body_text(prior_rfs[pi])
                if not p_body:
                    continue
                p_body_words = _content_words(p_body)
                overlap = len(c_body_words & p_body_words)
                max_len = max(len(c_body_words), len(p_body_words), 1)
                # Body text similarity > 40% is a strong signal of same risk
                if overlap / max_len >= 0.4 and overlap > best_overlap:
                    best_overlap = overlap
                    best_pi = pi

            if best_pi >= 0:
                current_matches[ci] = best_pi
                matched_prior_indices.add(best_pi)
                unmatched_current.remove(ci)
                unmatched_prior.remove(best_pi)

    # --- Pass 3: Bulk reorganization detection ---
    # If > 50% of factors are unmatched, it's likely a bulk rewrite — lower thresholds
    total = max(len(current_rfs), len(prior_rfs), 1)
    unmatched_pct = len(unmatched_current) / total
    if unmatched_pct > 0.5 and unmatched_current and unmatched_prior:
        logger.info(
            "Bulk reorganization detected: %.0f%% unmatched, lowering thresholds",
            unmatched_pct * 100,
        )
        for ci in list(unmatched_current):
            c_title = _normalize_title(current_rfs[ci].get("title", ""))
            best_ratio = 0.0
            best_pi = -1

            for pi in unmatched_prior:
                if pi in matched_prior_indices:
                    continue
                p_title = _normalize_title(prior_rfs[pi].get("title", ""))
                ratio = SequenceMatcher(None, c_title, p_title).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_pi = pi

            if best_ratio >= _TITLE_MATCH_THRESHOLD_REORG and best_pi >= 0:
                current_matches[ci] = best_pi
                matched_prior_indices.add(best_pi)

    # Process matched pairs (UNCHANGED, ESCALATED, DE_ESCALATED)
    for ci, pi in current_matches.items():
        current_rf = current_rfs[ci]
        prior_rf = prior_rfs[pi]
        change = _classify_change(current_rf, prior_rf)
        changes.append(change)

    # NEW risk factors (in current, no match in prior)
    for ci, current_rf in enumerate(current_rfs):
        if ci in current_matches:
            continue
        changes.append(
            RiskFactorChange(
                title=current_rf.get("title", "Unknown"),
                category=current_rf.get("category", "OTHER"),
                change_type="NEW",
                current_severity=current_rf.get("severity", "MEDIUM"),
                prior_severity=None,
                summary=f"New risk factor added: {current_rf.get('title', 'Unknown')}",
            )
        )

    # REMOVED risk factors (in prior, no match in current)
    for pi, prior_rf in enumerate(prior_rfs):
        if pi in matched_prior_indices:
            continue
        changes.append(
            RiskFactorChange(
                title=prior_rf.get("title", "Unknown"),
                category=prior_rf.get("category", "OTHER"),
                change_type="REMOVED",
                current_severity=prior_rf.get("severity", "MEDIUM"),
                prior_severity=prior_rf.get("severity", "MEDIUM"),
                summary=f"Risk factor removed: {prior_rf.get('title', 'Unknown')}",
            )
        )

    return changes


def _normalize_title(title: str) -> str:
    """Normalize a risk factor title for comparison."""
    return title.lower().strip()


def _classify_change(
    current: dict[str, Any],
    prior: dict[str, Any],
) -> RiskFactorChange:
    """Classify a matched risk factor pair as UNCHANGED/ESCALATED/DE_ESCALATED."""
    c_sev = current.get("severity", "MEDIUM")
    p_sev = prior.get("severity", "MEDIUM")
    c_rank = _SEVERITY_RANK.get(c_sev, 2)
    p_rank = _SEVERITY_RANK.get(p_sev, 2)

    if c_rank > p_rank:
        change_type = "ESCALATED"
        summary = f"Severity increased from {p_sev} to {c_sev}"
    elif c_rank < p_rank:
        change_type = "DE_ESCALATED"
        summary = f"Severity decreased from {p_sev} to {c_sev}"
    else:
        change_type = "UNCHANGED"
        summary = "Risk factor continues at same severity"

    return RiskFactorChange(
        title=current.get("title", "Unknown"),
        category=current.get("category", "OTHER"),
        change_type=change_type,
        current_severity=c_sev,
        prior_severity=p_sev,
        summary=summary,
    )


# ---------------------------------------------------------------------------
# Controls comparison
# ---------------------------------------------------------------------------


def _compare_controls(
    current: dict[str, Any],
    prior: dict[str, Any],
) -> tuple[bool, str | None]:
    """Compare controls assessment between years.

    Returns (controls_changed, material_weakness_change).
    material_weakness_change is 'APPEARED', 'REMEDIATED', or None.
    """
    c_mw = bool(current.get("has_material_weakness", False))
    p_mw = bool(prior.get("has_material_weakness", False))

    if c_mw and not p_mw:
        return True, "APPEARED"
    elif not c_mw and p_mw:
        return True, "REMEDIATED"
    elif c_mw != p_mw:
        return True, None

    # Check if material weaknesses list changed
    c_list = current.get("material_weaknesses", [])
    p_list = prior.get("material_weaknesses", [])
    if set(str(x) for x in c_list) != set(str(x) for x in p_list):
        return True, None

    return False, None


# ---------------------------------------------------------------------------
# Legal proceedings comparison
# ---------------------------------------------------------------------------


def _compare_legal_proceedings(
    current: dict[str, Any],
    prior: dict[str, Any],
) -> int:
    """Return net new legal proceedings (current count - prior count)."""
    c_count = len(current.get("legal_proceedings", []))
    p_count = len(prior.get("legal_proceedings", []))
    return c_count - p_count


# ---------------------------------------------------------------------------
# Disclosure changes
# ---------------------------------------------------------------------------


def _build_disclosure_changes(
    current: dict[str, Any],
    prior: dict[str, Any],
    controls_changed: bool,
    mw_change: str | None,
    legal_delta: int,
) -> list[DisclosureChange]:
    """Build disclosure change list from cross-section comparison."""
    changes: list[DisclosureChange] = []

    # Controls changes
    if mw_change == "APPEARED":
        changes.append(
            DisclosureChange(
                section="controls",
                change_type="NEW",
                description="Material weakness disclosed for the first time",
                do_relevance="HIGH",
            )
        )
    elif mw_change == "REMEDIATED":
        changes.append(
            DisclosureChange(
                section="controls",
                change_type="MATERIAL_CHANGE",
                description="Previously disclosed material weakness has been remediated",
                do_relevance="MEDIUM",
            )
        )
    elif controls_changed:
        changes.append(
            DisclosureChange(
                section="controls",
                change_type="MATERIAL_CHANGE",
                description="Changes in internal controls disclosures",
                do_relevance="MEDIUM",
            )
        )

    # Legal proceedings changes
    if legal_delta > 0:
        changes.append(
            DisclosureChange(
                section="legal_proceedings",
                change_type="NEW",
                description=f"{legal_delta} new legal proceeding(s) disclosed",
                do_relevance="HIGH" if legal_delta >= 2 else "MEDIUM",
            )
        )
    elif legal_delta < 0:
        changes.append(
            DisclosureChange(
                section="legal_proceedings",
                change_type="REMOVED",
                description=(f"{abs(legal_delta)} legal proceeding(s) resolved or removed"),
                do_relevance="LOW",
            )
        )

    # MD&A key financial concerns comparison
    c_concerns = set(current.get("key_financial_concerns", []))
    p_concerns = set(prior.get("key_financial_concerns", []))
    new_concerns = c_concerns - p_concerns
    removed_concerns = p_concerns - c_concerns

    for concern in sorted(new_concerns):
        changes.append(
            DisclosureChange(
                section="mda",
                change_type="NEW",
                description=f"New MD&A concern: {concern}",
                do_relevance="MEDIUM",
            )
        )
    for concern in sorted(removed_concerns):
        changes.append(
            DisclosureChange(
                section="mda",
                change_type="REMOVED",
                description=f"MD&A concern no longer mentioned: {concern}",
                do_relevance="LOW",
            )
        )

    return changes


__all__ = ["compute_yoy_comparison"]
