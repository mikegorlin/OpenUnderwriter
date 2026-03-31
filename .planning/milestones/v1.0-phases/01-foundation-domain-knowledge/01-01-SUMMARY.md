---
phase: 01-foundation-domain-knowledge
plan: 01
subsystem: scaffolding
tags: [python, uv, ruff, pyright, pytest, toolchain]
dependency-graph:
  requires: []
  provides: [python-package, cli-entry-point, directory-structure, dev-tooling, arch05-enforcement]
  affects: [01-02, 01-03, all-subsequent-phases]
tech-stack:
  added: [pydantic-v2, typer, rich, httpx, ruff, pyright, pytest, pytest-asyncio, hatchling]
  patterns: [src-layout, pep561-py-typed, strict-type-checking]
key-files:
  created:
    - pyproject.toml
    - uv.lock
    - .python-version
    - .gitignore
    - ruff.toml
    - README.md
    - src/do_uw/__init__.py
    - src/do_uw/py.typed
    - src/do_uw/cli.py
    - src/do_uw/models/__init__.py
    - src/do_uw/stages/__init__.py
    - src/do_uw/stages/resolve/__init__.py
    - src/do_uw/stages/acquire/__init__.py
    - src/do_uw/stages/extract/__init__.py
    - src/do_uw/stages/analyze/__init__.py
    - src/do_uw/stages/score/__init__.py
    - src/do_uw/stages/benchmark/__init__.py
    - src/do_uw/stages/render/__init__.py
    - src/do_uw/config/__init__.py
    - src/do_uw/cache/__init__.py
    - tests/__init__.py
    - tests/conftest.py
    - tests/models/__init__.py
    - tests/config/__init__.py
    - scripts/check_file_lengths.py
  modified: []
decisions:
  - id: d-01-01-01
    decision: "Used hatchling build backend with src/ layout per plan specification"
    reason: "Standard Python packaging with clear src/package separation"
  - id: d-01-01-02
    decision: "pyright strict mode configured in pyproject.toml rather than separate pyrightconfig.json"
    reason: "Single config file reduces scatter; pyproject.toml is the standard location"
  - id: d-01-01-03
    decision: "ruff.toml as separate file from pyproject.toml"
    reason: "Clarity per plan specification; ruff config is substantial enough to warrant its own file"
metrics:
  duration: "2m 37s"
  completed: "2026-02-07"
---

# Phase 1 Plan 1: Project Scaffolding & Dev Tooling Summary

**One-liner:** Python 3.12 package with uv, hatchling build, 7-stage pipeline directory tree, strict pyright/ruff/pytest toolchain, and ARCH-05 500-line enforcement script.

## What Was Done

### Task 1: Initialize uv project with all dependencies and directory structure
- Initialized project with `uv init --name do-uw --python 3.12 --package --lib`
- Configured `pyproject.toml` with hatchling build backend and src/ layout
- Added runtime dependencies: pydantic>=2.10, typer>=0.15, rich>=13.0, httpx>=0.28
- Added dev dependencies: ruff, pyright, pytest, pytest-asyncio
- Created full directory tree matching CLAUDE.md specification:
  - `src/do_uw/` with models/, stages/ (7 pipeline stages), config/, cache/
  - `tests/` with models/, config/
- Created minimal CLI entry point (`do-uw analyze <ticker>`)
- Created PEP 561 `py.typed` marker
- Created `.gitignore` with Python/IDE/cache entries
- **Commit:** `77aad7c`

### Task 2: Configure dev tooling and ARCH-05 file-length enforcement
- Created `ruff.toml` with py312 target, line-length 99, comprehensive rule selection (E, F, B, I, UP, S, C4, RUF)
- Configured pyright strict mode in `pyproject.toml`
- Created `scripts/check_file_lengths.py` enforcing ARCH-05 500-line limit with 400-line warnings
- All quality gates pass: ruff check, ruff format, pyright strict, file-length check, pytest discovery
- **Commit:** `b410cf5`

## Verification Results

| Check | Result |
|-------|--------|
| `uv sync` | 28 packages resolved, 27 installed |
| `uv run do-uw --help` | Shows analyze command with ticker argument |
| `from do_uw import __version__` | Returns "0.1.0" |
| `ruff check src/ tests/` | All checks passed |
| `ruff format --check src/ tests/` | 17 files already formatted |
| `pyright src/` | 0 errors, 0 warnings, 0 informations |
| `check_file_lengths.py` | All files within 500 line limit |
| `pytest --co` | Test discovery works (0 tests, expected) |

## Deviations from Plan

None -- plan executed exactly as written.

## Decisions Made

1. **hatchling build backend** -- Used per plan specification, replacing the uv_build backend that `uv init` defaults to.
2. **pyright config in pyproject.toml** -- Co-located with other tool config rather than separate pyrightconfig.json.
3. **ruff.toml separate file** -- Keeps ruff's substantial config readable and distinct from package metadata.

## Next Phase Readiness

Plan 01-02 can proceed immediately. The package skeleton provides:
- Working `uv run` environment with all dependencies
- All directories ready for Pydantic models and config files
- Strict type checking and linting enforced from the start
- Test infrastructure ready for TDD workflow
