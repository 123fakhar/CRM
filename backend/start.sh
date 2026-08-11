#!/bin/sh
set -eu

PORT="${PORT:-8000}"
echo "Seagulls CRM starting: host=0.0.0.0 port=${PORT} static_dir=${STATIC_DIR:-/app/static}"

exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT}" \
  --proxy-headers \
  --forwarded-allow-ips="*"
