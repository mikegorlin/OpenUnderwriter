---
phase: 115
slug: contract-enforcement-traceability-gate
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-18
---

# Phase 115 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `uv run pytest tests/brain/ tests/stages/analyze/ -x -q` |
| **Full suite command** | `uv run pytest` |
| **Estimated runtime** | ~30 seconds (quick) / ~120 seconds (full) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/brain/ tests/stages/analyze/ -x -q`
- **After every plan wave:** Run `uv run pytest`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| TBD | TBD | TBD | INFRA-01 | unit | `uv run pytest tests/brain/test_do_context_schema.py` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | INFRA-02 | unit | `uv run pytest tests/stages/analyze/test_do_context_engine.py` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | INFRA-03 | unit | `uv run pytest tests/stages/analyze/test_do_context_migration.py` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | INFRA-04 | unit | `uv run pytest tests/stages/render/test_signal_consumer_do_context.py` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | INFRA-05 | unit | `uv run pytest tests/test_do_context_ci_gate.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/brain/test_do_context_schema.py` — stubs for INFRA-01 (schema validation)
- [ ] `tests/stages/analyze/test_do_context_engine.py` — stubs for INFRA-02 (engine evaluation)
- [ ] `tests/stages/analyze/test_do_context_migration.py` — stubs for INFRA-03 (golden parity)
- [ ] `tests/stages/render/test_signal_consumer_do_context.py` — stubs for INFRA-04 (consumer accessor)
- [ ] `tests/test_do_context_ci_gate.py` — stubs for INFRA-05 (CI gate detection)

*Existing test infrastructure covers framework setup — only test file stubs needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| YAML do_context renders identically to Python functions | INFRA-03 | Golden snapshots automate this | N/A — fully automated |

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
