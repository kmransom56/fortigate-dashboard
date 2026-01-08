#!/bin/bash
# Meraki Magic TUI Launcher (Linux)
# Interactive dashboard for Meraki network management

echo "========================================"
echo "  Meraki Magic TUI Dashboard"
echo "  Multi-Organization Management"
echo "========================================"
echo

# Ensure user site-packages is in PYTHONPATH
export PYTHONPATH="${HOME}/.local/lib/python3.12/site-packages:${PYTHONPATH}"

# Check if textual is installed
if ! python3 -c "import textual" 2>/dev/null; then
    echo "Installing required dependencies..."
    python3 -m pip install --user textual python-dotenv meraki --break-system-packages
    # Refresh PYTHONPATH after installation
    export PYTHONPATH="${HOME}/.local/lib/python3.12/site-packages:${PYTHONPATH}"
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "WARNING: .env file not found!"
    echo "Please create .env with MERAKI_API_KEY and MERAKI_ORG_ID"
    exit 1
fi

# Launch TUI
echo "Starting dashboard..."
echo
python3 meraki_tui.py
