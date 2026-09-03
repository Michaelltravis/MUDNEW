# World Room Audit — June 11, 2026

*Question: did the build lose rooms from the large, comprehensive world
(especially Midgaard) that existed in February/March? Answer: **no** —
the repository never lost a room. What players saw was a runtime bug.*

## Method
Every zone file was diffed across the full git history of `world/zones/`:
- `d6d03c6` (Feb 19) — oldest commit containing world data
- `5862089` (Mar 17) — last world change before this branch
- `HEAD` (now)

Compared per zone: room vnum sets, room names, exit sets, description
lengths, mob/object prototypes, and reset counts. `origin/main` is an
ancestor of this branch (nothing newer exists elsewhere); there were no
world commits in April or May.

## Findings

| | Feb 19 | Mar 17 | Now |
|---|---|---|---|
| Zone files | 55 | 60 | 60 |
| Rooms | 2,828 | 3,012 | 3,012 |

- **Zero rooms lost.** Every February room exists today, by vnum, with
  identical names. March added 5 endgame zones (+184 rooms: Ashen
  Expanse, Drowned Reliquary, Black Observatory, Crown of Bone,
  Shattered Throne).
- **Midgaard (zone 30) is intact**: the same 75 rooms as February, zero
  renames, descriptions unchanged, all mob/object resets present.
- **No zone lost population**: mob prototypes, object prototypes and
  resets are intact or grown in all 60 zones.
- **The stables (3200–3203 → 3210–3213)**: the only renumbered vnums.
  In February the stables zone *collided* with the Midgaard river rooms
  (two zones defined the same vnums — which one existed in-game depended
  on file load order) and its exits were all `null` (unfinished). They
  now live at 3210–3213, fully wired off Temple Square, with their
  original descriptions. The river kept its vnums, byte-identical to
  February.
- **One vnum absent from the current world**: 3034 "Rental Room 3", and
  only in `zone_030_circlemud.json.bak` — a leftover of the *stub*
  world's inn (its door leads to what is the Pet Shop in the real
  Midgaard). Stub content, deliberately not restored.

## Why the world looked small in-game
The engine's default-world bootstrap used to **overwrite** the real zone
files with a 43-room starter world whenever it ran (it fired on the
hosting machine at some point). That replaced the 75-room Midgaard with
a 13-room stub and orphaned most of the world — which is exactly the
"we lost the comprehensive town" experience.

Fixed in this branch, twice over:
1. The bootstrap can no longer overwrite existing zone files, and a
   world that fails to load refuses to rebuild on top of the data
   (`world_builder.py`, `world.py`).
2. **Self-heal**: at startup the server canary-checks zone 30; if it is
   the stub, it restores `world/zones/` from git automatically and
   reloads (verified by deliberately corrupting a test environment).

Connectivity was separately audited and repaired on this branch: 3,009
of 3,012 rooms are walkable from the Temple (the other 3 are Limbo,
immortal-only by design), with zero dangling exits and zero duplicate
vnums.
