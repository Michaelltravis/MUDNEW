# Marquee quests: the balance pass

The owner asked that a marquee quest take "a couple hours of play time" for one hero, and that
it get harder with the number of heroes who set out on it. This pass measured what the
quests actually ask of each class, alone and in groups, with the game's own combat code. It
then retuned `src/marquee_scale.py` to match. Along the way it found and fixed several bugs
that change every fight, not only the quests.

## In short

- **Every class, alone:** an elite takes about a minute, a warden about two, and the trial's
  boss about three. The boss costs about two thirds of the hero's health at its worst moment;
  elites and wardens cost up to about half. Deaths are rare: 0.03 a quest on average for a
  lone hero (Push 13: 0.18), at most one in three quests for any class and level.
- **Groups of 2, 3 and 6:** every party finishes, with no fight lost in 324 simulated group
  quests. The creatures are made for the heroes who set out: their health for what the party
  deals, their damage for what the party can stand.
- **Time:** a lone hero who knows the way plays a quest through in 41-70 simulated minutes
  (median 58). That is 13-20 minutes of fighting, 6-28 of resting and 17-33 of walking. See
  [Time](#time-and-the-two-hour-goal) for what that means against the two-hour goal.
- **Both combat modes:** the numbers hold in the round-by-round fights (telnet, and `/play`
  with real-time combat off) and in `/play`'s real-time combat.

## Fixes that change every fight

These were wrong for every player, everywhere, not only in the quests:

| what | was | now |
|---|---|---|
| creature armour | zone files give it as `armor_class`, but the loader read `ac`, so every creature had the default | creatures wear their file's armour (an older `ac` still works). Levels 10-39 are harder to hit now, 40 and up easier. |
| INT and DEX bonuses | class names are lower case, the checks weren't, so a mage's INT never helped them hit and a thief's DEX never added damage | both apply |
| warrior skills | a warrior's skills did the same damage at level 50 as at 10 | they grow with level as the warrior's swings do |
| Charm Person (and sleep, blindness) | worked on creatures flagged against it, and on bosses | they shrug it off ("is unaffected") |
| shield spells cast again | each cast added another full shield: stoneskin five times was five shields, armor five times -100 AC | a recast renews the spell's shield or bonus |
| a boss's blow on a pet | the boss crashed sending a message to the pet and froze mid-cast for the rest of the fight (a necromancer's servant stopped any boss) | the blow lands and the boss goes on (a failed cast can no longer freeze it either) |
| big quest creatures | any creature over 5,000 health took the world's "boss" kit: a slam on everyone in the room every 8 s, fear, adds, enrage. A lone warrior's or assassin's elites got it by accident (and most classes' at higher levels), and so did nearly every creature a group met, waves included | a quest's creatures keep their own kit (a world creature that big still gets it) |

(Push 12 already stopped bosses landing an extra bruiser's blow on top of their own rotation.)

## How hard the quests are now

`src/marquee_scale.py` sizes each creature when it is placed:

- **Health** = `ROUNDS[kind]` x `dpr(level)` x `CLASS_K` x the party's health factor.
  - `dpr(level)` is the median hero's damage a round, measured: 204 at level 45, 254 at 50,
    317 at 55, 395 at 60 since the endgame gear's stats count (Push 22; 240, 282 and 332
    before). It was a guess at first (150 to 197).
  - `CLASS_K` is how a class's damage compares with the median, measured. At first it was a
    guess with the mage at 1.1 and the warrior at 1.0; measured, they are 0.56 and 1.49
    (Push 23). So a lone warrior's elites died in 31 s instead of 66, and a mage's took 82.
  - For a group, both are the mean over everyone who set out. The quest now records their
    classes when it is accepted.
