#!/usr/bin/env bash
# Installa il toolkit Sethlans nella home globale di Claude Code (~/.claude).
# Copia il command /sethlans, i subagent generici e il protocollo Tabula.
#
# Uso:
#   ./install.sh            # copia (salta i file gia presenti)
#   ./install.sh --force    # sovrascrive
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${HOME}/.claude"
FORCE=0
[[ "${1:-}" == "--force" ]] && FORCE=1

echo "Installazione toolkit Sethlans -> $DEST"
mkdir -p "$DEST/commands" "$DEST/agents"

copy_safe() {
  local from="$1" to="$2"
  if [[ -e "$to" && $FORCE -eq 0 ]]; then
    echo "  esiste gia: $to (usa --force per sovrascrivere) - salto"
    return
  fi
  cp "$from" "$to"
  echo "  copiato: $to"
}

copy_safe "$SRC/commands/sethlans.md" "$DEST/commands/sethlans.md"
copy_safe "$SRC/tabula-protocol.md"   "$DEST/tabula-protocol.md"
for f in "$SRC"/agents/*.md; do
  copy_safe "$f" "$DEST/agents/$(basename "$f")"
done

echo "Fatto. Riavvia Claude Code e digita /sethlans per usarlo."
