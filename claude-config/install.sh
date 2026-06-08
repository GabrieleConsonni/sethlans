#!/usr/bin/env bash
# Installs the Sethlans toolkit into Claude Code's global home (~/.claude).
# Copies the /sethlans command, the generic subagents, and the Tabula protocol.
#
# Usage:
#   ./install.sh            # copy (skips files that already exist)
#   ./install.sh --force    # overwrite
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${HOME}/.claude"
FORCE=0
[[ "${1:-}" == "--force" ]] && FORCE=1

echo "Installing Sethlans toolkit -> $DEST"
mkdir -p "$DEST/commands" "$DEST/agents"

copy_safe() {
  local from="$1" to="$2"
  if [[ -e "$to" && $FORCE -eq 0 ]]; then
    echo "  already exists: $to (use --force to overwrite) - skipping"
    return
  fi
  cp "$from" "$to"
  echo "  copied: $to"
}

for f in "$SRC"/commands/*.md; do
  copy_safe "$f" "$DEST/commands/$(basename "$f")"
done
copy_safe "$SRC/tabula-protocol.md"   "$DEST/tabula-protocol.md"
for f in "$SRC"/agents/*.md; do
  copy_safe "$f" "$DEST/agents/$(basename "$f")"
done

echo "Done. Restart Claude Code and type /sethlans to use it."