- **Damage** (what the creature's blows and specials in `world/zones/zone_097.json` are
  multiplied by) = `FOE_DAMAGE[kind]` x `CLASS_D` x `LEVEL_D`^(level - 45) x the party's
  damage factor.
  - `FOE_DAMAGE`: elites 2.0, a ritual's waves 0.7, everything else 1.0.
  - `CLASS_D` is what the class can stand, measured (Push 23): necromancer 0.45, thief 0.57,
    mage 0.67, assassin 0.82, warrior 0.99, ranger 1.04, bard 1.04, cleric 1.48, paladin 2.07.
    For a group it is the mean over who set out.
  - `LEVEL_D` is 1.009: creatures hit 0.9% harder a level above 45, because heroes grow
    sturdier (1.8% before the endgame gear's stats counted).
- **Level**: a creature is as many levels above its file's as the quest is above 45. Without
  that, a level-55 party met creatures so far below them that they never wound up their blows.

The rest is as it was: the party's size is fixed when the quest is accepted. Health grows
x(1 + 0.8(n-1)), damage x(1 + 0.1(n-1)), and each wave gets one more creature for every two
extra heroes. A boss acts 6% sooner for each extra hero.

## Measured again after the spell fixes (Push 14)

Push 14 made spells and effects do what they say (`docs/REBUILD_PLAN.md`). Several of those
fixes change what a class deals or can stand, so both tables were measured again:

- **Spell cooldowns hold.** A mage cast Meteor Storm (ten minutes) whenever it was the strongest
  spell ready. Their damage is 0.58 of the median hero's now, not 0.65, and their creatures
  have less health to match.
- **The necromancer's high spells work.** Summon Gargoyle (level 50) brings a second fighter, and
  Soul Harvest and Apocalypse strike every foe: 1.10 of the median, not 0.99.
- **Room spells strike the foes.** Their damage was skipped before.
- **Stuns end.** A bash (30%), Kidney Shot or a creature's paralysing touch left the target
  "stunned" for good. A boss so stunned never cast, enraged or changed phase again. A paladin
  bashes whenever Halo of Reckoning (now on its 10 s cooldown) isn't ready, so their bosses came
  out harmless at any share. Now a stun costs a round, and a boss only staggers.
- **The paladin's own spells work.** Protection from evil takes a sixth off an evil creature's
  blows, Hallowed Ground burns the foes each round, Dawnhammer staggers a boss (it takes half
  again from every blow for a moment), and Ascendant Hour's haste adds swings. A paladin stands
  1.77 now (it was 1.33).
- **The simulation's necromancer** raised a new bone knight only when no pet stood by. With the
  gargoyle working, a fallen knight was never raised again, and the creatures went straight
  for the necromancer, which no player would allow. Only the raised dead count now.

## Measured again after the balance follow-ups (Push 18)

- **Caster shields gain 2 a level, not 4** (`ABSORB_LEVEL_BONUS`). At 4, a level-45 mage's
  stoneskin and armour ward held 369 damage against 191 health, so an elite's blows never got
  through. Mages, clerics and bards now feel an elite's and a warden's blows.
- **The bone knight's shield wall rests.** It was up about two rounds in three with no rest, it
  stayed up after a fight, and its taunt turned fighting groupmates onto the knight. It now
  lasts three rounds and rests six, comes down out of a fight, and turns only the creatures
  fighting its owner, their group or their pets. A necromancer's servant holds less, so they
  stand less.
- **Damage over time finishes a creature.** Poison, plague and the rest stopped at 1 health, so a
  creature at its last few points outlived every tick. The killing tick is now dealt as a wound
  from whoever it fights, who gets the kill. A player is never killed by it: poison lingering
  after a fight still stops at 1.
- **`CLASS_D` measured again** for the classes these change (`--calibrate --classes
  mage,necromancer --runs 8`): `CLASS_K` hardly moved (mage 0.57, necromancer 1.14). With
  shields halved, a lone mage's trial boss cost up to 90% of their health, and a lone
  necromancer at level 60 died 1.3 times a quest. Both are set at their weakest level again:
  - the mage at 0.55 (levels 45-60 stand 0.55, 0.88, 0.67 and 0.67);
  - the necromancer at 0.50 (0.65, 0.81, 0.50 and 0.50).
  Their quests now cost a lone mage 32-50% of their health at the boss with no deaths, and a
  lone necromancer at most 0.3 deaths a quest, as in Push 14.
- **Real quests are written down** (`src/marquee_log.py`): each acceptance, each stage's end,
  each death on the quest and its end (finished or abandoned), with the party, its classes and
  level, and the combat mode, go to `lib/marquee_runs.jsonl` (an immortal's quests are tests and
  are left out). `marquee stats` (immortals) sums them up by class and party size. See
  [Time](#time-and-the-two-hour-goal).

## Measured again with the endgame gear (Push 22)

- **The endgame items' stats count.** 62 items (levels 40-70) gave their stats as an `effects`
  dict the server never read. They load now, so heroes at 45-60 wearing them are stronger:
  Coral Plate's -35 armour class, the Cinderbrand Greatsword's +10 to hit, +12 damage and +4
  strength. The simulator dresses its heroes from the same gear table, so they wear them too.
- **The simulator chooses armour right.** It scored an `armor` affect the wrong way round, a
  better (lower) armour class counting as worse, so it passed over the best armour.
- **An archer needs a bow.** The ordinary blow's reach now follows the weapon in hand, so the
  simulated ranger wields a bow (it took the best weapon of any kind before, and shot anyway).
- **Measured again** (`--calibrate --levels 45,50,55,60 --runs 8`, the classes split over three
  runs):
  - The median hero deals about 200 a round at 45, 290 at 50, 310 at 55 and 395 at 60: some
    10-17% more at 50-60. `dpr()` rises 4.5% a level from 45 (3.3% before). Below 45, where
    that gear isn't worn, it keeps the curve the zone bosses were sized by.
  - `CLASS_K` against the new curve: warrior and assassin 1.47, paladin 1.13, thief 1.05,
    necromancer 1.04, bard 0.85, cleric 0.82, ranger 0.73 (0.99 before: a bow's blows are
    lighter than the swords it used to fire), mage 0.52.
  - What each class can stand now falls about 1% a level from 45 to 60 at the old 1.8%-a-level
    rise in the creatures' blows, so the rise is 0.9% (chosen, as before, so most classes come
    out flat across levels). `CLASS_D` is then each class's mean over the levels: thief 0.54,
    assassin 0.78, bard 0.78, warrior 1.05, ranger 1.07, cleric 1.40, paladin 1.88.
  - The mage is again set at its weakest level, 0.64 (at 60): heroes in plate stand more at 45
    than they did (a mage 0.83), less at 60. The necromancer's weakest level stands 0.59, but
    its deaths come all at once (when the bone knight falls): played through at 0.55, a lone
    necromancer still died 0.3-0.5 times a quest, at 0.50 0-0.4 times. It stays at 0.50.
  - The ranger falls most with level (1.25 at 45 to 0.91 at 60). At its mean, a lone
    level-60 ranger's trial boss costs about 70% of their health and 0.1 deaths a quest.
- **The zone bosses** were measured again too (below).

## Measured again with gear health and attributes (Push 23)

- **Gear's health, mana and attributes count now** (they only showed in `score` before): an
  item's +200 health raises the real maximum, and +2 constitution, intelligence or wisdom
  reaches regeneration, saves, spell criticals and the rest. The simulator's heroes wear the
  same gear table, so they carry it too.
- **Damage** moved little: the median hero deals 1-5% more, so `dpr()` stays. Casters' own
  damage rose with their gear's intelligence (spell criticals): `CLASS_K` mage 0.52 to 0.56,
  cleric 0.82 to 0.86, necromancer 1.04 to 1.16, ranger 0.73 to 0.78.
- **What each class can stand** rose for most (`--calibrate`, the classes split over three
  runs; the four whose `CLASS_K` moved measured again under their new value):
  - warrior 0.99, cleric 1.48, thief 0.57, ranger 1.04, bard 1.04 (0.78: its health and
    charisma from gear), assassin 0.82.
  - The paladin's curve stays flat (55-79% of its health at the boss over shares 1.4-3.0,
    deaths only from 3.5): measured on a wider grid, it is 2.07.
  - The mage stays at its weakest level, 0.67 (levels 45-60 stand 0.75, 0.86, 0.75, 0.69).
    Played through eight times at 0.67, it died 0.2 times a quest at 45 and never at 60.
  - The necromancer's damage rose, so its quest creatures got more health: longer fights,
    more time for the bone knight to fall. Its level-60 cliff moved down (0.4: 0.1 deaths a
    quest, 0.5: 0.8). It is set at 0.45: played through eight times at 45, 55 and 60, it died
    0.1-0.2 times a quest.
- `LEVEL_D` stays 0.9% a level: most classes still come out flat across levels.
- **The zone bosses** were measured again too (below): most hit harder, since heroes carry more
  health.

## Measured again with gear wards (Push 24)

- **Gear's wards count now:** fire, frost, poison, shadow and the rest turn aside up to 75% of
  their kind of harm, and every source says its kind: spells their school, boss abilities by
  name or their own `element` (69 of 100 are elemental), creatures' spells, breath and venom,
  poison ticks and hazards. Gear's saves, spell resistance and haste count too.
