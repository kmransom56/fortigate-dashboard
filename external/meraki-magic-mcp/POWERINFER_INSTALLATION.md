# PowerInfer & TurboSparse Installation Guide

## Installation Status

### ✅ PowerInfer Engine - INSTALLED

- **Location:** `/media/keith/DATASTORE/PowerInfer`
- **Build Directory:** `/media/keith/DATASTORE/PowerInfer/build`
- **Executables:**
  - `bin/main` - Main PowerInfer inference executable
  - `bin/server` - PowerInfer server (HTTP API)

### ⏳ TurboSparse Models - DOWNLOADING

Models are being downloaded to: `/media/keith/DATASTORE/models`

## What Was Installed

### 1. PowerInfer Repository

```bash
cd /media/keith/DATASTORE
git clone https://github.com/SJTU-IPADS/PowerInfer.git
```

### 2. PowerInfer Build

```bash
cd PowerInfer
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
```

**Build completed successfully!**

### 3. Python Dependencies

- ✅ `huggingface_hub` - For downloading models
- ✅ PowerInfer Python requirements installed

## Using PowerInfer

### Option 1: Direct Execution

```bash
cd /media/keith/DATASTORE/PowerInfer/bin
./main -m /path/to/model -p "Your prompt here"
```

### Option 2: Server Mode (HTTP API)

```bash
cd /media/keith/DATASTORE/PowerInfer/bin
./server --host 0.0.0.0 --port 8080 -m /path/to/model
```

### Option 3: Via Our Integration (Automatic)

The application will automatically detect and use PowerInfer when:
1. PowerInfer executable is found
2. TurboSparse models are available

## Downloading TurboSparse Models

### Method 1: Using Download Script (Recommended)

```bash
cd /media/keith/DATASTORE/meraki-magic-mcp
python3 download_turbosparse.py
```

Select:
- `1` for TurboSparse-Mistral-7B (~14GB)
- `2` for TurboSparse-Mixtral-47B (~28GB)
- `3` for both

### Method 2: Using Ollama (Easier, if available)

```bash
# If TurboSparse models are available in Ollama format
ollama pull turbosparse-mistral-7b
ollama pull turbosparse-mixtral-47b
```

The system will automatically detect and use them via the Ollama wrapper!

### Method 3: Manual Download

```bash
cd /media/keith/DATASTORE/models
python3 -c "
from huggingface_hub import snapshot_download
snapshot_download('SJTU-IPADS/PowerInfer', local_dir='TurboSparse-Mistral-7B', repo_type='model')
"
```

## Configuration

### Environment Variables

```bash
export POWERINFER_PATH="/media/keith/DATASTORE/PowerInfer/bin/main"
export POWERINFER_MODEL_PATH="/media/keith/DATASTORE/models/TurboSparse-Mistral-7B"
```

### Config File

Edit `~/.network_observability_ai_config.json`:

```json
{
  "backend": "powerinfer",
  "backend_config": {
    "powerinfer_path": "/media/keith/DATASTORE/PowerInfer/bin/main",
    "powerinfer_model_path": "/media/keith/DATASTORE/models/TurboSparse-Mistral-7B"
  }
}
```

## Testing

### Test PowerInfer Detection

```bash
cd /media/keith/DATASTORE/meraki-magic-mcp
python3 -c "
from reusable.config import AIConfig, AgentBackend
import os

# Set paths
os.environ['POWERINFER_PATH'] = '/media/keith/DATASTORE/PowerInfer/bin/main'
os.environ['POWERINFER_MODEL_PATH'] = '/media/keith/DATASTORE/models/TurboSparse-Mistral-7B'

print('PowerInfer available:', AIConfig._check_powerinfer_available())
print('Detected backend:', AIConfig.detect_backend().value if AIConfig.detect_backend() else 'None')
"
```

### Test PowerInfer Client

```bash
python3 -c "
from reusable.powerinfer_client import PowerInferClient
import os

os.environ['POWERINFER_PATH'] = '/media/keith/DATASTORE/PowerInfer/bin/main'
client = PowerInferClient(
    powerinfer_path='/media/keith/DATASTORE/PowerInfer/bin/main',
    model_path='/media/keith/DATASTORE/models/TurboSparse-Mistral-7B'
)
print('Available:', client.is_available())
"
```

## Model Conversion (If Needed)

If you have models in other formats, PowerInfer provides conversion tools:

```bash
cd /media/keith/DATASTORE/PowerInfer
python3 convert-hf-to-powerinfer-gguf.py --help
python3 convert.py --help
```

## Performance

Once models are downloaded and configured:

- **2-5× faster** inference than standard models
- **90-97% activation sparsity**
- **Runs on consumer hardware** (24GB DRAM for 47B model)
- **~11.68 tokens/sec** on smartphones

## Troubleshooting

### PowerInfer Not Detected

1. Check executable exists:
   ```bash
   ls -lh /media/keith/DATASTORE/PowerInfer/bin/main
   ```

2. Check permissions:
   ```bash
   chmod +x /media/keith/DATASTORE/PowerInfer/bin/main
   ```

3. Set environment variable:
   ```bash
   export POWERINFER_PATH="/media/keith/DATASTORE/PowerInfer/bin/main"
   ```

### Models Not Found

1. Check model directory:
   ```bash
   ls -lh /media/keith/DATASTORE/models/
   ```

2. Verify model files:
   ```bash
   find /media/keith/DATASTORE/models -name "*.bin" -o -name "*.gguf" | head -5
   ```

3. Re-download if needed:
   ```bash
   python3 download_turbosparse.py
   ```

### Build Issues

If build failed:

```bash
cd /media/keith/DATASTORE/PowerInfer/build
rm -rf *
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
```

## Next Steps

1. ✅ PowerInfer built and ready
2. ⏳ Download TurboSparse models (in progress)
3. ⏳ Test PowerInfer with models
4. ⏳ Verify 2-5× speedup

## Files Created

- `/media/keith/DATASTORE/PowerInfer/` - PowerInfer source and build
- `/media/keith/DATASTORE/models/` - Model storage directory
- `download_turbosparse.py` - Model download script
- `POWERINFER_INSTALLATION.md` - This guide

## Resources

- **PowerInfer GitHub:** https://github.com/SJTU-IPADS/PowerInfer
- **TurboSparse Models:** https://huggingface.co/SJTU-IPADS/PowerInfer
- **Documentation:** See PowerInfer README.md
