---
phase: 116
slug: d-o-commentary-layer
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-19
---

# Phase 116 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `uv run pytest tests/brain/ tests/stages/render/ -x -q --timeout=30` |
| **Full suite command** | `uv run pytest` |
| **Estimated runtime** | ~45 seconds (quick) / ~120 seconds (full) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/brain/ tests/stages/render/ -x -q`
- **After every plan wave:** Run `uv run pytest`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 45 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| TBD | TBD | 1 | COMMENT-01 | unit | `uv run pytest tests/brain/test_do_context_batch.py` | ❌ W0 | ⬜ pending |
| TBD | TBD | 2 | COMMENT-01 | unit | `uv run pytest tests/stages/render/test_do_context_migration.py` | ❌ W0 | ⬜ pending |
| TBD | TBD | 3 | COMMENT-02 | unit | `uv run pytest tests/stages/render/test_scoring_commentary.py` | ❌ W0 | ⬜ pending |
| TBD | TBD | 3 | COMMENT-03 | unit | `uv run pytest tests/stages/render/test_forensic_commentary.py` | ❌ W0 | ⬜ pending |
| TBD | TBD | 4 | COMMENT-04,05,06 | unit | `uv run pytest tests/stages/analyze/test_narrative_generation.py` | ❌ W0 | ⬜ pending |
| TBD | TBD | 4 | SCORE-04 | unit | `uv run pytest tests/stages/render/test_tier_explanation.py` | ❌ W0 | ⬜ pending |
| TBD | TBD | 5 | SCORE-01 | unit | `uv run pytest tests/stages/render/test_factor_detail.py` | ❌ W0 | ⬜ pending |
| TBD | TBD | 6 | COMMENT-01 | integration | `uv run pytest tests/brain/test_do_context_ci_gate.py` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/brain/test_do_context_batch.py` — stubs for batch generation validation
- [ ] `tests/stages/render/test_do_context_migration.py` — stubs for hardcoded function migration parity
- [ ] `tests/stages/render/test_scoring_commentary.py` — stubs for factor detail rendering
- [ ] `tests/stages/analyze/test_narrative_generation.py` — stubs for LLM narrative generation
- [ ] `tests/stages/render/test_tier_explanation.py` — stubs for algorithmic tier explanation

*Existing test infrastructure covers framework setup — only test file stubs needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| D&O columns visually correct in HTML | COMMENT-01 | Layout/rendering quality | Open HTML worksheet, check each evaluative table has D&O column |
| Narrative paragraphs read well | COMMENT-04,05,06 | Content quality assessment | Read each section opener, verify company-specific and analytical |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 45s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
