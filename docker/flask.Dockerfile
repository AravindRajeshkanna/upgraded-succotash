# Stage 1: build dependencies
FROM python:3.12-slim AS builder

WORKDIR /app

# System deps for building wheels (psycopg2, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Install Python deps into a venv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY app/requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Stage 2: runtime
FROM python:3.12-slim

# Create non-root user
RUN useradd -m flaskuser

WORKDIR /app

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Only app code, no build tools
COPY app/ .

ENV FLASK_ENV=production \
    PYTHONUNBUFFERED=1

USER flaskuser

# Example: Gunicorn entrypoint
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
