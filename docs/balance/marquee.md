# Marquee quests: the balance pass

The owner asked that a marquee quest take "a couple hours of play time" for one hero, and that
it get harder with the number of heroes who set out on it. This pass measured what the
quests actually ask of each class, alone and in groups, with the game's own combat code. It
then retuned `src/marquee_scale.py` to match. Along the way it found and fixed several bugs
that change every fight, not only the quests.

## In short

- **Every class, alone:** an elite takes about a minute, a warden about two, and the trial's
  boss about three. The boss costs about two thirds of the hero's health at its worst moment;
  elites and wardens cost up to about half. Deaths are rare: 0.18 a quest on average for a
  lone hero, at most one.
- **Groups of 2, 3 and 6:** every party finishes, with no fight lost in 324 simulated group
  quests. The creatures are made for the heroes who set out: their health for what the party
  deals, their damage for what the party can stand.
- **Time:** a lone hero who knows the way plays a quest through in 40-81 simulated minutes
  (median 62). That is 12-23 minutes of fighting, 6-30 of resting and 17-34 of walking. See
  [Time](#time-and-the-two-hour-goal) for what that means against the two-hour goal.
- **Both combat modes:** the numbers hold in the round-by-round fights (telnet and the 2D
  client) and in the 3D client's real-time combat.

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
  - `dpr(level)` is the median hero's damage a round, measured: 204 at level 45, 240 at 50,
    282 at 55, 332 at 60. It was a guess before (150 to 197).
  - `CLASS_K` is how a class's damage compares with the median, measured. Before, it was a
    guess with the mage at 1.1 and the warrior at 1.0; measured, they are 0.65 and 1.58.
    So a lone warrior's elites died in 31 s instead of 66, and a mage's took 82.
  - For a group, both are the mean over everyone who set out. The quest now records their
    classes when it is accepted.
- **Damage** (what the creature's blows and specials in `world/zones/zone_097.json` are
  multiplied by) = `FOE_DAMAGE[kind]` x `CLASS_D` x `LEVEL_D`^(level - 45) x the party's
  damage factor.
  - `FOE_DAMAGE`: elites 2.0, a ritual's waves 0.7, everything else 1.0.
  - `CLASS_D` is what the class can stand, measured: thief 0.56, necromancer 0.70, bard 0.70,
    mage 0.74, assassin 0.80, ranger 0.99, warrior 1.06, cleric 1.33, paladin 1.33. For a
    group it is the mean over who set out.
  - `LEVEL_D` is 1.018: creatures hit 1.8% harder a level above 45, because heroes grow sturdier.
- **Level**: a creature is as many levels above its file's as the quest is above 45. Without
  that, a level-55 party met creatures so far below them that they never wound up their blows.

The rest is as it was: the party's size is fixed when the quest is accepted. Health grows
x(1 + 0.8(n-1)), damage x(1 + 0.1(n-1)), and each wave gets one more creature for every two
extra heroes. A boss acts 6% sooner for each extra hero.

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
- **`CLASS_D`** is found per class by trying damage shares from 0.3 to 2.0 at each level (8
  quests each). It is the share at which a lone hero's trial boss costs 65% of their health,
  or at which the quest costs half a death, whichever comes first, averaged over the levels.
  - With the 1.8%-a-level rise included, most classes come out nearly flat across levels,
    which is how the rise was chosen.
  - The necromancer is set a little under its measurement (0.70 against 0.73). Its servant
    makes it all-or-nothing: safe while the servant stands, exposed when it falls, more so
    at higher levels.

## Results

Three quests per row, rounds mode, `--dodge 0.6 --gear 0.75 --walk 4 --travel 1`. "Fights
lost" counts the fights the party had to go back for.

### Alone

| class | level | party | minutes in all | fighting | resting | on the way | deaths | fights lost (to) | hero damage/round | dpr() | health at worst: elite / warden / wave / boss |
|---|---|---|---|---|---|---|---|---|---|---|---|
| warrior | 45 | 1 | 62 | 19 | 9 | 34 | 0.7 | 0.3 (boss 0.3) | 280 | 204 | 42% / 29% / 19% / 80% |
| warrior | 50 | 1 | 56 | 16 | 7 | 33 | 0.0 | 0.0 | 402 | 240 | 31% / 29% / 25% / 51% |
| warrior | 55 | 1 | 61 | 18 | 9 | 34 | 0.3 | 0.3 (wave 0.3) | 442 | 282 | 32% / 41% / 28% / 74% |
| warrior | 60 | 1 | 56 | 15 | 8 | 33 | 0.0 | 0.0 | 568 | 332 | 26% / 41% / 27% / 75% |
| paladin | 45 | 1 | 62 | 18 | 25 | 19 | 0.0 | 0.0 | 208 | 204 | 28% / 47% / 20% / 61% |
| paladin | 50 | 1 | 64 | 17 | 28 | 20 | 0.0 | 0.0 | 271 | 240 | 36% / 29% / 19% / 68% |
| paladin | 55 | 1 | 64 | 17 | 27 | 20 | 0.0 | 0.0 | 309 | 282 | 48% / 37% / 17% / 73% |
| paladin | 60 | 1 | 46 | 15 | 11 | 19 | 0.0 | 0.0 | 388 | 332 | 50% / 42% / 16% / 56% |
| cleric | 45 | 1 | 66 | 20 | 27 | 20 | 0.0 | 0.0 | 149 | 204 | 20% / 52% / 23% / 69% |
| cleric | 50 | 1 | 59 | 15 | 24 | 19 | 0.0 | 0.0 | 212 | 240 | 21% / 34% / 17% / 67% |
| cleric | 55 | 1 | 64 | 17 | 26 | 20 | 0.3 | 0.3 (wave 0.3) | 238 | 282 | 24% / 46% / 21% / 69% |
| cleric | 60 | 1 | 58 | 14 | 24 | 19 | 0.0 | 0.0 | 312 | 332 | 25% / 39% / 20% / 70% |
| mage | 45 | 1 | 81 | 23 | 29 | 29 | 1.0 | 1.0 (boss 1.0) | 107 | 204 | 2% / 1% / 8% / 53% |
| mage | 50 | 1 | 66 | 17 | 25 | 25 | 0.3 | 0.3 (boss 0.3) | 152 | 240 | 6% / 0% / 2% / 61% |
| mage | 55 | 1 | 69 | 17 | 27 | 25 | 0.7 | 0.3 (boss 0.3) | 183 | 282 | 10% / 0% / 15% / 70% |
| mage | 60 | 1 | 69 | 16 | 28 | 25 | 0.3 | 0.3 (wave 0.3) | 237 | 332 | 0% / 0% / 13% / 87% |
| necromancer | 45 | 1 | 65 | 16 | 26 | 22 | 0.3 | 0.3 (boss 0.3) | 200 | 204 | 0% / 30% / 6% / 35% |
| necromancer | 50 | 1 | 67 | 18 | 27 | 23 | 0.3 | 0.3 (wave 0.3) | 227 | 240 | 7% / 32% / 13% / 20% |
| necromancer | 55 | 1 | 73 | 18 | 30 | 25 | 1.0 | 1.0 (boss 0.3, warden 0.3, wave 0.3) | 269 | 282 | 17% / 17% / 7% / 17% |
| necromancer | 60 | 1 | 70 | 17 | 29 | 24 | 0.7 | 0.7 (warden 0.3, wave 0.3) | 339 | 332 | 21% / 17% / 7% / 11% |
| thief | 45 | 1 | 46 | 16 | 6 | 24 | 0.0 | 0.0 | 205 | 204 | - / 45% / 24% / 87% |
| thief | 50 | 1 | 44 | 13 | 6 | 25 | 0.0 | 0.0 | 286 | 240 | - / 30% / 24% / 64% |
| thief | 55 | 1 | 44 | 13 | 6 | 24 | 0.0 | 0.0 | 316 | 282 | - / 33% / 25% / 86% |
| thief | 60 | 1 | 43 | 13 | 6 | 24 | 0.0 | 0.0 | 388 | 332 | - / 28% / 25% / 58% |
| assassin | 45 | 1 | 44 | 18 | 8 | 19 | 0.3 | 0.3 (boss 0.3) | 311 | 204 | 30% / 24% / 24% / 51% |
| assassin | 50 | 1 | 40 | 16 | 6 | 18 | 0.0 | 0.0 | 399 | 240 | 34% / 21% / 16% / 58% |
| assassin | 55 | 1 | 45 | 18 | 9 | 19 | 0.3 | 0.3 (boss 0.3) | 430 | 282 | 36% / 33% / 27% / 54% |
| assassin | 60 | 1 | 43 | 15 | 11 | 17 | 0.0 | 0.0 | 571 | 332 | 53% / 48% / 32% / 89% |
| ranger | 45 | 1 | 68 | 17 | 26 | 24 | 0.0 | 0.0 | 190 | 204 | 56% / 54% / 33% / 59% |
| ranger | 50 | 1 | 69 | 16 | 28 | 25 | 0.0 | 0.0 | 250 | 240 | 54% / 56% / 26% / 65% |
| ranger | 55 | 1 | 70 | 18 | 27 | 25 | 0.0 | 0.0 | 268 | 282 | 56% / 59% / 32% / 65% |
| ranger | 60 | 1 | 65 | 16 | 24 | 24 | 0.0 | 0.0 | 327 | 332 | 57% / 57% / 39% / 65% |
| bard | 45 | 1 | 61 | 15 | 14 | 32 | 0.0 | 0.0 | 172 | 204 | - / 30% / 14% / 67% |
| bard | 50 | 1 | 57 | 13 | 12 | 32 | 0.0 | 0.0 | 231 | 240 | - / 21% / 10% / 60% |
| bard | 55 | 1 | 57 | 14 | 12 | 32 | 0.0 | 0.0 | 254 | 282 | - / 49% / 13% / 73% |
| bard | 60 | 1 | 55 | 12 | 11 | 32 | 0.0 | 0.0 | 325 | 332 | - / 26% / 14% / 61% |

The necromancer's boss costs little because its servant holds the boss's attention; its deaths
come when the servant falls. A mage's and a cleric's elites cost little because their shields
absorb an elite's blows.

### Groups

The worst-off member of each party; deaths count every member.

| class | level | party | minutes in all | fighting | resting | on the way | deaths | fights lost (to) | hero damage/round | dpr() | health at worst: elite / warden / wave / boss |
|---|---|---|---|---|---|---|---|---|---|---|---|
| warrior | 45 | 2 | 75 | 16 | 26 | 33 | 0.0 | 0.0 | 295 | 204 | 45% / 36% / 20% / 54% |
| warrior | 45 | 3 | 76 | 18 | 25 | 33 | 0.0 | 0.0 | 312 | 204 | 44% / 41% / 23% / 72% |
| warrior | 45 | 6 | 81 | 20 | 28 | 33 | 0.0 | 0.0 | 336 | 204 | 47% / 57% / 33% / 72% |
| warrior | 50 | 2 | 73 | 13 | 26 | 34 | 0.0 | 0.0 | 417 | 240 | 28% / 27% / 16% / 60% |
| warrior | 50 | 3 | 78 | 16 | 28 | 34 | 0.0 | 0.0 | 464 | 240 | 40% / 36% / 21% / 50% |
| warrior | 50 | 6 | 76 | 16 | 26 | 33 | 0.0 | 0.0 | 466 | 240 | 45% / 39% / 28% / 70% |
| warrior | 55 | 2 | 73 | 14 | 25 | 33 | 0.0 | 0.0 | 462 | 282 | 45% / 44% / 23% / 57% |
| warrior | 55 | 3 | 72 | 15 | 24 | 32 | 0.0 | 0.0 | 502 | 282 | 41% / 40% / 27% / 60% |
| warrior | 55 | 6 | 76 | 17 | 26 | 33 | 0.0 | 0.0 | 517 | 282 | 48% / 36% / 32% / 70% |
| warrior | 60 | 2 | 71 | 13 | 25 | 33 | 0.0 | 0.0 | 581 | 332 | 31% / 50% / 24% / 65% |
| warrior | 60 | 3 | 74 | 15 | 26 | 33 | 0.0 | 0.0 | 635 | 332 | 38% / 51% / 25% / 55% |
| warrior | 60 | 6 | 77 | 16 | 27 | 34 | 0.0 | 0.0 | 662 | 332 | 49% / 45% / 38% / 71% |
| paladin | 45 | 2 | 64 | 16 | 27 | 20 | 0.0 | 0.0 | 214 | 204 | 45% / 33% / 12% / 64% |
| paladin | 45 | 3 | 65 | 18 | 27 | 20 | 0.0 | 0.0 | 240 | 204 | 42% / 57% / 26% / 73% |
| paladin | 45 | 6 | 65 | 19 | 26 | 20 | 0.0 | 0.0 | 250 | 204 | 55% / 69% / 36% / 72% |
| paladin | 50 | 2 | 63 | 15 | 28 | 20 | 0.0 | 0.0 | 284 | 240 | 23% / 12% / 11% / 66% |
| paladin | 50 | 3 | 60 | 15 | 26 | 20 | 0.0 | 0.0 | 328 | 240 | 42% / 49% / 24% / 59% |
| paladin | 50 | 6 | 67 | 17 | 30 | 20 | 0.0 | 0.0 | 342 | 240 | 43% / 39% / 34% / 77% |
| paladin | 55 | 2 | 59 | 14 | 25 | 19 | 0.0 | 0.0 | 327 | 282 | 22% / 41% / 10% / 68% |
| paladin | 55 | 3 | 62 | 15 | 27 | 19 | 0.0 | 0.0 | 375 | 282 | 39% / 50% / 31% / 62% |
| paladin | 55 | 6 | 63 | 17 | 26 | 19 | 0.0 | 0.0 | 362 | 282 | 53% / 64% / 38% / 72% |
| paladin | 60 | 2 | 62 | 14 | 28 | 20 | 0.0 | 0.0 | 411 | 332 | 21% / 29% / 15% / 63% |
| paladin | 60 | 3 | 60 | 15 | 26 | 19 | 0.0 | 0.0 | 452 | 332 | 48% / 49% / 28% / 61% |
| paladin | 60 | 6 | 61 | 16 | 26 | 20 | 0.0 | 0.0 | 470 | 332 | 44% / 46% / 35% / 74% |
| cleric | 45 | 2 | 60 | 16 | 25 | 19 | 0.0 | 0.0 | 171 | 204 | 15% / 55% / 7% / 61% |
| cleric | 45 | 3 | 66 | 18 | 28 | 20 | 0.0 | 0.0 | 176 | 204 | 47% / 65% / 32% / 73% |
| cleric | 45 | 6 | 66 | 19 | 27 | 20 | 0.0 | 0.0 | 187 | 204 | 45% / 67% / 40% / 74% |
| cleric | 50 | 2 | 63 | 14 | 29 | 20 | 0.0 | 0.0 | 234 | 240 | 0% / 29% / 10% / 58% |
| cleric | 50 | 3 | 63 | 15 | 28 | 20 | 0.0 | 0.0 | 249 | 240 | 37% / 47% / 38% / 60% |
| cleric | 50 | 6 | 65 | 17 | 28 | 20 | 0.0 | 0.0 | 253 | 240 | 40% / 48% / 38% / 72% |
| cleric | 55 | 2 | 58 | 14 | 25 | 19 | 0.0 | 0.0 | 262 | 282 | 28% / 37% / 16% / 65% |
| cleric | 55 | 3 | 59 | 15 | 24 | 19 | 0.0 | 0.0 | 281 | 282 | 45% / 51% / 30% / 60% |
| cleric | 55 | 6 | 63 | 17 | 27 | 19 | 0.0 | 0.0 | 271 | 282 | 49% / 38% / 47% / 72% |
| cleric | 60 | 2 | 57 | 13 | 25 | 19 | 0.0 | 0.0 | 336 | 332 | 11% / 29% / 14% / 62% |
| cleric | 60 | 3 | 63 | 15 | 28 | 20 | 0.0 | 0.0 | 357 | 332 | 38% / 47% / 31% / 56% |
| cleric | 60 | 6 | 68 | 17 | 31 | 20 | 0.0 | 0.0 | 362 | 332 | 48% / 66% / 39% / 73% |
| mage | 45 | 2 | 66 | 17 | 26 | 23 | 0.0 | 0.0 | 115 | 204 | 2% / 38% / 7% / 63% |
| mage | 45 | 3 | 66 | 18 | 26 | 23 | 0.0 | 0.0 | 126 | 204 | 30% / 54% / 25% / 78% |
| mage | 45 | 6 | 72 | 20 | 29 | 24 | 0.0 | 0.0 | 131 | 204 | 47% / 51% / 33% / 75% |
| mage | 50 | 2 | 63 | 14 | 26 | 23 | 0.0 | 0.0 | 170 | 240 | 4% / 17% / 1% / 63% |
| mage | 50 | 3 | 70 | 16 | 30 | 24 | 0.0 | 0.0 | 180 | 240 | 25% / 52% / 26% / 71% |
| mage | 50 | 6 | 68 | 17 | 27 | 24 | 0.0 | 0.0 | 189 | 240 | 30% / 56% / 31% / 75% |
| mage | 55 | 2 | 64 | 15 | 27 | 23 | 0.0 | 0.0 | 189 | 282 | 1% / 38% / 10% / 61% |
| mage | 55 | 3 | 65 | 16 | 26 | 23 | 0.0 | 0.0 | 208 | 282 | 47% / 36% / 29% / 68% |
| mage | 55 | 6 | 70 | 18 | 29 | 24 | 0.0 | 0.0 | 215 | 282 | 47% / 57% / 34% / 73% |
| mage | 60 | 2 | 61 | 13 | 25 | 23 | 0.0 | 0.0 | 264 | 332 | 13% / 15% / 13% / 73% |
| mage | 60 | 3 | 65 | 15 | 27 | 23 | 0.0 | 0.0 | 270 | 332 | 40% / 46% / 30% / 51% |
| mage | 60 | 6 | 63 | 16 | 25 | 23 | 0.0 | 0.0 | 288 | 332 | 46% / 38% / 39% / 72% |
| necromancer | 45 | 2 | 63 | 15 | 26 | 22 | 0.0 | 0.0 | 211 | 204 | 14% / 55% / 7% / 71% |
| necromancer | 45 | 3 | 67 | 18 | 27 | 22 | 0.0 | 0.0 | 221 | 204 | 35% / 46% / 25% / 75% |
| necromancer | 45 | 6 | 69 | 20 | 28 | 22 | 0.0 | 0.0 | 217 | 204 | 48% / 42% / 33% / 76% |
| necromancer | 50 | 2 | 64 | 14 | 28 | 22 | 0.0 | 0.0 | 264 | 240 | 8% / 35% / 11% / 66% |
| necromancer | 50 | 3 | 62 | 15 | 25 | 21 | 0.0 | 0.0 | 256 | 240 | 37% / 39% / 26% / 64% |
| necromancer | 50 | 6 | 63 | 16 | 25 | 21 | 0.0 | 0.0 | 277 | 240 | 42% / 51% / 35% / 71% |
| necromancer | 55 | 2 | 60 | 14 | 25 | 21 | 0.0 | 0.0 | 301 | 282 | 9% / 35% / 14% / 73% |
| necromancer | 55 | 3 | 67 | 16 | 28 | 22 | 0.0 | 0.0 | 329 | 282 | 39% / 47% / 25% / 69% |
| necromancer | 55 | 6 | 68 | 18 | 29 | 22 | 0.0 | 0.0 | 318 | 282 | 54% / 60% / 35% / 75% |
| necromancer | 60 | 2 | 60 | 13 | 25 | 21 | 0.3 | 0.0 | 357 | 332 | 10% / 44% / 15% / 76% |
| necromancer | 60 | 3 | 66 | 16 | 29 | 22 | 0.0 | 0.0 | 371 | 332 | 48% / 31% / 27% / 67% |
| necromancer | 60 | 6 | 62 | 16 | 25 | 21 | 0.0 | 0.0 | 392 | 332 | 51% / 32% / 38% / 71% |
| thief | 45 | 2 | 58 | 13 | 21 | 24 | 0.0 | 0.0 | 224 | 204 | - / 41% / 20% / 55% |
| thief | 45 | 3 | 63 | 15 | 23 | 25 | 0.0 | 0.0 | 245 | 204 | - / 39% / 24% / 73% |
| thief | 45 | 6 | 60 | 16 | 21 | 24 | 0.0 | 0.0 | 259 | 204 | - / 39% / 32% / 78% |
| thief | 50 | 2 | 51 | 11 | 18 | 23 | 0.0 | 0.0 | 309 | 240 | - / 24% / 21% / 60% |
| thief | 50 | 3 | 55 | 12 | 20 | 23 | 0.0 | 0.0 | 343 | 240 | - / 28% / 23% / 59% |
| thief | 50 | 6 | 57 | 13 | 20 | 24 | 0.0 | 0.0 | 354 | 240 | - / 50% / 32% / 75% |
| thief | 55 | 2 | 56 | 12 | 20 | 24 | 0.0 | 0.0 | 331 | 282 | - / 28% / 17% / 60% |
| thief | 55 | 3 | 60 | 14 | 23 | 24 | 0.0 | 0.0 | 369 | 282 | - / 39% / 24% / 68% |
| thief | 55 | 6 | 59 | 14 | 21 | 24 | 0.0 | 0.0 | 390 | 282 | - / 34% / 35% / 74% |
| thief | 60 | 2 | 59 | 12 | 22 | 25 | 0.0 | 0.0 | 417 | 332 | - / 23% / 23% / 72% |
| thief | 60 | 3 | 59 | 12 | 22 | 25 | 0.0 | 0.0 | 473 | 332 | - / 30% / 28% / 60% |
| thief | 60 | 6 | 57 | 12 | 21 | 24 | 0.0 | 0.0 | 504 | 332 | - / 54% / 35% / 70% |
| assassin | 45 | 2 | 58 | 15 | 25 | 17 | 0.0 | 0.0 | 285 | 204 | 20% / 32% / 19% / 60% |
| assassin | 45 | 3 | 63 | 18 | 27 | 18 | 0.0 | 0.0 | 312 | 204 | 35% / 41% / 26% / 75% |
| assassin | 45 | 6 | 59 | 18 | 24 | 17 | 0.0 | 0.0 | 326 | 204 | 35% / 48% / 29% / 76% |
| assassin | 50 | 2 | 62 | 15 | 30 | 18 | 0.0 | 0.0 | 387 | 240 | 24% / 42% / 16% / 61% |
| assassin | 50 | 3 | 58 | 15 | 26 | 17 | 0.0 | 0.0 | 413 | 240 | 43% / 47% / 27% / 52% |
| assassin | 50 | 6 | 60 | 16 | 26 | 17 | 0.0 | 0.0 | 433 | 240 | 35% / 54% / 28% / 75% |
| assassin | 55 | 2 | 60 | 15 | 27 | 18 | 0.0 | 0.0 | 415 | 282 | 11% / 41% / 16% / 64% |
| assassin | 55 | 3 | 60 | 16 | 26 | 18 | 0.0 | 0.0 | 460 | 282 | 36% / 42% / 28% / 63% |
| assassin | 55 | 6 | 60 | 17 | 25 | 17 | 0.0 | 0.0 | 474 | 282 | 47% / 47% / 35% / 72% |
| assassin | 60 | 2 | 59 | 14 | 27 | 18 | 0.0 | 0.0 | 560 | 332 | 21% / 39% / 25% / 58% |
| assassin | 60 | 3 | 60 | 15 | 27 | 18 | 0.0 | 0.0 | 598 | 332 | 44% / 47% / 31% / 56% |
| assassin | 60 | 6 | 61 | 16 | 27 | 18 | 0.0 | 0.0 | 647 | 332 | 53% / 38% / 32% / 72% |
| ranger | 45 | 2 | 67 | 15 | 27 | 25 | 0.0 | 0.0 | 189 | 204 | 26% / 33% / 25% / 62% |
| ranger | 45 | 3 | 70 | 18 | 27 | 25 | 0.0 | 0.0 | 198 | 204 | 41% / 52% / 26% / 74% |
| ranger | 45 | 6 | 70 | 19 | 27 | 25 | 0.0 | 0.0 | 201 | 204 | 43% / 48% / 39% / 74% |
| ranger | 50 | 2 | 68 | 14 | 29 | 25 | 0.0 | 0.0 | 253 | 240 | 31% / 30% / 21% / 62% |
| ranger | 50 | 3 | 65 | 14 | 25 | 25 | 0.0 | 0.0 | 268 | 240 | 37% / 37% / 24% / 59% |
| ranger | 50 | 6 | 72 | 17 | 30 | 25 | 0.0 | 0.0 | 286 | 240 | 42% / 36% / 29% / 72% |
| ranger | 55 | 2 | 64 | 14 | 25 | 24 | 0.0 | 0.0 | 276 | 282 | 32% / 57% / 17% / 61% |
| ranger | 55 | 3 | 68 | 16 | 27 | 24 | 0.0 | 0.0 | 293 | 282 | 46% / 35% / 28% / 63% |
| ranger | 55 | 6 | 67 | 17 | 26 | 24 | 0.0 | 0.0 | 302 | 282 | 51% / 39% / 37% / 73% |
| ranger | 60 | 2 | 68 | 14 | 29 | 25 | 0.0 | 0.0 | 339 | 332 | 48% / 37% / 28% / 60% |
| ranger | 60 | 3 | 65 | 14 | 26 | 24 | 0.0 | 0.0 | 365 | 332 | 41% / 29% / 30% / 55% |
| ranger | 60 | 6 | 67 | 16 | 26 | 25 | 0.0 | 0.0 | 384 | 332 | 35% / 51% / 38% / 69% |
| bard | 45 | 2 | 65 | 12 | 21 | 32 | 0.0 | 0.0 | 179 | 204 | - / 43% / 11% / 62% |
| bard | 45 | 3 | 65 | 14 | 20 | 31 | 0.0 | 0.0 | 186 | 204 | - / 52% / 22% / 70% |
| bard | 45 | 6 | 72 | 16 | 24 | 32 | 0.0 | 0.0 | 193 | 204 | - / 48% / 29% / 83% |
| bard | 50 | 2 | 64 | 11 | 21 | 32 | 0.0 | 0.0 | 244 | 240 | - / 39% / 11% / 60% |
| bard | 50 | 3 | 67 | 13 | 23 | 32 | 0.0 | 0.0 | 259 | 240 | - / 29% / 25% / 57% |
| bard | 50 | 6 | 65 | 13 | 21 | 32 | 0.0 | 0.0 | 273 | 240 | - / 43% / 33% / 73% |
| bard | 55 | 2 | 61 | 11 | 19 | 31 | 0.0 | 0.0 | 271 | 282 | - / 20% / 8% / 60% |
| bard | 55 | 3 | 62 | 12 | 19 | 31 | 0.0 | 0.0 | 297 | 282 | - / 45% / 24% / 63% |
| bard | 55 | 6 | 66 | 13 | 21 | 32 | 0.0 | 0.0 | 289 | 282 | - / 30% / 33% / 73% |
| bard | 60 | 2 | 61 | 10 | 19 | 31 | 0.0 | 0.0 | 336 | 332 | - / 41% / 14% / 59% |
| bard | 60 | 3 | 65 | 12 | 21 | 32 | 0.0 | 0.0 | 369 | 332 | - / 32% / 25% / 52% |
| bard | 60 | 6 | 61 | 12 | 17 | 31 | 0.0 | 0.0 | 367 | 332 | - / 45% / 33% / 75% |

### Real-time combat (the 3D client)

The same quests, with skills a second apart (`--mode action`).

| class | level | party | minutes in all | fighting | resting | on the way | deaths | fights lost (to) | hero damage/round | dpr() | health at worst: elite / warden / wave / boss |
|---|---|---|---|---|---|---|---|---|---|---|---|
| warrior | 45 | 1 | 61 | 18 | 8 | 34 | 0.3 | 0.3 (boss 0.3) | 292 | 204 | 36% / 32% / 19% / 71% |
| warrior | 45 | 3 | 76 | 18 | 25 | 33 | 0.0 | 0.0 | 319 | 204 | 41% / 57% / 24% / 68% |
| warrior | 55 | 1 | 58 | 17 | 8 | 33 | 0.0 | 0.0 | 455 | 282 | 38% / 35% / 22% / 53% |
| warrior | 55 | 3 | 72 | 15 | 24 | 32 | 0.0 | 0.0 | 510 | 282 | 44% / 44% / 27% / 55% |
| paladin | 45 | 1 | 63 | 18 | 26 | 19 | 0.0 | 0.0 | 202 | 204 | 48% / 42% / 19% / 56% |
| paladin | 45 | 3 | 65 | 18 | 27 | 20 | 0.0 | 0.0 | 238 | 204 | 46% / 64% / 31% / 71% |
| paladin | 55 | 1 | 65 | 17 | 27 | 20 | 0.0 | 0.0 | 308 | 282 | 50% / 48% / 19% / 60% |
| paladin | 55 | 3 | 63 | 16 | 27 | 19 | 0.0 | 0.0 | 356 | 282 | 47% / 40% / 33% / 59% |
| cleric | 45 | 1 | 66 | 20 | 27 | 20 | 0.0 | 0.0 | 148 | 204 | 20% / 52% / 20% / 64% |
| cleric | 45 | 3 | 66 | 18 | 28 | 20 | 0.0 | 0.0 | 177 | 204 | 46% / 56% / 32% / 76% |
| cleric | 55 | 1 | 64 | 17 | 26 | 20 | 0.3 | 0.3 (wave 0.3) | 240 | 282 | 24% / 50% / 20% / 72% |
| cleric | 55 | 3 | 59 | 16 | 24 | 19 | 0.0 | 0.0 | 277 | 282 | 37% / 48% / 32% / 63% |
| mage | 45 | 1 | 77 | 22 | 29 | 27 | 0.7 | 0.7 (boss 0.7) | 109 | 204 | 0% / 0% / 5% / 70% |
| mage | 45 | 3 | 67 | 18 | 26 | 23 | 0.0 | 0.0 | 127 | 204 | 37% / 53% / 23% / 71% |
| mage | 55 | 1 | 69 | 17 | 26 | 25 | 0.3 | 0.3 (boss 0.3) | 179 | 282 | 7% / 2% / 10% / 57% |
| mage | 55 | 3 | 65 | 16 | 26 | 23 | 0.0 | 0.0 | 212 | 282 | 40% / 41% / 27% / 61% |
| necromancer | 45 | 1 | 63 | 17 | 25 | 21 | 0.0 | 0.0 | 194 | 204 | 6% / 0% / 0% / 46% |
| necromancer | 45 | 3 | 67 | 18 | 27 | 22 | 0.0 | 0.0 | 211 | 204 | 26% / 50% / 23% / 72% |
| necromancer | 55 | 1 | 67 | 16 | 28 | 22 | 0.0 | 0.0 | 281 | 282 | 19% / 0% / 0% / 34% |
| necromancer | 55 | 3 | 67 | 16 | 28 | 22 | 0.0 | 0.0 | 307 | 282 | 26% / 43% / 25% / 72% |
| thief | 45 | 1 | 45 | 15 | 6 | 24 | 0.0 | 0.0 | 214 | 204 | - / 29% / 24% / 72% |
| thief | 45 | 3 | 63 | 15 | 23 | 25 | 0.0 | 0.0 | 237 | 204 | - / 31% / 25% / 74% |
| thief | 55 | 1 | 45 | 14 | 7 | 25 | 0.3 | 0.3 (boss 0.3) | 314 | 282 | - / 35% / 28% / 76% |
| thief | 55 | 3 | 61 | 14 | 23 | 24 | 0.0 | 0.0 | 371 | 282 | - / 35% / 26% / 63% |
| assassin | 45 | 1 | 44 | 18 | 8 | 19 | 0.3 | 0.3 (boss 0.3) | 311 | 204 | 33% / 25% / 17% / 75% |
| assassin | 45 | 3 | 62 | 17 | 27 | 18 | 0.0 | 0.0 | 314 | 204 | 35% / 42% / 23% / 71% |
| assassin | 55 | 1 | 46 | 18 | 10 | 18 | 0.0 | 0.0 | 424 | 282 | 40% / 40% / 24% / 79% |
| assassin | 55 | 3 | 60 | 15 | 26 | 18 | 0.0 | 0.0 | 467 | 282 | 40% / 41% / 25% / 58% |
| ranger | 45 | 1 | 70 | 18 | 27 | 25 | 0.3 | 0.3 (elite 0.3) | 190 | 204 | 52% / 53% / 31% / 58% |
| ranger | 45 | 3 | 70 | 17 | 28 | 25 | 0.0 | 0.0 | 200 | 204 | 31% / 56% / 24% / 66% |
| ranger | 55 | 1 | 70 | 18 | 28 | 25 | 0.0 | 0.0 | 272 | 282 | 49% / 51% / 35% / 66% |
| ranger | 55 | 3 | 67 | 16 | 27 | 24 | 0.0 | 0.0 | 293 | 282 | 42% / 38% / 29% / 61% |
| bard | 45 | 1 | 68 | 15 | 22 | 32 | 0.0 | 0.0 | 175 | 204 | - / 21% / 10% / 76% |
| bard | 45 | 3 | 66 | 14 | 21 | 31 | 0.0 | 0.0 | 186 | 204 | - / 29% / 24% / 69% |
| bard | 55 | 1 | 67 | 13 | 21 | 33 | 0.3 | 0.3 (boss 0.3) | 275 | 282 | - / 36% / 15% / 61% |
| bard | 55 | 3 | 63 | 12 | 20 | 31 | 0.0 | 0.0 | 295 | 282 | - / 53% / 25% / 59% |

## Time and the two-hour goal

The fights take what the design asks: an elite about a minute, a warden about two, a boss about
three. Around them, a lone hero who knows the way spends 6-30 minutes resting and 17-34 walking,
40-81 minutes in all. Thieves and assassins finish soonest: they have no mana to rest back.
Mages finish last.

That is efficient play by a player who knows the way. A first time through adds what the
simulation does not count: reading the stages, finding unfamiliar places, looting, and the odd
death and walk back.

If the quests still play short, one number moves them: `ROUNDS` in `marquee_scale.py`, the
rounds a lone hero needs for each kind of foe. Longer fights cost more health, so after changing
it run `--calibrate` again and copy the new `CLASS_D`.

## Rerunning

    python3 tools/balance/sim.py --levels 45,50,55,60 --party 1,2,3,6 --runs 3     # the tables above
    python3 tools/balance/sim.py --levels 45,55 --party 1,3 --mode action          # real-time combat
    python3 tools/balance/sim.py --calibrate --levels 45,50,55,60 --runs 8         # CLASS_K and CLASS_D
    python3 tools/balance/sim.py --classes mage --levels 45 --party 1 --verbose    # one quest, stage by stage
    python3 tests/test_balance.py                                                  # the fixes, and one quest simulated

`--foe-damage elite=1.5` and `--class-damage mage=0.8` try other values without editing the
code. Any creature turn that raises an error is printed once (`  ! ...`): those are the game's
own bugs.
