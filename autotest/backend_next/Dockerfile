FROM python:3.11-slim

# Install Docker CLI so MarinaBox can spin up containers
RUN apt-get update && apt-get install -y docker.io && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy environment file (for API keys)
COPY .env ./

# Copy FastAPI application code
COPY app/ ./app/

# Expose the FastAPI port
EXPOSE 8000

# Run the FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
