FROM python:3.10-slim

LABEL maintainer="Fortinet MCP Server Contributors"
LABEL description="A comprehensive MCP server for Fortinet FortiGate and FortiSwitch management with 246 auto-discovered API endpoints"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user
RUN groupadd -r fortinet && useradd -r -g fortinet fortinet

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY fortinet_server_enhanced.py .
COPY mcp_rest_bridge.py .
COPY test_server.py .
COPY install_mcp.sh .
COPY *.md .
COPY examples/ ./examples/
COPY browser_extension/ ./browser_extension/

# Create directories for logs and data
RUN mkdir -p /app/logs /app/data && \
    chown -R fortinet:fortinet /app

# Create startup script
RUN cat > /app/start.sh << 'EOF'
#!/bin/bash
set -e

echo "🔥 Starting Fortinet MCP Server"
echo "📊 Environment: ${ENVIRONMENT:-production}"
echo "🌐 API Endpoints: 246"

# Health check
echo "🔍 Testing FortiGate connection..."
python3 -c "
try:
    from fortinet_server_enhanced import fg_api
    result = fg_api.test_connection()
    if result.get('status') == 'success':
        print('✅ FortiGate connection successful')
    else:
        print('⚠️  FortiGate connection warning:', result.get('message', 'Unknown'))
except Exception as e:
    print('❌ FortiGate connection failed:', str(e))
"

# Start the appropriate service
case "${SERVICE_MODE:-mcp}" in
    "mcp")
        echo "🚀 Starting MCP Server..."
        exec python3 fortinet_server_enhanced.py
        ;;
    "rest")
        echo "🌐 Starting REST API Bridge..."
        exec python3 mcp_rest_bridge.py
        ;;
    "test")
        echo "🧪 Running tests..."
        exec python3 test_server.py
        ;;
    *)
        echo "❌ Unknown service mode: ${SERVICE_MODE}"
        exit 1
        ;;
esac
EOF

RUN chmod +x /app/start.sh

# Switch to non-root user
USER fortinet

# Expose ports
EXPOSE 5000 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Default command
CMD ["/app/start.sh"]

# Metadata
LABEL org.opencontainers.image.title="Fortinet MCP Server"
LABEL org.opencontainers.image.description="A comprehensive MCP server for Fortinet network management"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.source="https://github.com/yourusername/fortinet-mcp-server"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.documentation="https://github.com/yourusername/fortinet-mcp-server/blob/main/README.md"