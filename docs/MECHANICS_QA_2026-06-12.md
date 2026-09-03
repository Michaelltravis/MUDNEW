# Mechanics QA — June 12, 2026

*Automated sweep of all 219 class abilities (123 spells, 96 skills) across
all 9 classes, plus every talent in all 24 trees. Harness:
`tools/test_abilities.py` (boots the world in-process, fires every ability
at a training dummy, classifies exceptions / silent no-ops / refusals).*

## Final state
| Status | Count | Meaning |
|---|---|---|
| OK | 161 | ability fired with correct output |
| PASSIVE | 26 | engine-driven (parry, second_attack…), no command expected |
| REFUSED | 32 | correct gating: class resources, stealth-only openers, usage prompts |
| EXC / SILENT / unknown-affect | **0** | — |

## Bugs found & fixed
1. **teleport** crashed (`UnboundLocalError: random`) — an inner `import
   random` in the special-spell handler shadowed the module import.
2. **identify / enchant weapon** crashed when cast without an item —
   object-target spells with no target now get "Cast it on what?".
3. **create food / create water** crashed (`ImportError: GameObject`) —
   rebuilt on the current `Object` API; both conjure real items again.
4. **bard `mockery` / assassin `poison`** were unreachable — implementations
   existed as `cmd_mock` / `cmd_envenom`; aliased, and envenom now accepts
   the assassin's `poison` skill.
5. **corpse explosion** crashed when it hit mobs, and kills it caused never
   triggered death handling. Both fixed.
6. **9 affect types did nothing** (silently weakened spells): `crit_chance`,
   `spell_power`, `heal_power`, `mana_regen`, `silenced`, `plague`,
   `all_stats`, `spirit_link`, `damage_redirect_pet`, plus `fire_crit` and
   `regenerating`. All implemented end-to-end:
   - crit riders join the combat crit roll (cap raised to 85 for riders)
   - spell/heal power riders join the existing equipment-bonus math
   - mana_regen multiplies the regen tick (Hymn of Hope doubles it)
   - silenced characters cannot cast ("the discordant silence swallows the words")
   - plague is a real DOT + diseased marker
   - **Spirit Link**: linked groupmates absorb 30% of each other's damage
     (the link never kills)
   - **Corpse Shield**: the necromancer's pet eats 50% of incoming damage
     and can be torn apart doing it

## Talent trees (all 24 audited)
- **Talent-granted spells were uncastable**: `learn_talent` put spell
  unlocks in `player.skills`, but casting reads `player.spells` — every
  pyroblast/ice-lance-style reward was dead on arrival. Fixed; respec now
  also revokes unlocked abilities.
- One structural bug (paladin Protection key/id mismatch) fixed.
- **20 orphaned spells wired in as new talents** (were implemented but
  unreachable): mage Frost gets Ice Barrier + Cold Snap, Arcane gets
  Arcane Missiles + Mana Rift; the necromancer Unholy tree becomes a true
  corpse economy (Curse → Festering Strike → Corpse Explosion → Mass
  Animate → Raise Abomination), Blood gets Dark Mending / Blood Boil /
  Death Pact / Siphon Unlife, Frost gets Death Strike + Remorseless
  Winter; paladin Holy capstone Lay on Hands; cleric Dispel Magic + Void
  Eruption; bard Anthem of Defense + Discordant Chord.
  *(Left dormant as duplicates/utility: apocalypse, lay_hands, block_door,
  break_door.)*
- **14 dead capstone unlocks** granted abilities nothing implemented.
  5 retargeted to real implementations (mesmerize, identify, mirror image,
  shadow step — gate relaxed for talent-trained thieves — camouflage);
  9 implemented as proper spells: Phoenix Flames, Renew, Inner Focus,
  Wound Poison, Polymorph (sheep!), Divine Favor, Dark Transformation,
  Breath of Sindragosa, Grand Illusion.
- Verified end-to-end: every wired talent learns, grants, and casts.

## Combat identity per class (the "unique and fun" audit)
The server already runs **eight distinct combat resources** — they were
just invisible outside the terminal:
| Class | Resource | Builds from |
|---|---|---|
| Warrior | Momentum ×10 | landing skill chains |
| Thief | Luck 0–10 | crits and dodges |
| Assassin | Intel 0–10 | marking and studying the target |
| Cleric | Faith 0–10 | healing (or dealing damage in shadow form) |
| Paladin | Holy Power 0–5 | righteous strikes |
| Ranger | Focus 0–100 | every hit, more on marked prey |
| Necromancer | Soul Shards 0–10 | hits (15%) and kills |
| Bard | Inspiration 0–10 | performing in combat (33% per hit) |

The client now ships the class resource in every map/combat payload and
renders it as a pip meter in the dock (🕯 FAITH ●●●●●●○○○○), replacing the
warrior-only momentum chip. Builders verified live: focus/holy
power/shards/inspiration rise through real combat rounds and their
spenders fire (Kill Command, Templar's Verdict…).