- **The quests moved within noise** (all nine classes alone at 45, 50, 55 and 60, three runs
  each, the simulator's fixed seeds). 24 of 36 rows came out exactly as before, and no class
  got harder. A few deaths went away: the assassin at 50 and 60 and the necromancer at 45,
  0.3 a quest each.
  - The heroes wear the same gear table, and most of its pieces ward nothing: what a ward
    adds is a little less of a poison spit or an ice storm.
  - `CLASS_K`, `CLASS_D` and `LEVEL_D` stay.
- **The zone bosses** eased a little: a lone hero's median worst fight is 49% of their
  health, from 51%, and they die 35 times in 360 fights, from 39.
  - The poison-spitting spider queens eased most: the Spider Queen of level 26 from 50% to
    41%, with no deaths now; the spider queen of level 12 from 52% to 46%.
  - That is a ward doing its work. `ZONE_BOSS_DAMAGE` stays.

## How it was measured

`tools/balance/sim.py` plays each class's quest with real `World`, `Player` and `Mobile`
objects and the real combat code, on a simulated clock (a quest takes about a second).

- **Heroes** are built the way the game builds them: created at level 1 and levelled up with
  the class's own dice, every ability their level has unlocked at 80% from use.
- **Gear:** each slot holds the item at the 75th percentile of what the world offers at that
  level.
- **Groups** are the quest's class plus a cleric, a warrior, a mage, a ranger and a bard, in
  that order.
- **Creatures** are placed exactly as the quest engine places them, stage by stage: kill,
  collect (two up at a time), ritual waves on their timers, and the trial's waves and boss.
- **Each fight** is fought round by round:
  - Before it, the heroes put up their defensive buffs. A necromancer keeps one raised
    servant (they last an hour, and every fight leaves corpses).
  - In it, each hero heals when someone is low, else uses the strongest attack that is
    ready, and swings. They hit the weakest foe first.
  - Each creature turns on any of the party, as `marquee._engage` does. Their wind-ups,
    specials and swings come from `mob_ai.py` and `bosses.py`.
  - A marked blow or a boss's telegraph is stepped out of 60% of the time.
- **The world's clocks** run on through each fight: poison every 3 s, damage and healing over
  time every 6 s, and regeneration (a fighter regains about 13% of their health a minute).
- **A fight lost** is fought again from the temple, against what is left of the foe, which
  has healed as creatures do out of a fight. A ritual starts over.
- **Time:** after each fight the heroes rest to full at the game's resting rates, about 40%
  of health and 50% of mana a minute. Walking between the quest's places takes the shortest
  way through the world's rooms at 4 s a room, plus a minute a leg for reading and finding
  the way. A death adds the walk back from the temple.
- **"Health at worst"** is the most of a hero's health a fight took at any point: a healer
  who mends back up still counts the low point, and a death counts as all of it. In a group
  it is the worst-off member.

Things a player does that the simulation does not, which all make the quests easier than
measured: potions, kiting, a ranger's tamed beast, more than one servant, interrupting a
boss's cast, and pulling one creature at a time.

The simulation found most of the bugs above. Its own first version also had mistakes that
made the quests look far harder than they are, and those were fixed before any number was
set:
- it counted only swings, not skills, spells or damage over time;
- it let foes flee and heroes stand out of reach;
- it ran no regeneration during fights, and rested at half the game's real rate;
- it sent every creature at the party's tank;
- it gave a lone hero an escort minion the game only gives groups.

## Calibration

`python3 tools/balance/sim.py --calibrate --levels 45,50,55,60 --runs 8` measures both tables:

- **`CLASS_K`** is each class's own damage a round over the median hero's, averaged over the
  four levels.
- **`CLASS_D`** is found per class by trying damage shares from 0.3 to 2.6 (3.0 for the
  paladin) at each level (8 quests each). It is the share at which a lone hero's trial boss
  costs 65% of their health, or at which the quest costs half a death, whichever comes first,
  averaged over the levels.
  - With the rise included (`LEVEL_D`: 0.9% a level since Push 22, 1.8% before), most
    classes come out nearly flat across levels, which is how the rise was chosen.
  - Two classes are set at their weakest level instead of the mean, since a death is the
    worst a quest can do:
    - the mage at 0.67 since Push 23 (0.64 in Push 22, 0.55 in Push 18, 0.75 before that):
      levels 45-60 stand 0.75, 0.86, 0.75 and 0.69;
    - the necromancer at 0.45 since Push 23 (0.50 from Push 18, 0.60 before that): its servant
      makes it all-or-nothing, safe while the bone knight stands and exposed when it falls, so
      it is set where a quest costs it well under half a death at every level (played through:
      0.1-0.2).
  - A paladin's boss costs 55-68% of their health across shares from 1.0 to 2.3: it mends
    itself back up. The share is set where the curve crosses 65%, and deaths start only
    above 2.3.
  - A class's own damage depends a little on the creatures' health (a longer fight thins a
    hero's opening burst), so a class whose `CLASS_K` moved was measured again under its new
    value before its `CLASS_D` was found.

## Results

Three quests per row, rounds mode, `--dodge 0.6 --gear 0.75 --walk 4 --travel 1`, measured
after Push 18 (before the endgame gear's stats counted: Push 22 measured the scale again, above,
but not these tables). "Fights lost" counts the fights the party had to go back for.

### Alone

| class | level | party | minutes in all | fighting | resting | on the way | deaths | fights lost (to) | hero damage/round | dpr() | health at worst: elite / warden / wave / boss |
|---|---|---|---|---|---|---|---|---|---|---|---|
| assassin | 45 | 1 | 43 | 18 | 7 | 18 | 0.0 | 0.0 | 309 | 204 | 32% / 29% / 19% / 49% |
| assassin | 50 | 1 | 41 | 16 | 7 | 18 | 0.0 | 0.0 | 403 | 240 | 33% / 27% / 19% / 57% |
| assassin | 55 | 1 | 44 | 18 | 9 | 18 | 0.0 | 0.0 | 431 | 282 | 32% / 38% / 25% / 75% |
| assassin | 60 | 1 | 41 | 14 | 9 | 17 | 0.0 | 0.0 | 583 | 332 | 47% / 40% / 25% / 72% |
| bard | 45 | 1 | 61 | 15 | 14 | 32 | 0.0 | 0.0 | 171 | 204 | - / 49% / 12% / 59% |
| bard | 50 | 1 | 57 | 13 | 12 | 32 | 0.0 | 0.0 | 229 | 240 | - / 38% / 12% / 62% |
| bard | 55 | 1 | 57 | 14 | 12 | 32 | 0.0 | 0.0 | 255 | 282 | - / 49% / 15% / 73% |
| bard | 60 | 1 | 56 | 13 | 11 | 32 | 0.0 | 0.0 | 320 | 332 | - / 42% / 15% / 69% |
| cleric | 45 | 1 | 66 | 20 | 27 | 20 | 0.0 | 0.0 | 156 | 204 | 11% / 50% / 23% / 70% |
| cleric | 50 | 1 | 59 | 15 | 24 | 19 | 0.0 | 0.0 | 228 | 240 | 15% / 41% / 13% / 84% |
| cleric | 55 | 1 | 62 | 17 | 25 | 20 | 0.0 | 0.0 | 241 | 282 | 18% / 45% / 20% / 68% |
| cleric | 60 | 1 | 58 | 15 | 25 | 19 | 0.0 | 0.0 | 323 | 332 | 26% / 51% / 16% / 61% |
| mage | 45 | 1 | 69 | 20 | 26 | 23 | 0.0 | 0.0 | 103 | 204 | 1% / 0% / 7% / 32% |
| mage | 50 | 1 | 63 | 16 | 24 | 23 | 0.0 | 0.0 | 136 | 240 | 0% / 0% / 0% / 36% |
| mage | 55 | 1 | 65 | 17 | 25 | 23 | 0.0 | 0.0 | 158 | 282 | 0% / 2% / 1% / 50% |
| mage | 60 | 1 | 66 | 16 | 27 | 23 | 0.0 | 0.0 | 205 | 332 | 0% / 2% / 6% / 50% |
| necromancer | 45 | 1 | 65 | 19 | 25 | 21 | 0.0 | 0.0 | 187 | 204 | 0% / 20% / 0% / 53% |
| necromancer | 50 | 1 | 63 | 15 | 26 | 22 | 0.0 | 0.0 | 292 | 240 | 0% / 31% / 4% / 0% |
| necromancer | 55 | 1 | 67 | 16 | 28 | 23 | 0.3 | 0.3 (boss 0.3) | 329 | 282 | 7% / 0% / 6% / 17% |
| necromancer | 60 | 1 | 65 | 15 | 28 | 22 | 0.0 | 0.0 | 402 | 332 | 6% / 4% / 7% / 2% |
| paladin | 45 | 1 | 57 | 18 | 19 | 20 | 0.3 | 0.3 (boss 0.3) | 232 | 204 | 21% / 46% / 18% / 72% |
| paladin | 50 | 1 | 53 | 16 | 18 | 20 | 0.0 | 0.0 | 321 | 240 | 8% / 49% / 22% / 65% |
| paladin | 55 | 1 | 54 | 17 | 17 | 20 | 0.0 | 0.0 | 344 | 282 | 26% / 41% / 19% / 61% |
| paladin | 60 | 1 | 48 | 18 | 11 | 19 | 0.0 | 0.0 | 371 | 332 | 59% / 55% / 30% / 67% |
| ranger | 45 | 1 | 70 | 18 | 27 | 25 | 0.3 | 0.3 (wave 0.3) | 190 | 204 | 60% / 52% / 32% / 59% |
| ranger | 50 | 1 | 69 | 17 | 28 | 25 | 0.0 | 0.0 | 247 | 240 | 54% / 52% / 27% / 58% |
| ranger | 55 | 1 | 69 | 17 | 27 | 25 | 0.0 | 0.0 | 273 | 282 | 56% / 50% / 28% / 60% |
| ranger | 60 | 1 | 65 | 16 | 24 | 24 | 0.0 | 0.0 | 333 | 332 | 61% / 56% / 35% / 58% |
| thief | 45 | 1 | 47 | 16 | 6 | 25 | 0.3 | 0.3 (boss 0.3) | 209 | 204 | - / 38% / 21% / 75% |
| thief | 50 | 1 | 45 | 13 | 6 | 25 | 0.0 | 0.0 | 280 | 240 | - / 38% / 19% / 73% |
| thief | 55 | 1 | 44 | 14 | 6 | 24 | 0.0 | 0.0 | 314 | 282 | - / 33% / 29% / 74% |
| thief | 60 | 1 | 43 | 13 | 6 | 24 | 0.0 | 0.0 | 390 | 332 | - / 27% / 25% / 64% |
| warrior | 45 | 1 | 60 | 19 | 7 | 33 | 0.0 | 0.0 | 279 | 204 | 36% / 23% / 17% / 89% |
| warrior | 50 | 1 | 54 | 16 | 6 | 33 | 0.0 | 0.0 | 402 | 240 | 27% / 24% / 20% / 41% |
| warrior | 55 | 1 | 58 | 17 | 7 | 33 | 0.0 | 0.0 | 441 | 282 | 28% / 35% / 23% / 61% |
| warrior | 60 | 1 | 55 | 15 | 6 | 33 | 0.0 | 0.0 | 568 | 332 | 22% / 35% / 24% / 60% |

The necromancer's boss costs little because its servant holds the boss's attention; its deaths
come when the servant falls. A mage's elites still cost little: a mage's creatures hit softest
(`CLASS_D` 0.55) and their wards take the rest. A cleric's cost 11-26% now that shields gain 2 a
level (Push 14: 8-14%).

### Groups

The worst-off member of each party; deaths count every member.

| class | level | party | minutes in all | fighting | resting | on the way | deaths | fights lost (to) | hero damage/round | dpr() | health at worst: elite / warden / wave / boss |
|---|---|---|---|---|---|---|---|---|---|---|---|
| assassin | 45 | 2 | 57 | 15 | 25 | 17 | 0.0 | 0.0 | 291 | 204 | 26% / 31% / 18% / 66% |
| assassin | 45 | 3 | 62 | 18 | 27 | 18 | 0.0 | 0.0 | 315 | 204 | 36% / 41% / 23% / 71% |
| assassin | 45 | 6 | 60 | 18 | 24 | 17 | 0.0 | 0.0 | 333 | 204 | 45% / 36% / 30% / 77% |
| assassin | 50 | 2 | 62 | 15 | 30 | 18 | 0.0 | 0.0 | 391 | 240 | 18% / 39% / 19% / 57% |
| assassin | 50 | 3 | 58 | 15 | 26 | 17 | 0.0 | 0.0 | 422 | 240 | 34% / 49% / 21% / 57% |
| assassin | 50 | 6 | 59 | 16 | 26 | 17 | 0.0 | 0.0 | 452 | 240 | 35% / 39% / 31% / 69% |
| assassin | 55 | 2 | 60 | 15 | 27 | 18 | 0.0 | 0.0 | 418 | 282 | 28% / 45% / 22% / 60% |
| assassin | 55 | 3 | 61 | 16 | 26 | 18 | 0.0 | 0.0 | 461 | 282 | 34% / 52% / 30% / 73% |
| assassin | 55 | 6 | 60 | 17 | 25 | 17 | 0.0 | 0.0 | 465 | 282 | 39% / 56% / 33% / 74% |
| assassin | 60 | 2 | 60 | 14 | 28 | 18 | 0.0 | 0.0 | 537 | 332 | 30% / 35% / 26% / 55% |
| assassin | 60 | 3 | 60 | 15 | 27 | 18 | 0.0 | 0.0 | 610 | 332 | 40% / 49% / 31% / 57% |
| assassin | 60 | 6 | 61 | 16 | 27 | 18 | 0.0 | 0.0 | 637 | 332 | 50% / 40% / 28% / 72% |
| bard | 45 | 2 | 66 | 13 | 21 | 32 | 0.0 | 0.0 | 176 | 204 | - / 52% / 12% / 67% |
| bard | 45 | 3 | 66 | 14 | 20 | 31 | 0.0 | 0.0 | 188 | 204 | - / 56% / 26% / 71% |
| bard | 45 | 6 | 72 | 16 | 24 | 32 | 0.0 | 0.0 | 197 | 204 | - / 40% / 29% / 74% |
| bard | 50 | 2 | 64 | 11 | 21 | 32 | 0.0 | 0.0 | 243 | 240 | - / 26% / 4% / 59% |
| bard | 50 | 3 | 68 | 12 | 23 | 32 | 0.0 | 0.0 | 259 | 240 | - / 31% / 23% / 53% |
| bard | 50 | 6 | 66 | 13 | 21 | 32 | 0.0 | 0.0 | 265 | 240 | - / 40% / 27% / 70% |
| bard | 55 | 2 | 61 | 11 | 19 | 31 | 0.0 | 0.0 | 266 | 282 | - / 40% / 13% / 61% |
| bard | 55 | 3 | 62 | 12 | 19 | 31 | 0.0 | 0.0 | 285 | 282 | - / 45% / 26% / 59% |
| bard | 55 | 6 | 66 | 14 | 20 | 32 | 0.0 | 0.0 | 294 | 282 | - / 44% / 30% / 73% |
| bard | 60 | 2 | 60 | 10 | 19 | 31 | 0.0 | 0.0 | 344 | 332 | - / 41% / 13% / 53% |
| bard | 60 | 3 | 65 | 12 | 22 | 32 | 0.0 | 0.0 | 371 | 332 | - / 41% / 27% / 53% |
| bard | 60 | 6 | 61 | 12 | 17 | 31 | 0.0 | 0.0 | 375 | 332 | - / 45% / 26% / 74% |
| cleric | 45 | 2 | 61 | 16 | 26 | 19 | 0.0 | 0.0 | 173 | 204 | 7% / 55% / 12% / 56% |
| cleric | 45 | 3 | 66 | 18 | 28 | 20 | 0.0 | 0.0 | 181 | 204 | 40% / 56% / 34% / 71% |
| cleric | 45 | 6 | 66 | 20 | 27 | 20 | 0.0 | 0.0 | 189 | 204 | 47% / 62% / 42% / 75% |
| cleric | 50 | 2 | 63 | 14 | 29 | 20 | 0.0 | 0.0 | 247 | 240 | 10% / 35% / 5% / 60% |
| cleric | 50 | 3 | 63 | 15 | 28 | 20 | 0.0 | 0.0 | 261 | 240 | 52% / 41% / 33% / 59% |
| cleric | 50 | 6 | 64 | 16 | 28 | 20 | 0.0 | 0.0 | 266 | 240 | 47% / 53% / 37% / 73% |
| cleric | 55 | 2 | 58 | 14 | 25 | 19 | 0.0 | 0.0 | 262 | 282 | 17% / 32% / 9% / 61% |
| cleric | 55 | 3 | 60 | 16 | 24 | 19 | 0.3 | 0.0 | 287 | 282 | 47% / 38% / 40% / 61% |
| cleric | 55 | 6 | 64 | 18 | 27 | 19 | 0.0 | 0.0 | 290 | 282 | 51% / 57% / 46% / 74% |
| cleric | 60 | 2 | 57 | 13 | 25 | 19 | 0.0 | 0.0 | 355 | 332 | 12% / 33% / 14% / 67% |
| cleric | 60 | 3 | 63 | 15 | 28 | 20 | 0.0 | 0.0 | 363 | 332 | 38% / 45% / 32% / 60% |
| cleric | 60 | 6 | 67 | 17 | 31 | 20 | 0.0 | 0.0 | 386 | 332 | 40% / 53% / 43% / 70% |
| mage | 45 | 2 | 66 | 16 | 27 | 23 | 0.0 | 0.0 | 108 | 204 | 15% / 13% / 4% / 65% |
| mage | 45 | 3 | 67 | 18 | 26 | 23 | 0.0 | 0.0 | 119 | 204 | 30% / 35% / 29% / 71% |
| mage | 45 | 6 | 73 | 20 | 29 | 24 | 0.0 | 0.0 | 127 | 204 | 45% / 51% / 31% / 77% |
| mage | 50 | 2 | 64 | 14 | 27 | 23 | 0.0 | 0.0 | 150 | 240 | 3% / 23% / 4% / 63% |
| mage | 50 | 3 | 70 | 16 | 30 | 24 | 0.0 | 0.0 | 167 | 240 | 37% / 38% / 21% / 62% |
| mage | 50 | 6 | 67 | 17 | 27 | 24 | 0.0 | 0.0 | 175 | 240 | 41% / 50% / 26% / 73% |
| mage | 55 | 2 | 64 | 14 | 27 | 23 | 0.0 | 0.0 | 181 | 282 | 6% / 17% / 10% / 58% |
| mage | 55 | 3 | 65 | 16 | 26 | 23 | 0.0 | 0.0 | 191 | 282 | 33% / 23% / 26% / 73% |
| mage | 55 | 6 | 70 | 18 | 28 | 24 | 0.0 | 0.0 | 201 | 282 | 49% / 48% / 32% / 72% |
| mage | 60 | 2 | 62 | 13 | 25 | 23 | 0.0 | 0.0 | 217 | 332 | 14% / 7% / 9% / 54% |
| mage | 60 | 3 | 65 | 15 | 27 | 23 | 0.0 | 0.0 | 252 | 332 | 36% / 40% / 29% / 59% |
| mage | 60 | 6 | 63 | 16 | 25 | 23 | 0.0 | 0.0 | 257 | 332 | 39% / 51% / 37% / 72% |
| necromancer | 45 | 2 | 63 | 16 | 26 | 22 | 0.0 | 0.0 | 218 | 204 | 9% / 44% / 7% / 60% |
| necromancer | 45 | 3 | 68 | 19 | 27 | 22 | 0.0 | 0.0 | 211 | 204 | 27% / 45% / 21% / 73% |
| necromancer | 45 | 6 | 70 | 21 | 27 | 22 | 0.0 | 0.0 | 206 | 204 | 40% / 61% / 29% / 73% |
| necromancer | 50 | 2 | 63 | 13 | 28 | 22 | 0.0 | 0.0 | 302 | 240 | 3% / 24% / 3% / 41% |
| necromancer | 50 | 3 | 62 | 16 | 25 | 21 | 0.0 | 0.0 | 276 | 240 | 34% / 34% / 21% / 60% |
| necromancer | 50 | 6 | 63 | 17 | 25 | 21 | 0.0 | 0.0 | 295 | 240 | 41% / 49% / 28% / 75% |
| necromancer | 55 | 2 | 59 | 13 | 25 | 21 | 0.0 | 0.0 | 349 | 282 | 19% / 40% / 3% / 39% |
| necromancer | 55 | 3 | 67 | 17 | 28 | 22 | 0.0 | 0.0 | 323 | 282 | 49% / 49% / 25% / 67% |
| necromancer | 55 | 6 | 70 | 19 | 29 | 22 | 0.0 | 0.0 | 319 | 282 | 48% / 36% / 32% / 76% |
| necromancer | 60 | 2 | 58 | 12 | 25 | 21 | 0.0 | 0.0 | 435 | 332 | 5% / 34% / 9% / 58% |
| necromancer | 60 | 3 | 67 | 16 | 29 | 22 | 0.0 | 0.0 | 412 | 332 | 44% / 37% / 25% / 66% |
| necromancer | 60 | 6 | 63 | 17 | 25 | 21 | 0.0 | 0.0 | 390 | 332 | 46% / 48% / 30% / 70% |
| paladin | 45 | 2 | 62 | 15 | 27 | 20 | 0.0 | 0.0 | 249 | 204 | 3% / 51% / 13% / 58% |
| paladin | 45 | 3 | 64 | 18 | 26 | 20 | 0.0 | 0.0 | 259 | 204 | 32% / 61% / 29% / 77% |
| paladin | 45 | 6 | 65 | 19 | 26 | 20 | 0.0 | 0.0 | 271 | 204 | 36% / 56% / 33% / 75% |
| paladin | 50 | 2 | 62 | 14 | 28 | 20 | 0.0 | 0.0 | 333 | 240 | 10% / 28% / 11% / 61% |
| paladin | 50 | 3 | 60 | 15 | 25 | 20 | 0.0 | 0.0 | 353 | 240 | 31% / 45% / 32% / 58% |
| paladin | 50 | 6 | 67 | 17 | 30 | 20 | 0.0 | 0.0 | 358 | 240 | 38% / 48% / 30% / 77% |
| paladin | 55 | 2 | 58 | 14 | 25 | 19 | 0.0 | 0.0 | 367 | 282 | 4% / 41% / 11% / 62% |
| paladin | 55 | 3 | 62 | 16 | 27 | 19 | 0.0 | 0.0 | 382 | 282 | 36% / 68% / 27% / 64% |
| paladin | 55 | 6 | 62 | 17 | 26 | 19 | 0.0 | 0.0 | 395 | 282 | 33% / 51% / 32% / 72% |
| paladin | 60 | 2 | 64 | 15 | 29 | 20 | 0.0 | 0.0 | 395 | 332 | 31% / 43% / 16% / 61% |
| paladin | 60 | 3 | 60 | 15 | 26 | 19 | 0.0 | 0.0 | 453 | 332 | 40% / 60% / 30% / 63% |
| paladin | 60 | 6 | 62 | 17 | 26 | 20 | 0.0 | 0.0 | 450 | 332 | 53% / 70% / 38% / 75% |
| ranger | 45 | 2 | 67 | 16 | 27 | 25 | 0.0 | 0.0 | 185 | 204 | 22% / 43% / 25% / 59% |
| ranger | 45 | 3 | 70 | 18 | 27 | 25 | 0.0 | 0.0 | 195 | 204 | 44% / 42% / 27% / 76% |
| ranger | 45 | 6 | 70 | 19 | 27 | 25 | 0.0 | 0.0 | 208 | 204 | 44% / 50% / 31% / 71% |
| ranger | 50 | 2 | 68 | 14 | 29 | 25 | 0.0 | 0.0 | 252 | 240 | 23% / 50% / 19% / 57% |
| ranger | 50 | 3 | 65 | 15 | 26 | 25 | 0.0 | 0.0 | 263 | 240 | 27% / 45% / 24% / 61% |
| ranger | 50 | 6 | 72 | 17 | 30 | 25 | 0.0 | 0.0 | 274 | 240 | 33% / 48% / 30% / 70% |
| ranger | 55 | 2 | 64 | 14 | 25 | 24 | 0.0 | 0.0 | 272 | 282 | 30% / 49% / 17% / 61% |
| ranger | 55 | 3 | 68 | 16 | 27 | 24 | 0.0 | 0.0 | 292 | 282 | 35% / 50% / 25% / 57% |
| ranger | 55 | 6 | 68 | 17 | 26 | 24 | 0.0 | 0.0 | 312 | 282 | 48% / 41% / 33% / 69% |
| ranger | 60 | 2 | 68 | 14 | 30 | 25 | 0.0 | 0.0 | 343 | 332 | 28% / 57% / 27% / 60% |
| ranger | 60 | 3 | 65 | 14 | 26 | 24 | 0.0 | 0.0 | 378 | 332 | 34% / 38% / 27% / 57% |
| ranger | 60 | 6 | 67 | 16 | 26 | 25 | 0.0 | 0.0 | 373 | 332 | 46% / 61% / 33% / 71% |
| thief | 45 | 2 | 57 | 13 | 20 | 24 | 0.0 | 0.0 | 230 | 204 | - / 46% / 17% / 65% |
| thief | 45 | 3 | 64 | 15 | 23 | 25 | 0.0 | 0.0 | 250 | 204 | - / 31% / 23% / 77% |
| thief | 45 | 6 | 60 | 15 | 21 | 24 | 0.0 | 0.0 | 257 | 204 | - / 24% / 28% / 71% |
| thief | 50 | 2 | 52 | 11 | 18 | 23 | 0.0 | 0.0 | 300 | 240 | - / 33% / 18% / 60% |
| thief | 50 | 3 | 55 | 12 | 20 | 23 | 0.0 | 0.0 | 339 | 240 | - / 25% / 25% / 57% |
| thief | 50 | 6 | 57 | 12 | 21 | 24 | 0.0 | 0.0 | 355 | 240 | - / 41% / 31% / 67% |
| thief | 55 | 2 | 56 | 12 | 20 | 24 | 0.0 | 0.0 | 329 | 282 | - / 36% / 27% / 62% |
| thief | 55 | 3 | 60 | 13 | 23 | 24 | 0.0 | 0.0 | 378 | 282 | - / 32% / 26% / 66% |
| thief | 55 | 6 | 59 | 14 | 21 | 24 | 0.0 | 0.0 | 391 | 282 | - / 33% / 32% / 70% |
| thief | 60 | 2 | 60 | 12 | 23 | 25 | 0.0 | 0.0 | 405 | 332 | - / 40% / 23% / 55% |
| thief | 60 | 3 | 59 | 12 | 21 | 25 | 0.0 | 0.0 | 462 | 332 | - / 28% / 27% / 66% |
| thief | 60 | 6 | 57 | 13 | 20 | 24 | 0.0 | 0.0 | 497 | 332 | - / 36% / 33% / 73% |
| warrior | 45 | 2 | 76 | 17 | 26 | 33 | 0.0 | 0.0 | 295 | 204 | 32% / 39% / 17% / 58% |
| warrior | 45 | 3 | 76 | 18 | 25 | 33 | 0.0 | 0.0 | 322 | 204 | 42% / 60% / 25% / 76% |
| warrior | 45 | 6 | 82 | 20 | 28 | 33 | 0.0 | 0.0 | 336 | 204 | 47% / 48% / 29% / 73% |
| warrior | 50 | 2 | 73 | 13 | 26 | 34 | 0.0 | 0.0 | 431 | 240 | 40% / 43% / 22% / 54% |
| warrior | 50 | 3 | 79 | 16 | 29 | 34 | 0.0 | 0.0 | 451 | 240 | 32% / 30% / 21% / 52% |
| warrior | 50 | 6 | 76 | 16 | 26 | 33 | 0.0 | 0.0 | 477 | 240 | 39% / 36% / 29% / 70% |
| warrior | 55 | 2 | 73 | 14 | 26 | 33 | 0.0 | 0.0 | 469 | 282 | 30% / 34% / 20% / 54% |
| warrior | 55 | 3 | 72 | 15 | 24 | 32 | 0.0 | 0.0 | 496 | 282 | 39% / 38% / 25% / 54% |
| warrior | 55 | 6 | 76 | 17 | 26 | 33 | 0.0 | 0.0 | 511 | 282 | 49% / 40% / 30% / 70% |
| warrior | 60 | 2 | 71 | 13 | 25 | 33 | 0.0 | 0.0 | 601 | 332 | 20% / 40% / 18% / 63% |
| warrior | 60 | 3 | 74 | 15 | 26 | 33 | 0.0 | 0.0 | 620 | 332 | 45% / 59% / 23% / 47% |
| warrior | 60 | 6 | 77 | 16 | 27 | 34 | 0.0 | 0.0 | 661 | 332 | 36% / 48% / 28% / 70% |

### Real-time combat (the 3D client)

The same quests, with skills a second apart (`--mode action`).

| class | level | party | minutes in all | fighting | resting | on the way | deaths | fights lost (to) | hero damage/round | dpr() | health at worst: elite / warden / wave / boss |
|---|---|---|---|---|---|---|---|---|---|---|---|
| warrior | 45 | 1 | 58 | 18 | 7 | 33 | 0.0 | 0.0 | 292 | 204 | 31% / 26% / 17% / 76% |
| warrior | 45 | 3 | 76 | 18 | 25 | 33 | 0.0 | 0.0 | 325 | 204 | 40% / 32% / 26% / 69% |
| warrior | 55 | 1 | 56 | 17 | 7 | 33 | 0.0 | 0.0 | 455 | 282 | 33% / 30% / 18% / 42% |
| warrior | 55 | 3 | 71 | 15 | 24 | 32 | 0.0 | 0.0 | 495 | 282 | 49% / 49% / 27% / 56% |
| paladin | 45 | 1 | 52 | 15 | 18 | 19 | 0.0 | 0.0 | 280 | 204 | 2% / 33% / 12% / 76% |
| paladin | 45 | 3 | 63 | 17 | 26 | 20 | 0.0 | 0.0 | 290 | 204 | 16% / 60% / 26% / 72% |
| paladin | 55 | 1 | 51 | 15 | 16 | 20 | 0.0 | 0.0 | 392 | 282 | 11% / 37% / 14% / 58% |
| paladin | 55 | 3 | 61 | 15 | 27 | 19 | 0.0 | 0.0 | 436 | 282 | 18% / 45% / 26% / 62% |
| cleric | 45 | 1 | 67 | 20 | 27 | 20 | 0.0 | 0.0 | 154 | 204 | 14% / 53% / 19% / 63% |
| cleric | 45 | 3 | 66 | 18 | 28 | 20 | 0.0 | 0.0 | 183 | 204 | 41% / 58% / 31% / 73% |
| cleric | 55 | 1 | 62 | 17 | 25 | 20 | 0.0 | 0.0 | 244 | 282 | 19% / 41% / 13% / 74% |
| cleric | 55 | 3 | 59 | 15 | 24 | 19 | 0.0 | 0.0 | 291 | 282 | 45% / 60% / 36% / 62% |
| mage | 45 | 1 | 72 | 20 | 27 | 25 | 0.3 | 0.3 (boss 0.3) | 103 | 204 | 1% / 0% / 12% / 56% |
| mage | 45 | 3 | 66 | 18 | 26 | 23 | 0.0 | 0.0 | 124 | 204 | 41% / 50% / 24% / 74% |
| mage | 55 | 1 | 66 | 17 | 26 | 23 | 0.0 | 0.0 | 157 | 282 | 2% / 0% / 8% / 47% |
| mage | 55 | 3 | 65 | 16 | 26 | 23 | 0.0 | 0.0 | 187 | 282 | 42% / 38% / 27% / 63% |
| necromancer | 45 | 1 | 65 | 18 | 25 | 21 | 0.0 | 0.0 | 193 | 204 | 1% / 0% / 0% / 5% |
| necromancer | 45 | 3 | 68 | 19 | 27 | 22 | 0.0 | 0.0 | 208 | 204 | 36% / 32% / 24% / 74% |
| necromancer | 55 | 1 | 67 | 15 | 29 | 23 | 0.3 | 0.3 (warden 0.3) | 350 | 282 | 15% / 17% / 0% / 21% |
| necromancer | 55 | 3 | 67 | 17 | 28 | 22 | 0.0 | 0.0 | 345 | 282 | 38% / 50% / 26% / 72% |
| thief | 45 | 1 | 48 | 16 | 7 | 25 | 0.3 | 0.3 (boss 0.3) | 204 | 204 | - / 38% / 24% / 78% |
| thief | 45 | 3 | 63 | 15 | 23 | 25 | 0.0 | 0.0 | 252 | 204 | - / 41% / 23% / 60% |
| thief | 55 | 1 | 43 | 14 | 5 | 24 | 0.0 | 0.0 | 312 | 282 | - / 35% / 22% / 69% |
| thief | 55 | 3 | 60 | 14 | 23 | 24 | 0.0 | 0.0 | 375 | 282 | - / 41% / 25% / 60% |
| assassin | 45 | 1 | 43 | 18 | 7 | 18 | 0.0 | 0.0 | 310 | 204 | 29% / 31% / 22% / 43% |
| assassin | 45 | 3 | 62 | 18 | 27 | 18 | 0.0 | 0.0 | 315 | 204 | 30% / 44% / 23% / 70% |
| assassin | 55 | 1 | 45 | 18 | 9 | 18 | 0.0 | 0.0 | 423 | 282 | 38% / 34% / 24% / 70% |
| assassin | 55 | 3 | 60 | 16 | 26 | 18 | 0.0 | 0.0 | 457 | 282 | 21% / 39% / 25% / 65% |
| ranger | 45 | 1 | 70 | 17 | 27 | 25 | 0.3 | 0.3 (elite 0.3) | 193 | 204 | 52% / 52% / 32% / 57% |
| ranger | 45 | 3 | 70 | 17 | 28 | 25 | 0.0 | 0.0 | 195 | 204 | 25% / 48% / 28% / 75% |
| ranger | 55 | 1 | 70 | 17 | 27 | 25 | 0.0 | 0.0 | 276 | 282 | 48% / 48% / 33% / 69% |
| ranger | 55 | 3 | 67 | 16 | 28 | 24 | 0.0 | 0.0 | 300 | 282 | 42% / 30% / 28% / 56% |
| bard | 45 | 1 | 68 | 15 | 22 | 32 | 0.0 | 0.0 | 175 | 204 | - / 21% / 10% / 76% |
| bard | 45 | 3 | 66 | 14 | 21 | 31 | 0.0 | 0.0 | 189 | 204 | - / 40% / 26% / 65% |
| bard | 55 | 1 | 67 | 13 | 21 | 33 | 0.3 | 0.3 (boss 0.3) | 275 | 282 | - / 36% / 15% / 61% |
| bard | 55 | 3 | 63 | 12 | 19 | 31 | 0.0 | 0.0 | 293 | 282 | - / 31% / 24% / 55% |

## Time and the two-hour goal

The fights take what the design asks: an elite about a minute, a warden about two, a boss about
three. Around them, a lone hero who knows the way spends 6-28 minutes resting and 17-33 walking,
41-70 minutes in all. Thieves and assassins finish soonest: they have no mana to rest back.
Rangers, mages and necromancers finish last.

That is efficient play by a player who knows the way. A first time through adds what the
simulation does not count: reading the stages, finding unfamiliar places, looting, and the odd
death and walk back.

If the quests still play short, one number moves them: `ROUNDS` in `marquee_scale.py`, the
rounds a lone hero needs for each kind of foe. Longer fights cost more health, so after changing
it run `--calibrate` again and copy the new `CLASS_D`.

Real quests now say how long they take: `marquee stats` (immortals) reads `lib/marquee_runs.jsonl`
and gives, by class and party size, the quests finished, their median minutes and range, and
deaths a quest. Once a few real quests are in, that is the number to tune `ROUNDS` against.

## Zone bosses

The bosses in the world's zones (the Goblin King, the dragons, the gate guardians: 20 of them
from level 12 to 60 at first, 111 from level 10 to 60 once the zones were populated) had never
been measured. Their files were written for far weaker heroes:
before this pass a party of three at a boss's level felled every one in 2-6 rounds, for 0-15%
of its health. These are not the event bosses of `world_events.py` (150,000 health, "requiring
group effort"), and the bosses above the mortal level cap (the four horsemen, Kirgan, the
sovereigns at 62-70) keep their files' numbers: they are raid fights.

A zone boss can't know who will fight it, so it is sized like a marquee trial's boss for a
lone hero at its level (`bosses.size_zone_boss`):

- **Health:** 40 rounds of what the median hero of its level deals (`marquee_scale.dpr`),
  whatever its file or its rank in a population file says: about two minutes alone (a warrior
  1.9, a mage 3.0, a boss's followers and waves included), and 0.3-1.8 minutes for a party of
  three.
- **Damage:** each boss's own blows, abilities, poison and adds are weighed by one share of
  their own (`ZONE_BOSS_DAMAGE`), found by `tools/balance/bosses.py --calibrate`: the share at
  which a lone hero of the median class loses half their health at the worst moment, or a
  quarter of lone heroes die, whichever comes first. The shares run from 0.08-0.09 (Malvoran,
  Ulgrathar and Vorlath, casters whose kits hit a dozen times too hard) and 0.11 (the
  Necromancer) to 1.5-1.7 (the ancient guardian, Grimclaw and the Oakfather, whose files have
  no damage dice and hit with 1d6); the median is 0.43. Measured again in Push 22, once the
  endgame gear's stats counted and an archer needed a bow in hand (the gate guardians 1.2 to
  0.95), and in Push 23, once gear's health and attributes counted: heroes carry more health,
  so most bosses hit harder (the Goblin King 0.25 to 0.40, the gate guardians 0.95 to 1.08).
  Measured again when the zones were populated (`world/population/`): 91 new bosses, and the
  old ones with mechanics of their own now (pools, waves, a call for help), which make a fight
  longer, so a boss's blows weigh a little less (the Goblin King 0.59, the mindflayer 0.48).

Three fixes came out of measuring them:

- A creature's poison and a boss's adds ignored its damage share: the spider queens' poison
  (`3 + level/5` a tick, every 3 s) and the Goblin King's goblins did their full damage at any
  share. Both now weigh as the creature's blows do (a quest's adds keep their own share).
