# Phase 32 Context — User Decisions

## Decisions (LOCKED)

### D1: Signal Lifecycle
Signals go through a defined lifecycle:
1. **Backlog** — identified as potentially useful, data source TBD
2. **Data Investigation** — understand WHERE to get the data, WHY we can't yet
3. **Monitoring** — active, runs every time, collects data, appears in detail view, but does NOT influence risk score
4. **Scoring** — promoted to scoring when validated (fire rate analysis, event correlation, etc.)
5. **Retired** — archived with full history, never deleted

User emphasis: "We should try to figure out where we can get the data first, and understand why we can't."

### D2: Display Embeds in Risk
Display items are properties OF risk sections, not a separate system.
- Each section (e.g., Governance) defines both what to DISPLAY and what to CHECK
- One brain, one config, one truth
- No separate "display manifest" — display requirements are part of the brain entries

### D3: Full History — Backlog + Changelog
The brain maintains:
- **Backlog**: Prioritized list of signals we COULD add (research-driven)
- **Changelog**: Every change to any check is versioned (added, modified, retired, threshold changed)
- Nothing is ever truly deleted — retired checks stay in history

### D4: Multi-Layer Feedback Loop
Optimization is relentless and multi-dimensional:
- **Fire rate analysis** — checks that never/always fire are miscalibrated
- **Override tracking** — when humans disagree with a check, that's signal
- **Event correlation** — retrospective analysis when D&O claims are filed
- **Provided feedback** — any external input
- **Self-analysis** — system questions its own checks ("why do we need this?", "can we do better?")

User: "Keep questioning why we need things and whether we can do better."

### D5: Dual Organization — Sections + Questions
The brain supports TWO views of the same data:
- **Report sections** — Litigation, Financials, Governance, Market, etc. (how underwriters read)
- **Risk questions** — "Will they get sued?", "Can they survive a claim?" (what we're answering)
- Same underlying checks and data, two organizational lenses
- Sections are the starting structure (matches report output)
- Questions are the analytical structure (drives risk assessment)
- Presentation optimization for maximum underwriter impact comes later

User: "Is there any reason why we can't do both? It should be relying on the same information."

### D6: Core + Supplements + Thresholds
Industry handling uses three layers:
- **Core checks** — run for every company (universal brain)
- **Industry-adjusted thresholds** — what's "normal" varies by sector (2.0 current ratio means different things for tech vs. banking)
- **Industry supplements** — specialized checks for specific sectors (PubPeer for biotech, FFO for REITs, clinical trials for pharma, etc.)

### D7: Inherent Risk Framework
The scoring model follows:
- **Inherent risk** — baseline risk level (industry, size, listing, jurisdiction)
- **Hazards** — things that COULD happen (claim types, regulatory actions, events)
- **Risk characteristics** — things that AMPLIFY or MITIGATE those hazards (governance quality, financial health, management track record, market signals)
- These combine to produce a **Final Score**

### D8: Broad Web Search is First-Class
Broad web searches are NOT a fallback — they are a primary acquisition method:
- Short seller reports, whistleblower complaints, state AG actions
- Employee reviews, scientific integrity sites, social media signals
- Investigative journalism, industry publications
- "A lot of the power of doing this is doing broad web searches on specific topics"

### D9: Brain Must Be Readable Without Code
- An underwriter should understand what's being checked without reading Python
- The brain configuration IS the documentation
- Code must stay synced with the readable brain — no discrepancies

### D10: Don't Simplify by Stripping
- Never deprecate/remove signals — retire them with history
- Keep the backlog of everything we COULD check
- Relentless optimization doesn't mean reduction — it means making everything better

### D11: Database Storage (DuckDB)
The brain lives in a DuckDB database, not flat JSON files:
- **Version history** — every edit is a new row (append-only), full audit trail
- **Continuous updates** — add/modify checks without redeploying code
- **Queryable** — SQL access for analytics, fire rate queries, coverage reports
- **Accessible** — easy to export readable docs, generate reports
- **DuckDB** chosen because it's already in the project (`.cache/analysis.duckdb`)
- Separate brain database (not mixed with pipeline cache)
- Pipeline reads check definitions from DB at runtime

User: "Store the data in a database that is easily accessible, supports version history, and can be updated continuously."

### D12: Integrate in do-uw First
- Brain database and all infrastructure lives within the current do-uw project
- Fully operational here first — no external dependencies
- Migration to a different host or service can be planned later when needed
- GSD orchestrator drives the implementation

User: "Integrate this within our current system so it's fully operational here first."

## Claude's Discretion
- Internal architecture of the check evaluation engine
- How to implement the section↔question dual mapping
- Specific threshold values and calibration approach
- How to structure industry supplements
- DuckDB schema design (tables, indexes, views)
- How to generate readable docs from DB (export format, frequency)

## Deferred Ideas
- Presentation optimization for maximum underwriter impact (D5 — later phase)
- Actual claims data integration for validation (D4 — when available)
- Auto-decline layer (from Old System — evaluate after brain redesign)
- Migration to external host/service (D12 — when needed)
