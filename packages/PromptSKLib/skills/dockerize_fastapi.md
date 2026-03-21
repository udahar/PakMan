# Skill: Dockerize FastAPI App

**skill_id:** `dockerize_fastapi_001`  
**name:** dockerize_fastapi_app  
**category:** engineering  
**version:** 1.0  

## Description

Creates production-ready Docker configuration for FastAPI applications with multi-stage builds and security best practices.

## Primitive Tags

- dockerfile
- fastapi
- multi_stage_build
- production_ready
- security_hardening
- containerization

## Prompt Strategy

```
For Dockerizing FastAPI:

1. USE MULTI-STAGE BUILD
   - Stage 1: Build dependencies
   - Stage 2: Minimal runtime image
   - Reduces final image size significantly

2. OPTIMIZE LAYER CACHING
   - Copy requirements.txt first
   - Install dependencies before copying code
   - Changes to code don't invalidate dependency cache

3. SECURITY HARDENING
   - Run as non-root user
   - Use slim/alpine base images
   - Don't include dev dependencies
   - Set proper file permissions

4. PRODUCTION CONFIGURATION
   - Use uvicorn with workers
   - Configure health checks
   - Set environment variables
   - Proper signal handling
```

## Solution Summary

```dockerfile
# Stage 1: Build dependencies
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .

# Install dependencies to virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# Stage 2: Runtime image
FROM python:3.11-slim

# Security: Create non-root user
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=appuser:appgroup . .

# Security: Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production

# Run with uvicorn workers
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

## docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/app
      - REDIS_URL=redis://redis:6379
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=app
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

volumes:
  postgres_data:
```

## Tests Passed

- [x] Multi-stage build reduces image size
- [x] Runs as non-root user
- [x] Health check configured
- [x] Dependencies cached properly
- [x] Production uvicorn workers
- [x] docker-compose with dependencies
- [x] Proper signal handling
- [x] Environment variables configured

## Benchmark Score

Pending evaluation

## Failure Modes

- **Large image**: Not using multi-stage build
  - Mitigation: Always use multi-stage, slim base images
- **Root user**: Security vulnerability
  - Mitigation: Create and use non-root user
- **No health check**: Undetected failures
  - Mitigation: Configure HEALTHCHECK in Dockerfile
- **Single worker**: Poor performance
  - Mitigation: Use multiple uvicorn workers

## Created From Task

Initial skill library creation

## Related Skills

- `fastapi_structure_001` - FastAPI project structure
- `async_database_001` - Async database connections
- `logging_setup_001` - Production logging

## Timestamp

2026-03-08
