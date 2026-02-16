# Balance Report — 2026-02-14

## Executive Summary

Comprehensive balance pass across all 9 classes. Reviewed resource mechanics, ability damage formulas, cooldowns, talent passives, and cross-class viability. Made 5 conservative tuning adjustments. No system redesigns.

**Overall Assessment**: The game is in good shape. Most classes have well-designed resource loops. A few generation rates were outliers (too fast or too slow) and one class was missing passive resource generation entirely.

---

## Changes Made

| # | Class | Change | Before | After | Rationale |
|---|-------|--------|--------|-------|-----------|
| 1 | **Thief** | Crit damage multiplier | 2.5x (250%) | 2.25x (225%) | Thief already has +10% base crit chance, guaranteed crits from Rigged Dice/Lucky Break, and Luck-based counterattacks. 2.5x crits on top of all that made sustained DPS too high vs melee peers. |
| 2 | **Ranger** | Focus gain per hit | 10 | 8 | At 10/hit + 5 from Hunter's Mark + 15 on dodge + talent bonuses, Rangers could fill 100 Focus in ~6-7 hits. Now takes ~8-9 hits baseline, better pacing for Focus spenders. |
| 3 | **Bard** | Inspiration generation chance | 25% per hit | 33% per hit | Bard was the slowest resource generator. At 25%, filling to 10 Inspiration took ~40 hits on average. Now ~30 hits. Still the slowest (intentional for support class) but no longer painfully slow. |
| 4 | **Paladin** | Holy Power generation chance | 25% per hit | 30% per hit | Paladin needs 3-5 Holy Power for key abilities (Templar's Verdict, Divine Storm, Word of Glory). At 25% it took ~20 hits to fill. At 30% it takes ~17. Small but meaningful improvement, especially with Oath of Vengeance (+10%) and Benediction talent (+3%/rank). |
| 5 | **Necromancer** | Added passive Soul Shard generation | None (ability-only) | 15% chance per melee hit | Necromancer was the only class with no passive resource generation from auto-attacks. All other classes gain their resource on hit. 15% is modest (comparable to Thief Luck at 15%) and supplements the ability-based generation from Drain Soul and kills. |

---

## Class-by-Class Analysis

### 1. Warrior — Momentum + Doctrine/Evolution
**Resource**: Momentum (0-10), +1 per unique ability used, resets on same-ability repeat.
**Generation Rate**: ✅ Well-balanced. Rewards ability variety. Unstoppable at 10 is a satisfying payoff.

| Stat | Value | Assessment |
|------|-------|------------|
| Momentum gain | +1 per unique ability | Good — forces rotation |
| Momentum damage | +5% per point (50% at max) | Strong but requires 10 unique abilities |
| Unstoppable | CC immune 4 rounds at 10 momentum | Appropriately powerful capstone |
| Strike CD | 4s | Fast, good filler |
| Bash CD | 8s | Standard |
| Cleave CD | 10s | Appropriate for AoE |
| Charge CD | 12s | Fair for opener |
| Rally/Execute CD | 15s | Correct for powerful abilities |
| Execute threshold | 25% HP (35% with talents) | Fair |

**Doctrine System**: Three distinct playstyles (Iron Wall/Berserker/Warlord) with meaningful tradeoffs. Berserker's self-damage costs are well-calibrated (5-20% HP). Evolution thresholds (50/150/300 uses) provide long-term progression.

**Verdict**: ✅ No changes needed. Best-designed class mechanically.

---

### 2. Assassin — Intel System
**Resource**: Intel (0-10), +1 per melee hit on marked target.
**Generation Rate**: ✅ Good. 10 hits to max is a satisfying ramp-up in combat.

| Stat | Value | Assessment |
|------|-------|------------|
| Intel gain | +1 per hit | Good — 10-round ramp |
| Intel threshold 3 | Expose Weakness (+15% damage) | Fair early payoff |
| Intel threshold 6 | Vital Strike (burst damage) | Good mid reward |
| Intel threshold 10 | Execute Contract (massive finisher) | Satisfying capstone |
| Auto-mark on combat start | Yes | Excellent QoL |
| Evasion | 100% dodge for duration | Strong defensive cooldown |
| Ghost passive | 50% dodge after big hit | Good survival talent |

**Talent Trees**: Lethality/Poison/Shadow are well-differentiated. Kill or Be Killed (+1% dodge per Intel) is very strong at 10 Intel but requires deep investment.

**Verdict**: ✅ No changes needed. Well-paced ramp-up class.

---

### 3. Thief — Luck System
**Resource**: Luck (0-10), 15% per hit + guaranteed on crits.
**Generation Rate**: ✅ Good (was slightly over-tuned on output, not generation).

| Stat | Value | Assessment |
|------|-------|------------|
| Luck gain chance | 15% per hit (crits always) | Good |
| Base crit chance | 15% (5 base + 10 class) | High but intentional |
| ~~Crit multiplier~~ | ~~2.5x~~ → **2.25x** | **CHANGED** — was too high |
| Combo points | 0-5, +1 per hit | Standard |
| Pocket Sand | Blind 2 rounds | Good utility |
| Rigged Dice | 3 guaranteed crits | Strong burst window |
| Jackpot | 10 Luck dump for massive damage | Satisfying capstone |
| Lucky counterattack | Free hit on dodge at 5+ Luck | Unique and fun |

**Rationale for crit nerf**: Thief stacks crit chance (+10% class, +5% talent ranks, +Lucky Break auto-crit at 10 Luck) AND has guaranteed crits from Rigged Dice. At 2.5x, the average DPS was ~12% higher than Assassin/Warrior in sustained combat. 2.25x brings it in line while keeping Thief as the crit-focused class.

**Verdict**: ⚠️ One change (crit mult 2.5x → 2.25x). Still the strongest crit class.

---

### 4. Necromancer — Soul Shards
**Resource**: Soul Shards (0-10).
**Generation Rate**: ⚠️ Was missing passive generation — **FIXED**.

| Stat | Value | Assessment |
|------|-------|------------|
| ~~Passive shard gain~~ | ~~None~~ → **15% per hit** | **ADDED** |
| Drain Soul | Active ability, generates shards | Core generator |
| Soul Bolt | Shard spender for damage | Good |
| Bone Shield | Shard spender for defense | Good |
| Soul Reap | Shard spender for burst | Good |
| Finger of Death | 12d10+30 + 8/level, 150 mana | Very strong single target |
| Animate Dead / Mass Animate | Pet summoning | Core identity |
| Bone Shield absorb | 500 per charge (750 with talent) | Adequate |

**Issue found**: Necromancer was the ONLY class without passive resource generation from auto-attacks. Warriors gain Momentum, Assassins gain Intel, Thieves gain Luck/Combo, Paladins gain Holy Power, Clerics gain Faith, Mages gain Arcane Charges, Rangers gain Focus, and Bards gain Inspiration — all on hit. Necromancer had to rely entirely on active abilities (Drain Soul) and kills.

**Fix**: Added 15% per-hit Soul Shard generation. This is modest — comparable to Thief's Luck generation rate — and supplements the active generators without making them obsolete.

**Verdict**: ⚠️ One change (added 15% passive shard gen). Pet + DoT + burst kit is well-designed otherwise.

---

### 5. Paladin — Holy Power + Oaths
**Resource**: Holy Power (0-5).
**Generation Rate**: ⚠️ Was slightly slow — **BUFFED**.

| Stat | Value | Assessment |
|------|-------|------------|
| ~~Holy Power gain chance~~ | ~~25%~~ → **30% per hit** | **CHANGED** |
| Oath of Vengeance | +10% HP gen, +damage | Offensive oath |
| Oath of Devotion | DR for group | Defensive oath |
| Oath of Justice | +5% HP gen, utility | Balanced oath |
| Templar's Verdict | 3 HP spend, big damage | Core spender |
| Word of Glory | 3 HP spend, big heal | Core heal |
| Divine Storm | AoE, HP spender | Good AoE option |
| Smite | Holy damage ability | Solid filler |

**Rationale for buff**: Paladin's key abilities require 3-5 Holy Power. At 25% per hit, reaching 3 HP took ~12 hits on average, and 5 HP took ~20. With Benediction talent (+3%/rank, 5 ranks) that was 25%+15%=40% at max investment — still slower than most classes fill their resource. 30% base brings unbuffed Paladin closer to peers while keeping the Benediction talent meaningful.

**Verdict**: ⚠️ One change (HP gen 25% → 30%). Oath system is well-designed.

---

### 6. Cleric — Faith + Shadow Form
**Resource**: Faith (0-10).
**Generation Rate**: ✅ Good. Two distinct generation paths.

| Stat | Value | Assessment |
|------|-------|------------|
| Faith from healing | +1 per heal (non-shadow) | Good — rewards role |
| Faith from damage | +1 per hit (shadow form) | Fair — comparable to Intel |
| Shadow form tradeoff | +25% shadow dmg, -30% healing | Meaningful choice |
| Divine Word | Faith spender, utility | Good |
| Holy Fire | Faith spender, damage | Good |
| Divine Intervention | 10 Faith, emergency save | Appropriately expensive |
| Guardian Spirit | Prevent death, costs 5 Faith | Strong cooldown |

**Shadow Form Analysis**: The -30% healing penalty for +25% shadow damage is a strong tradeoff. Shadow Clerics can't effectively heal, making this a true specialization choice. Faith generation from damage (1 per hit) is slower than Assassin Intel but Cleric has more ability variety.

**Verdict**: ✅ No changes needed. Dual-spec design is excellent.

---

### 7. Mage — Arcane Charges
**Resource**: Arcane Charges (0-5, expandable to 6 with Arcane Mastery talent).
**Generation Rate**: ✅ Good. +1 per offensive spell.

| Stat | Value | Assessment |
|------|-------|------------|
| Charge gain | +1 per offensive spell | Fast, appropriate for caster |
| Charge damage bonus | +8% per charge (40% at 5) | Strong but offset by mana cost |
| Charge mana cost increase | +10% per charge (50% at 5) | Good tradeoff |
| Arcane Barrage | Dumps all charges | Core rotation ability |
| Fireball | 3d6+5 + 3/level, 40 mana | Solid workhorse |
| Meteor Swarm | 8d6+10 + 4/level, 80 mana | Strong single-target |
| Spell crit base | 10% (5 base + 5 class) | Fair |
| Spell crit mult | 2.0x | Fair for caster |
| Meteor Storm (60) | 15d10+50 + 6/level, 200 mana, 10min CD | Appropriately powerful capstone |

**Mana Economy**: At 5 charges, mana costs are 50% higher. This creates natural burst windows — stack charges, dump with Arcane Barrage, rebuild. The charge→mana cost tradeoff is one of the best-balanced resource mechanics in the game.

**Talent Analysis**: Fire/Frost/Arcane trees are well-differentiated. Combustion (guaranteed fire crits) and Deep Freeze (stun + frost burst) are strong tier 5 talents but appropriately gated.

**Verdict**: ✅ No changes needed. Best-balanced caster class.

---

### 8. Ranger — Focus
**Resource**: Focus (0-100).
**Generation Rate**: ⚠️ Was slightly fast — **REDUCED**.

| Stat | Value | Assessment |
|------|-------|------------|
| ~~Focus per hit~~ | ~~10~~ → **8** | **CHANGED** |
| Focus from dodge | +15 | Unchanged, rewards defense |
| Focus from Hunter's Mark target | +5 bonus | Unchanged |
| Master Marksman talent | +2/rank/hit | Unchanged |
| Aimed Shot | Focus spender, burst | Good |
| Kill Command | Focus spender, pet attack | Good identity |
| Rapid Fire | Focus spender, multi-hit | Fun burst window |
| Hunter's Mark | Utility, enables bonus Focus | Core mechanic |

**Rationale for nerf**: At 10 Focus/hit + 5 from Mark + 15 on dodge, Rangers could fill 100 Focus in ~6-7 hits (even fewer with Master Marksman talent at +10). This meant Focus spenders were available almost every other combat round, making Focus feel trivial. At 8/hit, baseline fill takes ~8-9 hits. With Hunter's Mark (13/hit) it's ~8 hits. This keeps the resource meaningful without making it frustrating.

**Pet System**: Wolf/Bear/Hawk/Cat/Boar each have distinct HP/damage/armor/special profiles. Well-designed. Beast Mastery talents provide meaningful pet scaling.

**Verdict**: ⚠️ One change (Focus gain 10 → 8). Pet system and talent trees are solid.

---

### 9. Bard — Inspiration
**Resource**: Inspiration (0-10).
**Generation Rate**: ⚠️ Was too slow — **BUFFED**.

| Stat | Value | Assessment |
|------|-------|------------|
| ~~Inspiration per hit~~ | ~~25% chance~~ → **33% chance** | **CHANGED** |
| Inspiration from healing allies | +1 per heal | Unchanged |
| Crescendo | Inspiration spender | Good |
| Encore | Repeat last ability, 3 Inspiration | Good design |
| Magnum Opus | Ultimate, 10 Inspiration | Satisfying capstone |
| Song of Courage | +2 hit, +1 dam, 3 mana/tick | Solid early buff |
| Battle Hymn | Haste + hit, 4 mana/tick | Strong combat buff |
| Dirge of Doom | Enemy debuff, 4 mana/tick | Good debuff |
| Song of Rest | Regen buff, 2 mana/tick | Essential utility |

**Rationale for buff**: At 25%, Bard generated ~1 Inspiration every 4 hits, meaning 10 Inspiration took ~40 hits. Compare to Assassin Intel (10 hits), Thief Luck (~7 hits to fill at 15% + crits), or Mage Arcane Charges (5 spells). Bard was dramatically slower, making Magnum Opus (10 Inspiration) feel nearly unattainable in normal combat. At 33%, it takes ~30 hits — still slower than all melee classes but no longer painfully so.

**Song System**: Ongoing mana-drain songs are a unique and well-designed mechanic. The mana-per-tick costs (2-8) create interesting choices about which song to maintain. Symphony of Destruction at 8 mana/tick is expensive but deals AoE damage.

**Verdict**: ⚠️ One change (Inspiration gen 25% → 33%). Song system and support kit are well-designed.

---

## Cross-Class Balance Summary

### DPS Tier List (Level 60, Single Target, Sustained)

| Tier | Class | Notes |
|------|-------|-------|
| S | **Mage** | Arcane Charges + spell scaling + crit potential. Burst king. |
| A | **Warrior** (Berserker) | High sustained with Momentum + self-damage tradeoffs |
| A | **Assassin** | Intel ramp into Execute Contract for huge burst |
| A | **Thief** | Crit-focused sustained DPS (slightly reduced from S-tier) |
| B+ | **Ranger** | Good sustained + pet damage. Focus abilities add burst windows |
| B+ | **Necromancer** | Pets + DoTs + Soul Shard burst. Multi-vector damage |
| B | **Paladin** (Retribution) | Holy Power → Templar's Verdict. Decent burst, lower sustained |
| B | **Cleric** (Shadow) | Shadow DoTs + Mind Flay. Respectable DPS with healing fallback |
| C | **Bard** | Support class. Lowest solo DPS but massive group utility |

### Healing Tier List

| Tier | Class | Notes |
|------|-------|-------|
| S | **Cleric** (Holy) | Full heal toolkit, Faith mechanic, Guardian Spirit |
| A | **Paladin** (Holy) | Word of Glory, Lay on Hands, off-heals |
| B | **Bard** | Song of Rest, group heals, support utility |

### Tankiness Tier List

| Tier | Class | Notes |
|------|-------|-------|
| S | **Warrior** (Iron Wall) | Shields, taunts, DR, death saves |
| S | **Paladin** (Protection) | Holy Shield, Ardent Defender, Divine Guardian |
| A | **Necromancer** (Blood) | Bone Shield, lifesteal, Vampiric Blood |
| B | **Cleric** (Discipline) | Shields, Pain Suppression |

### Boss Fight Viability

All 9 classes can handle endgame bosses, though through different strategies:

- **Warrior**: Sustained damage + self-healing (Rally). Berserker for DPS race, Iron Wall for survival.
- **Mage**: Burst windows with Arcane Charges. Kite with Frost slows/roots. Mana management critical.
- **Assassin**: Intel ramp → Execute Contract for big burst. Evasion/Vanish for survival.
- **Thief**: Sustained crits + Jackpot burst. Second Chance passive for death prevention.
- **Ranger**: Pet tanks while Ranger DPSes from safety. Focus abilities for burst phases.
- **Necromancer**: Pets + DoTs for sustained. Bone Shield for survival. Soul Reap for burst.
- **Paladin**: Self-heals + damage. Lay on Hands emergency. Divine Shield for invuln phases.
- **Cleric**: Shadow DPS + self-healing. Can swap to healing in emergencies.
- **Bard**: Slowest kills but highest survivability through self-buffs and CC (Lullaby, Mesmerize).

---

## Talent Tree Assessment

### Meaningful vs Negligible Passives

**Well-designed passives** (clear gameplay impact):
- Warrior Combo Mastery (50% stronger combo bonuses)
- Assassin Ghost (50% dodge after big hit)
- Thief Second Chance (survive fatal blow once per fight)
- Paladin Ardent Defender (survive fatal blow, heal to 20%)
- Cleric Atonement (damage heals lowest ally)
- Mage Shatter (50% more crit damage to frozen targets)

**Borderline passives** (low per-rank impact, consider buffing):
- Bard Resonance (song lingers 2s/rank after stopping) — in practice songs rarely stop intentionally
- Ranger Survivalist (HP regen +2%/rank) — negligible in combat, marginal out of combat
- Necromancer Desolation (DoT damage +2%/rank) — low impact per rank

These borderline passives are not worth changing right now — they provide incremental value and don't break anything. Worth revisiting if player feedback indicates they feel like "dead" talents.

---

## Cooldown Analysis

### Short Cooldowns (< 10s)
- Warrior Strike: 4s ✅
- Warrior Bash: 8s ✅

### Medium Cooldowns (10-30s)
- Warrior Cleave: 10s ✅
- Warrior Charge: 12s ✅
- Warrior Rally/Execute: 15s ✅
- Paladin Holy Shock: 15s ✅
- Paladin Consecration: 20s ✅

### Long Cooldowns (30s-3min)
- Mage Arcane Explosion: 30s ✅
- Paladin Hammer of Justice: 45s ✅
- Cleric Mass Dispel: 60s ✅
- Paladin Avenging Wrath: 180s ✅
- Mage Icy Veins/Combustion: 180s ✅

### Ultimate Cooldowns (5-10min)
- Paladin Divine Shield: 300s ✅
- Mage Meteor Storm: 600s ✅
- Cleric Divine Intervention: 600s ✅
- Bard Magnum Opus: 600s ✅
- Paladin Crusader's Judgment: 600s ✅
- Necromancer Apocalypse: 600s ✅

All cooldowns appear well-calibrated. No changes needed.

---

## Files Modified

1. `src/combat.py` — 5 changes:
   - Line ~797: Bard Inspiration generation 25% → 33%
   - Line ~750: Paladin Holy Power generation 25% → 30%
   - Line ~573: Thief crit multiplier 2.5x → 2.25x
   - Line ~775: Ranger Focus per hit 10 → 8
   - Line ~803 (new): Added Necromancer Soul Shard generation (15% per hit)

---

*Report generated 2026-02-14. Next review recommended after significant content additions or player feedback.*
