# Dockerfile for restaurant-system
# Uses Python 3.11 (recommended for compatibility with eventlet)
FROM python:3.11-slim

# Prevents Python from writing .pyc files and enables unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies (for any packages that need compilation)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       gcc \
       libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY . /app

# Create a non-root user to run the app (optional but recommended)
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

# Recommended production ports and Gunicorn settings: use eventlet worker
EXPOSE 8000

# Keep GUNICORN_WORKERS=1: Socket.IO broadcasts only reach clients connected to
# the same worker process, so >1 worker silently drops live updates for some
# clients unless a shared message queue (e.g. Redis) backs socketio. One
# eventlet worker comfortably handles a single restaurant's concurrent load.
ENV WORKER_CLASS=eventlet
ENV GUNICORN_WORKERS=1

# Entrypoint: read worker class and workers count from environment at container start
CMD ["/bin/sh", "-c", "gunicorn -k ${WORKER_CLASS} -w ${GUNICORN_WORKERS} -b 0.0.0.0:${PORT:-8000} run:app"]
