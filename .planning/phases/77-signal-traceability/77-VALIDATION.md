---
phase: 77
slug: signal-traceability
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-07
---

# Phase 77 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `uv run pytest tests/brain/test_chain_validator.py -x -q` |
| **Full suite command** | `uv run pytest tests/brain/test_chain_validator.py tests/test_cli_brain_trace.py -x -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/brain/test_chain_validator.py -x -q`
- **After every plan wave:** Run `uv run pytest tests/brain/test_chain_validator.py tests/test_cli_brain_trace.py -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 77-01-01 | 01 | 1 | TRACE-01 | unit | `uv run pytest tests/brain/test_chain_validator.py -x -q` | ❌ W0 | ⬜ pending |
| 77-01-02 | 01 | 1 | TRACE-01 | unit | `uv run pytest tests/brain/test_chain_validator.py -x -q` | ❌ W0 | ⬜ pending |
| 77-02-01 | 02 | 2 | TRACE-01 | integration | `uv run pytest tests/test_cli_brain_trace.py -x -q` | ❌ W0 | ⬜ pending |
| 77-02-02 | 02 | 2 | TRACE-02 | integration | `uv run pytest tests/test_cli_brain_trace.py -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/brain/test_chain_validator.py` — stubs for TRACE-01 (chain validation logic)
- [ ] `tests/test_cli_brain_trace.py` — stubs for TRACE-01, TRACE-02 (CLI command tests)

*Existing test infrastructure (pytest, conftest) covers framework needs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CLI Rich formatting | TRACE-01 | Visual layout verification | Run `do-uw brain trace-chain FIN.CR` and verify vertical chain view renders correctly |
| Full audit table readability | TRACE-01 | Visual density check | Run `do-uw brain trace-chain` and verify 400+ signals table is scannable |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
