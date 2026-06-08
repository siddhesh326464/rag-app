# --- UI MICROSERVICE (STREAMLIT) ---
FROM python:3.11-slim

# Install uv (blazing fast package manager - 10-100x faster than pip)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /apps

# Install system dependencies (build-essential needed by nemoguardrails -> annoy C++ extension)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies with uv
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Copy application code
COPY . .

# Set Environment Variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8501

# Streamlit default port
EXPOSE 8501

# Start the Streamlit application
CMD ["streamlit", "run", "ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]