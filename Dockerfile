FROM python:3.12-slim

# Update system packages
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY ./app ./app
COPY ./src ./src
COPY ./app/certs ./certs
COPY ./requirements.txt .
COPY ./curl_command.sh .
# Install dependencies
RUN pip install --upgrade pip
RUN pip install uv
RUN uv venv  # create a virtual environment for uv
RUN uv pip install -r requirements.txt
# Create logs directory
RUN mkdir -p logs

# Make the curl command executable
RUN chmod +x curl_command.sh

# Expose port 10000 for both applications
EXPOSE 10000

# Default command runs the FastAPI dashboard
CMD ["sh", "-c", "HOST_IP=$(ip route | awk '/default/ {print $3}'); echo \"Application listening on port 10000; connect via http://$HOST_IP:10000\"; uv run uvicorn app.main:app --host 0.0.0.0 --port 10000"]