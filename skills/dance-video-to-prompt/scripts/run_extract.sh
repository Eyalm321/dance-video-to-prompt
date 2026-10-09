#!/usr/bin/env bash
# Frame extraction wrapper: auto-locates REPO_ROOT, does not call any model API
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd -P)"

resolve_repo_root() {
  if [[ -n "${DANCE_VIDEO_PROMPT_ROOT:-}" && -d "${DANCE_VIDEO_PROMPT_ROOT}" ]]; then
    echo "$DANCE_VIDEO_PROMPT_ROOT"
    return
  fi

  # skills/dance-video-to-prompt → two levels up is the repo root
  local cand
  cand="$(cd "$SKILL_DIR/../.." && pwd)"
  if [[ -x "$cand/scripts/extract_frames.sh" ]]; then
    echo "$cand"
    return
  fi

  # .grok/skills/dance-video-to-prompt → three levels up
  cand="$(cd "$SKILL_DIR/../../.." && pwd)"
  if [[ -x "$cand/scripts/extract_frames.sh" ]]; then
    echo "$cand"
    return
  fi

  # Default: repo root (two levels above skills/xxx)
  echo "$(cd "$SKILL_DIR/../.." && pwd)"
}

REPO_ROOT="$(resolve_repo_root)"
EXTRACT="$REPO_ROOT/scripts/extract_frames.sh"

if [[ ! -f "$EXTRACT" ]]; then
  echo "Error: frame extraction script not found: $EXTRACT"
  echo "Please set DANCE_VIDEO_PROMPT_ROOT to point to the project root directory"
  exit 1
fi

exec bash "$EXTRACT" "$@"
