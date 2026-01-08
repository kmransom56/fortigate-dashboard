# Reusable Framework Integration Guide

## Adding PowerInfer & TurboSparse to Your Application

The reusable framework now includes PowerInfer and TurboSparse support as a standard component. Here's how to integrate it into any application.

## Quick Integration

### Step 1: Import the Framework

```python
from reusable.simple_ai import get_ai_assistant
```

That's it! PowerInfer is automatically detected and used if available.

### Step 2: Use AI Features

```python
# Get AI assistant (auto-detects PowerInfer)
assistant = get_ai_assistant(app_name="my_app")

# All features automatically use PowerInfer (2-5× faster!)
result = assistant.audit("code.py", "security")
result = assistant.repair("bug_description", "file.py")
result = assistant.optimize("slow_function", "file.py")
result = assistant.learn("architecture", "docs/")
```

## Advanced Integration

### Custom Backend Selection

```python
from reusable import AgentFrameworkWrapper, AgentBackend

# Force PowerInfer backend
agent = AgentFrameworkWrapper(
    backend=AgentBackend.POWERINFER,
    config={
        "powerinfer_path": "/path/to/powerinfer",
        "powerinfer_model_path": "/path/to/model"
    }
)

if agent.is_available():
    response = agent.chat("Your prompt")
```

### Direct PowerInfer Access

```python
from reusable.powerinfer import (
    is_powerinfer_available,
    get_powerinfer_client
)

if is_powerinfer_available():
    client = get_powerinfer_client()
    if client:
        response = client.chat("Hello!")
```

## Integration Patterns

### Pattern 1: Automatic (Recommended)

```python
from reusable.simple_ai import get_ai_assistant

# PowerInfer automatically used if available
assistant = get_ai_assistant("my_app")

# Use normally - PowerInfer provides 2-5× speedup
result = assistant.audit("file.py", "performance")
```

### Pattern 2: Explicit Check

```python
from reusable.simple_ai import get_ai_assistant
from reusable.powerinfer import is_powerinfer_available

assistant = get_ai_assistant("my_app")

if is_powerinfer_available():
    print("Using PowerInfer (2-5× faster!)")
else:
    print("Using fallback backend")

result = assistant.audit("file.py", "security")
```

### Pattern 3: Custom Configuration

```python
from reusable import AgentFrameworkWrapper, AgentBackend
import os

# Set paths
os.environ['POWERINFER_PATH'] = '/path/to/powerinfer'
os.environ['POWERINFER_MODEL_PATH'] = '/path/to/model'

# Create agent
agent = AgentFrameworkWrapper(
    backend=AgentBackend.POWERINFER,
    config={
        "powerinfer_path": os.environ['POWERINFER_PATH'],
        "powerinfer_model_path": os.environ['POWERINFER_MODEL_PATH']
    }
)

if agent.is_available():
    response = agent.chat("Your prompt")
```

## Application Examples

### Example 1: CLI Tool

```python
#!/usr/bin/env python3
"""My CLI Tool with PowerInfer Support"""

from reusable.simple_ai import get_ai_assistant

def main():
    assistant = get_ai_assistant("my_cli_tool")
    
    # Audit code
    result = assistant.audit("main.py", "security")
    print(result)
    
    # Repair issues
    result = assistant.repair("Fix memory leak", "memory.py")
    print(result)

if __name__ == "__main__":
    main()
```

### Example 2: Web Application

```python
from flask import Flask, request, jsonify
from reusable.simple_ai import get_ai_assistant

app = Flask(__name__)
assistant = get_ai_assistant("web_app")

@app.route("/audit", methods=["POST"])
def audit_code():
    code = request.json.get("code")
    result = assistant.audit(code, "security")
    return jsonify({"result": result})

@app.route("/repair", methods=["POST"])
def repair_code():
    description = request.json.get("description")
    code = request.json.get("code")
    result = assistant.repair(description, code)
    return jsonify({"result": result})
```

### Example 3: TUI Application

```python
from textual.app import App
from reusable.simple_ai import get_ai_assistant

class MyTUI(App):
    def __init__(self):
        super().__init__()
        self.assistant = get_ai_assistant("my_tui")
    
    def on_mount(self):
        # Display backend info
        backend = self.assistant.agent.get_backend_name()
        self.notify(f"Using: {backend}")
    
    def action_audit(self):
        result = self.assistant.audit("app.py", "performance")
        self.notify(result)
```

## Configuration

### Environment Variables

```bash
# PowerInfer paths
export POWERINFER_PATH="/path/to/powerinfer"
export POWERINFER_MODEL_PATH="/path/to/model"
export POWERINFER_BASE_URL="http://localhost:8080"  # If using API mode
```

### Config File

```json
{
  "backend": "powerinfer",
  "backend_config": {
    "powerinfer_path": "/path/to/powerinfer",
    "powerinfer_model_path": "/path/to/model",
    "ollama_base_url": "http://localhost:11435"
  }
}
```

## Backend Priority

The framework automatically selects backends in this order:

1. **PowerInfer** (fastest, 2-5× speedup, no API keys)
2. **Ollama** (local, no API keys)
3. **OpenAI** (requires API key)
4. **Anthropic** (requires API key)
5. Others...

## Testing Integration

### Test PowerInfer Availability

```python
from reusable.powerinfer import is_powerinfer_available, get_powerinfer_info

if is_powerinfer_available():
    info = get_powerinfer_info()
    print(f"PowerInfer: Available")
    print(f"Models: {info['turbosparse_models']}")
else:
    print("PowerInfer: Not available (using fallback)")
```

### Test AI Assistant

```python
from reusable.simple_ai import get_ai_assistant

assistant = get_ai_assistant("test_app")
print(f"Backend: {assistant.agent.get_backend_name()}")
print(f"Available: {assistant.agent.is_available()}")

# Test a simple query
result = assistant.agent.chat("Hello!")
print(f"Response: {result[:100]}...")
```

## Benefits

### ✅ Automatic

- No configuration needed
- Auto-detects PowerInfer
- Falls back gracefully

### ✅ Fast

- 2-5× faster inference
- 90-97% activation sparsity
- Minimal resource usage

### ✅ Easy

- One import statement
- Standard interface
- Works everywhere

### ✅ Flexible

- Multiple access methods
- Custom configuration
- Backend selection

## Files Structure

```
reusable/
├── __init__.py              # Main exports
├── simple_ai.py            # High-level AI assistant
├── powerinfer.py           # PowerInfer convenience functions
├── powerinfer_client.py   # PowerInfer client implementation
├── ollama_client.py        # Ollama client
├── agent_framework_wrapper.py  # Multi-backend wrapper
├── config.py               # Configuration and detection
└── README_POWERINFER.md    # PowerInfer documentation
```

## Summary

PowerInfer and TurboSparse are now standard components:

1. **Import:** `from reusable.simple_ai import get_ai_assistant`
2. **Use:** `assistant = get_ai_assistant("my_app")`
3. **Enjoy:** 2-5× faster inference automatically!

No configuration needed - it just works! 🚀
