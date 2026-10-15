# Room text audit (generated)

`python3 tools/audit/room_text.py --md docs/world/room_text_audit.md` writes this from the world as it loads. 124 zones, 9251 rooms; 4574 rooms (49%) name something standing in them; 138 rooms drawn against their text (roofed look, open text 78, town look, no town 34, open look, roofed text 26).

Most named: ash 624, lantern 541, bones 496, pillar 427, table 408, banner 407, shelf 308, bed 287, chains 283, bench 277, brazier 272, blood 206, rubble 195, grave 192, candle 182, flowers 165, skull 165, rug 161, standing_stone 142, barrel 117, torch 116, altar 113, mushroom 112, throne 112, crate 112, crystal 108, pole 98, well 84, chest 83, statue 81, cairn 79, fence 66, drum 60, cage 58, stake 56, weapons 48, coffin 48, fountain 47, tent 42, dead_tree 35.

See [room_visuals.md](room_visuals.md) for the plan.

| zone | name | rooms | looks | wrongly drawn | rooms naming features | most named |
|---|---|---|---|---|---|---|
| 54 | New Thalos | 285 | city 82, inside 78, water_noswim 51 | town look, no town: 8 | 18% | table 8, rug 6, bench 6, flowers 6 |
| 290 | The Black Observatory | 36 | inside 29, mountain 6, castle 1 | roofed look, open text: 8 | 33% | ash 9, well 4 |
| 455 | Gondor Island | 16 | inside 10, forest 3, water_swim 1 | roofed look, open text: 7 | 43% | rubble 4, pillar 2, shelf 1, crystal 1 |
| 30 | Garathorm Inner City | 213 | inside 104, city 92, garden 8 | town look, no town: 5, open look, roofed text: 1 | 31% | lantern 20, banner 18, well 6, table 6 |
| 481 | Ghenna | 86 | cave 43, city 22, inside 13 | town look, no town: 5, roofed look, open text: 1 | 45% | blood 12, bones 11, table 5, rubble 4 |
| 488 | Tunnels of Sin | 85 | cave 76, inside 5, crypt 4 | roofed look, open text: 6 | 57% | pillar 18, bones 11, ash 7, banner 6 |
| 512 | Orc Tunnels | 450 | cave 254, mine 49, city 27 | roofed look, open text: 5, town look, no town: 1 | 63% | ash 59, bones 38, pillar 34, lantern 31 |
| 504 | Elvandar | 69 | inside 35, forest 34 | open look, roofed text: 4, roofed look, open text: 1 | 78% | lantern 28, table 14, bench 9, shelf 8 |
| 431 | Garathorm Cathedral | 73 | crypt 27, inside 27, field 18 | open look, roofed text: 2, roofed look, open text: 2 | 68% | bench 12, grave 11, bones 9, banner 7 |
| 439 | Mount Olympus | 66 | inside 30, mountain 21, terrace 8 | roofed look, open text: 2, open look, roofed text: 2 | 77% | table 18, throne 16, pillar 14, ash 5 |
| 480 | Salem's Lot | 82 | inside 30, city 21, field 15 | town look, no town: 3, open look, roofed text: 1 | 70% | table 10, fence 10, lantern 9, chains 8 |
| 508 | Durmandel II | 32 | inside 18, field 5, crypt 3 | open look, roofed text: 2, roofed look, open text: 2 | 81% | banner 7, grave 6, table 4, bones 4 |
| 25 | High Tower Of Magic I | 98 | inside 85, forest 12, field 1 | roofed look, open text: 3 | 21% | table 7, bed 6, rug 3, shelf 3 |
| 72 | Sewer | 196 | sewer 174, cave 17, water_swim 3 | roofed look, open text: 3 | 13% | bones 14, torch 7, skull 7, bed 3 |
| 120 | Sea of Storms | 350 | water_noswim 89, inside 67, water_swim 48 | roofed look, open text: 2, town look, no town: 1 | 44% | lantern 27, table 22, pillar 21, ash 17 |
| 408 | Trade Road | 574 | forest 240, city 106, inside 83 | roofed look, open text: 2, town look, no town: 1 | 48% | ash 42, brazier 32, lantern 30, table 27 |
| 419 | Mishrak | 94 | inside 38, city 35, forest 7 | town look, no town: 3 | 71% | lantern 17, candle 13, table 12, ash 11 |
| 476 | Stone Circle | 94 | stones 67, inside 12, forest 8 | open look, roofed text: 3 | 92% | standing_stone 54, altar 20, bones 11, ash 10 |
| 60 | Plains | 187 | forest 110, field 34, water_noswim 14 | town look, no town: 2 | 28% | rug 26, flowers 6, bones 5, dead_tree 4 |
| 66 | Northern Wilderness | 66 | snow 57, cave 4, mountain 3 | open look, roofed text: 2 | 42% | grave 5, pole 5, bones 5, brazier 4 |
| 186 | Newbie Zone | 41 | inside 38, city 1, field 1 | town look, no town: 1, roofed look, open text: 1 | 21% | mushroom 7, statue 1, banner 1 |
| 238 | The Haunted Monastery | 25 | crypt 12, inside 10, field 2 | roofed look, open text: 2 | 84% | rubble 4, blood 4, bones 4, table 4 |
| 248 | The Clockwork Foundry | 30 | cave 29, inside 1 | roofed look, open text: 2 | 26% | chest 2, bones 2, cage 2, table 1 |
| 414 | Strange Garden | 34 | field 24, inside 8, forest 2 | open look, roofed text: 2 | 79% | flowers 13, bed 10, grave 6, bench 6 |
| 436 | Baron Kalveh's Fief | 95 | inside 62, field 17, city 10 | roofed look, open text: 2 | 85% | table 18, grave 13, ash 11, brazier 11 |
| 479 | Ancalador | 55 | cave 48, crypt 4, hills 2 | roofed look, open text: 2 | 36% | bones 5, skull 4, candle 4, blood 3 |
| 501 | Aredrel Dwarven | 99 | cave 59, field 12, inside 12 | open look, roofed text: 1, roofed look, open text: 1 | 84% | lantern 32, grave 13, crystal 11, bench 10 |
| 505 | Lost Crypt I | 107 | crypt 93, cave 14 | roofed look, open text: 2 | 64% | bones 25, ash 14, lantern 7, banner 6 |
| 515 | Orcus Temple | 29 | inside 20, castle 5, city 4 | town look, no town: 2 | 89% | skull 7, banner 7, bones 6, lantern 6 |
| 519 | White Gold Cathedral | 100 | inside 97, field 2, forest 1 | roofed look, open text: 2 | 80% | lantern 17, bed 17, bench 16, ash 16 |
| 0 | Limbo - Internal | 3 | city 2, inside 1 | town look, no town: 1 | 0% | - |
| 15 | The Straight Path | 41 | inside 35, field 5, hills 1 | roofed look, open text: 1 | 9% | blood 2, standing_stone 1, throne 1, crystal 1 |
| 40 | Mountain Range | 160 | cave 78, mountain 47, hills 12 | roofed look, open text: 1 | 32% | shelf 9, ash 6, flowers 5, chains 5 |
| 53 | Great Pyramid | 59 | cave 33, crypt 15, desert 10 | roofed look, open text: 1 | 18% | bones 2, coffin 2, rubble 2, crate 1 |
| 62 | The Orc Enclave | 68 | forest 34, cave 25, field 5 | roofed look, open text: 1 | 54% | rug 15, cage 6, table 4, bed 4 |
| 90 | The Haunted Swamp | 20 | swamp 17, forest 2, inside 1 | open look, roofed text: 1 | 70% | bones 5, dead_tree 3, mushroom 2, stake 2 |
| 140 | The Necropolis of Eternal Nigh | 31 | crypt 22, dungeon 8, field 1 | roofed look, open text: 1 | 77% | bones 12, skull 8, blood 6, candle 4 |
| 220 | Castle Of The Apocalypse II | 122 | inside 63, castle 29, city 21 | town look, no town: 1 | 40% | banner 26, lantern 24, ash 6, rubble 5 |
| 245 | Shadowspire Citadel | 30 | inside 25, dungeon 3, castle 1 | roofed look, open text: 1 | 50% | crystal 8, pillar 6, throne 3, chains 2 |
| 424 | Castle Catacombs | 47 | crypt 33, cave 13, inside 1 | roofed look, open text: 1 | 55% | banner 6, ash 4, shelf 3, chains 3 |
| 426 | Troglodyte Mines | 44 | cave 17, mine 17, dungeon 8 | roofed look, open text: 1 | 79% | chains 9, lantern 9, ash 7, bones 6 |
| 429 | City of Ancients | 46 | city 23, inside 10, ruins 9 | open look, roofed text: 1 | 71% | pillar 13, bones 6, ash 6, banner 5 |
| 435 | MiNar I | 439 | forest 333, field 101, inside 4 | open look, roofed text: 1 | 30% | ash 24, bed 18, flowers 17, mushroom 10 |
| 441 | King's Forest | 11 | mountain 6, forest 3, cave 1 | roofed look, open text: 1 | 45% | ash 2, bed 2, well 2, chains 1 |
| 445 | Ogre Village | 88 | forest 30, snow 11, hills 9 | open look, roofed text: 1 | 46% | bones 15, brazier 9, ash 8, skull 5 |
| 447 | Mahn-Tor Keep | 90 | inside 57, city 24, cave 5 | roofed look, open text: 1 | 86% | banner 19, lantern 14, table 13, brazier 12 |
| 449 | Leper Island | 80 | forest 29, village 16, inside 13 | roofed look, open text: 1 | 51% | brazier 8, ash 8, fence 6, pole 6 |
| 454 | Caverns of the Pale Man | 100 | cave 97, mine 3 | roofed look, open text: 1 | 61% | bones 9, ash 9, shelf 7, pillar 7 |
| 461 | Tombs of Atuan | 36 | crypt 25, cave 8, dungeon 2 | roofed look, open text: 1 | 77% | pillar 7, bones 6, ash 5, chains 5 |
| 464 | Brethrenmere | 62 | cave 16, inside 16, mine 15 | roofed look, open text: 1 | 83% | lantern 26, table 11, bench 7, shelf 5 |
| 467 | Moria Deep | 22 | cave 9, mine 9, crypt 3 | roofed look, open text: 1 | 72% | bones 4, ash 4, banner 4, chest 2 |
| 470 | Castle of Ostragoth | 111 | cave 55, inside 26, crypt 14 | roofed look, open text: 1 | 68% | ash 14, bed 12, banner 10, bones 10 |
| 471 | Badlands II | 118 | field 35, forest 22, snow 20 | open look, roofed text: 1 | 50% | grave 11, ash 8, cairn 6, bones 6 |
| 474 | Cave Elf Kingdom | 113 | cave 65, inside 24, dungeon 18 | roofed look, open text: 1 | 82% | lantern 44, pillar 16, bench 12, throne 11 |
| 478 | Fire Grotto | 96 | cave 63, mine 13, dungeon 11 | roofed look, open text: 1 | 68% | ash 32, chains 14, bones 13, pillar 8 |
| 495 | Island Of The Dead | 98 | crypt 47, shore 25, forest 17 | roofed look, open text: 1 | 47% | ash 11, pillar 8, bench 6, chains 5 |
| 499 | Phaeton's Academy | 53 | inside 32, dungeon 15, garden 4 | roofed look, open text: 1 | 75% | lantern 14, bench 9, table 6, grave 5 |
| 517 | Garathorm School House | 33 | inside 29, city 2, field 2 | open look, roofed text: 1 | 60% | table 8, bench 7, shelf 5, rug 2 |
| 9 | Minos River Island | 10 | inside 10 | - | 60% | bones 2, stake 1, ash 1, rubble 1 |
| 12 | God Rooms | 4 | inside 4 | - | 25% | table 1 |
| 32 | Stable & Temple | 50 | inside 32, city 5, dungeon 5 | - | 14% | banner 3, altar 2, well 1, table 1 |
| 33 | The Three Of Swords | 76 | cave 32, mountain 19, hills 7 | - | 35% | torch 12, table 3, well 2, bed 2 |
| 36 | The Chessboard of Garathorm | 67 | city 65, inside 2 | - | 1% | bones 1 |
| 50 | Great Eastern Desert | 105 | water_swim 41, water_noswim 26, mountain 13 | - | 28% | mushroom 6, rubble 4, bed 4, grave 3 |
| 51 | Drow City | 100 | cave 65, inside 23, city 11 | - | 22% | banner 6, bed 4, lantern 4, throne 4 |
| 52 | Thalos | 49 | city 29, ruins 15, inside 4 | - | 51% | rubble 10, flowers 5, table 5, banner 2 |
| 61 | Haon-Dor (Dark) | 5 | web 2, inside 2, cave 1 | - | 20% | altar 1 |
| 63 | Arachnos | 53 | web 30, field 8, forest 7 | - | 9% | flowers 3, bones 1, chest 1 |
| 64 | Rand's Tower | 38 | inside 38 | - | 26% | table 6, bed 3, shelf 1, chest 1 |
| 65 | Dwarven Kingdom | 49 | inside 22, mine 11, field 8 | - | 12% | ash 2, bed 2, throne 1, blood 1 |
| 67 | The Eastern Highlands | 14 | hills 7, mountain 4, forest 1 | - | 28% | cairn 1, brazier 1, dead_tree 1, pillar 1 |
| 68 | The Sunken Coast | 12 | shore 2, cave 2, water_swim 2 | - | 58% | crystal 2, barrel 1, crate 1, bones 1 |
| 69 | The Ashlands | 12 | volcanic 10, shore 1, inside 1 | - | 66% | ash 7, bones 2, pillar 1, skull 1 |
| 73 | The Mindflayer's Lair | 3 | inside 3 | - | 66% | bones 2, tent 1, skull 1, throne 1 |
| 79 | Redferne's Residence | 20 | inside 15, mountain 5 | - | 50% | chains 6, crystal 2, table 1, shelf 1 |
| 80 | The Dragon's Domain | 5 | flying 2, cave 2, mountain 1 | - | 20% | pillar 1, bones 1, ash 1 |
| 100 | The Dwarven Mines of Khaz-Duru | 25 | cave 14, mine 10, mountain 1 | - | 56% | torch 2, crystal 2, statue 1, pillar 1 |
| 110 | Elven Village | 35 | inside 19, forest 15, mountain 1 | - | 14% | bed 2, weapons 1, barrel 1, ash 1 |
| 130 | The Sunken Ruins of Atal'narat | 18 | underwater 15, water_swim 2, city 1 | - | 61% | pillar 4, rubble 3, tent 3, bones 2 |
| 150 | Welmar's Castle | 58 | inside 57, castle 1 | - | 41% | banner 7, bed 6, throne 4, table 4 |
| 160 | The Plane of Eternal Chaos | 26 | mountain 13, volcanic 12, castle 1 | - | 23% | bones 2, crystal 2, ash 1, blood 1 |
| 180 | The Great Northern Forest | 26 | snow 15, forest 9, stones 1 | - | 61% | bones 4, crystal 3, well 2, standing_stone 2 |
| 190 | The Frostspire | 27 | snow 12, inside 9, cave 4 | - | 59% | bones 4, crystal 4, rubble 1, chains 1 |
| 200 | Forest of Shadows | 10 | forest 7, inside 2, web 1 | - | 100% | rug 5, bones 2, mushroom 1, rubble 1 |
| 210 | Tunnel Of Sticks | 101 | cave 101 | - | 0% | - |
| 235 | The Goblin Warrens | 20 | cave 13, inside 6, forest 1 | - | 85% | bones 6, mushroom 5, brazier 3, throne 3 |
| 240 | The Sunken Temple of Nereus | 25 | underwater 25 | - | 68% | bones 4, pillar 3, tent 3, altar 2 |
| 250 | Bedlam Arena | 18 | inside 16, water_swim 1, field 1 | - | 16% | banner 1, torch 1, blood 1, pillar 1 |
| 260 | Garathorm Housing District | 22 | city 22 | - | 9% | lantern 1, fence 1, brazier 1, table 1 |
| 270 | The Whispering Woods | 19 | forest 12, inside 2, water_swim 1 | - | 68% | flowers 4, mushroom 2, altar 2, well 1 |
| 280 | The Ashen Expanse | 36 | volcanic 32, desert 4 | - | 83% | ash 27, bones 8, banner 6, skull 3 |
| 285 | The Drowned Reliquary | 36 | underwater 36 | - | 58% | skull 6, pillar 5, candle 4, chains 3 |
| 295 | Crown of Bone | 36 | crypt 33, inside 2, castle 1 | - | 100% | bones 18, skull 8, grave 7, chains 5 |
| 300 | The Shattered Throne | 40 | inside 19, castle 14, mountain 7 | - | 62% | throne 12, rubble 6, pillar 5, banner 4 |
| 403 | Garathorm Wall | 50 | city 50 | - | 58% | banner 11, ash 8, brazier 5, lantern 4 |
| 415 | Quickstream | 22 | water_swim 22 | - | 22% | ash 3, fence 1, cairn 1, bones 1 |
| 416 | Castle Of Caboon | 49 | cave 31, crypt 10, inside 5 | - | 75% | ash 11, bones 10, grave 9, candle 6 |
| 418 | Garathorm Vineyard | 3 | inside 3 | - | 66% | bed 1, chest 1, barrel 1 |
| 420 | Fameland | 44 | inside 44 | - | 95% | statue 12, lantern 10, brazier 8, pillar 7 |
| 423 | Hommlet | 12 | inside 12 | - | 91% | bed 5, lantern 4, chest 3, table 3 |
| 442 | Outcast Fortress | 102 | cave 65, forest 17, field 6 | - | 8% | flowers 4, bed 2, rug 1, banner 1 |
| 448 | Mira Retrum I | 111 | water_noswim 102, shore 8, water_swim 1 | - | 36% | cairn 8, pole 6, bones 5, stake 4 |
| 451 | Mira Retrum II | 141 | water_swim 84, water_noswim 52, shore 3 | - | 29% | shelf 15, rubble 5, bones 4, pillar 3 |
| 452 | Submerged Temple | 65 | cave 36, inside 16, dungeon 7 | - | 66% | pillar 7, candle 5, shelf 5, chains 5 |
| 453 | Crater | 42 | volcanic 28, cave 14 | - | 64% | crate 17, rubble 5, ash 5, bones 4 |
| 457 | Castle Of The Apocalypse I | 36 | castle 36 | - | 0% | - |
| 458 | Castle Varok | 84 | inside 47, hills 25, field 8 | - | 61% | bed 13, table 10, rug 8, candle 7 |
| 465 | Below Moria | 97 | cave 65, mine 12, snow 5 | - | 61% | ash 17, drum 15, bones 11, pillar 8 |
| 469 | High Tower Of Magic II | 84 | inside 79, dungeon 5 | - | 22% | shelf 10, table 5, altar 2, ash 1 |
| 472 | Mount Ravenmist | 90 | mountain 69, snow 18, cave 2 | - | 37% | shelf 9, cairn 6, ash 4, standing_stone 4 |
| 475 | World Of Chaos | 90 | inside 29, necropolis 20, shore 17 | - | 90% | blood 33, bones 28, pillar 28, ash 8 |
| 482 | Haunted House | 49 | inside 48, ruins 1 | - | 77% | table 10, bed 6, lantern 6, chains 5 |
| 491 | Morvoct | 86 | inside 36, village 15, water_swim 9 | - | 70% | bones 13, table 11, ash 9, pillar 7 |
| 494 | Eden | 21 | garden 12, forest 7, field 2 | - | 61% | flowers 8, banner 3, grave 2, bed 2 |
| 496 | Isle of Lag | 22 | cave 9, forest 6, mountain 4 | - | 40% | ash 2, lantern 1, barrel 1, well 1 |
| 502 | Draconian Camp | 55 | cave 29, forest 22, inside 3 | - | 78% | ash 8, pole 7, brazier 7, bones 6 |
| 503 | Durmandel I | 114 | city 40, cave 31, field 20 | - | 73% | lantern 28, ash 18, table 18, banner 13 |
| 507 | Lost Crypt II | 84 | crypt 41, cave 35, volcanic 8 | - | 71% | ash 20, pillar 10, coffin 10, bones 9 |
| 509 | Durmandel Mines I | 151 | mine 149, cave 1, water_noswim 1 | - | 45% | ash 17, lantern 14, pillar 9, chains 5 |
| 514 | Morkai | 33 | cave 21, crypt 10, lava_cave 1 | - | 81% | bones 16, ash 7, skull 6, grave 4 |
| 518 | Necromancer Mines | 52 | mine 22, cave 14, inside 8 | - | 65% | bones 8, lantern 6, chains 5, grave 5 |
| 520 | Warded Castle | 77 | inside 38, castle 32, dungeon 3 | - | 77% | table 9, ash 8, banner 7, bed 7 |
| 521 | The Winterwood | 67 | snow 63, cave 2, ice_cave 1 | - | 20% | grave 2, tent 2, pole 2, dead_tree 2 |
| 522 | The Winterlands | 80 | snow 42, cave 38 | - | 53% | pillar 9, rubble 6, crystal 5, bench 4 |
