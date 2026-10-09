#!/usr/bin/env bash
# Shared: frame extraction only, no model API calls (both the Skill version and the API version depend on this script)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ $# -lt 1 ]]; then
  echo "Usage: bash scripts/extract_frames.sh <video_path> [--interval 0.33] [--max-frames 36] [-o output_dir]"
  exit 1
fi

PYTHON="python3"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
fi

export PYTHONUNBUFFERED=1
exec "$PYTHON" "$ROOT/src/main.py" "$@" --mode agent
