# Reusable AI Assistant Framework Integration

## Overview

The Meraki Magic MCP TUI has been integrated with the reusable AI assistant framework from `/reusable`, providing standard AI capabilities across your applications.

## What Was Integrated

### Core Components

1. **AIAssistant** - High-level AI operations
   - Audit: Analyze code, configuration, security
   - Repair: Fix issues automatically
   - Optimize: Improve performance
   - Learn: Build knowledge base from codebase

2. **AgentFrameworkWrapper** - Multi-backend AI support
   - OpenAI
   - Anthropic (Claude)
   - AutoGen
   - Magentic-One
   - Docker CAgent

3. **SecureKeyManager** - Encrypted API key storage
   - Secure key management
   - Environment variable fallback
   - App-specific storage

4. **Simple AI Functions** - Easy-to-use wrappers
   - `audit_file()` - Audit files
   - `repair_code()` - Repair issues
   - `optimize_code()` - Optimize code
   - `learn_from_codebase()` - Learn from code

## Features Added to TUI

### AI Commands in Chat

The TUI chat now supports AI assistant commands:

```
audit meraki_tui.py security    # Security audit
repair "function is slow" meraki_tui.py  # Get repair suggestions
optimize mcp_client.py performance  # Performance optimization
learn architecture  # Learn about codebase architecture
```

### Natural Language Queries

The TUI can now use AI to understand natural language queries about Meraki networks:

```
"What are the firewall rules for the main network?"
"Show me devices that are offline"
"Analyze the network configuration"
```

### Automatic Backend Detection

- Auto-detects available AI backends from environment variables
- Falls back gracefully if AI not available
- Supports multiple backends (OpenAI, Anthropic, etc.)

## Usage

### Basic Usage

```bash
# Launch TUI with AI assistant (default)
./launch-tui.sh

# Or directly
python3 meraki_tui.py
```

### Disable AI

```bash
# Run without AI assistant
python3 meraki_tui.py --no-ai

# Run without MCP
python3 meraki_tui.py --no-mcp

# Run without both
python3 meraki_tui.py --no-mcp --no-ai
```

### Configure AI Backend

Set environment variables for your preferred backend:

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic (Claude)
export ANTHROPIC_API_KEY="sk-ant-..."

# AutoGen
export AUTOGEN_API_KEY="..."

# Magentic-One
export MAGENTIC_ONE_API_KEY="..."
```

Or use the configuration file:
```bash
python3 -c "from reusable.config import AIConfig; from reusable.agent_framework_wrapper import AgentBackend; AIConfig.set_backend(AgentBackend.OPENAI)"
```

## Architecture

```
┌─────────────────────────────────────────┐
│         TUI Application                │
│      (meraki_tui.py)                   │
└─────────────┬───────────────────────────┘
              │
      ┌───────┴───────┐
      │               │
┌─────▼─────┐   ┌─────▼─────┐
│ MCP Tools  │   │ AI Tools  │
│            │   │           │
│ • Meraki   │   │ • Audit   │
│   API      │   │ • Repair  │
│ • Caching  │   │ • Optimize│
│ • 804+     │   │ • Learn   │
│   methods  │   │ • NLP     │
└────────────┘   └───────────┘
```

## Integration Details

### Code Changes

1. **Import Reusable Framework**
   ```python
   from reusable.simple_ai import (
       get_ai_assistant,
       audit_file,
       repair_code,
       optimize_code,
       learn_from_codebase
   )
   ```

2. **Initialize AI Assistant**
   ```python
   self.ai_assistant = get_ai_assistant(
       app_name="meraki_magic_mcp",
       auto_setup=False
   )
   ```

3. **Handle AI Commands**
   - `handle_ai_audit()` - Process audit commands
   - `handle_ai_repair()` - Process repair commands
   - `handle_ai_optimize()` - Process optimize commands
   - `handle_ai_learn()` - Process learn commands
   - `try_ai_or_mcp_query()` - Natural language queries

### Command Routing

The TUI routes commands intelligently:

1. **Built-in Commands** (show networks, show devices, etc.)
2. **AI Commands** (audit, repair, optimize, learn)
3. **AI Natural Language** (if AI available)
4. **MCP API Calls** (fallback for Meraki-specific queries)

## Examples

### Audit Code

```
User: audit meraki_tui.py security
TUI: 🔍 Auditing meraki_tui.py (security)...
     **Audit Results:**
     - Found 3 potential security issues
     - API keys should not be logged
     - Input validation needed for user commands
