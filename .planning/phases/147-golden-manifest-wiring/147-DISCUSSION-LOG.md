# Phase 147: Golden Manifest Wiring - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-28
**Phase:** 147-golden-manifest-wiring
**Areas discussed:** Wiring Strategy, Data Flow, Audit & Testing
**Mode:** Auto (--auto flag, recommended defaults selected)

---

## Wiring Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Three-tier classification | renders/wired/suppressed — every template gets exactly one | ✓ |
| Binary classification | renders or suppressed only — simpler but loses nuance | |
| Five-tier classification | renders/partial/wired/pending/suppressed — over-engineered | |

**User's choice:** [auto] Three-tier classification (recommended)
**Notes:** Matches existing test patterns in test_manifest_rendering.py

## Data Flow

| Option | Description | Selected |
|--------|-------------|----------|
| Wire through existing builders | Add keys to assembly_registry builders | ✓ |
| Create new builder files | One builder per manifest section | |
| Direct template-to-state wiring | Templates read state directly | |

**User's choice:** [auto] Wire through existing builders (recommended)
**Notes:** Follows assembly_registry pattern, no new files

## Audit & Testing

| Option | Description | Selected |
|--------|-------------|----------|
| Automated test with real state.json | Load state, render each template, classify | ✓ |
| Manual audit spreadsheet | Human reviews each template | |
| Manifest-only validation | Check requires clauses without rendering | |

**User's choice:** [auto] Automated test with real state.json (recommended)
**Notes:** Existing test_manifest_rendering.py provides the framework

## Claude's Discretion

- Template wiring order within sections
- Merge decisions for small templates
- Specific Jinja2 guard expressions
- Display-only templates with zero signals: suppress vs show placeholder

## Deferred Ideas

None
