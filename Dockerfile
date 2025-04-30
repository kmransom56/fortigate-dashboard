FROM python:3.12-slim

WORKDIR /app

# Copy project files
COPY ./app ./app
COPY ./app/certs ./certs
COPY ./requirements.txt .

# Copy our fixed curl command for reference
COPY ./fixed_curl_command.sh .
COPY ./fortigate_api_authentication_guide.md .
COPY ./ssl_certificate_verification_guide.md .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Make the fixed curl command executable
RUN chmod +x fixed_curl_command.sh

# Expose FastAPI port
EXPOSE 8001

# Run uvicorn directly (no --reload)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]