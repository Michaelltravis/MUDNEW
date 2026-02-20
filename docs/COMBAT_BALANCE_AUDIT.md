# Combat Balance Audit - February 3, 2026

## Executive Summary

The combat system has **critical balance issues** stemming from a bad CircleMUD data conversion. Most mob damage values would instantly kill players. This document catalogs all issues found and tracks fixes.

## Critical Issues

### 1. ⚠️ Mob Damage Dice (CRITICAL - GAME-BREAKING)

**Problem:** Damage dice values across most zones use a broken formula like `LdL+L*10` where L is mob level.

**Examples:**
| Mob | Level | Current Damage | Average | Impact |
|-----|-------|----------------|---------|--------|
| Shadow Guardian | 9 | `9d9+90` | ~130 dmg | 1-shot kill |
| Mage | 10 | `10d10+100` | ~155 dmg | 1-shot kill |
| Diamond Golem | 23 | `23d23+230` | ~506 dmg | Instant death |
| Waiter | 23 | `6d10+390` | ~423 dmg | Instant death |
| Wolf | 4 | `1d12+47` | ~54 dmg | 1-shot low levels |
| Cityguard | 10 | `1d12+123` | ~130 dmg | 1-shot kill |

**Expected Damage Ranges:**
- Level 1-5: ~1-8 damage per hit
- Level 6-10: ~2-12 damage per hit
- Level 11-15: ~4-20 damage per hit
- Level 16-20: ~8-30 damage per hit
- Level 21-25: ~12-40 damage per hit

**Fix:** Created `scripts/fix_mob_balance.py` to recalculate all damage values.

**Status:** ❌ NOT FIXED - Needs to be applied

---

### 2. ⚠️ Mob EXP Values (CRITICAL)

**Problem:** Almost every mob gives **8 exp** regardless of level. A level 23 diamond golem gives the same exp as a level 1 janitor.

**Expected EXP Formula:** `base_exp * level^1.3` (exponential growth)

| Level | Current EXP | Expected EXP |
|-------|-------------|--------------|
| 1 | 8 | ~15 |
| 5 | 8 | ~50 |
| 10 | 8 | ~150 |
| 15 | 8 | ~280 |
| 20 | 8 | ~450 |
| 25 | 8 | ~650 |

**Fix:** Included in `scripts/fix_mob_balance.py`

**Status:** ❌ NOT FIXED - Needs to be applied

---

### 3. ⚠️ Defense Formula Bug (MODERATE)

**Problem:** The defense formula inverts armor class:
```python
defense = 10 + (defender.get_armor_class() // 10)
```

This means:
- AC -10 (best armor) → defense 9 (easier to hit)
- AC +10 (no armor) → defense 11 (harder to hit)

**This is backwards!** Better armor should be harder to hit.

**Fix:** Change to:
```python
defense = 10 - (defender.get_armor_class() // 10)
```

**Status:** ❌ NOT FIXED

---

### 4. ✅ Shopkeeper Damage (INTENTIONAL - NO FIX NEEDED)

Shopkeepers have `1d1+30000` damage. This is **intentional** godmode to prevent players from killing shops. This is standard CircleMUD behavior and should NOT be changed.

---

## What's Working Well

### ✅ Spell Damage Balance
Spells have reasonable damage scaling:
- Magic Missile: `1d4+1` + 1/level
- Fireball: `3d6+5` + 3/level
- Harm: `5d8` (flat)

### ✅ Critical Hit System
- Base 5% + DEX bonus + level bonus
- Class bonuses (Thief +10%, Warrior +5%)
- Crit multiplier 2.0x (2.5x for Thief)

### ✅ EXP Scaling by Level Difference
The exp_mult system properly scales exp based on killer/victim level difference:
- +5 levels: +50% exp (challenging)
- Same level: 100%
- -5 to -7 levels: 25%
- -8 or more: 10% (gray mob)

### ✅ Stance System
Warrior stances properly modify damage/defense:
- Berserk: +25% damage, worse AC
- Defensive: -25% damage, better AC
- Precision: -10% damage, +15% crit, +4 hitroll

### ✅ Pet Combat
Pet attacks use reasonable damage dice directly from pet definition.

### ✅ Poison System
Envenom and poison effects are balanced with charges and duration.

---

## Recommended Fixes (Priority Order)

### Priority 1: Apply Mob Balance Fix
```bash
cd /Users/michaeltravis/clawd/projects/Misthollow
python3 scripts/fix_mob_balance.py --apply
```

### Priority 2: Fix Defense Formula
In `src/combat.py`, change:
```python
# Line 176, 515, 556
defense = 10 + (defender.get_armor_class() // 10)
```
To:
```python
defense = 10 - (defender.get_armor_class() // 10)
```

### Priority 3: Verify HP Values
Many mobs have low HP for their level. The fix script includes HP fixes but these should be verified for feel.

---

## Testing Checklist

After fixes are applied:
- [ ] Level 1 player can kill level 1-3 mobs in 3-5 hits
- [ ] Level 1 player survives 2-3 hits from level 1 mob
- [ ] Level 10 player gets meaningful exp from level 8-12 mobs
- [ ] Level 10 player gets reduced exp from level 5 mobs
- [ ] Better armor (lower AC) is harder to hit
- [ ] Shopkeepers remain invincible
- [ ] Boss fights take 30-60 seconds, not 2 seconds

---

## Appendix: Zones Requiring Fixes

| Zone | File | Mobs | Est. Broken |
|------|------|------|-------------|
| 025 | zone_025.json | 50+ | 90%+ |
| 030 | zone_030.json | 60+ | 70%+ |
| 050 | zone_050.json | 40+ | 90%+ |
| 051 | zone_051.json | 30+ | 90%+ |
| etc. | ... | ... | ... |

Run `python3 scripts/fix_mob_balance.py -v` for full breakdown.
