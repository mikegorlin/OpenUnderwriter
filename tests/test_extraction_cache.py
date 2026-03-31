"""Tests for ExtractionCache SQLite table.

Validates cache operations: create, set/get round-trip, cache miss,
key uniqueness by schema_version, and company cost aggregation.
"""

from __future__ import annotations

from pathlib import Path

from do_uw.stages.extract.llm.cache import ExtractionCache


def test_create_table(tmp_path: Path) -> None:
    """Cache creates table on initialization."""
    db = tmp_path / "test.db"
    cache = ExtractionCache(db_path=db)
    assert db.exists()
    stats = cache.get_stats()
    assert stats["total_entries"] == 0
    cache.close()


def test_set_get_roundtrip(tmp_path: Path) -> None:
    """Stored extraction can be retrieved."""
    cache = ExtractionCache(db_path=tmp_path / "test.db")
    cache.set(
        "0001-23-456789",
        "10-K",
        "abc123",
        '{"field": "value"}',
        input_tokens=1000,
        output_tokens=200,
        cost_usd=0.002,
        model_id="anthropic/claude-haiku-4-5",
    )
    result = cache.get("0001-23-456789", "10-K", "abc123")
    assert result == '{"field": "value"}'
    cache.close()


def test_cache_miss_returns_none(tmp_path: Path) -> None:
    """Non-existent key returns None."""
    cache = ExtractionCache(db_path=tmp_path / "test.db")
    result = cache.get("nonexistent", "10-K", "v1")
    assert result is None
    cache.close()


def test_different_schema_version_different_result(
    tmp_path: Path,
) -> None:
    """Same accession + form_type with different schema_version are separate entries."""
    cache = ExtractionCache(db_path=tmp_path / "test.db")

    cache.set("acc1", "10-K", "v1", '{"version": 1}')
    cache.set("acc1", "10-K", "v2", '{"version": 2}')

    r1 = cache.get("acc1", "10-K", "v1")
    r2 = cache.get("acc1", "10-K", "v2")

    assert r1 == '{"version": 1}'
    assert r2 == '{"version": 2}'
    cache.close()


def test_upsert_overwrites(tmp_path: Path) -> None:
    """Setting same key again overwrites the value."""
    cache = ExtractionCache(db_path=tmp_path / "test.db")

    cache.set("acc1", "10-K", "v1", '{"old": true}')
    cache.set("acc1", "10-K", "v1", '{"new": true}')

    result = cache.get("acc1", "10-K", "v1")
    assert result == '{"new": true}'
    cache.close()


def test_get_company_cost_aggregation(tmp_path: Path) -> None:
    """Company cost sums across multiple accessions."""
    cache = ExtractionCache(db_path=tmp_path / "test.db")

    cache.set("acc1", "10-K", "v1", "{}", cost_usd=0.10)
    cache.set("acc2", "DEF 14A", "v1", "{}", cost_usd=0.05)
    cache.set("acc3", "10-Q", "v1", "{}", cost_usd=0.03)
    # Different company -- should not be included
    cache.set("other", "10-K", "v1", "{}", cost_usd=0.99)

    cost = cache.get_company_cost(["acc1", "acc2", "acc3"])
    assert abs(cost - 0.18) < 0.001
    cache.close()


def test_get_company_cost_empty_list(tmp_path: Path) -> None:
    """Empty accession list returns zero cost."""
    cache = ExtractionCache(db_path=tmp_path / "test.db")
    assert cache.get_company_cost([]) == 0.0
    cache.close()


def test_get_stats(tmp_path: Path) -> None:
    """Stats return entry counts and cost breakdown by form type."""
    cache = ExtractionCache(db_path=tmp_path / "test.db")

    cache.set(
        "acc1", "10-K", "v1", "{}",
        input_tokens=1000, output_tokens=200, cost_usd=0.002,
    )
    cache.set(
        "acc2", "10-K", "v1", "{}",
        input_tokens=2000, output_tokens=400, cost_usd=0.004,
    )
    cache.set(
        "acc3", "DEF 14A", "v1", "{}",
        input_tokens=500, output_tokens=100, cost_usd=0.001,
    )

    stats = cache.get_stats()
    assert stats["total_entries"] == 3
    assert abs(stats["total_cost_usd"] - 0.007) < 0.0001
    assert stats["total_input_tokens"] == 3500
    assert stats["total_output_tokens"] == 700
    assert "10-K" in stats["by_form_type"]
    assert stats["by_form_type"]["10-K"]["count"] == 2
    cache.close()


def test_parent_directory_created(tmp_path: Path) -> None:
    """Cache creates parent directories if they don't exist."""
    db = tmp_path / "nested" / "dir" / "test.db"
    cache = ExtractionCache(db_path=db)
    assert db.exists()
    cache.close()
