#!/usr/bin/env bash
# Sync the skill to the project's .grok and the user's global directories for easy reuse
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SKILL_NAME="dance-video-to-prompt"

# Repo root: two levels above skills/xxx
REPO_ROOT="$(cd "$SKILL_DIR/../.." && pwd)"

echo "Source skill: $SKILL_DIR"
echo "Repo root:    $REPO_ROOT"

sync_to() {
  local dest="$1"
  mkdir -p "$(dirname "$dest")"
  rm -rf "$dest"
  mkdir -p "$dest"
  # Copy contents (without .git)
  cp -R "$SKILL_DIR/." "$dest/"
  # Make sure scripts are executable
  chmod +x "$dest/scripts/"*.sh 2>/dev/null || true
  echo "Synced → $dest"
}

# 1) Project-local Grok discovery path
sync_to "$REPO_ROOT/.grok/skills/$SKILL_NAME"

# 2) User-global Grok
if [[ -d "${HOME}/.grok" ]] || mkdir -p "${HOME}/.grok/skills" 2>/dev/null; then
  sync_to "${HOME}/.grok/skills/$SKILL_NAME"
fi

# 3) Claude / agents global (directory created automatically)
if mkdir -p "${HOME}/.agents/skills" 2>/dev/null; then
  sync_to "${HOME}/.agents/skills/$SKILL_NAME"
fi

# 4) Claude Code skills (directory created automatically)
if mkdir -p "${HOME}/.claude/skills" 2>/dev/null; then
  sync_to "${HOME}/.claude/skills/$SKILL_NAME"
fi

echo ""
echo "Done. Primary copy (maintain this one as the source of truth):"
echo "  $REPO_ROOT/skills/$SKILL_NAME"
echo ""
echo "Usage examples:"
echo "  /dance-video-to-prompt /path/to/video.mp4"
echo "  or: bash $REPO_ROOT/skills/$SKILL_NAME/scripts/run_extract.sh /path/to/video.mp4"
