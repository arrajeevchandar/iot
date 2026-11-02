#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/create_credentials.py
case "${1:-}" in
  --full)
    .venv/bin/python -m pip install -r tinyml/requirements.txt
    export PLATFORMIO_CORE_DIR="${PLATFORMIO_CORE_DIR:-/workspace/.platformio}"
    .venv/bin/pio run -e esp32dev -j 4
    .venv/bin/python scripts/merge_firmware.py --environment esp32dev
    ;;
  "") ;;
  *) echo 'Usage: bash scripts/setup.sh [--full]'; exit 2 ;;
esac
.venv/bin/python -m pytest -q
echo 'Setup complete. Start the local demo with: bash scripts/run.sh'
