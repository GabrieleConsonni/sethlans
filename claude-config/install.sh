#!/usr/bin/env bash
# Installs the Sethlans toolkit into Claude Code's global home (~/.claude).
# Copies the /sethlans skill, the generic subagents, and the Tabula protocol.
# Source of truth: ../.claude-plugin/ (plugin directory).
#
# Usage:
#   ./install.sh            # copy (skips files that already exist)
#   ./install.sh --force    # overwrite
#
# Preferred: use the Claude Code plugin system instead:
#   /plugin install sethlans@claude-community
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$REPO_ROOT/.claude-plugin"
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

for f in "$SRC"/skills/*.md; do
  copy_safe "$f" "$DEST/commands/$(basename "$f")"
done
copy_safe "$SRC/tabula-protocol.md"  "$DEST/tabula-protocol.md"
for f in "$SRC"/agents/*.md; do
  copy_safe "$f" "$DEST/agents/$(basename "$f")"
done

echo "Done. Restart Claude Code and type /sethlans to use it."
