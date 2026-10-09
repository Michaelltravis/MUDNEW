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
# (the `|| true` matters: with pipefail, "no runtime files modified" made grep exit 1 and
#  silently killed the whole deploy right after "== pull" — reported from the first real run)
git status --porcelain --untracked-files=no | awk '{print $2}' | { grep -E "$RUNTIME_RE" || true; } | while read -r f; do
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
# Stop whatever holds the game ports, however it was started ("python3 main.py" from run.sh,
# "python3 src/main.py" from older notes, a launchd job...). Matching on the process name alone
# missed the older form: the old server kept the ports, the new one could not bind, and the
# health check below happily talked to the OLD server.
# (always succeeds: lsof exits 1 when a port is free, and under set -e + pipefail that alone
#  would abort the deploy between stopping the old server and starting the new one)
ports_pids() { lsof -ti tcp:4000 -sTCP:LISTEN 2>/dev/null; lsof -ti tcp:4001 -sTCP:LISTEN 2>/dev/null; lsof -ti tcp:4003 -sTCP:LISTEN 2>/dev/null; true; }
old_pids=$(ports_pids | sort -u | tr '\n' ' ')
[ -n "$old_pids" ] && echo "   stopping $old_pids" && kill $old_pids 2>/dev/null || true
pkill -f "main.py" 2>/dev/null || true
for i in $(seq 1 10); do [ -z "$(ports_pids)" ] && break; sleep 1; done
left=$(ports_pids | sort -u | tr '\n' ' '); [ -n "$left" ] && kill -9 $left 2>/dev/null || true
sleep 1
nohup ./run.sh > server.log 2>&1 &
up=0
for i in $(seq 1 60); do
  sleep 1
  if curl -sf -o /dev/null http://localhost:4001/ && curl -sf -o /dev/null http://localhost:4003/; then up=1; break; fi
done
if [ "$up" = 1 ]; then echo "== up: web map :4001, bridge+art :4003, telnet :4000"
else echo "!! server did not answer on :4001/:4003 within 60 s — see server.log"; tail -20 server.log; exit 1; fi
# /art/ only exists in the new build, so it doubles as "is the NEW server the one answering?"
if curl -sf -o /dev/null http://localhost:4003/art/manifest.json; then
  echo "== new build is serving (art on :4003; the proxy must route mud.frostpine.net/art/* to :4003, like /ws)"
else
  echo "!! :4003 answers but /art/manifest.json is 404 — an OLD server is still holding the ports."
  echo "   listening: $(lsof -nP -iTCP:4003 -sTCP:LISTEN 2>/dev/null | tail -n +2 | awk '{print $1" pid "$2}' | tr '\n' ' ')"
  echo "   server.log:"; tail -5 server.log | sed 's/^/     /'
  exit 1
fi
echo "== open https://map.frostpine.net/platformer"
