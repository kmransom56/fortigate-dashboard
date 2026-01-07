# Dockerfile for LTM Network Intelligence Platform
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    wget \
    git \
    build-essential \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Copy requirements first for better caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/config /app/security /app/backups

# Set proper permissions
RUN chown -R appuser:appgroup /app
RUN chmod +x /app/unified_network_intelligence.py
RUN chmod +x /app/scripts/*.py

# Create startup script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "Starting LTM Network Intelligence Platform..."\n\
echo "Environment: ${ENVIRONMENT:-development}"\n\
\n\
# Wait for dependencies\n\
echo "Waiting for dependencies to be ready..."\n\
\n\
# Wait for Neo4j\n\
if [ -n "$NEO4J_URI" ]; then\n\
    echo "Waiting for Neo4j..."\n\
    until curl -s "${NEO4J_URI/bolt/http}" > /dev/null 2>&1; do\n\
        sleep 2\n\
    done\n\
    echo "Neo4j is ready!"\n\
fi\n\
\n\
# Wait for Redis\n\
if [ -n "$REDIS_URL" ]; then\n\
    echo "Waiting for Redis..."\n\
    until redis-cli -u "$REDIS_URL" ping > /dev/null 2>&1; do\n\
        sleep 2\n\
    done\n\
    echo "Redis is ready!"\n\
fi\n\
\n\
# Wait for PostgreSQL\n\
if [ -n "$POSTGRES_HOST" ]; then\n\
    echo "Waiting for PostgreSQL..."\n\
    until pg_isready -h "$POSTGRES_HOST" -p 5432 -U "$POSTGRES_USER" > /dev/null 2>&1; do\n\
        sleep 2\n\
    done\n\
    echo "PostgreSQL is ready!"\n\
fi\n\
\n\
# Initialize platform if not already initialized\n\
if [ ! -f "/app/config/platform_initialized" ]; then\n\
    echo "Initializing LTM platform..."\n\
    python unified_network_intelligence.py --initialize --components ltm,mcp,kg,security,performance,api\n\
    touch /app/config/platform_initialized\n\
fi\n\
\n\
# Start the platform\n\
echo "Starting LTM Network Intelligence Platform..."\n\
exec python unified_network_intelligence.py "$@"\n\
' > /app/start.sh

RUN chmod +x /app/start.sh

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Switch to non-root user
USER appuser

# Expose ports
EXPOSE 8000 8002 8003

# Set entrypoint
ENTRYPOINT ["/app/start.sh"]
CMD []