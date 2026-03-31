"""ORM-to-dict converters for knowledge store models.

Provides functions to convert SQLAlchemy ORM objects to plain dicts
for the KnowledgeStore query API. Extracted from store.py for
500-line compliance.
"""

from __future__ import annotations

from typing import Any

from do_uw.knowledge.models import (
    Check,
    IndustryPlaybook,
    Note,
    Pattern,
    RedFlag,
    ScoringRule,
)


def check_to_dict(check: Check) -> dict[str, Any]:
    """Convert a Check ORM object to a plain dict."""
    return {
        "id": check.id,
        "name": check.name,
        "section": check.section,
        "pillar": check.pillar,
        "severity": check.severity,
        "execution_mode": check.execution_mode,
        "status": check.status,
        "threshold_type": check.threshold_type,
        "threshold_value": check.threshold_value,
        "required_data": check.required_data,
        "data_locations": check.data_locations,
        "scoring_factor": check.scoring_factor,
        "scoring_rule": check.scoring_rule,
        "output_section": check.output_section,
        "origin": check.origin,
        "version": check.version,
        "metadata_json": check.metadata_json,
        # Phase 31 knowledge model enrichment fields
        "content_type": check.content_type,
        "depth": check.depth,
        "rationale": check.rationale,
        "field_key": check.field_key,
        "extraction_path": check.extraction_path,
        "pattern_ref": check.pattern_ref,
    }


def pattern_to_dict(pattern: Pattern) -> dict[str, Any]:
    """Convert a Pattern ORM object to a plain dict."""
    return {
        "id": pattern.id,
        "name": pattern.name,
        "category": pattern.category,
        "description": pattern.description,
        "allegation_types": pattern.allegation_types,
        "trigger_conditions": pattern.trigger_conditions,
        "score_impact": pattern.score_impact,
        "severity_modifier": pattern.severity_modifier,
        "status": pattern.status,
    }


def scoring_rule_to_dict(rule: ScoringRule) -> dict[str, Any]:
    """Convert a ScoringRule ORM object to a plain dict."""
    return {
        "id": rule.id,
        "factor_id": rule.factor_id,
        "condition": rule.condition,
        "points": rule.points,
        "triggers_crf": rule.triggers_crf,
    }


def red_flag_to_dict(flag: RedFlag) -> dict[str, Any]:
    """Convert a RedFlag ORM object to a plain dict."""
    return {
        "id": flag.id,
        "name": flag.name,
        "condition": flag.condition,
        "detection_logic": flag.detection_logic,
        "max_tier": flag.max_tier,
        "max_quality_score": flag.max_quality_score,
        "status": flag.status,
    }


def note_to_dict(note: Note) -> dict[str, Any]:
    """Convert a Note ORM object to a plain dict."""
    return {
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "tags": note.tags,
        "source": note.source,
        "signal_id": note.signal_id,
    }


def playbook_to_dict(pb: IndustryPlaybook) -> dict[str, Any]:
    """Convert an IndustryPlaybook ORM object to a plain dict."""
    return {
        "id": pb.id,
        "name": pb.name,
        "description": pb.description,
        "sic_ranges": pb.sic_ranges,
        "naics_prefixes": pb.naics_prefixes,
        "check_overrides": pb.check_overrides,
        "scoring_adjustments": pb.scoring_adjustments,
        "risk_patterns": pb.risk_patterns,
        "claim_theories": pb.claim_theories,
        "meeting_questions": pb.meeting_questions,
        "status": pb.status,
    }
