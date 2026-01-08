# TurboSparse Models Download Status

## Current Situation

### SJTU-IPADS Models
- **Status:** ⚠️ Requires authentication or not publicly available
- **Repository:** `SJTU-IPADS/PowerInfer` and related repos
- **Issue:** 401 Unauthorized error when accessing

### Alternative Models Found
- **Tiiny/TurboSparse-Mistral-Instruct** - Available, downloading
- **Tiiny/TurboSparse-Mixtral** - Available
- **Tiiny/TurboSparse-Mixtral-Instruct** - Available

## Download Options

### Option 1: Use Tiiny Models (Currently Downloading)

```bash
# TurboSparse-Mistral-Instruct (downloading)
cd /media/keith/DATASTORE/meraki-magic-mcp
python3 -c "
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id='Tiiny/TurboSparse-Mistral-Instruct',
    local_dir='/media/keith/DATASTORE/models/TurboSparse-Mistral-Instruct',
    local_dir_use_symlinks=False
)
"
```

### Option 2: Authenticate with Hugging Face (For SJTU-IPADS Models)

If you have access to SJTU-IPADS models:

```bash
# Login to Hugging Face
huggingface-cli login

# Then download
python3 download_turbosparse_hf.py
```

### Option 3: Manual Download

1. Visit: https://huggingface.co/Tiiny/TurboSparse-Mistral-Instruct
2. Download model files manually
3. Place in: `/media/keith/DATASTORE/models/TurboSparse-Mistral-Instruct/`

### Option 4: Check PowerInfer GitHub

The PowerInfer GitHub repository may have direct download links:
- https://github.com/SJTU-IPADS/PowerInfer

## Model Compatibility

**Important:** TurboSparse models need to be in PowerInfer GGUF format (`.powerinfer.gguf`).

If downloaded models are in standard format, convert them:

```bash
cd /media/keith/DATASTORE/PowerInfer
python3 convert-hf-to-powerinfer-gguf.py \
    /media/keith/DATASTORE/models/TurboSparse-Mistral-Instruct \
    /path/to/mlp_predictors \
    --outfile /media/keith/DATASTORE/models/TurboSparse-Mistral-Instruct/model.powerinfer.gguf
```

## Verification

### Check Download Progress

```bash
cd /media/keith/DATASTORE/models
ls -lh TurboSparse-*
du -sh TurboSparse-*
```

### Check Model Format

```bash
cd /media/keith/DATASTORE/models
find . -name "*.gguf" -o -name "*.powerinfer.gguf" | head -10
```

### Test PowerInfer Detection

```bash
cd /media/keith/DATASTORE/meraki-magic-mcp
python3 -c "
import sys
sys.path.insert(0, '.')
from reusable.powerinfer_client import PowerInferClient
import os

os.environ['POWERINFER_PATH'] = '/media/keith/DATASTORE/PowerInfer/build/bin/main'
client = PowerInferClient(
    powerinfer_path='/media/keith/DATASTORE/PowerInfer/build/bin/main',
    model_path='/media/keith/DATASTORE/models/TurboSparse-Mistral-Instruct'
)
print('PowerInfer available:', client.is_available())
print('Model path:', client.model_path)
"
```

## Current Download Status

- **Tiiny/TurboSparse-Mistral-Instruct:** ⏳ Downloading in background
- **SJTU-IPADS models:** ⚠️ Requires authentication

## Next Steps

1. **Wait for download to complete** (check with `ls -lh /media/keith/DATASTORE/models/`)
2. **Verify model format** (should be `.gguf` or `.powerinfer.gguf`)
3. **Convert if needed** (use PowerInfer conversion tools)
4. **Test PowerInfer** with downloaded models
5. **Verify speedup** with `test_powerinfer_speedup.py`

## Troubleshooting

### Download Fails

- Check internet connection
- Verify Hugging Face access
- Try manual download from web interface

### Model Format Issues

- Ensure models are in GGUF format
- May need conversion to PowerInfer GGUF format
- Check PowerInfer documentation for format requirements

### PowerInfer Not Detecting Models

- Verify model path is correct
- Check file permissions
- Ensure model files are complete (not partial download)

## Resources

- **Tiiny Models:** https://huggingface.co/Tiiny
- **PowerInfer GitHub:** https://github.com/SJTU-IPADS/PowerInfer
- **Hugging Face Auth:** https://huggingface.co/docs/hub/security-tokens
