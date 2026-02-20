# Changelog — 2026-02-19

## MUME Adoption Batch A

### Added
- Guided tutorial step prompts for tutorial quests, including one-time contextual hints for movement, inventory, wielding, and quest acceptance.
- Tutorial hint cadence integrated into movement, inventory, and wield flows (non-intrusive, one-time).

### Improved
- Quest journal: lookup by area or name/ID ("quests <area>" and "quests <name>") with concise summaries.
- Consider output: clearer threat messaging plus tactical OB/DB/PB-style quick readout.
- Score output: added OB/DB/PB tactical line for readability.

---

## Batch 1 — Endgame Content (Misthollow)

### Added: The Ashen Expanse (Zone 280, Level 58–62)
- New endgame zone (36 rooms) branching east from **Ashlands (room 6909)**.
- Theme: scorched badlands of ash, obsidian, and ember storms.
- Mobs: ash wraiths, cinder marauders, obsidian golems, furnace sentinels, magma reavers.
- Minibosses: **Cinder Warden Kael**, **The Scoria Matron** (loot tables for class upgrades).
- Final boss: **The Ember Sovereign** (boss loot table; no ground placement).
- Loot highlights:
  - **Cinderbrand Greatsword** (warrior)
  - **Emberguard Bulwark** (cleric/paladin)
  - **Pyreweave Robe** (mage)
  - **Ashen Stalker Dagger** (assassin/thief)
  - **Smoldering Longbow** (ranger)
  - **Cinderwind Lyre** (bard)
  - **Crown of the Ember Sovereign**, **Heartstone of the Expanse**

### Added: The Drowned Reliquary (Zone 285, Level 60–64)
- New endgame underwater zone (36 rooms) branching east from **Sunken Temple (room 24024)**.
- Theme: drowned temple reliquary, coral halls, abyssal catacombs.
- Zone mechanic: **drowning timer** at entry (water breathing required).
- Mobs: drowned acolytes, reliquary guardians, barnacle knights, abyssal cantors.
- Minibosses: **Reliquary Abbot**, **Drowned Sanctifier** (loot tables for class upgrades).
- Final boss: **The Thalassine Lich** (boss loot table; no ground placement).
- Loot highlights:
  - **Tideworn Mace** (cleric/paladin)
  - **Reliquary Scepter** / **Lichwarden Staff** (necromancer/mage)
  - **Abyssal Mantle** (mage)
  - **Barnacle-etched Greaves** (warrior)
  - **Coral-thread Cloak** (ranger)
  - **Siltshadow Stiletto** (assassin/thief)
  - **Hymnkeeper's Chord** (bard)
  - **Drowned Soulstone** (necromancer)

### Connections & Integrity
- Added new zone exits:
  - Ashlands 6909 → Ashen Expanse 28000
  - Sunken Temple 24024 → Drowned Reliquary 28500
- Boss loot handled via boss loot tables (no ground spawns).

---

## Batch 1 Summary
- **Rooms:** 72 (Ashen Expanse 36, Drowned Reliquary 36)
- **Mobs:** 24 total (including 4 minibosses)
- **Bosses:** 2
- **Loot Items:** 19
- **Key Mechanics:** Underwater drowning timer in Drowned Reliquary entry; no-recall boss chambers; endgame AI flags (aggressive, sentinel, no_charm/no_sleep)

---

## Batch 2 — Endgame Content (Misthollow)

### Added: The Black Observatory (Zone 290, Level 62–66)
- New endgame observatory zone (36 rooms) branching east from **Ashen Expanse (room 28035)**.
- Theme: obsidian skywatch, voidglass halls, star-metal instruments, astral engines.
- Mobs: starbound acolytes, obsidian lens-keepers, voidglass sentinels, gravitic wisps, nightglass stalkers, umbral astrologers, astral constructs.
- Minibosses: **Curator Nyx**, **The Voidglass Warden** (loot tables for class upgrades).
- Final boss: **The Eclipse Regent** (boss loot table; no ground placement).
- Loot highlights:
  - **Starforged Glaive** (warrior/paladin)
  - **Nebulae Longbow** (ranger)
  - **Nightglass Stiletto** (assassin/thief)
  - **Lyre of Orbits** (bard)
  - **Astral Seer's Diadem** (mage/cleric)
  - **Voidglass Aegis**, **Eventide Mantle**, **Crown of the Black Observatory**, **Regent's Starblade**

