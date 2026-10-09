#!/usr/bin/env bash
# Install local dependencies (frame extraction needs opencv + pillow; API mode also needs httpx)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PYTHON="python3"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "python3 not found"
  exit 1
fi

if [[ ! -d "$ROOT/.venv" ]]; then
  "$PYTHON" -m venv "$ROOT/.venv"
fi

# shellcheck disable=SC1091
source "$ROOT/.venv/bin/activate"

PIP_INDEX="${PIP_INDEX_URL:-https://pypi.org/simple}"
pip install -U pip -i "$PIP_INDEX"
pip install -r "$ROOT/requirements.txt" -i "$PIP_INDEX"

if ! python -c "import cv2" 2>/dev/null; then
  pip install opencv-python-headless -i "$PIP_INDEX"
fi

if [[ ! -f "$ROOT/config/settings.env" ]]; then
  cp "$ROOT/config/settings.example.env" "$ROOT/config/settings.env"
  echo "Created config/settings.env (VISION_MODEL only needs to be filled in for API mode)"
fi

chmod +x "$ROOT/scripts/"*.sh 2>/dev/null || true

echo "Setup complete."
echo "Skill/Agent mode: bash scripts/extract_frames.sh /path/to/video.mp4"
echo "API mode:         bash scripts/analyze_api.sh /path/to/video.mp4"
