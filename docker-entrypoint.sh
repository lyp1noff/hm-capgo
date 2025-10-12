#!/bin/bash
set -euo pipefail

echo "[ENTRYPOINT] Running migrations..."
alembic upgrade head

echo "[ENTRYPOINT] Starting app..."
exec gunicorn src.hm_capgo.main:app \
  -k uvicorn.workers.UvicornWorker \
  --workers 4 \
  --bind 0.0.0.0:8000 \
  --error-logfile - \
  --log-level info
