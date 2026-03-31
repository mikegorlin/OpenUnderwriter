"""Knowledge store query API with full-text search.

Provides the KnowledgeStore class, the primary interface for querying
D&O underwriting domain knowledge (checks, patterns, scoring rules,
red flags, sectors, notes, and industry playbooks).

Supports FTS5 full-text search with LIKE fallback when FTS5 is
unavailable at runtime.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, cast

from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from do_uw.knowledge.models import (
    Base,
    Check,
    IndustryPlaybook,
    Note,
    Pattern,
    RedFlag,
    ScoringRule,
    Sector,
)
from do_uw.knowledge.store_bulk import KnowledgeStoreBulkMixin
from do_uw.knowledge.store_converters import (
    check_to_dict,
    pattern_to_dict,
    playbook_to_dict,
    red_flag_to_dict,
    scoring_rule_to_dict,
)

logger = logging.getLogger(__name__)

_DEFAULT_DB_PATH = Path(__file__).parent / "knowledge.db"


class KnowledgeStore(KnowledgeStoreBulkMixin):
    """Query API for the D&O underwriting knowledge store.

    Wraps a SQLite database with FTS5 full-text search support.
    Provides multi-criteria filtering for checks, patterns, scoring
    rules, red flags, sectors, notes, and industry playbooks.

    Args:
        db_path: Path to the SQLite database. Use None for in-memory.
            Defaults to knowledge.db in the knowledge package directory.
    """

    def __init__(self, db_path: str | Path | None = _DEFAULT_DB_PATH) -> None:
        if db_path is None:
            url = "sqlite://"
        else:
            url = f"sqlite:///{db_path}"
        self._engine: Engine = create_engine(url, echo=False)
        self._session_factory = sessionmaker(bind=self._engine)
        Base.metadata.create_all(self._engine)
        self._fts_available: bool = self._check_fts5()
        if self._fts_available:
            self._ensure_fts_index()

    @contextmanager
    def _session(self) -> Iterator[Session]:
        """Yield a session with commit/rollback handling."""
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @contextmanager
    def get_session(self) -> Iterator[Session]:
        """Public session context manager for external query use.

        Provides commit/rollback handling. Used by provenance and
        traceability modules that need direct ORM access.
        """
        with self._session() as session:
            yield session

    def signal_count(self) -> int:
        """Return number of checks in the store."""
        with self._session() as session:
            result = session.execute(
                select(func.count()).select_from(Check)
            )
            return result.scalar_one()

    def _check_fts5(self) -> bool:
        """Check if FTS5 is available via PRAGMA compile_options."""
        try:
            with self._engine.connect() as conn:
                result = conn.execute(text("PRAGMA compile_options"))
                options = [row[0] for row in result]
                available = "ENABLE_FTS5" in options
                if not available:
                    logger.info("FTS5 not available; using LIKE fallback")
                return available
        except Exception:
            logger.warning("Could not check FTS5 availability")
            return False

    def _ensure_fts_index(self) -> None:
        """Create FTS5 virtual tables if they do not exist."""
        with self._engine.connect() as conn:
            # Notes FTS (standalone, not content-synced)
            conn.execute(
                text(
                    "CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts "
                    "USING fts5(title, content, tags)"
                )
            )
            # Signals FTS (standalone, populated on search)
            conn.execute(
                text(
                    "CREATE VIRTUAL TABLE IF NOT EXISTS signals_fts "
                    "USING fts5(signal_id, name, pillar)"
                )
            )
            conn.commit()


    def query_checks(
        self,
        section: int | None = None,
        status: str | None = None,
        factor: str | None = None,
        severity: str | None = None,
        pillar: str | None = None,
        content_type: str | None = None,
        depth: int | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Filter checks by any combination of criteria.

        Supports section, status, factor, severity, pillar, and
        Phase 31 enriched fields: content_type and depth.
        """
        with self._session() as session:
            stmt = select(Check)
            if section is not None:
                stmt = stmt.where(Check.section == section)
            if status is not None:
                stmt = stmt.where(Check.status == status)
            if factor is not None:
                stmt = stmt.where(Check.scoring_factor == factor)
            if severity is not None:
                stmt = stmt.where(Check.severity == severity)
            if pillar is not None:
                stmt = stmt.where(Check.pillar == pillar)
            if content_type is not None:
                stmt = stmt.where(Check.content_type == content_type)
            if depth is not None:
                stmt = stmt.where(Check.depth == depth)
            stmt = stmt.limit(limit)
            checks = list(session.execute(stmt).scalars().all())
            return [check_to_dict(c) for c in checks]

    def get_check(self, signal_id: str) -> dict[str, Any] | None:
        """Get a single check by ID, or None if not found."""
        with self._session() as session:
            check = session.get(Check, signal_id)
            if check is None:
                return None
            return check_to_dict(check)

    def search_checks(
        self, query: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Full-text search across check names and pillars.

        Uses FTS5 BM25 ranking when available, falls back to LIKE.
        """
        from do_uw.knowledge.store_search import (
            fts_search_checks,
            like_search_checks,
        )

        with self._session() as session:
            if self._fts_available:
                return fts_search_checks(session, query, limit)
            return like_search_checks(session, query, limit)


    def query_patterns(
        self,
        category: str | None = None,
        allegation_type: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """Filter patterns by category, allegation type, or status."""
        with self._session() as session:
            stmt = select(Pattern)
            if category is not None:
                stmt = stmt.where(Pattern.category == category)
            if status is not None:
                stmt = stmt.where(Pattern.status == status)
            patterns = list(session.execute(stmt).scalars().all())
            results = [pattern_to_dict(p) for p in patterns]
            if allegation_type is not None:
                results = [
                    r
                    for r in results
                    if allegation_type
                    in r.get("allegation_types", [])
                ]
            return results


    def get_scoring_rules(
        self, factor_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Get scoring rules, optionally filtered by factor ID."""
        with self._session() as session:
            stmt = select(ScoringRule)
            if factor_id is not None:
                stmt = stmt.where(ScoringRule.factor_id == factor_id)
            rules = list(session.execute(stmt).scalars().all())
            return [scoring_rule_to_dict(r) for r in rules]


    def get_red_flags(
        self, status: str | None = None
    ) -> list[dict[str, Any]]:
        """Get red flag gates, optionally filtered by status."""
        with self._session() as session:
            stmt = select(RedFlag)
            if status is not None:
                stmt = stmt.where(RedFlag.status == status)
            flags = list(session.execute(stmt).scalars().all())
            return [red_flag_to_dict(f) for f in flags]


    def get_sector_baselines(
        self, sector_code: str | None = None
    ) -> dict[str, Any]:
        """Get sector baselines as {metric: {sector_code: data}} dict."""
        with self._session() as session:
            stmt = select(Sector)
            if sector_code is not None:
                stmt = stmt.where(Sector.sector_code == sector_code)
            sectors = list(session.execute(stmt).scalars().all())
            result: dict[str, Any] = {}
            for s in sectors:
                metric = s.metric_name
                if metric not in result:
                    result[metric] = {}
                # Parse metadata_json if present for rich data
                if s.metadata_json:
                    try:
                        parsed: Any = json.loads(s.metadata_json)
                        result[metric][s.sector_code] = parsed
                    except (json.JSONDecodeError, TypeError):
                        result[metric][s.sector_code] = s.baseline_value
                else:
                    result[metric][s.sector_code] = s.baseline_value
            return result


    def add_note(
        self,
        title: str,
        content: str,
        tags: str | None = None,
        source: str | None = None,
        signal_id: str | None = None,
    ) -> int:
        """Insert a new underwriting note. Returns the note ID."""
        from datetime import UTC, datetime

        now = datetime.now(UTC)
        note = Note(
            title=title,
            content=content,
            tags=tags,
            source=source,
            signal_id=signal_id,
            created_at=now,
            modified_at=now,
        )
        with self._session() as session:
            session.add(note)
            session.flush()
            note_id: int = note.id
        return note_id

    def search_notes(
        self, query: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Full-text search on notes.

        Uses FTS5 BM25 ranking when available, falls back to LIKE.
        """
        from do_uw.knowledge.store_search import (
            fts_search_notes,
            like_search_notes,
        )

        with self._session() as session:
            if self._fts_available:
                return fts_search_notes(session, query, limit)
            return like_search_notes(session, query, limit)


    def query_notes_by_tag(
        self, tag: str, limit: int = 1000
    ) -> list[dict[str, Any]]:
        """Get notes filtered by exact tag match.

        Args:
            tag: Tag value to filter on (exact match).
            limit: Maximum number of notes to return.

        Returns:
            List of note dicts matching the tag.
        """
        from do_uw.knowledge.store_converters import note_to_dict

        with self._session() as session:
            stmt = (
                select(Note).where(Note.tags == tag).limit(limit)
            )
            notes = list(session.execute(stmt).scalars().all())
            return [note_to_dict(n) for n in notes]

    def get_playbook(
        self, playbook_id: str
    ) -> dict[str, Any] | None:
        """Get an industry playbook by ID, or None if not found."""
        with self._session() as session:
            pb = session.get(IndustryPlaybook, playbook_id)
            if pb is None:
                return None
            return playbook_to_dict(pb)

    def get_playbook_for_sic(
        self, sic_code: str
    ) -> dict[str, Any] | None:
        """Find matching active playbook by SIC code range."""
        try:
            sic_int = int(sic_code)
        except (ValueError, TypeError):
            return None
        with self._session() as session:
            stmt = select(IndustryPlaybook).where(
                IndustryPlaybook.status == "ACTIVE"
            )
            playbooks = list(session.execute(stmt).scalars().all())
            for pb in playbooks:
                raw_ranges = pb.sic_ranges
                if not isinstance(raw_ranges, list):
                    continue
                ranges = cast(list[Any], raw_ranges)
                for entry in ranges:
                    if not isinstance(entry, dict):
                        continue
                    range_dict = cast(dict[str, Any], entry)
                    low = int(range_dict.get("low", 0))
                    high = int(range_dict.get("high", 0))
                    if low <= sic_int <= high:
                        return playbook_to_dict(pb)
            return None
