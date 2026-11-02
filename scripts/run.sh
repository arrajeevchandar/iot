#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ "${1:-}" == "--public" ]]; then
  test -f .env || { echo 'Run .venv/bin/python scripts/create_credentials.py first.'; exit 1; }
  set -a
  source .env
  set +a
  exec .venv/bin/python -m uvicorn dashboard.app:app --host 0.0.0.0 --port "${PORT:-8000}"
fi
exec .venv/bin/python -m uvicorn dashboard.app:app --host 127.0.0.1 --port "${PORT:-8000}"
