# Worksheet Quality Report — 2026-02-15

**Tickers tested:** TSLA, AAPL (--no-llm mode, from SEC cache)
**Pipeline version:** Post-Phase 30, with output quality fixes

## Summary

The worksheet is **functional but not yet "amazing."** An experienced D&O underwriter would find Sections 1, 3, 4, and 7 useful, Section 2 needs cleanup, Section 5 needs significant work, and Section 6 needs contextual enrichment. The document tells a risk story but has data gaps and display issues that undermine trust.

## What Works Well

### Section 1: Executive Summary
- Clear tier classification (WALK for TSLA, WIN for AAPL) with rationale
- 10-factor scoring breakdown with transparent point deductions
- Red flag gates with evidence
- Severity scenarios at 25th/50th/75th/95th percentiles
- Tower recommendation with attachment point
- Good differentiation between tickers (TSLA at 30/100, AAPL at 88/100)

### Section 3: Financial Health
- XBRL-sourced financials are accurate and well-presented
- Distress indicators (Z-Score, O-Score, M-Score, Piotroski) with zone classifications
- Capital structure, liquidity, earnings quality metrics
- Audit risk assessment (auditor, tenure, material weaknesses)
- YoY change calculations
- Source attribution to Company Facts API

### Section 4: Market & Trading Signals
- Stock performance metrics accurate (from yfinance)
- Insider trading analysis with 10b5-1 plan coverage
- Cluster selling detection with named insiders
- Earnings guidance track record
- Claims-made context callout (good D&O-specific insight)

### Section 7: Risk Scoring
- 10-factor model transparent and well-structured
- Allegation theory mapping (A through E) with evidence
- Claim probability bands
- Risk type classification (BINARY_EVENT, GUIDANCE_DEPENDENT)

## Issues Fixed This Session

| Issue | Before | After |
|-------|--------|-------|
| Garbage leadership names | 14 entries incl. "Western Association", "Partner Brands" | 8 garbage names filtered (org names blocked) |
| Sector classification | TSLA = "Industrials" | TSLA = "Consumer Discretionary" |
| Enum humanization | "REGULATORY_ENTITY", "product_liability_recall" | "Regulatory", "Product Liability Recall" |
| D&O Exposure redundancy | "Regulatory Multi Jurisdiction: Regulatory Multi Jurisdiction" | "Regulatory Multi Jurisdiction (Identified)" |
| Coverage gap inflation | 33 gaps (16 were aspirational) | 22 gaps (real data gaps only) |
| Empty composite patterns | "Triggers: . Impact: F5: +0" displayed | Zero-impact patterns hidden |

## Remaining Issues (Prioritized by Underwriter Impact)

### CRITICAL — Would make underwriter distrust the document

1. **Leadership names still partially wrong** (TSLA regex path)
   - "Kimbal Musk" listed as CEO (he's a board member, not CEO)
   - "Musk Mr" — reversed name format
   - "Tim Cook" — Apple's CEO appearing in Tesla's worksheet
   - Root cause: Regex extraction from proxy text mentions other companies' executives
   - Fix needed: Cross-reference extracted names against company officers from SEC EDGAR

2. **Board Composition mostly N/A** (both tickers in --no-llm mode)
   - Board Size, Independence Ratio, Classified Board, Dual-Class, Overboarded Directors all N/A
   - These are available in the DEF 14A and should be populated
   - Root cause: LLM extraction populates these; regex fallback doesn't
   - Fix: Improve regex fallback OR always enable LLM for proxy parsing

3. **Sentiment & Narrative Coherence: "Not evaluated"** everywhere
   - This section exists in every worksheet but contributes nothing
   - Undermines trust — if you can't evaluate it, don't show the table
   - Fix: Hide section when all fields are "Not evaluated"

### HIGH — Degrades usefulness

4. **Business Overview is raw 10-K dump** (Section 2)
   - Wall of unformatted text directly from Item 1
   - Includes HTML entities (&#174;, &#8482;)
   - Should be summarized to 3-5 key points
   - Fix: Either truncate to first 200 words with "..." or use LLM summarization

5. **Revenue Segments show "N/A" for percentages** (Section 2)
   - Segment names exist but percentage breakdowns are missing
   - Should be extractable from XBRL or 10-K Item 7
   - Fix: Extract revenue segment data from XBRL or LLM

6. **CEO Compensation "N/A"** (TSLA without LLM)
   - Critical D&O data point not available in regex-only mode
   - AAPL shows $16.8M (from yfinance), but TSLA doesn't
   - Fix: Improve yfinance compensation data extraction

7. **Peer group doesn't match sector** (TSLA)
   - Even with sector fixed to Consumer Discretionary, peers still include
     Amazon, Home Depot, McDonald's — not auto industry peers
   - Peer selection uses yfinance sector separately from resolved sector
   - Fix: Reconcile peer_group.py sector source with resolved sector

### MEDIUM — Polish and completeness

8. **Earnings Quality check threshold possibly inverted**
   - OCF/NI of 3.89 fires RED (>2.0 threshold) but narrative says "healthy"
   - HIGH OCF/NI means cash flow covers earnings many times — this is GOOD
   - Need to verify: is this threshold correct? Or should it be inverted?

9. **SOL dates are generic, not event-specific**
   - Employment Discrimination, Antitrust, FCPA, Environmental etc. all show
     trigger date of 2026-01-29 (filing date, not an actual triggering event)
   - These windows are generic, not tied to known incidents
   - Fix: Only show SOL windows triggered by actual identified events

10. **Historical matters section shows count but no table** (TSLA)
    - "5 historical matter(s)" with no details
    - Fix: Either render the historical cases or don't mention the count

11. **AI Risk section shows "GENERIC"** for Tesla
    - Tesla is one of the most AI-involved companies; "General / Other Industries" is wrong
    - Root cause: AI risk industry classification doesn't use the resolved sector
    - Fix: Wire AI risk module to use resolved SIC/sector

12. **Section 8 AI Risk "Peer comparison unavailable"**
    - No peer context for AI risk scoring
    - Fix: Connect AI risk to peer group data

## Data Quality by Section

| Section | Quality | Issues |
|---------|---------|--------|
| 1. Executive Summary | HIGH | Accurate, well-structured, good differentiation |
| 2. Company Profile | MEDIUM | Raw text dump, N/A segments, wrong peers |
| 3. Financial Health | HIGH | XBRL data accurate, good distress analysis |
| 4. Market & Trading | HIGH | Accurate market data, good insider analysis |
| 5. Governance | LOW | Wrong names, N/A board metrics, empty sentiment |
| 6. Litigation | MEDIUM | Cases present but coverage types were raw enums (fixed), historical section incomplete |
| 7. Risk Scoring | HIGH | Transparent, well-structured, good allegation mapping |
| 8. AI Risk | LOW | Generic classification, no peer comparison |
| Meeting Prep | MEDIUM | Good structure but questions based on incomplete data |

## Recommendations for Next Priority

1. **Enable LLM extraction for proxy statements** — This single change would fix leadership names, board composition, compensation data, and governance metrics. The --no-llm mode is useful for testing but production should use LLM.

2. **Summarize business overview** — Replace raw 10-K dump with structured summary.

3. **Reconcile sector/peer sources** — Single source of truth for sector classification that flows through to peer selection, AI risk classification, and sector baselines.

4. **Hide empty sections** — Don't show "Not evaluated" tables. Silence means clean.

5. **Verify scoring thresholds** — Audit OCF/NI and other thresholds where direction may be inverted.
