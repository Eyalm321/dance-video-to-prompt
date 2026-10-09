#!/usr/bin/env bash
# API version: frame extraction + three-stage vision API analysis → prompt.md
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -f "$ROOT/config/settings.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/config/settings.env"
  set +a
fi

LOG_DIR="$ROOT/logs"
mkdir -p "$LOG_DIR"

if [[ $# -lt 1 ]]; then
  echo "Usage: bash scripts/analyze_api.sh <video_path> [extra args...]"
  echo "Example: bash scripts/analyze_api.sh ./dance.mp4"
  echo "         bash scripts/analyze_api.sh ./dance.mp4 --interval 0.25 --no-verify"
  exit 1
fi

VIDEO="$1"
shift || true

if [[ ! -f "$VIDEO" ]]; then
  echo "Error: video not found: $VIDEO"
  exit 1
fi

PYTHON="python3"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
fi

export PYTHONUNBUFFERED=1
"$PYTHON" "$ROOT/src/main.py" "$VIDEO" --mode api "$@" 2>&1 | tee -a "$LOG_DIR/analyze.log"
