#!/bin/bash

# Network Device MCP Server - Docker Startup Script
echo "🐳 Starting Network Device MCP Server with Docker..."
echo "================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.docker .env
    echo "✅ Created .env file from template."
    echo "📝 Please edit .env file with your FortiManager credentials before running again."
    echo ""
    echo "Required settings in .env:"
    echo "  FMG_IP=your-fortimanager-ip"
    echo "  FMG_USERNAME=your-username"
    echo "  FMG_PASSWORD=your-password"
    exit 1
fi

# Build and start the container
echo "🔨 Building Docker image..."
docker-compose build

echo "🚀 Starting Network Device MCP Server..."
docker-compose up -d

# Wait for service to be ready
echo "⏳ Waiting for service to start..."
sleep 10

# Check if service is healthy
if curl -f http://localhost:12000/health > /dev/null 2>&1; then
    echo ""
    echo "🎉 SUCCESS! Network Device MCP Server is running!"
    echo "================================================="
    echo "🌐 Web Interface: http://localhost:12000"
    echo "📊 API Documentation: http://localhost:12000/api"
    echo "🏥 Health Check: http://localhost:12000/health"
    echo ""
    echo "🔍 Test ADOM Discovery:"
    echo "   curl http://localhost:12000/api/fortimanager/bww/adoms"
    echo "   curl http://localhost:12000/api/fortimanager/arbys/adoms"
    echo "   curl http://localhost:12000/api/fortimanager/sonic/adoms"
    echo ""
    echo "📝 Your team can now access the application at:"
    echo "   http://localhost:12000"
    echo ""
echo "🛑 To stop the server:"
echo "   docker-compose down"
echo ""
echo "💡 Windows PowerShell Note:"
echo "   If using PowerShell, use: .\\start-docker.bat"
echo "   Instead of: start-docker.bat"
else
    echo "❌ Service health check failed."
    echo "📊 Check logs with: docker-compose logs"
    echo "🔍 Check status with: docker-compose ps"
fi
