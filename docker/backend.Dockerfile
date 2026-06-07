FROM python:3.11-slim

WORKDIR /apps

RUN apt-get update && apt-get install -y \
    build-essential \
    libmagic-dev \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PORT=8080


EXPOSE 8080


CMD ["python", "-m", "uvicorn", "apps.main:app", "--host", "0.0.0.0", "--port", "8080"]