#!/usr/bin/env bash
# Deploy Misthollow on frostpine: pull the branch, install the one Python dep, restart the server.
# Idempotent; safe to run by hand, by OpenClaw, or by .github/workflows/deploy-frostpine.yml.
#   bash deploy/frostpine.sh [branch]     (default: claude/nice-johnson-slpinu)
set -euo pipefail
BRANCH="${1:-claude/nice-johnson-slpinu}"
REPO_DIR="${MUD_DIR:-$HOME/MUDNEW}"
cd "$REPO_DIR"

echo "== pull $BRANCH"
git fetch origin "$BRANCH"
git checkout -q "$BRANCH"
git reset -q --hard "origin/$BRANCH"

echo "== deps"
python3 -m pip install -q aiohttp 2>/dev/null || pip3 install -q aiohttp

echo "== restart"
pkill -9 -f "python3 main.py" 2>/dev/null || true
sleep 2
nohup ./run.sh > server.log 2>&1 &
for i in $(seq 1 45); do
  sleep 1
  if curl -sf -o /dev/null http://localhost:4001/ && curl -sf -o /dev/null http://localhost:4003/; then
    echo "== up: web map :4001, bridge+art :4003, telnet :4000 (commit $(git rev-parse --short HEAD))"
    break
  fi
done
curl -sf -o /dev/null http://localhost:4003/art/manifest.json && echo "== art served on :4003 (/art/ must be proxied from mud.frostpine.net)" || echo "!! /art/manifest.json not served — characters will render as silhouettes"

echo "== proxy check (Caddy must route mud.frostpine.net/art/* -> :4003 and /ws -> :4003; map.frostpine.net/* -> :4001)"
command -v caddy >/dev/null && caddy validate --config /etc/caddy/Caddyfile >/dev/null 2>&1 && echo "   Caddyfile validates" || echo "   (caddy not found or validation skipped — verify the /art/ route by hand)"
echo "== open https://map.frostpine.net/platformer"
