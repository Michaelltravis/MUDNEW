# Zone bosses, measured

`python3 tools/balance/bosses.py --runs 2 --report ...`: each zone boss against a lone hero of every class at the boss's level, then a party of three (warrior, cleric, mage), with the game's own combat code (`tools/balance/sim.py`). Each cell: the minutes the fight took, the most of the hero's health it took at the worst moment (a death is all of it), and deaths (†) over the runs; "(lived)" is a fight called off at 15 minutes. Why the bosses are sized so: `docs/balance/marquee.md`, "Zone bosses".

| boss | level | health | warrior | mage | cleric | paladin | necromancer | thief | ranger | bard | assassin | lone heroes: median worst, deaths | party of three |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| spider queen | 12 | 2794 | 2.1m 46% | 3.9m 98% 1† | 2.6m 33% | 2.5m 49% | 4.1m 0% | 1.9m 74% 1† | 4.1m 52% | 2.9m 65% | 2.3m 42% | 48%, 2/18 | 0.8m 0% |
| alpha wolf | 14 | 2982 | 2.2m 40% | 3.5m 100% 2† | 3.8m 51% | 1.6m 35% | 3.4m 13% | 2.1m 49% | 3.4m 54% | 3.5m 46% | 2.6m 45% | 48%, 2/18 | 0.7m 12% |
| sewer king | 15 | 3080 | 1.8m 48% | 2.7m 100% 2† | 2.7m 39% | 1.6m 37% | 2.9m 82% | 1.9m 74% | 2.9m 49% | 2.7m 54% | 1.8m 53% | 51%, 2/18 | 0.6m 8% |
| the Goblin King | 22 | 3867 | 5.4m 22% | 11.6m 100% 2† | 15.0m 44% (lived) | 5.1m 35% | 3.1m 2% | 5.5m 96% 1† | 10.2m 55% | 15.0m 28% (lived) | 8.8m 72% | 51%, 3/18 | 1.2m 3% |
| ancient guardian | 25 | 4262 | 2.1m 21% | 3.2m 80% | 3.2m 55% | 1.6m 19% | 3.1m 99% 1† | 2.1m 36% | 3.6m 60% | 2.8m 77% 1† | 2.0m 20% | 54%, 2/18 | 0.6m 8% |
| the Spider Queen | 26 | 4403 | 1.7m 35% | 2.7m 100% 2† | 2.5m 57% | 1.8m 13% | 2.2m 0% | 1.5m 87% 1† | 2.8m 75% 1† | 2.4m 8% | 1.9m 69% | 50%, 4/18 | 0.7m 3% |
| the Necromancer | 28 | 4698 | 3.6m 13% | 15.0m 85% (lived) | 14.7m 22% | 4.0m 16% | 15.0m 77% (lived) | 4.4m 49% | 15.0m 50% (lived) | 14.5m 54% | 4.8m 54% | 49%, 0/18 | 0.8m 3% |
| frozen dwarven king | 28 | 4698 | 1.5m 15% | 2.4m 87% 1† | 2.5m 54% | 1.7m 33% | 2.9m 80% | 1.7m 55% | 2.8m 69% | 2.5m 66% | 1.9m 34% | 53%, 1/18 | 0.6m 18% |
| master mindflayer | 30 | 5014 | 1.6m 18% | 2.9m 67% 1† | 2.6m 41% | 1.6m 27% | 2.7m 82% 1† | 1.8m 64% | 3.2m 62% | 2.2m 67% | 2.1m 48% | 52%, 2/18 | 0.7m 0% |
| Vyrkothas the Frost Wyrm | 30 | 5014 | 1.6m 16% | 3.1m 100% 2† | 2.9m 59% | 2.0m 26% | 2.4m 5% | 1.9m 49% | 3.0m 54% | 2.8m 67% | 2.1m 51% | 53%, 2/18 | 0.8m 8% |
| Grimclaw the Great Bear | 36 | 6092 | 1.0m 34% | 2.3m 100% 2† | 1.8m 53% | 1.1m 24% | 1.4m 100% 2† | 1.3m 11% | 2.8m 69% | 1.8m 60% | 0.9m 28% | 50%, 4/18 | 0.5m 3% |
| the Oakfather | 40 | 6937 | 0.9m 38% | 2.0m 100% 2† | 1.7m 45% | 1.2m 35% | 0.9m 100% 2† | 1.1m 21% | 2.9m 85% | 1.6m 58% | 0.9m 32% | 50%, 4/18 | 0.5m 23% |
| the Blightlord | 40 | 6937 | 1.1m 30% | 3.0m 54% | 2.1m 6% | 1.3m 3% | 0.7m 100% 2† | 1.2m 46% | 3.9m 88% | 1.8m 43% | 0.9m 45% | 47%, 2/18 | 0.5m 14% |
| Aurexus the Bronze Dragon | 44 | 7899 | 1.1m 32% | 2.4m 70% 1† | 1.8m 33% | 1.2m 20% | 1.4m 59% 1† | 1.5m 83% | 2.3m 66% | 1.7m 50% | 0.9m 40% | 48%, 2/18 | 0.6m 32% |
| beholder | 45 | 8160 | 1.3m 23% | 2.9m 100% 2† | 2.5m 50% | 1.7m 20% | 2.2m 66% 1† | 1.7m 88% 1† | 2.2m 46% | 2.5m 68% | 1.2m 32% | 48%, 4/18 | 0.6m 18% |
| Verdraxx the Green Dragon | 47 | 8910 | 2.4m 18% | 3.1m 100% 2† | 3.9m 47% | 2.8m 21% | 2.5m 57% 1† | 2.9m 65% | 4.1m 54% | 4.1m 73% | 1.6m 32% | 51%, 3/18 | 0.7m 17% |
| Scorathax the Red Dragon | 50 | 10168 | 1.3m 28% | 2.9m 100% 2† | 2.4m 42% | 1.7m 18% | 2.4m 78% | 1.6m 41% | 2.9m 64% | 2.2m 61% | 1.3m 36% | 48%, 2/18 | 0.6m 7% |
| Kaleidos the Prismatic Dragon | 50 | 10168 | 1.2m 21% | 2.4m 100% 2† | 2.0m 32% | 1.4m 30% | 1.8m 96% 1† | 1.4m 76% 1† | 2.5m 63% | 2.0m 56% | 1.1m 39% | 52%, 4/18 | 0.5m 15% |
| gate guardian | 60 | 15791 | 1.5m 14% | 3.0m 77% | 2.4m 42% | 1.9m 12% | 1.9m 100% 2† | 1.9m 51% | 3.3m 59% | 2.2m 56% | 1.4m 25% | 52%, 2/18 | 0.5m 14% |
| gate guardian | 60 | 15791 | 1.5m 14% | 3.0m 77% | 2.4m 42% | 1.9m 12% | 1.9m 100% 2† | 1.9m 51% | 3.3m 59% | 2.2m 56% | 1.4m 25% | 52%, 2/18 | 0.5m 14% |

All: a lone hero's median worst 50%, deaths 49/360.
