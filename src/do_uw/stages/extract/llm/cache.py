"""SQLite-backed cache for LLM extraction results.

Stores extracted JSON keyed by (accession_number, form_type, schema_version)
to prevent re-extraction of the same filing with the same schema.
Uses the same database file as AnalysisCache (.cache/analysis.db).

Follows the same initialization pattern as sqlite_cache.py:
WAL journal mode, check_same_thread=False, parent directory auto-creation.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

# Default cache database path (shared with AnalysisCache)
DEFAULT_DB_PATH = Path(".cache/analysis.db")


class ExtractionCache:
    """SQLite-backed cache for LLM extraction results.

    Table: extraction_cache
    Primary key: (accession_number, form_type, schema_version)
    Also stores token counts, estimated cost, and model ID for auditing.
    """

    def __init__(self, db_path: Path = DEFAULT_DB_PATH) -> None:
        """Initialize cache, creating table if needed.

        Args:
            db_path: Path to SQLite database file.
        """
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None
        self._lock = threading.Lock()
        self._initialize()

    def _initialize(self) -> None:
        """Create database and table if they don't exist."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS extraction_cache (
                accession_number TEXT NOT NULL,
                form_type TEXT NOT NULL,
                schema_version TEXT NOT NULL,
                extracted_json TEXT NOT NULL,
                input_tokens INTEGER NOT NULL DEFAULT 0,
                output_tokens INTEGER NOT NULL DEFAULT 0,
                estimated_cost_usd REAL NOT NULL DEFAULT 0.0,
                model_id TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL,
                PRIMARY KEY (accession_number, form_type, schema_version)
            )
            """
        )
        self._conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_extraction_form
            ON extraction_cache (form_type)
            """
        )
        self._conn.commit()

    def get(
        self,
        accession: str,
        form_type: str,
        schema_version: str,
    ) -> str | None:
        """Get cached extraction result.

        Args:
            accession: SEC accession number.
            form_type: Filing form type (e.g., "10-K").
            schema_version: Hash of the extraction schema.

        Returns:
            Cached JSON string, or None if not cached.
        """
        with self._lock:
            if self._conn is None:
                return None
            cursor = self._conn.execute(
                "SELECT extracted_json FROM extraction_cache "
                "WHERE accession_number = ? AND form_type = ? "
                "AND schema_version = ?",
                (accession, form_type, schema_version),
            )
            row = cursor.fetchone()
            return str(row[0]) if row else None

    def set(
        self,
        accession: str,
        form_type: str,
        schema_version: str,
        extracted_json: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = 0.0,
        model_id: str = "",
    ) -> None:
        """Store extraction result in cache.

        Uses INSERT OR REPLACE so re-extraction overwrites stale data.

        Args:
            accession: SEC accession number.
            form_type: Filing form type.
            schema_version: Hash of the extraction schema.
            extracted_json: Serialized extraction result.
            input_tokens: Number of input tokens used.
            output_tokens: Number of output tokens used.
            cost_usd: Estimated cost in USD.
            model_id: Model identifier (e.g., "openai/deepseek-chat").
        """
        with self._lock:
            if self._conn is None:
                return
            self._conn.execute(
                "INSERT OR REPLACE INTO extraction_cache VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    accession,
                    form_type,
                    schema_version,
                    extracted_json,
                    input_tokens,
                    output_tokens,
                    cost_usd,
                    model_id,
                    time.time(),
                ),
            )
            self._conn.commit()

    def get_company_cost(self, accessions: list[str]) -> float:
        """Get total extraction cost for a set of accession numbers.

        Args:
            accessions: List of SEC accession numbers for the company.

        Returns:
            Total estimated cost in USD across all cached extractions.
        """
        if self._conn is None or not accessions:
            return 0.0
        placeholders = ",".join("?" * len(accessions))
        cursor = self._conn.execute(
            "SELECT SUM(estimated_cost_usd) FROM extraction_cache "  # noqa: S608
            f"WHERE accession_number IN ({placeholders})",
            accessions,
        )
        row = cursor.fetchone()
        return float(row[0]) if row and row[0] else 0.0

    def get_costs_by_filing_type(self, accessions: list[str]) -> dict[str, float]:
        """Get per-filing-type cost breakdown for given accessions.

        Args:
            accessions: List of SEC accession numbers.

        Returns:
            Dict mapping form_type to total cost in USD.
        """
        if self._conn is None or not accessions:
            return {}
        placeholders = ",".join("?" * len(accessions))
        cursor = self._conn.execute(
            "SELECT form_type, SUM(estimated_cost_usd) "  # noqa: S608
            f"FROM extraction_cache "
            f"WHERE accession_number IN ({placeholders}) "
            "GROUP BY form_type",
            accessions,
        )
        by_type: dict[str, float] = {}
        for row in cursor.fetchall():
            by_type[str(row[0])] = float(row[1]) if row[1] else 0.0
        return by_type

    def get_stats(self) -> dict[str, Any]:
        """Return cache statistics.

        Returns:
            Dict with total entries, total cost, total tokens,
            and entries by form type.
        """
        if self._conn is None:
            return {
                "total_entries": 0,
                "total_cost_usd": 0.0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "by_form_type": {},
            }

        cursor = self._conn.execute(
            "SELECT COUNT(*), "
            "COALESCE(SUM(estimated_cost_usd), 0), "
            "COALESCE(SUM(input_tokens), 0), "
            "COALESCE(SUM(output_tokens), 0) "
            "FROM extraction_cache"
        )
        row = cursor.fetchone()
        total = int(row[0]) if row else 0
        cost = float(row[1]) if row else 0.0
        inp = int(row[2]) if row else 0
        out = int(row[3]) if row else 0

        # Breakdown by form type
        cursor2 = self._conn.execute(
            "SELECT form_type, COUNT(*), "
            "COALESCE(SUM(estimated_cost_usd), 0) "
            "FROM extraction_cache GROUP BY form_type"
        )
        by_form: dict[str, dict[str, float | int]] = {}
        for ft_row in cursor2.fetchall():
            by_form[str(ft_row[0])] = {
                "count": int(ft_row[1]),
                "cost_usd": float(ft_row[2]),
            }

        return {
            "total_entries": total,
            "total_cost_usd": cost,
            "total_input_tokens": inp,
            "total_output_tokens": out,
            "by_form_type": by_form,
        }

    def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
