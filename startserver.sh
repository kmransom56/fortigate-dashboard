#!/bin/bash

# Bash script to start the FastAPI application

# Kill any existing processes on port 8001
echo "Checking for processes on port 8001..."
lsof -i TCP:8001 || echo "No processes found on port 8001"
sudo fuser -k 8001/tcp 2>/dev/null || echo "No processes to kill on port 8001"

# Navigate to the project directory
cd "$(dirname "$0")"

# Check if the virtual environment exists, if not, create it
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install required packages if needed
if [ ! -f "venv/.packages-installed" ]; then
    echo "Installing required packages..."
    pip install -r requirements.txt || echo "No requirements.txt found, installing basic packages"
    pip install fastapi uvicorn jinja2 python-dotenv requests
    touch venv/.packages-installed
fi

# Create the logs directory if it doesn't exist
mkdir -p logs

# Start the FastAPI application on port 8001
echo "Starting the FastAPI application on port 8001..."
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# Display a message with the URL
echo "Server started! Access the dashboard at http://localhost:8001"
echo "Press Ctrl+C to stop the server"
