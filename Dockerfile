# ==============================================================================
# Multi-stage Dockerfile for Leiloar Radar API & Ingestion Engine
# ==============================================================================

FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir build

COPY src/ src/
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels .

# Runtime container
FROM python:3.12-slim AS runner

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

COPY .env.example .env
COPY fixtures/ fixtures/

ENV LEILOAR_API_HOST=0.0.0.0
ENV LEILOAR_API_PORT=8000
ENV LEILOAR_DATABASE_PATH=/app/data/leiloar_radar.db

RUN mkdir -p /app/data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "leiloar.cli", "serve", "--host", "0.0.0.0", "--port", "8000"]
