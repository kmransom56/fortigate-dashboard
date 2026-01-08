# PowerInfer & TurboSparse Integration

## Overview

PowerInfer and TurboSparse support is now a standard component of the reusable framework, providing **2-5× faster inference** on consumer hardware with no API keys required.

## Quick Start

### Basic Usage

```python
from reusable.simple_ai import get_ai_assistant

# PowerInfer is automatically detected and used if available
assistant = get_ai_assistant(app_name="my_app")

# All AI features automatically use PowerInfer (2-5× faster!)
result = assistant.audit("code.py", "security")
result = assistant.repair("bug_description", "file.py")
result = assistant.optimize("slow_function", "file.py")
```

### Direct PowerInfer Access

```python
from reusable.powerinfer import (
    is_powerinfer_available,
    get_powerinfer_client,
    list_turbosparse_models,
    get_powerinfer_info
)

# Check if PowerInfer is available
if is_powerinfer_available():
    # Get PowerInfer client
    client = get_powerinfer_client()
    
    if client:
        # Use directly
        response = client.chat("Hello, how are you?")
        print(response)

# List available TurboSparse models
models = list_turbosparse_models()
print(f"Available models: {models}")

# Get detailed information
info = get_powerinfer_info()
print(f"PowerInfer available: {info['powerinfer_available']}")
print(f"Models: {info['turbosparse_models']}")
```

## Features

### ✅ Automatic Detection

PowerInfer is automatically detected and prioritized:

1. **PowerInfer** (fastest, 2-5× speedup) - First priority
2. **Ollama** (local, no API keys) - Second priority
3. Cloud APIs (OpenAI, Anthropic, etc.) - Fallback

### ✅ Multiple Access Methods

- **Via AI Assistant** - Automatic, transparent
- **Direct Client** - Full control
- **Via Ollama** - If TurboSparse models loaded in Ollama

### ✅ No Configuration Required

Works out of the box with auto-detection:

```python
# Just use it - no configuration needed!
assistant = get_ai_assistant("my_app")
```

## Installation

### PowerInfer Engine

PowerInfer must be installed separately:

```bash
git clone https://github.com/SJTU-IPADS/PowerInfer.git
cd PowerInfer
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
```

### TurboSparse Models

Download TurboSparse models from Hugging Face or use via Ollama.

## Configuration

### Environment Variables (Optional)

```bash
# PowerInfer executable path
export POWERINFER_PATH="/path/to/powerinfer"

# TurboSparse model path
export POWERINFER_MODEL_PATH="/path/to/TurboSparse-Mistral-7B"

# PowerInfer API URL (if running as service)
export POWERINFER_BASE_URL="http://localhost:8080"
```

### Programmatic Configuration

```python
from reusable.powerinfer import get_powerinfer_client

# Configure paths
client = get_powerinfer_client(
    powerinfer_path="/path/to/powerinfer",
    model_path="/path/to/model",
    prefer_ollama=True  # Prefer Ollama if available
)
```

## Integration Examples

### Example 1: Simple Integration

```python
from reusable.simple_ai import get_ai_assistant

# PowerInfer automatically used if available
assistant = get_ai_assistant("my_app")

# All commands use PowerInfer (2-5× faster)
result = assistant.audit("app.py", "performance")
```

### Example 2: Direct PowerInfer Usage

```python
from reusable.powerinfer import get_powerinfer_client

client = get_powerinfer_client()
if client:
    response = client.chat(
        "Explain quantum computing",
        system_prompt="You are a helpful teacher."
    )
    print(response)
```

### Example 3: Check Availability

```python
from reusable.powerinfer import is_powerinfer_available, get_powerinfer_info

if is_powerinfer_available():
    info = get_powerinfer_info()
    print(f"PowerInfer: {info['powerinfer_available']}")
    print(f"Models: {info['turbosparse_models']}")
    print(f"Via Ollama: {info['via_ollama']}")
```

### Example 4: Custom Application

```python
from reusable import get_ai_assistant, AgentBackend, AgentFrameworkWrapper

# Force PowerInfer backend
agent = AgentFrameworkWrapper(
    backend=AgentBackend.POWERINFER,
    config={
        "powerinfer_path": "/path/to/powerinfer",
        "powerinfer_model_path": "/path/to/model"
    }
)

if agent.is_available():
    response = agent.chat("Your prompt here")
```

## Performance

### Speedup

- **2-5× faster** than standard models
- **2.83× average speedup**
- Peak speedups of 2-5×

### Efficiency

- **90-97% activation sparsity** (TurboSparse models)
- Minimal GPU memory usage
- Runs on consumer hardware (24GB DRAM for 47B model)

### Mobile Support

- Runs on smartphones
- ~11.68 tokens/sec on OnePlus 12
- Previously difficult for 47B models

## Backend Priority

The framework automatically selects the best available backend:

1. **PowerInfer** (fastest, no API keys)
2. **Ollama** (local, no API keys)
3. **OpenAI** (requires API key)
4. **Anthropic** (requires API key)
5. Others...

## API Reference

### `is_powerinfer_available()`

Check if PowerInfer is available.

**Returns:** `bool` - True if PowerInfer is available

### `get_powerinfer_client()`

Get a PowerInfer client instance.

**Returns:** `PowerInferClient` or `None`

### `list_turbosparse_models()`

List available TurboSparse models.

**Returns:** `list` - List of model paths/names

### `get_powerinfer_info()`

Get detailed PowerInfer status information.

**Returns:** `dict` - Status information

## Troubleshooting

### PowerInfer Not Detected

1. Check executable exists:
   ```python
   from reusable.powerinfer import get_powerinfer_info
   info = get_powerinfer_info()
   print(info)
   ```

2. Set environment variable:
   ```bash
   export POWERINFER_PATH="/path/to/powerinfer"
   ```

### Models Not Found

1. Check model directory:
   ```python
   from reusable.powerinfer import list_turbosparse_models
   models = list_turbosparse_models()
   print(models)
   ```

2. Verify model files exist

### Performance Issues

- Ensure using TurboSparse models (not standard models)
- Check that PowerInfer is actually being used (not falling back)
- Verify model format is PowerInfer GGUF

## Files

- `powerinfer_client.py` - Low-level PowerInfer client
- `powerinfer.py` - High-level convenience functions
- `config.py` - Backend detection and configuration
- `agent_framework_wrapper.py` - Integration with agent framework

## Resources

- **PowerInfer GitHub:** https://github.com/SJTU-IPADS/PowerInfer
- **TurboSparse Paper:** https://arxiv.org/abs/2406.05955
- **Hugging Face:** Search for "TurboSparse" or "PowerInfer"

## Summary

PowerInfer and TurboSparse are now standard components of the reusable framework:

- ✅ Automatic detection and prioritization
- ✅ Easy integration (just use `get_ai_assistant()`)
- ✅ 2-5× faster inference
- ✅ No API keys required
- ✅ Works with TurboSparse models (90-97% sparsity)
- ✅ Mobile support

Just import and use - it works automatically! 🚀
