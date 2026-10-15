# New-player audit: /play from the title screen to level 5

How it was done: a fresh human warrior was created through `/play`'s own creation wizard (race,
form, class, stats), then played to level 5 by a script that follows only what a newcomer is
shown — the quest tracker's words and its gold arrow — doing each step the way the tracker says
(walking the arrow's way, right-click Talk, Tab and F, opening the window it names). Screenshots
were taken at each new step, each level and wherever the script got stuck. The 3D client ran under
software rendering (no GPU), so its own frame times are not meaningful; everything else is.

Result after the fixes below: **level 5 in about a quarter of an hour of play, no deaths, never stuck**:
Awakening (talk to Sage Aldric) → Eyes Open (the fountain, the altar) → Know Thyself (character
sheet, bags, spellbook) → Blood and Steel (the training dummy) → The Art of Survival (rest, stand,
eat) → Tools of the Trade, with level 5 arriving on the way to the weapon shop.

## Findings, worst first

| # | What a newcomer met | Fixed |
|---|---|---|
| 1 | **The tracker froze after a step done in place.** Talking to Sage Aldric finished Awakening, but the tracker kept saying "Speak with Sage Aldric" for good: the map payload (which carries the tracker) was only sent when the player moved. The script talked to Aldric for two minutes and got nowhere. | `quests.py` `_push`: every quest accepted, advanced or finished sends the payload at once. |
| 2 | **The tutorial could not be finished in /play.** Know Thyself asks you to *type* `score`, `equipment`, `inventory`, `skills`, `spells`; /play shows those things in windows (C, I, K), and opening a window counted for nothing. The same for the shop list, quests and who. | The HUD tells the server when a window opens (`uiseen`), which counts as the command (`commands.py UI_SEEN`). |
| 3 | **The tutorial spoke telnet.** "Check your score (type "score")", "Defeat a training dummy (type "kill dummy")": the tracker and the chat log told a mouse-and-keys player to type commands. | `quest_guide.web_text`: on /play the step says how, e.g. "Check your score: open your Character sheet (C)", "Defeat a training dummy: Tab to target it, F to attack", "right-click yourself, then Rest". |
| 4 | **"Defeat 3 creatures" had no arrow.** Steps whose target is any creature pointed nowhere. | `quest_guide`: the way to the nearest fair fight (no shopkeepers or trainers, not far above your level, not in a peaceful room). |
| 5 | **A step finished in a fight lagged.** The training dummy's death finished Blood and Steel, but the tutorial only moved on at the player's next command, and meanwhile the tracker said "Return to Sage Aldric" (tutorials need no return). | Finished tutorial quests complete where the progress lands (`check_quest_progress`). |
| 6 | **"GOD ROOMS" over the stairs in the very first room.** The Temple's stairs up to the immortals' rooms were drawn with a signpost, a way no new player can take. | Exits only immortals may take are marked in the zone map (`imm`) and not drawn. |
| 7 | **An empty bar of eight slots across the middle of the screen.** The first extra action bar showed from the start with nothing on it. | An extra bar with nothing on it stays faded until hovered or until an ability is dragged. |
| 8 | **The server restarting froze the game.** The page lost its connection silently: no message, and nothing came back until a manual reload and sign-in. | A veil says the connection was lost and that it is reconnecting; the page waits for the server, reloads and signs straight back in with the browser's stored sign-in. |

Seen and left alone:
- **Levelling is fast.** The tutorial's own rewards carry a newcomer to level 3 before any fight and
  to level 5 after one training dummy. That may be intended (a quick start); it is a balance call.
- **Sage Aldric's greeting says "simply type talk aldric".** That is his spoken line, not a UI hint;
  /play players can still type it, and the tracker beside it says how to do it with the mouse.
- **Two dark slabs in the Training Grounds** (the room's weapon racks, by its features) looked black
  in a top-down frame under software rendering; worth a look on a real GPU.

## Load time

`MH.bootTimes` (new) records, in ms from the page's start, when the art kits are loaded, when the
title scene is up and when the player is in the world. Measured here:

- the page itself: ~0.4 s; 155 requests and ~5 MB to the title screen;
- the five art kits fetched and parsed: **0.8 s**;
- the title scene built: ~114 s here, all of it software rendering (shader compiles and the first
  frames on the CPU). On a real GPU this is the step to watch: open the browser console on /play
  and read `MH.bootTimes` (`title` minus `kits` is the scene).

## Reconnect

Before: when the server restarted, /play said nothing; the world stood still, commands went
nowhere, and only a manual reload and sign-in brought it back. After: see finding 8; checked live
by restarting the server under a signed-in page. The first live check caught one more thing: the
reloaded page signed in before its title scene was built, and the world (which starts listening for
the first map then) never drew the hero; the stored sign-in now waits for the title.

## Checks

`python3 tests/test_polish.py` (batch 6 section) checks the tracker push, the window credits, the
/play wording in the tracker and the chat log, "any creature" guidance, the tutorial's immediate
completion, the God Rooms stairs, the faded bar and the reconnect wiring.
