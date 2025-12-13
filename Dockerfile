FROM python:3.12-slim

LABEL maintainer="FortiGate Dashboard Team"
LABEL description="Enterprise FortiGate Network Management Dashboard with 3D Topology & AI Integration"
LABEL version="2.0"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    NODE_VERSION=20

# Install system dependencies including Node.js for scraping tools
RUN sed -i 's/main/main contrib non-free/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && apt-get install -y \
    gcc \
    g++ \
    pkg-config \
    libssl-dev \
    libffi-dev \
    curl \
    wget \
    git \
    sqlite3 \
    dnsutils \
    net-tools \
    iputils-ping \
    snmp \
    snmp-mibs-downloader \
    && curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Install uv for faster Python package management
RUN pip install --no-cache-dir uv

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with uv
RUN uv pip install --system --no-cache-dir -r requirements.txt

# Install additional packages for enterprise features
RUN uv pip install --system --no-cache-dir \
    pandas \
    numpy \
    beautifulsoup4 \
    lxml \
    redis \
    asyncio \
    aiofiles \
    playwright \
    meraki

# Copy application code
COPY . .

# Install Node.js dependencies for scraping tools (if package.json exists)
RUN if [ -f "./app/services/package.json" ]; then \
    cd app/services && npm install --omit=dev; \
    fi

# Install Playwright browsers for scraping
RUN playwright install --with-deps chromium

# Create necessary directories
RUN mkdir -p /app/data \
    /app/static/icons \
    /app/templates \
    /app/secrets \
    /app/downloaded_files \
    /app/logs \
    /app/cache \
    /app/assets

# Set up default secrets directory structure
RUN touch /app/secrets/.keep

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/debug/topology || exit 1

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
