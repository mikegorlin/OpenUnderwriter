---
phase: 118
slug: revenue-model-company-intelligence-dossier
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-20
---

# Phase 118 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x (existing) |
| **Config file** | pyproject.toml (existing) |
| **Quick run command** | `uv run pytest tests/models/test_dossier.py tests/stages/extract/test_dossier_extraction.py tests/stages/benchmark/test_dossier_enrichment.py tests/stages/render/test_dossier_context_builders.py tests/stages/render/test_dossier_templates.py -x -q` |
| **Full suite command** | `uv run pytest -x -q` |
| **Estimated runtime** | ~30 seconds (dossier only), ~120 seconds (full suite) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/models/test_dossier.py tests/stages/extract/test_dossier_extraction.py tests/stages/benchmark/test_dossier_enrichment.py tests/stages/render/test_dossier_context_builders.py tests/stages/render/test_dossier_templates.py -x -q`
- **After every plan wave:** Run `uv run pytest -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 118-01-01 | 01 | 1 | DOSSIER-01 thru 09 | unit | `uv run pytest tests/models/test_dossier.py -x` | ❌ W0 | ⬜ pending |
| 118-02-01 | 02 | 2 | DOSSIER-01,02,03,04,05,06,08,09 | unit | `uv run pytest tests/stages/extract/test_dossier_extraction.py -x` | ❌ W0 | ⬜ pending |
| 118-03-01 | 03 | 2 | DOSSIER-03,04,08,09 | unit | `uv run pytest tests/stages/benchmark/test_dossier_enrichment.py -x` | ❌ W0 | ⬜ pending |
| 118-04-01 | 04 | 3 | DOSSIER-01 thru 09 | unit | `uv run pytest tests/stages/render/test_dossier_context_builders.py -x` | ❌ W0 | ⬜ pending |
| 118-05-01 | 05 | 3 | DOSSIER-01 thru 09 | unit | `uv run pytest tests/stages/render/test_dossier_templates.py -x` | ❌ W0 | ⬜ pending |
| 118-06-01 | 06 | 4 | DOSSIER-01 thru 09 | integration | `uv run pytest tests/stages/render/test_dossier_integration.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/models/test_dossier.py` — model instantiation, serialization, defaults for DossierData
- [ ] `tests/stages/extract/test_dossier_extraction.py` — LLM extraction schema validation
- [ ] `tests/stages/benchmark/test_dossier_enrichment.py` — concentration scoring, D&O risk generation
- [ ] `tests/stages/render/test_dossier_context_builders.py` — context builder output shapes
- [ ] `tests/stages/render/test_dossier_templates.py` — template rendering with fixture data
- [ ] `tests/stages/render/test_dossier_integration.py` — end-to-end from state to rendered HTML

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual layout matches gold standard PDF | ALL | Layout quality requires human judgment | Open rendered HTML, compare section-by-section against HNGE PDF pages 4-12 |
| D&O commentary is company-specific | DOSSIER-01 thru 09 | Narrative quality requires human review | Verify no boilerplate, every sentence has company data |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