- A boss's summons were endless: the Goblin King called three goblins every 18 s for as long as
  the fight lasted, and once he lived long enough a room filled with them. A summoning ability
  now calls only while fewer than twice its number of the boss's callers still stand. A phase's
  adds still always come.
- The simulator saved its heroes: an achievement (level 50) writes the player, and thousands of
  simulated heroes filled `lib/players` and the leaderboards. It no longer writes anything.

And four more when the populated zones' bosses were measured:

- A population file's `boss` rank lifts a creature to eleven times a regular's health, about
  1.45 times the sizing, and five designed files held 3.5-7 times it (Archon Prime 108,693 at
  level 60, Shadow Lord Malachar, the Kraken, the Abbot's Ghost, Grizznak): a party took 3.5-6
  minutes over them and a lone hero was called off at 15. A zone boss's health is now the
  sizing's, never its file's.
- A plague pool burned the moment it was laid, so the STEP OUT cue came too late to heed. It
  now settles for 1.5 s first (`boss_mechanics.POOL_ARM`). The simulator's heroes step out of a
  pool, and keep moving against a hunger, with the same `--dodge` chance as a marked blow;
  before, they stood in every pool, and the pools alone cost a lone hero 20-45% whatever the
  boss's share.
- A boss's add whose file says boss took on the generic boss kit (`mob_ai`): the frozen dwarven
  king, raised by Vyrkothas at half health, summoned minions of a sixth of his health each,
  every 25 s, at full damage and without end, and killed 72% of lone heroes at any share. A
  boss's adds are adds now, and the generic kit's minions are weighed by their summoner's share,
  no more than four standing when it calls.
- A boss's call for help, in the simulator, brought in the temple's neighbours (it fights by
  the altar), and they were gone for the next fight. It now raises the boss's own followers,
  weighed as its adds are. In the game the zone's creatures nearby still come first, at their
  own strength: clearing the halls around a boss makes it easier.

What a lone hero at the boss's level meets, over the 111 bosses (two fights each;
[the full table](bosses.md)):

