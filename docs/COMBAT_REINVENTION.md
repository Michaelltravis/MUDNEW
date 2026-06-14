# Misthollow — Combat Reinvention

Goal: replace the World-of-Warcraft-derived spells, skills, and talent trees
with original abilities native to Misthollow. Each class is anchored on its
**unique signature resource** (which WoW has no equivalent of) and the
world's existing factions/lore. Animations from the per-ability FX registry
(`fx-abilities.js`) are remapped to the new names — no ability loses its look.

Rollout is **class-by-class**, each batch:
1. New SPELLS entries + new `special` hooks (genuinely new mechanics).
2. New skill `cmd_` methods or reworks.
3. Talent-tree rename (display names + talent text; ids kept or migrated).
4. **Save migration** mapping old ability keys → new (existing characters
   keep equivalent power).
5. FX registry remap + help/learn/config updates.
6. In-process tests, then commit.

The Necromancer (batch 1) is the implemented template below.

---

## What's being replaced (the WoW lifts)

- **Talent trees**: Necro *Unholy/Blood/Frost* (DK), Ranger *Beast Mastery/
  Marksmanship/Survival* (Hunter), Cleric *Holy/Discipline/Shadow* (Priest),
  Paladin *Holy/Protection/Retribution*, Mage *Fire/Frost/Arcane*.
- **Abilities**: mortal strike, whirlwind, bladestorm, avatar, rallying cry;
  death grip, death coil, army, remorseless winter, breath of sindragosa,
  soul reaper, plague strike; kill command, bestial wrath, aimed shot,
  serpent/wyvern sting, marked shot; eviscerate, mutilate, envenom, fan of
  knives, shadow dance, kidney shot, killing spree; crusader strike, divine
  storm, templar's verdict, avenging wrath, word of glory; icy veins,
  combustion, arcane barrage/blast, evocation, blink, time warp, mirror
  image; prayer of mending, spirit link, lightwell, holy fire.

---

## Per-class new identity (resource + lore)

### Necromancer — "Soulbinder of the Mist"  ·  resource: **Soul Shards**
Lore: the death-cults beneath the Drow Conclave and the Forgotten Crypt bind
souls into the Mist. The Soulbinder *harvests* shards from the dying and
*spends* them on escalating death-magic and risen servants.
Talent trees: **Unholy/Blood/Frost → Mistbinding / Sanguine / Gravecold.**
Signature mechanics: shard generation on kills/DoT-deaths; shard spending
scales damage; an execute that reaps shards.
| Old (WoW) | New | Mechanic |
|---|---|---|
| death grip | **Mistgrasp** | shadow dmg, roots in mist, +1 Soul Shard |
| death coil | **Wraithfire** | hurls bound spirits; consumes up to 5 shards, dmg per shard |
| plague strike | **Mistrot** | stacking rot DoT; releases a shard when the host dies |
| finger of death | **Sever the Cord** | execute: <25% HP → massive reap + 3 shards |
| soul reaper | **Reap** | shard-fueled scythe finisher |
| army of the dead | **Crypt Call** | raise a transient host of crypt-shades |
| vampiric touch | **Leechcraft** | drain that banks overheal as a shard |

### Warrior — "Vanguard of Midgaard"  ·  resource: **Momentum**
Lore: the disciplined shield-line of the city watch. Momentum builds on
connecting blows and is spent on decisive finishers; doctrines (Iron Wall/
Berserker/Warlord) already original — refine names of granted abilities.
| mortal strike → **Rivenstrike** · whirlwind → **Sweeping Guard** · bladestorm → **Bladewall** · avatar → **Aspect of the Vanguard** · rallying cry → **Hold the Line** |

### Mage — "Adept of the High Tower"  ·  resource: **Arcane Charges**
Trees: Fire/Frost/Arcane → **Emberweave / Rimeward / Mistcalling.**
arcane blast → **Towerbolt** · arcane barrage → **Charge Release** · evocation
→ **Drink the Leyline** · blink → **Stepwise** · mirror image → **Tower
Echoes** · combustion → **Kindling Focus** · icy veins → **Rimeheart.**

### Cleric — "Keeper of the Holy Order"  ·  resource: **Faith**
Trees: Holy/Discipline/Shadow → **Radiance / Vigil / Penance.**
prayer of mending → **Travelling Grace** · spirit link → **Shared Burden** ·
lightwell → **Font of the Vigil** · holy fire → **Pyre of Faith.**

### Paladin — "Lightbringer"  ·  resource: **Holy Power**
Trees: Holy/Protection/Retribution → **Dawnward / Bulwark / Reckoning.**
crusader strike → **Dawnstrike** · divine storm → **Halo of Reckoning** ·
templar's verdict → **Verdict of the Order** · avenging wrath → **Ascendant
Hour** · word of glory → **Absolution.**

### Ranger — "Silversong Warden"  ·  resource: **Focus**
Trees: BM/Marks/Survival → **Wildbond / Truesight / Pathcraft.**
kill command → **Wildbond Strike** · bestial wrath → **Primal Accord** ·
aimed shot → **Truesight Shot** · serpent sting → **Thornvenom** · marked
shot → **Hunter's Verdict** · stampede → **Call of the Pack.**

### Thief — "the Whisper (Thieves Guild)"  ·  resource: **Luck**
backstab kept (generic) · gambits spend/build Luck: jackpot → **The Big
Score** · rigged dice → **Loaded Odds** · pocket sand → **Cheap Trick.**

### Assassin — "the Dark Brotherhood"  ·  resource: **Intel**
Intel marks build to guaranteed kills: mark → **Contract Mark** · expose →
**Read the Mark** · execute contract → **Fulfil the Contract** · shadow step
→ **Slip the Veil** · killing spree → **Bloodied Ledger.**

### Bard — "Court Performer"  ·  resource: **Inspiration**
(Already largely original.) Refine: hymn of hope → **Refrain of Hope** ·
chord of disruption → **Shattering Chord** · siren song → **Beguiling Verse.**

---

## Animation mapping
Every new name is added to `fx-abilities.js` (the per-ability signature
registry), reusing the existing 169 signatures by intent — e.g. Mistgrasp →
the death-grip beam+glyph, Wraithfire → the death-coil blight nova, Mistrot →
the poison cone. No new art is required; the registry regexes are re-keyed.

## Save safety
Renamed ability/talent keys are migrated on player load: a `LEGACY_ABILITY_MAP`
copies each old key's rank/proficiency to the new key, so existing characters
keep their learned abilities at equal power. Old keys are dropped after copy.
