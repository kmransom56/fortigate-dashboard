#!/bin/bash
# PowerInfer and TurboSparse Installation Script

set -e

INSTALL_DIR="/media/keith/DATASTORE"
POWERINFER_DIR="${INSTALL_DIR}/PowerInfer"
MODELS_DIR="${INSTALL_DIR}/models"
BUILD_DIR="${POWERINFER_DIR}/build"

echo "=========================================="
echo "PowerInfer & TurboSparse Installation"
echo "=========================================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."
if ! command -v cmake &> /dev/null; then
    echo "❌ cmake not found. Installing..."
    sudo apt-get update && sudo apt-get install -y cmake build-essential
fi

if ! command -v git &> /dev/null; then
    echo "❌ git not found. Installing..."
    sudo apt-get install -y git
fi

echo "✅ Prerequisites OK"
echo ""

# Install Python dependencies
echo "Installing Python dependencies..."
python3 -m pip install --user huggingface_hub --break-system-packages 2>&1 | tail -3
echo ""

# Clone PowerInfer if not exists
if [ ! -d "${POWERINFER_DIR}" ]; then
    echo "Cloning PowerInfer repository..."
    cd "${INSTALL_DIR}"
    git clone https://github.com/SJTU-IPADS/PowerInfer.git
    echo "✅ PowerInfer cloned"
else
    echo "✅ PowerInfer directory exists, updating..."
    cd "${POWERINFER_DIR}"
    git pull
fi
echo ""

# Build PowerInfer
echo "Building PowerInfer..."
cd "${POWERINFER_DIR}"
mkdir -p build
cd build

if [ ! -f "CMakeCache.txt" ]; then
    echo "Running cmake..."
    cmake .. -DCMAKE_BUILD_TYPE=Release
fi

echo "Compiling (this may take a while)..."
make -j$(nproc)

if [ -f "powerinfer" ] || [ -f "powerinfer-server" ]; then
    echo "✅ PowerInfer built successfully"
    ls -lh powerinfer* 2>&1 | head -3
else
    echo "⚠️  PowerInfer executable not found in expected location"
    echo "Checking build directory..."
    find . -name "powerinfer*" -type f -executable 2>/dev/null | head -5
fi
echo ""

# Create models directory
mkdir -p "${MODELS_DIR}"
echo "✅ Models directory: ${MODELS_DIR}"
echo ""

# Download TurboSparse models
echo "=========================================="
echo "TurboSparse Model Download"
echo "=========================================="
echo ""
echo "TurboSparse models are available from:"
echo "  - Hugging Face: https://huggingface.co/SJTU-IPADS/PowerInfer"
echo ""
echo "To download models, you can:"
echo ""
echo "Option 1: Use huggingface-cli (recommended)"
echo "  huggingface-cli download SJTU-IPADS/PowerInfer --local-dir ${MODELS_DIR}/TurboSparse-Mistral-7B"
echo ""
echo "Option 2: Use Python"
echo "  python3 -c \"from huggingface_hub import snapshot_download; snapshot_download('SJTU-IPADS/PowerInfer', local_dir='${MODELS_DIR}/TurboSparse-Mistral-7B')\""
echo ""
echo "Option 3: Load via Ollama (easiest)"
echo "  ollama pull turbosparse-mistral-7b"
echo "  ollama pull turbosparse-mixtral-47b"
echo ""

# Check if models exist
if [ -d "${MODELS_DIR}/TurboSparse-Mistral-7B" ] || [ -d "${MODELS_DIR}/TurboSparse-Mixtral-47B" ]; then
    echo "✅ TurboSparse models found:"
    ls -d ${MODELS_DIR}/TurboSparse-* 2>/dev/null | head -5
else
    echo "⚠️  TurboSparse models not found in ${MODELS_DIR}"
    echo "   You can download them manually or use Ollama (see above)"
fi
echo ""

# Test PowerInfer
echo "=========================================="
echo "Testing PowerInfer"
echo "=========================================="
echo ""

POWERINFER_BIN=$(find "${BUILD_DIR}" -name "powerinfer*" -type f -executable 2>/dev/null | head -1)

if [ -n "${POWERINFER_BIN}" ]; then
    echo "✅ PowerInfer executable: ${POWERINFER_BIN}"
    echo "   Testing..."
    "${POWERINFER_BIN}" --help 2>&1 | head -10 || echo "   (Help command may not be available)"
else
    echo "⚠️  PowerInfer executable not found"
    echo "   Build may have created it with a different name"
    echo "   Check: ${BUILD_DIR}"
fi
echo ""

# Update configuration
echo "=========================================="
echo "Configuration"
echo "=========================================="
echo ""

if [ -n "${POWERINFER_BIN}" ]; then
    echo "PowerInfer path: ${POWERINFER_BIN}"
    echo ""
    echo "To use PowerInfer, set environment variables:"
    echo "  export POWERINFER_PATH=\"${POWERINFER_BIN}\""
    if [ -d "${MODELS_DIR}/TurboSparse-Mistral-7B" ]; then
        echo "  export POWERINFER_MODEL_PATH=\"${MODELS_DIR}/TurboSparse-Mistral-7B\""
    fi
    echo ""
    echo "Or update ~/.network_observability_ai_config.json:"
    echo "{"
    echo "  \"backend\": \"powerinfer\","
    echo "  \"backend_config\": {"
    echo "    \"powerinfer_path\": \"${POWERINFER_BIN}\""
    if [ -d "${MODELS_DIR}/TurboSparse-Mistral-7B" ]; then
        echo "    \"powerinfer_model_path\": \"${MODELS_DIR}/TurboSparse-Mistral-7B\""
    fi
    echo "  }"
    echo "}"
fi
echo ""

# Test integration
echo "=========================================="
echo "Testing Integration"
echo "=========================================="
echo ""

cd /media/keith/DATASTORE/meraki-magic-mcp
python3 -c "
from reusable.config import AIConfig, AgentBackend
import os

# Set paths if found
powerinfer_bin = '${POWERINFER_BIN}'
if powerinfer_bin and os.path.exists(powerinfer_bin):
    os.environ['POWERINFER_PATH'] = powerinfer_bin

models_dir = '${MODELS_DIR}'
if os.path.exists(models_dir):
    os.environ['POWERINFER_MODEL_PATH'] = models_dir

print('PowerInfer available:', AIConfig._check_powerinfer_available())
print('Detected backend:', AIConfig.detect_backend().value if AIConfig.detect_backend() else 'None')
print('Available backends:', [b.value for b in AIConfig.list_available_backends()])
" 2>&1

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Download TurboSparse models (see instructions above)"
echo "  2. Test PowerInfer: python3 meraki_tui.py"
echo "  3. AI commands will automatically use PowerInfer when available"
echo ""
