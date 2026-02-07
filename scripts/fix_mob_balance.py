#!/usr/bin/env python3
"""
RealmsMUD Mob Balance Fix Script
================================
Fixes broken damage dice and exp values from CircleMUD conversion.

The original conversion resulted in damage like "23d23+230" which averages
500+ damage per hit - instant death for any player.

This script applies balanced formulas appropriate for the mob's level.
"""

import json
import os
import sys
from pathlib import Path

# Balanced damage formulas by level range
# Format: (num_dice, die_size, bonus_per_level)
# Damage = num_dice d die_size + (level * bonus_per_level)
DAMAGE_FORMULAS = {
    # Level 1-5: Very weak, learning mobs
    (1, 5): {"dice": "1d4", "bonus_mult": 0.5},
    # Level 6-10: Basic threats
    (6, 10): {"dice": "1d6", "bonus_mult": 0.8},
    # Level 11-15: Moderate challenge
    (11, 15): {"dice": "1d8", "bonus_mult": 1.0},
    # Level 16-20: Serious threats
    (16, 20): {"dice": "2d6", "bonus_mult": 1.2},
    # Level 21-25: Dangerous
    (21, 25): {"dice": "2d8", "bonus_mult": 1.5},
    # Level 26-30: Very dangerous
    (26, 30): {"dice": "3d6", "bonus_mult": 1.8},
    # Level 31-40: Elite
    (31, 40): {"dice": "3d8", "bonus_mult": 2.0},
    # Level 41-50: Boss-tier
    (41, 50): {"dice": "4d8", "bonus_mult": 2.5},
}

# EXP formula: base_exp * level * level_multiplier
# This creates a curve where higher level mobs give proportionally more exp
BASE_EXP = 15
EXP_LEVEL_MULT = 1.3  # Exponential growth factor

# HP formulas (dice + fixed bonus)
HP_FORMULAS = {
    (1, 5): {"dice": "1d8", "bonus_mult": 3},      # ~7-11 HP at level 1-5
    (6, 10): {"dice": "2d8", "bonus_mult": 5},     # ~17-26 HP
    (11, 15): {"dice": "3d10", "bonus_mult": 8},   # ~40-60 HP
    (16, 20): {"dice": "4d10", "bonus_mult": 12},  # ~65-95 HP
    (21, 25): {"dice": "5d10", "bonus_mult": 18},  # ~100-150 HP
    (26, 30): {"dice": "6d10", "bonus_mult": 25},  # ~150-200 HP
    (31, 40): {"dice": "8d10", "bonus_mult": 35},  # ~220-300 HP
    (41, 50): {"dice": "10d10", "bonus_mult": 50}, # ~300-400 HP
}


def get_formula_for_level(formulas: dict, level: int) -> dict:
    """Get the appropriate formula for a given level."""
    for (min_lvl, max_lvl), formula in formulas.items():
        if min_lvl <= level <= max_lvl:
            return formula
    # Default to highest tier for levels above 50
    return list(formulas.values())[-1]


def calculate_balanced_damage(level: int) -> str:
    """Calculate balanced damage dice for a given level."""
    formula = get_formula_for_level(DAMAGE_FORMULAS, level)
    bonus = int(level * formula["bonus_mult"])
    if bonus > 0:
        return f"{formula['dice']}+{bonus}"
    return formula['dice']


def calculate_balanced_hp(level: int) -> str:
    """Calculate balanced HP dice for a given level."""
    formula = get_formula_for_level(HP_FORMULAS, level)
    bonus = level * formula["bonus_mult"]
    return f"{formula['dice']}+{int(bonus)}"


def calculate_balanced_exp(level: int) -> int:
    """Calculate balanced experience reward for a given level."""
    return int(BASE_EXP * (level ** EXP_LEVEL_MULT))


def is_shopkeeper(mob: dict) -> bool:
    """Check if mob is a shopkeeper (should have godmode damage)."""
    return mob.get("special") == "shopkeeper" or "shopkeeper" in str(mob.get("flags", []))


def is_broken_damage(damage_dice: str, level: int) -> bool:
    """Check if damage dice value appears broken."""
    if not damage_dice:
        return False
    
    # Parse the damage string
    try:
        dice_part = damage_dice
        if '+' in damage_dice:
            dice_part, bonus = damage_dice.split('+')
            bonus = int(bonus)
        elif '-' in damage_dice:
            dice_part, penalty = damage_dice.split('-')
            bonus = -int(penalty)
        else:
            bonus = 0
        
        # If bonus is > 50 or > 10 * level, it's probably broken
        if bonus > 50 and bonus > level * 5:
            return True
        
        # Check for patterns like "23d23" which are clearly wrong
        if 'd' in dice_part:
            parts = dice_part.split('d')
            if len(parts) == 2:
                num_dice = int(parts[0])
                die_size = int(parts[1])
                # If num_dice matches level and die_size matches level, it's the broken formula
                if num_dice == level and die_size == level:
                    return True
                # Or if average damage is way too high
                avg_damage = (num_dice * (die_size + 1) / 2) + bonus
                expected_max = level * 4 + 20  # Reasonable max for level
                if avg_damage > expected_max * 3:
                    return True
    except (ValueError, IndexError):
        pass
    
    return False


