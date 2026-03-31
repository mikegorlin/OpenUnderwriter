# Phase 130: Dual-Voice Intelligence - Context

**Gathered:** 2026-03-23 (updated — replaces original context based on user readability feedback)
**Status:** Ready for planning

<domain>
## Phase Boundary

Transform every analytical section from machine-readable data dump into a human-readable formal research report. Every section gets a dual-voice structure: brief factual narrative + supporting tables ("What Was Said"), then bulleted D&O commentary ("Underwriting Commentary"). The executive summary tells the risk story first, then delivers the recommendation. All system internals (factor codes, signal IDs, scoring engine details, AI labels) are removed from the main body — they live in the appendix only.

</domain>

<decisions>
## Implementation Decisions

### Writing Voice & Tone
- **D-01:** Formal research report voice — structured, thorough, third-person. Like a Marsh or Aon D&O market report. Professional but readable.
- **D-02:** BAN from all main body prose: factor codes (F1-F10), signal IDs (LIT.SCA.active), check ratios (5-of-90), scoring internals ("composite risk score of 88.64", "deduction points", "signal triggered", "check engine", "brain", "data coverage"), and ALL AI labels ("AI Assessment", "automated analysis", "system detected"). The reader must never know a machine wrote this.
- **D-03:** System internals live in the appendix ONLY. No tooltips, no hover — clean separation between research report (main body) and audit trail (appendix).
- **D-04:** Remove "AI Assessment" label from HTML templates (`narratives.html.j2`), Word renderer (`word_renderer.py`), and Markdown templates. Replace with nothing — the prose stands on its own.
- **D-05:** LLM prompts must be rewritten to produce formal research report prose, not system narration. Ban factor codes and signal IDs from prompt instructions. The LLM should write like an analyst, not describe a scoring engine.

### Section Structure
- **D-06:** Factual layer = brief 2-3 sentence narrative summary + supporting tables/charts/KV pairs. Prose is minimal and purely descriptive. Numbers in tables, not buried in sentences.
- **D-07:** Commentary layer = bulleted D&O analysis. No prose paragraphs — just bulleted findings with implications. Fastest to scan, most actionable for a busy underwriter.
- **D-08:** Adapt structure per section — most sections use dual-voice, but each section's content drives the layout. Litigation leads with the case table; Scoring leads with charts; Governance leads with the board grid. Not a rigid template forced on every section.
- **D-09:** Visually distinct blocks — factual in light gray, commentary in navy/blue-gray tinted box. Clear headers on each.

### Executive Summary Design
- **D-10:** Lead with risk narrative — 2-3 paragraphs telling the D&O risk story: what this company is, what the key exposures are, what makes it interesting or dangerous. Recommendation comes AFTER the story.
- **D-11:** Key negatives: numbered list, each with specific finding + dollar/percentage magnitude + which SCA theory it enables (e.g., "enables loss causation argument under Section 10(b)"). Top 5.
- **D-12:** Key positives: numbered list, each with specific evidence + quantification + the SCA theory it defeats (e.g., "consistent beat-and-raise pattern defeats the core scienter element"). Top 5.
- **D-13:** No factor codes in exec summary or anywhere in main body. "Prior litigation history is the primary risk driver" not "F1 = 5/20 points."
- **D-14:** Recommendation block (tier + probability + severity + defense cost) follows the narrative and findings. Underwriter reads the story first, gets the verdict second.

