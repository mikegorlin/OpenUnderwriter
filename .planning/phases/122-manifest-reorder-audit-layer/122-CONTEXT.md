# Phase 122: Manifest Reorder + Audit Layer - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning
**Source:** Direct from user conversation (no discuss-phase needed)

<domain>
## Phase Boundary

Reorder output_manifest.yaml sections to tell a risk story. Add `layer` field for 3-tier document structure. Merge Company Profile + Business Dossier. Move audit sections to collapsed appendix. The worksheet must read as a narrative, not a data dump.

</domain>

<decisions>
## Implementation Decisions

### Narrative Story Flow (NON-NEGOTIABLE)
- The worksheet tells the RISK STORY of a specific company
- Each section answers the question the underwriter has after reading the previous one:
  1. **Verdict** (Scorecard) → "What's the bottom line?"
  2. **Why** (Executive Brief) → "What are the 3-5 things driving this risk?"
  3. **The Company** (merged Profile + Dossier) → "Who are they, how do they make money?"
  4. **Financial Health** → "Can they survive? Are the books clean?"
  5. **Legal Exposure** (Litigation) → "Who's suing, what's pending?"
  6. **Who's Running It** (Governance) → "Can you trust the leadership?"
  7. **Market Signal** (Market & Trading) → "What's the market telling you?"
  8. **What's Coming** (Forward-Looking) → "What risks are on the horizon?"
  9. **Scoring Detail** → "How did we arrive at the verdict?"
  10. **Recommendation** (Decision Record) → "What should we do?"
- Each section needs a narrative connector sentence bridging from previous section

### Layer Classification
- **Decision layer**: Scorecard, Executive Brief, Red Flags
- **Analysis layer**: Company, Financial, Litigation, Governance, Market, Forward-Looking, Scoring
- **Audit layer**: QA Trail, Signal Disposition, Epistemological Trace, Pattern Engines, Sources, Data Coverage

### Merges
- Company Profile + Business Dossier → single "Company & Operations" section
- Alternative Data (51 lines, empty) → absorb into relevant analysis sections or delete
- AI Risk Assessment (227 lines) → merge into Scoring Detail
- Devil's Advocate (31 lines, stub) → delete until real content exists

### Claude's Discretion
- Exact narrative connector sentence templates
- How to handle sections that have no data (graceful omission vs placeholder)
- Whether audit layer is collapsed `<details>` or separate file

</decisions>

<canonical_refs>
## Canonical References

### Manifest & Rendering
- `src/do_uw/brain/output_manifest.yaml` — Section order and group definitions
- `src/do_uw/templates/html/worksheet.html.j2` — Main template with Zone 0/1/1.5/2/3 includes
- `src/do_uw/stages/render/html_context_assembly.py` — Context builder wiring

### Section Templates
- `src/do_uw/templates/html/sections/` — All section templates

</canonical_refs>

<specifics>
## Specific Ideas

- "The worksheet needs to tell a story" — user's exact words
- "Continuously improve, iterate and enhance the story with more facts and better peer info"
- Each section should have more company-specific facts, not less
- Peer comparison data should be richer and more visible throughout

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 122-manifest-reorder-audit-layer*
*Context gathered: 2026-03-21*
