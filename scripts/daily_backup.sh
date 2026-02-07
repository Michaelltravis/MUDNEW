#!/bin/bash
# Daily backup script for RealmsMUD
# Run via cron: 0 4 * * * /path/to/daily_backup.sh >> /path/to/backups/cron.log 2>&1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_SCRIPT="$PROJECT_DIR/scripts/backup.py"
PYTHON3=$(which python3)

echo "=== RealmsMUD Daily Backup - $(date) ==="

# Create backup
$PYTHON3 "$BACKUP_SCRIPT"

# Prune backups older than 14 days
$PYTHON3 "$BACKUP_SCRIPT" --prune 14

echo "=== Backup complete ==="
echo ""
