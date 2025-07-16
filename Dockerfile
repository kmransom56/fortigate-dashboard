FROM python:3.12-slim
# Set environment variables
ENV UV_VERSION=0.1.19

# Install dependencies and uv
RUN apt-get update && apt-get install -y curl ca-certificates \
    && curl -Ls https://astral.sh/uv/install.sh | sh \
    && mv ~/.local/bin/uv /usr/local/bin/uv \
    && chmod +x /usr/local/bin/uv \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
# Set working directory
WORKDIR /app
COPY . /app
# Create certs directory and copy SSL certificates
RUN mkdir -p /certs
# Copy actual certificates directory
COPY app/certs/ /certs/
# Copy requirements file
COPY requirements.txt ./requirements.txt

# Install dependencies
RUN uv pip install --no-cache-dir --system -r requirements.txt


# Copy the application code
COPY app ./app
COPY tools ./tools
COPY scripts ./scripts
COPY secrets ./secrets
# Ensure icons.db is copied
COPY app/static/icons.db ./app/static/icons.db

# Expose the port the app runs on
EXPOSE 10000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
