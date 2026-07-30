#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SKILL_SRC="$REPO_ROOT/plugins/cline/specadia/skills/specadia-plan"

case "${1:---global}" in
  --global)
    DEST="${CLINE_SKILLS_DIR:-$HOME/.cline/skills}"
    ;;
  --project)
    DEST="$(pwd)/.cline/skills"
    ;;
  *)
    echo "usage: install-skills.sh [--global | --project]" >&2
    exit 2
    ;;
esac

if [[ ! -f "$SKILL_SRC/SKILL.md" ]]; then
  echo "error: Specadia skill not found at $SKILL_SRC" >&2
  exit 1
fi

mkdir -p "$DEST"
TARGET="$DEST/specadia-plan"

if [[ -e "$TARGET" && ! -L "$TARGET" ]]; then
  echo "error: $TARGET exists and is not a symlink" >&2
  exit 1
fi

if [[ -L "$TARGET" ]]; then
  RESOLVED="$(python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$TARGET")"
  EXPECTED="$(python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$SKILL_SRC")"
  if [[ "$RESOLVED" != "$EXPECTED" ]]; then
    echo "error: refusing to replace user-managed symlink $TARGET" >&2
    exit 1
  fi
fi

ln -sfn "$SKILL_SRC" "$TARGET"
echo "linked specadia-plan -> $SKILL_SRC"
