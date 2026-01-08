# Changelog

## Version 1.3.0 - PowerInfer & TurboSparse Integration

### Added
- **PowerInfer & TurboSparse Support** - Fast local inference (2-5× speedup)
  - `reusable/powerinfer.py` - High-level convenience functions
  - `reusable/powerinfer_client.py` - Low-level PowerInfer client
  - Automatic detection and prioritization
  - Support for TurboSparse models via Ollama
  - No API keys required

### New Functions
- `is_powerinfer_available()` - Check if PowerInfer is available
- `get_powerinfer_client()` - Get PowerInfer client instance
- `list_turbosparse_models()` - List available TurboSparse models
- `get_powerinfer_info()` - Get detailed PowerInfer status

### New Classes
- `PowerInferClient` - Direct PowerInfer client
- `PowerInferOllamaWrapper` - TurboSparse models via Ollama

### Backend Priority
PowerInfer is now the **first priority** backend:
1. PowerInfer (fastest, 2-5× speedup, no API keys)
2. Ollama (local, no API keys)
3. OpenAI (requires API key)
4. Anthropic (requires API key)
5. Others...

### Documentation
- `README_POWERINFER.md` - PowerInfer usage guide
- `INTEGRATION_GUIDE.md` - Integration examples

### Changes
- Updated `reusable/__init__.py` to export PowerInfer components
- Updated `reusable/config.py` to detect PowerInfer
- Updated `reusable/agent_framework_wrapper.py` to support PowerInfer backend
- Version bumped to 1.3.0

## Version 1.2.0

### Features
- AI Assistant framework
- Multi-backend support (OpenAI, Anthropic, AutoGen, etc.)
- Secure key management
- Audit, repair, optimize, learn functions

## Version 1.0.0

### Initial Release
- Basic reusable components
- Secure key manager
- Agent framework wrapper
