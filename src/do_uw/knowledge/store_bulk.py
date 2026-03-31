"""Bulk insert, metadata, and check feedback methods for KnowledgeStore.

Provides the KnowledgeStoreBulkMixin class with write operations:
bulk inserts for checks/patterns/scoring rules/red flags/sectors,
metadata key-value storage, and check feedback loop (CheckRun
recording and stats queries).

Extracted from store.py for 500-line compliance.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from do_uw.knowledge.models import (
    Check,
    CheckRun,
    Note,
    Pattern,
    RedFlag,
    ScoringRule,
    Sector,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class KnowledgeStoreBulkMixin:
    """Mixin providing bulk write and feedback loop methods.

    Requires the consuming class to define ``_session()`` returning
    a context manager that yields a SQLAlchemy ``Session``.
    """

    @contextmanager
    def _session(self) -> Iterator[Session]:
        """Declared for type-checking; implemented in KnowledgeStore.

        This abstract stub exists only so type-checkers understand the mixin's
        dependency on _session(). KnowledgeStore always overrides this method;
        calling it directly on KnowledgeStoreBulkMixin alone is a programmer
        error. Do not add callers that bypass KnowledgeStore.
        """
        raise NotImplementedError(  # pragma: no cover
            "KnowledgeStoreBulkMixin._session() is an abstract stub. "
            "Use KnowledgeStore (which provides a real _session() implementation) "
            "instead of instantiating KnowledgeStoreBulkMixin directly."
        )
        yield  # type: ignore[misc]  # pragma: no cover

    # ------------------------------------------------------------------
    # Bulk insert operations
    # ------------------------------------------------------------------

    def bulk_insert_checks(self, checks: list[Check]) -> int:
        """Upsert multiple checks (idempotent). Returns count processed."""
        with self._session() as session:
            for check in checks:
                session.merge(check)
            session.flush()
        return len(checks)

    def bulk_insert_patterns(self, patterns: list[Pattern]) -> int:
        """Upsert multiple patterns (idempotent). Returns count processed."""
        with self._session() as session:
            for pattern in patterns:
                session.merge(pattern)
            session.flush()
        return len(patterns)

    def bulk_insert_scoring_rules(self, rules: list[ScoringRule]) -> int:
        """Upsert multiple scoring rules (idempotent). Returns count processed."""
        with self._session() as session:
            for rule in rules:
                session.merge(rule)
            session.flush()
        return len(rules)

    def bulk_insert_red_flags(self, flags: list[RedFlag]) -> int:
        """Upsert multiple red flags (idempotent). Returns count processed."""
        with self._session() as session:
            for flag in flags:
                session.merge(flag)
            session.flush()
        return len(flags)

    def bulk_insert_sectors(self, sectors: list[Sector]) -> int:
        """Upsert multiple sector baselines (idempotent).

        Sectors use auto-increment PK so we check for existing
        (sector_code, metric_name) pairs and update or insert.
        Returns count of sectors processed.
        """
        with self._session() as session:
            for sector in sectors:
                existing = (
                    session.execute(
                        select(Sector).where(
                            Sector.sector_code == sector.sector_code,
                            Sector.metric_name == sector.metric_name,
                        )
                    )
                    .scalars()
                    .first()
                )
                if existing is not None:
                    # Update existing record in place
                    existing.baseline_value = sector.baseline_value
                    existing.metadata_json = sector.metadata_json
                else:
                    session.add(sector)
            session.flush()
        return len(sectors)

    # ------------------------------------------------------------------
    # Metadata key-value storage
    # ------------------------------------------------------------------

    def store_metadata(self, key: str, data: dict[str, Any]) -> None:
        """Store raw JSON metadata for backward-compat reconstruction."""
        from datetime import UTC, datetime

        now = datetime.now(UTC)
        note = Note(
            title=f"__metadata__{key}",
            content=json.dumps(data),
            tags="metadata",
            source="BRAIN_MIGRATION",
            created_at=now,
            modified_at=now,
        )
        with self._session() as session:
            # Remove existing metadata note if any
            existing = (
                session.execute(
                    select(Note).where(
                        Note.title == f"__metadata__{key}"
                    )
                )
                .scalars()
                .first()
            )
            if existing is not None:
                session.delete(existing)
                session.flush()
            session.add(note)
            session.flush()

    def get_metadata(self, key: str) -> dict[str, Any] | None:
        """Retrieve stored metadata by key, or None if not found."""
        with self._session() as session:
            note = (
                session.execute(
                    select(Note).where(
                        Note.title == f"__metadata__{key}"
                    )
                )
                .scalars()
                .first()
            )
            if note is None:
                return None
            result: dict[str, Any] = json.loads(note.content)
            return result

    # ------------------------------------------------------------------
    # Check feedback loop methods (Phase 30-02)
    # ------------------------------------------------------------------

    def write_signal_runs(self, runs: list[CheckRun]) -> int:
        """Batch INSERT per-check results from a pipeline run.

        Always inserts new rows (never upserts). Each ANALYZE execution
        produces a fresh set of CheckRun records.

        Args:
            runs: List of CheckRun ORM objects to insert.

        Returns:
            Count of rows inserted.
        """
        if not runs:
            return 0
        with self._session() as session:
            session.add_all(runs)
            session.flush()
        return len(runs)

    def get_check_stats(
        self,
        signal_id: str | None = None,
        min_runs: int = 1,
    ) -> list[dict[str, Any]]:
        """Compute fire rate and skip rate per check across all runs.

        Groups check_runs by signal_id and status, computes counts
        and rates. Filters to checks with >= min_runs evaluations.

        Args:
            signal_id: Optional filter to a single check.
            min_runs: Minimum number of runs to include.

        Returns:
            List of dicts with keys: signal_id, total_runs, fired,
            clear, skipped, info, fire_rate, skip_rate.
        """
        with self._session() as session:
            stmt = select(
                CheckRun.signal_id,
                CheckRun.status,
                func.count().label("cnt"),
            ).group_by(CheckRun.signal_id, CheckRun.status)

            if signal_id is not None:
                stmt = stmt.where(CheckRun.signal_id == signal_id)

            rows = list(session.execute(stmt).all())

        # Aggregate per signal_id
        agg: dict[str, dict[str, int]] = {}
        for cid, status, cnt in rows:
            if cid not in agg:
                agg[cid] = {
                    "fired": 0,
                    "clear": 0,
                    "skipped": 0,
                    "info": 0,
                }
            status_key = status.lower()
            if status_key == "triggered":
                agg[cid]["fired"] += cnt
            elif status_key in agg[cid]:
                agg[cid][status_key] += cnt

        results: list[dict[str, Any]] = []
        for cid, counts in sorted(agg.items()):
            total = (
                counts["fired"]
                + counts["clear"]
                + counts["skipped"]
                + counts["info"]
            )
            if total < min_runs:
                continue
            results.append({
                "signal_id": cid,
                "total_runs": total,
                "fired": counts["fired"],
                "clear": counts["clear"],
                "skipped": counts["skipped"],
                "info": counts["info"],
                "fire_rate": counts["fired"] / total if total else 0.0,
                "skip_rate": counts["skipped"] / total if total else 0.0,
            })
        return results

    def get_dead_checks(
        self, min_runs: int = 3
    ) -> list[dict[str, Any]]:
        """Find checks that never fire (deprecation candidates).

        Returns checks evaluated >= min_runs times but with
        fire_rate == 0.0. These may need threshold recalibration
        or deprecation.

        Args:
            min_runs: Minimum number of runs to consider.

        Returns:
            List of dicts matching get_check_stats format,
            filtered to fire_rate == 0.0.
        """
        all_stats = self.get_check_stats(min_runs=min_runs)
        return [s for s in all_stats if s["fire_rate"] == 0.0]
