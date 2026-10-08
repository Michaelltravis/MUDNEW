#!/usr/bin/env bash
# Deploy Misthollow on frostpine: pull the branch, install the one Python dep, restart the server.
# Idempotent; run by hand, by OpenClaw, or by deploy/autopull.sh (the GitHub-driven path).
#   bash deploy/frostpine.sh [branch]          (default: claude/nice-johnson-slpinu)
#   NO_RESTART=1 bash deploy/frostpine.sh      (update files only)
set -euo pipefail
BRANCH="${1:-claude/nice-johnson-slpinu}"
REPO_DIR="${MUD_DIR:-$HOME/MUDNEW}"
cd "$REPO_DIR"

# Live game state that happens to be tracked in git. A deploy must never roll it back
# (the auction house, update notes, saved players, logs).
RUNTIME_RE='^(data/|src/data/|lib/|logs/|log/)'

echo "== pull $BRANCH"
git fetch -q origin "$BRANCH"

# refuse to clobber uncommitted CODE edits made on the box
dirty_code=$(git status --porcelain --untracked-files=no | awk '{print $2}' | grep -vE "$RUNTIME_RE" || true)
if [ -n "$dirty_code" ]; then
  echo "!! uncommitted changes to code on this machine — not deploying over them:"
  echo "$dirty_code" | sed 's/^/   /'
  echo "   commit or stash them (git stash) and run again."
  exit 2
fi

# keep the live copies of runtime files across the reset
keep=$(mktemp -d)
git status --porcelain --untracked-files=no | awk '{print $2}' | grep -E "$RUNTIME_RE" | while read -r f; do
  mkdir -p "$keep/$(dirname "$f")"; cp -p "$f" "$keep/$f"
done
git checkout -q "$BRANCH" 2>/dev/null || git checkout -q -B "$BRANCH" "origin/$BRANCH"
git reset -q --hard "origin/$BRANCH"
( cd "$keep" && find . -type f | while read -r f; do mkdir -p "$REPO_DIR/$(dirname "$f")"; cp -p "$f" "$REPO_DIR/$f"; done )
rm -rf "$keep"
echo "   at $(git rev-parse --short HEAD) — $(git log -1 --format=%s | cut -c1-70)"

echo "== deps"
python3 -m pip install -q aiohttp 2>/dev/null || pip3 install -q aiohttp || true

if [ "${NO_RESTART:-0}" = "1" ]; then echo "== files updated, server not restarted (NO_RESTART=1)"; exit 0; fi

echo "== restart"
pkill -f "python3 main.py" 2>/dev/null || true
sleep 3
pkill -9 -f "python3 main.py" 2>/dev/null || true
nohup ./run.sh > server.log 2>&1 &
up=0
for i in $(seq 1 60); do
  sleep 1
  if curl -sf -o /dev/null http://localhost:4001/ && curl -sf -o /dev/null http://localhost:4003/; then up=1; break; fi
done
if [ "$up" = 1 ]; then echo "== up: web map :4001, bridge+art :4003, telnet :4000"
else echo "!! server did not answer on :4001/:4003 within 60 s — see server.log"; tail -20 server.log; exit 1; fi
curl -sf -o /dev/null http://localhost:4003/art/manifest.json \
  && echo "== art served on :4003 (the proxy must route mud.frostpine.net/art/* to :4003, like /ws)" \
  || echo "!! /art/manifest.json not served — characters will render as silhouettes"
echo "== open https://map.frostpine.net/platformer"
