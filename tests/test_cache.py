"""Tests for SQLite cache layer.

Tests initialization, get/set, TTL expiration, persistence across
instances, stats, and cleanup.
"""

from __future__ import annotations

import time
from pathlib import Path

from do_uw.cache import AnalysisCache


class TestCacheInit:
    """Test cache initialization."""

    def test_cache_creates_database(self, tmp_path: Path) -> None:
        """Cache creates the database file on init."""
        db_path = tmp_path / "test.db"
        cache = AnalysisCache(db_path=db_path)
        assert db_path.exists()
        cache.close()

    def test_cache_creates_parent_directories(self, tmp_path: Path) -> None:
        """Cache creates parent directories if they don't exist."""
        db_path = tmp_path / "nested" / "deep" / "cache.db"
        cache = AnalysisCache(db_path=db_path)
        assert db_path.exists()
        cache.close()


class TestCacheOperations:
    """Test get/set/delete operations."""

    def test_set_and_get(self, tmp_path: Path) -> None:
        """Values can be stored and retrieved."""
        db_path = tmp_path / "test.db"
        cache = AnalysisCache(db_path=db_path)

        cache.set("ticker:AAPL", {"name": "Apple"}, "test")
        result = cache.get("ticker:AAPL")
        assert result == {"name": "Apple"}
        cache.close()

    def test_get_missing_key_returns_none(self, tmp_path: Path) -> None:
        """Getting a non-existent key returns None."""
        db_path = tmp_path / "test.db"
        cache = AnalysisCache(db_path=db_path)
        assert cache.get("nonexistent") is None
        cache.close()

    def test_delete_existing_key(self, tmp_path: Path) -> None:
        """Deleting an existing key returns True."""
        db_path = tmp_path / "test.db"
        cache = AnalysisCache(db_path=db_path)
        cache.set("key1", "value1", "test")
        assert cache.delete("key1") is True
        assert cache.get("key1") is None
        cache.close()

    def test_delete_missing_key(self, tmp_path: Path) -> None:
        """Deleting a non-existent key returns False."""
        db_path = tmp_path / "test.db"
        cache = AnalysisCache(db_path=db_path)
        assert cache.delete("missing") is False
        cache.close()


class TestCachePersistence:
    """Test cache persists across instances."""

    def test_cache_persistence(self, tmp_path: Path) -> None:
        """Data persists across separate cache instances."""
        db_path = tmp_path / "persist.db"

        # Write with first instance
        cache1 = AnalysisCache(db_path=db_path)
        cache1.set("key1", "val1", "test")
        cache1.close()

        # Read with second instance
        cache2 = AnalysisCache(db_path=db_path)
        assert cache2.get("key1") == "val1"
        cache2.close()


class TestCacheTTL:
    """Test cache TTL expiration."""

    def test_expired_entry_returns_none(self, tmp_path: Path) -> None:
        """Expired entries return None and are cleaned up."""
        db_path = tmp_path / "ttl.db"
        cache = AnalysisCache(db_path=db_path)

        # Set with very short TTL
        cache.set("short", "value", "test", ttl=1)
        assert cache.get("short") == "value"

        # Wait for expiration
        time.sleep(1.1)
        assert cache.get("short") is None
        cache.close()


class TestCacheStats:
    """Test cache statistics and cleanup."""

    def test_stats_counts(self, tmp_path: Path) -> None:
        """Stats report correct total and valid counts."""
        db_path = tmp_path / "stats.db"
        cache = AnalysisCache(db_path=db_path)

        cache.set("a", 1, "test")
        cache.set("b", 2, "test")

        stats = cache.stats()
        assert stats["total"] == 2
        assert stats["valid"] == 2
        assert stats["expired"] == 0
        cache.close()

    def test_clear_removes_all(self, tmp_path: Path) -> None:
        """Clear removes all entries."""
        db_path = tmp_path / "clear.db"
        cache = AnalysisCache(db_path=db_path)

        cache.set("a", 1, "test")
        cache.set("b", 2, "test")
        removed = cache.clear()
        assert removed == 2
        assert cache.stats()["total"] == 0
        cache.close()

    def test_cleanup_expired(self, tmp_path: Path) -> None:
        """cleanup_expired removes only expired entries."""
        db_path = tmp_path / "cleanup.db"
        cache = AnalysisCache(db_path=db_path)

        cache.set("short", "x", "test", ttl=1)
        cache.set("long", "y", "test", ttl=3600)

        time.sleep(1.1)
        removed = cache.cleanup_expired()
        assert removed == 1
        assert cache.get("long") == "y"
        cache.close()
