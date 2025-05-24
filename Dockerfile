FROM python:3.12-slim

WORKDIR /app

# Copy project files
COPY ./app ./app
COPY ./src ./src
COPY ./app/certs ./certs
COPY ./requirements.txt .

# Copy documentation and reference files
COPY ./fortigate_api_authentication_guide.md .
COPY ./ssl_certificate_verification_guide.md .
COPY ./curl_command.sh .

# Copy data files
COPY ./storelans-*.csv ./

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install fastapi uvicorn flask paramiko pyopenssl redis

# Create logs directory
RUN mkdir -p logs

# Make the curl command executable
RUN chmod +x curl_command.sh

# Expose ports for both applications
EXPOSE 8001 5002

# Default command runs the FastAPI dashboard
# Override with docker-compose to run the Flask troubleshooter
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]