# Zones, measured

`tools/balance/zones.py` takes a hero or a party through a zone room by room and fights what lives there. It uses
the game's own combat code on a simulated clock, the same heroes and rotation as `tools/balance/sim.py`, and rests
back to full between fights.

**What the columns mean**
- **Median fight / worst fight:** the share of a hero's health a fight took at its worst moment. A death counts as
  all of it.
- **Deaths:** how many heroes died over the whole clear.

All heroes are level 60 unless a section says otherwise. That is the mortal cap (`Config.MAX_MORTAL_LEVEL`), so
creatures above it are raid content.

## The build-out count fix (every creature as many times as written)

The build-out had placed each creature once per zone, whatever its count. Fixing that adds 834 creatures to the
world at load: 2,387 rising to 3,221.

The six zones it filled most, each fought at the median level of its foes:

| Zone (creatures added) | Foes then → now | Lone hero, median fight | Lone deaths over the clear | Party of three |
|---|---|---|---|---|
| 512 Orc Tunnels, without Morkai (+94) | 18 → 81 | warrior 15%, cleric 0%, mage 0% | 3, 0, 1 | no deaths, worst 28% |
| 408 Trade Road (+76) | about 1 → 71 | 21%, 0%, 0% | 9, 5, 8 | 2 deaths |
| 435 MiNar I (+67) | 2 → 43 | 17%, 0%, 0% | 5, 0, 5 | no deaths, worst 70% |
| 120 Sea of Storms (+42) | 1 → 61 | 55%, 0%, 0% | 17, 10, 15 | 3 deaths |
| 509 Durmandel Mines I (+23) | 5 → 30 | 10%, 0%, 0% | 0, 0, 2 | no deaths, worst 14% |
| 451 Mira Retrum II (+22) | 2 → 10 | 27%, 0%, 0% | 3, 3, 3 | no deaths, worst 71% |

**The fix didn't make fights harder, only more numerous.** The median fight is as cheap as before.

**The deaths are to the same named and elite creatures** that killed lone heroes under the old cap: the owlbear,
the frost sea serpent, the Ice Leviathan, the shades of Carcosa, Orschnag, the High Priest of Terror and the outlaw
captains. A lone hero at the middle level of a zone whose range runs well above it isn't meant to beat them; a
party of three nearly always does.

**No zone needed tuning for the fix.** One thing to watch: the build-out can place two strong creatures in one room,
such as a captain beside its boss, or a priest beside its effigy.

## Dead Morkai against Crown of Bone (level 60)

Dead Morkai (the city and its tombs, creatures of levels 60–68) should sit just below Crown of Bone, the other
end-game zone.

**As first built, it was far softer.**
- Its ordinary creatures had 1,500 hp on the world curve, against 4,400 in Crown of Bone. A lone mage's median fight
  cost 0%, against Crown's 22%.
- A party of three beat Gorbash with nobody below 22% health.

**Tuned** (`world/population/zone_512.json`, `zone_514.json`):
- ordinary creatures have 1.75× health (about 2,700–3,150);
- Gorbash and Moloch have 22,000 hp, and their abilities hit about 25% harder.

| Lone hero, median fight | Crown of Bone | Morkai before | Morkai after |
|---|---|---|---|
| Warrior | 63% | 39% | 62% |
| Thief | 37% | 29% | 37% |
| Mage | 22% | 0% | 0% |
| Paladin | 6% | 0% | 2% |
| Cleric | 2% | 0% | 0% |
| **Party of three** | 3 deaths at the Sovereign | worst 78% | worst 84%, no deaths |

The tombs, after tuning:
- a party's worst moment is 82%, at Moloch;
- lone heroes die to Moloch and to Imrael with his mirror wraith.

Ordinary fights now cost what Crown of Bone's do. The bosses still need a group: Gorbash, Vrakk and Moloch kill lone
heroes, while a party of three survives them close to the edge, just short of the Sovereign.

**A fix found on the way:** a population entry that stated its own health beside a rank (`population.apply`) failed
with a duplicate key, and the whole zone's entries were silently dropped. Stated numbers now win over the rank's.

```
python3 tools/balance/zones.py --busiest 6 --compare --exclude 13828-13899
python3 tools/balance/zones.py --rooms 13828,13831-13848,13884-13899 --name "Dead Morkai" --levels 60 --classes warrior,cleric,mage,thief,paladin
python3 tools/balance/zones.py --zones 295 --levels 60 --classes warrior,cleric,mage,thief,paladin      # Crown of Bone
```
