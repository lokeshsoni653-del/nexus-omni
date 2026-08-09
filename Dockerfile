# OmniMind AI — Core Backend Engine Dockerfile for Cloud Deployments (Render / Railway / EC2)
FROM python:3.11-slim

WORKDIR /app

# Install essential build tools & C-libraries for ChromaDB and C-extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose container port
EXPOSE 8000

# Launch Uvicorn server dynamically reading PORT environment variable
CMD ["sh", "-c", "uvicorn omnimind.backend.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