| class | health at worst (median) | deaths in 222 fights | minutes (median) |
|---|---|---|---|
| necromancer | 2% | 17 | 2.4 |
| paladin | 28% | 0 | 1.9 |
| warrior | 35% | 0 | 1.9 |
| cleric | 49% | 0 | 3.0 |
| assassin | 51% | 0 | 2.1 |
| ranger | 56% | 0 | 3.4 |
| bard | 56% | 1 | 2.9 |
| thief | 62% | 16 | 2.1 |
| mage | 76% | 80 | 3.0 |

A party of three (warrior, cleric, mage) finishes any of them in 0.3-1.8 minutes (median 0.8),
its worst-off member losing 0-49% (median 9%). The necromancer's bone knight takes the blows
(2% at the median), until it falls: then it is the necromancer. (The first 20, measured in
Push 23 with gear's health and attributes counting: 39 deaths in 360 fights, 49 in Push 22; and
in Push 24, with gear's wards meeting the bosses' fire, poison and the rest: 35 deaths. All 111
now: 114 deaths in 1,998 fights.)

The spread between classes is the cost of a boss that can't know who fights it: a lone mage
(about 190 health at level 45, and half the median hero's damage) or a necromancer whose bone
knight falls usually dies at the boss's level, where a warrior or a paladin loses a quarter of
their health. A level or two, or a friend, changes that. If every class should be able to solo
them at level, the bosses could weigh their blows by the class they strike, as a marquee
quest's creatures are made for the classes that embarked.

The simulation's heroes don't interrupt a cast. The Necromancer's Drain Life heals him a tenth
of his health unless interrupted, and the Goblin King keeps calling goblins, which the
simulation's heroes fight first. So a lone mage, cleric, ranger or bard can take ten minutes or
more over them, where a player who presses X or strikes the boss would not.

## Rerunning

    python3 tools/balance/sim.py --levels 45,50,55,60 --party 1,2,3,6 --runs 3     # the tables above
    python3 tools/balance/sim.py --levels 45,55 --party 1,3 --mode action          # real-time combat
    python3 tools/balance/sim.py --calibrate --levels 45,50,55,60 --runs 8         # CLASS_K and CLASS_D
    python3 tools/balance/sim.py --classes mage --levels 45 --party 1 --verbose    # one quest, stage by stage
    python3 tests/test_balance.py                                                  # the fixes, and one quest simulated
    python3 tools/balance/bosses.py --runs 2 --report docs/balance/bosses.md       # the zone bosses, every class
    python3 tools/balance/bosses.py --calibrate --runs 2                           # ZONE_BOSS_DAMAGE (bosses.py)
    python3 tools/balance/bosses.py --bosses 3503 --classes mage                   # one boss, one class

`--foe-damage elite=1.5` and `--class-damage mage=0.8` try other values without editing the
code. Any creature turn that raises an error is printed once (`  ! ...`): those are the game's
own bugs.
