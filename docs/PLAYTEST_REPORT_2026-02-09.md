# Playtest Report — February 9-10, 2026

## Test Environment
- Server: localhost:4000 (telnet), :4001 (web map), :4003 (web client)
- Test accounts: Deckard (immortal, lv60 warrior), fresh characters (Ramfour/Ramfive)
- All tests run via piped nc commands

---

## Test Results

### 1. Character Creation — ✅ PASS
- Account creation works (bug fixed during session)
- Race/class selection accepts both numbers and names
- Starter equipment correct: short sword, chainmail, helmet, greaves, shield, bread, waterskin, torch
- Tutorial auto-starts, Sage Aldric greets, quest accepted

### 2. Tutorial Flow — ✅ PASS
- `hint` command shows current objective with directions
- `talk aldric` completes step 1, auto-advances to step 2
- No quest dump (filtered to current step only)
- Single completion banner (no duplicates)
- Compass hint "You sense your objective lies to the north" works in Temple Square
- Item rewards given (healing potion on step 1 completion)

### 3. Shops — ⚠️ PARTIAL PASS
- **Pet Shop (3031) `list`**: ✅ Shows pets with prices, levels
- **Pet Shop (3031) `buy sword`**: ✅ Correctly says it's a pet shop, shows available pets
- **Weapon/Armor shops**: NOT TESTED (Deckard's `goto 3031` landed in pet shop)
- **Issue**: Need to test actual weapon/armor shops via correct room numbers

### 4. Pet Store — ⚠️ PARTIAL PASS
- **Room 3031 (Pet Shop)**: Shows 5 pets (kitten 150g, puppy 186g, beagle 300g, rottweiler 1200g, wolf 60g)
- **Room 3032 (Pet Shop Store)**: Shows the physical pet mobs correctly
- **🔴 BUG (Major)**: Room 3032 `list` shows WRONG pets — "the wizard (Lv33, 285000g)", "the Peacekeeper (Lv17)", "green gelatinous blob (Lv20)". These are non-pet mobs leaking into the pet shop listing.
- **🔴 BUG (Major)**: The 7 new pets from the shop stocking task (tabby cat, raven, green snake, hawk, war dog, bear, dire wolf) are NOT showing in the pet list. Only the original 5 pets appear.
- **Wolf pricing**: 60 gold seems too cheap for a level 4 pet (beagle costs 300g at level 2)

### 5. Rent System — ✅ PASS
- `rent cost` shows proper breakdown: base 50g/day + inventory 30g/day + equipment 10g/day = 90g/day
- Receptionist is in room 3008
- Pricing feels reasonable

### 6. ATM/Object Duplication — 🔴 CRITICAL BUG
- **Room 3001 (Temple)**: Shows "An automatic teller machine has been installed in the wall here." **10 TIMES**
- **Room 3008 (Reception)**: Shows ATM **10 TIMES**
- This is an obj_reset duplication bug — the ATM object is being spawned multiple times per zone reset
- Also: "The corpse of Deckard lies here" in the Temple — corpses should decay

### 7. Mail System — ⚠️ PARTIAL PASS
- `mail send Avikan Testing mail system` → "Mail sent to Avikan." ✅
- `mail list` → "Your mailbox is empty." ✅ (sent TO Avikan, not FROM — correct)
- Need to test receiving mail (login as Avikan)

### 8. Trade/Duel Commands — ✅ PASS
- `trade` → Shows proper syntax: "trade <player> | trade offer <item> | trade accept | trade cancel"
- `duel` → Shows proper syntax: "duel <player> [gold wager] | duel accept"

### 9. Faction/Reputation — ✅ PASS
- `reputation` command works, shows all 9 factions with proper starting values
- Midgaard: Neutral (0), Drow Conclave: Hostile (-300), Holy Order: Friendly (300), etc.
- Starting values match the faction definitions

### 10. Time/Weather — ✅ PASS
- `time` → "It is early morning (8:25). Day 11 of Early Summer, year 1000." ✅
- `weather` → Formatted display with temp (75°F), wind (calm 7mph), season ✅

### 11. Combat — ⚠️ PARTIAL (Accidental)
- Nyk (lv10) logged in at Mindflayer's Sanctum and got attacked immediately
- Mind flayer does 9-10 damage per hit — seems reasonable for a level 10 in a level 15+ zone
- Player was low HP (21/163) on login — hunger/thirst draining HP
- **🟡 Issue (Minor)**: "You are starving to death! You are dying of thirst!" — player took hunger/thirst damage. Need to verify food/drink is accessible.

### 12. Boss Phases — NOT TESTED
- Visited Scorathax's room but didn't initiate combat (would need to fight to see phases)
- Scorathax is present with proper description: "A colossal red dragon coils atop a mountain of gold"

### 13. Locked Doors/Containers — NOT TESTED
- Didn't test opening locked chests or doors this session
- Need a dedicated test with keys and pick lock attempts

### 14. Web Client — ✅ PASS
- `curl localhost:4003` returns proper HTML with `<!DOCTYPE html>` — web client is serving

### 15. Server Log — ⚠️ ISSUES FOUND
- **`cmd_use` missing**: `AttributeError: type object 'CommandHandler' has no attribute 'cmd_use'` — the `use` command doesn't exist but players try to use potions with it
- **Connection lost errors**: Multiple "Error sending to... Connection lost" — these are from piped test scripts disconnecting, not real bugs
- **ConnectionResetError**: Same — test script artifacts

---

## Bug Summary

| # | Severity | Issue | Details |
|---|----------|-------|---------|
| 1 | 🔴 Critical | ATM object duplication | ATM spawns 10x in rooms 3001, 3008. Likely obj_reset running every zone tick without max check |
| 2 | 🔴 Major | Pet shop shows wrong mobs | Room 3032 lists wizard, Peacekeeper, blob as purchasable pets |
| 3 | 🔴 Major | New pets missing | 7 new pets (cat, raven, snake, hawk, war dog, bear, wolf) not in shop |
| 4 | 🟡 Major | `cmd_use` missing | Players can't `use` potions — need alias to `quaff` |
| 5 | 🟡 Minor | Corpse decay | Deckard's corpse still in Temple — may not be decaying |
| 6 | 🟡 Minor | Hunger/thirst damage | Players take damage from hunger/thirst with no obvious fix nearby |
| 7 | 🟡 Minor | Wolf pet pricing | 60g for lv4 wolf vs 300g for lv2 beagle — inconsistent |

## Recommendations

1. **Fix ATM duplication immediately** — likely needs `max_existing: 1` on the obj_reset or dedup logic
2. **Fix pet shop room detection** — room 3032 is flagging non-pet mobs as purchasable
3. **Add `cmd_use` as alias for `quaff`** — very common MUD command
4. **Verify corpse decay timer** — should be ~5 minutes
5. **Test locked doors and boss phases** in next session
6. **Stock the 7 new pets** properly in the pet shop room
