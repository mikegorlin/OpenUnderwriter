# Phase 144: Pipeline & Rendering Resilience - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-28
**Phase:** 144-pipeline-rendering-resilience
**Areas discussed:** Failure strategy, Missing data display, Stage status tracking, Supabase independence

---

## Failure Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Continue all stages | Failed stage logged, pipeline continues to RENDER. Most resilient. | ✓ |
| Continue but skip dependents | If EXTRACT fails, skip ANALYZE/SCORE/BENCHMARK but still RENDER. | |
| You decide | Claude picks based on pipeline architecture | |

**User's choice:** Continue all stages (Recommended)
**Notes:** None

---

| Option | Description | Selected |
|--------|-------------|----------|
| Exit 0 with warnings | HTML produced = success. Log warnings about failed stages. | ✓ |
| Exit non-zero on any failure | Exit 1 even if HTML produced. Useful for CI. | |
| You decide | Claude picks based on CLI conventions | |

**User's choice:** Exit 0 with warnings (Recommended)
**Notes:** None

---

## Missing Data Display

| Option | Description | Selected |
|--------|-------------|----------|
| Banner + available data | Amber 'Incomplete' banner at top, then whatever data IS available | ✓ |
| Collapsed placeholder | Section header visible, body = 'Data not available' | |
| Hide entirely | Missing sections don't appear at all | |

**User's choice:** Banner + available data (Recommended)
**Notes:** None

---

| Option | Description | Selected |
|--------|-------------|----------|
| Gray placeholder box | Same dimensions as chart, light gray, centered 'No data available' | ✓ |
| Skip chart entirely | No chart, no placeholder. Layout shifts possible. | |
| You decide | Claude picks the visual approach | |

**User's choice:** Gray placeholder box (Recommended)
**Notes:** None

---

## Stage Status Tracking

| Option | Description | Selected |
|--------|-------------|----------|
| Footer status bar | Small bar at bottom with green/red/gray indicators | |
| State.json only | Status stays in state.json for debugging only | |
| Both + section banners | Footer bar AND per-section banners | |

**User's choice:** Other — Display in the audit section. Full traceability is paramount. "This is the single source of truth."
**Notes:** User emphasized that the worksheet must show what the pipeline did, what data it has, and what's missing. No hiding failures. Audit section is the right home for this.

---

## Supabase Independence

| Option | Description | Selected |
|--------|-------------|----------|
| Dual-path render | Risk card pulls from acquired_data directly, never from extracted. Two separate paths. | ✓ |
| Fallback chain | Try extracted first, fall back to acquired_data. Single path with fallback. | |
| You decide | Claude picks the architecture | |

**User's choice:** Dual-path render (Recommended)
**Notes:** None

---

## Claude's Discretion

- Chart placeholder styling details
- Stage execution wrapper pattern (contextmanager vs inline try/except)
- Audit section template structure

## Deferred Ideas

None — discussion stayed within phase scope.