### Added: Crown of Bone (Zone 295, Level 64–68)
- New endgame ossuary zone (36 rooms) branching east from **Drowned Reliquary (room 28535)**.
- Theme: bone-crowned catacombs, ribbed halls, ossuary bridges, marrow altars.
- Mobs: bone thralls, ossuary archers, marrow priests, gravebound juggernauts, spine reavers, sepulcher wraiths, ribcage sentinels.
- Minibosses: **The Charnel Choir Vicar**, **The Ossuary Harvester** (loot tables for class upgrades).
- Final boss: **The Bone-Crowned Sovereign** (boss loot table; no ground placement).
- Loot highlights:
  - **Gravewind Greatsword** (warrior)
  - **Ossuary Bulwark** (cleric/paladin)
  - **Skullcaller Wand** (mage/necromancer)
  - **Rattlebind Longbow** (ranger)
  - **Marrowcarver Stiletto** (assassin/thief)
  - **Cadaverous Lute** (bard)
  - **Boneweft Cowl**, **Gravebinder Mail**, **Crown of the Ossuary**, **Sovereign's Boneblade**

### Connections & Integrity
- Added new zone exits:
  - Ashen Expanse 28035 → Black Observatory 29000
  - Drowned Reliquary 28535 → Crown of Bone 29500
- Boss loot handled via boss loot tables (no ground spawns).

---

## Batch 2 Summary
- **Rooms:** 72 (Black Observatory 36, Crown of Bone 36)
- **Mobs:** 20 total (including 4 minibosses)
- **Minibosses:** 4
- **Bosses:** 2
- **Loot Items:** 20
- **Notable Mechanics:** No-recall boss chambers; endgame AI flags (aggressive, sentinel, no_charm/no_sleep); deep-chain progression from Batch 1 endgame zones

---

## Batch 3 — Endgame Content (Misthollow)

### Added: The Shattered Throne (Zone 300, Level 68–70+)
- New raid-tier fortress/throne complex (40 rooms) branching east from **Black Observatory (room 29035)** and **Crown of Bone (room 29535)**.
- Theme: fractured imperial fortress, reality tears, shattered throne sanctum.
- Mobs: imperial bulwarks (tank), rift arcanists (caster), throne confessors (healer), fractureblade stalkers (assassin), reality maulers, null-ward sentinels, riftbound cantors, riftwarden juggernauts.
- Minibosses: **Marshal Kyrell**, **Choir-Matron Serathis**, **Shatterblade Veyl** (class loot tables).
- Final boss: **The Shattered Emperor** (boss loot table; no ground placement).
- Loot highlights:
  - **Thronebreaker Greatsword** (warrior)
  - **Imperial Lumenblade** / **Aegis of the Fractured Oath** (paladin/cleric)
  - **Riftweaver Staff** (mage)
  - **Gravebound Scepter** (necromancer)
  - **Stormrend Longbow** (ranger)
  - **Veilripper Dirk** (thief)
  - **Voidglass Kris** (assassin)
  - **Hymn of Shattered Strings** (bard)
  - **Crown of the Shattered Throne**, **Imperial Fractureplate**, **Shard of the Shattered Throne**

### Connections & Integrity
- Added new zone exits:
  - Black Observatory 29035 → Shattered Throne 30000
  - Crown of Bone 29535 → Shattered Throne 30001
- Boss loot handled via boss loot tables (no ground spawns).

---

## Batch 3 Summary
- **Rooms:** 40
- **Mobs:** 12 total (including 3 minibosses)
- **Minibosses:** 3
- **Bosses:** 1
- **Loot Items:** 16
- **Notable Mechanics:** Dual-branch endgame convergence; no-recall sanctum and boss chamber; raid-tier archetype packs (tank/caster/healer/assassin)
