# OmniMind AI — Core Backend Engine Dockerfile for Cloud Deployments (Render / Railway / EC2)
FROM python:3.11-slim

WORKDIR /app

# Install essential build tools, C-libraries, and OCR engine
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    gcc \
    # Tesseract OCR engine for scanned PDF fallback
    tesseract-ocr \
    tesseract-ocr-eng \
    # poppler-utils required by pdf2image to convert PDF pages to images
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose container port
EXPOSE 8000

# Launch Uvicorn server dynamically reading PORT environment variable
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]
