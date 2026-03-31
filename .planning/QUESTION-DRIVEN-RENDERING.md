# Question-Driven Rendering Framework

> **Principle:** Every section answers a specific underwriter question. Lead with the answer, show the evidence, flag what's concerning.

## Pattern: Answer → Evidence → Flags

```
┌─────────────────────────────────────────┐
│ ANSWER (1-2 sentences, company-specific │
│ with dollar amounts and dates)          │
├─────────────────────────────────────────┤
│ EVIDENCE (tables, charts, data that     │
│ supports the answer)                    │
├─────────────────────────────────────────┤
│ FLAGS (brain signals that fired,        │
│ what's concerning and why)              │
└─────────────────────────────────────────┘
```

---

## Section → Question Mapping

### 1. EXECUTIVE SUMMARY (Decision Layer)

| Sub-section | Underwriter Question | Answer Pattern |
|---|---|---|
| Company Profile | "Who is this company?" | "{Name} is a {market_cap_tier} {sector} company, public since {ipo_year}, with {employees} employees across {countries} countries. {one_sentence_business}." |
| Risk Classification | "Should I write this risk?" | "Tier: {tier} — {action}. Quality score {score}/100. Claim probability {prob_band}." |
| Key Findings | "What are the 3-5 things I need to know RIGHT NOW?" | Each finding: company-specific fact + D&O implication + severity. NO boilerplate 10-K language. |
| Claim Probability | "What's the likelihood we pay a claim?" | "{prob_band} ({low}%-{high}%). Based on {factors}. Comparable peers: {peer_settlement_range}." |
| Tower Recommendation | "Where should I sit in the tower?" | "Recommended: {layer}. Primary expected loss: {EL}. Maximum DDL: {DDL}." |

### 2. CRITICAL RISK FLAGS (Decision Layer)

| Sub-section | Underwriter Question | Answer Pattern |
|---|---|---|
| Triggered Flags | "What could blow up this risk?" | Each flag: specific trigger + evidence + what it means for D&O. Only flags that FIRED, not theoretical. |

### 3. COMPANY & OPERATIONS (Analysis Layer)

| Sub-section | Underwriter Question | Answer Pattern |
|---|---|---|
| Business Description | "How does this company make money?" | NOT raw 10-K text. "Apple generates {rev}B annually: {pct}% from {product}, {pct}% from {services}. Revenue is {concentrated/diversified} across {segments}." |
| Revenue Segments | "Where's the revenue concentration risk?" | Table + answer: "iPhone is {pct}% of revenue — a single product decline could trigger a material miss disclosure." |
| Customer Concentration | "Is revenue dependent on a few customers?" | "No single customer >10% of revenue" or "{customer} represents {pct}% — loss would be material." |
| M&A Profile | "Has the company been doing deals?" | "{N} acquisitions in past 3 years totaling ${amount}. Largest: {name} (${size}). Integration risk: {assessment}." |
| 10-K YoY Analysis | "What changed in this year's filing?" | Only CHANGES that matter: new risk factors, removed language, material differences. NOT a full comparison. |
| Risk Factors | "What does the company say could go wrong?" | ONLY company-specific risk factors. Filter out boilerplate (macroeconomic, natural disasters, IT failures). |

### 4. MARKET ACTIVITY (Analysis Layer)

| Sub-section | Underwriter Question | Answer Pattern |
|---|---|---|
| Stock Charts | "What's the stock story?" | Charts FIRST (1Y + 5Y with sector overlay). Answer: "AAPL up {pct}% over 12mo vs sector {pct}%. {trend characterization}." |
| Stock Drops | "Has the stock had drops that could trigger a claim?" | "Largest drop: {pct}% on {date} ({catalyst}). DDL: ${amount}. {N} drops > 10% in past year." |
| Short Interest | "Are shorts betting against this company?" | "{pct}% of float short ({days_to_cover} days to cover). {characterization: de minimis / elevated / critical}." |
| Insider Trading | "Are insiders selling ahead of bad news?" | Answer first: "Net {buying/selling} of ${amount} over 12 months. {any_concerning_patterns}." Then Form 4 table. |
| Analyst Consensus | "What does the Street think?" | "{N} analysts: {buy/hold/sell split}. Median PT ${price} ({upside/downside}%). {recent_revision_trend}." |

### 5. FINANCIAL HEALTH (Analysis Layer)

| Sub-section | Underwriter Question | Answer Pattern |
|---|---|---|
| Annual Comparison | "Is the company getting better or worse?" | "Revenue {grew/declined} {pct}% to ${amount}. Net income {trend}. Cash position: ${cash}. Key concern: {or 'None'}." |
| Distress Indicators | "Could this company go bankrupt?" | "Altman Z: {score} ({zone}). Beneish M: {score} ({manipulation_flag}). {one_sentence_conclusion}." |
| Forensic Dashboard | "Are the books clean?" | "Beneish {pass/flag}: {N} of 8 dimensions flagged. {which_ones_and_why}." |
| Earnings Quality | "Can I trust the reported numbers?" | "Accrual ratio: {ratio}. Cash conversion: {pct}%. {quality_assessment}." |
| Audit Profile | "Who audits and are there issues?" | "{auditor} (Big 4). {N} years as auditor. SOX 302/906: {clean/issues}. Material weaknesses: {count}." |
| Peer Comparison | "How does this compare to peers?" | "vs {peer_group}: Revenue {percentile}th pctile, margins {percentile}th, leverage {percentile}th. {outlier_flags}." |

### 6. GOVERNANCE (Analysis Layer)

