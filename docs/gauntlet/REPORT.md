# Misthollow Reforged — report for the human brake

Branch `claude/nice-johnson-slpinu`. Reference for every blind A/B: BrowserQuest, run locally.
Everything below is recorded under `docs/gauntlet/`; `STATUS.md` is the detailed handoff.

## Scoreboard
| piece | best verdict | confidence | record |
|---|---|---|---|
| atmosphere / actors / HUD | WIN | — | `graphics-01`, `graphics-02` |
| style lock (Lucifer CC0 art, 9 class models) | WIN 6/7 | — | `style-01`, `docs/art/` |
| combat pacing / feel | WIN | — | `playability-01`, `playability-02` |
| world / walk (continuous world, physics across rooms) | WIN (walk + forest) | medium, sides swapped by seed | `world-03/round-5` |
| onboarding (picker → welcome → Guide → growing hotbar) | WIN (start + first) | **high** | `onboard-01/round-4` |
| easy to start | 9 of 9 classes reach level 5, two runs each, 1.5–5.4 min | measured | `progression-01/classes*` |
| hard to master | each mechanic bites in a measured tier, two runs per tier | measured | `progression-01/README.md` |
| multiplayer | presence, ally badges, need/greed/pass; three two-client playthroughs | shown | `multiplayer/` |

## Bugs the measurements found and fixed (all would have reached players)
- Held-key teleport: holding a direction 1.5 s fired the exit (the cause of seven walk losses).
- Exit breaker counted wall-clock time (any stalled frame = "stuck").
- Tutorial sent newcomers out the wrong gate into level-4 aggressive goblins; "north three times" was four.
- Bard, paladin, ranger started without the attack the UI promised (roster order).
- Six "newbie" creatures of levels 1–5 share one keyword in the same corridors (level 4–5 renamed).
- A level-1 bard/thief could start on 13–14 HP (floor 16); level-up HP was 1..d (floor d/2).
- `mload` crashed the caller's connection; `Player.die()` crashed the whole server.
- Prompted `interrupt` at 35% ("a prompt that lies two times in three"); non-boss spells one-shot
  from above half health (capped at 60% of max HP); `consider` rated casters a step too low.

## Dials left to the human (each named with its location in the records)
- Max-HP variance at equal level (40 vs 58 at level 5) decides mastery-tier fights more than play.
- Defensive stance is a net loss at the mastery tier; the reaction layer beats the buttons only at
  the caster tier (interrupt) — the systems bite, but they have not been shown to out-perform the
  basics without a human's timing.
- `NEWCOMER_EXP` is brisk (level 5 in ~2.5 min); 300/450/600/800 for a ~10-minute first five levels.
- Canopy crispness at game scale; welcome/Guide text size.

## What only a human can add
A real playthrough (the bots play a 1 s-granularity script), more critic rounds for confidence,
and taste on the dials above. Nothing in this report should be read as "finished": it is what has
been built, measured and verified, with the numbers.
