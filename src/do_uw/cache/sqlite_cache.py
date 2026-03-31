"""SQLite-based cache for analysis data.

Provides persistent key-value storage with TTL expiration.
Per CLAUDE.md: SQLite for local data cache (ARCH-04).

The cache stores serialized values with metadata (source, created_at,
expires_at) and supports automatic expiration on read.
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any

# Default TTL: 7 days in seconds
DEFAULT_TTL_SECONDS = 7 * 24 * 60 * 60

# Default cache database path
DEFAULT_DB_PATH = Path(".cache/analysis.db")


class AnalysisCache:
    """SQLite-backed cache with TTL expiration.

    Thread-safe for single-writer, multiple-reader access.
    Values are JSON-serialized for storage.
    """

    def __init__(
        self,
        db_path: Path = DEFAULT_DB_PATH,
        default_ttl: int = DEFAULT_TTL_SECONDS,
    ) -> None:
        self._db_path = db_path
        self._default_ttl = default_ttl
        self._conn: sqlite3.Connection | None = None
        self._initialize()

    def _initialize(self) -> None:
        """Create database and table if they don't exist."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(
            str(self._db_path),
            check_same_thread=False,
        )
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cache_entries (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL,
                expires_at REAL NOT NULL
            )
            """
        )
        self._conn.commit()

    @property
    def db_path(self) -> Path:
        """Return the database file path."""
        return self._db_path

    def set(
        self,
        key: str,
        value: Any,
        source: str,
        ttl: int | None = None,
    ) -> None:
        """Store a value in the cache.

        Args:
            key: Cache key (unique identifier).
            value: Value to store (must be JSON-serializable).
            source: Data source attribution.
            ttl: Time-to-live in seconds. Uses default if not provided.
        """
        if self._conn is None:
            msg = "Cache not initialized"
            raise RuntimeError(msg)

        ttl_seconds = ttl if ttl is not None else self._default_ttl
        now = time.time()
        expires = now + ttl_seconds
        serialized = json.dumps(value)

        self._conn.execute(
            """
            INSERT OR REPLACE INTO cache_entries
                (key, value, source, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (key, serialized, source, now, expires),
        )
        self._conn.commit()

    def get(self, key: str) -> Any | None:
        """Retrieve a value from the cache.

        Returns None if key doesn't exist or has expired.
        Expired entries are deleted on access.
        """
        if self._conn is None:
            msg = "Cache not initialized"
            raise RuntimeError(msg)

        cursor = self._conn.execute(
            "SELECT value, expires_at FROM cache_entries WHERE key = ?",
            (key,),
        )
        row = cursor.fetchone()
        if row is None:
            return None

        value_str: str = row[0]
        expires_at: float = row[1]

        if time.time() > expires_at:
            self.delete(key)
            return None

        return json.loads(value_str)

    def delete(self, key: str) -> bool:
        """Delete a cache entry.

        Returns True if entry existed and was deleted.
        """
        if self._conn is None:
            msg = "Cache not initialized"
            raise RuntimeError(msg)

        cursor = self._conn.execute(
            "DELETE FROM cache_entries WHERE key = ?", (key,)
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def clear(self) -> int:
        """Delete all cache entries.

        Returns the number of entries deleted.
        """
        if self._conn is None:
            msg = "Cache not initialized"
            raise RuntimeError(msg)

        cursor = self._conn.execute("DELETE FROM cache_entries")
        self._conn.commit()
        return cursor.rowcount

    def stats(self) -> dict[str, int]:
        """Return cache statistics.

        Returns dict with 'total', 'expired', and 'valid' counts.
        """
        if self._conn is None:
            msg = "Cache not initialized"
            raise RuntimeError(msg)

        now = time.time()
        cursor = self._conn.execute(
            "SELECT COUNT(*) FROM cache_entries"
        )
        total: int = cursor.fetchone()[0]

        cursor = self._conn.execute(
            "SELECT COUNT(*) FROM cache_entries WHERE expires_at < ?",
            (now,),
        )
        expired: int = cursor.fetchone()[0]

        return {
            "total": total,
            "expired": expired,
            "valid": total - expired,
        }

    def cleanup_expired(self) -> int:
        """Remove all expired entries.

        Returns the number of entries removed.
        """
        if self._conn is None:
            msg = "Cache not initialized"
            raise RuntimeError(msg)

        now = time.time()
        cursor = self._conn.execute(
            "DELETE FROM cache_entries WHERE expires_at < ?", (now,)
        )
        self._conn.commit()
        return cursor.rowcount

    def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
