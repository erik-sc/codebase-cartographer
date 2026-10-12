#!/usr/bin/env bash
# Installs codebase-cartographer skills and agents for Claude Code.
#   ./install.sh                 -> user scope (~/.claude)
#   ./install.sh project [DIR]   -> project scope (DIR/.claude, default: cwd) + merged permissions
set -euo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCOPE="${1:-user}"
TARGET="${2:-$PWD}"

if [ "$SCOPE" = "user" ]; then DEST="$HOME/.claude"; else DEST="$TARGET/.claude"; fi
mkdir -p "$DEST/skills" "$DEST/agents"

for d in "$SRC"/skills/*/; do
  name="$(basename "$d")"
  rm -rf "$DEST/skills/$name"
  cp -R "$d" "$DEST/skills/$name"
  echo "skill   -> $DEST/skills/$name"
done
cp -f "$SRC"/agents/*.md "$DEST/agents/"
echo "agents  -> $DEST/agents/"

if [ "$SCOPE" = "project" ]; then
  SETTINGS="$DEST/settings.json"
  python3 - "$SETTINGS" "$SRC/templates/settings.project.json" <<'PY'
import json, sys, os
path, tpl = sys.argv[1], sys.argv[2]
cur = json.load(open(path)) if os.path.exists(path) else {}
t = json.load(open(tpl))
perm = cur.setdefault("permissions", {})
for k in ("allow", "deny"):
    seen = list(perm.get(k, []))
    for rule in t["permissions"][k]:
        if rule not in seen:
            seen.append(rule)
    perm[k] = seen
json.dump(cur, open(path, "w"), indent=2)
print("settings-> " + path + " (permissions merged)")
PY
  CM="$TARGET/CLAUDE.md"
  if ! grep -q "codebase-knowledge" "$CM" 2>/dev/null; then
    printf '\n%s\n' "$(cat "$SRC/templates/CLAUDE.md.snippet")" >> "$CM"
    echo "CLAUDE.md-> appended knowledge-base import"
  fi
  echo "Accept the workspace-trust dialog once so the allow rules apply."
fi
echo
echo "Done. In Claude Code run:  /learn-codebase   (then /ask-codebase, /trace-flow, /quiz-me)"
