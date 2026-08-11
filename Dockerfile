# Multi-stage production image for Seagulls Communications CRM
FROM node:22-alpine AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim AS runtime
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STATIC_DIR=/app/static \
    PORT=8000

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY backend/ ./
COPY --from=frontend-build /frontend/dist ./static

RUN if [ -f /app/start.sh ]; then sed -i 's/\r$//' /app/start.sh && chmod +x /app/start.sh; fi

EXPOSE 8000

# Double-quoted shell form so Railway's $PORT expands. Bind all interfaces.
CMD ["sh", "-c", "echo SeagullsCRM_listen_0.0.0.0_${PORT:-8000} && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
