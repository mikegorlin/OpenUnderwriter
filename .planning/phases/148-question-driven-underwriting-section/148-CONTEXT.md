# Phase 148: Question-Driven Underwriting Section - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Complete the Underwriting Decision Framework section: add dedicated answerers for all 55 questions across 8 domains, integrate Supabase SCA scenario questions inline, add LLM extraction for specific data gaps, add domain-level and section-level verdict roll-ups, and optimize for print/PDF. The YAML framework, loader, template, and 8 initial answerers already exist from Phase 145 pre-work.

</domain>

<decisions>
## Implementation Decisions

### Answer Quality Bar
- **D-01:** Partial answers with inline flags — answer with whatever structured data is available, mark missing pieces as "Needs Review" with specific filing references inline. Never punt entirely when partial data exists.
- **D-02:** LLM extraction for specific gaps — use LLM against filing text for questions where data exists in narrative but isn't structurally extracted. Priority gaps: risk factors (BIZ-06, 10-K Item 1A), M&A activity (BIZ-05, 8-K/proxy), customer concentration (10-K Item 1/7), regulatory/compliance risks (OPS-01+, 10-K Item 1/1A).
- **D-03:** Always render the section regardless of answer rate — low answer rates show "Needs Review" items which is useful information. No minimum threshold.

### Supabase SCA Integration
- **D-04:** SCA-derived questions integrate inline by domain — slot into matching domains (SCA settlement → Litigation, SCA filing frequency → Litigation, SCA peer comparison → Market, trigger patterns → Market/Operational). Display with a "SCA Data" source badge to distinguish from brain-sourced questions.
- **D-05:** All four SCA scenario types generate questions: filing frequency & recidivism, settlement ranges & severity, peer SCA comparison, trigger pattern matching.

### Answerer Coverage Strategy
- **D-06:** All 8 domains built in parallel — broad coverage across all domains simultaneously rather than sequential by priority.
- **D-07:** Dedicated answerer per question — every question gets its own answerer function. Fully explicit, no ambiguity about which logic handles which question. Move away from generic category fallbacks in screening_answers.

### Visual Presentation
- **D-08:** Keep current verdict dots (14px circles, green +/red -/gray =/amber ?) — compact and scannable, matches CIQ aesthetic.
- **D-09:** Domain-level AND section-level verdict badges — each domain header shows net assessment (Favorable/Unfavorable/Mixed) based on upgrade vs downgrade counts. Section header shows overall assessment. Maximum signal density.
- **D-10:** Print optimization required — add @media print rules for completeness bars, small text, verdict dots, and domain groupings. These elements need explicit print treatment.

### Claude's Discretion
- LLM prompt design for filing text extraction (risk factors, M&A, concentration, regulatory)
- How to structure the per-question answerer files (one file per domain vs one file per question)
- Specific @media print CSS rules
- SCA question YAML schema details (question_id format, data_sources, answer_template)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Pre-work (Phase 145 session)
- `src/do_uw/brain/questions/*.yaml` — 55 question definitions across 8 domains (schema, ordering, data_sources, answer_templates)
- `src/do_uw/brain/questions/__init__.py` — YAML loader (`load_all_domains()`)
- `src/do_uw/stages/render/context_builders/uw_questions.py` — Context builder with 8 domain-specific answerers and `_domain_answerers` registry
- `src/do_uw/stages/render/context_builders/screening_answers.py` — Generic auto-answer engine (11 answerers + category fallbacks)
- `src/do_uw/templates/html/sections/report/uw_questions.html.j2` — Jinja2 template with domain groups, verdict dots, completeness bars

### Pipeline data sources (for answerer implementation)
- `src/do_uw/models/state.py` — AnalysisState model (all answerers read from this)
- `src/do_uw/stages/render/context_builders/assembly_uw_analysis.py` — How UW analysis context is assembled
- `src/do_uw/stages/render/context_builders/uw_analysis.py` — UW analysis context builder (integration point)

### Supabase integration
- `src/do_uw/stages/render/context_builders/` — Existing Supabase SCA integration patterns

### Requirements
- `.planning/REQUIREMENTS.md` — QFW-01 through QFW-07

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `uw_questions.py` (541 lines) — context builder with `_domain_answerers` dict registry pattern and 8 working answerers (BIZ-01, BIZ-03, FIN-01, FIN-02, GOV-01, LIT-01, MKT-01, UW-01)
- `screening_answers.py` (737 lines) — generic answerer with `_ANSWERERS` and `_CATEGORY_FALLBACKS` dicts, 11 answerer functions
- `load_all_domains()` — loads and returns all 8 domain YAML files in order
- `uw_questions.html.j2` — complete template already rendering domain groups with verdict dots and completeness bars

### Established Patterns
- Answer dict structure: `answer`, `evidence`, `verdict` (UPGRADE/DOWNGRADE/NEUTRAL/NO_DATA), `confidence`, `data_found`
- Domain-specific answerers return partial dicts that merge into question dicts
- YAML questions define `data_sources`, `answer_template`, `upgrade_criteria`, `downgrade_criteria`

### Integration Points
- `assembly_uw_analysis.py` — where uw_questions context is wired into the full render context
- `uw_analysis.html.j2` — parent template that includes the questions sub-template
- `worksheet.html.j2` / `base.html.j2` — nav button already wired

</code_context>

<specifics>
## Specific Ideas

- All SCA scenario types are priority — no filtering or phased rollout
- Dedicated answerer per question means the `_domain_answerers` dict should map every question_id to its own function
- LLM extraction targets filing text that's already in state (10-K text from EXTRACT stage) — no new data acquisition needed

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 148-question-driven-underwriting-section*
*Context gathered: 2026-03-28*
