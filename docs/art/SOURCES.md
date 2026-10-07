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
