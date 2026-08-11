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

RUN chmod +x /app/start.sh

EXPOSE 8000

# Explicit sh -c keeps ${PORT} expansion reliable on Railway.
# Healthchecks must reach 0.0.0.0:$PORT (never 127.0.0.1).
CMD ["sh", "/app/start.sh"]
