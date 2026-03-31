"""Shared test fixtures for do-uw tests.

All shared fixtures should be defined here. Pytest automatically discovers
this file and makes its fixtures available to all tests.
"""

import os
from pathlib import Path
from tempfile import mkdtemp
from unittest.mock import patch

import pytest

# Set env var BEFORE any test modules are imported/collected.
# This ensures get_brain_db_path() returns a safe path even if called
# during module-level imports or fixture setup.
_BRAIN_TEST_DIR = mkdtemp(prefix="brain_test_")
os.environ["DO_UW_BRAIN_DB_PATH"] = os.path.join(_BRAIN_TEST_DIR, "brain_test.duckdb")


@pytest.fixture()
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture()
def fixtures_dir() -> Path:
    """Return the test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def _guard_brain_db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> object:  # type: ignore[misc]
    """Prevent tests from creating MagicMock junk files in the project root.

    Uses BOTH env var (catches all callers regardless of import style) and
    module patch (catches code that already imported the function reference).
    Each test gets its own isolated path via tmp_path.
    """
    safe_db = tmp_path / "brain_test.duckdb"
    monkeypatch.setenv("DO_UW_BRAIN_DB_PATH", str(safe_db))
    with patch(
        "do_uw.brain.brain_schema.get_brain_db_path", return_value=safe_db
    ) as m:
        yield m
