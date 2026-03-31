# Sasha Platform: Architecture & Implementation Handoff

This document provides context, architectural decisions, and the current state of the **Sasha Underwriting Platform** to assist in its continued development and improvement.

## 1. Project Context
Sasha Platform is a complete architectural overhaul of a legacy system (`do-uw` / Underwriting 5.0 Lite). The primary goal of the overhaul was to transition from a markdown-centric, hardcoded architecture to a **data-first, declarative Python pipeline**. 

The system acts as an automated underwriting engine that ingests company data (SEC filings, market data, litigation, unstructured web context), evaluates it against hundreds of predefined industry signals, and generates a comprehensive, multi-page, consulting-grade HTML report.

## 2. Core Architecture Overview
The platform is designed around a "Brain-Centric" architecture with four distinct layers:

1. **Data Collection Layer ([sasha/collect/](file:///Users/gorlin/projects/UW/sasha-platform/src/sasha/collect))**
   - Pluggable data collectors ([SECCollector](file:///Users/gorlin/projects/UW/sasha-platform/src/sasha/collect/sec.py#14-132), [MarketCollector](file:///Users/gorlin/projects/UW/sasha-platform/src/sasha/collect/market.py#9-92), [LitigationCollector](file:///Users/gorlin/projects/UW/sasha-platform/src/sasha/collect/litigation.py#8-54), [WebCollector](file:///Users/gorlin/projects/UW/sasha-platform/src/sasha/collect/web.py#7-40)) that fetch raw data.
   - Outputs are normalized into a single, comprehensive Pydantic state model called the [Dossier](file:///Users/gorlin/projects/UW/sasha-platform/src/sasha/models/dossier.py#41-69) ([sasha/models/dossier.py](file:///Users/gorlin/projects/UW/sasha-platform/src/sasha/models/dossier.py)).

2. **The Brain (Signal Definitions)**
   - Located in the `brain/` directory.
   - Contains ~450+ underwriting checks defined purely in YAML format. 
   - Signals map to data via dot-path strings (e.g., `data_strategy.field_key: "market.short_percent_float"`).

3. **Declarative Evaluator ([sasha/assess/signals.py](file:///Users/gorlin/projects/UW/sasha-platform/src/sasha/assess/signals.py))**
   - A generic evaluation engine that parses the YAML files.
   - It dynamically resolves the dot-paths against the populated [Dossier](file:///Users/gorlin/projects/UW/sasha-platform/src/sasha/models/dossier.py#41-69) object and evaluates the threshold conditions (e.g., `>`, `<`, `==`) to trigger `RED`, `YELLOW`, or `CLEAR` status flags.
   - *Crucially, this eliminates the need for thousands of lines of hardcoded `if/else` mappers.*

4. **Rendering Layer (`sasha/render/`)**
   - Translates the evaluated [AssessmentDocument](file:///Users/gorlin/projects/UW/sasha-platform/src/sasha/models/document.py#23-40) into a static, standalone report.
   - Powered by Jinja2 templates ([sasha/render/templates/index.html](file:///Users/gorlin/projects/UW/sasha-platform/src/sasha/render/templates/index.html)) using a Capital IQ / McKinsey aesthetic.
   - Replaced interactive HTMX components from the legacy web-app with statically compiled equivalents.

## 3. Current Implementation State
The core pipeline is fully wired and functional. Running the CLI command:
```bash
uv run python -m sasha.cli assess AAPL
```
successfully executes the Pipeline:
1. Initializes all 4 collectors.
2. Constructs the JSON [Dossier](file:///Users/gorlin/projects/UW/sasha-platform/src/sasha/models/dossier.py#41-69).
3. Loads and evaluates all 450+ YAML signals against the [Dossier](file:///Users/gorlin/projects/UW/sasha-platform/src/sasha/models/dossier.py#41-69).
4. Renders a comprehensive static HTML document saved to `output/{TICKER}_assessment.html`.

**Note on Mock Data:**
Currently, [LitigationCollector](file:///Users/gorlin/projects/UW/sasha-platform/src/sasha/collect/litigation.py#8-54) and [WebCollector](file:///Users/gorlin/projects/UW/sasha-platform/src/sasha/collect/web.py#7-40) use mock data. The [SECCollector](file:///Users/gorlin/projects/UW/sasha-platform/src/sasha/collect/sec.py#14-132) uses real `yfinance` filings but has mocked outputs for advanced forensic XBRL metrics (e.g., Beneish M-Score, Accruals).

## 4. Next Implementation Priorities (Your Tasks)

To bring the Sasha Platform to its final production grade, focus on the following implementations:

### Priority A: Data Collection un-mocking
- **Litigation Data:** Implement real API integrations (e.g., SCAC, CourtListener) inside [sasha/collect/litigation.py](file:///Users/gorlin/projects/UW/sasha-platform/src/sasha/collect/litigation.py).
- **Web Context:** Implement the Semantic Web Search inside [sasha/collect/web.py](file:///Users/gorlin/projects/UW/sasha-platform/src/sasha/collect/web.py) to fulfill the "Blind Spot Discovery" mandate (scanning for recent news, executive turnover, regulatory chatter).
- **XBRL Forensics:** Replace the mocked dictionaries in [sasha/collect/sec.py](file:///Users/gorlin/projects/UW/sasha-platform/src/sasha/collect/sec.py) with actual calculated metrics from SEC XBRL data.

### Priority B: Static Charting & Visualizations
- The legacy `do-uw` project contains extensive `matplotlib` charting logic (`do-uw/src/do_uw/stages/render/charts/`) producing Bloomberg-themed visualizations.
- **Task:** Port this charting logic into `sasha-platform`. Since the new rendering pipeline outputs a standalone HTML file without a web server, the charts must be generated as base64-encoded SVG or PNG strings and embedded directly into the Jinja2 context variables.

### Priority C: LLM Head Writer Integration
- The current narrative generation is basic.
- **Task:** Enhance `sasha.document.head_writer` to consume the triggered signals and construct sophisticated, synthesized paragraphs for each report section (e.g., "Financials", "Governance") using an LLM (like Gemini or Claude).

### Priority D: Human-in-the-Loop (Triage Interface)
- Integrate a review mechanism where an underwriter can see the raw pipeline output (confidence scores, automated triggers) before the final narrative is generated, allowing for manual overrides.

## 5. Structuring Signals for the Brain
To preserve the declarative nature of the system, signals in the `brain/` directory should be strictly structured as follows:
- **Domain Categorization**: Group YAML files by their target domain (e.g., `financials/`, [market/](file:///Users/gorlin/projects/UW/sasha-platform/src/sasha/collect/market.py#21-92), [litigation/](file:///Users/gorlin/projects/UW/sasha-platform/src/sasha/collect/litigation.py#13-54), `governance/`) corresponding to the respective [Collector](file:///Users/gorlin/projects/UW/sasha-platform/src/sasha/collect/sec.py#14-132) outputs.
- **Data Strategy Formulation**: Every signal MUST define a `data_strategy` block.
    - [field_key](file:///Users/gorlin/projects/UW/sasha-platform/src/sasha/assess/signals.py#53-81): Use explicit dot-path notation mapping exactly to the [Dossier](file:///Users/gorlin/projects/UW/sasha-platform/src/sasha/models/dossier.py#41-69) state model (e.g., `market.short_percent_float`, `computed.beneish_m_score`).
- **Evaluation Rules**: Define thresholds declaratively (e.g., `operator: ">"`, `value: 10`). Rely on the pipeline's evaluator rather than complex Python logic within the signals.
- **Flexible Evidence Strings**: Use parameterized strings (e.g., `evidence: "Short interest is {market.short_percent_float}% (> 10% threshold)"`) so the Head Writer LLM has precise facts to ground its synthesis.
- **Categorization and Tagging**: Tag signals with metadata (e.g., `#forensic`, `#liquidity_risk`) to enable thematic aggregations during the narrative generation phase.

## 6. Effective Rendering & Display Strategy
Generating an underwriting document requires an intuitive, "Pyramid Principle" display strategy to avoid overwhelming the user with raw data points:

- **Executive Pyramid**: The top of the generated HTML (or UI) must present the synthesized thesis (the LLM abstract), the computed Quality Score, and the overall Risk Tier (WIN, WATCH, WALK, RUN).
- **Thematic Findings (Not Raw Lists)**: Instead of listing 50 individually triggered red flags, group signals thematically using a "Key Findings" pattern. Present 3-5 high-priority synthesized bullet points (e.g., "Elevated Forensic Risk due to M-Score and Aggressive Revenue Recognition").
- **Visual Design (Capital IQ / Bloomberg Aesthetic)**:
    - Build dense, high-contrast visual components (e.g., dark mode charts embedded in clean white reports or full dark-mode terminals).
    - Stick to meaningful palettes: Navy blues/grays for standard data, reserving strict Red/Yellow/Green usage *only* for signal intensity.
    - Provide inline mini-charts (sparklines) for historical context wherever a critical metric is evaluated.
- **Visualizing Risk Posture**:
    - **Peer Radar Chart**: Plot the company's scores across 6 dimensions vs its sector baseline.
    - **Factor Deduction Waterfall**: Visually explain the Quality Score by showing exactly which signal categories (e.g., "Governance Flags: -15 pts") dragged the score down from a perfect 100.
- **Traceability (The Audit Log)**: While the top-level report should be a clean synthesis, every claim must be backed by an **Assessment Audit Log** table at the bottom of the document. This raw table must contain the `Signal ID`, `Intensity`, and `Evidence` to mathematically prove the AI's conclusions and build underwriter trust.

## 7. The Scoring Architecture: Hazard/Agent/Environment (H/A/E)
To accurately quantify claim risk, Sasha implements a multiplicative scoring model based on the H/A/E framework. This replaces the flat additive models of the past. The formula is:
**Claim Risk = Base Rate (Host) * Agent Multiplier * Environment Multiplier**

1. **Host (Base Rate / Susceptibility)**:
   - What is the company's underlying vulnerability based on its structural and historical profile?
   - Examples: Sector base rates, Prior Litigation history, M&A/IPO/SPAC status, high leverage (Debt/EBITDA).
   - *Math*: Starts at a calibrated sector base rate (e.g., TECH = 5.0%, BIOT = 7.0%). Penalties from Host signals are added. Max cap is 50% (0.50).

2. **Agent (Catalyst / Trigger)**:
   - What acute events are actively stressing the company right now?
   - Examples: Catastrophic Stock Drops (>60%), Short Seller Reports, Earnings Misses, Restatements, Auditor Resignations.
   - *Math*: Represented as a multiplier starting at 1.0x. Massive acute events scale this rapidly (e.g., 2.0x, 3.0x).

3. **Environment (Market / Legal Factors)**:
   - What external factors dampen or amplify the risk?
   - Examples: Macroeconomic volatility, specific plaintiff-friendly legal circuits, regulatory shifts.
   - *Math*: Also a multiplier. Can be < 1.0x (mitigating) or > 1.0x (amplifying).

**The 10-Factor Baseline:**
Within the H/A/E model, Signals evaluate against 10 core factors that have proven historical lift ratios for securities class action (SCA) filings:
1. **Prior Litigation** (Weight 20%, ~4.2x lift)
2. **Stock Decline** (Weight 15%, ~3.8x lift)
3. **Restatement/Audit** (Weight 12%, ~4.5x lift)
4. **IPO/SPAC/M&A** (Weight 10%, ~2.8x lift)
5. **Guidance Misses** (Weight 10%, ~2.4x lift)
6. **Volatility** (Weight 9%, ~1.9x lift)
7. **Short Interest** (Weight 8%, ~2.1x lift)
8. **Financial Distress** (Weight 8%, ~2.0x lift)
9. **Governance Issues** (Weight 6%, ~1.3x lift)
10. **Officer Stability** (Weight 2%, ~1.2x lift)

*Crucial Note for Claude*: When expanding the scoring logic in [sasha/assess/scoring/multiplicative.py](file:///Users/gorlin/projects/UW/sasha-platform/src/sasha/assess/scoring/multiplicative.py), ensure that these 10 factors map cleanly into their respective H, A, or E buckets. Signals must be tagged with their respective dimension (Host, Agent, Environment) in their YAML definitions so the evaluator can route their intensity correctly.

## 8. Summary of Recommendations for Claude
- **Data First**: Never write Python logic to map data if a Pydantic dot-path can do it.
- **Strict Separation**: Keep the Brain (YAMLs) completely separated from the Evaluator (Python). 
- **Thematic Narrative**: Prompt the Head Writer LLM to speak in themes, not raw lists.
- **Consulting Aesthetic**: The output HTML must look like a multi-page PDF generated by McKinsey or Capital IQ. Rely heavily on the Jinja2 templates.
- **Actuarial Rigor**: Ensure the H/A/E mathematical structure is preserved. Every triggered flag must mathematically justify the final 'Claim Risk' percentage output.

