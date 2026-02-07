#!/bin/bash
# Install RealmsMUD backup cron job

CRON_LINE="0 */6 * * * /Users/michaeltravis/clawd/projects/RealmsMUD/scripts/backup.sh >> /Users/michaeltravis/clawd/projects/RealmsMUD/backups/backup.log 2>&1"

# Check if already installed
if crontab -l 2>/dev/null | grep -q "RealmsMUD/scripts/backup.sh"; then
    echo "Cron job already installed"
else
    (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
    echo "Cron job installed: Backups every 6 hours"
fi

echo ""
echo "Current cron jobs:"
crontab -l 2>/dev/null | grep -v "^#" | head -5
