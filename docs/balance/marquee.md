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
- **Time:** a lone hero who knows the way plays a quest through in 40-72 simulated minutes
  (median 58). That is 12-20 minutes of fighting, 6-29 of resting and 17-33 of walking. See
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
  - `dpr(level)` is the median hero's damage a round, measured: 204 at level 45, 240 at 50,
    282 at 55, 332 at 60. It was a guess before (150 to 197).
  - `CLASS_K` is how a class's damage compares with the median, measured. Before, it was a
    guess with the mage at 1.1 and the warrior at 1.0; measured, they are 0.58 and 1.58.
    So a lone warrior's elites died in 31 s instead of 66, and a mage's took 82.
  - For a group, both are the mean over everyone who set out. The quest now records their
    classes when it is accepted.
- **Damage** (what the creature's blows and specials in `world/zones/zone_097.json` are
  multiplied by) = `FOE_DAMAGE[kind]` x `CLASS_D` x `LEVEL_D`^(level - 45) x the party's
  damage factor.
  - `FOE_DAMAGE`: elites 2.0, a ritual's waves 0.7, everything else 1.0.
  - `CLASS_D` is what the class can stand, measured: thief 0.55, necromancer 0.60, bard 0.70,
    mage 0.75, assassin 0.77, warrior 0.94, ranger 0.97, cleric 1.35, paladin 1.77. For a
    group it is the mean over who set out.
  - `LEVEL_D` is 1.018: creatures hit 1.8% harder a level above 45, because heroes grow sturdier.
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
  - With the 1.8%-a-level rise included, most classes come out nearly flat across levels,
    which is how the rise was chosen.
  - Two classes are set at their weakest level instead of the mean, since a death is the
    worst a quest can do:
    - the mage at 0.75 (its mean is 0.88; level 45, where the quests open, stands 0.75);
    - the necromancer at 0.60 (levels 45-60 stand 0.60, 0.86, 0.74 and 0.58; at the mean
      0.70 a level-60 necromancer died 1.6 times a quest). Its servant makes it
      all-or-nothing: safe while the bone knight stands, exposed when it falls.
  - A paladin's boss costs 55-68% of their health across shares from 1.0 to 2.3: it mends
    itself back up. The share is set where the curve crosses 65%, and deaths start only
    above 2.3.
  - A class's own damage depends a little on the creatures' health (a longer fight thins a
    hero's opening burst), so a class whose `CLASS_K` moved was measured again under its new
    value before its `CLASS_D` was found.

## Results

Three quests per row, rounds mode, `--dodge 0.6 --gear 0.75 --walk 4 --travel 1`. "Fights
lost" counts the fights the party had to go back for.

### Alone

| class | level | party | minutes in all | fighting | resting | on the way | deaths | fights lost (to) | hero damage/round | dpr() | health at worst: elite / warden / wave / boss |
|---|---|---|---|---|---|---|---|---|---|---|---|
| warrior | 45 | 1 | 60 | 19 | 7 | 33 | 0.0 | 0.0 | 279 | 204 | 36% / 23% / 17% / 89% |
| warrior | 50 | 1 | 54 | 16 | 6 | 33 | 0.0 | 0.0 | 402 | 240 | 27% / 24% / 20% / 41% |
| warrior | 55 | 1 | 58 | 17 | 7 | 33 | 0.0 | 0.0 | 441 | 282 | 28% / 35% / 23% / 61% |
| warrior | 60 | 1 | 55 | 15 | 6 | 33 | 0.0 | 0.0 | 568 | 332 | 22% / 35% / 24% / 60% |
| paladin | 45 | 1 | 56 | 18 | 18 | 19 | 0.0 | 0.0 | 229 | 204 | 23% / 54% / 17% / 66% |
| paladin | 50 | 1 | 53 | 16 | 18 | 20 | 0.0 | 0.0 | 323 | 240 | 8% / 47% / 14% / 66% |
| paladin | 55 | 1 | 54 | 17 | 17 | 20 | 0.0 | 0.0 | 341 | 282 | 23% / 40% / 19% / 63% |
| paladin | 60 | 1 | 48 | 17 | 11 | 19 | 0.0 | 0.0 | 380 | 332 | 60% / 55% / 31% / 76% |
| cleric | 45 | 1 | 66 | 20 | 27 | 20 | 0.0 | 0.0 | 155 | 204 | 8% / 41% / 18% / 63% |
| cleric | 50 | 1 | 59 | 15 | 25 | 19 | 0.0 | 0.0 | 225 | 240 | 9% / 33% / 12% / 67% |
| cleric | 55 | 1 | 62 | 17 | 25 | 20 | 0.0 | 0.0 | 249 | 282 | 11% / 39% / 15% / 79% |
| cleric | 60 | 1 | 58 | 15 | 25 | 19 | 0.0 | 0.0 | 326 | 332 | 14% / 44% / 13% / 64% |
| mage | 45 | 1 | 72 | 20 | 27 | 25 | 0.3 | 0.3 (boss 0.3) | 103 | 204 | 1% / 0% / 12% / 56% |
| mage | 50 | 1 | 63 | 16 | 24 | 23 | 0.0 | 0.0 | 136 | 240 | 0% / 0% / 0% / 43% |
| mage | 55 | 1 | 66 | 17 | 25 | 23 | 0.0 | 0.0 | 158 | 282 | 0% / 0% / 1% / 61% |
| mage | 60 | 1 | 66 | 16 | 27 | 23 | 0.0 | 0.0 | 207 | 332 | 0% / 2% / 4% / 68% |
| necromancer | 45 | 1 | 66 | 19 | 25 | 21 | 0.0 | 0.0 | 186 | 204 | 0% / 0% / 0% / 24% |
| necromancer | 50 | 1 | 63 | 15 | 26 | 22 | 0.0 | 0.0 | 277 | 240 | 7% / 0% / 0% / 0% |
| necromancer | 55 | 1 | 68 | 16 | 29 | 23 | 0.3 | 0.3 (boss 0.3) | 327 | 282 | 1% / 25% / 0% / 57% |
| necromancer | 60 | 1 | 66 | 15 | 28 | 23 | 0.3 | 0.3 (boss 0.3) | 411 | 332 | 3% / 0% / 0% / 33% |
| thief | 45 | 1 | 47 | 16 | 6 | 25 | 0.3 | 0.3 (boss 0.3) | 209 | 204 | - / 38% / 21% / 75% |
| thief | 50 | 1 | 45 | 13 | 6 | 25 | 0.0 | 0.0 | 280 | 240 | - / 38% / 19% / 73% |
| thief | 55 | 1 | 44 | 14 | 6 | 24 | 0.0 | 0.0 | 314 | 282 | - / 33% / 29% / 74% |
| thief | 60 | 1 | 43 | 13 | 6 | 24 | 0.0 | 0.0 | 390 | 332 | - / 27% / 25% / 64% |
| assassin | 45 | 1 | 42 | 18 | 6 | 18 | 0.0 | 0.0 | 309 | 204 | 30% / 29% / 20% / 45% |
| assassin | 50 | 1 | 40 | 16 | 7 | 18 | 0.0 | 0.0 | 403 | 240 | 33% / 26% / 19% / 41% |
| assassin | 55 | 1 | 45 | 18 | 9 | 18 | 0.0 | 0.0 | 429 | 282 | 32% / 41% / 31% / 72% |
| assassin | 60 | 1 | 41 | 15 | 9 | 17 | 0.0 | 0.0 | 577 | 332 | 43% / 30% / 27% / 84% |
| ranger | 45 | 1 | 67 | 17 | 26 | 24 | 0.0 | 0.0 | 191 | 204 | 56% / 54% / 34% / 58% |
| ranger | 50 | 1 | 69 | 16 | 28 | 25 | 0.0 | 0.0 | 251 | 240 | 54% / 56% / 28% / 60% |
| ranger | 55 | 1 | 70 | 17 | 27 | 25 | 0.0 | 0.0 | 275 | 282 | 56% / 59% / 33% / 67% |
| ranger | 60 | 1 | 65 | 16 | 24 | 24 | 0.0 | 0.0 | 331 | 332 | 59% / 56% / 37% / 55% |
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
| warrior | 45 | 2 | 75 | 16 | 26 | 33 | 0.0 | 0.0 | 299 | 204 | 38% / 41% / 11% / 56% |
| warrior | 45 | 3 | 76 | 18 | 25 | 33 | 0.0 | 0.0 | 322 | 204 | 42% / 60% / 25% / 76% |
| warrior | 45 | 6 | 82 | 20 | 28 | 33 | 0.0 | 0.0 | 339 | 204 | 45% / 53% / 30% / 77% |
| warrior | 50 | 2 | 73 | 13 | 26 | 34 | 0.0 | 0.0 | 430 | 240 | 37% / 31% / 23% / 54% |
| warrior | 50 | 3 | 79 | 16 | 29 | 34 | 0.0 | 0.0 | 451 | 240 | 32% / 30% / 21% / 52% |
| warrior | 50 | 6 | 76 | 16 | 26 | 33 | 0.0 | 0.0 | 462 | 240 | 46% / 47% / 32% / 70% |
| warrior | 55 | 2 | 73 | 14 | 26 | 33 | 0.0 | 0.0 | 469 | 282 | 30% / 34% / 20% / 54% |
| warrior | 55 | 3 | 72 | 15 | 24 | 32 | 0.0 | 0.0 | 496 | 282 | 39% / 38% / 25% / 54% |
| warrior | 55 | 6 | 76 | 17 | 26 | 33 | 0.0 | 0.0 | 517 | 282 | 48% / 45% / 37% / 72% |
| warrior | 60 | 2 | 71 | 13 | 25 | 33 | 0.0 | 0.0 | 601 | 332 | 20% / 40% / 18% / 63% |
| warrior | 60 | 3 | 74 | 15 | 26 | 33 | 0.0 | 0.0 | 620 | 332 | 45% / 59% / 23% / 47% |
| warrior | 60 | 6 | 77 | 16 | 28 | 34 | 0.0 | 0.0 | 664 | 332 | 39% / 55% / 30% / 73% |
| paladin | 45 | 2 | 62 | 15 | 27 | 20 | 0.0 | 0.0 | 248 | 204 | 3% / 46% / 12% / 62% |
| paladin | 45 | 3 | 65 | 18 | 27 | 20 | 0.0 | 0.0 | 254 | 204 | 35% / 48% / 28% / 77% |
| paladin | 45 | 6 | 65 | 19 | 26 | 20 | 0.0 | 0.0 | 262 | 204 | 36% / 63% / 34% / 76% |
| paladin | 50 | 2 | 62 | 14 | 28 | 20 | 0.0 | 0.0 | 336 | 240 | 9% / 28% / 10% / 60% |
| paladin | 50 | 3 | 59 | 15 | 25 | 20 | 0.0 | 0.0 | 354 | 240 | 31% / 42% / 27% / 58% |
| paladin | 50 | 6 | 67 | 17 | 30 | 20 | 0.0 | 0.0 | 362 | 240 | 40% / 56% / 32% / 76% |
| paladin | 55 | 2 | 58 | 14 | 25 | 19 | 0.0 | 0.0 | 364 | 282 | 3% / 42% / 7% / 65% |
| paladin | 55 | 3 | 62 | 16 | 27 | 19 | 0.0 | 0.0 | 382 | 282 | 36% / 68% / 27% / 64% |
| paladin | 55 | 6 | 62 | 17 | 26 | 19 | 0.0 | 0.0 | 399 | 282 | 52% / 44% / 36% / 73% |
| paladin | 60 | 2 | 63 | 15 | 28 | 20 | 0.0 | 0.0 | 399 | 332 | 20% / 25% / 15% / 62% |
| paladin | 60 | 3 | 60 | 15 | 26 | 19 | 0.0 | 0.0 | 453 | 332 | 40% / 60% / 30% / 63% |
| paladin | 60 | 6 | 63 | 16 | 26 | 20 | 0.0 | 0.0 | 465 | 332 | 62% / 53% / 39% / 74% |
| cleric | 45 | 2 | 61 | 16 | 25 | 19 | 0.0 | 0.0 | 175 | 204 | 1% / 50% / 7% / 61% |
| cleric | 45 | 3 | 66 | 18 | 28 | 20 | 0.0 | 0.0 | 181 | 204 | 39% / 51% / 30% / 75% |
| cleric | 45 | 6 | 66 | 20 | 27 | 20 | 0.0 | 0.0 | 190 | 204 | 51% / 63% / 41% / 79% |
| cleric | 50 | 2 | 63 | 14 | 29 | 20 | 0.0 | 0.0 | 245 | 240 | 2% / 22% / 3% / 58% |
| cleric | 50 | 3 | 63 | 16 | 28 | 20 | 0.0 | 0.0 | 255 | 240 | 47% / 54% / 32% / 57% |
| cleric | 50 | 6 | 64 | 16 | 28 | 20 | 0.0 | 0.0 | 267 | 240 | 48% / 43% / 41% / 75% |
| cleric | 55 | 2 | 58 | 14 | 25 | 19 | 0.0 | 0.0 | 269 | 282 | 12% / 23% / 6% / 55% |
| cleric | 55 | 3 | 60 | 16 | 24 | 19 | 0.3 | 0.0 | 285 | 282 | 47% / 38% / 42% / 60% |
| cleric | 55 | 6 | 64 | 17 | 27 | 19 | 0.0 | 0.0 | 292 | 282 | 52% / 54% / 42% / 73% |
| cleric | 60 | 2 | 57 | 13 | 25 | 19 | 0.0 | 0.0 | 347 | 332 | 7% / 28% / 13% / 62% |
| cleric | 60 | 3 | 63 | 15 | 28 | 20 | 0.0 | 0.0 | 363 | 332 | 38% / 45% / 32% / 60% |
| cleric | 60 | 6 | 68 | 17 | 31 | 20 | 0.0 | 0.0 | 381 | 332 | 50% / 48% / 41% / 71% |
| mage | 45 | 2 | 67 | 17 | 27 | 23 | 0.0 | 0.0 | 109 | 204 | 1% / 15% / 0% / 56% |
| mage | 45 | 3 | 67 | 18 | 26 | 23 | 0.0 | 0.0 | 116 | 204 | 42% / 41% / 23% / 68% |
| mage | 45 | 6 | 72 | 20 | 28 | 24 | 0.0 | 0.0 | 130 | 204 | 48% / 55% / 30% / 74% |
| mage | 50 | 2 | 64 | 14 | 27 | 23 | 0.3 | 0.0 | 152 | 240 | 3% / 19% / 2% / 71% |
| mage | 50 | 3 | 70 | 16 | 30 | 24 | 0.0 | 0.0 | 169 | 240 | 38% / 52% / 20% / 59% |
| mage | 50 | 6 | 67 | 16 | 27 | 24 | 0.0 | 0.0 | 172 | 240 | 36% / 44% / 38% / 71% |
| mage | 55 | 2 | 64 | 14 | 27 | 23 | 0.0 | 0.0 | 180 | 282 | 1% / 0% / 6% / 59% |
| mage | 55 | 3 | 65 | 16 | 26 | 23 | 0.0 | 0.0 | 193 | 282 | 40% / 31% / 25% / 70% |
| mage | 55 | 6 | 70 | 18 | 29 | 24 | 0.0 | 0.0 | 202 | 282 | 48% / 45% / 40% / 72% |
| mage | 60 | 2 | 62 | 13 | 25 | 23 | 0.0 | 0.0 | 221 | 332 | 6% / 12% / 7% / 56% |
| mage | 60 | 3 | 65 | 15 | 27 | 23 | 0.0 | 0.0 | 247 | 332 | 39% / 44% / 27% / 69% |
| mage | 60 | 6 | 63 | 15 | 25 | 23 | 0.0 | 0.0 | 260 | 332 | 44% / 44% / 35% / 69% |
| necromancer | 45 | 2 | 64 | 16 | 26 | 22 | 0.0 | 0.0 | 220 | 204 | 12% / 24% / 11% / 60% |
| necromancer | 45 | 3 | 68 | 19 | 27 | 22 | 0.0 | 0.0 | 217 | 204 | 28% / 38% / 21% / 69% |
| necromancer | 45 | 6 | 70 | 21 | 27 | 22 | 0.0 | 0.0 | 212 | 204 | 51% / 54% / 30% / 77% |
| necromancer | 50 | 2 | 63 | 13 | 28 | 22 | 0.0 | 0.0 | 303 | 240 | 6% / 56% / 11% / 61% |
| necromancer | 50 | 3 | 62 | 15 | 25 | 21 | 0.0 | 0.0 | 299 | 240 | 28% / 36% / 19% / 60% |
| necromancer | 50 | 6 | 64 | 17 | 25 | 21 | 0.0 | 0.0 | 296 | 240 | 38% / 51% / 33% / 74% |
| necromancer | 55 | 2 | 59 | 13 | 25 | 21 | 0.0 | 0.0 | 341 | 282 | 31% / 17% / 14% / 61% |
| necromancer | 55 | 3 | 67 | 17 | 28 | 22 | 0.0 | 0.0 | 322 | 282 | 48% / 39% / 22% / 75% |
| necromancer | 55 | 6 | 69 | 18 | 29 | 22 | 0.0 | 0.0 | 334 | 282 | 46% / 52% / 30% / 74% |
| necromancer | 60 | 2 | 59 | 12 | 25 | 21 | 0.3 | 0.0 | 424 | 332 | 22% / 46% / 12% / 77% |
| necromancer | 60 | 3 | 67 | 16 | 29 | 22 | 0.0 | 0.0 | 402 | 332 | 38% / 48% / 27% / 70% |
| necromancer | 60 | 6 | 62 | 16 | 25 | 21 | 0.0 | 0.0 | 413 | 332 | 46% / 30% / 31% / 71% |
| thief | 45 | 2 | 57 | 13 | 20 | 24 | 0.0 | 0.0 | 229 | 204 | - / 43% / 17% / 56% |
| thief | 45 | 3 | 63 | 15 | 23 | 25 | 0.0 | 0.0 | 245 | 204 | - / 31% / 28% / 71% |
| thief | 45 | 6 | 60 | 15 | 21 | 24 | 0.0 | 0.0 | 251 | 204 | - / 29% / 31% / 81% |
| thief | 50 | 2 | 51 | 11 | 18 | 23 | 0.0 | 0.0 | 301 | 240 | - / 32% / 17% / 61% |
| thief | 50 | 3 | 54 | 12 | 19 | 23 | 0.0 | 0.0 | 340 | 240 | - / 25% / 25% / 54% |
| thief | 50 | 6 | 58 | 13 | 21 | 24 | 0.0 | 0.0 | 347 | 240 | - / 41% / 32% / 72% |
| thief | 55 | 2 | 56 | 12 | 20 | 24 | 0.0 | 0.0 | 328 | 282 | - / 32% / 27% / 61% |
| thief | 55 | 3 | 60 | 13 | 23 | 24 | 0.0 | 0.0 | 378 | 282 | - / 32% / 26% / 66% |
| thief | 55 | 6 | 59 | 14 | 21 | 24 | 0.0 | 0.0 | 393 | 282 | - / 36% / 34% / 74% |
| thief | 60 | 2 | 60 | 12 | 23 | 25 | 0.0 | 0.0 | 408 | 332 | - / 38% / 23% / 55% |
| thief | 60 | 3 | 59 | 12 | 21 | 25 | 0.0 | 0.0 | 462 | 332 | - / 28% / 27% / 66% |
| thief | 60 | 6 | 57 | 13 | 20 | 24 | 0.0 | 0.0 | 495 | 332 | - / 40% / 36% / 73% |
| assassin | 45 | 2 | 58 | 15 | 25 | 17 | 0.0 | 0.0 | 284 | 204 | 22% / 40% / 16% / 60% |
| assassin | 45 | 3 | 62 | 18 | 27 | 18 | 0.0 | 0.0 | 315 | 204 | 29% / 51% / 23% / 73% |
| assassin | 45 | 6 | 59 | 18 | 24 | 17 | 0.0 | 0.0 | 328 | 204 | 40% / 53% / 32% / 74% |
| assassin | 50 | 2 | 62 | 15 | 30 | 18 | 0.0 | 0.0 | 392 | 240 | 18% / 21% / 14% / 62% |
| assassin | 50 | 3 | 59 | 15 | 26 | 17 | 0.0 | 0.0 | 406 | 240 | 29% / 41% / 27% / 53% |
| assassin | 50 | 6 | 60 | 16 | 26 | 17 | 0.0 | 0.0 | 441 | 240 | 40% / 52% / 35% / 72% |
| assassin | 55 | 2 | 60 | 15 | 27 | 18 | 0.0 | 0.0 | 412 | 282 | 23% / 39% / 19% / 66% |
| assassin | 55 | 3 | 60 | 16 | 26 | 18 | 0.0 | 0.0 | 465 | 282 | 34% / 52% / 28% / 66% |
| assassin | 55 | 6 | 60 | 17 | 25 | 17 | 0.0 | 0.0 | 470 | 282 | 40% / 61% / 37% / 74% |
| assassin | 60 | 2 | 59 | 14 | 27 | 18 | 0.0 | 0.0 | 543 | 332 | 27% / 41% / 21% / 66% |
| assassin | 60 | 3 | 60 | 15 | 27 | 18 | 0.0 | 0.0 | 620 | 332 | 40% / 46% / 32% / 59% |
| assassin | 60 | 6 | 61 | 16 | 27 | 18 | 0.0 | 0.0 | 644 | 332 | 47% / 43% / 42% / 68% |
| ranger | 45 | 2 | 68 | 15 | 28 | 25 | 0.0 | 0.0 | 184 | 204 | 18% / 39% / 22% / 60% |
| ranger | 45 | 3 | 71 | 18 | 28 | 25 | 0.0 | 0.0 | 196 | 204 | 50% / 52% / 26% / 72% |
| ranger | 45 | 6 | 70 | 19 | 27 | 25 | 0.0 | 0.0 | 205 | 204 | 48% / 51% / 34% / 76% |
| ranger | 50 | 2 | 68 | 14 | 29 | 25 | 0.0 | 0.0 | 251 | 240 | 29% / 31% / 22% / 55% |
| ranger | 50 | 3 | 65 | 15 | 26 | 25 | 0.0 | 0.0 | 263 | 240 | 31% / 44% / 24% / 60% |
| ranger | 50 | 6 | 72 | 17 | 31 | 25 | 0.0 | 0.0 | 281 | 240 | 39% / 49% / 32% / 74% |
| ranger | 55 | 2 | 64 | 14 | 25 | 24 | 0.0 | 0.0 | 271 | 282 | 25% / 42% / 18% / 58% |
| ranger | 55 | 3 | 68 | 16 | 27 | 24 | 0.0 | 0.0 | 292 | 282 | 35% / 50% / 25% / 57% |
| ranger | 55 | 6 | 67 | 17 | 26 | 24 | 0.0 | 0.0 | 298 | 282 | 48% / 52% / 38% / 74% |
| ranger | 60 | 2 | 68 | 14 | 30 | 25 | 0.0 | 0.0 | 342 | 332 | 27% / 57% / 23% / 56% |
| ranger | 60 | 3 | 65 | 14 | 26 | 24 | 0.0 | 0.0 | 378 | 332 | 34% / 38% / 27% / 57% |
| ranger | 60 | 6 | 68 | 16 | 27 | 25 | 0.0 | 0.0 | 378 | 332 | 52% / 50% / 39% / 73% |
| bard | 45 | 2 | 65 | 13 | 21 | 32 | 0.0 | 0.0 | 179 | 204 | - / 56% / 8% / 57% |
| bard | 45 | 3 | 65 | 14 | 20 | 31 | 0.0 | 0.0 | 186 | 204 | - / 52% / 25% / 71% |
| bard | 45 | 6 | 72 | 16 | 24 | 32 | 0.0 | 0.0 | 193 | 204 | - / 47% / 30% / 74% |
| bard | 50 | 2 | 64 | 11 | 21 | 32 | 0.0 | 0.0 | 246 | 240 | - / 23% / 5% / 61% |
| bard | 50 | 3 | 68 | 12 | 23 | 32 | 0.0 | 0.0 | 259 | 240 | - / 39% / 24% / 53% |
| bard | 50 | 6 | 65 | 13 | 21 | 32 | 0.0 | 0.0 | 265 | 240 | - / 41% / 26% / 73% |
| bard | 55 | 2 | 61 | 11 | 19 | 31 | 0.0 | 0.0 | 268 | 282 | - / 36% / 7% / 56% |
| bard | 55 | 3 | 62 | 12 | 19 | 31 | 0.0 | 0.0 | 285 | 282 | - / 45% / 26% / 59% |
| bard | 55 | 6 | 66 | 13 | 21 | 32 | 0.0 | 0.0 | 296 | 282 | - / 46% / 33% / 74% |
| bard | 60 | 2 | 60 | 10 | 19 | 31 | 0.0 | 0.0 | 345 | 332 | - / 38% / 12% / 65% |
| bard | 60 | 3 | 65 | 12 | 22 | 32 | 0.0 | 0.0 | 372 | 332 | - / 41% / 27% / 55% |
| bard | 60 | 6 | 60 | 12 | 17 | 31 | 0.0 | 0.0 | 380 | 332 | - / 48% / 26% / 67% |

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
three. Around them, a lone hero who knows the way spends 6-29 minutes resting and 17-33 walking,
40-72 minutes in all. Thieves and assassins finish soonest: they have no mana to rest back.
Rangers, mages and necromancers finish last.

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
