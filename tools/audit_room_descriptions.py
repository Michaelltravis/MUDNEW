#!/usr/bin/env python3
"""Audit all zone files for rooms with missing or poor descriptions."""

import json
import os
from pathlib import Path

# Get the zones directory
BASE_DIR = Path(__file__).parent.parent
ZONES_DIR = BASE_DIR / 'world' / 'zones'

def audit_zones():
    """Check all zones for missing room descriptions."""
    zones_without_desc = {}
    total_rooms = 0
    rooms_missing_desc = 0
    rooms_short_desc = 0
    
    # Get all zone files
    zone_files = sorted(ZONES_DIR.glob('zone_*.json'))
    
    print(f"Auditing {len(zone_files)} zone files...\n")
    
    for zone_file in zone_files:
        with open(zone_file, 'r') as f:
            try:
                zone_data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"❌ ERROR reading {zone_file.name}: {e}")
                continue
        
        zone_num = zone_data.get('number', '?')
        zone_name = zone_data.get('name', 'Unknown')
        rooms = zone_data.get('rooms', {})
        
        if not rooms:
            continue
        
        missing = []
        short = []
        
        for room_key, room in rooms.items():
            total_rooms += 1
            vnum = room.get('vnum', room_key)
            name = room.get('name', 'Unnamed Room')
            desc = room.get('description', '').strip()
            
            if not desc:
                missing.append((vnum, name))
                rooms_missing_desc += 1
            elif len(desc) < 50:
                short.append((vnum, name, len(desc)))
                rooms_short_desc += 1
        
        if missing or short:
            zones_without_desc[zone_num] = {
                'name': zone_name,
                'file': zone_file.name,
                'missing': missing,
                'short': short,
                'total': len(rooms)
            }
    
    # Print results
    print("=" * 80)
    print("ROOM DESCRIPTION AUDIT RESULTS")
    print("=" * 80)
    print(f"\nTotal rooms checked: {total_rooms}")
    print(f"Rooms with NO description: {rooms_missing_desc}")
    print(f"Rooms with SHORT description (<50 chars): {rooms_short_desc}")
    print(f"Zones with issues: {len(zones_without_desc)}/{len(zone_files)}")
    print()
    
    if zones_without_desc:
        print("=" * 80)
        print("ZONES NEEDING ATTENTION")
        print("=" * 80)
        
        for zone_num in sorted(zones_without_desc.keys()):
            info = zones_without_desc[zone_num]
            print(f"\n📦 Zone {zone_num}: {info['name']} ({info['file']})")
            print(f"   Total rooms: {info['total']}")
            
            if info['missing']:
                print(f"   ❌ Missing descriptions ({len(info['missing'])}):")
                for vnum, name in info['missing'][:5]:  # Show first 5
                    print(f"      • Room {vnum}: {name}")
                if len(info['missing']) > 5:
                    print(f"      ... and {len(info['missing']) - 5} more")
            
            if info['short']:
                print(f"   ⚠️  Short descriptions ({len(info['short'])}):")
                for vnum, name, length in info['short'][:3]:  # Show first 3
                    print(f"      • Room {vnum}: {name} ({length} chars)")
                if len(info['short']) > 3:
                    print(f"      ... and {len(info['short']) - 3} more")
    else:
        print("✅ All rooms have adequate descriptions!")
    
    print("\n" + "=" * 80)
    
    # Save detailed report to file
    report_path = BASE_DIR / 'tools' / 'room_description_report.json'
    with open(report_path, 'w') as f:
        json.dump(zones_without_desc, f, indent=2)
    print(f"📄 Detailed report saved to: {report_path}")
    print("=" * 80)

if __name__ == '__main__':
    audit_zones()