def fix_mob(mob: dict, vnum: str, dry_run: bool = True) -> tuple:
    """Fix a single mob's balance. Returns (changed, changes_list)."""
    changes = []
    level = mob.get("level", 1)
    
    # Skip shopkeepers - their 30000 damage is intentional
    if is_shopkeeper(mob):
        return False, []
    
    # Check and fix damage dice
    damage_dice = mob.get("damage_dice", "")
    if is_broken_damage(damage_dice, level):
        new_damage = calculate_balanced_damage(level)
        changes.append(f"damage: {damage_dice} -> {new_damage}")
        if not dry_run:
            mob["damage_dice"] = new_damage
    
    # Check and fix exp (if it's 8 or very low for the level)
    exp = mob.get("exp", 0)
    expected_exp = calculate_balanced_exp(level)
    if exp < expected_exp * 0.3:  # If exp is less than 30% of expected
        changes.append(f"exp: {exp} -> {expected_exp}")
        if not dry_run:
            mob["exp"] = expected_exp
    
    # Optionally fix HP if it seems broken
    hp_dice = mob.get("hp_dice", "")
    if hp_dice:
        try:
            # Parse HP dice to check if it's reasonable
            if '+' in hp_dice:
                dice_part, hp_bonus = hp_dice.split('+')
                hp_bonus = int(hp_bonus)
            else:
                hp_bonus = 0
            
            # If HP bonus is way too low for the level (common issue)
            if hp_bonus < level * 2 and level > 5:
                new_hp = calculate_balanced_hp(level)
                changes.append(f"hp: {hp_dice} -> {new_hp}")
                if not dry_run:
                    mob["hp_dice"] = new_hp
        except (ValueError, IndexError):
            pass
    
    return len(changes) > 0, changes


def process_zone_file(zone_path: Path, dry_run: bool = True) -> dict:
    """Process a single zone file and fix mob balance."""
    results = {
        "file": str(zone_path),
        "mobs_checked": 0,
        "mobs_fixed": 0,
        "changes": []
    }
    
    with open(zone_path, 'r') as f:
        zone_data = json.load(f)
    
    mobs = zone_data.get("mobs", {})
    if not isinstance(mobs, dict):
        return results
    
    for vnum, mob in mobs.items():
        results["mobs_checked"] += 1
        changed, changes = fix_mob(mob, vnum, dry_run)
        if changed:
            results["mobs_fixed"] += 1
            mob_name = mob.get("short_desc", mob.get("name", "unknown"))
            results["changes"].append({
                "vnum": vnum,
                "name": mob_name,
                "level": mob.get("level", 1),
                "changes": changes
            })
    
    if not dry_run and results["mobs_fixed"] > 0:
        with open(zone_path, 'w') as f:
            json.dump(zone_data, f, indent=2)
    
    return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fix mob balance in RealmsMUD zones")
    parser.add_argument("--apply", action="store_true", help="Actually apply fixes (default is dry-run)")
    parser.add_argument("--zone", type=str, help="Process only this zone file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show all changes")
    args = parser.parse_args()
    
    dry_run = not args.apply
    
    # Find zone files
    zones_dir = Path(__file__).parent.parent / "world" / "zones"
    if args.zone:
        zone_files = [zones_dir / args.zone]
    else:
        zone_files = sorted(zones_dir.glob("zone_*.json"))
    
    print(f"{'DRY RUN - ' if dry_run else ''}RealmsMUD Mob Balance Fix")
    print("=" * 60)
    
    total_checked = 0
    total_fixed = 0
    
    for zone_path in zone_files:
        if not zone_path.exists():
            print(f"Warning: {zone_path} not found")
            continue
        
        results = process_zone_file(zone_path, dry_run)
        total_checked += results["mobs_checked"]
        total_fixed += results["mobs_fixed"]
        
        if results["mobs_fixed"] > 0:
            zone_name = zone_path.stem
            print(f"\n{zone_name}: {results['mobs_fixed']}/{results['mobs_checked']} mobs need fixes")
            
            if args.verbose:
                for change in results["changes"]:
                    print(f"  [{change['vnum']}] {change['name']} (L{change['level']})")
                    for c in change["changes"]:
                        print(f"    - {c}")
    
    print("\n" + "=" * 60)
    print(f"Total: {total_fixed}/{total_checked} mobs {'would be' if dry_run else 'were'} fixed")
    
    if dry_run and total_fixed > 0:
        print("\nRun with --apply to actually make changes")


if __name__ == "__main__":
    main()
