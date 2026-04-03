# Brain Analyzer MCP Server

Read-only analysis of brain YAML signals. Provides metrics, validation, and coverage reporting without modifying the brain.

## Purpose

The brain analyzer MCP server allows external tools (like OpenCode agents) to inspect the brain's YAML signal definitions while maintaining **brain portability**:

- **Read-only**: Never modifies YAML files
- **Cache directory storage**: Analysis results stored in `.cache/` not `brain/`
- **Uses existing Pydantic schema**: Validates with `BrainSignalEntry` from `brain_signal_schema.py`
- **No business logic**: Pure analysis, no scoring or evaluation

## Tools

The server provides 4 tools:

### 1. `brain_analyzer_list_signals`
List brain signals with metadata.

**Parameters:**
- `limit` (default: 100): Maximum number of signals to return
- `offset` (default: 0): Offset for pagination

**Returns:** Array of signal objects with `id`, `name`, `work_type`, `layer`, `factors`, `rap_class`, `schema_version`.

### 2. `brain_analyzer_get_signal`
Get detailed information about a specific signal.

**Parameters:**
- `signal_id` (required): Signal ID (e.g., `GOV.BOARD.independence`)

**Returns:** Complete `BrainSignalEntry` object with all fields.

### 3. `brain_analyzer_compute_metrics`
Compute comprehensive metrics about brain signals.

**Parameters:** None

**Returns:** Metrics object with:
- `total_signals`: Count of all loaded signals
- `signals_by_layer`: Distribution across signal/hazard/data_element/peril_confirming
- `signals_by_work_type`: Distribution across evaluate/extract/display/infer/acquire
- `signals_by_factor`: Count per factor (F1-F10)
- `signals_by_peril`: Count per peril ID (empty until peril IDs are populated)
- `signals_by_rap_class`: Distribution across host/agent/environment
- `signals_by_schema_version`: Count per schema version (1, 3, 4)
- `data_source_coverage`: Which data sources signals require
- `required_data_coverage`: Which data types signals require

### 4. `brain_analyzer_validate_yaml`
Validate brain YAML files and report errors.

**Parameters:** None

**Returns:** Validation object with:
- `valid`: Boolean indicating if all YAML files are valid
- `error_count`: Number of validation errors
- `warning_count`: Number of warnings (empty files)
- `errors`: Array of error messages (max 50)
- `warnings`: Array of warning messages (max 50)

## Configuration

### OpenCode Configuration

Add to `opencode.json`:

```json
{
  "mcp": {
    "brain-analyzer": {
      "type": "local",
      "command": [".venv/bin/python", "-m", "do_uw.mcp_servers.brain_analyzer"],
      "enabled": true,
      "environment": {
        "BRAIN_ROOT": "src/do_uw/brain"
      }
    }
  }
}
```

### Environment Variables

- `BRAIN_ROOT`: Path to brain directory (default: `src/do_uw/brain`)
- `BRAIN_ANALYZER_CACHE`: Whether to cache loaded signals (default: true, not yet implemented)

## Usage Examples

### Python Client

```python
import asyncio
from mcp import StdioServerParameters, ClientSession
from mcp.client.stdio import stdio_client

async def analyze_brain():
    server_params = StdioServerParameters(
        command=".venv/bin/python",
        args=["-m", "do_uw.mcp_servers.brain_analyzer"],
        env={"BRAIN_ROOT": "src/do_uw/brain"}
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize(
                name="my-client",
                version="0.1.0"
            )
            
            # Get metrics
            tools = await session.list_tools()
            print(f"Tools: {[t.name for t in tools]}")
            
            # Compute metrics
            result = await session.call_tool(
                "brain_analyzer_compute_metrics",
                arguments={}
            )
            print(f"Metrics: {result.content[0].text}")
```

### Command Line Test

```bash
# Start server manually
BRAIN_ROOT=src/do_uw/brain .venv/bin/python -m do_uw.mcp_servers.brain_analyzer

# In another terminal, send JSON-RPC messages
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"0.1.0","capabilities":{},"clientInfo":{"name":"test","version":"0.1.0"}}}' | nc localhost ...
```

## Brain Portability Guarantee

The analyzer respects the **brain portability constraint**:

1. **YAML files are the only source of truth** - analyzer reads directly from `brain/signals/*.yaml`
2. **No modifications** - analyzer never writes to brain files
3. **Cache separation** - any cached data stored in `.cache/` not `brain/`
4. **Schema validation** - uses same `BrainSignalEntry` schema as production pipeline
5. **No business logic** - only analysis, no scoring thresholds or evaluation logic

This ensures the brain remains portable: YAML + manifest + evaluation results produce identical worksheets from separate systems.

## Implementation Details

- **Location**: `src/do_uw/mcp_servers/brain_analyzer/`
- **Server**: `server.py` - MCP stdio server implementation
- **Entry point**: `__main__.py` - runs `asyncio.run(main())`
- **Dependencies**: `mcp` package (already in `pyproject.toml`)

## Testing

```bash
# Test brain signal loading
uv run python test_brain_load.py

# Test server startup
python -m do_uw.mcp_servers.brain_analyzer &
sleep 2
kill %1
```

## Stats (as of 2026-03-31)

- **601 signals** loaded successfully
- **Layers**: 410 signal, 137 hazard, 3 data_element, 25 peril_confirming, 26 None
- **Work types**: 448 evaluate, 104 extract, 2 display, 21 infer, 26 acquire
- **Factors**: F3 (127), F10 (122), F1 (81), F9 (46), F6 (39), F2 (32), F7 (32), F5 (33), F8 (15), F4 (21)
- **RAP classes**: host (204), agent (269), environment (128)
- **Schema versions**: v1 (48), v3 (513), v4 (40)
- **Validation**: All YAML files valid, 0 errors, 0 warnings