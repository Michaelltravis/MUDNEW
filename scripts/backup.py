#!/usr/bin/env python3
"""
Misthollow Automated Backup System

Creates timestamped backups of:
- Player save files (data/players/)
- Zone files (world/zones/)
- Configuration files
- Logs (optional)

Usage:
    python3 scripts/backup.py              # Full backup
    python3 scripts/backup.py --players    # Players only
    python3 scripts/backup.py --world      # World/zones only
    python3 scripts/backup.py --restore <backup_file>  # Restore from backup
    python3 scripts/backup.py --list       # List available backups
    python3 scripts/backup.py --prune 7    # Delete backups older than 7 days
"""

import os
import sys
import json
import shutil
import tarfile
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
BACKUP_DIR = PROJECT_ROOT / "backups"
DATA_DIR = PROJECT_ROOT / "data"
WORLD_DIR = PROJECT_ROOT / "world"
SRC_DIR = PROJECT_ROOT / "src"

# What to back up
BACKUP_TARGETS = {
    "players": DATA_DIR / "players",
    "zones": WORLD_DIR / "zones",
    "updates": DATA_DIR / "updates.json",
    "motd": DATA_DIR / "motd.txt",
    "config": SRC_DIR / "config.py",
}

# Optional targets (backed up if they exist)
OPTIONAL_TARGETS = {
    "logs": PROJECT_ROOT / "server.log",
    "help_custom": DATA_DIR / "help_custom.json",
}


def ensure_backup_dir():
    """Create backup directory if it doesn't exist."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    return BACKUP_DIR


def get_timestamp():
    """Get formatted timestamp for backup filename."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def create_backup(include_players=True, include_world=True, include_logs=False):
    """Create a compressed backup archive."""
    ensure_backup_dir()
    timestamp = get_timestamp()
    
    # Determine backup type for filename
    if include_players and include_world:
        backup_type = "full"
    elif include_players:
        backup_type = "players"
    elif include_world:
        backup_type = "world"
    else:
        print("Error: Nothing to back up!")
        return None
    
    backup_name = f"realmsmud_{backup_type}_{timestamp}.tar.gz"
    backup_path = BACKUP_DIR / backup_name
    
    print(f"Creating backup: {backup_name}")
    
    files_backed_up = 0
    total_size = 0
    
    with tarfile.open(backup_path, "w:gz") as tar:
        # Back up player data
        if include_players:
            players_dir = BACKUP_TARGETS["players"]
            if players_dir.exists():
                for player_file in players_dir.glob("*.json"):
                    arcname = f"players/{player_file.name}"
                    tar.add(player_file, arcname=arcname)
                    files_backed_up += 1
                    total_size += player_file.stat().st_size
                    print(f"  + {arcname}")
        
        # Back up world/zone files
        if include_world:
            zones_dir = BACKUP_TARGETS["zones"]
            if zones_dir.exists():
                for zone_file in zones_dir.glob("*.json"):
                    arcname = f"zones/{zone_file.name}"
                    tar.add(zone_file, arcname=arcname)
                    files_backed_up += 1
                    total_size += zone_file.stat().st_size
                    print(f"  + {arcname}")
        
        # Back up config files
        for name, path in BACKUP_TARGETS.items():
            if name in ("players", "zones"):
                continue  # Already handled
            if path.exists() and path.is_file():
                arcname = f"config/{path.name}"
                tar.add(path, arcname=arcname)
                files_backed_up += 1
                total_size += path.stat().st_size
                print(f"  + {arcname}")
        
        # Optional: logs
        if include_logs:
            for name, path in OPTIONAL_TARGETS.items():
                if path.exists():
                    arcname = f"optional/{path.name}"
                    tar.add(path, arcname=arcname)
                    files_backed_up += 1
                    total_size += path.stat().st_size
                    print(f"  + {arcname}")
        
        # Add manifest
        manifest = {
            "timestamp": timestamp,
            "type": backup_type,
            "files_count": files_backed_up,
            "original_size_bytes": total_size,
            "realmsmud_version": "1.0.0",
        }
        manifest_json = json.dumps(manifest, indent=2)
        manifest_bytes = manifest_json.encode("utf-8")
        
        import io
        manifest_info = tarfile.TarInfo(name="manifest.json")
        manifest_info.size = len(manifest_bytes)
        tar.addfile(manifest_info, io.BytesIO(manifest_bytes))
    
    backup_size = backup_path.stat().st_size
    compression_ratio = (1 - backup_size / total_size) * 100 if total_size > 0 else 0
    
    print(f"\n✓ Backup complete: {backup_path}")
    print(f"  Files: {files_backed_up}")
    print(f"  Original size: {total_size / 1024:.1f} KB")
    print(f"  Compressed size: {backup_size / 1024:.1f} KB ({compression_ratio:.1f}% compression)")
    
    return backup_path


def list_backups():
    """List all available backups."""
    ensure_backup_dir()
    backups = sorted(BACKUP_DIR.glob("realmsmud_*.tar.gz"), reverse=True)
    
    if not backups:
        print("No backups found.")
        return []
    
    print(f"Available backups in {BACKUP_DIR}:\n")
    print(f"{'Filename':<45} {'Size':>10} {'Date':>20}")
    print("-" * 80)
    
    for backup in backups:
        size = backup.stat().st_size
        mtime = datetime.fromtimestamp(backup.stat().st_mtime)
        size_str = f"{size / 1024:.1f} KB" if size < 1024 * 1024 else f"{size / 1024 / 1024:.1f} MB"
        print(f"{backup.name:<45} {size_str:>10} {mtime.strftime('%Y-%m-%d %H:%M:%S'):>20}")
    
    print(f"\nTotal: {len(backups)} backup(s)")
    return backups


