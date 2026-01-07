#!/bin/bash

echo "========================================================="
echo " Voice-Enabled Network Management Platform - NOC Style"
echo "========================================================="
echo

echo "Installing Node.js dependencies..."
npm install
echo

echo "Starting NOC-Style Platform..."
echo
echo "Python Backend: http://localhost:5000 (Flask)"
echo "Node.js Frontend: http://localhost:5001 (NOC Interface)"
echo

echo "Press Ctrl+C to stop both servers"
echo

# Function to cleanup background processes
cleanup() {
    echo
    echo "Stopping servers..."
    kill $PYTHON_PID 2>/dev/null
    kill $NODE_PID 2>/dev/null
    echo "Servers stopped."
    exit 0
}

# Set trap to cleanup on interrupt
trap cleanup INT

# Start Python Flask server in background
python3 rest_api_server.py &
PYTHON_PID=$!

# Wait for Python server to start
sleep 3

# Start Node.js server in background  
node server_noc_style.js &
NODE_PID=$!

echo "========================================================="
echo " Platform Started Successfully!"
echo
echo " 🌐 NOC Dashboard: http://localhost:5001"
echo " 📊 Original Dashboard: http://localhost:5000"
echo " 🔧 Health Check: http://localhost:5001/health"
echo "========================================================="
echo

# Wait for background processes
wait