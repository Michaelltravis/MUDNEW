#!/usr/bin/env bash
# One-time setup on frostpine: check GitHub every minute and deploy when the branch moves.
#   bash deploy/install-autopull.sh            (install)
#   bash deploy/install-autopull.sh --remove   (uninstall)
# macOS: a launchd agent (cron needs Full Disk Access there and fails with "Operation not
# permitted"). Linux: a crontab line.
set -euo pipefail
REPO_DIR="${MUD_DIR:-$HOME/MUDNEW}"
LABEL="net.frostpine.mud-autopull"

if [ "$(uname)" = "Darwin" ]; then
  PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
  launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
  if [ "${1:-}" = "--remove" ]; then rm -f "$PLIST"; echo "autopull removed"; exit 0; fi
  mkdir -p "$HOME/Library/LaunchAgents"
  cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key><array><string>/bin/bash</string><string>$REPO_DIR/deploy/autopull.sh</string></array>
  <key>WorkingDirectory</key><string>$REPO_DIR</string>
  <key>EnvironmentVariables</key><dict>
    <key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    <key>MUD_DIR</key><string>$REPO_DIR</string>
  </dict>
  <key>StartInterval</key><integer>60</integer>
  <key>RunAtLoad</key><true/>
  <!-- the deploy restarts the MUD server from inside this job; without this, launchd
       kills the freshly started server the moment the check exits -->
  <key>AbandonProcessGroup</key><true/>
  <key>StandardOutPath</key><string>$REPO_DIR/deploy.log</string>
  <key>StandardErrorPath</key><string>$REPO_DIR/deploy.log</string>
</dict></plist>
PL
  launchctl bootstrap "gui/$(id -u)" "$PLIST"
  echo "autopull installed (launchd $LABEL): GitHub is checked every minute; log at $REPO_DIR/deploy.log"
  launchctl print "gui/$(id -u)/$LABEL" 2>/dev/null | grep -E "state|run interval" | head -3
  exit 0
fi

LINE="* * * * * cd $REPO_DIR && /bin/bash deploy/autopull.sh"
current=$(crontab -l 2>/dev/null | grep -v 'deploy/autopull.sh' || true)
if [ "${1:-}" = "--remove" ]; then printf '%s\n' "$current" | crontab -; echo "autopull removed"; exit 0; fi
printf '%s\n%s\n' "$current" "PATH=/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin
$LINE" | sed '/^$/d' | crontab -
echo "autopull installed (cron): GitHub is checked every minute; log at $REPO_DIR/deploy.log"
