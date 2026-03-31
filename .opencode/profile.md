# OpenCode User Profile: Mike Gorlin

## User Identity
- **Name**: Mike Gorlin
- **Role**: Head of underwriting at GorlinBase MGA (Managing General Agent)
- **Experience**: 25 years of commercial underwriting experience
- **Technical proficiency**: Builds his own tools, skills, and systems. Hands-on with code.
- **Work environment**: Uses Claude Code, Claude Desktop, Obsidian, Supabase, GitHub (mikegorlin)
- **Email**: Outlook (not Gmail)

## Communication Style
- **Direct and concise**: No preamble, no over-explaining, no filler
- **Fast typing with typos**: Never correct spelling — understand intent
- **Low confirmation threshold**: Don't ask for confirmation on low-risk, reversible things
- **Short answers preferred**: "yes", "do it", "got it" = trust the direction
- **No summaries**: Don't summarize what just happened
- **No repetition**: Don't repeat back what was said
- **Action-oriented**: Lead with action, not explanation
- **When given a location**: Go there directly, don't over-search

## Thinking Patterns
- **End-to-end thinking**: Before proposing, walk through: new machine, missing files, sync across devices, degraded states
- **Bias toward action**: If intent is 80% clear, execute. Ask only when genuinely ambiguous
- **Collapse steps**: Don't create artificial checkpoints between read, decide, and act
- **Pre-purchase failure mode analysis**: Walk through failure modes yourself first
- **Practical over elegant**: Will it work tomorrow on a different machine?
- **Version identification**: When multiple versions exist, identify the latest and skip the rest

## Key Systems
- **GitHub**: mikegorlin
- **Obsidian Vault**: GorlinVaultRemote (synced across devices)
- **Open Brain**: Supabase-based thought capture (MCP tools: capture_thought, search_thoughts)
- **Underwriting bench**: `~/projects/UW/do-uw` (angry-dolphin CLI — `analyze <TICKER>`)
- **MCP integrations**: Supabase, Open Brain, EdgarTools, Brave Search, Playwright, Fetch, Context7, DuckDB, GitHub

## D&O Underwriting Domain Knowledge
- **Industry focus**: Biotech & life sciences D&O risk analysis (specialized framework)
- **Database**: GorlinBase D&O pricing and underwriting database (Supabase: jfqenpobwadlhuvseiax.supabase.co)
- **Data scope**: 4,275 accounts, 3,454 programs, 5,223 layers, 1,296 carriers
- **Pricing metrics**: ROL (rate on line), ROU (rate on unit), rate per million, retention/SIR, quota share, part-off
- **Workflow**: Ticker analysis → risk assessment → tower visualization → proposal generation
- **Output quality**: Professional D&O tower visual HTML reports with pixel-perfect CSS

## Current Project: D&O Underwriting Worksheet System
- **Product motto**: "The single source of truth for underwriters to make the most knowledgeable decisions on a risk."
- **Architecture**: 7-stage pipeline (RESOLVE → ACQUIRE → EXTRACT → ANALYZE → SCORE → BENCHMARK → RENDER)
- **State management**: Single Pydantic `AnalysisState` model as source of truth
- **Brain framework**: YAML-based (brain/signals/*.yaml, 36 files, 600+ signals)
- **Visual system**: Card Catalog Design System v4 with 4-layer architecture (Data Pool → Card Registry → Design Elements → Rendered Worksheet)
- **Card registry**: 62 lego-brick cards across 13 sections
- **Design elements**: 88 chart styles, 56 components
- **Output formats**: HTML (primary), Word, PDF, Markdown

## Critical Rules (NON-NEGOTIABLE)
1. **Brain source of truth**: YAML files are ONLY source for brain signals/sections/config
2. **Narrative quality**: Every sentence must contain company-specific data (dollar amounts, percentages, dates)
3. **Data integrity**: Every data point MUST have source and confidence fields
4. **XBRL first**: XBRL/SEC filings are ALWAYS primary data source for financial metrics
5. **IPO-specific treatment**: Mandatory for companies public < 5 years
6. **Root-cause problem solving**: A patch is NEVER a solution
7. **Visual quality**: NEVER make things look worse; match references pixel-for-pixel
8. **Self-verification**: NEVER show output without verifying it yourself first
9. **Pipeline execution discipline**: Monitor pipeline to completion
10. **Preserve before improve**: NEVER remove existing analytical capabilities

## OpenCode Integration
- **Worktree strategy**: Main directory (`main` branch) vs. `.opencode/worktrees/opencode-do/` (`opencode-do` branch)
- **MCP servers configured**: edgartools, context7, playwright, fetch, supabase (brave-search and github disabled pending API keys)
- **Plugin**: oh-my-openagent with agent swarm (Sisyphus, Hephaestus, Prometheus, Oracle, Librarian, Explore)
- **GSD enforcement**: `npx oh-my-opencode run` waits for todo completion
- **Design superpowers**: stylelint, htmlhint, axe-core, purgecss, csso, pixelmatch installed
- **Supabase connectivity**: Credentials in `.env` file

## Skill Mapping (Claude Desktop → OpenCode)
- **marketprice**: Query/update GorlinBase D&O pricing database (use Supabase MCP)
- **biotech-uw**: Biotech & life sciences D&O risk analysis (apply biotech framework)
- **tower-visual**: Generate professional D&O tower visual HTML reports
- **shopping-sherpa**: Product research and shopping assistant (not directly applicable)
- **chef-gpt**: Cooking assistant (not directly applicable)
- **open-brain-companion**: Open Brain system setup/troubleshooting (use capture_thought/search_thoughts MCP)

## Working Style with OpenCode
- **Agent swarm**: Use parallel agents for independent tasks
- **GSD workflow**: Start with `/gsd:quick`, `/gsd:debug`, or `/gsd:execute-phase`
- **MCP boundary**: MCP tools used ONLY in ACQUIRE stage; subagents cannot access MCP tools
- **Data acquisition**: Use edgartools for SEC filings, playwright for dynamic sites, fetch for URL content
- **Blind spot detection**: Include proactive discovery searches at START of ACQUIRE
- **Cross-validation**: Every finding should be cross-validated against at least 2 sources

## File Structure Awareness
- `src/do_uw/` – Core application code
- `brain/` – YAML brain framework (signals, sections, framework)
- `config/` – JSON scoring weights, thresholds, patterns
- `stages/` – 7 pipeline stages
- `templates/html/` – HTML/CSS templates (catalog.css)
- `output/` – Analysis outputs
- `.planning/` – Project documentation and state tracking
- `.opencode/` – OpenCode-specific configuration

## Testing & Verification
- **Unit/integration**: `uv run pytest`
- **Visual regression**: `VISUAL_REGRESSION=1 uv run pytest tests/test_visual_regression.py`
- **Performance budget**: `PERFORMANCE_TESTS=1 uv run pytest tests/test_performance_budget.py`
- **Cross-ticker QA**: `uv run python scripts/qa_compare.py`
- **Self-review loop**: After generating output, review yourself, critique, identify improvements, fix, re-render

---

*This profile is automatically loaded into OpenCode context. Update when user preferences or systems change.*