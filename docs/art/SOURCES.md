# Art sources (Phase A style lock)

Style lock: **Foozle "Lucifer" collection** (dark fantasy, 32px tiles, 48px four-direction
actors, matching UI/effects/items). Every adopted pack is CC0 (Creative Commons Zero 1.0);
each pack's `Readme.txt` with the license statement is committed beside its PNGs under
`src/web_isometric/art/<pack>/`. Aseprite sources and the 10K-pixel mockups are not committed.
Tooling: `tools/art_manifest.py` scans the folder and writes `src/web_isometric/art/manifest.json`.

| Pack | Covers | Source |
|---|---|---|
| lucifer-exterior-tileset | dark forest, graveyard, castle walls, dirt roads, banners (32px atlas 40x8) | https://foozlecc.itch.io/lucifer-exterior-tileset |
| lucifer-dungeon-tileset | stone dungeon, carpets, doors, torches (21x8) | https://foozlecc.itch.io/lucifer-dungeon-tileset |
| lucifer-lava-dungeon-tileset | lava halls, animated doors, flags, torches | https://foozlecc.itch.io/lucifer-lava-dungeon-tileset |
| cave-and-desert-tileset | cave and desert tiles, palms, torches, hazards | https://foozlecc.itch.io/cave-and-desert-tileset |
| green-valley-tileset (16px) | grassland accents, reserve | https://foozlecc.itch.io/green-valley-tileset |
| lucifer-warrior / necromancer / sorceress | hero sheets: idle, walk/run, 3 attacks, hurt, death, 4 directions | https://foozlecc.itch.io/lucifer-warrior (and -necromancer, -sorceress) |
| legend-main-character (64px, reserve) | one hero, 25+ animations, 3 colours; different artist, kept as reserve | https://foozlecc.itch.io/legend-main-character |
| lucifer-skeleton-{grunt,hunter}-enemy, -{king,ancient}-boss | undead | https://foozlecc.itch.io/lucifer-skeleton-grunt-enemy etc. |
| lucifer-goblin-{slinger,berserker}-enemy, -{rider,beast}-boss | goblins | https://foozlecc.itch.io/lucifer-goblin-slinger-enemy etc. |
| lucifer-cultist-enemy, lucifer-possessed-enemy | humanoid casters / possessed | https://foozlecc.itch.io/lucifer-cultist-enemy |
| lucifer-rpg-ui, rpg-ui-set-1 | HUD, boss bars, buttons, icons, fonts, login/menu backgrounds | https://foozlecc.itch.io/lucifer-rpg-ui |
| lucifer-effects, pixel-magic-sprite-effects | hit, slash, magic FX strips | https://foozlecc.itch.io/lucifer-effects |
| lucifer-equipment, lucifer-pickups | item/equipment icons, pickups | https://foozlecc.itch.io/lucifer-equipment |
| trap-pack | 30 animated traps | https://foozlecc.itch.io/trap-pack |

Evaluated, not adopted: Kenney Tiny Town / Tiny Dungeon (CC0, 16px; bright cartoon style clashes
with Lucifer), Pixel Frog Tiny Swords (custom licence, not CC0, 64px bright style),
0x72 DungeonTileset II (CC0, 16px, no attack animations). Failed to fetch: lucifer-desert-tileset
(retry later; the world has one desert room).

Kept from before: the procedural painterly ground (`painter.js`) stays as the base layer; Lucifer
tiles are used for walls, props, doors and decor on top of it. LPC paperdolls and DCSS creature
sprites remain as fallbacks until every class and mob archetype is mapped (see `roles.json`).

## Decisions after the search for beast and extra hero sheets (2026-10-07)
- **Beasts and non-humanoid monsters keep the CC0 DCSS creature art.** No CC0 top-down animal
  pack with four-direction animation exists in a matching style; the candidates found were
  CC-BY (Reemax giant spider, LPC rat/cat/dog, AntumDeluge rodents), paid (PidrouDays bear), or
  16px cartoon (Tiny Creatures). DCSS art already sits inside the actor pipeline with outlines
  and scale rules, and the style-01 critic did not flag it.
- **Five classes stay recolours of the three Lucifer silhouettes** (warrior, sorceress,
  necromancer) until a sheet in the same style is commissioned. CC0 alternatives found were
  16px idle-only (PixeLike) or AI-generated / non-CC0 (Pixel Heroes, Tiny Questers).
  Recolours are distinct at a glance (see `class-lineup.png`); the gap is silhouette variety.

# 3D client art (`/play`, docs/REBUILD_PLAN.md engine section)

Style: stylised low-poly 3D. Every pack is **CC0 1.0**; each pack's licence file is copied to
`src/web_isometric/art3d/licenses/`. `tools/art3d/fetch.sh` downloads the sources (not
committed) and `tools/art3d/build.mjs` builds the optimised files in `src/web_isometric/art3d/`:
characters without animations (~150 KB each), one shared animation file for the common
41-joint rig (`chars/rig_anims.glb`, 68 clips), and kits (many props in one file, textures
stored once, meshopt-compressed).

| Pack | Author | Covers | Source |
|---|---|---|---|
| KayKit Character Pack: Adventurers 1.0 | Kay Lousberg | Knight, Barbarian, Mage, Rogue, Rogue (hooded), weapons/shields/hats; 75 animations | https://kaylousberg.itch.io/kaykit-adventurers (mirror: github.com/KayKit-Game-Assets/KayKit-Character-Pack-Adventures-1.0) |
| KayKit Character Pack: Skeletons 1.0 | Kay Lousberg | skeleton warrior, mage, rogue, minion; 95 animations (superset, same rig) | https://kaylousberg.itch.io/kaykit-skeletons (mirror: github.com/KayKit-Game-Assets/KayKit-Character-Pack-Skeletons-1.0) |
| KayKit Dungeon Remastered 1.0 | Kay Lousberg | walls, floors, pillars, torches, barrels, crates, chests, rubble, stairs (37 used of 200+) | https://kaylousberg.itch.io/kaykit-dungeon-remastered (mirror: github.com/KayKit-Game-Assets/KayKit-Dungeon-Remastered-1.0) |
| Stylized Nature MegaKit (standard) | Quaternius | trees, pines, dead trees, bushes, ferns, grass, flowers, rocks, pebbles (26 used) | https://opengameart.org/content/stylized-nature-megakit, https://quaternius.com |

Build notes: the nature kit's COLOR_0 (wind masks for Quaternius' own shader) is dropped
because glTF multiplies it into the colour; its bushes use the twisted tree's autumn-red leaf
atlas, which the build remixes to green; normal maps are dropped and textures resized to 512.
Candidates for later milestones (CC0): Quaternius Animated Monster Pack (OpenGameArt), KayKit
Medieval Hexagon, Halloween Bits and Furniture Bits (GitHub mirrors).
