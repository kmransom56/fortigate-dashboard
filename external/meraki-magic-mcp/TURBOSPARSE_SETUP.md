# TurboSparse Models Setup Guide

## Current Status

### PowerInfer Engine
✅ **INSTALLED** - Ready to use
- Location: `/media/keith/DATASTORE/PowerInfer/build/bin/main`
- Status: Detected and working

### TurboSparse Models
⏳ **NEED TO OBTAIN** - Choose one method below

## Method 1: Ollama (Easiest - Recommended)

If TurboSparse models are available in Ollama format:

```bash
# Try pulling TurboSparse models
ollama pull turbosparse-mistral-7b
ollama pull turbosparse-mixtral-47b
```

**Note:** TurboSparse models may not be in the standard Ollama registry. If the pull fails, try Method 2 or 3.

The system will **automatically detect** TurboSparse models in Ollama via the `PowerInferOllamaWrapper`.

## Method 2: Hugging Face Download

### Step 1: Authenticate (if needed)

```bash
# Install huggingface-cli if not available
python3 -m pip install --user huggingface_hub --break-system-packages

# Login (if models are gated)
huggingface-cli login
```

### Step 2: Download Models

```bash
cd /media/keith/DATASTORE/meraki-magic-mcp
python3 download_turbosparse.py
```

Or manually:

```python
from huggingface_hub import snapshot_download

# Download TurboSparse-Mistral-7B
snapshot_download(
    repo_id="SJTU-IPADS/TurboSparse-Mistral-7B",  # Check actual repo name
    local_dir="/media/keith/DATASTORE/models/TurboSparse-Mistral-7B"
)
```

### Step 3: Convert to PowerInfer Format (if needed)

If models are in Hugging Face format, convert to PowerInfer GGUF:

```bash
cd /media/keith/DATASTORE/PowerInfer
python3 convert-hf-to-powerinfer-gguf.py \
    /path/to/model \
    /path/to/mlp_predictors \
    --outfile /media/keith/DATASTORE/models/TurboSparse-Mistral-7B/model.powerinfer.gguf
```

## Method 3: Use Existing Models

If you have TurboSparse models in another location:

1. Copy to: `/media/keith/DATASTORE/models/TurboSparse-Mistral-7B/`
2. Ensure model file is named: `*.powerinfer.gguf` or `*.gguf`
3. Set environment variable:
   ```bash
   export POWERINFER_MODEL_PATH="/media/keith/DATASTORE/models/TurboSparse-Mistral-7B"
   ```

## Verification

### Check Model Availability

```bash
cd /media/keith/DATASTORE/meraki-magic-mcp
python3 -c "
import sys
sys.path.insert(0, '.')
from reusable.powerinfer_client import PowerInferClient, PowerInferOllamaWrapper
import os

# Check direct PowerInfer
os.environ['POWERINFER_PATH'] = '/media/keith/DATASTORE/PowerInfer/build/bin/main'
client = PowerInferClient(
    powerinfer_path='/media/keith/DATASTORE/PowerInfer/build/bin/main',
    model_path='/media/keith/DATASTORE/models/TurboSparse-Mistral-7B'
)
print('Direct PowerInfer:', client.is_available())
print('Model path:', client.model_path)

# Check via Ollama
wrapper = PowerInferOllamaWrapper()
print('TurboSparse via Ollama:', wrapper.is_available())
print('Models found:', wrapper.turbosparse_models)
"
```

### Test Backend Detection

```bash
cd /media/keith/DATASTORE/meraki-magic-mcp
python3 -c "
import sys
sys.path.insert(0, '.')
from reusable.config import AIConfig, AgentBackend
import os

os.environ['POWERINFER_PATH'] = '/media/keith/DATASTORE/PowerInfer/build/bin/main'
os.environ['POWERINFER_MODEL_PATH'] = '/media/keith/DATASTORE/models/TurboSparse-Mistral-7B'

backend = AIConfig.detect_backend()
print('Detected backend:', backend.value if backend else 'None')
print('PowerInfer available:', AIConfig._check_powerinfer_available())
"
```

## Testing Speedup

Once models are available, test the speedup:

```bash
cd /media/keith/DATASTORE/meraki-magic-mcp
python3 test_powerinfer_speedup.py
```

This will compare:
- PowerInfer (with TurboSparse) vs Ollama (standard models)
- Expected: 2-5× speedup with PowerInfer

## Using in TUI

Once models are loaded:

```bash
cd /media/keith/DATASTORE/meraki-magic-mcp
python3 meraki_tui.py
```

The TUI will automatically:
1. Detect PowerInfer (if models available)
2. Use PowerInfer for AI commands (2-5× faster)
3. Fall back to Ollama if PowerInfer not available

## Troubleshooting

### Models Not Detected

1. **Check model location:**
   ```bash
   ls -lh /media/keith/DATASTORE/models/
   ```

2. **Verify model format:**
   ```bash
   find /media/keith/DATASTORE/models -name "*.gguf" -o -name "*.powerinfer.gguf"
   ```

3. **Set environment variables:**
   ```bash
   export POWERINFER_PATH="/media/keith/DATASTORE/PowerInfer/build/bin/main"
   export POWERINFER_MODEL_PATH="/media/keith/DATASTORE/models/TurboSparse-Mistral-7B"
   ```

### PowerInfer Not Using Models

1. **Check model path in config:**
   ```python
   from reusable.config import AIConfig
   print(AIConfig._check_powerinfer_available())
   ```

2. **Test direct execution:**
   ```bash
   /media/keith/DATASTORE/PowerInfer/build/bin/main \
     -m /media/keith/DATASTORE/models/TurboSparse-Mistral-7B/model.powerinfer.gguf \
     -p "Hello"
   ```

### Speedup Not Achieved

- Ensure you're using TurboSparse models (not standard models)
- Check that PowerInfer is actually being used (not falling back to Ollama)
- Verify model format is PowerInfer GGUF (not standard GGUF)

## Resources

- **PowerInfer GitHub:** https://github.com/SJTU-IPADS/PowerInfer
- **TurboSparse Paper:** https://arxiv.org/abs/2406.05955
- **Hugging Face:** Search for "TurboSparse" or "PowerInfer"

## Next Steps

1. ✅ PowerInfer installed
2. ⏳ Obtain TurboSparse models (choose method above)
3. ⏳ Test speedup with `test_powerinfer_speedup.py`
4. ⏳ Use in TUI for 2-5× faster AI commands
