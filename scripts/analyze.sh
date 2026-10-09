#!/usr/bin/env bash
# Unified entry point: agent mode by default; use --mode api for API mode
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -f "$ROOT/config/settings.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/config/settings.env"
  set +a
fi

if [[ $# -lt 1 ]]; then
  echo "Usage:"
  echo "  bash scripts/analyze.sh <video>                  # default agent: frame extraction + work package only"
  echo "  bash scripts/analyze.sh <video> --mode api       # fully automated via API"
  echo "  bash scripts/extract_frames.sh <video>           # same as agent"
  echo "  bash scripts/analyze_api.sh <video>              # same as api"
  exit 1
fi

PYTHON="python3"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
fi

export PYTHONUNBUFFERED=1
exec "$PYTHON" "$ROOT/src/main.py" "$@"
