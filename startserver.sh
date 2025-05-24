#!/bin/bash

# Bash script to start the FortiGate Dashboard applications
# This script can start either the FastAPI dashboard, the Flask troubleshooter, or both

# Default settings
DASHBOARD_PORT=8001
TROUBLESHOOTER_PORT=5002
START_DASHBOARD=true
START_TROUBLESHOOTER=false
KILL_EXISTING=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dashboard)
            START_DASHBOARD=true
            shift
            ;;
        --troubleshooter)
            START_TROUBLESHOOTER=true
            shift
            ;;
        --all)
            START_DASHBOARD=true
            START_TROUBLESHOOTER=true
            shift
            ;;
        --dashboard-port)
            DASHBOARD_PORT=$2
            shift 2
            ;;
        --troubleshooter-port)
            TROUBLESHOOTER_PORT=$2
            shift 2
            ;;
        --no-kill)
            KILL_EXISTING=false
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --dashboard         Start the FastAPI dashboard application (default)"
            echo "  --troubleshooter    Start the Flask troubleshooter application"
            echo "  --all               Start both applications"
            echo "  --dashboard-port N  Set dashboard port (default: 8001)"
            echo "  --troubleshooter-port N  Set troubleshooter port (default: 5002)"
            echo "  --no-kill           Don't kill existing processes on the ports"
            echo "  --help              Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Navigate to the project directory
cd "$(dirname "$0")"

# Kill existing processes if requested
if [ "$KILL_EXISTING" = true ]; then
    if [ "$START_DASHBOARD" = true ]; then
        echo "Checking for processes on port $DASHBOARD_PORT..."
        lsof -i TCP:$DASHBOARD_PORT || echo "No processes found on port $DASHBOARD_PORT"
        sudo fuser -k $DASHBOARD_PORT/tcp 2>/dev/null || echo "No processes to kill on port $DASHBOARD_PORT"
    fi
    
    if [ "$START_TROUBLESHOOTER" = true ]; then
        echo "Checking for processes on port $TROUBLESHOOTER_PORT..."
        lsof -i TCP:$TROUBLESHOOTER_PORT || echo "No processes found on port $TROUBLESHOOTER_PORT"
        sudo fuser -k $TROUBLESHOOTER_PORT/tcp 2>/dev/null || echo "No processes to kill on port $TROUBLESHOOTER_PORT"
    fi
fi

# Check if uv is installed, if not, install it
if ! command -v uv &> /dev/null; then
    echo "Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Add uv to PATH for this session
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Check if the virtual environment exists, if not, create it
if [ ! -d "venv" ]; then
    echo "Creating virtual environment with uv..."
    uv venv venv
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install required packages if needed
if [ ! -f "venv/.packages-installed" ]; then
    echo "Installing required packages with uv..."
    if [ -f "requirements.txt" ]; then
        uv pip install -r requirements.txt
    else
        echo "No requirements.txt found, installing basic packages"
        uv pip install fastapi uvicorn jinja2 python-dotenv requests flask paramiko pyopenssl redis
    fi
    touch venv/.packages-installed
fi

# Create the logs directory if it doesn't exist
mkdir -p logs

# Function to start applications in background
start_app() {
    if [ "$1" = "dashboard" ]; then
        echo "Starting the FastAPI dashboard application on port $DASHBOARD_PORT..."
        uvicorn app.main:app --host 0.0.0.0 --port $DASHBOARD_PORT --reload &
        echo "Dashboard started! Access at http://localhost:$DASHBOARD_PORT"
    elif [ "$1" = "troubleshooter" ]; then
        echo "Starting the Flask troubleshooter application on port $TROUBLESHOOTER_PORT..."
        # Update the port in the fortigateconnectivity.py file
        sed -i "s/port=[0-9]\+/port=$TROUBLESHOOTER_PORT/" src/fortigateconnectivity.py
        python src/fortigateconnectivity.py &
        echo "Troubleshooter started! Access at https://localhost:$TROUBLESHOOTER_PORT"
    fi
}

# Start the requested applications
if [ "$START_DASHBOARD" = true ]; then
    start_app dashboard
fi

if [ "$START_TROUBLESHOOTER" = true ]; then
    start_app troubleshooter
fi

# If both applications are started, wait for both to finish
if [ "$START_DASHBOARD" = true ] && [ "$START_TROUBLESHOOTER" = true ]; then
    echo "Both applications are running. Press Ctrl+C to stop them."
    wait
elif [ "$START_DASHBOARD" = true ]; then
    echo "Dashboard is running. Press Ctrl+C to stop it."
    wait
elif [ "$START_TROUBLESHOOTER" = true ]; then
    echo "Troubleshooter is running. Press Ctrl+C to stop it."
    wait
fi

# Display a message with the URL
echo "Server started! Access the dashboard at http://localhost:8001"
echo "Press Ctrl+C to stop the server"
