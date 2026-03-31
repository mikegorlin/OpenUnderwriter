# OpenCode Configuration for D&O Underwriting

## Purpose
Dedicated OpenCode environment with MCP servers, agent swarm, and Supabase connectivity for the D&O Underwriting Worksheet System. This environment is separate from Claude Desktop and uses DeepSeek Reasoner model in Warp terminal.

## Quick Start

1. **Navigate to this worktree**:
   ```bash
   cd /Users/gorlin/projects/UW/do-uw/.opencode/worktrees/opencode-do
   ```

2. **Load environment variables** (OpenCode may not auto‑load `.env`):
   ```bash
   export $(grep -v '^#' .env | xargs)
   ```

3. **Launch OpenCode** (must be installed globally):
   ```bash
   opencode
   ```

4. **Verify MCP servers** (within OpenCode session):
   ```
   /mcp list
   ```

## Configuration Files

- `opencode.json` – MCP server definitions (edgartools, context7, playwright, fetch, supabase, etc.)
- `.env` – API keys and database credentials (do not commit)
- `package.json` – Node dependencies for MCP servers
- `profile.md` – User profile with D&O domain knowledge
- `oh‑my‑opencode.json` – Agent swarm settings (Sisyphus default)

## MCP Server Status

| Server | Status | Notes |
|--------|--------|-------|
| edgartools | ✅ Connected | SEC EDGAR/XBRL data via Python MCP |
| context7 | ✅ Connected | Remote library documentation |
| playwright | ✅ Connected | Browser automation for scraping |
| fetch | ✅ Connected | URL content extraction |
| supabase | ✅ Connected | GorlinBase D&O database |
| brave‑search | ⚠️ Disabled | Needs `BRAVE_API_KEY` |
| github | ⚠️ Disabled | Needs `GITHUB_TOKEN` |
| duckdb | ⚠️ Disabled | Dist files missing; disabled |

## Agent Swarm & GSD Workflows

- **Oh‑my‑openagent plugin** enabled with default agent “Sisyphus”
- **GSD enforcement active** – all work must start via `/gsd:*` commands
- **5‑agent concurrency** for parallel task execution

## D&O Pipeline Integration

The main `do‑uw` codebase is accessible from this environment. Recent fixes applied:

- Output file naming with date+version (`AAPL_20260329_v0_2_0_worksheet.html`)
- HTML‑only output configuration (`formats` parameter)
- MARKET_SHORT and SEC_ENFORCEMENT data acquisition
- LLM extractor bug fixes for competitive extraction

**Run a test analysis** (from project root, not this worktree):
```bash
cd /Users/gorlin/projects/UW/do-uw
uv run angry-dolphin analyze AAPL --fresh --no-llm
```

## Testing MCP Servers Manually

```bash
# Supabase
node ./node_modules/.bin/supabase-mcp-claude

# edgartools
../../../.venv/bin/python -m edgar.ai.mcp.server

# playwright & fetch
./node_modules/.bin/playwright-mcp --help
./node_modules/.bin/fetch-mcp --help
```

## Next Steps

1. **Obtain API keys** for Brave Search and GitHub; add to `.env`
2. **Rebuild duckdb‑mcp** (`npm rebuild duckdb‑mcp`) or reinstall
3. **Test pipeline completion** – fix USPTO patent fetch retry loop
4. **Verify HTML output** matches Card Catalog Design System v4

## Support

- OpenCode documentation: https://opencode.ai
- MCP server packages: npmjs.com (search `‑mcp‑server`)
- D&O project: `CLAUDE.md` for architecture and rules

---

*Configuration generated: March 29, 2026*