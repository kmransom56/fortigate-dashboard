FROM python:3.12-slim

WORKDIR /app

# Copy project files
COPY ./app ./app
COPY ./app/certs ./certs
COPY ./requirements.txt .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose FastAPI port
EXPOSE 8001

# Run uvicorn directly (no --reload)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
