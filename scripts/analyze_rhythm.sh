#!/usr/bin/env bash
# Video audio-track rhythm analysis (BPM / beats / energy) → rhythm_analysis.json + rhythm_brief.md
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ $# -lt 2 ]]; then
  echo "Usage: bash scripts/analyze_rhythm.sh <video_path> <output_dir OUT_DIR>"
  exit 1
fi

PYTHON="python3"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
fi

export PYTHONUNBUFFERED=1
exec "$PYTHON" "$ROOT/src/analyze_rhythm.py" "$1" -o "$2"