### Commentary Generation (from original context, still valid)
- **D-15:** LLM with full signal context — one batched LLM call per section in BENCHMARK stage. Pass signal results + scoring factors + financials + company data as context.
- **D-16:** Cached in state (`state.benchmarked.commentary`) — generate once in BENCHMARK, re-render uses cache. Only regenerate on `--fresh` or when underlying data changes.
- **D-17:** Cross-validate all dollar amounts in commentary against XBRL/state data (leverage Phase 129's `validate_narrative_amounts()`).

### Claude's Discretion
- Exact LLM prompt engineering for each section's commentary (within the "formal research report, no system internals" constraint)
- How to batch multiple section commentaries into fewer API calls (cost optimization)
- Per-section layout adaptation — which sections lead with what content type
- How to restructure existing narrative prompts to produce research-report quality output

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Voice & Tone
- `memory/feedback-human-readability.md` — Specific readability problems identified by user (2026-03-23)
- `memory/feedback-section-rework-directive.md` — How to approach each section rework
- `memory/feedback-output-quality-crisis.md` — What went wrong with prior output quality

### Templates to Modify (AI label removal + dual-voice blocks)
- `src/do_uw/templates/html/components/narratives.html.j2` — Contains "AI Assessment" label (line 16)
- `src/do_uw/templates/html/sections/executive/key_findings.html.j2` — Exec summary "AI Assessment"
- `src/do_uw/stages/render/word_renderer.py` — "[AI Assessment]" prefix (lines 330-331)
- `src/do_uw/templates/markdown/worksheet.md.j2` — "AI Assessment" in markdown (line 26)

### LLM Prompts to Rewrite
- `src/do_uw/stages/benchmark/narrative_prompts.py` — Currently asks for "F3 = X/Y points" format (line 50)
- `src/do_uw/stages/benchmark/narrative_helpers.py` — "possible deduction points" phrasing (line 189)
- `src/do_uw/stages/benchmark/thesis_templates.py` — "possible deduction points" (line 66)
- `src/do_uw/stages/benchmark/key_findings.py` — Key findings generation with factor scores

### Commentary Generation
- `src/do_uw/stages/benchmark/narrative_generator.py` — Existing LLM narrative generation + `validate_narrative_amounts()`
- `src/do_uw/stages/benchmark/narrative_data_sections.py` — Data extraction for LLM context

### Executive Summary
- `src/do_uw/stages/render/context_builders/company_exec_summary.py` — Current exec summary builder
- `src/do_uw/stages/render/context_builders/_bull_bear.py` — Bull/bear case generation
- `src/do_uw/stages/render/context_builders/decision_context.py` — Decision context with tier/recommendation

### Assembly & Registry
- `src/do_uw/stages/render/context_builders/assembly_registry.py` — Registry pattern for context builders
- `src/do_uw/templates/html/` — All HTML section templates that need dual-voice blocks

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `narrative_generator.py`: already does LLM calls in BENCHMARK — extend with commentary generation
- `_signal_consumer.py`: aggregates signal results per section — reuse for commentary context
- `validate_narrative_amounts()`: cross-validates LLM dollar amounts — apply to commentary
- `_bull_bear.py`: generates bull/bear cases — key negatives/positives can extend this
- Evaluative context builders (`financials_evaluative.py`, etc.) already pull `do_context` from signals

### Established Patterns
- BENCHMARK stage runs after SCORE — has access to all scoring results
- Context builders return `dict[str, Any]` — add `commentary_*` keys per section
- Assembly registry dispatches context building — commentary keys flow through automatically

### Integration Points
- `state.benchmarked` — add `commentary: dict[str, SectionCommentary]` field
- Templates — add dual-voice blocks per section
- Exec summary template — major overhaul for narrative-first + findings + recommendation
- Remove "AI Assessment" from 4 locations (HTML, Word, Markdown, narrative component)
- Rewrite LLM prompts in narrative_prompts.py to produce formal research report prose

</code_context>

<specifics>
## Specific Ideas

- The HNGE report's visual separation pattern is the design target for dual-voice blocks
- User emphasized: "it's like it's written for a machine" — this is the #1 problem to solve
- User wants formal research report quality, not system narration
- Bulleted commentary, not prose paragraphs — underwriters scan, they don't read novels
- Per-section adaptation: litigation leads with case table, scoring with charts, governance with board grid
- Exec summary tells the risk STORY first, verdict second
- "Would an underwriter write this?" is the quality test for every paragraph

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 130-dual-voice-intelligence*
*Context gathered: 2026-03-23 (updated)*
