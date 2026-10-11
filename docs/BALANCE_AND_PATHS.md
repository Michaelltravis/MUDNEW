# Misthollow: Class Balance & The Path System

*Audit of all 9 classes (170 abilities), the solo/group design, and the
respec economy. Companion to the Path system in `src/paths.py`.*

## The Two Paths

| | 🐺 Lone Wolf | 🤝 Fellowship |
|---|---|---|
| Active when | **Ungrouped** only | **Grouped** only |
| Damage reduction | 8% +2%/10 levels (cap 20%) | — |
| Lifesteal on hits | 4% +2%/15 levels (cap 12%) | — |
| Consumable mastery | Every potion +8% max HP/mana | — |
| Bonus XP | — | +15% (on top of the +10%/member group bonus) |
| Coordinated strikes | — | +10% damage when a groupmate fights your target |
| The cost | Grants **nothing** in a group | Grants **nothing** alone |

- First choice free: `path lone_wolf` / `path fellowship` (or the TALENTS panel).
- Switching paths or resetting talents requires the **Trial of Unlearning**.

### Why this solves "solo anything"
The Lone Wolf kit is sustain, not damage: kill speed stays group-favored,
but a stocked, patient wolf can outlast anything. At 60 with capped DR
(20%), lifesteal (12%), potion mastery, and the right spec (defensive
stance + sustain talents), every boss becomes an endurance puzzle —
exactly "consumables and strategy." Groups still clear faster and
cheaper, and Fellowship's coordinated strikes + XP make grouping a real
build rather than a default.

## Trial of Unlearning (respec quest, repeatable, scales by bracket)
Giver: **Sage Aldric** (Temple of Midgaard, mob 3200).

| Bracket | Quest | Pilgrimage |
|---|---|---|
| 1–19 | Novice | Reflect at the temple altar |
| 20–39 | Adept | Altar + both city gates |
| 40+ | Master | Altar + the Dragon's Domain mountain pass |

Completion resets all talents (points refunded) and unlocks one path
switch. The cost is time and danger, scaling naturally with level.

## Class audit (chassis + solo/group temperament)

| Class | HP die | Abilities | Solo temperament | Group role |
|---|---|---|---|---|
| Warrior | d12 | 16 sk | Best raw chassis; momentum + doctrines reward long solo fights. Berserker doctrine = natural wolf. | Tank/DPS anchor |
| Paladin | d10 | 12 sk + 13 sp | Self-heals + plate = strongest innate soloer even before Lone Wolf | Off-tank, group shields (aegis, divine protection) |
| Ranger | d10 | 12 sk + 7 sp | Pet (tame) + cure light + range = excellent wolf | Sustained DPS, track utility |
| Cleric | d8 | 6 sk + 33 sp | Slow kills but unkillable; sanctuary+heal loop | THE group multiplier (group heal, mass buffs) |
| Assassin | d8 | 15 sk | Burst + evasion; weak sustain — Lone Wolf lifesteal patches their exact hole | Burst windows, marks |
| Thief | d6 | 15 sk | Fragile; relies on evasion/tricks. LW DR makes them viable | Utility (locks, traps, steal) |
| Bard | d6 | 11 sk + 18 sp | Charm/sleep control soloing; thin chassis | Song auras are inherently group-shaped |
| Necromancer | d4 | 4 sk + 20 sp | Pets tank + drains heal: design-intent soloer | Debuff engine (weaken, blindness, fear) |
| Mage | d4 | 5 sk + 32 sp | Glass cannon: nukes + control, dies in two hits. LW DR helps; still the hardest wolf | Highest burst, CC (sleep, slow) |

### Balance findings & recommendations
1. **No class is broken** — the chassis spread (d4–d12) is compensated
   by spell breadth, and the DB/PB defense system caps per-source
   contributions sensibly. No numeric nerfs recommended this pass.
2. **Mage/thief fragility** was the biggest solo blocker; Lone Wolf DR
   (multiplicative, post-mitigation) addresses it without touching
   class numbers.
3. **Warrior momentum already scales +5% damage/point** — pairing it
   with LW lifesteal is intentionally strong solo; the group cost
   (nothing in groups) is its governor.
4. **Cleric/bard group gravity** is correct: their kits ARE the group
   benefit. Fellowship XP makes bringing them rewarding for everyone.
5. **Watchpoint**: LW lifesteal + necromancer drains stack two sustain
   loops; if wolves trivialize mid-tier bosses, drop LW lifesteal to
   3%+1.5%/15 for drain-class casters before touching anything else.

## Tuning levers (in one place)
- `paths.py`: DR/lifesteal/potion/XP/coordination constants.
- `config.py`: STANCE_MODIFIERS, EXP multipliers, class dice.
- `warrior_abilities.py`: ABILITY_BASE_MULT per warrior skill.
- `talents.py`: per-talent effect magnitudes.
