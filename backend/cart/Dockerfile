# --- Stage 1: Builder ---
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install build dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt

# Copy rest of the source code
COPY . .

# --- Stage 2: Final Image ---
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m appuser

WORKDIR /app

# Copy installed packages and app code from builder
COPY --from=builder /install /usr/local/
COPY --from=builder /app /app

# Use non-root user
USER appuser

EXPOSE 8000

# Entrypoint
CMD ["sh", "-c", "python manage.py runserver 0.0.0.0:8000"]