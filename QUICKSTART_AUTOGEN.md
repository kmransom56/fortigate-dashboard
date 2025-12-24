# Quick Start: AutoGen Teachable Agent

## Installation

```bash
# Install dependencies
# Note: Use version 0.2.18 which has teachable agent support
pip install 'pyautogen==0.2.18'

# Or with uv
uv pip install 'pyautogen==0.2.18'
```

**Important**: 
- In zsh, always quote package names to prevent glob expansion
- Use version 0.2.18 (newer versions have different API)
- The agent uses `AssistantAgent` with function calling (works great even without TeachableAgent)

## Setup API Key

```bash
# For OpenAI
export OPENAI_API_KEY="your-api-key-here"

# Or for Azure OpenAI
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_OPENAI_ENDPOINT="https://your-endpoint.openai.azure.com/"
export AZURE_OPENAI_API_VERSION="2024-02-15-preview"
```

## Quick Examples

### 1. Generate API Documentation

```bash
python autogen_agent.py --task "Generate API documentation from device inventory"
```

### 2. Analyze Code

```bash
python autogen_agent.py --task "Analyze fortigate_self_api_doc.py for errors"
```

### 3. Interactive Mode

```bash
python autogen_agent.py --interactive
```

Then type tasks like:
- "Generate API documentation"
- "Analyze all Python files in app/services"
- "Fix code quality issues in fortigate_self_api_doc.py"

## What the Agent Can Do

✅ Generate API documentation from device inventory  
✅ Analyze Python code for errors and issues  
✅ Automatically fix common code problems  
✅ Use function calling to execute tools and complete tasks  
✅ Maintain documentation automatically  

## Files Created

- `autogen_agent.py` - Main agent script
- `agent_tools.py` - Tools the agent can use
- `example_agent_usage.py` - Example usage patterns
- `README_AUTOGEN_AGENT.md` - Full documentation

## Troubleshooting

**No API key error?**
```bash
export OPENAI_API_KEY="your-key"
```

**Import error?**
```bash
pip install 'pyautogen==0.2.18'
```

**Agent not responding?**
- Check API key is set correctly
- Verify network connectivity
- Check FortiGate API is accessible (for documentation tasks)
