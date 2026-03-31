"""Knowledge store for D&O underwriting domain intelligence.

Provides SQLAlchemy ORM models, lifecycle management, migration
infrastructure, query API, learning infrastructure, and narrative
composition for the knowledge store database.

Public API:
    Models: Base, Check, CheckHistory, CheckRun, Pattern, ScoringRule,
            RedFlag, Sector, Note, IndustryPlaybook
    Lifecycle: SignalStatus, validate_transition, transition_signal,
               record_field_change
    Store: KnowledgeStore
    Migration: migrate_from_json
    Learning: record_analysis_run, get_signal_effectiveness,
              find_redundant_pairs, get_learning_summary
    Narrative: compose_narrative, get_available_narratives,
               suggest_new_narrative, NarrativeStory
    Ingestion: ingest_document, ingest_text, DocumentType, IngestionResult
    Playbooks: activate_playbook, load_playbooks, get_industry_signals,
               get_industry_questions, get_scoring_adjustments,
               get_claim_theories, get_active_signals_with_industry
"""

from __future__ import annotations

from do_uw.knowledge.ingestion import (
    DocumentType,
    IngestionResult,
    ingest_document,
    ingest_text,
)
from do_uw.knowledge.learning import (
    AnalysisOutcome,
    SignalEffectiveness,
    find_redundant_pairs,
    get_signal_effectiveness,
    get_learning_summary,
    record_analysis_run,
)
from do_uw.knowledge.lifecycle import (
    SignalStatus,
    record_field_change,
    transition_signal,
    validate_transition,
)
from do_uw.knowledge.migrate import migrate_from_json
from do_uw.knowledge.models import (
    Base,
    Check,
    CheckHistory,
    CheckRun,
    IndustryPlaybook,
    Note,
    Pattern,
    RedFlag,
    ScoringRule,
    Sector,
    Signal,
    SignalHistory,
    SignalRun,
)
from do_uw.knowledge.narrative import (
    NarrativeStory,
    compose_narrative,
    get_available_narratives,
    suggest_new_narrative,
)
from do_uw.knowledge.playbooks import (
    activate_playbook,
    get_active_signals_with_industry,
    get_claim_theories,
    get_industry_signals,
    get_industry_questions,
    get_scoring_adjustments,
    load_playbooks,
)
from do_uw.knowledge.store import KnowledgeStore

__all__ = [
    "AnalysisOutcome",
    "Base",
    "Check",
    "SignalEffectiveness",
    "CheckHistory",
    "CheckRun",
    "DocumentType",
    "IndustryPlaybook",
    "IngestionResult",
    "KnowledgeStore",
    "NarrativeStory",
    "Note",
    "Pattern",
    "RedFlag",
    "ScoringRule",
    "Sector",
    "SignalStatus",
    "activate_playbook",
    "compose_narrative",
    "find_redundant_pairs",
    "get_active_signals_with_industry",
    "get_available_narratives",
    "get_signal_effectiveness",
    "get_claim_theories",
    "get_industry_signals",
    "get_industry_questions",
    "get_learning_summary",
    "get_scoring_adjustments",
    "ingest_document",
    "ingest_text",
    "load_playbooks",
    "migrate_from_json",
    "record_analysis_run",
    "record_field_change",
    "suggest_new_narrative",
    "transition_signal",
    "validate_transition",
]
