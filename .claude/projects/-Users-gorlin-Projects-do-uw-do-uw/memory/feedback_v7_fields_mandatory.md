---
name: v7_fields_mandatory
description: v7.0 signal fields (rap_class, epistemology, evaluation.mechanism) are REQUIRED not optional — enforce at schema level
type: feedback
---

v7.0 fields on signals are foundational and mandatory, not optional. Every signal must have them. Enforce at the Pydantic schema level (no `| None`), not just via CI tests.

**Why:** Mike explicitly corrected the approach of making v7.0 fields optional with `| None` defaults. These are the backbone of v7.0 — treating them as optional undermines the entire architecture. A signal without rap_class or epistemology is not a valid signal.

**How to apply:** When adding new required fields to brain signal schema, make them required in Pydantic (no `| None`, no `default=None`). Populate all existing signals first, then tighten the schema. Never leave foundational fields optional permanently.