| Sub-section | Underwriter Question | Answer Pattern |
|---|---|---|
| People Risk | "Who are the key people and what's their risk?" | Board size, independence %, key departures. Then individual profiles with LITIGATION HISTORY and CHARACTER issues. |
| Board Composition | "Is the board properly constituted?" | "{N} directors, {pct}% independent. Average tenure {years}. {diversity_note}. {overboarding_flags}." |
| Compensation | "Is management overpaid?" | "CEO total comp: ${amount}. Pay ratio: {ratio}:1. Say-on-pay: {pct}% approval. {concerning_patterns}." |
| Ownership Structure | "Who controls this company?" | "Institutional: {pct}%. Insider: {pct}%. Top holder: {name} ({pct}%). {control_flags}." |

### 7. LITIGATION & REGULATORY (Analysis Layer)

| Sub-section | Underwriter Question | Answer Pattern |
|---|---|---|
| Active Matters | "What's the current litigation exposure?" | "{N} active matters: {breakdown}. Total potential exposure: ${range}. Most critical: {case_name} ({theory})." |
| SEC Enforcement | "Is the SEC investigating?" | "Pipeline stage: {stage}. {evidence}. D&O implication: {assessment}." |
| Settlement History | "What's the company's settlement track record?" | "{N} prior settlements totaling ${total}. Largest: ${amount} ({year}, {theory}). Plaintiff bar anchor: ${typical}." |
| SOL Analysis | "Are there open exposure windows?" | "{N} windows open. Nearest expiry: {date} ({type}). Closed windows: {N}." |
| Defense Strength | "How defensible is this company?" | "Defense posture: {strong/moderate/weak}. PSLRA motion to dismiss: {likely/unlikely}. Key defense: {factor}." |

### 8. SCORING & RISK ASSESSMENT (Analysis Layer)

| Sub-section | Underwriter Question | Answer Pattern |
|---|---|---|
| 10-Factor Scoring | "How does the risk score break down?" | Visual: factor bars. Answer: "Largest deductions: {factor1} ({points}pts), {factor2} ({points}pts). Strengths: {factor3}." |
| Claim Probability | "What's the math behind the probability?" | "Base rate: {sector_rate}%. Adjustments: {list}. Final band: {low}-{high}%." |
| Meeting Prep | "What questions should I ask the broker?" | 5-7 questions specific to THIS company's risk profile. NOT generic D&O questions. |

---

## What We Already Have

### Data Available (in state.json)
- Company profile (ticker, name, sector, SIC, employees, market cap, years public)
- XBRL financials (3-5 years: revenue, income, assets, equity, cash, debt)
- Stock data (1Y/5Y prices, drops, volume, short interest, institutional holders)
- Governance (board members, committees, compensation, insider transactions)
- Litigation (SCAs, derivatives, regulatory, settlements, SOL windows)
- Brain signal results (600+ signals with status, evidence, D&O context)
- Scoring (10-factor, claim probability, tier, severity scenarios)
- LLM extractions (10-K risk factors, MD&A, executive details)

### What's Missing or Weak
1. **Key Risk Findings** — pulls raw 10-K risk factor titles instead of synthesizing company-specific risks
2. **Executive brief prose** — system jargon leaks ("A_DISCLOSURE theory", "forensic signal architecture")
3. **Business Description** — sometimes dumps raw 10-K text instead of concise summary
4. **Risk Factors** — includes boilerplate (macroeconomic, natural disasters) that every company has
5. **Cybersecurity** — raw truncated 10-K text, not analysis
6. **Historical litigation** — may miss older cases not in SCAC/EFTS
7. **10-K YoY** — shows all changes, not just material D&O-relevant changes
8. **Meeting Prep Questions** — sometimes generic D&O questions, not company-specific

### Architecture for Answer Generation
Each section answer can be generated by:
1. **Template-driven** — Jinja2 template with conditional logic (works for structured data like financials, governance)
2. **Signal-driven** — Brain signal results provide the "what's concerning" layer; template just renders them
3. **LLM-driven** — For narrative synthesis (Key Findings, Business Description) where the answer requires reasoning across multiple data points

The answer pattern needs the **context builder** to pre-compute the answer string, not just pass raw data to the template. The template renders the answer; it doesn't generate it.

---

## Implementation Priority (for Monday)

### P0 — Must fix (these make the worksheet look broken)
1. Key Risk Findings: filter boilerplate, require company-specific evidence
2. Executive brief: remove system jargon, write in underwriter voice
3. Business Description: concise summary, not raw 10-K dump
4. Cybersecurity section: analysis not text dump

### P1 — Should fix (these make the worksheet less useful)
5. Risk Factors: filter boilerplate risk factors
6. Meeting Prep: company-specific questions only
7. Insider Trading: lead with answer, not just transaction table
8. Stock section: answer before data grid

### P2 — Nice to have (these improve polish)
9. All sections: add answer strings to context builders
10. Financial section: lead with conclusion
11. Governance: lead with people risk assessment
12. Litigation: lead with exposure summary

---

## Prototype Approach

Build a **parallel report** that uses the same state.json but renders with question-driven templates. This lets us compare old vs new side by side without breaking the existing output.

File: `src/do_uw/stages/render/question_driven_report.py`
- Reads state.json
- For each section, generates the "answer" string
- Renders a clean HTML report with answer → evidence → flags pattern
- Outputs to `output/{TICKER}/{TICKER}_qd_report.html`

This is a separate renderer, not a modification of the existing one. We can iterate on it without risk.
