"""Underwriting Decision Framework -- question-driven section context builder.

Loads the 55-question D&O underwriting framework from brain/questions/*.yaml,
auto-answers each question via ANSWERER_REGISTRY, and formats for template rendering.

SCA-derived questions (from Supabase claims data) are slotted inline into their
matching domain groups (Litigation, Market, Operational) with "SCA Data" source badges.

The framework follows the logical order a 30-year D&O underwriter uses:
  1. Company & Business -> 2. Financial -> 3. Governance -> 4. Market ->
  5. Litigation -> 6. Operational -> 7. Program -> 8. Decision

Each question gets: answer text, evidence list, verdict badge, confidence level.
Questions without data show "Needs Review" with filing references.
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.brain.questions import load_all_domains
from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders.answerers import ANSWERER_REGISTRY
from do_uw.stages.render.context_builders.answerers._helpers import (
    suggest_filing_reference,
)
from do_uw.stages.render.context_builders.answerers.sca_questions import (
    generate_sca_questions,
)

logger = logging.getLogger(__name__)


def build_uw_questions_context(
    state: AnalysisState,
    ctx: dict[str, Any],
) -> dict[str, Any]:
    """Build the Underwriting Decision Framework section context.

    Args:
        state: Full pipeline state.
        ctx: Existing render context (has executive_summary, financials, etc.).

    Returns:
        Dict with domain groups, each containing answered questions.
    """
    domains = load_all_domains()
    ctx_with_state = {**ctx, "_state": state}

    # Generate SCA-derived questions and slot into matching domains
    sca_questions = generate_sca_questions(state, ctx_with_state)
    sca_by_domain: dict[str, list[dict[str, Any]]] = {}
    for sq in sca_questions:
        target = sq.get("domain", "")
        sca_by_domain.setdefault(target, []).append(sq)

    domain_groups: list[dict[str, Any]] = []
    total_answered = 0
    total_questions = 0
    total_upgrades = 0
    total_downgrades = 0

    for domain in domains:
        domain_label = domain.get("domain_label", "Unknown")
        domain_id = domain.get("domain", "")
        raw_questions = domain.get("questions", [])

        # Answer each question via the answerer registry
        formatted_questions: list[dict[str, Any]] = []
        domain_answered = 0
        domain_upgrades = 0
        domain_downgrades = 0

        for q in raw_questions:
            qid = q.get("question_id", "")
            answerer = ANSWERER_REGISTRY.get(qid)

            if answerer:
                try:
                    result = answerer(q, state, ctx_with_state)
                    aq = {**q, **result}
                except Exception:
                    logger.warning("Answerer %s crashed — marking NO_DATA", qid)
                    aq = {
                        **q,
                        "verdict": "NO_DATA",
                        "data_found": False,
                        "answer": "",
                        "evidence": [],
                        "confidence": "LOW",
                    }
            else:
                # No answerer registered -- mark as needs review
                aq = {
                    **q,
                    "verdict": "NO_DATA",
                    "data_found": False,
                    "answer": "",
                    "evidence": [],
                    "confidence": "LOW",
                }

            verdict = aq.get("verdict", "NO_DATA")
            has_answer = verdict != "NO_DATA" and aq.get("data_found", False)

            if has_answer:
                domain_answered += 1
                total_answered += 1

            if verdict == "UPGRADE":
                domain_upgrades += 1
                total_upgrades += 1
            elif verdict == "DOWNGRADE":
                domain_downgrades += 1
                total_downgrades += 1

            # Build evidence string
            evidence = aq.get("evidence", [])
            evidence_str = " | ".join(evidence[:4]) if evidence else ""

            # Build filing reference for unanswered questions
            filing_ref = ""
            if not has_answer:
                ds = aq.get("data_sources", [])
                if ds:
                    filing_ref = suggest_filing_reference(ds)

            formatted_questions.append({
                "question_id": aq.get("question_id", ""),
                "text": aq.get("text", ""),
                "answer": aq.get("answer", ""),
                "evidence": evidence_str,
                "verdict": verdict,
                "confidence": aq.get("confidence", "LOW"),
                "has_answer": has_answer,
                "filing_ref": filing_ref,
                "weight": aq.get("weight", 5),
                "source": "",
                "upgrade_criteria": aq.get("upgrade_criteria", ""),
                "downgrade_criteria": aq.get("downgrade_criteria", ""),
            })
            total_questions += 1

        # Append SCA questions for this domain (pre-answered)
        for sq in sca_by_domain.get(domain_id, []):
            verdict = sq.get("verdict", "NO_DATA")
            has_answer = verdict != "NO_DATA" and sq.get("data_found", False)

            if has_answer:
                domain_answered += 1
                total_answered += 1

            if verdict == "UPGRADE":
                domain_upgrades += 1
                total_upgrades += 1
            elif verdict == "DOWNGRADE":
                domain_downgrades += 1
                total_downgrades += 1

            evidence = sq.get("evidence", [])
            evidence_str = " | ".join(evidence[:4]) if isinstance(evidence, list) else ""

            formatted_questions.append({
                "question_id": sq.get("question_id", ""),
                "text": sq.get("text", ""),
                "answer": sq.get("answer", ""),
                "evidence": evidence_str,
                "verdict": verdict,
                "confidence": sq.get("confidence", "LOW"),
                "has_answer": has_answer,
                "filing_ref": "",
                "weight": sq.get("weight", 5),
                "source": sq.get("source", ""),
                "upgrade_criteria": sq.get("upgrade_criteria", ""),
                "downgrade_criteria": sq.get("downgrade_criteria", ""),
            })
            total_questions += 1

        # Domain verdict badge
        net = domain_upgrades - domain_downgrades
        domain_verdict = "FAVORABLE" if net > 0 else ("UNFAVORABLE" if net < 0 else "MIXED")

        domain_groups.append({
            "domain": domain_id,
            "domain_label": domain_label,
            "description": domain.get("description", ""),
            "questions": formatted_questions,
            "answered_count": domain_answered,
            "total_count": len(formatted_questions),
            "answer_pct": round(domain_answered / max(len(formatted_questions), 1) * 100),
            "upgrades": domain_upgrades,
            "downgrades": domain_downgrades,
            "verdict": domain_verdict,
        })

    # Summary stats
    answer_pct = round(total_answered / max(total_questions, 1) * 100)

    # Section-level verdict
    net_total = total_upgrades - total_downgrades
    section_verdict = "FAVORABLE" if net_total > 0 else (
        "UNFAVORABLE" if net_total < 0 else "MIXED"
    )

    return {
        "domains": domain_groups,
        "total_questions": total_questions,
        "total_answered": total_answered,
        "answer_pct": answer_pct,
        "total_upgrades": total_upgrades,
        "total_downgrades": total_downgrades,
        "net_assessment": section_verdict,
        "section_verdict": section_verdict,
    }
