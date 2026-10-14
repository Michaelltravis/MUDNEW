# Rites of passage, and how full the world is

The owner asked for three things:
- an audit of every zone for creature density;
- the Island of the Dead to have mini-bosses before its doors that drop the keys;
- crossing with Charon to be a conversation and a coin.

This page says what was built, where it is used, and how to use it in more places.

## The audit
`tools/audit/density.py` loads the world as the game does and counts, per zone:
- rooms a body can walk;
- creatures at load, all of them and the hostile ones;
- hostile creatures per walkable room, and empty rooms;
- the foes' level band;
- doors, locked doors, and locked doors whose key nothing in the world provides.

The table is in [density.md](density.md).

**Before:** 63 of 124 zones were thin, with fewer than 0.35 hostile creatures per walkable room. The worst cases:
- the Tunnel of Sticks: 3 foes in 101 rooms;
- the Island of the Dead: 25 in 75;
- Trade Road: 71 in 466.

Almost no door in the world was locked.

**The fill.** `tools/audit/densify.py --write` adds more of each thin zone's own ordinary creatures to its empty rooms, near where those creatures already live. The rules:
- Water creatures go to water and land creatures to land.
- No creature is placed in a peaceful room, a shop, a death trap or a god room.
- One-of-a-kind creatures stay one: named creatures, "the ...", bosses, sentinels and shopkeepers.
- A guard post a zone's population places on purpose (a `spawns` group of three rooms or fewer, such as the myconid sentries) keeps its number.
- The aim is 0.45 hostile creatures per walkable room, and 0.25 on a road or open plain between places.
- The fills are written as `"fill"` entries in `world/population/zone_<n>.json`. `population.py` applies them at load and raises every reset of that creature in the zone to the new total.
- The tool plans from the world without fills, so running it again gives the same answer.

**After:** 1,227 more creatures across 52 zones. Twelve zones are still under the line, each on purpose:

| Kind of zone | Zones |
|---|---|
| Travel zones, at their lower aim | Trade Road, Plains |
| Monster towns full of peaceful inhabitants | Drow City, Orc Enclave, High Tower I and II |
| Small zones whose few foes are elites | Quickstream, King's Forest |
| Puzzle houses with one guardian a room | Rand's Tower, Redferne's Residence |
| An empty tunnel | the pit of Minos |
| No more free rooms near its creatures | Mountain Range |

**Balance.** The fill adds more fights, not harder ones. `tools/balance/zones.py --zones 521,210`:
- **The Winterwood (level 14, now 31 foes):** a party of three loses no one, and its worst moment costs 42%. A lone warrior at the zone's median level dies 5 times in 30 fights, to its level-20 foes.
- **The Tunnel of Sticks (level 35, now 46 foes):** a party's worst moment costs 15%, and lone heroes nearly always win.

## Rites of passage (`src/rites.py`, `world/rites.json`)

### Gates
A door locked by a key that its **gatekeeper**, a mini-boss standing before it, carries:
- Kill the keeper and take the key from the corpse. The key opens that one door and **crumbles in the lock**.
- The door is **warded**: no pick, no bash and no break-door spell opens it.
- The zone's reset locks it again, and the keeper comes back with a fresh key.

A keeper can be any of these:
- an existing creature (`"keeper": 6401`);
- a mini-boss made for the door from one of the zone's own creatures (`"keeper": {"from": 5104, "room": 5140, "short_desc": ..., "level": 22}`), copied with sub-boss rank;
- a build-out creature placed exactly (`"at": [room vnums]` in a part).

### Tolls
A ferryman, bargeman or gate-warden who carries you across for a fare:
- **Talking:** `talk charon`, or the Talk window. His words, the fare as a choice, a question to ask, a way to leave.
- **Paying:** `pay charon`, `give 1 gold charon` or `give coin charon`.
- **The crossing:** the via room for a few seconds, with lines of the journey, then the far side.
- **No fighting:** toll-keepers are `no_attack`.
- **Barred ways:** a `bars` entry closes a way a body cannot walk, such as the Styx. The ferryman's words go on the bar; the bar is built at load and never saved.

`give <n> gold <anyone>` now works for everyone, not just toll-keepers.

## Where they are used

### The Island of the Dead (zone 495)
- **Charon** waits at the wharf before the Styx (3772), and the Styx can no longer be walked. The fare is one coin, and he answers questions about what lies beyond. The **hollow oarsman** rows the living back from the far landing (3774).
- **Ten gatekeepers:**
  - the Necropolis Warden (temple door);
  - the Sphinx (the Oracle's chamber);
  - the Siren (Aphrodite's altar);
  - **Cerberus** (the gates of Hades);
  - the Wardens of the White, Gray and Black Gates;
  - the Furies **Alecto, Megaera and Tisiphone** (the fiery, icy and misty doors).
- **Hades** waits on the onyx throne (boss, drops the Helm of Darkness).
- **New regulars:** forest lamias, temple acolyte shades, wailing shades and hounds of Hades.
- **Totals:** 25 creatures before, 77 now.

### Sixteen more boss approaches
Each has a mini-boss with the key before the last door to the boss:
- Drow City (the Temple Warden of Lloth);
- Great Pyramid (the Tomb Guardian);
- Arachnos (the Brood Warden);
- Haunted Swamp (Old Snapjaw);
- Troglodyte Mines;
- Mahn-Tor Keep;
- Castle of Ostragoth;
- Salem's Lot;
- Morvoct;
- Phaeton's Academy;
- Durmandel I (the Gatestone);
- Lost Crypt II (the Blood Herald);
- Morkai (the Throne Warden);
- the Winterlands (the Frost Herald);
- Rand's Tower (the Demon of Decay);
- the Orc Enclave (the Huntmaster).

Four candidate gates were left out because the boss can be reached another way: Sea of Storms, Garathorm Cathedral, Castle Varok and Below Moria.

### The river barge
An old bargeman at Garathorm's Quay (3049) poles you up the river and through the mountain rapids to the tunnel landing (5002) for five gold. A bargewoman brings you back. Before this, the only way along the river was a raft costing about a thousand gold.

## Ideas for more
- **Riddles:** the Sphinx could ask one before she fights. A dialogue choice with the right answer opens the door without the fight (a `gate` effect from dialogue).
- **Bandit tolls:** the old toll booth on Trade Road (2346) could hold road-wardens who ask a toll. Pay and pass, or refuse and fight; unlike a ferryman they can be fought.
- **Offerings:** an altar that takes an item (`give feather altar`) to open a sealed way. The "grey feather of the dead" on the island is a natural one for the Judge's chambers.
- **Keys that open more:** a dungeon's master key, dropped by its sub-boss, opens every gate in that dungeon for one run.
- **Hiring a guide:** pay a guide at a maze's edge to lead you through, as a timed escort.

## Tests
- `tests/test_rites.py`: the Styx crossing both ways, the fare refused without gold, Charon unattackable, a gate's locks, its keeper and key, the key crumbling, and the reset re-locking.
- `tests/test_buildout.py`: counts a keeper's carried key as dropped.
