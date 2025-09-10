# Multi-stage build for enterprise FortiGate Dashboard
FROM python:3.12-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV UV_VERSION=0.4.18
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies with better caching
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    iputils-ping \
    net-tools \
    sqlite3 \
    nodejs \
    npm \
    snmp \
    git \
    && curl -Ls https://astral.sh/uv/install.sh | sh \
    && mv ~/.local/bin/uv /usr/local/bin/uv \
    && chmod +x /usr/local/bin/uv \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Optionally install SVGO for runtime SVG optimization
RUN npm install -g svgo@4.0.0 || true

# Set working directory
WORKDIR /app

# Copy requirements file first for better Docker layer caching
COPY requirements.txt ./requirements.txt

# Install Python dependencies
RUN uv pip install --no-cache-dir --system -r requirements.txt

# Create necessary directories for enterprise features
RUN mkdir -p /app/certs \
    && mkdir -p /app/data \
    && mkdir -p /app/static/icons \
    && mkdir -p /app/static/icons_backup \
    && mkdir -p /app/logs \
    && mkdir -p /app/cache \
    && mkdir -p /app/temp

# Copy application code and static files
COPY app ./app
COPY tools ./tools
COPY scripts ./scripts

# Copy FortiGate inventory data and downloaded files
COPY downloaded_files ./downloaded_files

# Create secrets directory (will be overridden by Docker secrets in production)
RUN mkdir -p ./secrets

# Ensure icon database and SVG files are properly copied
COPY app/static/ ./app/static/

# Copy enterprise architecture documentation and project files
COPY ENTERPRISE_ARCHITECTURE.md ./ENTERPRISE_ARCHITECTURE.md
COPY CLAUDE.md ./CLAUDE.md
COPY README.md ./README.md 

# Create a non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && chown -R appuser:appuser /app \
    && chmod -R 755 /app

# Switch to non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 10000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:10000/api/cloud_status || exit 1

# Development stage
FROM base AS development
ENV ENVIRONMENT=development
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000", "--reload", "--workers", "1"]

# Production stage
FROM base AS production
ENV ENVIRONMENT=production

# Additional production optimizations
RUN python -O -m compileall /app/app/ \
    && find /app -name "*.pyc" -delete \
    && find /app -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Production command with optimized settings
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000", "--workers", "2", "--access-log", "--log-level", "info"]
