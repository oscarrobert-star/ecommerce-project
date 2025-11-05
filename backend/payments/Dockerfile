# --- Stage 1: Builder with dependency install ---
    FROM python:3.11-slim as builder

    ENV PYTHONDONTWRITEBYTECODE=1
    ENV PYTHONUNBUFFERED=1
    
    # Install build dependencies
    RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        && rm -rf /var/lib/apt/lists/*
    
    WORKDIR /app
    
    # Cache dependencies: only re-run pip install if requirements.txt changes
    COPY requirements.txt .
    RUN pip install --prefix=/install --no-cache-dir -r requirements.txt
    
    # Then copy the rest of the app
    COPY . .
    
    # --- Stage 2: Final image ---
    FROM python:3.11-slim
    
    ENV PYTHONDONTWRITEBYTECODE=1
    ENV PYTHONUNBUFFERED=1
    
    # Install runtime deps
    RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq-dev \
        && rm -rf /var/lib/apt/lists/*
    
    WORKDIR /app
    
    # Copy dependencies and app from builder
    COPY --from=builder /install /usr/local
    COPY --from=builder /app /app
    
    EXPOSE 8000
    
    # Run migrations and start server
    CMD ["sh", "-c", "python manage.py runserver 0.0.0.0:8000"]