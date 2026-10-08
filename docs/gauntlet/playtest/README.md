# Human playtest — the evidence only a person can add

The automated record (`../REPORT.md`, `../STATUS.md`) is complete. What remains is a real person
playing the first ten minutes. This page is the deploy + script for that.

## Deploy on the Mac mini (paste to OpenClaw)
```
cd ~/MUDNEW && git fetch origin claude/nice-johnson-slpinu && git checkout claude/nice-johnson-slpinu
pip3 install aiohttp
./run.sh &            # telnet :4000, web map :4001, command bridge + art :4003
open http://localhost:4001/platformer
```
Behind a reverse proxy: forward `/` → :4001, `/ws` and `/art/` → :4003 (`src/web_isometric/platformer/net.js`,
`MH.urls`, expects `mud.<host>` for the bridge). Nothing else to set up: accounts, world and art are in the repo.

## Script (15 minutes, one sitting, a brand-new character)
1. **forge a new soul** → human → a class from the picker (warrior, cleric, ranger carry "★ first pick").
   Note: did the picker tell you how you'd fight before you chose?
2. First screen: read only the welcome card; press **Talk to Sage Aldric** on it.
   Note: did you know what to do within ten seconds? Was anything else shouting for attention?
3. Follow the **Guide** (top-left) step by step — every step has a button. Expected route:
   temple → training dummy (**1** attack, **2** flee, **3** your class ability; **brace** when a creature
   winds up) → West Gate → Light Forest rabbit/fox → back → Great Field (4 north) → Newbie Zone (3 kills).
   Note the clock at level 2 and level 5. Bots: 1.5–5.4 min to level 5, 0–1 deaths.
4. Walk, don't teleport: hold a direction across at least three room edges.
   Note any seam, pop-in or stall at a crossing. Bots: none since world-03 round 5.
5. In the Newbie Zone `consider` a zombie, a wanderer and a veteran: Moderate / Challenging / DEADLY
   to a level 2–3 character. Do NOT fight the DEADLY one (that is the lesson).
6. If you die: which fight, at what HP.
7. Optional multiplayer (second browser or a friend): `group <name>` in the Newbie Zone, kill something
   together, watch the partner's screen for the ally badge and the need/greed/pass popup.
8. Write five lines in `docs/gauntlet/playtest/<date>.md`: class · time to L2 / L5 · deaths ·
   the one thing that confused you · the one thing that felt best.

## Decide afterwards (then it gets executed)
- XP ramp: keep `NEWCOMER_EXP = (250, 350, 500, 650)` (`src/player.py`) or slow to 300/450/600/800.
- Hit-dice variance: keep `randint(d/2, d)` per level or tighten to `randint(0.7d, d)`.
- Defensive stance: leave as a late-game trade, or give it flat damage reduction so it pays at the mastery tier.
- Further critic rounds (walk, onboarding): ~52k tokens each.
