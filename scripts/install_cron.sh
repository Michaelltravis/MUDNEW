#!/bin/bash
# Install Misthollow backup cron job

CRON_LINE="0 */6 * * * /Users/michaeltravis/clawd/projects/Misthollow/scripts/backup.sh >> /Users/michaeltravis/clawd/projects/Misthollow/backups/backup.log 2>&1"

# Check if already installed
if crontab -l 2>/dev/null | grep -q "Misthollow/scripts/backup.sh"; then
    echo "Cron job already installed"
else
    (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
    echo "Cron job installed: Backups every 6 hours"
fi

echo ""
echo "Current cron jobs:"
crontab -l 2>/dev/null | grep -v "^#" | head -5
