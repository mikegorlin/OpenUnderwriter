---
name: Research config accidentally disabled
description: Research toggle was accidentally flipped to false during v5.x facet refactor - verify config.json research=true at session start
type: feedback
---

Research was accidentally disabled in `.planning/config.json` during commit 74c5221 (facet YAML refactor in v5.x). All v7.0 phases (102-108) were planned without research. Phases 102-106 also had no CONTEXT.md (discuss-phase wasn't used until Phase 107). Fixed 2026-03-16 by setting `"research": true`.

**Why:** Accidental toggle during an unrelated refactor. No phases had RESEARCH.md or VALIDATION.md in v7.0 until Phase 109. The code shipped fine (5,687 tests pass) but planning rigor was reduced.

**How to apply:** At session start, verify `.planning/config.json` has `"research": true`. If a phase is being planned without research, flag it — research should always run unless explicitly skipped with `--skip-research`.
