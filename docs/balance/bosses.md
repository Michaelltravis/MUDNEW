# Zone bosses, measured

`python3 tools/balance/bosses.py --runs 2 --report ...`: each zone boss against a lone hero of every class at the boss's level, then a party of three (warrior, cleric, mage), with the game's own combat code (`tools/balance/sim.py`). Each cell: the minutes the fight took, the most of the hero's health it took at the worst moment (a death is all of it), and deaths (†) over the runs; "(lived)" is a fight called off at 15 minutes. Why the bosses are sized so: `docs/balance/marquee.md`, "Zone bosses".

| boss | level | health | warrior | mage | cleric | paladin | necromancer | thief | ranger | bard | assassin | lone heroes: median worst, deaths | party of three |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| spider queen | 12 | 2794 | 2.1m 46% | 3.9m 98% 1† | 2.6m 33% | 2.5m 49% | 4.1m 0% | 1.9m 74% 1† | 4.1m 52% | 2.9m 65% | 2.3m 42% | 48%, 2/18 | 0.8m 0% |
| alpha wolf | 14 | 2982 | 2.2m 40% | 3.5m 100% 2† | 3.8m 51% | 1.6m 35% | 3.4m 13% | 2.1m 49% | 3.4m 54% | 3.5m 46% | 2.6m 45% | 48%, 2/18 | 0.7m 12% |
| sewer king | 15 | 3080 | 1.8m 48% | 2.7m 100% 2† | 2.7m 39% | 1.6m 37% | 2.9m 82% | 1.9m 74% | 2.9m 49% | 2.7m 54% | 1.8m 53% | 51%, 2/18 | 0.6m 8% |
| the Goblin King | 22 | 3867 | 5.4m 13% | 15.0m 58% (lived) | 15.0m 55% (lived) | 5.2m 23% | 3.0m 0% | 8.1m 78% 1† | 9.4m 54% | 15.0m 26% (lived) | 8.8m 50% | 46%, 1/18 | 1.1m 3% |
| ancient guardian | 25 | 4262 | 2.1m 21% | 3.2m 86% | 3.2m 55% | 1.6m 16% | 2.9m 100% 2† | 2.1m 36% | 3.6m 59% | 3.0m 81% 1† | 2.0m 20% | 54%, 3/18 | 0.6m 8% |
| the Spider Queen | 26 | 4403 | 1.7m 33% | 2.8m 92% 1† | 2.5m 57% | 1.8m 23% | 2.3m 0% | 1.4m 87% 1† | 2.8m 75% 1† | 2.4m 9% | 1.9m 69% | 50%, 3/18 | 0.7m 3% |
| the Necromancer | 28 | 4698 | 3.9m 12% | 13.2m 95% 1† | 14.5m 23% | 4.0m 25% | 15.0m 85% (lived) | 4.4m 50% | 15.0m 50% (lived) | 13.6m 59% | 4.9m 48% | 50%, 1/18 | 0.8m 4% |
| frozen dwarven king | 28 | 4698 | 1.5m 20% | 2.5m 99% 1† | 2.6m 66% | 1.6m 28% | 2.9m 50% | 1.7m 66% | 2.7m 73% | 2.4m 59% | 1.9m 35% | 53%, 1/18 | 0.6m 21% |
| master mindflayer | 30 | 5014 | 1.7m 34% | 2.6m 81% 1† | 2.6m 45% | 1.6m 23% | 2.3m 78% 1† | 1.9m 61% | 2.9m 61% | 2.2m 65% | 2.1m 51% | 53%, 2/18 | 0.7m 0% |
| Vyrkothas the Frost Wyrm | 30 | 5014 | 1.7m 15% | 3.1m 100% 2† | 3.1m 44% | 1.9m 26% | 2.3m 0% | 1.9m 51% | 2.9m 52% | 2.7m 72% | 2.0m 43% | 48%, 2/18 | 0.8m 7% |
| Grimclaw the Great Bear | 36 | 6092 | 1.0m 23% | 2.3m 100% 2† | 1.8m 48% | 1.3m 18% | 1.2m 100% 2† | 1.2m 10% | 1.9m 55% | 1.6m 55% | 0.9m 20% | 48%, 4/18 | 0.4m 3% |
| the Oakfather | 40 | 6937 | 0.8m 25% | 2.3m 97% 1† | 1.6m 33% | 1.2m 36% | 1.3m 100% 2† | 1.2m 23% | 1.9m 56% | 1.6m 54% | 1.1m 37% | 49%, 3/18 | 0.5m 21% |
| the Blightlord | 40 | 6937 | 1.1m 65% | 2.1m 88% 1† | 2.2m 49% | 1.4m 39% | 0.8m 100% 2† | 1.2m 6% | 2.4m 42% | 2.0m 65% | 0.8m 71% 1† | 51%, 4/18 | 0.5m 41% |
| Aurexus the Bronze Dragon | 44 | 7899 | 1.1m 33% | 2.4m 70% 1† | 1.8m 33% | 1.2m 20% | 1.4m 59% 1† | 1.5m 84% | 1.8m 71% | 1.7m 51% | 0.9m 40% | 49%, 2/18 | 0.6m 33% |
| beholder | 45 | 8160 | 1.3m 22% | 3.0m 100% 2† | 2.5m 45% | 1.7m 19% | 2.3m 66% 1† | 1.7m 83% | 2.0m 55% | 2.3m 65% | 1.2m 29% | 53%, 3/18 | 0.6m 17% |
| Verdraxx the Green Dragon | 47 | 8707 | 2.2m 7% | 4.0m 100% 2† | 3.9m 42% | 2.4m 7% | 2.5m 55% 1† | 2.8m 54% | 3.5m 52% | 3.5m 71% | 1.9m 23% | 48%, 3/18 | 0.7m 16% |
| Scorathax the Red Dragon | 50 | 9598 | 1.3m 22% | 2.4m 62% 1† | 2.3m 46% | 1.7m 15% | 2.1m 86% | 1.6m 81% | 2.1m 61% | 2.0m 60% | 1.1m 47% | 52%, 1/18 | 0.6m 8% |
| Kaleidos the Prismatic Dragon | 50 | 9598 | 1.1m 21% | 2.2m 100% 2† | 1.9m 25% | 1.4m 21% | 1.8m 87% 1† | 1.3m 77% 1† | 2.0m 60% | 1.9m 56% | 1.1m 42% | 53%, 4/18 | 0.5m 16% |
| gate guardian | 60 | 13279 | 1.2m 22% | 2.5m 70% | 1.9m 34% | 1.7m 15% | 1.6m 100% 2† | 1.6m 49% | 2.1m 66% | 1.9m 57% | 1.2m 30% | 49%, 2/18 | 0.4m 17% |
| gate guardian | 60 | 13279 | 1.2m 22% | 2.5m 70% | 1.9m 34% | 1.7m 15% | 1.6m 100% 2† | 1.6m 49% | 2.1m 66% | 1.9m 57% | 1.2m 30% | 49%, 2/18 | 0.4m 17% |

All: a lone hero's median worst 50%, deaths 47/360.
