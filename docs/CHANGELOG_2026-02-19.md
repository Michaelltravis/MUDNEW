# Changelog — 2026-02-19

## MUME Adoption Batch A (Combat Core)

### Added
- **Stance system:** `stance` command with aggressive/normal/defensive tradeoffs applied to hit/damage/AC.
- **Escape toolkit:** `escape` (directed), `disengage` (non-primary target), and `flee` (panic/random) now separated with clear messaging and cooldowns.
- **Second Wind:** `secondwind` restores movement points with a short regen surge; costs mana for casters, HP for martial classes.
- **Tactical telemetry:** `tactical` command provides a concise combat stat line (OB/DB/PB, stance, mitigation, wimpy, flee risk).

### Improved
- **Wimpy auto-flee:** wimpy threshold now triggers auto-flee attempts during combat.
- **Movement economy:** combat rounds and escape actions now consume movement points; winded penalties apply when movement is depleted.

### Balancing Notes & Defaults
- Stance modifiers: Aggressive (+3 hit/+3 dam/+10 AC), Defensive (-2 hit/-2 dam/-10 AC), Normal (0/0/0).
- Combat move drain: 1 move per combat round; winded penalty at 0 move (hit -2, damage -10%).
- Escape costs: flee 10 move (random), escape 12 move (directed), disengage 6 move.
- Cooldowns: flee 6s, escape 8s, disengage 6s.
- Second Wind: restores 25% max move, 60s cooldown, 30s +50% move regen surge.
- Wimpy default remains off (0).

---

## MUME Adoption Batch B (Spells & Skills Interaction)

### Added
- **Armour ward absorb:** `armor` now grants a depleting absorb pool that scales with caster level and spell proficiency, then fades with duration.
- **Shield evasion boost:** shield-style effects now add dodge/evasion bonuses and surface in `tactical` telemetry.
- **Briskness:** new ranger mobility spell restores movement immediately and grants a short regen surge.
- **Stat-linked skill bonuses:** key skills now add a small bonus from their primary stat (e.g., DEX for dodge/evasion, STR for bash).

### Improved
- Absorption wards now mitigate physical damage plus selected magical categories.
- Heavy armor reduces absorb effectiveness for ward-style buffs.
- Tactical output now includes shield evasion bonuses when active.

### Balancing Notes & Defaults
- Armour ward base: 60 absorb on `armor`.
- Absorb scaling: +4 per caster level; +50% of base at 100% proficiency.
- Prime stat bonus: +2 absorb per point above 10 in the class prime stat.
- Armor penalty: softcap 20 total armor weight; -2% absorb per weight over softcap, up to 40%.
- Shield evasion bonuses: shielded +4%, holy/divine shield +6%, aegis ward +4%.
- Briskness: +20% max move instant restore, +35% move regen for 18 ticks; +20% instant restore in wilderness.
- Skill stat bonus: (stat-10)//2 for dodge/evasion/parry, bash/kick/cleave/charge/execute, backstab/sneak/hide, track/tame.

---

## MUME Adoption Batch C (Group Combat Control & Telemetry)

### Added
- **Protect command:** warriors/paladins can guard an ally and intercept attacks based on rescue/shield skill and STR/CON.
- **Assist polish:** assist now joins a fight without automatically stealing aggro.
- **Protection telemetry:** `tactical` now surfaces protect/guard status alongside escape/disengage readiness.

### Improved
- **Rescue scaling:** rescue success now scales with rescue skill, STR/DEX, and stance, with clear attacker messaging.
- **Consider readout:** now includes stance, movement state (winded/steady), and key defense layers (parry/dodge/block/mitigation).
- **Escape clarity:** flee/escape/disengage cooldowns now report remaining seconds and consistent risk messaging.

### Balancing Notes & Defaults
- Rescue cooldown: 6s.
- Protect intercept cooldown: 4s.
- Protect intercept chance: based on rescue or shield block skill + STR/CON (defensive stance bonus, winded penalty).
- Escape/flee risk labels standardized (low/medium/high) across panic vs controlled exits.

---

## MUME Adoption Batch D (Polish & Validation)

### Added
- **Protect progression hook:** successful intercepts can improve rescue or shield block skill.

### Improved
- **Protect edge cases:** linkdead protectors are ignored/cleared; pet intercepts now respect cooldowns.
- **Multiple protectors messaging:** protect command now notes when someone is already guarding the target.
- **Rescue progression:** successful rescues can improve rescue skill.
- **Failed rescue visibility:** ally + attacker now receive concise feedback when a rescue attempt fails.

### Validation
- Ran `python3 -m py_compile` on all `src/*.py`.

---

## MUME Adoption Batch E (QA/Balancing)

### Improved
- Escape/flee/disengage now only spend movement when the attempt is actually viable (valid exits/targets, no forced focus).
- Default stance initialization aligned to `normal` for new characters to match stance system output.

---

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

---

## Overnight Recap (Batch D)
- **Commits:** HEAD (see git log)
- **Files touched:**
  - `src/player.py`
  - `src/commands.py`
  - `src/help_data.py`
  - `docs/CHANGELOG_2026-02-19.md`
- **Notes:** protect/rescue progression hooks added; intercept edge cases tightened; pet protect cooldown now honored.
- **Recommended next steps:**
  - Consider a lightweight log line for failed rescue attempts if players want more feedback.
  - Review protect/progression tuning once live combat logs are available.

---

## MUME Mapping Sheet (Design/Tuning)

### Added
- New design document: `docs/MUME_TO_MISTHOLLOW_COMBAT_MAPPING.md`
- Captures MUME -> Misthollow mapping for:
  - OB/DB/PB telemetry model
  - stance (mood) tradeoffs
  - shield + armor-weight DB/PB behavior
  - stat interactions (STR/DEX/CON/INT/WIS/WIL/PER)
  - flee/escape/disengage identity
  - movement economy and group-control triangle

### Next Pass Targets
- Normalize DB/PB source caps and contribution ceilings.
- Increase explicit WIL impact on escape stability/panic resistance.
- Add concise `help tactical` formula summary for player transparency.

## MUME Numeric Tuning Pass 1

### Tuned
- **Escape stability (WIL):** flee/escape now include capped willpower composure bonus; high-WIL builds panic less.
- **Cooldown composure:** WIL slightly reduces flee/escape/disengage cooldowns (small capped effect).
- **DB/PB source caps:** shield/stance/skill/item contributions now have explicit ceilings to prevent single-source dominance.
- **Weight penalties:** DB/PB weight penalties are capped for predictable scaling.
- **Help clarity:** `help tactical` now includes concise OB/DB/PB and escape/flee formula summary.

## MUME Numeric Tuning Pass 2 (Live Calibration)

### Tuned
- **Stance spread increased:** aggressive now pushes OB harder with clearer DB/PB downside; defensive now gives stronger PB/DB with lower OB.
- **DB/PB caps moved to config constants:** source ceilings are now centralized and tunable without code edits.
- **Calibration target:** make stance choice materially visible in hit pressure vs mitigation for endgame fights.

### Config knobs added
- `DB_CAP_SHIELD_MAGIC`, `DB_CAP_DODGE_SKILL`, `DB_CAP_DODGE_ITEM`, `DB_CAP_STANCE`, `DB_CAP_WEIGHT_PENALTY`
- `PB_CAP_STANCE`, `PB_CAP_PARRY`, `PB_CAP_SHIELD_BLOCK`, `PB_CAP_WEIGHT_PENALTY`
