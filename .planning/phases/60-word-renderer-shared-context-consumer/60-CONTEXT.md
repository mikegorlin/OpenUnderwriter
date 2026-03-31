# Phase 60: Word Renderer as Shared-Context Consumer - Context

**Gathered:** 2026-03-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Rewrite 28 Word section files (10,628 lines across `stages/render/sections/sect*.py`) to consume `context_builders/` context instead of accessing `state.*` directly. Eliminate ~6,000 lines of duplicated extraction logic. Word sections become formatting-only modules that receive a pre-built context dict.

This is a pure refactoring phase — output should not change. Visual improvements happen in later phases (61: Surface Hidden Data, 63: Charts, 65: Narratives).

</domain>

<decisions>
## Implementation Decisions

### Migration Strategy
- Follow roadmap 3-plan split: sect1-4, sect5-8, sect9+
- Plan 01 includes both plumbing (wire `build_template_context()` into `word_renderer.py`) AND sect1-4 migration
- Each plan migrates a batch of sections, runs tests after
- One section per commit within each plan for granular rollback

### Section Signature Change
- Sections currently receive `(doc, state, ds)` — change to `(doc, context, ds)`
- Context-only: no state parameter passed to sections. Clean break enforces zero `state.*` access
- If a section needs data not in context_builders, extend context_builders first — don't pass state as fallback
- `word_renderer.py` calls `build_template_context()` once, passes the resulting context dict to all sections

### Line Count Target
- Natural reduction: swap state access for context dict access, delete duplicated extraction code
- ~200-300 lines per section is aspirational, not a hard gate
- Don't actively refactor formatting logic — just remove extraction code that's now in context_builders

### Word Formatting Retention
- All Word-specific formatting preserved: cell shading, font sizes, table ordering, density indicators, chart embedding
- Only change WHERE data comes from, not WHAT gets rendered
- Chart embedding stays as-is (chart_helpers.py generates PNGs, Word sections embed them) — Phase 63 will handle chart improvements

### docx_helpers.py
- Light cleanup if issues encountered during migration, but no proactive refactoring
- It's working infrastructure — don't touch unless something breaks

### Verification Approach
- Existing Word tests passing (WORD-06) is the primary verification gate
- Quick sanity run on one ticker at the end of Phase 60 — open the doc, confirm not broken
- No new visual diff test or baseline snapshot (later v3.0 phases will change output anyway)

### Markdown Renderer Deprecation
- Add CLI deprecation warning when user runs `do-uw analyze --format markdown`
- Warning says: "Markdown output is deprecated. Use HTML or Word."
- Still generates the markdown file — not removed, just deprecated
- `build_template_context()` stays in `md_renderer.py` (HTML/PDF depend on it)
- Markdown templates in `templates/markdown/` left as-is
- Full removal is future cleanup

### Claude's Discretion
- Order of section migration within each batch
- How to handle edge cases where context_builders don't have equivalent data
- Whether to extend context_builders or adapt Word sections when gaps found
- Exact wording of markdown deprecation warning

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `context_builders/` package (9 modules, 3,213 lines): `company.py`, `financials.py`, `governance.py`, `litigation.py`, `market.py`, `scoring.py`, `analysis.py`, `calibration.py`, `financials_balance.py`
- `context_builders/__init__.py`: re-exports all 22 `extract_*` functions
- `build_template_context()` in `md_renderer.py:67`: already calls all context_builders, returns complete context dict
- `docx_helpers.py`: shared Word infrastructure (table builders, paragraph helpers, page numbers)
- `design_system.py`: `DesignSystem` class + `setup_styles()` for Word doc styling

### Established Patterns
- Section renderers follow pattern: `render_section_N(doc, state, ds, **kwargs) -> None`
- `word_renderer.py` uses `_try_import_renderer()` for graceful fallback on missing sections
- Section 4 (Market) has special `chart_dir` kwarg for PNG embedding
- Density indicators and pre-computed narratives added by word_renderer.py before each section
- 9 `md_renderer_helpers_*.py` shim files exist — these are thin re-exports to context_builders (Phase 58)

### Integration Points
- `word_renderer.py:render_word_document()` is the entry point — orchestrates all sections
- `html_renderer.py` already calls `build_template_context()` via `build_html_context()`
- Only 2 of 28 section files currently import from `context_builders/` — rest access `state.*` directly
- 76+ direct `state.*` accesses across section files need to become `context[...]` lookups
- Meeting prep section (`meeting_prep.py`) and calibration section (`sect_calibration.py`) are special cases

### Key Measurements
- 28 section files: 10,628 total lines
- Largest: `sect4_market_events.py` (497), `sect3_audit.py` (495), `sect5_governance_board.py` (488)
- Smallest: `sect4_market_helpers.py` (97), `sect3_peers.py` (116), `sect3_quarterly.py` (122)
- Expected reduction: ~4,000-6,000 lines (extraction code removed)

</code_context>

<specifics>
## Specific Ideas

No specific requirements — the phase goal (swap extraction source, preserve output) is clear and mechanical.

</specifics>

<deferred>
## Deferred Ideas

- Unified chart generation across formats — Phase 63 (Interactive Charting)
- Moving `build_template_context()` from `md_renderer.py` to `context_builders/` — future cleanup
- Full markdown renderer removal — future cleanup after deprecation period
- Word-specific visual improvements — later v3.0 phases

</deferred>

---

*Phase: 60-word-renderer-shared-context-consumer*
*Context gathered: 2026-03-02*
