FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV UV_VERSION=0.4.18

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    iputils-ping \
    net-tools \
    sqlite3 \
    nodejs \
    npm \
    snmp \
    && curl -Ls https://astral.sh/uv/install.sh | sh \
    && mv ~/.local/bin/uv /usr/local/bin/uv \
    && chmod +x /usr/local/bin/uv \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Optionally install SVGO for runtime SVG optimization
RUN npm install -g svgo@4.0.0 || true

# Set working directory
WORKDIR /app

# Copy requirements file first for better Docker layer caching
COPY requirements.txt ./requirements.txt

# Install Python dependencies
RUN uv pip install --no-cache-dir --system -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/certs \
    && mkdir -p /app/data \
    && mkdir -p /app/static/icons \
    && mkdir -p /app/static/icons_backup

# Copy application code and static files
COPY app ./app
COPY tools ./tools
COPY scripts ./scripts

# Create secrets directory (will be overridden by Docker secrets in production)
RUN mkdir -p ./secrets

# Ensure icon database and SVG files are properly copied
COPY app/static/ ./app/static/ 

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

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000", "--workers", "1"]
