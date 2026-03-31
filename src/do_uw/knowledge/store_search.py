"""FTS5 and LIKE search implementations for the knowledge store.

Provides full-text search with FTS5 BM25 ranking when available,
and LIKE-based fallback search. Extracted from store.py for
500-line compliance.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from do_uw.knowledge.models import Check, Note
from do_uw.knowledge.store_converters import check_to_dict, note_to_dict

logger = logging.getLogger(__name__)


def fts_search_checks(
    session: Session, query: str, limit: int
) -> list[dict[str, Any]]:
    """FTS5 search on signals_fts virtual table."""
    rebuild_signals_fts(session)
    sql = text(
        "SELECT signal_id FROM signals_fts "
        "WHERE signals_fts MATCH :query "
        "ORDER BY rank LIMIT :limit"
    )
    result = session.execute(sql, {"query": query, "limit": limit})
    signal_ids = [row[0] for row in result]
    if not signal_ids:
        return []
    results: list[dict[str, Any]] = []
    for cid in signal_ids:
        check = session.get(Check, cid)
        if check is not None:
            results.append(check_to_dict(check))
    return results


def rebuild_signals_fts(session: Session) -> None:
    """Rebuild FTS index from current signals data."""
    try:
        session.execute(text("DELETE FROM signals_fts"))
        session.execute(
            text(
                "INSERT INTO signals_fts(signal_id, name, pillar) "
                "SELECT id, name, pillar FROM signals"
            )
        )
    except Exception:
        logger.debug("Could not rebuild signals FTS index")


# Backward-compat alias
rebuild_checks_fts = rebuild_signals_fts


def like_search_checks(
    session: Session, query: str, limit: int
) -> list[dict[str, Any]]:
    """LIKE-based fallback search on checks."""
    pattern = f"%{query}%"
    stmt = (
        select(Check)
        .where(Check.name.ilike(pattern) | Check.pillar.ilike(pattern))
        .limit(limit)
    )
    checks = list(session.execute(stmt).scalars().all())
    return [check_to_dict(c) for c in checks]


def fts_search_notes(
    session: Session, query: str, limit: int
) -> list[dict[str, Any]]:
    """FTS5 search on notes_fts virtual table."""
    rebuild_notes_fts(session)
    sql = text(
        "SELECT rowid FROM notes_fts "
        "WHERE notes_fts MATCH :query "
        "ORDER BY rank LIMIT :limit"
    )
    result = session.execute(sql, {"query": query, "limit": limit})
    rowids = [row[0] for row in result]
    if not rowids:
        return []
    results: list[dict[str, Any]] = []
    for rid in rowids:
        note = session.get(Note, rid)
        if note is not None:
            results.append(note_to_dict(note))
    return results


def rebuild_notes_fts(session: Session) -> None:
    """Rebuild FTS index from current notes data."""
    try:
        session.execute(text("DELETE FROM notes_fts"))
        session.execute(
            text(
                "INSERT INTO notes_fts(rowid, title, content, tags) "
                "SELECT id, title, content, COALESCE(tags, '') "
                "FROM notes WHERE title NOT LIKE '__metadata__%'"
            )
        )
    except Exception:
        logger.debug("Could not rebuild notes FTS index")


def like_search_notes(
    session: Session, query: str, limit: int
) -> list[dict[str, Any]]:
    """LIKE-based fallback search on notes."""
    pattern = f"%{query}%"
    stmt = (
        select(Note)
        .where(
            Note.title.ilike(pattern)
            | Note.content.ilike(pattern)
            | Note.tags.ilike(pattern)
        )
        .limit(limit)
    )
    notes = list(session.execute(stmt).scalars().all())
    return [note_to_dict(n) for n in notes]
