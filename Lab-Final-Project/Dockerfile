# ==========================================
# Stage 1: Builder
# ==========================================
FROM python:3.11-slim AS builder

WORKDIR /build
COPY requirements.txt .

# Install build dependencies (like gcc) if needed by any python packages
RUN apt-get update && apt-get install -y gcc && \
    pip install --user --no-cache-dir -r requirements.txt

# ==========================================
# Stage 2: Runtime
# ==========================================
FROM python:3.11-slim

# Security: Create and use a non-root user
RUN useradd -m -s /bin/bash appuser
USER appuser

WORKDIR /app

# Copy installed dependencies from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Ensure local python bin is on PATH so uvicorn can be found
ENV PATH=/home/appuser/.local/bin:$PATH

# Copy application source code
COPY --chown=appuser:appuser ./app ./app

# Expose default port
ENV PORT=8000
EXPOSE $PORT

HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:${PORT}/health || exit 1

# Start application
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
