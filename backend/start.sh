#!/bin/sh
set -eu

PORT="${PORT:-8000}"
echo "Seagulls CRM starting: host=0.0.0.0 port=${PORT} static_dir=${STATIC_DIR:-/app/static}"

# No shell glob risk: do not pass bare '*'. Railway healthchecks hit this process on $PORT.
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT}" \
  --proxy-headers \
  --forwarded-allow-ips="*"
