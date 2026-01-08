# Ollama Integration - Local LLM Support

## Status: ✅ **Ollama Support Added**

The reusable framework now supports local Ollama with LLM and CodeLLaMA models - **no API keys needed!**

## What Was Added

### 1. Ollama Backend Support

- ✅ Added `AgentBackend.OLLAMA` to the backend enum
- ✅ Created `OllamaClient` class for local Ollama API communication
- ✅ Auto-detection of Ollama port (11435, then 11434)
- ✅ Auto-detection of available models (prefers CodeLLaMA for code tasks)

### 2. Configuration Updates

- ✅ Ollama is now **first priority** in backend detection (no API keys needed)
- ✅ Auto-detects Ollama availability
- ✅ Falls back to other backends if Ollama unavailable

### 3. Model Detection

The system automatically detects and uses:
- **CodeLLaMA** (preferred for code tasks)
- **DeepSeek-Coder** (alternative code model)
- **Qwen2.5-Coder** (alternative code model)
- **LLM/Llama** models (general purpose)
- First available model (fallback)

## Your Ollama Setup

**Port:** 11435 (configured in systemd override)  
**Available Models:**
- `fortinet-meraki:v4`
- `fortinet-meraki:q4`
- `fortinet-meraki:7b`
- `qwen2.5-coder:7b-instruct-q4_K_M`
- `mistral:7b-instruct-v0.2-q4_K_M`
- `llama3.2:3b`
- `deepseek-coder:6.7b`
- `codellama:7b`
- And more...

## Usage

### Automatic Detection

The TUI and AI assistant will automatically use Ollama if available:

```python
from reusable.simple_ai import get_ai_assistant

# Auto-detects Ollama (no API keys needed!)
assistant = get_ai_assistant(app_name="meraki_magic_mcp")
```

### Manual Configuration

```python
from reusable.agent_framework_wrapper import AgentFrameworkWrapper, AgentBackend

# Use Ollama explicitly
agent = AgentFrameworkWrapper(
    backend=AgentBackend.OLLAMA,
    config={
        "ollama_base_url": "http://localhost:11435",  # Optional
        "ollama_model": "codellama:7b"  # Optional
    }
)
```

## Testing

### Test Ollama Detection

```bash
python3 -c "from reusable.config import AIConfig, AgentBackend; print('Ollama available:', AIConfig._check_ollama_available()); print('Detected backend:', AIConfig.detect_backend())"
```

### Test Ollama Client

```bash
python3 test_ollama.py
```

### Test in TUI

```bash
# TUI will automatically use Ollama if available
python3 meraki_tui.py
```

## Configuration

### Environment Variables (Optional)

```bash
# Custom Ollama URL (if not on localhost:11435)
export OLLAMA_BASE_URL="http://localhost:11435"

# Preferred model
export OLLAMA_MODEL="codellama:7b"
```

### Config File

Edit `~/.network_observability_ai_config.json`:

```json
{
  "backend": "ollama",
  "backend_config": {
    "ollama_base_url": "http://localhost:11435",
    "ollama_model": "codellama:7b"
  }
}
```

## Benefits

### ✅ No API Keys Required
- Local Ollama runs on your machine
- No external API calls
- No API key management

### ✅ Privacy
- All processing happens locally
- No data sent to external services
- Complete control over models

### ✅ Cost
- Free to use
- No per-request charges
- Use your own hardware

### ✅ Custom Models
- Use specialized models (like `fortinet-meraki`)
- Fine-tuned for your use case
- Full model control

## Troubleshooting

### Ollama Not Detected

1. **Check Ollama is running:**
   ```bash
   systemctl status ollama
   ```

2. **Check port:**
   ```bash
   # Your Ollama is on port 11435
   curl http://localhost:11435/api/tags
   ```

3. **Test detection:**
   ```bash
   python3 -c "from reusable.config import AIConfig; print(AIConfig._check_ollama_available())"
   ```

### Models Not Found

1. **List available models:**
   ```bash
   ollama list
   ```

2. **Pull a model if needed:**
   ```bash
   ollama pull codellama:7b
   ollama pull deepseek-coder:6.7b
   ```

### Slow Responses

- Ollama responses can be slower than cloud APIs
- Consider using smaller/quantized models
- Increase timeout in config if needed

## Files Modified

- `reusable/agent_framework_wrapper.py` - Added Ollama backend support
- `reusable/config.py` - Added Ollama detection and priority
- `reusable/ollama_client.py` - New Ollama client implementation

## Next Steps

1. ✅ Ollama support integrated
2. ✅ Auto-detection working
3. ✅ TUI will use Ollama automatically
4. ⏳ Test AI commands in TUI chat

Try in TUI:
```
audit meraki_tui.py code
repair "function is slow" mcp_client.py
optimize meraki_tui.py performance
```

All will use your local Ollama with CodeLLaMA! 🚀
