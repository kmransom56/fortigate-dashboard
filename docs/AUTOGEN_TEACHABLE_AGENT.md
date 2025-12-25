# AutoGen Teachable Agent Integration

## Overview

The FortiGate Dashboard now includes a fully integrated AutoGen Teachable Agent that can learn from interactions and improve over time. The agent is integrated with the AI healer, knowledge base, and platform skills.

---

## Features

### ✅ Learning Capabilities
- **Teachable Agent**: Uses AutoGen's `TeachableAgent` to learn from conversations
- **Persistent Memory**: Stores learned knowledge in both agent memory and knowledge base
- **Knowledge Base Integration**: Syncs with `app/data/healer_knowledge_base.json`

### ✅ Platform Skills
The agent has access to:
- **Network Diagnostics**: Check platform health, get recent errors, analyze topology
- **Network Healing**: Find known fixes, execute remediations, reset sessions
- **Teaching**: Teach new fixes, list knowledge
- **Code Quality**: Check syntax, format code, lint code, auto-fix issues

### ✅ API Integration
- RESTful API endpoints for chat, teaching, and knowledge management
- Integrated with FastAPI application
- Works with existing `/api/teach` and `/api/report-error` endpoints

---

## Installation

### 1. Install Dependencies

```bash
# Install pyautogen (version 0.2.18 has teachable agent support)
pip install 'pyautogen==0.2.18'

# Or using uv
uv pip install 'pyautogen==0.2.18'
```

**Important**: Version 0.2.18 is required for `TeachableAgent` support. Newer versions (0.10+) have a different API structure.

### 2. Set Up API Keys

```bash
# For OpenAI
export OPENAI_API_KEY="your-openai-api-key"

# For Azure OpenAI (optional)
export AZURE_OPENAI_API_KEY="your-azure-api-key"
export AZURE_OPENAI_ENDPOINT="https://your-endpoint.openai.azure.com/"
export AZURE_OPENAI_API_VERSION="2024-02-15-preview"
```

---

## Usage

### Service API

```python
from app.services.autogen_teachable_agent import get_autogen_teachable_agent_service

# Get agent service
agent_service = get_autogen_teachable_agent_service()

# Chat with the agent
result = agent_service.chat("Check the platform health and diagnose any issues")

# Teach the agent a new fix
result = agent_service.teach(
    error_pattern="Connection timeout",
    fix_description="Increase timeout to 60 seconds",
    category="network_errors",
    severity="medium",
    auto_remediable=True
)

# Get knowledge statistics
stats = agent_service.get_knowledge_stats()
```

### REST API Endpoints

#### 1. Chat with Agent

```bash
POST /api/autogen/chat
Content-Type: application/json

{
  "message": "Check the platform health and diagnose any issues",
  "clear_history": false
}
```

**Response**:
```json
{
  "success": true,
  "message": "Check the platform health...",
  "response": "I'll check the platform health...",
  "timestamp": "2025-01-XX...",
  "conversation_history": 5
}
```

#### 2. Teach Agent

```bash
POST /api/autogen/teach
Content-Type: application/json

{
  "error_pattern": "Connection timeout",
  "fix_description": "Increase timeout to 60 seconds",
  "category": "network_errors",
  "severity": "medium",
  "auto_remediable": true
}
```

**Response**:
```json
{
  "success": true,
  "message": "Learned fix for pattern: Connection timeout",
  "category": "network_errors",
  "total_fixes": 15,
  "timestamp": "2025-01-XX..."
}
```

#### 3. Get Knowledge Statistics

```bash
GET /api/autogen/knowledge
```

**Response**:
```json
{
  "total_categories": 3,
  "total_fixes": 15,
  "category_breakdown": {
    "syntax_errors": 3,
    "code_quality": 2,
    "network_errors": 10
  },
  "severity_breakdown": {
    "critical": 2,
    "high": 3,
    "medium": 8,
    "low": 2
  },
  "auto_remediable_count": 5,
  "agent_memory_entries": 12
}
```

#### 4. Reset Agent Memory

```bash
POST /api/autogen/reset
Content-Type: application/json

{
  "keep_knowledge_base": true
}
```

---

## Integration with AI Healer

The teachable agent is fully integrated with the AI healer:

1. **Shared Knowledge Base**: Both use `app/data/healer_knowledge_base.json`
2. **Code Quality Tools**: Agent can use AI healer's code quality methods
3. **Error Reporting**: Errors reported via `/api/report-error` can trigger agent learning
4. **Teaching**: Agent can teach new fixes that the AI healer will use

### Example: Auto-Learning from Errors

```python
# When an error is reported
POST /api/report-error
{
  "error": "SyntaxError: unexpected indent",
  "category": "syntax_error"
}

# The AI healer diagnoses it
# If no fix found, the teachable agent can learn from it
# Future similar errors will be automatically fixed
```

---

## Platform Skills Available

The agent has access to these platform skills:

### Diagnostics
- `check_platform_health()` - Check overall platform health
- `get_recent_errors()` - Get recent errors from logs
- `analyze_network_topology()` - Analyze network topology

### Healing
- `find_known_fix()` - Search knowledge base for fixes
- `execute_remediation()` - Execute self-healing actions
- `reset_http_session()` - Reset HTTP sessions
- `clear_cache()` - Clear application caches
- `reconnect_api()` - Force API reconnection

