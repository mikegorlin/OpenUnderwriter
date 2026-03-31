# OpenCode Setup for D&O Underwriting System

## Overview
OpenCode (running in Warp terminal with DeepSeek Reasoner model) has been configured to support all MCP servers from the D&O underwriting pipeline while maintaining complete separation from Claude Desktop setup.

## Worktree Strategy
- **Main directory**: `/Users/gorlin/projects/UW/do-uw/` (on `main` branch)
- **OpenCode worktree**: `/Users/gorlin/projects/UW/do-uw/.opencode/worktrees/opencode-do/` (on `opencode-do` branch)
- **Isolation**: No files touched on main branch - all OpenCode work isolated to worktree
- **Transfer capability**: Easy transfer of developments between Claude and OpenCode via branch merging

## MCP Server Configuration

### ✅ Working (Configured & Tested)
1. **edgartools** — SEC EDGAR filings, XBRL data
   - Command: `../../../.venv/bin/python -m edgar.ai.mcp.server`
   - Environment: `EDGAR_IDENTITY="do-uw/0.1.0 (contact@example.com)"`

2. **context7** — Up-to-date library documentation
   - Type: Remote server at `https://mcp.context7.com/mcp`

3. **playwright** — Browser automation for scraping dynamic sites
   - Command: `playwright-mcp`
   - Installed: `@playwright/mcp` (0.0.68)

4. **fetch** — Simple URL content extraction
   - Command: `fetch-mcp`
   - Installed: `fetch-mcp` (0.0.5)

5. **supabase** — GorlinBase D&O underwriting database
   - Command: `supabase-mcp`
   - Installed: `supabase-mcp` (1.5.0)
   - Environment variables set from marketprice skill

### ⚠️ Installed but Needs API Keys
6. **brave-search** — Web search with news/domain filtering (2,000 free/month)
   - Command: `brave-search-mcp-server`
   - Installed: `@brave/brave-search-mcp-server` (2.0.75)
   - Status: Disabled (needs `BRAVE_API_KEY`)
   - Get key: https://brave.com/search/api/

7. **github** — Dev workflow (issues, PRs)
   - Command: `github-mcp`
   - Installed: `github-mcp` (0.0.7)
   - Status: Disabled (needs `GITHUB_TOKEN`)
   - Optional: Generate personal access token

### 🤖 oh-my-openagent Built-in MCPs
The plugin provides these MCP servers automatically:
- **Exa** — Neural web search (needs `EXA_API_KEY`)
- **Context7** — Already configured separately
- **Grep.app** — GitHub code search

## Environment Variables
Created `.env` file with:
- **Supabase credentials** from GorlinBase D&O database (URL, ANON_KEY, SERVICE_ROLE_KEY)
- **MCP_API_KEY** set to `test-key` (required by supabase-mcp)
- **ANTHROPIC_API_KEY** and **SERPER_API_KEY** from main .env
- **Placeholders** for BRAVE_API_KEY, GITHUB_TOKEN, EXA_API_KEY

Run setup script: `source setup_opencode.sh`

## Agent Swarm & GSD Integration

### oh-my-openagent Plugin Features
- **Default agent**: Sisyphus (orchestrator)
- **Other agents**: Hephaestus, Prometheus, Oracle, Librarian, Explore
- **GSD enforcement**: `npx oh-my-opencode run` waits for todo completion
- **Parallel background agents**: Configurable concurrency limits
- **Configuration**: `.opencode/oh-my-opencode.json`

### GSD Wrapper Script
Created `gsd` script in worktree root that:
1. Validates environment
2. Runs GSD with oh-my-openagent integration
3. Ensures disciplined task completion

## User Knowledge Transfer

Created `USER_PROFILE.md` with:
- **Mike Gorlin**: Head of underwriting at GorlinBase MGA, 25 years experience
- **Working style**: Direct, concise, action-oriented
- **Key systems**: GitHub (mikegorlin), Obsidian, Open Brain, Supabase
- **D&O domain knowledge**: Project architecture, critical rules, pipeline stages
- **Current phase**: Card Catalog Design System v4 (62 cards across 13 sections)

