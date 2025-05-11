#!/bin/bash

# Bash script to start the FastAPI application

# Navigate to the project directory
cd "$(dirname "$0")"

# Check if the virtual environment exists, if not, create it
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Create the logs directory if it doesn't exist
if [ ! -d "logs" ]; then
    mkdir -p logs
fi

# Install required Python packages
pip install -r requirements.txt

# Start the Uvicorn server and redirect logs to a file
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload > logs/output.log 2>&1 &

# Display the logs in real-time
tail -f logs/output.log