```

### Repair Issues

```
User: repair "function is too slow" mcp_client.py
TUI: 🔧 Analyzing repair for: function is too slow...
     **Repair Analysis:**
     - Consider caching API responses
     - Use async/await for concurrent calls
     - Suggested code changes...
```

### Natural Language Query

```
User: What are the firewall rules for the main network?
TUI: **AI Response:**
     I'll help you get the firewall rules. Let me query the Meraki API...
     [Calls MCP tool to get firewall rules]
     **Firewall Rules:**
     [Displays rules]
```

## Benefits

### Standardized AI Features

- ✅ Same AI framework across all your applications
- ✅ Consistent API for audit, repair, optimize, learn
- ✅ Multi-backend support (OpenAI, Anthropic, etc.)
- ✅ Secure key management

### Enhanced TUI

- ✅ AI-powered natural language understanding
- ✅ Code audit and repair capabilities
- ✅ Optimization suggestions
- ✅ Knowledge base learning

### Extensibility

- ✅ Easy to add more AI backends
- ✅ Can integrate other reusable components
- ✅ Modular architecture

## Configuration

### Environment Variables

```env
# AI Backend API Keys
OPENAI_API_KEY="sk-..."
ANTHROPIC_API_KEY="sk-ant-..."
AUTOGEN_API_KEY="..."
MAGENTIC_ONE_API_KEY="..."

# Meraki API (existing)
MERAKI_API_KEY="..."
MERAKI_ORG_ID="..."
```

### Configuration File

The AI framework uses `~/.network_observability_ai_config.json`:

```json
{
  "backend": "openai",
  "backend_config": {
    "model": "gpt-4",
    "temperature": 0.7
  }
}
```

## Troubleshooting

### AI Not Available

If you see "⚠️ AI Assistant Not Available":

1. **Check API Keys:**
   ```bash
   echo $OPENAI_API_KEY
   echo $ANTHROPIC_API_KEY
   ```

2. **Check Reusable Directory:**
   ```bash
   ls reusable/
   ```

3. **Test AI Assistant:**
   ```python
   from reusable.simple_ai import get_ai_assistant
   assistant = get_ai_assistant()
   ```

### Backend Not Working

1. **List Available Backends:**
   ```python
   from reusable.config import AIConfig
   print(AIConfig.list_available_backends())
   ```

2. **Set Backend Manually:**
   ```python
   from reusable.config import AIConfig
   from reusable.agent_framework_wrapper import AgentBackend
   AIConfig.set_backend(AgentBackend.OPENAI)
   ```

## Future Enhancements

### Planned Features

1. **More AI Commands**
   - `update [file]` - Update code
   - `test [file]` - Generate tests
   - `document [file]` - Generate documentation

2. **Context Awareness**
   - Remember previous queries
   - Learn from user patterns
   - Suggest relevant commands

3. **Integration with Other Tools**
   - File system operations
   - Git operations
   - Database queries

## See Also

- [MCP_TUI_INTEGRATION.md](MCP_TUI_INTEGRATION.md) - MCP integration details
- [TUI-README.md](TUI-README.md) - TUI documentation
- [reusable/](reusable/) - Reusable framework source

## Summary

✅ **Integration Complete**

The TUI now has:
- ✅ AI assistant framework integrated
- ✅ Audit, repair, optimize, learn commands
- ✅ Natural language query support
- ✅ Multi-backend AI support
- ✅ Secure key management
- ✅ Standardized across applications

The reusable framework is now a standard feature of the Meraki Magic MCP TUI!
