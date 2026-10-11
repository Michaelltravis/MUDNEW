# Zone bosses, measured

`python3 tools/balance/bosses.py --runs 2 --report ...`: each zone boss against a lone hero of every class at the boss's level, then a party of three (warrior, cleric, mage), with the game's own combat code (`tools/balance/sim.py`). Each cell: the minutes the fight took, the most of the hero's health it took at the worst moment (a death is all of it), and deaths (†) over the runs; "(lived)" is a fight called off at 15 minutes. Why the bosses are sized so: `docs/balance/marquee.md`, "Zone bosses".

| boss | level | health | warrior | mage | cleric | paladin | necromancer | thief | ranger | bard | assassin | lone heroes: median worst, deaths | party of three |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| spider queen | 12 | 2794 | 2.1m 68% | 3.4m 75% | 2.3m 42% | 2.4m 52% | 3.9m 0% | 1.8m 55% 1† | 4.0m 53% | 2.6m 75% | 2.0m 27% | 52%, 1/18 | 0.5m 0% |
| alpha wolf | 14 | 2982 | 2.1m 18% | 3.5m 82% | 3.8m 39% | 1.6m 23% | 2.6m 0% | 2.3m 76% | 3.4m 56% | 3.0m 3% | 2.5m 60% | 33%, 0/18 | 0.6m 12% |
| sewer king | 15 | 3080 | 1.9m 47% | 2.6m 89% 1† | 2.3m 42% | 1.6m 36% | 2.4m 14% | 1.6m 78% 1† | 2.9m 53% | 2.6m 8% | 1.9m 59% | 48%, 2/18 | 0.5m 10% |
| the Goblin King | 22 | 3867 | 3.7m 42% | 12.8m 68% 1† | 15.0m 42% (lived) | 5.0m 36% | 2.8m 10% | 7.3m 81% | 8.4m 61% | 15.0m 52% (lived) | 7.6m 66% | 51%, 1/18 | 1.0m 3% |
| ancient guardian | 25 | 4262 | 2.0m 33% | 2.3m 89% | 3.3m 58% | 1.6m 21% | 2.5m 86% 1† | 1.9m 34% | 3.2m 59% | 2.8m 44% | 2.1m 25% | 50%, 1/18 | 0.5m 6% |
| the Spider Queen | 26 | 4403 | 1.7m 36% | 2.0m 58% | 2.3m 40% | 1.6m 11% | 2.0m 0% | 1.6m 89% 1† | 2.5m 68% | 2.2m 37% | 1.7m 83% 1† | 50%, 2/18 | 0.7m 6% |
| the Necromancer | 28 | 4698 | 3.3m 17% | 15.0m 82% (lived) | 12.7m 41% | 3.9m 11% | 15.0m 79% (lived) | 3.9m 61% | 15.0m 48% (lived) | 9.7m 46% | 4.5m 59% | 51%, 0/18 | 0.7m 5% |
| frozen dwarven king | 28 | 4698 | 1.4m 28% | 2.0m 75% | 2.6m 47% | 1.6m 36% | 2.1m 53% | 1.8m 71% | 2.5m 59% | 2.2m 47% | 1.8m 49% | 55%, 0/18 | 0.5m 14% |
| master mindflayer | 30 | 5014 | 1.6m 24% | 2.4m 75% | 2.2m 40% | 1.5m 28% | 2.1m 54% | 1.8m 78% 1† | 2.9m 79% | 2.1m 58% | 2.1m 51% | 54%, 1/18 | 0.5m 0% |
| Vyrkothas the Frost Wyrm | 30 | 5014 | 1.6m 19% | 2.6m 60% 1† | 2.8m 46% | 1.9m 36% | 2.1m 0% | 1.9m 53% | 2.7m 61% | 2.6m 69% | 2.1m 55% | 46%, 1/18 | 0.6m 5% |
| Grimclaw the Great Bear | 36 | 6092 | 1.0m 39% | 2.1m 100% 2† | 1.6m 40% | 1.1m 26% | 1.2m 100% 2† | 1.2m 15% | 2.6m 67% | 1.6m 57% | 0.9m 35% | 49%, 4/18 | 0.6m 21% |
| the Oakfather | 40 | 6937 | 0.9m 34% | 2.2m 100% 1† | 1.6m 50% | 1.2m 32% | 1.1m 100% 2† | 1.1m 19% | 2.9m 75% | 1.6m 54% | 0.9m 26% | 48%, 3/18 | 0.5m 11% |
| the Blightlord | 40 | 6937 | 1.1m 33% | 2.0m 94% 1† | 2.1m 22% | 1.2m 4% | 2.4m 50% | 1.0m 51% 1† | 1.3m 100% 2† | 1.7m 50% | 0.9m 49% | 50%, 4/18 | 0.5m 10% |
| Aurexus the Bronze Dragon | 44 | 7899 | 1.1m 33% | 2.2m 100% 2† | 1.7m 10% | 1.2m 21% | 1.6m 60% 1† | 1.2m 97% 1† | 2.1m 56% | 1.7m 52% | 0.9m 44% | 51%, 4/18 | 0.5m 14% |
| beholder | 45 | 8160 | 1.3m 24% | 2.9m 96% 1† | 2.2m 39% | 1.7m 33% | 2.2m 59% 1† | 1.7m 90% 1† | 2.1m 43% | 2.3m 64% | 1.2m 34% | 47%, 3/18 | 0.5m 16% |
| Verdraxx the Green Dragon | 47 | 8910 | 2.2m 9% | 3.3m 100% 2† | 3.5m 54% | 2.6m 9% | 3.2m 62% | 2.7m 55% | 3.7m 53% | 4.0m 59% | 1.6m 25% | 50%, 2/18 | 0.8m 15% |
| Scorathax the Red Dragon | 50 | 10168 | 1.2m 27% | 2.6m 100% 2† | 2.3m 31% | 1.8m 18% | 1.9m 88% 1† | 1.6m 50% | 2.8m 74% | 2.2m 65% | 1.2m 50% | 56%, 3/18 | 0.6m 16% |
| Kaleidos the Prismatic Dragon | 50 | 10168 | 1.2m 25% | 2.5m 86% | 1.8m 14% | 1.4m 34% | 1.9m 21% | 1.3m 79% 1† | 2.3m 74% | 1.9m 57% | 1.1m 45% | 50%, 1/18 | 0.5m 16% |
| gate guardian | 60 | 15791 | 1.4m 15% | 2.7m 90% 1† | 2.1m 44% | 1.8m 9% | 1.8m 100% 2† | 1.8m 53% | 3.2m 61% | 2.1m 53% | 1.4m 29% | 50%, 3/18 | 0.5m 13% |
| gate guardian | 60 | 15791 | 1.4m 15% | 2.7m 90% 1† | 2.1m 44% | 1.8m 9% | 1.8m 100% 2† | 1.8m 53% | 3.2m 61% | 2.1m 53% | 1.4m 29% | 50%, 3/18 | 0.5m 13% |

All: a lone hero's median worst 51%, deaths 39/360.
