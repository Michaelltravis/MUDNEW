#!/usr/bin/env bash
# One-time setup on frostpine: check GitHub every minute and deploy when the branch moves.
#   bash deploy/install-autopull.sh            (install)
#   bash deploy/install-autopull.sh --remove   (uninstall)
set -euo pipefail
REPO_DIR="${MUD_DIR:-$HOME/MUDNEW}"
LINE="* * * * * cd $REPO_DIR && /bin/bash deploy/autopull.sh"
current=$(crontab -l 2>/dev/null | grep -v 'deploy/autopull.sh' || true)
if [ "${1:-}" = "--remove" ]; then
  printf '%s\n' "$current" | crontab -; echo "autopull removed"; exit 0
fi
printf '%s\n%s\n' "$current" "PATH=/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin
$LINE" | sed '/^$/d' | crontab -
echo "autopull installed: GitHub is checked every minute; log at $REPO_DIR/deploy.log"
crontab -l | grep autopull
