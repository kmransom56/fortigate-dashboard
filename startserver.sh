# PowerShell script to start the FastAPI application

# Navigate to the project directory
Set-Location -Path "C:\Users\Keith Ransom\Documents\fortigate-dashboard"

# Check if the virtual environment exists, if not, create it
if (-Not (Test-Path -Path "venv")) {
    python -m venv venv
}

# Activate the virtual environment
& .\venv\Scripts\Activate.ps1

# Create the logs directory if it doesn't exist
if (-Not (Test-Path -Path "logs")) {
    New-Item -ItemType Directory -Path "logs"
}

# Install required Python packages
pip install -r requirements.txt

# Start the Uvicorn server and redirect logs to a file
Start-Process -FilePath "uvicorn" -ArgumentList "app.main:app --host 0.0.0.0 --port 8001 --reload > logs/output.log 2>&1" -NoNewWindow

# Display the logs in real-time
Get-Content -Path "logs/output.log" -Wait