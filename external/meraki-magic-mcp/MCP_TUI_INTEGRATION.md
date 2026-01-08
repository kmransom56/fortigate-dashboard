# MCP-TUI Integration Guide

## Overview

The TUI application has been enhanced to use MCP (Model Context Protocol) functions, allowing it to leverage MCP tools and integrate with other AI tools.

## Architecture

```
┌─────────────────────────────────────────┐
│         TUI Application                │
│      (meraki_tui.py)                   │
└─────────────┬───────────────────────────┘
              │
              │ Uses
              ▼
┌─────────────────────────────────────────┐
│      MerakiMCPWrapper                  │
│      (mcp_client.py)                   │
│                                         │
│  • Wraps MCP tools                      │
│  • Falls back to direct API             │
│  • Handles JSON parsing                 │
└─────────────┬───────────────────────────┘
              │
      ┌───────┴───────┐
      │               │
┌─────▼─────┐   ┌─────▼─────┐
│ MCP Tools │   │ Direct    │
│ (via MCP  │   │ Meraki    │
│  module)  │   │ API       │
└───────────┘   └───────────┘
```

## Features

### 1. MCP Integration
- TUI uses MCP tools when available
- Automatic fallback to direct API if MCP fails
- Benefits from MCP caching and error handling

### 2. Unified Interface
- Same API calls work with or without MCP
- Transparent switching between MCP and direct API
- No code changes needed in TUI logic

### 3. Future AI Tool Integration
- Architecture supports adding other AI tools
- MCP client can be extended for other MCP servers
- Chat interface can route to different AI tools

## Usage

### Running with MCP (Default)

```bash
# TUI automatically uses MCP tools
./launch-tui.sh

# Or directly
python3 meraki_tui.py
```

### Running without MCP (Direct API)

```bash
# Disable MCP, use direct API only
python3 meraki_tui.py --no-mcp
```

## How It Works

### 1. Initialization

```python
# TUI creates MCP wrapper
self.meraki_api = MerakiMCPWrapper(use_mcp=True)

# Wrapper tries to load MCP module
# Falls back to direct API if MCP unavailable
```

### 2. API Calls

```python
# TUI calls wrapper methods
networks = self.meraki_api.get_organization_networks(org_id)

# Wrapper:
# 1. Tries MCP tool first
# 2. Parses JSON response if needed
# 3. Falls back to direct API on error
```

### 3. MCP Tool Execution

```python
# MCP client imports MCP module dynamically
# Calls internal MCP functions directly
# Returns results (handles JSON strings)
```

## Benefits

### MCP Advantages
- ✅ **Caching**: MCP caches read operations (reduces API calls)
- ✅ **Error Handling**: Better error messages and retry logic
- ✅ **Rate Limiting**: Automatic rate limit handling
- ✅ **Response Management**: Handles large responses intelligently
- ✅ **Read-Only Mode**: Safety mode for exploration

### Direct API Advantages
- ✅ **No Dependencies**: Works without MCP module
- ✅ **Simpler**: Direct calls, no JSON parsing
- ✅ **Faster**: No module import overhead

## Extending for Other AI Tools

### Adding New MCP Server

```python
# In mcp_client.py
class MultiMCPClient:
    def __init__(self):
        self.meraki_client = MCPClient("meraki-mcp-dynamic.py")
        self.other_client = MCPClient("other-mcp-server.py")
    
    def call_tool(self, server: str, tool: str, **kwargs):
        if server == "meraki":
            return self.meraki_client.call_mcp_tool(tool, **kwargs)
        elif server == "other":
            return self.other_client.call_mcp_tool(tool, **kwargs)
```

### Adding AI Chat Integration

```python
# In meraki_tui.py process_chat_message()
async def process_chat_message(self, message: str):
    # Try MCP tools first
    result = await self.try_mcp_api_call(message)
    
    # If no MCP match, try other AI tools
    if not result:
        result = await self.try_ai_tool_call(message)
    
    # Fallback to help
    if not result:
        self.show_help()
```

## Configuration

### Environment Variables

Both MCP and TUI use the same `.env`:

```env
MERAKI_API_KEY="your_key"
MERAKI_ORG_ID="default_org_id"

# MCP-specific (used when MCP is enabled)
ENABLE_CACHING=true
CACHE_TTL_SECONDS=300
READ_ONLY_MODE=false
```

## Troubleshooting

### MCP Not Working

1. **Check MCP module loads:**
   ```python
   python3 -c "from mcp_client import MCPClient; c = MCPClient(); print(c.get_meraki_tools())"
   ```

2. **Check MCP script path:**
   - Default: `meraki-mcp-dynamic.py` in same directory
   - Can be overridden in `MCPClient(mcp_script_path="...")`

3. **Fallback to direct API:**
   - TUI automatically falls back if MCP fails
   - Use `--no-mcp` flag to disable MCP entirely

### Performance Issues

- **MCP caching**: Enable `ENABLE_CACHING=true` in `.env`
- **Direct API**: Use `--no-mcp` if MCP adds overhead
- **Large responses**: MCP handles truncation automatically

## Future Enhancements

### Planned Features

1. **Multiple MCP Servers**
   - Support for other MCP tools (file system, git, etc.)
   - Tool routing based on query type

2. **AI Chat Integration**
   - Connect to Claude/OpenAI APIs
   - Natural language query processing
   - Context-aware responses

3. **Tool Discovery**
   - Auto-discover available MCP tools
   - Show available tools in TUI help
   - Dynamic tool registration

4. **Response Streaming**
   - Stream large responses
   - Progress indicators
   - Incremental updates

## Code Structure

```
meraki-magic-mcp/
├── meraki_tui.py          # TUI application (uses MCP wrapper)
├── mcp_client.py          # MCP client wrapper
├── meraki-mcp-dynamic.py  # MCP server (provides tools)
└── .env                   # Shared configuration
```

## Examples

### Using MCP Tools in TUI

```python
# In TUI chat, user types:
"Show me firewall rules for network Main Office"

# TUI processes:
result = self.meraki_api.call_meraki_api(
    section="appliance",
    method="getNetworkApplianceFirewallL3FirewallRules",
    parameters={"networkId": network_id}
)

# MCP wrapper:
# 1. Calls MCP tool (with caching)
# 2. Returns parsed result
# 3. TUI displays in chat
```

### Adding Custom Tool

```python
# In mcp_client.py
def get_custom_data(self, org_id: str):
    """Custom tool using MCP"""
    return self.mcp_client.call_mcp_tool(
        "call_meraki_api",
        section="organizations",
        method="getOrganizationInventory",
        parameters={"organizationId": org_id}
    )
```

## See Also

- [README.md](README.md) - Main project documentation
- [TUI-README.md](TUI-README.md) - TUI-specific documentation
- [README-DYNAMIC.md](README-DYNAMIC.md) - MCP server documentation
