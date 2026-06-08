# --- INGESTION MICROSERVICE (BATCH WORKER) ---
FROM python:3.11-slim

# Install uv (blazing fast package manager - 10-100x faster than pip)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libmagic-dev \
    libxcb1 \
    libx11-6 \
    libxrender1 \
    libxext6 \
    libgl1 \
    libgomp1 \
    poppler-utils \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies with uv
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Copy application code
COPY . .

# Set Environment Variables
ENV PYTHONUNBUFFERED=1

# Cloud Run uses the PORT env var
EXPOSE 8080

# Start the Ingestion FastAPI application
CMD ["python", "-m", "uvicorn", "app.ingestion.processor:app", "--host", "0.0.0.0", "--port", "8080"]