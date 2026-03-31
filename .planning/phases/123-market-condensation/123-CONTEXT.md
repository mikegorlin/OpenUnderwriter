# Phase 123: Market Condensation - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary
Condense Market & Trading section from 52K lines to <5K lines. Top 10 insiders, top 10 holders, 1Y drops with top 5 events, single chart. Overflow to audit layer.
</domain>

<decisions>
## Implementation Decisions

### Condensation Rules
- Insider trading: top 10 transactions by value (not 100+)
- Institutional holders: top 10 by % held (not 50+)
- Stock drops: 1 year history, top 5 events with catalysts (not 25 years)
- Charts: 1 stock chart (1Y) in main body; additional charts move to audit
- Revenue segments: fix extraction gap (FIX-01)

### Overflow Handling
- Full data preserved in audit layer appendix (Preserve Before Improve)
- Main body shows summary with "See full data in Audit Trail" link

### Claude's Discretion
- Exact table layouts for condensed versions
- How to summarize overflow (count + link vs collapsed details)
</decisions>

<canonical_refs>
## Canonical References
- `src/do_uw/templates/html/sections/market/` — All market sub-templates
- `src/do_uw/stages/render/context_builders/_market_display.py` — Market context builder
- `src/do_uw/stages/render/context_builders/governance.py` — Ownership/insider context
</canonical_refs>

<deferred>
None
</deferred>

---
*Phase: 123-market-condensation*
*Context gathered: 2026-03-21*
