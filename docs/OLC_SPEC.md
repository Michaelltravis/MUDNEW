# RealmsMUD OLC Spec (OasisOLC‑style)

## Goals
- Provide in‑game, menu‑driven world building that mirrors CircleMUD’s OasisOLC
- Preserve RealmsMUD JSON file format for rooms/mobs/objects/zones
- Enforce building rules from the OasisOLC handbook

## Building Rules (Enforced Guidance)
- Balance mobs vs gear; add tradeoffs to powerful gear.
- Room descriptions **3+ lines**, proper grammar/punctuation.
- Avoid naming specific mobs or their equipped items in room descs.
- Avoid directional phrasing (“behind you”, “to your right”).
- Keep lines ~65–75 chars for non‑wrapping clients.
- Spell out numbers when reasonable.
- Doors/exits must be defined on both sides when locked/closed.
- Hidden exits require search discovery; avoid unreachable rooms.

## Permissions & Safety
- OLC restricted to builder/admin roles.
- Each builder assigned zones (by zone number).
- Edits tracked; `save` required to write JSON files.
- “Internal” save vs “disk” save, matching Oasis behavior.

---

# Core OLC Commands

## Global
- `olc` (shows active editor and help)
- `save <zone>` (write JSON files)
- `zlist`, `rlist`, `mlist`, `olist` (list vnums)
- `olc status` (locks, current editors)

## Room Editor — `redit`
Usage:
- `redit` (edit current room)
- `redit <vnum>` (edit specific room)

Menu fields:
1. Name
2. Description (multi‑line, terminated by `@`)
3. Flags (dark, indoors, peaceful, deathtrap, etc.)
4. Sector type
5–A. Exits (north/east/south/west/up/down)
B. Extra descriptions (keyword → description)
Q. Quit (save internal?)

Exit editor:
- To room (vnum)
- Description
- Door name
- Door state (open/closed/locked)
- Key vnum (optional)
- Hidden/secret + search difficulty
- Purge exit

## Mob Editor — `medit`
Usage:
- `medit <vnum>`

Menu fields:
- Name / short / long / description
- Level / hp dice / damage dice / AC
- Gold / exp / alignment
- Flags (aggressive, sentinel, helper, etc.)
- Affects (detect, invis, sanctuary, etc.)
- Loot table / boss metadata

## Object Editor — `oedit`
Usage:
- `oedit <vnum>`

Menu fields:
- Name / short / room desc / long desc
- Item type
- Wear slot
- Weight / value
- Flags
- Affects (stat bonuses, skill/spell affixes)
- Extra descriptions
- Container fields (capacity, flags, key)

## Zone Editor — `zedit`
Usage:
- `zedit` (current room)
- `zedit <zone>`

Zone commands:
- M: Load mob
- O: Load object to room
- G/E: Load object to mob (equip/hold)
- D: Door state (open/close/lock)
- R: Remove object from room (prevent buildup)
- W: Set room/zone weather (optional)

Notes:
- Door lock state set **both sides**.
- Equipment placed after mob load and set “dependent”.

---

# Data Model Mapping (RealmsMUD JSON)

## Rooms (`world/zones/zone_XXX.json` → rooms)
- `name`, `description`, `sector_type`, `flags`
- `exits` map: to_room, description, door state, key_vnum, hidden/secret
- `extra_descs`

## Mobs (`world/zones/zone_XXX.json` → mobs)
- `name`, `short_desc`, `long_desc`, `description`
- `level`, `hp_dice`, `damage_dice`, `armor_class`
- `flags`, `affects`, `alignment`, `gold`, `exp`
- `loot_table`, `boss_*`

## Objects (`world/zones/zone_XXX.json` → objects)
- `name`, `short_desc`, `room_desc`, `description`
- `item_type`, `wear_slot`, `weight`, `value`
- `flags`, `affects`, `damage_dice` (weapons)
- `capacity`, `container_flags`, `key_vnum`

## Zone resets (future)
- Optional top‑level `resets` section OR current room‑based `mob_resets` / `obj_resets`.

---

# Implementation Plan

**Phase 1 — MVP OLC (Rooms only)**
1) `redit` command with menu flow
2) Load/save to zone JSON (in‑memory + disk)
3) Extra desc editor
4) Exit editor incl. doors

**Phase 2 — Mobs & Objects**
1) `medit`, `oedit` menus
2) Validate fields and ranges
3) Write to zone JSON

**Phase 3 — Zone Editor**
1) `zedit` with load commands
2) Sync to `mob_resets` / `obj_resets`
3) Door lock state helper

**Phase 4 — Admin / Workflow**
1) Permissions + zone ownership
2) OLC lock system
3) `save` + backups

---

# Implementation Status

## Completed ✅
- [x] `redit` - Full room editor with exits, doors, extra descs
- [x] `medit` - Full mob editor with stats, flags, boss setup
- [x] `oedit` - Full object editor with types, affects, wear slots
- [x] `save <zone>` - Write zone JSON to disk
- [x] Room `to_dict()` preserves full exit data
- [x] OLC state machine with menu-driven input

## Pending
- [ ] `zedit` - Zone reset editor
- [ ] Permissions/zone ownership system
- [ ] OLC lock system (prevent concurrent edits)
- [ ] Backup before save

# Checklist (Handbook‑aligned) - ALL COMPLETE ✅
- [x] Room desc ≥ 3 lines, 65–75 chars (40 zones audited)
- [x] No mob‑specific room descs
- [x] No gear references in mob descs
- [x] Doors defined both sides
- [x] Gear has tradeoffs or balanced power
- [x] Zone balance pass
