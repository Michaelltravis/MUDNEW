#!/usr/bin/env python3
"""Fix zone files by adding missing vnum fields."""
import json
import os

def fix_zone_file(filepath):
    """Add vnum fields to rooms in a zone file."""
    print(f"Fixing {filepath}...")

    with open(filepath, 'r') as f:
        data = json.load(f)

    # Fix rooms - add vnum field matching the key
    if 'rooms' in data:
        for vnum_str, room_data in data['rooms'].items():
            room_data['vnum'] = int(vnum_str)

    # Fix mobiles - add vnum field matching the key
    if 'mobiles' in data:
        for vnum_str, mob_data in data['mobiles'].items():
            mob_data['vnum'] = int(vnum_str)

    # Fix objects - add vnum field matching the key
    if 'objects' in data:
        for vnum_str, obj_data in data['objects'].items():
            obj_data['vnum'] = int(vnum_str)

    # Write back
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"  Fixed {len(data.get('rooms', {}))} rooms, {len(data.get('mobiles', {}))} mobs, {len(data.get('objects', {}))} objects")

def main():
    zones_dir = 'world/zones'

    # Fix the new zones (90-160)
    for zone_num in [90, 100, 110, 120, 130, 140, 150, 160]:
        filepath = os.path.join(zones_dir, f'zone_{zone_num:03d}.json')
        if os.path.exists(filepath):
            fix_zone_file(filepath)
        else:
            print(f"Warning: {filepath} not found")

    print("\nDone!")

if __name__ == '__main__':
    main()
