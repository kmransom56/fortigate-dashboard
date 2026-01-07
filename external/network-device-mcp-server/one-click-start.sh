#!/bin/bash

echo ""
echo "========================================================================"
echo "  🚀 Network Device Management - One-Click Docker Setup"
echo "========================================================================"
echo ""
echo "This will start your complete network device management system:"
echo "  - FastAPI Backend Server    (http://localhost:8000)"
echo "  - Web Dashboard            (http://localhost:12000)"
echo "  - Health monitoring and logging"
echo ""
echo "Requirements: Docker Desktop must be installed and running"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

echo ""
echo "📋 Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    echo ""
    echo "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
    echo "Then restart this script."
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available"
    echo "Please update Docker Desktop to the latest version"
    exit 1
fi

echo "✅ Docker is ready!"
echo ""

echo "🏗️  Building and starting containers..."
echo "This may take a few minutes on first run..."
echo ""

if ! docker compose -f docker-compose.production.yml up --build -d; then
    echo ""
    echo "❌ Failed to start containers"
    echo "Check the error messages above and try again"
    exit 1
fi

echo ""
echo "========================================================================"
echo "  ✅ SUCCESS! Your Network Device Management System is running"
echo "========================================================================"
echo ""
echo "🌐 Web Dashboard:      http://localhost:12000"
echo "🔧 FastAPI Backend:    http://localhost:8000"
echo "📖 API Documentation:  http://localhost:8000/docs"
echo ""
echo "🔍 To view logs:       docker compose -f docker-compose.production.yml logs -f"
echo "🛑 To stop:           docker compose -f docker-compose.production.yml down"
echo "📊 To view status:     docker compose -f docker-compose.production.yml ps"
echo ""

# Try to open browser
if command -v open &> /dev/null; then
    echo "Opening dashboard in your default browser..."
    sleep 3
    open http://localhost:12000
elif command -v xdg-open &> /dev/null; then
    echo "Opening dashboard in your default browser..."
    sleep 3
    xdg-open http://localhost:12000
else
    echo "Please open http://localhost:12000 in your browser"
fi

echo ""
echo "Press Enter to view logs, or Ctrl+C to exit..."
read
docker compose -f docker-compose.production.yml logs -f