### Teaching
- `teach_fix()` - Teach a new error fix
- `list_knowledge()` - List all learned knowledge

### Code Quality
- `check_syntax()` - Check Python files for syntax errors
- `format_code()` - Format code with Black
- `lint_code()` - Lint code with Flake8
- `run_code_quality_checks()` - Run all quality checks
- `auto_fix_code_issues()` - Auto-fix code issues

---

## Example Use Cases

### 1. Diagnose and Fix Code Issues

```python
agent_service = get_autogen_teachable_agent_service()

# Ask agent to check code quality
result = agent_service.chat(
    "Check the syntax of app/main.py and fix any errors"
)

# Agent will:
# 1. Run syntax check
# 2. Format code if needed
# 3. Report any issues
# 4. Learn from the experience
```

### 2. Learn from New Errors

```python
# When a new error occurs
agent_service.teach(
    error_pattern="ImportError: cannot import name",
    fix_description="Check import paths and ensure modules are in PYTHONPATH",
    category="import_errors",
    severity="high",
    auto_remediable=False
)

# Future similar errors will be automatically diagnosed
```

### 3. Network Diagnostics

```python
# Ask agent to diagnose network issues
result = agent_service.chat(
    "Check the platform health and diagnose any network connectivity issues"
)

# Agent will:
# 1. Check platform health
# 2. Get recent errors
# 3. Analyze topology
# 4. Suggest fixes
```

---

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=your-api-key

# Optional (for Azure OpenAI)
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Optional (model selection)
AUTOGEN_MODEL=gpt-4  # or gpt-3.5-turbo, etc.
```

### Service Configuration

```python
# Custom configuration
agent_service = AutoGenTeachableAgentService(
    model="gpt-4",
    api_key="your-key",
    work_dir="/custom/work/dir"
)
```

---

## Knowledge Base Structure

The agent stores learned knowledge in `app/data/healer_knowledge_base.json`:

```json
{
  "fixes": {
    "category_name": [
      {
        "pattern": "Error pattern to match",
        "fix": "How to fix this error",
        "severity": "medium",
        "auto_remediable": false,
        "learned_at": "2025-01-XX...",
        "learned_by": "autogen_teachable_agent"
      }
    ]
  },
  "metadata": {
    "version": "1.0",
    "last_updated": "2025-01-XX...",
    "commands": {...}
  }
}
```

---

## Memory Management

### Agent Memory

The teachable agent maintains its own memory database in `work_dir/autogen/memory/`. This is separate from the knowledge base and stores conversation context.

### Reset Options

```python
# Reset agent memory but keep knowledge base
agent_service.reset_memory(keep_knowledge_base=True)

# Reset everything (including knowledge base)
agent_service.reset_memory(keep_knowledge_base=False)
```

---

## Troubleshooting

### Agent Not Available

**Error**: `AutoGen teachable agent not available`

**Solution**:
```bash
pip install 'pyautogen==0.2.18'
```

### API Key Not Found

**Error**: `No OpenAI API key found`

**Solution**:
```bash
export OPENAI_API_KEY="your-api-key"
```

### TeachableAgent Not Available

**Warning**: `TeachableAgent not available in this pyautogen version`

**Solution**: Ensure you're using `pyautogen==0.2.18`. Newer versions don't have `TeachableAgent`.

### Skills Not Registered

**Warning**: `Could not register platform skills`

**Solution**: Check that `extras/autogen_skills.py` is accessible and skills are properly defined.

---

## Best Practices

1. **Start with Diagnostics**: Use the agent to diagnose issues before teaching fixes
2. **Learn from Real Errors**: Teach fixes based on actual errors encountered
3. **Use Categories**: Organize fixes by category (syntax_errors, network_errors, etc.)
4. **Set Severity**: Mark critical issues appropriately
5. **Auto-Remediation**: Mark fixes as `auto_remediable` only if they're safe to auto-apply
6. **Regular Review**: Periodically review learned knowledge for accuracy

---

## Integration with Existing Systems

### AI Healer Integration

- ✅ Shared knowledge base
- ✅ Code quality tools available to agent
- ✅ Error reporting triggers agent learning

### AutoGen Skills Integration

- ✅ Network diagnostics available
- ✅ Network healing available
- ✅ Teaching capabilities available

### API Integration

- ✅ `/api/teach` endpoint works with agent
- ✅ `/api/report-error` can trigger agent learning
- ✅ New `/api/autogen/*` endpoints for agent interaction

---

## Next Steps

1. **Set up API keys** for OpenAI or Azure OpenAI
2. **Install pyautogen**: `pip install 'pyautogen==0.2.18'`
3. **Test the agent**: Use `/api/autogen/chat` endpoint
4. **Teach fixes**: Start teaching the agent common error patterns
5. **Monitor learning**: Check `/api/autogen/knowledge` for stats

---

## Files Created

- `app/services/autogen_teachable_agent.py` - Main service
- `docs/AUTOGEN_TEACHABLE_AGENT.md` - This documentation

## Files Modified

- `app/main.py` - Added API endpoints for agent interaction

---

**Status**: ✅ **Ready to Use**

The teachable agent is fully integrated and ready to learn from your interactions!
