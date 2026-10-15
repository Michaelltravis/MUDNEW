# The polish pass (October 2026)

The owner: "I like all the suggestions. Complete all the suggested fixes." Six batches, each its
own pull request, each with its checks in `tests/test_polish.py` (and the web tests).

| Batch | What changed | PR |
|---|---|---|
| 1 | Mana stays in the orb and the class resource shows as pips; dark rooms are dark (a light you carry lights them); exit signs fade with distance and in a fight; big numbers shortened (200k); Tab keeps to your own room first | #136 |
| 2 | Combat numbers: where they show, their size and screen shake are settings, with a colour key; bursts of small hits add up; shake and hit-pause grow with the blow; a clear "you have fallen" card | #137 |
| 3 | Gear: tooltips compare with what you wear, an upgrade badge in the bags and loot window, rare drops stand in a beam of their colour | #138 |
| 4 | Quests: every ordinary quest is tracked, with where to go next and a gold arrow on the ground | #139 |
| 5 | Rooms drawn as their words say: ice and lava caves, a zone's own stone and light, landmark and boss rooms laid out by hand (`docs/world/room_visuals.md`) | #140 |
| 6 | A newcomer played from the title screen to level 5; everything that got in the way fixed: the tracker now follows a quest at once, the tutorial can be finished in /play and speaks its language, the God Rooms stairs are gone from the first room, the empty extra bar stays out of the way, and the page reconnects by itself when the server restarts. Load time is now measured (`MH.bootTimes`) | this one |

Details of batch 6, with what was seen and the numbers: `docs/NEW_PLAYER_AUDIT_2026-10-15.md`.
