#!/bin/bash
# Misthollow Backup Script
# Run via cron: 0 */6 * * * /path/to/backup.sh

BACKUP_DIR="/Users/michaeltravis/clawd/projects/Misthollow/backups"
DATA_DIR="/Users/michaeltravis/clawd/projects/Misthollow/lib"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/realmsmud_backup_$DATE.tar.gz"

# Keep only last 20 backups
cd "$BACKUP_DIR" && ls -t realmsmud_backup_*.tar.gz 2>/dev/null | tail -n +21 | xargs rm -f 2>/dev/null

# Create backup
tar -czf "$BACKUP_FILE" -C "$(dirname $DATA_DIR)" "$(basename $DATA_DIR)" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "Backup created: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"
else
    echo "ERROR: Backup failed!"
    exit 1
fi