## Testing & Verification

### 1. Environment Setup
```bash
cd /Users/gorlin/projects/UW/do-uw/.opencode/worktrees/opencode-do
source setup_opencode.sh
```

### 2. MCP Connectivity Test
In OpenCode terminal:
```
/mcp list
```
Should show: edgartools, context7, playwright, fetch, supabase

### 3. Pipeline Test
```bash
# From main directory
./gsd analyze AAPL
# Or
cd ../.. && angry-dolphin analyze AAPL
```

### 4. Agent Swarm Test
```bash
npx oh-my-opencode run "Test D&O pipeline analysis"
```

## Files Created

### Configuration Files
- `opencode.json` — MCP server configurations
- `.env` — Environment variables (contains Supabase keys)
- `.env.example` — Template for missing API keys
- `.opencode/oh-my-opencode.json` — Plugin configuration

### Documentation
- `USER_PROFILE.md` — User knowledge transfer
- `OPENCODE.md` — Original setup documentation (447 lines)
- `README_OPENCODE.md` — This summary

### Scripts
- `setup_opencode.sh` — Environment setup script
- `gsd` — GSD wrapper script (executable)

### Node.js Dependencies
- `package.json` — MCP server packages
- `package-lock.json` — Locked dependencies
- `node_modules/` — Installed packages

## Next Steps

### Immediate (Before Using OpenCode)
1. **Get API keys**:
   - Brave Search API: https://brave.com/search/api/
   - Exa API (for neural search): https://exa.ai/
   - GitHub Token (optional): https://github.com/settings/tokens

2. **Update `.env`** with obtained keys
3. **Enable MCP servers** in `opencode.json` by setting `"enabled": true`

### Medium Term
1. **Test MCP integration** in ACQUIRE stage of pipeline
2. **Implement Supabase queries** for D&O pricing data lookup
3. **Create OpenCode skills** equivalent to Claude Desktop skills:
   - `marketprice` — D&O pricing database
   - `biotech-uw` — Biotech risk analysis
   - `tower-visual` — Tower HTML reports

### Long Term
1. **Parallel agent execution** for pipeline stages
2. **Automated quality checks** using agent swarm
3. **Knowledge sync** between OpenCode and Claude Desktop via git merging

## Git Operations

### Push OpenCode changes to main
```bash
# From main directory
git checkout main
git merge opencode-do --no-ff
git push origin main
```

### Pull OpenCode changes from Claude work
```bash
# From OpenCode worktree
git fetch origin
git merge origin/main
```

### Worktree management
```bash
# Create new worktree
git worktree add ../do-uw-opencode opencode-do

# Remove worktree
git worktree remove .opencode/worktrees/opencode-do
```

## Architecture Notes

### MCP Boundary Enforcement
- MCP tools (EdgarTools, Brave Search, Playwright, Fetch) used ONLY in ACQUIRE stage
- Subagents CANNOT access MCP tools — all data acquisition happens in main context
- EXTRACT and later stages operate on local data only

### Data Source Priority (NON-NEGOTIABLE)
1. **XBRL/SEC filings** — ALWAYS primary (audited, authoritative)
2. **yfinance** — FALLBACK only (real-time price, market data)
3. **Web search** — Blind spot detection, cross-validation

### Brain Source of Truth
- **YAML files** are ONLY source of truth for brain signals
- **DuckDB** (`brain.duckdb`) is PROCESSING/CACHE database ONLY
- NEVER query brain.duckdb to read signal definitions — always read YAML files

---

## Status: Ready for Testing
OpenCode is configured with all essential MCP servers for D&O underwriting pipeline execution. Missing API keys for brave-search and github can be added as needed. Supabase connectivity to GorlinBase database is fully configured and ready for queries.