def is_within_directory(directory, target):
    """Check if target path is within the directory."""
    abs_directory = os.path.realpath(directory)
    abs_target = os.path.realpath(target)
    prefix = os.path.commonpath([abs_directory, abs_target])
    return prefix == abs_directory


def restore_backup(backup_file, dry_run=False):
    """Restore from a backup archive."""
    backup_path = Path(backup_file)
    if not backup_path.exists():
        # Try looking in backup directory
        backup_path = BACKUP_DIR / backup_file
    
    if not backup_path.exists():
        print(f"Error: Backup file not found: {backup_file}")
        return False
    
    print(f"Restoring from: {backup_path}")
    
    if dry_run:
        print("\n[DRY RUN - no changes will be made]\n")
    
    with tarfile.open(backup_path, "r:gz") as tar:
        # Read manifest
        try:
            manifest_file = tar.extractfile("manifest.json")
            if manifest_file:
                manifest = json.load(manifest_file)
                print(f"Backup info:")
                print(f"  Type: {manifest.get('type', 'unknown')}")
                print(f"  Timestamp: {manifest.get('timestamp', 'unknown')}")
                print(f"  Files: {manifest.get('files_count', 'unknown')}")
        except KeyError:
            print("Warning: No manifest found in backup")
        
        print("\nFiles to restore:")
        for member in tar.getmembers():
            if member.name == "manifest.json":
                continue
            
            # Determine destination and expected base directory
            base_dir = PROJECT_ROOT
            if member.name.startswith("players/"):
                dest = DATA_DIR / member.name
                base_dir = DATA_DIR / "players"
            elif member.name.startswith("zones/"):
                dest = WORLD_DIR / member.name
                base_dir = WORLD_DIR / "zones"
            elif member.name.startswith("config/"):
                filename = Path(member.name).name
                if filename == "config.py":
                    dest = SRC_DIR / filename
                elif filename == "updates.json":
                    dest = DATA_DIR / filename
                elif filename == "motd.txt":
                    dest = DATA_DIR / filename
                else:
                    dest = DATA_DIR / filename
                # For config files, we use Path(member.name).name which is already safe
                base_dir = dest.parent
            else:
                dest = PROJECT_ROOT / member.name
                base_dir = PROJECT_ROOT
            
            action = "would restore" if dry_run else "restoring"

            # Security check: Ensure destination is within the expected base directory
            if not is_within_directory(base_dir, dest):
                print(f"  [SECURITY WARNING] Skipping {member.name}: Path traversal detected!")
                continue

            print(f"  {action}: {member.name} -> {dest}")
            
            if not dry_run:
                # Create parent directories
                dest.parent.mkdir(parents=True, exist_ok=True)
                
                # Extract file
                if member.isfile():
                    with tar.extractfile(member) as src:
                        with open(dest, "wb") as dst:
                            dst.write(src.read())
    
    if dry_run:
        print("\n[DRY RUN complete - use without --dry-run to actually restore]")
    else:
        print("\n✓ Restore complete!")
        print("  Note: Restart the server to load restored data")
    
    return True


def prune_backups(days):
    """Delete backups older than specified days."""
    ensure_backup_dir()
    cutoff = datetime.now() - timedelta(days=days)
    backups = list(BACKUP_DIR.glob("realmsmud_*.tar.gz"))
    
    deleted = 0
    freed = 0
    
    for backup in backups:
        mtime = datetime.fromtimestamp(backup.stat().st_mtime)
        if mtime < cutoff:
            size = backup.stat().st_size
            print(f"Deleting: {backup.name} ({mtime.strftime('%Y-%m-%d')})")
            backup.unlink()
            deleted += 1
            freed += size
    
    if deleted:
        print(f"\n✓ Deleted {deleted} backup(s), freed {freed / 1024 / 1024:.1f} MB")
    else:
        print(f"No backups older than {days} days found.")


def main():
    parser = argparse.ArgumentParser(description="Misthollow Backup System")
    parser.add_argument("--players", action="store_true", help="Back up players only")
    parser.add_argument("--world", action="store_true", help="Back up world/zones only")
    parser.add_argument("--logs", action="store_true", help="Include logs in backup")
    parser.add_argument("--list", action="store_true", help="List available backups")
    parser.add_argument("--restore", metavar="FILE", help="Restore from backup file")
    parser.add_argument("--dry-run", action="store_true", help="Show what restore would do")
    parser.add_argument("--prune", metavar="DAYS", type=int, help="Delete backups older than DAYS")
    
    args = parser.parse_args()
    
    if args.list:
        list_backups()
    elif args.restore:
        restore_backup(args.restore, dry_run=args.dry_run)
    elif args.prune:
        prune_backups(args.prune)
    else:
        # Default: full backup unless specific flags set
        include_players = not args.world or args.players
        include_world = not args.players or args.world
        if args.players and not args.world:
            include_world = False
        if args.world and not args.players:
            include_players = False
        
        create_backup(
            include_players=include_players,
            include_world=include_world,
            include_logs=args.logs
        )


if __name__ == "__main__":
    main()
